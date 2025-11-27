"""Run Django tests per app to avoid top-level `tests` discovery conflicts.

This script loads Django, enumerates non-django apps from INSTALLED_APPS,
then runs `python manage.py test <app>` for each app and prints a summary.
"""
import os
import sys
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_quitus_PAL.settings')
# Ensure project root is on sys.path so Django settings package can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import django
django.setup()

from django.conf import settings

apps = [a for a in settings.INSTALLED_APPS if not a.startswith('django.')]
print('Apps to test:')
for a in apps:
    print(' -', a)

results = {}
for app in apps:
    # If the app contains a `tests` package, prefer running that package label to avoid discovery issues
    app_path = os.path.join(project_root, app.replace('.', os.sep))
    label = app
    tests_pkg_path = os.path.join(app_path, 'tests')
    if os.path.isdir(tests_pkg_path):
        label = f"{app}.tests"

    print(f"\n=== Running tests for: {app} (label: {label}) ===")
    rc = subprocess.call([sys.executable, 'manage.py', 'test', label, '-v', '2'])
    results[app] = rc
    if rc != 0:
        print(f"Tests for {app} failed with exit code {rc}.")

print('\n=== Summary ===')
failed = False
for app, rc in results.items():
    status = 'OK' if rc == 0 else f'FAIL (code {rc})'
    print(f"{app}: {status}")
    if rc != 0:
        failed = True

if failed:
    sys.exit(1)
else:
    sys.exit(0)

# Additionally, discover standalone test files (test*.py) outside app packages
def run_standalone_tests():
    print('\nSearching for standalone test*.py files outside app packages...')
    standalone = []
    app_paths = [os.path.abspath(os.path.join(project_root, a.replace('.', os.sep))) for a in apps]
    for root, dirs, files in os.walk(project_root):
        # skip virtualenvs, media, migrations, static, etc.
        if any(part in ('venv', '.venv', 'env', '__pycache__', 'media', 'static', 'node_modules') for part in root.split(os.sep)):
            continue
        for fname in files:
            if fname.startswith('test') and fname.endswith('.py'):
                full = os.path.abspath(os.path.join(root, fname))
                # skip if inside an app package
                if any(full.startswith(ap) for ap in app_paths):
                    continue
                # skip the scripts folder helper
                if os.path.commonpath([full, os.path.abspath(os.path.join(project_root, 'scripts'))]) == os.path.abspath(os.path.join(project_root, 'scripts')):
                    continue
                standalone.append(full)

    if not standalone:
        print('No standalone test files found.')
        return 0

    overall = 0
    for f in standalone:
        rel = os.path.relpath(f, project_root)
        print(f"\nRunning standalone tests in: {rel}")
        rc = subprocess.call([sys.executable, '-m', 'unittest', rel])
        overall += rc
        if rc != 0:
            print(f"Standalone tests in {rel} failed (exit {rc}).")

    return overall


if __name__ == '__main__':
    extra_failures = run_standalone_tests()
    if extra_failures:
        print('\nSome standalone tests failed.')
        sys.exit(1)
    else:
        print('\nStandalone tests OK (if any).')

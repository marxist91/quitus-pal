from django.conf import settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','gestion_quitus_PAL.settings')
import django
django.setup()
from django.db import connection
cur = connection.cursor()
# Add nullable quitus_id column if not exists (MySQL doesn't support IF NOT EXISTS for ADD COLUMN pre-8.0?)
# We'll check existing columns first.
cur.execute("SHOW COLUMNS FROM historique_quitus")
cols = [r[0] for r in cur.fetchall()]
print('Existing columns:', cols)
if 'quitus_id' not in cols:
    print('Adding column quitus_id')
    cur.execute("ALTER TABLE historique_quitus ADD COLUMN quitus_id CHAR(32) NULL")
else:
    print('Column quitus_id already exists')
# Check constraints
cur.execute("SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name='historique_quitus' AND column_name='quitus_id'")
existing_fk = cur.fetchall()
print('Existing fk for quitus_id:', existing_fk)
if not existing_fk:
    print('Adding foreign key constraint')
    cur.execute("ALTER TABLE historique_quitus ADD CONSTRAINT fk_historique_quitus_quitus FOREIGN KEY (quitus_id) REFERENCES quitus(id) ON DELETE CASCADE")
else:
    print('Foreign key already exists')
# Show final columns
cur.execute('SHOW COLUMNS FROM historique_quitus')
for row in cur.fetchall():
    print(row)
print('Done')

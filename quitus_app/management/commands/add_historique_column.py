from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Add quitus_id column and FK to historique_quitus if missing'

    def handle(self, *args, **options):
        cur = connection.cursor()
        cur.execute("SHOW COLUMNS FROM historique_quitus")
        cols = [r[0] for r in cur.fetchall()]
        self.stdout.write('Existing columns: %s' % cols)
        if 'quitus_id' not in cols:
            self.stdout.write('Adding column quitus_id')
            cur.execute("ALTER TABLE historique_quitus ADD COLUMN quitus_id CHAR(32) NULL")
        else:
            self.stdout.write('Column quitus_id already exists')

        cur.execute("SELECT constraint_name FROM information_schema.key_column_usage WHERE table_schema = DATABASE() AND table_name='historique_quitus' AND column_name='quitus_id'")
        existing_fk = cur.fetchall()
        self.stdout.write('Existing fk for quitus_id: %s' % (existing_fk,))
        if not existing_fk:
            self.stdout.write('Adding foreign key constraint')
            cur.execute("ALTER TABLE historique_quitus ADD CONSTRAINT fk_historique_quitus_quitus FOREIGN KEY (quitus_id) REFERENCES quitus(id) ON DELETE CASCADE")
        else:
            self.stdout.write('Foreign key already exists')

        cur.execute('SHOW COLUMNS FROM historique_quitus')
        for row in cur.fetchall():
            self.stdout.write(str(row))
        self.stdout.write('Done')

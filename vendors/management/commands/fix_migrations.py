from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fixes the migration history for sites app'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if the migrations are already applied
            cursor.execute(
                "SELECT COUNT(*) FROM django_migrations WHERE app='sites' AND name IN ('0001_initial', '0002_alter_domain_unique')"
            )
            count = cursor.fetchone()[0]
            
            if count < 2:
                # Mark sites migrations as applied
                cursor.execute(
                    "INSERT INTO django_migrations (app, name, applied) VALUES ('sites', '0001_initial', NOW()), ('sites', '0002_alter_domain_unique', NOW())"
                )
                self.stdout.write(self.style.SUCCESS('Successfully fixed migration history.'))
            else:
                self.stdout.write(self.style.SUCCESS('Migration history is already correct.'))

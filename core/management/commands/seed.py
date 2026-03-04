from django.core.management.base import BaseCommand
from core.models import User, BloodInventory


class Command(BaseCommand):
    help = 'Seed the database with default admin account and blood inventory'

    def handle(self, *args, **kwargs):
        # Create blood inventory for all 8 blood groups
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        for bg in blood_groups:
            obj, created = BloodInventory.objects.get_or_create(
                blood_group=bg,
                defaults={'units_available': 0}
            )
            if created:
                self.stdout.write(f'  ✅ Blood inventory created for {bg}')

        # Create default admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@lifeflow.com',
                password='admin123',
                first_name='Super',
                last_name='Admin',
                role='admin',
            )
            self.stdout.write('  ✅ Admin account created → username: admin | password: admin123')
        else:
            self.stdout.write('  ℹ️  Admin already exists. Skipped.')

        self.stdout.write(self.style.SUCCESS('\n🎉 Seeding complete! Run: python manage.py runserver'))

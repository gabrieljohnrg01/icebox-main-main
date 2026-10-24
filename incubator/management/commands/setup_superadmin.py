from django.core.management.base import BaseCommand
from incubator.models import User

class Command(BaseCommand):
    help = 'Creates a superadmin without a password for the passwordless flow'

    def handle(self, *args, **options):
        # We prompt for username internally or use a default
        username = 'superadmin'
        email = 'superadmin@example.com'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Superadmin with username "{username}" already exists.'))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=None,
            first_name='Super',
            last_name='Admin',
            role='super_admin'
        )
        user.set_unusable_password()
        user.save()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created superadmin "{username}". Login with this username and no password.'))

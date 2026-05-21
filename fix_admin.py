import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from incubator.models import User

try:
    # Find the superuser that was just created
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        admin_user.role = 'super_admin'
        admin_user.save()
        print(f"[\u2713] Successfully updated role of user '{admin_user.username}' to super_admin!")
    else:
        print("[!] No superuser found in the database.")
except Exception as e:
    print(f"[!] Error: {e}")

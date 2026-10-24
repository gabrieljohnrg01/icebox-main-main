from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Seeds all default data (predefined milestone templates and readiness level frameworks)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Milestone & Deliverable templates..."))
        call_command('seed_templates')
        
        self.stdout.write(self.style.NOTICE("Populating Readiness Level templates (TRL, CRL, BRL, FRL)..."))
        call_command('populate_rl')
        
        self.stdout.write(self.style.SUCCESS("All seed data successfully initialized!"))

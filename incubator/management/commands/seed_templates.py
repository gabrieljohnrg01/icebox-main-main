from django.core.management.base import BaseCommand
from incubator.models import MilestoneTemplate, DeliverableTemplate, Deliverable, RLTemplate
from incubator.views import sync_all_templates_readiness

class Command(BaseCommand):
    help = 'Seeds predefined Milestone and Deliverable templates and links legacy deliverables'

    def handle(self, *args, **options):
        template_data = [
            {
                "title": "Milestone 1",
                "description": "Initial setup and registration",
                "progress": 1,
                "deliverables": [
                    ("Deliverable 1", "Complete deliverable 1 for milestone 1"),
                    ("Deliverable 2", "Complete deliverable 2 for milestone 1"),
                    ("Deliverable 3", "Complete deliverable 3 for milestone 1"),
                    ("Deliverable 4", "Complete deliverable 4 for milestone 1"),
                    ("Deliverable 5", "Complete deliverable 5 for milestone 1"),
                ]
            },
            {
                "title": "Milestone 2",
                "description": "Second phase",
                "progress": 2,
                "deliverables": [
                    ("Deliverable 1", "Complete deliverable 1 for milestone 2"),
                    ("Deliverable 2", "Complete deliverable 2 for milestone 2"),
                    ("Deliverable 3", "Complete deliverable 3 for milestone 2"),
                ]
            },
            {
                "title": "Milestone 3",
                "description": "Third phase",
                "progress": 3,
                "deliverables": [
                    ("Deliverable 1", "Complete deliverable 1 for milestone 3"),
                    ("Deliverable 2", "Complete deliverable 2 for milestone 3"),
                    ("Deliverable 3", "Complete deliverable 3 for milestone 3"),
                    ("Deliverable 4", "Complete deliverable 4 for milestone 3"),
                ]
            },
            {
                "title": "Milestone 4",
                "description": "Final phase",
                "progress": 4,
                "deliverables": [
                    ("Deliverable 1", "Complete deliverable 1 for milestone 4"),
                    ("Deliverable 2", "Complete deliverable 2 for milestone 4"),
                    ("Deliverable 3", "Complete deliverable 3 for milestone 4"),
                ]
            }
        ]

        created_ms = 0
        created_dt = 0
        linked = 0

        for ms_data in template_data:
            mt, created = MilestoneTemplate.objects.get_or_create(
                title=ms_data["title"],
                defaults={
                    "description": ms_data["description"],
                    "milestone_progress": ms_data["progress"]
                }
            )
            if created:
                created_ms += 1
                
            for name, reqs in ms_data["deliverables"]:
                dt, created_d = DeliverableTemplate.objects.get_or_create(
                    milestone_template=mt,
                    name=name,
                    defaults={
                        "requirements": reqs
                    }
                )
                if created_d:
                    created_dt += 1
                    
                updated = Deliverable.objects.filter(
                    name=name,
                    milestone__title=mt.title,
                    template__isnull=True
                ).update(template=dt)
                linked += updated

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_ms} Milestone Templates."))
        self.stdout.write(self.style.SUCCESS(f"Seeded {created_dt} Deliverable Templates."))
        self.stdout.write(self.style.SUCCESS(f"Successfully linked {linked} legacy deliverables to the templates!"))

        # Configure default baseline readiness levels on templates if not already set
        rl_map = {rl.name: rl for rl in RLTemplate.objects.filter(name__in=['TRL', 'CRL', 'BRL', 'FRL'])}
        default_ms_rls = {
            1: ['TRL', 'CRL'],
            2: ['TRL', 'CRL', 'BRL'],
            3: ['TRL', 'CRL', 'BRL', 'FRL'],
            4: ['TRL', 'CRL', 'BRL', 'FRL'],
        }
        for mt in MilestoneTemplate.objects.all():
            if not mt.rl_templates.exists():
                ms_names = default_ms_rls.get(mt.milestone_progress, ['TRL', 'CRL'])
                mt.rl_templates.set([rl_map[n] for n in ms_names if n in rl_map])

            for dt in mt.deliverable_templates.all():
                if not dt.rl_templates.exists():
                    dt_names = default_ms_rls.get(mt.milestone_progress, ['TRL', 'CRL'])
                    dt.rl_templates.set([rl_map[n] for n in dt_names if n in rl_map])

        sync_all_templates_readiness()
        self.stdout.write(self.style.SUCCESS("Synchronized readiness levels across all milestone and deliverable templates to startups."))

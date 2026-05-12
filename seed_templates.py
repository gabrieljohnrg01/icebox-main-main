import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from incubator.models import MilestoneTemplate, DeliverableTemplate, Deliverable

# Create the predefined Milestone and Deliverable templates
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
    # 1. Create the MilestoneTemplate if it doesn't exist
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
        # 2. Create the DeliverableTemplate
        dt, created_d = DeliverableTemplate.objects.get_or_create(
            milestone_template=mt,
            name=name,
            defaults={
                "requirements": reqs
            }
        )
        if created_d:
            created_dt += 1
            
        # 3. Link existing deliverables! Since multiple milestones might have a "Deliverable 1",
        # we only link the ones that reside underneath the corresponding SAME named Milestone!
        updated = Deliverable.objects.filter(
            name=name,
            milestone__title=mt.title,
            template__isnull=True
        ).update(template=dt)
        linked += updated

print(f"Seeded {created_ms} Milestone Templates.")
print(f"Seeded {created_dt} Deliverable Templates.")
print(f"Successfully linked {linked} legacy deliverables to the new templates!")

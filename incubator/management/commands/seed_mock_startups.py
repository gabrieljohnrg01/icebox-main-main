from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from incubator.models import (
    User, Cohort, Startup, StartupMember, Milestone, Deliverable,
    Readiness, MilestoneReadiness, ProgressReport, Comment,
    MilestoneTemplate, DeliverableTemplate, RLTemplate
)
from incubator.views import sync_deliverable_template_readiness, sync_milestone_template_readiness
import datetime

class Command(BaseCommand):
    help = 'Generates 4 realistic mockup startups with team members, milestones, deliverables, and readiness levels for demonstration.'

    def handle(self, *args, **options):
        self.stdout.write("Initializing mock demonstration startups...")

        with transaction.atomic():
            # 1. Ensure active Cohort exists
            cohort, _ = Cohort.objects.get_or_create(
                name="Cohort 2026-A",
                defaults={
                    "start_date": timezone.now().date() - datetime.timedelta(days=90),
                    "end_date": timezone.now().date() + datetime.timedelta(days=275),
                }
            )

            # Ensure baseline templates exist
            from django.core.management import call_command
            call_command('seed_all')

            demo_password = "Password123!"

            # Startup Definitions
            startups_data = [
                {
                    "name": "AgriPulse Innovations",
                    "description": "Smart IoT soil sensors and AI-powered crop health diagnostics providing real-time irrigation and nutrient recommendations for precision agriculture.",
                    "email": "contact@agripulse.io",
                    "contact_number": "+63 917 123 4501",
                    "starting_milestone": 2,
                    "founder": {
                        "username": "carlos.mendez",
                        "email": "carlos.mendez@agripulse.io",
                        "first_name": "Carlos",
                        "last_name": "Mendez",
                        "contact_number": "+63 917 123 4501",
                        "position": "CEO",
                    },
                    "members": [
                        {
                            "username": "elena.santos",
                            "email": "elena.santos@agripulse.io",
                            "first_name": "Elena",
                            "last_name": "Santos",
                            "contact_number": "+63 917 123 4502",
                            "position": "CTO",
                        },
                        {
                            "username": "marco.reyes",
                            "email": "marco.reyes@agripulse.io",
                            "first_name": "Marco",
                            "last_name": "Reyes",
                            "contact_number": "+63 917 123 4503",
                            "position": "COO",
                        },
                    ],
                    "report": {
                        "title": "Q1 Pilot Testing & Sensor Deployment Report",
                        "description": "Completed deployment of 45 sensor nodes across three partner farms in Central Luzon.",
                        "achievements": "Achieved 99.4% telemetry uptime; reduced irrigation water usage by 24% in field tests.",
                        "challenges": "Occasional cellular signal drops in remote rural pockets; exploring LoRaWAN mesh relay.",
                        "next_steps": "Finalize manufacturing prototype for casing waterproofing and deploy v2 firmware.",
                    },
                    "trl_level": "Level 6",
                    "crl_level": "Level 5",
                    "brl_level": "Level 4",
                    "frl_level": "Level 3",
                },
                {
                    "name": "BioNova Diagnostics",
                    "description": "Portable microfluidic rapid test kits coupled with a smartphone spectrophotometer for decentralized detection of infectious diseases in rural clinics.",
                    "email": "info@bionova.health",
                    "contact_number": "+63 918 234 5601",
                    "starting_milestone": 1,
                    "founder": {
                        "username": "althea.cruz",
                        "email": "althea.cruz@bionova.health",
                        "first_name": "Althea",
                        "last_name": "Cruz",
                        "contact_number": "+63 918 234 5601",
                        "position": "CEO",
                    },
                    "members": [
                        {
                            "username": "julian.navarro",
                            "email": "julian.navarro@bionova.health",
                            "first_name": "Julian",
                            "last_name": "Navarro",
                            "contact_number": "+63 918 234 5602",
                            "position": "Chief Scientific Officer",
                        },
                        {
                            "username": "samantha.dizon",
                            "email": "samantha.dizon@bionova.health",
                            "first_name": "Samantha",
                            "last_name": "Dizon",
                            "contact_number": "+63 918 234 5603",
                            "position": "Regulatory & Quality Lead",
                        },
                    ],
                    "report": {
                        "title": "Bio-Reagent Stability & Assay Validation",
                        "description": "Verified chemical reagent stability at room temperature across 30 days accelerated shelf testing.",
                        "achievements": "Synthesized 50 test cartridges with 96.8% sensitivity against benchmark laboratory assays.",
                        "challenges": "Sourcing medical-grade nitrocellulose membrane with consistent capillary flow rates.",
                        "next_steps": "Submit initial clinical protocol to Institutional Ethics Review Board.",
                    },
                    "trl_level": "Level 4",
                    "crl_level": "Level 3",
                    "brl_level": "Level 2",
                    "frl_level": "Level 2",
                },
                {
                    "name": "EcoCharge Mobility",
                    "description": "Standardized smart battery swapping kiosks and telematics network tailored for commercial electric two-wheelers and municipal e-trikes.",
                    "email": "hello@ecocharge.ph",
                    "contact_number": "+63 919 345 6701",
                    "starting_milestone": 3,
                    "founder": {
                        "username": "rafael.devera",
                        "email": "rafael.devera@ecocharge.ph",
                        "first_name": "Rafael",
                        "last_name": "De Vera",
                        "contact_number": "+63 919 345 6701",
                        "position": "CEO",
                    },
                    "members": [
                        {
                            "username": "vincent.tan",
                            "email": "vincent.tan@ecocharge.ph",
                            "first_name": "Vincent",
                            "last_name": "Tan",
                            "contact_number": "+63 919 345 6702",
                            "position": "CTO",
                        },
                        {
                            "username": "beatrice.ramos",
                            "email": "beatrice.ramos@ecocharge.ph",
                            "first_name": "Beatrice",
                            "last_name": "Ramos",
                            "contact_number": "+63 919 345 6703",
                            "position": "Head of Partnerships",
                        },
                    ],
                    "report": {
                        "title": "Commercial Pilot: 5-Station Swapping Network",
                        "description": "Operating 5 operational swap stations supporting a fleet of 60 registered delivery courier riders.",
                        "achievements": "Over 4,200 successful battery swaps logged with average swap turnaround under 60 seconds.",
                        "challenges": "Thermal management optimization during peak noon ambient temperatures.",
                        "next_steps": "Scale to 15 additional station hubs and onboard 2 logistics fleet partners.",
                    },
                    "trl_level": "Level 7",
                    "crl_level": "Level 6",
                    "brl_level": "Level 6",
                    "frl_level": "Level 5",
                },
                {
                    "name": "QuantumLogix AI",
                    "description": "Enterprise freight optimization and dynamic dispatch engine using quantum-inspired combinatorial algorithms to slash last-mile routing costs.",
                    "email": "ops@quantumlogix.tech",
                    "contact_number": "+63 920 456 7801",
                    "starting_milestone": 1,
                    "founder": {
                        "username": "gabriel.vance",
                        "email": "gabriel.vance@quantumlogix.tech",
                        "first_name": "Gabriel",
                        "last_name": "Vance",
                        "contact_number": "+63 920 456 7801",
                        "position": "CEO",
                    },
                    "members": [
                        {
                            "username": "maya.lin",
                            "email": "maya.lin@quantumlogix.tech",
                            "first_name": "Maya",
                            "last_name": "Lin",
                            "contact_number": "+63 920 456 7802",
                            "position": "Head of AI Research",
                        },
                        {
                            "username": "derrick.wu",
                            "email": "derrick.wu@quantumlogix.tech",
                            "first_name": "Derrick",
                            "last_name": "Wu",
                            "contact_number": "+63 920 456 7803",
                            "position": "Product Manager",
                        },
                    ],
                    "report": {
                        "title": "Core Algorithm Benchmark & Simulator Launch",
                        "description": "Benchmarked heuristics against standard vehicle routing problem (CVRP) test datasets.",
                        "achievements": "Demonstrated 18.2% reduction in fleet fuel consumption and route distances on simulated runs.",
                        "challenges": "Integrating heterogeneous constraints (driver shift legal limits, cold-chain refrigeration).",
                        "next_steps": "Beta API integration with two third-party logistics test customers.",
                    },
                    "trl_level": "Level 5",
                    "crl_level": "Level 4",
                    "brl_level": "Level 3",
                    "frl_level": "Level 2",
                },
            ]

            milestone_templates = list(MilestoneTemplate.objects.all().prefetch_related('rl_templates', 'deliverable_templates__rl_templates').order_by('milestone_progress'))

            for s_data in startups_data:
                # 1. Create or update Founder User
                f_data = s_data["founder"]
                founder_user, created_f = User.objects.get_or_create(
                    username=f_data["username"],
                    defaults={
                        "email": f_data["email"],
                        "first_name": f_data["first_name"],
                        "last_name": f_data["last_name"],
                        "contact_number": f_data["contact_number"],
                        "role": "incubatee",
                        "must_change_password": False,
                    }
                )
                founder_user.set_password(demo_password)
                founder_user.must_change_password = False
                founder_user.save()

                # 2. Create or update Startup
                startup, created_s = Startup.objects.get_or_create(
                    name=s_data["name"],
                    defaults={
                        "description": s_data["description"],
                        "email": s_data["email"],
                        "contact_number": s_data["contact_number"],
                        "owner": founder_user,
                        "cohort": cohort,
                    }
                )
                startup.description = s_data["description"]
                startup.email = s_data["email"]
                startup.contact_number = s_data["contact_number"]
                startup.owner = founder_user
                startup.cohort = cohort
                startup.is_archived = False
                startup.save()

                # Link Founder as CEO in StartupMember
                StartupMember.objects.get_or_create(
                    startup=startup,
                    user=founder_user,
                    defaults={"role": f_data["position"]}
                )

                # 3. Create or update Team Members
                for m_data in s_data["members"]:
                    member_user, created_m = User.objects.get_or_create(
                        username=m_data["username"],
                        defaults={
                            "email": m_data["email"],
                            "first_name": m_data["first_name"],
                            "last_name": m_data["last_name"],
                            "contact_number": m_data["contact_number"],
                            "role": "incubatee",
                            "must_change_password": False,
                        }
                    )
                    member_user.set_password(demo_password)
                    member_user.must_change_password = False
                    member_user.save()

                    StartupMember.objects.get_or_create(
                        startup=startup,
                        user=member_user,
                        defaults={"role": m_data["position"]}
                    )

                # 4. Generate Milestones & Deliverables
                starting_m = s_data["starting_milestone"]
                for mt in milestone_templates:
                    p = mt.milestone_progress
                    is_past = p < starting_m
                    is_current = p == starting_m
                    
                    ms_status = "completed" if is_past else ("pending" if is_current else "not-yet")
                    completed_at = (timezone.now() - datetime.timedelta(days=(30 * (starting_m - p)))) if is_past else None

                    ms, _ = Milestone.objects.get_or_create(
                        startup=startup,
                        milestone_progress=p,
                        defaults={
                            "title": mt.title,
                            "description": mt.description or f"Phase {p} for {startup.name}",
                            "status": ms_status,
                            "completed_at": completed_at,
                        }
                    )
                    ms.status = ms_status
                    ms.completed_at = completed_at
                    ms.save()

                    # Instantiate Milestone Readiness
                    for rl_t in mt.rl_templates.all():
                        mr, _ = MilestoneReadiness.objects.get_or_create(
                            milestone=ms,
                            name=rl_t.name
                        )
                        if is_past:
                            mr.incubatee_level = s_data.get(f"{rl_t.name.lower()}_level", "Level 4")
                            mr.admin_level = s_data.get(f"{rl_t.name.lower()}_level", "Level 4")
                            mr.save()

                    # Deliverables
                    for pos, dt in enumerate(mt.deliverable_templates.all()):
                        deliv_status = "approved" if is_past else "pending"
                        deliv, _ = Deliverable.objects.get_or_create(
                            milestone=ms,
                            template=dt,
                            defaults={
                                "position": pos,
                                "name": dt.name,
                                "requirements": dt.requirements or "See template specifications.",
                                "status": deliv_status,
                            }
                        )
                        deliv.status = deliv_status
                        deliv.save()

                        # Instantiate Deliverable Readiness
                        for rl_t in dt.rl_templates.all():
                            r_obj, _ = Readiness.objects.get_or_create(
                                deliverable=deliv,
                                name=rl_t.name
                            )
                            if is_past:
                                r_obj.incubatee_level = s_data.get(f"{rl_t.name.lower()}_level", "Level 3")
                                r_obj.admin_level = s_data.get(f"{rl_t.name.lower()}_level", "Level 3")
                                r_obj.save()

                # 5. Add Sample Progress Report
                rep_data = s_data["report"]
                ProgressReport.objects.get_or_create(
                    startup=startup,
                    title=rep_data["title"],
                    defaults={
                        "submitted_by": founder_user,
                        "description": rep_data["description"],
                        "achievements": rep_data["achievements"],
                        "challenges": rep_data["challenges"],
                        "next_steps": rep_data["next_steps"],
                        "submitted_at": timezone.now() - datetime.timedelta(days=7),
                    }
                )

                self.stdout.write(self.style.SUCCESS(f"Created startup: '{startup.name}' (Founder: {founder_user.username}, +{len(s_data['members'])} members)"))

        self.stdout.write(self.style.SUCCESS("\nAll 4 mockup startups with their members and progression successfully generated!"))


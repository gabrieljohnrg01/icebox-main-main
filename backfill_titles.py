import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from incubator.models import DeliverableFile, DeliverableTemplate, DeliverableTemplateResource
from incubator.views import get_link_title_safe

for f in DeliverableFile.objects.filter(link_url__isnull=False).exclude(link_url=""):
    if not f.link_title:
        title = get_link_title_safe(f.link_url)
        if title:
            f.link_title = title
            f.save()
            print(f"Updated DeliverableFile: {title}")

for t in DeliverableTemplate.objects.filter(admin_link__isnull=False).exclude(admin_link=""):
    if not t.admin_link_title:
        title = get_link_title_safe(t.admin_link)
        if title:
            t.admin_link_title = title
            t.save()
            print(f"Updated DeliverableTemplate: {title}")

for r in DeliverableTemplateResource.objects.filter(link__isnull=False).exclude(link=""):
    if not r.link_title:
        title = get_link_title_safe(r.link)
        if title:
            r.link_title = title
            r.save()
            print(f"Updated DeliverableTemplateResource: {title}")

print("Backfill complete!")

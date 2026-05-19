import os
import re

filepath = 'incubator/views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add get_link_title helper at the top
helper_func = """
import requests
import re
from bs4 import BeautifulSoup

def get_link_title_safe(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, timeout=3, headers=headers)
        if r.status_code == 200:
            match = re.search(r'<title>(.*?)</title>', r.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:490]
    except Exception:
        pass
    return None
"""
if "def get_link_title_safe" not in text:
    # insert after the imports
    text = text.replace("from django.urls import reverse", "from django.urls import reverse" + helper_func)

# 2. Update attach_admin_file (around line 451)
#         link_url = request.POST.get('link_url')
#         if link_url:
#             DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, uploaded_by_role='admin')
old_admin_link = """        link_url = request.POST.get('link_url')
        if link_url:
            DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, uploaded_by_role='admin')"""
new_admin_link = """        link_url = request.POST.get('link_url')
        if link_url:
            link_title = get_link_title_safe(link_url)
            DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, link_title=link_title, uploaded_by_role='admin')"""
text = text.replace(old_admin_link, new_admin_link)

# 3. Update attach_incubatee_file (around line 487)
#         link_url = request.POST.get('link_url')
#         if link_url:
#             DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, uploaded_by_role='incubatee')
old_inc_link = """        link_url = request.POST.get('link_url')
        if link_url:
            DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, uploaded_by_role='incubatee')"""
new_inc_link = """        link_url = request.POST.get('link_url')
        if link_url:
            link_title = get_link_title_safe(link_url)
            DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, link_title=link_title, uploaded_by_role='incubatee')"""
text = text.replace(old_inc_link, new_inc_link)

# 4. In edit_deliverable_page context (around line 845)
#     global_template_link = None
#     if deliverable.template and deliverable.template.admin_link:
#         global_template_link = deliverable.template.admin_link
old_global = """    global_template_link = None
    if deliverable.template and deliverable.template.admin_link:
        global_template_link = deliverable.template.admin_link"""
new_global = """    global_template_link = None
    global_template_link_title = None
    if deliverable.template and deliverable.template.admin_link:
        global_template_link = deliverable.template.admin_link
        global_template_link_title = deliverable.template.admin_link_title or get_link_title_safe(global_template_link)"""
text = text.replace(old_global, new_global)

# Add to context in edit_deliverable_page
old_context = """        'global_template_link': global_template_link,"""
new_context = """        'global_template_link': global_template_link,
        'global_template_link_title': global_template_link_title,"""
text = text.replace(old_context, new_context)

# 5. In add_custom_deliverable / edit templates, we should fetch title
old_dt_link = """        if 'admin_link' in request.POST:
            dt.admin_link = request.POST.get('admin_link')"""
new_dt_link = """        if 'admin_link' in request.POST:
            dt.admin_link = request.POST.get('admin_link')
            if dt.admin_link:
                dt.admin_link_title = get_link_title_safe(dt.admin_link)"""
text = text.replace(old_dt_link, new_dt_link)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

print("views.py updated")

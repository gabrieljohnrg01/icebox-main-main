import os

filepath = 'incubator/views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

old_admin_files = "admin_files = [{'id': f.id, 'url': f.file.url, 'name': f.file.name.split('/')[-1]} for f in d.files.filter(uploaded_by_role='admin') if f.file]"
new_admin_files = "admin_files = [{'id': f.id, 'url': f.file.url if f.file else f.link_url, 'name': f.file.name.split('/')[-1] if f.file else (f.link_title or f.link_url)} for f in d.files.filter(uploaded_by_role='admin') if f.file or f.link_url]"

old_incubatee_files = "incubatee_files = [{'id': f.id, 'url': f.file.url, 'name': f.file.name.split('/')[-1]} for f in d.files.filter(uploaded_by_role='incubatee') if f.file]"
new_incubatee_files = "incubatee_files = [{'id': f.id, 'url': f.file.url if f.file else f.link_url, 'name': f.file.name.split('/')[-1] if f.file else (f.link_title or f.link_url), 'is_text': bool(f.text_content), 'text_content': f.text_content} for f in d.files.filter(uploaded_by_role='incubatee') if f.file or f.link_url or f.text_content]"

text = text.replace(old_admin_files, new_admin_files)
text = text.replace(old_incubatee_files, new_incubatee_files)

# Update global template for view_milestone
old_global = """        global_template_data = None
        if d.template and d.template.admin_file:
            global_template_data = {
                'url': d.template.admin_file.url,
                'name': d.template.admin_file.name.split('/')[-1]
            }"""
new_global = """        global_template_data = None
        if d.template and d.template.admin_file:
            global_template_data = {
                'url': d.template.admin_file.url,
                'name': d.template.admin_file.name.split('/')[-1],
                'type': 'file'
            }
        elif d.template and d.template.admin_link:
            global_template_data = {
                'url': d.template.admin_link,
                'name': d.template.admin_link_title or get_link_title_safe(d.template.admin_link) or d.template.admin_link,
                'type': 'link'
            }"""
text = text.replace(old_global, new_global)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

print("views.py view_milestone updated")

import os

filepath = 'templates/startups/edit_deliverable.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Update global template link display
old_global = """                        <a href="{{ global_template_link }}" target="_blank" class="admin-file-link">
                            <i class="bi bi-link-45deg" style="color: #27ae60;"></i> {{ global_template_link }} (Template Link)
                        </a>"""
new_global = """                        <a href="{{ global_template_link }}" target="_blank" class="admin-file-link">
                            <i class="bi bi-link-45deg" style="color: #27ae60;"></i> {% if global_template_link_title %}{{ global_template_link_title }}{% else %}{{ global_template_link }}{% endif %} (Template Link)
                        </a>"""
text = text.replace(old_global, new_global)

# Update admin files link display
old_admin = """                        {% elif f.link_url %}
                        <a href="{{ f.link_url }}" target="_blank" class="admin-file-link">
                            <i class="bi bi-link-45deg"></i> {{ f.link_url }}
                        </a>"""
new_admin = """                        {% elif f.link_url %}
                        <a href="{{ f.link_url }}" target="_blank" class="admin-file-link">
                            <i class="bi bi-link-45deg"></i> {% if f.link_title %}{{ f.link_title }}{% else %}{{ f.link_url }}{% endif %}
                        </a>"""
text = text.replace(old_admin, new_admin)

# Update incubatee files link display
old_incubatee = """                                    {% elif f.link_url %}
                                        <i class="bi bi-link-45deg"></i>
                                        <a href="{{ f.link_url }}" target="_blank" class="link-text">{{ f.link_url }}</a>"""
new_incubatee = """                                    {% elif f.link_url %}
                                        <i class="bi bi-link-45deg"></i>
                                        <a href="{{ f.link_url }}" target="_blank" class="link-text">{% if f.link_title %}{{ f.link_title }}{% else %}{{ f.link_url }}{% endif %}</a>"""
text = text.replace(old_incubatee, new_incubatee)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

print("edit_deliverable.html updated")

import os

filepath = 'templates/settings/index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the edit form
old_edit_form = """                                    <div class="flex items-center gap-xs justify-between">
                                        <input type="file" name="admin_file" class="form-control" style="font-size:0.7rem; padding: 0.15rem; flex: 1;">
                                        <input type="url" name="admin_link" value="{{ dt.admin_link|default:'' }}" class="form-control" placeholder="Template Link URL..." style="font-size:0.7rem; padding: 0.3rem 0.5rem; flex: 1;">
                                        <button type="submit" class="btn btn-primary" style="font-size: 0.7rem; padding: 0.3rem 0.75rem;">Save</button>
                                    </div>"""

new_edit_form = """                                    <div id="resources-container-{{ dt.id }}" class="flex flex-col gap-xs mt-xs">
                                        {% if dt.admin_file %}
                                        <div class="flex items-center gap-xs">
                                            <span style="font-size:0.7rem; color:var(--text-secondary);"><i class="bi bi-file-earmark"></i> Current File: {{ dt.admin_file.name|slice:"15:" }}</span>
                                        </div>
                                        {% endif %}
                                        {% if dt.admin_link %}
                                        <div class="flex items-center gap-xs">
                                            <span style="font-size:0.7rem; color:var(--text-secondary);"><i class="bi bi-link-45deg"></i> Current Link: <a href="{{ dt.admin_link }}" target="_blank">{{ dt.admin_link }}</a></span>
                                        </div>
                                        {% endif %}
                                        {% for res in dt.resources.all %}
                                        <div class="flex items-center gap-xs">
                                            {% if res.file %}
                                            <span style="font-size:0.7rem; color:var(--text-secondary);"><i class="bi bi-file-earmark"></i> Extra File: {{ res.file.name|slice:"15:" }}</span>
                                            {% elif res.link %}
                                            <span style="font-size:0.7rem; color:var(--text-secondary);"><i class="bi bi-link-45deg"></i> Extra Link: <a href="{{ res.link }}" target="_blank">{{ res.link }}</a></span>
                                            {% endif %}
                                        </div>
                                        {% endfor %}
                                    </div>
                                    <div class="flex justify-between items-center mt-xs">
                                        <div class="relative" style="display:inline-block;">
                                            <button type="button" class="btn btn-ghost" style="font-size:0.7rem; padding:0.2rem 0.5rem; color: var(--accent-color);" onclick="const opts = document.getElementById('add-opts-{{ dt.id }}'); opts.style.display = opts.style.display === 'none' ? 'block' : 'none';">
                                                <i class="bi bi-plus-lg"></i> Add Reference
                                            </button>
                                            <div id="add-opts-{{ dt.id }}" style="display:none; position:absolute; bottom:100%; left:0; background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:4px; z-index:10; padding:4px; margin-bottom: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                                                <button type="button" class="btn btn-ghost" style="display:block; width:100%; text-align:left; font-size:0.7rem; padding:0.3rem 0.8rem; margin-bottom:2px;" onclick="addResourceInput({{ dt.id }}, 'file')"><i class="bi bi-file-earmark-arrow-up" style="color: #2980b9;"></i> File</button>
                                                <button type="button" class="btn btn-ghost" style="display:block; width:100%; text-align:left; font-size:0.7rem; padding:0.3rem 0.8rem;" onclick="addResourceInput({{ dt.id }}, 'link')"><i class="bi bi-link-45deg" style="color: #27ae60;"></i> Link</button>
                                            </div>
                                        </div>
                                        <button type="submit" class="btn btn-primary" style="font-size: 0.7rem; padding: 0.3rem 0.75rem;">Save</button>
                                    </div>"""

text = text.replace(old_edit_form, new_edit_form)

# Add the JS function at the end of the file before endblock
js_code = """
<script>
function addResourceInput(id, type) {
    const container = document.getElementById('resources-container-' + id);
    document.getElementById('add-opts-' + id).style.display = 'none';
    const div = document.createElement('div');
    div.className = 'flex items-center gap-xs mt-xs';
    if (type === 'file') {
        div.innerHTML = '<i class="bi bi-file-earmark-arrow-up" style="color: #2980b9; font-size: 0.9rem;"></i> <input type="file" name="new_files" class="form-control" style="font-size:0.7rem; padding:0.15rem; flex:1;"> <button type="button" onclick="this.parentElement.remove()" class="btn btn-ghost" style="color:var(--danger-color); padding:0.15rem;"><i class="bi bi-x"></i></button>';
    } else {
        div.innerHTML = '<i class="bi bi-link-45deg" style="color: #27ae60; font-size: 0.9rem;"></i> <input type="url" name="new_links" placeholder="https://..." class="form-control" style="font-size:0.7rem; padding:0.3rem 0.5rem; flex:1;"> <button type="button" onclick="this.parentElement.remove()" class="btn btn-ghost" style="color:var(--danger-color); padding:0.15rem;"><i class="bi bi-x"></i></button>';
    }
    container.appendChild(div);
}
</script>
"""

if "function addResourceInput(" not in text:
    text = text.replace("{% endblock %}", js_code + "\n{% endblock %}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated successfully")

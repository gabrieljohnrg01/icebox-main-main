import os

filepath = 'templates/settings/index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

old_add_form = """                            <div class="flex items-center gap-xs">
                                <input type="file" name="admin_file" class="form-control" style="font-size: 0.7rem; padding: 0.15rem 0.5rem; flex: 1;">
                                <input type="url" name="admin_link" class="form-control" placeholder="Template Link URL..." style="font-size: 0.75rem; padding: 0.25rem 0.5rem; flex: 1;">
                                <button type="submit" class="btn btn-primary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">+ Add</button>
                            </div>"""

new_add_form = """                            <div id="resources-container-add-{{ template.id }}" class="flex flex-col gap-xs mt-xs"></div>
                            <div class="flex justify-between items-center mt-xs">
                                <div class="relative" style="display:inline-block;">
                                    <button type="button" class="btn btn-ghost" style="font-size:0.75rem; padding:0.25rem 0.5rem; color: var(--accent-color);" onclick="const opts = document.getElementById('add-opts-add-{{ template.id }}'); opts.style.display = opts.style.display === 'none' ? 'block' : 'none';">
                                        <i class="bi bi-plus-lg"></i> Add Reference
                                    </button>
                                    <div id="add-opts-add-{{ template.id }}" style="display:none; position:absolute; bottom:100%; left:0; background:var(--bg-secondary); border:1px solid var(--border-color); border-radius:4px; z-index:10; padding:4px; margin-bottom: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                                        <button type="button" class="btn btn-ghost" style="display:block; width:100%; text-align:left; font-size:0.75rem; padding:0.3rem 0.8rem; margin-bottom:2px;" onclick="addResourceInput('add-{{ template.id }}', 'file')"><i class="bi bi-file-earmark-arrow-up" style="color: #2980b9;"></i> File</button>
                                        <button type="button" class="btn btn-ghost" style="display:block; width:100%; text-align:left; font-size:0.75rem; padding:0.3rem 0.8rem;" onclick="addResourceInput('add-{{ template.id }}', 'link')"><i class="bi bi-link-45deg" style="color: #27ae60;"></i> Link</button>
                                    </div>
                                </div>
                                <button type="submit" class="btn btn-primary" style="font-size: 0.75rem; padding: 0.25rem 0.75rem;">+ Add Deliverable</button>
                            </div>"""

if old_add_form in text:
    text = text.replace(old_add_form, new_add_form)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated add form UI successfully")
else:
    print("Could not find old add form in text.")

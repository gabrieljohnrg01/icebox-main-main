import os

filepath = 'templates/startups/view.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Change the button
old_button_section = '''                <div class="flex flex-col items-center justify-center relative z-10 flex-shrink-0" style="min-width: 80px;">
                    <form method="post" action="{% url 'add_milestone' startup.id %}" style="display: flex; flex-direction: column; align-items: center;">
                        {% csrf_token %}
                        <button type="submit" style="background: var(--accent-color); border: none; border-radius: 50%; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #fff; box-shadow: 0 8px 18px rgba(0, 0, 0, 0.2); transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Add Custom Milestone">
                            <i class="bi bi-plus-circle" style="font-size: 24px;"></i>
                        </button>
                        <span style="font-size: 0.75rem; color: var(--text-tertiary); font-weight: 700; margin-top: 8px; text-align: center;">Add Custom<br>Milestone</span>
                    </form>
                </div>'''

new_button_section = '''                <div class="flex flex-col items-center justify-center relative z-10 flex-shrink-0" style="min-width: 80px;">
                    <div style="display: flex; flex-direction: column; align-items: center;">
                        <button type="button" onclick="document.getElementById('addCustomMilestoneModal').style.display='flex'" style="background: var(--accent-color); border: none; border-radius: 50%; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #fff; box-shadow: 0 8px 18px rgba(0, 0, 0, 0.2); transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Add Custom Milestone">
                            <i class="bi bi-plus-circle" style="font-size: 24px;"></i>
                        </button>
                        <span style="font-size: 0.75rem; color: var(--text-tertiary); font-weight: 700; margin-top: 8px; text-align: center;">Add Custom<br>Milestone</span>
                    </div>
                </div>'''

text = text.replace(old_button_section, new_button_section)

# 2. Update Milestone card to show title if provided, else Milestone progress
# Currently it uses `Milestone {{ milestone.milestone_progress }}`
# We will use `{{ milestone.title|default:"Milestone "|add:milestone.milestone_progress }}` or just `{{ milestone.title }}`
# Wait, `milestone.title` is always set to `Milestone {next_num}` by default now!
# So we can just use `{{ milestone.title }}`
# We need to replace it in two places (locked and unlocked states)
old_title_tag = 'Milestone {{ milestone.milestone_progress }}'
new_title_tag = '{{ milestone.title }}'
text = text.replace(old_title_tag, new_title_tag)

# 3. Add Modal HTML to the end of the file, just before {% endblock %}
modal_html = '''
    <!-- Add Custom Milestone Modal -->
    <div id="addCustomMilestoneModal" class="modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 2000; align-items: center; justify-content: center; backdrop-filter: blur(2px);">
        <div class="glass-card" style="width: 400px; padding: 24px; position: relative;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0; font-size: 1.25rem;">Add Custom Milestone</h2>
                <button type="button" onclick="document.getElementById('addCustomMilestoneModal').style.display='none'" style="background: none; border: none; cursor: pointer; color: #a0aec0; font-size: 1.5rem; line-height: 1;">&times;</button>
            </div>
            <form action="{% url 'add_milestone' startup.id %}" method="post">
                {% csrf_token %}
                <div style="margin-bottom: 16px;">
                    <label style="font-size:0.85rem; font-weight:500; display:block; margin-bottom:4px;">Milestone Name</label>
                    <input type="text" name="title" class="form-control" placeholder="e.g., Prototype Phase" style="width:100%; font-size:0.85rem; padding:8px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--input-bg); color: var(--text-primary);">
                </div>
                <div style="margin-bottom: 24px;">
                    <label style="font-size:0.85rem; font-weight:500; display:block; margin-bottom:4px;">Number of Deliverables</label>
                    <input type="number" name="deliverable_count" class="form-control" min="0" value="0" style="width:100%; font-size:0.85rem; padding:8px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--input-bg); color: var(--text-primary);">
                </div>
                <div style="display: flex; justify-content: flex-end; gap: 8px;">
                    <button type="button" class="btn" style="background: transparent; color: var(--text-secondary); border: 1px solid var(--border-color);" onclick="document.getElementById('addCustomMilestoneModal').style.display='none'">Cancel</button>
                    <button type="submit" class="btn btn-primary" style="background-color: var(--accent-color); color: white; border: none;">Add Milestone</button>
                </div>
            </form>
        </div>
    </div>
'''

if '<!-- Add Custom Milestone Modal -->' not in text:
    text = text.replace('{% endblock %}', modal_html + '\n{% endblock %}')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

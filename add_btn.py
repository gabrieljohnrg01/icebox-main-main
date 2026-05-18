import os

filepath = 'templates/startups/view_milestone.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Add button
old_loop_end = '''            </div>
            {% endfor %}

        </div>
    </div>'''

new_loop_end = '''            </div>
            {% endfor %}
            
            {% if user.role in "admin,super_admin" and not is_locked %}
            <div style="position:relative; width: 100%; height: 100px;">
                <button type="button" class="add-deliverable-btn" title="Add Custom Deliverable" onclick="document.getElementById('addCustomDeliverableModal').style.display='flex'">
                    <i class="bi bi-plus-circle"></i>
                </button>
                <div class="add-deliverable-text">Add Custom Deliverable</div>
            </div>
            {% endif %}

        </div>
    </div>'''

if old_loop_end in text:
    text = text.replace(old_loop_end, new_loop_end)
else:
    print("Could not find old loop end")

# Add Modal
modal_code = '''
    <!-- Add Custom Deliverable Modal -->
    <div id="addCustomDeliverableModal" class="modal" style="display: none;">
        <div class="modal-content" style="max-width: 400px; padding: 24px;">
            <div class="modal-header">
                <h2>Add Custom Deliverable</h2>
                <button type="button" class="modal-close" onclick="document.getElementById('addCustomDeliverableModal').style.display='none'">&times;</button>
            </div>
            <form action="{% url 'add_custom_deliverable' milestone.id %}" method="post">
                {% csrf_token %}
                <div class="mb-sm" style="margin-bottom: 12px;">
                    <label style="font-size:0.85rem; font-weight:500; display:block; margin-bottom:4px;">Deliverable Name</label>
                    <input type="text" name="name" class="form-control" required placeholder="e.g., Financial Report" style="width:100%; font-size:0.85rem; padding:8px;">
                </div>
                <div class="mb-sm" style="margin-bottom: 12px;">
                    <label style="font-size:0.85rem; font-weight:500; display:block; margin-bottom:4px;">Requirements</label>
                    <textarea name="requirements" class="form-control" rows="3" placeholder="Description of the deliverable..." style="width:100%; font-size:0.85rem; padding:8px; resize:vertical;"></textarea>
                </div>
                <div class="flex justify-end gap-xs" style="margin-top: 16px;">
                    <button type="button" class="btn btn-ghost" onclick="document.getElementById('addCustomDeliverableModal').style.display='none'">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Deliverable</button>
                </div>
            </form>
        </div>
    </div>
'''

if 'id="deliverableModal"' in text:
    text = text.replace('<!-- Deliverable Modal -->', modal_code + '\n    <!-- Deliverable Modal -->')
else:
    print("Could not find deliverableModal")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated view_milestone.html successfully")

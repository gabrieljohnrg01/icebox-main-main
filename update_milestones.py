import os

filepath = 'templates/startups/view.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Make the line white
old_line = '<div class="absolute w-full bg-border" style="height: 4px; top: 3.5rem; left: 0; z-index: 0;"></div>'
new_line = '<div class="absolute w-full" style="height: 4px; top: 3.5rem; left: 0; z-index: 0; background-color: #ffffff;"></div>'
text = text.replace(old_line, new_line)

# Add the button inside the flex container
old_loop_end = '''                {% empty %}
                <div class="glass-card w-full text-center text-muted">No milestones defined yet.</div>
                {% endfor %}
            </div>'''

new_loop_end = '''                {% empty %}
                <div class="glass-card w-full text-center text-muted">No milestones defined yet.</div>
                {% endfor %}
                
                {% if user.role == 'admin' or user.role == 'super_admin' %}
                <div class="flex flex-col items-center justify-center relative z-10" style="min-width: 100px; padding-top: 1.5rem;">
                    <form method="post" action="{% url 'add_milestone' startup.id %}" style="display: flex; align-items: center; justify-content: center; height: 100%;">
                        {% csrf_token %}
                        <button type="submit" class="w-12 h-12 rounded-full border-2 border-white flex items-center justify-center bg-transparent shadow-lg transition-transform" style="cursor: pointer; padding:0;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Add Custom Milestone">
                            <i class="bi bi-plus" style="font-size: 2.2rem; color: white;"></i>
                        </button>
                    </form>
                </div>
                {% endif %}
            </div>'''

text = text.replace(old_loop_end, new_loop_end)

# Remove the old form at the bottom
old_bottom_form = '''        {% if user.role == 'admin' or user.role == 'super_admin' %}
        <div class="flex justify-center mt-md">
            <form method="post" action="{% url 'add_milestone' startup.id %}">
                {% csrf_token %}
                <!-- <button type="submit" class="btn btn-outline border-dashed hover:border-accent">
                    + Add New Milestone
                </button> -->
            </form>
        </div>
        {% endif %}'''

text = text.replace(old_bottom_form, '')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

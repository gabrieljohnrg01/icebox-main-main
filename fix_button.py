import os

filepath = 'templates/startups/view.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Adjust the line position
old_line = '<div class="absolute w-full" style="height: 4px; top: 3.5rem; left: 0; z-index: 0; background-color: #ffffff;"></div>'
new_line = '<div class="absolute w-full" style="height: 4px; top: 68px; left: 0; z-index: 0; background-color: #ffffff;"></div>'
text = text.replace(old_line, new_line)

# Fix the button
old_button_section = '''                {% if user.role == 'admin' or user.role == 'super_admin' %}
                <div class="flex flex-col items-center justify-center relative z-10" style="min-width: 100px; padding-top: 1.5rem;">
                    <form method="post" action="{% url 'add_milestone' startup.id %}" style="display: flex; align-items: center; justify-content: center; height: 100%;">
                        {% csrf_token %}
                        <button type="submit" class="w-12 h-12 rounded-full border-2 border-white flex items-center justify-center bg-transparent shadow-lg transition-transform" style="cursor: pointer; padding:0;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Add Custom Milestone">
                            <i class="bi bi-plus" style="font-size: 2.2rem; color: white;"></i>
                        </button>
                    </form>
                </div>
                {% endif %}'''

new_button_section = '''                {% if user.role == 'admin' or user.role == 'super_admin' %}
                <div class="flex flex-col items-center justify-center relative z-10" style="min-width: 100px;">
                    <form method="post" action="{% url 'add_milestone' startup.id %}" style="display: flex; align-items: center; justify-content: center; height: 100%;">
                        {% csrf_token %}
                        <button type="submit" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid white; background: transparent !important; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Add Custom Milestone">
                            <i class="bi bi-plus" style="font-size: 2rem; color: white; line-height: 0;"></i>
                        </button>
                    </form>
                </div>
                {% endif %}'''

text = text.replace(old_button_section, new_button_section)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

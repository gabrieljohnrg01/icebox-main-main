import os

filepath = 'templates/startups/view.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove the old line
old_line_html = '''        <div class="relative py-lg overflow-x-auto">
            <!-- Connecting Line -->
            <div class="absolute w-full" style="height: 4px; top: 5.5rem; left: 0; z-index: 0; background-color: #ffffff;"></div>

            <div class="flex justify-between gap-lg dcss" style="min-width: 600px;">'''

new_line_html = '''        <div class="relative py-lg overflow-x-auto">
            <div class="flex justify-between gap-lg dcss" style="min-width: 600px; position: relative;">
                <!-- Connecting Line -->
                <div class="absolute w-full" style="height: 4px; top: 44px; left: 0; z-index: 0; background-color: #ffffff;"></div>'''

text = text.replace(old_line_html, new_line_html)

# 2. Fix the button alignment
old_button_section = '''                {% if user.role == 'admin' or user.role == 'super_admin' %}
                <div class="flex flex-col items-center relative z-10" style="min-width: 100px; padding-top: 1rem;">
                    <form method="post" action="{% url 'add_milestone' startup.id %}" style="display: flex; justify-content: center;">
                        {% csrf_token %}
                        <button type="submit" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid white; background: transparent !important; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Add Custom Milestone">
                            <i class="bi bi-plus" style="font-size: 2rem; color: white; line-height: 0; margin-top:2px;"></i>
                        </button>
                    </form>
                </div>
                {% endif %}'''

new_button_section = '''                {% if user.role == 'admin' or user.role == 'super_admin' %}
                <div class="flex flex-col items-center relative z-10" style="min-width: 100px; padding-top: 20px;">
                    <form method="post" action="{% url 'add_milestone' startup.id %}" style="display: flex; justify-content: center;">
                        {% csrf_token %}
                        <button type="submit" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid white; background: transparent !important; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Add Custom Milestone">
                            <i class="bi bi-plus" style="font-size: 2rem; color: white; line-height: 0; margin-top:2px;"></i>
                        </button>
                    </form>
                </div>
                {% endif %}'''

text = text.replace(old_button_section, new_button_section)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

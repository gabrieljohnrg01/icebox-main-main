import os

filepath = 'templates/startups/view.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Remove the absolute progress bar
progress_bar_str = '''            <!-- Progress Bar Background Track -->
            <div class="absolute w-full" style="height: 6px; top: 167px; left: 0; z-index: 0; background-color: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                <!-- Filled Progress -->
                <div style="height: 100%; width: {{ startup.progress }}%; background-color: var(--accent-color); border-radius: 3px; transition: width 0.8s ease;"></div>
            </div>'''
text = text.replace(progress_bar_str, '')

# Now replace the flex container and its contents
import re

start_marker = r'<div class="flex justify-between gap-lg dcss" style="min-width: 600px;">'
end_marker = r'{% empty %}'

# We need to construct the new content.
new_content = '''<div class="flex items-center" style="min-width: 600px; padding: 1rem 0;">
                {% for milestone in milestones %}
                <div class="flex flex-col items-center relative z-10 w-[240px] flex-shrink-0">
                    <!-- Card -->
                    {% if milestone.is_locked and user.role != 'admin' and user.role != 'super_admin' %}
                    <div class="glass-card p-md w-full text-center opacity-50 cursor-not-allowed relative" style="transition: all 0.3s ease;">
                        <div class="absolute inset-0 flex items-center justify-center">
                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-accent">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                            </svg>
                        </div>
                        <div class="mb-xs flex items-center justify-center">
                            <div class="w-10 h-10 rounded-full flex items-center justify-center border-4 shadow-lg bg-secondary text-white">
                                🔒
                            </div>
                        </div>
                        <div class="font-bold text-primary mb-xs">
                            Milestone {{ milestone.milestone_progress }}
                        </div>
                        <ul class="text-sm text-muted text-left list-disc list-inside space-y-1">
                            {% if milestone.deliverables.first %}
                            <li>{{ milestone.deliverables.first.name }}</li>
                            {% endif %}
                        </ul>
                        <div class="mt-xs text-left" style="width: 100%;">
                            <div class="flex justify-between text-xs mb-1">
                                <span class="text-muted">Progress</span>
                                <span class="font-bold text-accent">{{ milestone.progress_percentage }}%</span>
                            </div>
                            <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                                <div style="height: 100%; width: {{ milestone.progress_percentage }}%; background: var(--accent-color); border-radius: 3px; transition: width 0.5s ease;"></div>
                            </div>
                        </div>
                        <div class="text-xs text-accent font-semibold mt-md">Complete previous milestone to unlock</div>
                    </div>
                    {% else %}
                    <a href="{% url 'view_milestone' startup.id milestone.id %}" class="glass-card p-md w-full text-center hover:border-accent transition-colors cursor-pointer" style="transition: all 0.3s ease; {% if milestone.status == 'completed' %}border: 1px solid var(--success-color); box-shadow: 0 0 15px rgba(34,197,94,0.3);{% endif %}">
                        <div class="mb-xs flex items-center justify-center">
                            <div class="w-10 h-10 rounded-full flex items-center justify-center border-4 shadow-lg {% if milestone.status == 'completed' %}bg-success text-white{% elif milestone.id == current_milestone_id %}bg-warning text-black{% else %}bg-secondary text-white{% endif %}">
                                {% if milestone.status == 'completed' %}
                                ✓
                                {% elif milestone.id == current_milestone_id %}
                                ⏳
                                {% else %}
                                🔒
                                {% endif %}
                            </div>
                        </div>
                        <div class="font-bold text-primary mb-xs">
                            Milestone {{ milestone.milestone_progress }}
                        </div>
                        <ul class="text-sm text-muted text-left list-disc list-inside space-y-1">
                            {% if milestone.deliverables.first %}
                            <li>{{ milestone.deliverables.first.name }}</li>
                            {% endif %}
                        </ul>
                        <div class="mt-xs text-left" style="width: 100%;">
                            <div class="flex justify-between text-xs mb-1">
                                <span class="text-muted">Progress</span>
                                <span class="font-bold text-accent">{{ milestone.progress_percentage }}%</span>
                            </div>
                            <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                                <div style="height: 100%; width: {{ milestone.progress_percentage }}%; background: var(--accent-color); border-radius: 3px; transition: width 0.5s ease;"></div>
                            </div>
                        </div>
                    </a>
                    {% endif %}
                </div>

                {% if not forloop.last %}
                <!-- Connecting Line -->
                <div class="flex-1 mx-sm rounded-full" style="height: 6px; min-width: 30px; background-color: {% if milestone.status == 'completed' %}var(--success-color){% else %}rgba(255,255,255,0.1){% endif %}; box-shadow: {% if milestone.status == 'completed' %}0 0 8px rgba(34,197,94,0.5){% else %}none{% endif %}; transition: all 0.3s ease;"></div>
                {% endif %}
                
                {% if forloop.last and (user.role == 'admin' or user.role == 'super_admin') %}
                <!-- Connecting Line to Add Button -->
                <div class="flex-1 mx-sm rounded-full" style="height: 6px; min-width: 30px; background-color: {% if milestone.status == 'completed' %}var(--success-color){% else %}rgba(255,255,255,0.1){% endif %}; box-shadow: {% if milestone.status == 'completed' %}0 0 8px rgba(34,197,94,0.5){% else %}none{% endif %}; transition: all 0.3s ease;"></div>
                {% endif %}

                {% empty %}'''

# Use regex to replace everything between start_marker and end_marker
pattern = re.compile(re.escape(start_marker) + r'.*?' + re.escape(end_marker), re.DOTALL)
text = pattern.sub(new_content, text)

# Now fix the add button part. It currently has an empty block followed by the button logic.
# Wait, the add button logic was outside the for loop!
# Let's see the original structure:
# {% empty %} ... {% endfor %}
# {% if user.role == 'admin' ... %} ... {% endif %}
# </div> (closes the flex container)

# Since we injected the line to the add button inside the forloop (using forloop.last), we just need to adapt the Add Button wrapper.
old_add_button = '''                {% if user.role == 'admin' or user.role == 'super_admin' %}
                <div class="flex flex-col items-center relative z-10" style="min-width: 100px; padding-top: 24px;">
                    <form method="post" action="{% url 'add_milestone' startup.id %}" style="display: flex; justify-content: center;">
                        {% csrf_token %}
                        <button type="submit" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid white; background: transparent !important; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Add Custom Milestone">
                            <i class="bi bi-plus" style="font-size: 2rem; color: white; line-height: 0; margin-top:2px;"></i>
                        </button>
                    </form>
                </div>
                {% endif %}
            </div>'''

new_add_button = '''                {% if user.role == 'admin' or user.role == 'super_admin' %}
                <div class="flex flex-col items-center relative z-10 flex-shrink-0" style="min-width: 60px;">
                    <form method="post" action="{% url 'add_milestone' startup.id %}" style="display: flex; justify-content: center;">
                        {% csrf_token %}
                        <button type="submit" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid white; background: transparent !important; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" title="Add Custom Milestone">
                            <i class="bi bi-plus" style="font-size: 2rem; color: white; line-height: 0; margin-top:2px;"></i>
                        </button>
                    </form>
                </div>
                {% endif %}
            </div>'''

text = text.replace(old_add_button, new_add_button)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

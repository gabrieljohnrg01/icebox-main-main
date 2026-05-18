import os
import re

filepath = 'templates/startups/view_milestone.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove .timeline::before
css_before = '''    .timeline::before {
        content: '';
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        width: 4px;
        height: 100%;
        background: var(--border-color);
        top: 0;
        border-radius: 4px;
    }'''
text = text.replace(css_before, '')

# Also remove the media query override if it exists
css_before_media = '''        .timeline::before {
            left: 20px;
        }'''
text = text.replace(css_before_media, '')

# Add the new .timeline-line CSS inside the style tag
style_search = '</style>'
timeline_line_css = '''
    .timeline-line {
        position: absolute;
        left: 50%;
        top: 46px;
        width: 4px;
        height: 100%;
        transform: translateX(-50%);
        background: var(--border-color);
        z-index: 0;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    .timeline-line.completed {
        background: var(--success-color);
        box-shadow: 0 0 8px rgba(34,197,94,0.5);
    }
    
    @media (max-width: 900px) {
        .timeline-line {
            left: 20px;
        }
    }
</style>'''
text = text.replace(style_search, timeline_line_css, 1)

# 2. Modify the HTML loop
loop_start = r'{% for d in deliverables_data %}'
loop_end = r'{% endfor %}'

old_loop_pattern = re.compile(re.escape(loop_start) + r'.*?' + re.escape(loop_end), re.DOTALL)

new_loop = '''{% for d in deliverables_data %}
            <div class="timeline-item" data-id="{{ d.obj.id }}" data-name="{{ d.obj.name }}"
                data-status="{{ d.obj.status }}" data-reqs="{{ d.obj.requirements|escapejs }}"
                data-due="{{ d.obj.due_date|date:'Y-m-d'|default:'' }}" data-admin-files="{{ d.admin_files_json }}"
                data-incubatee-files="{{ d.incubatee_files_json }}" data-rls="{{ d.rls_json }}"
                data-global-template="{{ d.global_template_file_json }}"
                data-comments="{{ d.comments_json }}" onclick="window.location.href='{% url 'edit_deliverable_page' d.obj.id %}'"
                style="cursor: pointer;">
                
                <!-- Connecting Line -->
                {% if not forloop.last %}
                <div class="timeline-line {% if d.obj.status == 'approved' %}completed{% endif %}"></div>
                {% else %}
                    {% if user.role in "admin,super_admin" and not is_locked %}
                    <div class="timeline-line {% if d.obj.status == 'approved' %}completed{% endif %}" style="height: calc(100% + 40px);"></div>
                    {% endif %}
                {% endif %}

                <div class="timeline-dot {% if d.obj.status == 'approved' %}completed{% elif d.obj.status == 'submitted' %}pending{% elif d.obj.status == 'rejected' %}rejected{% else %}not-started{% endif %}">
                    {% if d.obj.status == 'approved' %}
                    <i class="bi bi-check-circle-fill"></i>
                    {% elif d.obj.status == 'submitted' %}
                    <i class="bi bi-clock-fill"></i>
                    {% elif d.obj.status == 'rejected' %}
                    <i class="bi bi-arrow-counterclockwise"></i>
                    {% else %}
                    <i class="bi bi-clock"></i>
                    {% endif %}
                </div>
                <div class="timeline-content" style="transition: all 0.3s ease; {% if d.obj.status == 'approved' %}border: 1px solid var(--success-color); box-shadow: 0 0 15px rgba(34,197,94,0.3);{% endif %}">
                    <div class="timeline-date">
                        {% if d.obj.due_date %}
                        {{ d.obj.due_date|date:"M d, Y" }}
                        {% else %}
                        No Due Date
                        {% endif %}
                    </div>
                    <p class="timeline-name">• {{ d.obj.name }}</p>
                </div>
            </div>
            {% endfor %}'''

text = old_loop_pattern.sub(new_loop, text)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

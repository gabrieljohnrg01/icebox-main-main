import os
import re

filepath = 'templates/startups/view.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove justify-between from flex container
old_container = '<div class="flex items-center w-full justify-between" style="min-width: 600px; padding: 1rem 0;">'
new_container = '<div class="flex items-center w-full" style="min-width: 600px; padding: 1rem 0;">'
text = text.replace(old_container, new_container)

# 2. Add flex-grow: 1 to the lines explicitly
# We need to find the lines and replace them.
# The lines are currently:
# <div class="flex-1 mx-sm rounded-full" style="height: 6px; min-width: 30px; background-color: {% if milestone.status == 'completed' %}var(--success-color){% else %}rgba(255,255,255,0.1){% endif %}; box-shadow: {% if milestone.status == 'completed' %}0 0 8px rgba(34,197,94,0.5){% else %}none{% endif %}; transition: all 0.3s ease;"></div>

line_pattern = re.compile(r'<div class="flex-1 mx-sm rounded-full" style="height: 6px; min-width: 30px;')
text = line_pattern.sub('<div class="mx-md rounded-full" style="flex: 1; height: 6px; min-width: 30px;', text)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

import os

filepath = 'templates/startups/view.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the progress bar top position
old_html = '''        <div class="relative py-lg overflow-x-auto">
            <!-- Progress Bar Background Track -->
            <div class="absolute w-full" style="height: 6px; top: 123px; left: 0; z-index: 0; background-color: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">'''

new_html = '''        <div class="relative py-lg overflow-x-auto">
            <!-- Progress Bar Background Track -->
            <div class="absolute w-full" style="height: 6px; top: 172px; left: 0; z-index: 0; background-color: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">'''

text = text.replace(old_html, new_html)

# Adjust button padding
old_button_section = '''                {% if user.role == 'admin' or user.role == 'super_admin' %}
                <div class="flex flex-col items-center relative z-10" style="min-width: 100px; padding-top: 12px;">'''

new_button_section = '''                {% if user.role == 'admin' or user.role == 'super_admin' %}
                <div class="flex flex-col items-center relative z-10" style="min-width: 100px; padding-top: 24px;">'''

text = text.replace(old_button_section, new_button_section)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

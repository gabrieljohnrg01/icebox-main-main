import os

filepath = 'templates/startups/view.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

old_html = '''        <div class="relative py-lg overflow-x-auto">
            <!-- Connecting Line -->
            <div class="absolute w-full" style="height: 4px; top: 124px; left: 0; z-index: 0; background-color: #ffffff;"></div>'''

new_html = '''        <div class="relative py-lg overflow-x-auto">
            <!-- Progress Bar Background Track -->
            <div class="absolute w-full" style="height: 6px; top: 123px; left: 0; z-index: 0; background-color: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                <!-- Filled Progress -->
                <div style="height: 100%; width: {{ startup.progress }}%; background-color: var(--accent-color); border-radius: 3px; transition: width 0.8s ease;"></div>
            </div>'''

text = text.replace(old_html, new_html)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

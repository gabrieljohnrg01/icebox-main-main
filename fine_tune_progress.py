import os

filepath = 'templates/startups/view.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('top: 172px;', 'top: 167px;')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

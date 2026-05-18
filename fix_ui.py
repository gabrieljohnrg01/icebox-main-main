import os

filepath = 'templates/settings/index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix placeholders for Edit form
old_inputs = '''                                        <input type="text" name="name" value="{{ dt.name }}" class="form-control" style="font-size:0.75rem; padding: 0.3rem 0.5rem; flex: 1;" required>
                                        <input type="text" name="requirements" value="{{ dt.requirements|default:'' }}" class="form-control" style="font-size:0.75rem; padding: 0.3rem 0.5rem; flex: 2;">'''
new_inputs = '''                                        <input type="text" name="name" value="{{ dt.name }}" class="form-control" placeholder="Deliverable Name" style="font-size:0.75rem; padding: 0.3rem 0.5rem; flex: 1;" required>
                                        <input type="text" name="requirements" value="{{ dt.requirements|default:'' }}" class="form-control" placeholder="Deliverable Requirements" style="font-size:0.75rem; padding: 0.3rem 0.5rem; flex: 2;">'''
text = text.replace(old_inputs, new_inputs)

# Fix relative positioning and dropdown placement for Edit form
text = text.replace(
    '<div class="relative" style="display:inline-block;">',
    '<div style="position:relative; display:inline-block;">'
)
text = text.replace(
    'bottom:100%; left:0;',
    'top:100%; left:0; margin-top: 4px;'
)
text = text.replace(
    'margin-bottom: 4px; box-shadow',
    'box-shadow'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated index.html successfully")

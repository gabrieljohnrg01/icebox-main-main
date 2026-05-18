import os

file_path = "templates/settings/index.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We know the markers.
# 1. Start of grid
start_marker = "    <!-- User Profile Picture -->"
# 2. Block B (Change Password)
b_start = "    <!-- User preferences (Password) -->"
b_end = "    {% if user.role == 'super_admin' %}"
# 3. Block C (Cohorts)
c_start = "    {% if user.role == 'super_admin' %}"
c_end = "    {% if is_admin %}"
# 4. Block D (Global Templates)
d_start = "    {% if is_admin %}"
d_end = "</div>\n\n<!-- Styles for forms matching the theme -->"

idx_start = content.find(start_marker)
idx_b_start = content.find(b_start)
idx_c_start = content.find(c_start)
idx_d_start = content.find(d_start)
idx_d_end = content.find(d_end)

if idx_start == -1 or idx_b_start == -1 or idx_c_start == -1 or idx_d_start == -1 or idx_d_end == -1:
    print("Could not find markers")
    exit(1)

block_a = content[idx_start:idx_b_start]
block_b = content[idx_b_start:idx_c_start]
block_c = content[idx_c_start:idx_d_start]
block_d = content[idx_d_start:idx_d_end]

# Clean up styling of individual blocks to fit the grid:
block_b = block_b.replace('margin-bottom: 1.25rem;', '')
block_c = block_c.replace('border-top: 1px solid var(--border-color); padding-top: 1.25rem; margin-bottom: 1.25rem;', '')
block_d = block_d.replace('border-top: 1px solid var(--border-color); padding-top: 1.25rem;', '')

new_content = content[:idx_start] + """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 2.5rem; align-items: start;">
        <!-- Left Column -->
        <div style="display: flex; flex-direction: column; gap: 0rem;">
""" + block_a + block_c + """
        </div>

        <!-- Right Column -->
        <div style="display: flex; flex-direction: column; gap: 0rem;">
""" + block_b + block_d + """
        </div>
    </div>
""" + content[idx_d_end:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Restructured layout successfully")

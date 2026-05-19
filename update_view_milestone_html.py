import os

filepath = 'templates/startups/view_milestone.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

old_upload = """                    uploadFiles.forEach(f => {
                        htmlBuilder += `<li data-file-id="${f.id}" style="margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
                             <a href="${f.url}" target="_blank" rel="noopener" style="word-break: break-all; margin-right: 10px;">📎 ${f.name}</a>`;
                        if ("{{ user.role }}" === "incubatee" || "{{ user.role }}" === "admin" || "{{ user.role }}" === "super_admin") {"""

new_upload = """                    uploadFiles.forEach(f => {
                        let linkHtml = '';
                        if (f.is_text) {
                            let safeText = '';
                            if (f.text_content) {
                                safeText = f.text_content.replace(/"/g, '&quot;').replace(/\\n/g, '\\\\n');
                            }
                            linkHtml = `<a href="javascript:void(0)" onclick="alert('Text Submission:\\\\n\\\\n' + decodeURIComponent('${encodeURIComponent(f.text_content || '')}'))" style="word-break: break-all; margin-right: 10px;">📝 Text Submission</a>`;
                        } else if (f.url && f.url.startsWith('http')) {
                            linkHtml = `<a href="${f.url}" target="_blank" rel="noopener" style="word-break: break-all; margin-right: 10px;">🔗 ${f.name}</a>`;
                        } else {
                            linkHtml = `<a href="${f.url}" target="_blank" rel="noopener" style="word-break: break-all; margin-right: 10px;">📎 ${f.name}</a>`;
                        }
                        
                        htmlBuilder += `<li data-file-id="${f.id}" style="margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
                             ${linkHtml}`;
                        if ("{{ user.role }}" === "incubatee" || "{{ user.role }}" === "admin" || "{{ user.role }}" === "super_admin") {"""

text = text.replace(old_upload, new_upload)

old_admin = """                    adminFiles.forEach(f => {
                        htmlBuilder += `<li data-file-id="${f.id}" style="margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
                             <a href="${f.url}" target="_blank" rel="noopener" style="word-break: break-all; margin-right: 10px;">📄 ${f.name}</a>`;"""

new_admin = """                    adminFiles.forEach(f => {
                        let linkHtml = '';
                        if (f.url && f.url.startsWith('http') && !f.url.includes('/media/')) {
                            linkHtml = `<a href="${f.url}" target="_blank" rel="noopener" style="word-break: break-all; margin-right: 10px;">🔗 ${f.name}</a>`;
                        } else {
                            linkHtml = `<a href="${f.url}" target="_blank" rel="noopener" style="word-break: break-all; margin-right: 10px;">📄 ${f.name}</a>`;
                        }
                        htmlBuilder += `<li data-file-id="${f.id}" style="margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
                             ${linkHtml}`;"""

text = text.replace(old_admin, new_admin)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

print("view_milestone.html updated")

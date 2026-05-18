import os

filepath = 'incubator/views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

old_redirect = '''                messages.success(request, f'Member {first_name} added! Username: {username}')
                return redirect('add_member', startup_id=startup.id)
            except Exception as e:'''

new_redirect = '''                messages.success(request, f'Member {first_name} added! Username: {username}')
                if request.POST.get('action') == 'save_and_view':
                    return redirect('view_startup', startup_id=startup.id)
                return redirect('add_member', startup_id=startup.id)
            except Exception as e:'''

text = text.replace(old_redirect, new_redirect)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done views.py")

filepath_html = 'templates/startups/add_member.html'
with open(filepath_html, 'r', encoding='utf-8') as f:
    text_html = f.read()

old_buttons = '''                <div class="flex items-center justify-between gap-md mt-lg pt-md border-t border-glass">
                    <a href="{% url 'view_startup' startup.id %}" class="btn btn-ghost">Add Member & View Startup</a>
                    <button type="submit" class="btn btn-primary">Add Member & Add Another</button>
                </div>'''

new_buttons = '''                <div class="flex items-center justify-between gap-md mt-lg pt-md border-t border-glass">
                    <button type="submit" name="action" value="save_and_view" class="btn btn-ghost">Add Member & View Startup</button>
                    <button type="submit" name="action" value="save_and_add_another" class="btn btn-primary">Add Member & Add Another</button>
                </div>'''

text_html = text_html.replace(old_buttons, new_buttons)

with open(filepath_html, 'w', encoding='utf-8') as f:
    f.write(text_html)
print("Done add_member.html")

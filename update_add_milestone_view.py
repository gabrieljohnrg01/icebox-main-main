import os
import re

filepath = 'incubator/views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

old_func = '''@login_required
def add_milestone(request, startup_id):
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')
    
    startup = get_object_or_404(Startup, id=startup_id)
    if request.method == 'POST':
        # Calculate next milestone number
        last_milestone = startup.milestones.order_by('-milestone_progress').first()
        next_num = (last_milestone.milestone_progress + 1) if last_milestone else 1
        
        Milestone.objects.create(
            startup=startup,
            milestone_progress=next_num,
            title=f"Milestone {next_num}",
            description="New added milestone",
            status='pending'
        )
        messages.success(request, f'Milestone {next_num} added!')
    
    return redirect('view_startup', startup_id=startup.id)'''

new_func = '''@login_required
def add_milestone(request, startup_id):
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')
    
    startup = get_object_or_404(Startup, id=startup_id)
    if request.method == 'POST':
        # Calculate next milestone number
        last_milestone = startup.milestones.order_by('-milestone_progress').first()
        next_num = (last_milestone.milestone_progress + 1) if last_milestone else 1
        
        title = request.POST.get('title', f"Milestone {next_num}")
        deliverable_count = int(request.POST.get('deliverable_count', 0))
        
        m = Milestone.objects.create(
            startup=startup,
            milestone_progress=next_num,
            title=title,
            description="New added milestone",
            status='pending'
        )
        
        for i in range(1, deliverable_count + 1):
            Deliverable.objects.create(
                milestone=m,
                name=f"Deliverable {i}",
                status='pending'
            )
            
        messages.success(request, f'Milestone {next_num} added!')
    
    return redirect('view_startup', startup_id=startup.id)'''

text = text.replace(old_func, new_func)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import User, Startup, StartupMember, ProgressReport, Milestone, Deliverable, DeliverableFile, Readiness, Comment, Notification, MilestoneTemplate, DeliverableTemplate, FBAnnouncement, Cohort, RLTemplate, RLTemplateLevel
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import translation
from django.conf import settings
from .forms import LoginForm, StartupForm, AdminCreationForm, ProgressReportForm, StartupMemberForm
from django.db.models import Count, Exists, OuterRef, Prefetch, Max, Q
from django.shortcuts import HttpResponse
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
import requests
import re
from bs4 import BeautifulSoup
import csv
import base64
import os
from django.conf import settings

def _get_img_src(request, rel_url, for_pdf=False):
    try:
        if for_pdf:
            rel = rel_url.lstrip('/')
            return os.path.join(settings.BASE_DIR, rel)
        else:
            if not rel_url.startswith('/'): rel_url = '/' + rel_url
            return request.build_absolute_uri(rel_url)
    except Exception:
        return ""

def get_link_title_safe(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, timeout=3, headers=headers)
        if r.status_code == 200:
            match = re.search(r'<title>(.*?)</title>', r.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:490]
    except Exception:
        pass
    return None


from django.urls import reverse
import requests
import re
from bs4 import BeautifulSoup

def get_link_title_safe(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, timeout=3, headers=headers)
        if r.status_code == 200:
            match = re.search(r'<title>(.*?)</title>', r.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:490]
    except Exception:
        pass
    return None

import json
from .email_utils import send_deliverable_status_email

def csrf_failure(request, reason=""):
    """Handle CSRF failures gracefully"""
    return render(request, 'csrf_error.html', {'reason': reason}, status=403)

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Check for passwordless login first
            user_obj = User.objects.filter(username=username).first()
            if not user_obj:
               user_obj = User.objects.filter(email=username).first()
            
            if user_obj and not user_obj.has_usable_password() and not password:
                login(request, user_obj)
                return redirect('dashboard')

            user = authenticate(request, username=username, password=password)
            if user is None:
                # Try finding user by email
                try:
                    user_obj = User.objects.filter(email=username).first()
                    if user_obj:
                        user = authenticate(request, username=user_obj.username, password=password)
                except:
                    pass
            
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username/email or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard(request):
    user = request.user
    if user.role == 'super_admin':
        return super_admin_dashboard(request)
    elif user.role == 'admin':
        return admin_dashboard(request)
    else:
        return incubatee_dashboard(request)

def super_admin_dashboard(request):
    admins = User.objects.filter(role='admin')
    incubatees = User.objects.filter(role='incubatee')
    startups = Startup.objects.select_related('owner').prefetch_related(
        'milestones',
    ).annotate(
        members_count=Count('startupmember')
    )
    
    # Compute the current active milestone for each startup
    for startup in startups:
        startup.current_milestone = None
        for milestone in startup.milestones.all().order_by('milestone_progress'):
            if milestone.status != 'completed' and not milestone.is_locked():
                startup.current_milestone = milestone
                break
    
    # Get upcoming deliverable dates and details for the right-hand widget
    all_deliverables_qs = Deliverable.objects.filter(due_date__isnull=False).exclude(status='approved').select_related('milestone__startup').order_by('due_date')
    
    deliverable_dates_dict = {}
    for d in all_deliverables_qs:
        date_str = d.due_date.strftime('%Y-%m-%d')
        milestone_label = d.milestone.title or f"Milestone {d.milestone.milestone_progress or ''}".strip()
        detail_string = f"• {d.milestone.startup.name}: {d.name} ({milestone_label})"
        if date_str not in deliverable_dates_dict:
            deliverable_dates_dict[date_str] = []
        deliverable_dates_dict[date_str].append(detail_string)
        
    for date_str in deliverable_dates_dict:
        deliverable_dates_dict[date_str] = "\n".join(deliverable_dates_dict[date_str])

    upcoming_deliverables = []
    today = timezone.localdate()
    for d in all_deliverables_qs[:5]:
        milestone_label = d.milestone.title or f"Milestone {d.milestone.milestone_progress or ''}".strip()
        due_date = d.due_date
        delta_days = (due_date - today).days
        if delta_days < 0:
            due_label = 'overdue'
        elif delta_days == 0:
            due_label = 'today'
        elif delta_days == 1:
            due_label = 'tomorrow'
        else:
            due_label = f'in {delta_days} days'

        announcement_text = (
            f"{d.milestone.startup.name}'s {milestone_label} deliverable '{d.name}' "
            f"is due {due_label}."
        )

        upcoming_deliverables.append({
            'due_date': due_date.strftime('%b %d'),
            'deliverable_name': d.name,
            'milestone_name': milestone_label,
            'startup_name': d.milestone.startup.name,
            'due_date_full': due_date.strftime('%Y-%m-%d'),
            'announcement_text': announcement_text,
        })
    
    context = {
        'admins': admins,
        'incubatees': incubatees,
        'startups': startups,
        'total_startups': startups.count(),
        'total_admins': admins.count(),
        'total_users': User.objects.count(),
        'deliverable_dates': json.dumps(deliverable_dates_dict),
        'upcoming_deliverables': upcoming_deliverables,
        'fb_announcements': FBAnnouncement.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/super_admin.html', context)

def admin_dashboard(request):
    startups = Startup.objects.select_related('owner').prefetch_related(
        'milestones',
    ).annotate(
        members_count=Count('startupmember')
    )
    
    # Compute the current active milestone for each startup
    for startup in startups:
        startup.current_milestone = None
        for milestone in startup.milestones.all().order_by('milestone_progress'):
            if milestone.status != 'completed' and not milestone.is_locked():
                startup.current_milestone = milestone
                break
    recent_reports = ProgressReport.objects.select_related('startup', 'submitted_by').order_by('-submitted_at')[:10]

    # Get upcoming deliverable dates and announcement data
    all_deliverables_qs = Deliverable.objects.filter(due_date__isnull=False).exclude(status='approved').select_related('milestone__startup').order_by('due_date')
    
    deliverable_dates_dict = {}
    for d in all_deliverables_qs:
        date_str = d.due_date.strftime('%Y-%m-%d')
        milestone_label = d.milestone.title or f"Milestone {d.milestone.milestone_progress or ''}".strip()
        detail_string = f"• {d.milestone.startup.name}: {d.name} ({milestone_label})"
        if date_str not in deliverable_dates_dict:
            deliverable_dates_dict[date_str] = []
        deliverable_dates_dict[date_str].append(detail_string)
        
    for date_str in deliverable_dates_dict:
        deliverable_dates_dict[date_str] = "\n".join(deliverable_dates_dict[date_str])

    upcoming_deliverables = []
    today = timezone.localdate()
    for d in all_deliverables_qs[:5]:
        milestone_label = d.milestone.title or f"Milestone {d.milestone.milestone_progress or ''}".strip()
        due_date = d.due_date
        delta_days = (due_date - today).days
        if delta_days < 0:
            due_label = 'overdue'
        elif delta_days == 0:
            due_label = 'today'
        elif delta_days == 1:
            due_label = 'tomorrow'
        else:
            due_label = f'in {delta_days} days'

        announcement_text = (
            f"{d.milestone.startup.name}'s {milestone_label} deliverable '{d.name}' "
            f"is due {due_label}."
        )

        upcoming_deliverables.append({
            'due_date': due_date.strftime('%b %d'),
            'deliverable_name': d.name,
            'milestone_name': milestone_label,
            'startup_name': d.milestone.startup.name,
            'due_date_full': due_date.strftime('%Y-%m-%d'),
            'announcement_text': announcement_text,
        })
    
    context = {
        'startups': startups, 
        'recent_reports': recent_reports,
        'total_startups': startups.count(),
        'total_users': User.objects.count(),
        'deliverable_dates': json.dumps(deliverable_dates_dict),
        'upcoming_deliverables': upcoming_deliverables,
        'fb_announcements': FBAnnouncement.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/admin.html', context)

def incubatee_dashboard(request):
    startups = request.user.startups.prefetch_related('milestones__deliverables').all()

    # Pre-calculate current milestone for each startup
    for startup in startups:
        startup.current_milestone = None
        for milestone in startup.milestones.all().order_by('milestone_progress'):
            if milestone.status != 'completed' and not milestone.is_locked():
                startup.current_milestone = milestone
                break

    if startups.count() == 1:
        return redirect('view_startup', startup_id=startups.first().id)

    context = {'startups': startups}
    return render(request, 'dashboard/incubatee.html', context)

@login_required
def add_admin(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            admin_user = form.save(commit=False)
            admin_user.created_by = request.user
            admin_user.save()
            messages.success(request, f'Admin {admin_user.username} created!')
            return redirect('dashboard')
    else:
        form = AdminCreationForm()
    return render(request, 'super_admin/add_admin.html', {'form': form})

@login_required
def delete_user(request, user_id):
    # Allow Super Admin and Admin to access
    if request.user.role not in ['super_admin', 'admin']:
        return redirect('dashboard')
        
    target_user = get_object_or_404(User, id=user_id)
    
    # Protections
    if target_user.role == 'super_admin':
        messages.error(request, 'Cannot delete Super Admin.')
        return redirect('dashboard')
        
    if request.user.role == 'admin':
        # Admin can ONLY delete Incubatees
        if target_user.role != 'incubatee':
            messages.error(request, 'Admins can only delete Incubatees.')
            return redirect('dashboard')
            
    target_user.delete()
    messages.success(request, f'User {target_user.username} deleted.')
    return redirect('dashboard')

@login_required
def startups_list(request):
    # Allow admins and super admins
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')

    startups = Startup.objects.all().prefetch_related(
        'milestones',
        'milestones__deliverables'
    )

    for startup in startups:
        startup.current_milestone = None
        for milestone in startup.milestones.all():
            if milestone.status != 'completed' and not milestone.is_locked():
                startup.current_milestone = milestone
                break

    context = {
        'startups': startups,
        'cohorts': Cohort.objects.all().order_by('-start_date'),
        'total_startups': Startup.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'startups/list.html', context)

@login_required
def delete_startup(request, startup_id):
    # Allow Super Admin and Admin
    if request.user.role not in ['super_admin', 'admin']:
        return redirect('dashboard')
        
    startup = get_object_or_404(Startup, id=startup_id)
    
    # Collect users to potentially delete
    users_to_check = set()
    if startup.owner:
        users_to_check.add(startup.owner)
    for member in startup.members.all():
        users_to_check.add(member)
        
    users_to_delete = []
    for u in users_to_check:
        if u.role == 'incubatee':
            other_owned = u.owned_startups.exclude(id=startup_id).exists()
            other_member = u.startups.exclude(id=startup_id).exists()
            if not other_owned and not other_member:
                users_to_delete.append(u)
                
    startup_name = startup.name
    startup.delete()
    
    for u in users_to_delete:
        u.delete()
        
    messages.success(request, f'Startup {startup_name} deleted. {len(users_to_delete)} orphaned member accounts were also cleaned up.')
    return redirect('startups_list')

@login_required
def add_startup(request):

    name = request.POST.get('name')
    # Allow admins and super admins
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')

    if Startup.objects.filter(name=name).exists():
        messages.error(request, 'Startup already exists.')
        return redirect('add_startup')

    if request.method == 'POST':
        form = StartupForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            startup = form.save(commit=False)
            startup.owner = request.user
            
            # Auto-assign cohort based on current date
            today = timezone.localdate()
            active_cohort = Cohort.objects.filter(
                Q(start_date__lte=today) &
                (Q(end_date__isnull=True) | Q(end_date__gte=today))
            ).order_by('-start_date').first()
            
            if active_cohort:
                startup.cohort = active_cohort
                
            startup.save()
            
            # Create milestones and deliverables from Global Templates
            starting_milestone = int(form.cleaned_data.get('starting_milestone', 1))
            milestone_templates = MilestoneTemplate.objects.all().order_by('milestone_progress')
            
            for mt in milestone_templates:
                i = mt.milestone_progress
                milestone_status = 'completed' if i < starting_milestone else 'pending'
                completed_time = timezone.now() if i < starting_milestone else None
                
                milestone = Milestone.objects.create(
                    startup=startup,
                    milestone_progress=i,
                    title=mt.title,
                    description=mt.description or f"Milestone for {startup.name}",
                    status=milestone_status,
                    completed_at=completed_time
                )
                
                deliverable_status = 'approved' if i < starting_milestone else 'pending'
                
                # Instantiate deliverables from the templates and map the template FK
                for dt in mt.deliverable_templates.all():
                    Deliverable.objects.create(
                        milestone=milestone,
                        template=dt,
                        name=dt.name,
                        requirements=dt.requirements or "See template requirements",
                        status=deliverable_status
                    )

            messages.success(request, 'Startup created! Now add members.')
            return redirect('add_member', startup_id=startup.id)
    else:
        form = StartupForm(user=request.user)
    return render(request, 'startups/add_startup.html', {'form': form})

# ... view_startup ...
@login_required
def view_startup(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id)
    # Check permission?
    milestones = startup.milestones.all()
    reports = startup.progress_reports.order_by('-submitted_at')
    
    # Calculate current milestone (first one that's not completed and not locked)
    current_milestone = None
    current_milestone_id = None
    current_deliverable = None
    for milestone in milestones:
        if milestone.status != 'completed' and not milestone.is_locked():
            current_milestone = milestone
            current_milestone_id = milestone.id
            current_deliverable = milestone.deliverables.filter(
                status__in=['pending', 'submitted']
            ).order_by('id').first()
            break
    
    # Get startup members (only for admins)
    startup_members = []
    if request.user.role in ['admin', 'super_admin']:
        startup_members = startup.members.all()
    
    context = {
        'startup': startup,
        'milestones': milestones,
        'reports': reports,
        'current_milestone_id': current_milestone_id,
        'current_milestone': current_milestone,
        'current_deliverable': current_deliverable,
        'startup_members': startup_members
    }
    return render(request, 'startups/view.html', context)

@login_required
def edit_startup(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id)
    
    # Allow admins, the owner, OR members (incubatees)
    is_owner = (request.user == startup.owner)
    is_member = (request.user in startup.members.all())
    is_admin = (request.user.role in ['admin', 'super_admin'])
    
    if not (is_admin or is_owner or is_member):
        return redirect('dashboard')

    # handle form submission and display
    if request.method == 'POST':
        form = StartupForm(request.POST, request.FILES, instance=startup, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Startup updated.')
            return redirect('view_startup', startup_id=startup.id)
    else:
        form = StartupForm(instance=startup, user=request.user)
    return render(request, 'startups/edit.html', {'form': form, 'startup': startup})


@login_required
def attach_admin_file(request, deliverable_id):
    # Only admin or super_admin can attach admin files
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')

    deliverable = get_object_or_404(Deliverable, id=deliverable_id)

    if request.method == 'POST':
        if request.FILES.getlist('file'):
            for f in request.FILES.getlist('file'):
                DeliverableFile.objects.create(deliverable=deliverable, file=f, uploaded_by_role='admin')
        
        link_url = request.POST.get('link_url')
        if link_url:
            link_title = get_link_title_safe(link_url)
            DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, link_title=link_title, uploaded_by_role='admin')
            
        link = reverse('view_milestone', args=[deliverable.milestone.startup.id, deliverable.milestone.id])
        msg = f"Admin uploaded a file for '{deliverable.name}'"
        members = list(deliverable.milestone.startup.members.all())
        recipients = set([m.user for m in members] + [deliverable.milestone.startup.owner] if deliverable.milestone.startup.owner else [m.user for m in members])
        for recipient in recipients:
            Notification.objects.create(recipient=recipient, message=msg, link=link)
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            files_data = [{'id': f.id, 'url': f.file.url, 'name': f.file.name.split('/')[-1]} for f in deliverable.files.filter(uploaded_by_role='admin')]
            return JsonResponse({'success': True, 'files': files_data})

    # Redirect back to milestone view
    milestone = deliverable.milestone
    return HttpResponseRedirect(reverse('view_milestone', args=[milestone.startup.id, milestone.id]))


@login_required
def attach_incubatee_file(request, deliverable_id):
    # Incubatee (startup members or owner) can attach their file
    deliverable = get_object_or_404(Deliverable, id=deliverable_id)
    startup = deliverable.milestone.startup

    # Allow owner, startup members, admins
    is_member = request.user in startup.members.all() or request.user == startup.owner
    if not (is_member or request.user.role in ['admin', 'super_admin']):
        return redirect('dashboard')

    if request.method == 'POST':
        if request.FILES.getlist('file'):
            for f in request.FILES.getlist('file'):
                DeliverableFile.objects.create(deliverable=deliverable, file=f, uploaded_by_role='incubatee')
                
        link_url = request.POST.get('link_url')
        if link_url:
            link_title = get_link_title_safe(link_url)
            DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, link_title=link_title, uploaded_by_role='incubatee')
            
        text_content = request.POST.get('text_content')
        if text_content:
            DeliverableFile.objects.create(deliverable=deliverable, text_content=text_content, uploaded_by_role='incubatee')
            
        # Automatically update status to 'submitted' so the timeline and admin queue reflect it
        if deliverable.status in ['pending', 'not_started', 'rejected']:
            deliverable.status = 'submitted'
            deliverable.save()
            
        link = reverse('view_milestone', args=[startup.id, deliverable.milestone.id])
        msg = f"{startup.name} uploaded a file for '{deliverable.name}'"
        admins = User.objects.filter(role__in=['admin', 'super_admin'])
        for admin in admins:
            Notification.objects.create(recipient=admin, message=msg, link=link)
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            files_data = []
            for f in deliverable.files.filter(uploaded_by_role='incubatee'):
                files_data.append({
                    'id': f.id, 
                    'url': f.file.url if f.file else (f.link_url if f.link_url else ''), 
                    'name': f.file.name.split('/')[-1] if f.file else ('Link Attachment' if f.link_url else 'Text Attachment'),
                    'is_file': bool(f.file),
                    'is_link': bool(f.link_url),
                    'is_text': bool(f.text_content),
                    'text_content': f.text_content if f.text_content else ''
                })
            return JsonResponse({'success': True, 'files': files_data})

    milestone = deliverable.milestone
    return HttpResponseRedirect(reverse('view_milestone', args=[milestone.startup.id, milestone.id]))

@login_required
def add_member(request, startup_id):

    first_name = request.POST.get('first_name')
    middle_name = request.POST.get('middle_name')
    lastname = request.POST.get('last_name')
    email_exist = request.POST.get('email')
    number = request.POST.get('contact_number')

    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')

    # if User.objects.filter(last_name=lastname).exists():
    #     messages.error(request, 'A user with this last name already exists. Please modify the last name to create a unique username.')
    #     return render(request, 'startups/add_member.html', {'form': form, 'startup': startup})
    
    # if User.objects.filter(email=email_exist).exists():
    #     messages.error(request, 'A user with this email already exists.')
    #     return render(request, 'startups/add_member.html', {'form': form, 'startup': startup})
    
    # if User.objects.filter(contact_number=number).exists():
    #     messages.error(request, 'A user with this contact number already exists.')
    #     return render(request, 'startups/add_member.html', {'form': form, 'startup': startup})


    startup = get_object_or_404(Startup, id=startup_id)
    
    if request.method == 'POST':
        form = StartupMemberForm(request.POST)

        if form.is_valid():
            email_exist = form.cleaned_data['email']
            existing_user = User.objects.filter(email=email_exist).first()
            
            position = form.cleaned_data['position']
            
            if existing_user:
                if existing_user.role != 'incubatee':
                    messages.error(request, 'Cannot add an admin account as a startup member.')
                    return redirect('add_member', startup_id=startup.id)
                    
                if StartupMember.objects.filter(startup=startup, user=existing_user).exists():
                    messages.error(request, 'This user is already a member of this startup.')
                    return redirect('add_member', startup_id=startup.id)
                    
                # Link existing user
                StartupMember.objects.create(startup=startup, user=existing_user, role=position)
                messages.success(request, f'Existing member {existing_user.get_full_name() or existing_user.username} linked to {startup.name} successfully!')
                
                action = request.POST.get('action')
                if action == 'save_and_add_another':
                    return redirect('add_member', startup_id=startup.id)
                else:
                    return redirect('view_startup', startup_id=startup.id)
            
            # If we reach here, it's a new user. 
            first_name = form.cleaned_data.get('first_name')
            middle_name = form.cleaned_data.get('middle_name', '')
            last_name = form.cleaned_data.get('last_name')
            contact = form.cleaned_data.get('contact_number')
            email = form.cleaned_data.get('email')
            
            if not first_name or not last_name or not contact:
                messages.error(request, 'First Name, Last Name, and Contact Number are required to create a new user.')
                return redirect('add_member', startup_id=startup.id)

            if User.objects.filter(contact_number=contact).exists():
                messages.error(request, 'A user with this contact number already exists. Please use their registered email to link their account.')
                return redirect('add_member', startup_id=startup.id)
            
            # Generate Username: lastname.firstname
            base_username = f"{last_name.lower()}.{first_name.lower()}".replace(" ", "")
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            try:
                user = User.objects.create(
                    username=username, 
                    email=email, 
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    contact_number=contact,
                    role='incubatee' 
                )
                user.set_unusable_password()
                user.save()
                
                # Link to Startup
                StartupMember.objects.create(
                    startup=startup,
                    user=user,
                    role=position
                )
                
                messages.success(request, f'Member {first_name} added! Username: {username}')
                if request.POST.get('action') == 'save_and_view':
                    return redirect('view_startup', startup_id=startup.id)
                return redirect('add_member', startup_id=startup.id)
            except Exception as e:
                messages.error(request, f"Error creating user: {e}")
    else:
        form = StartupMemberForm()

    return render(request, 'startups/add_member.html', {'form': form, 'startup': startup})


@login_required
def delete_member(request, startup_id, member_id):
    # Only admin or super_admin can remove members
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')

    startup = get_object_or_404(Startup, id=startup_id)
    user = get_object_or_404(User, id=member_id)

    # Ensure the membership exists
    membership = StartupMember.objects.filter(startup=startup, user=user).first()
    if not membership:
        messages.error(request, 'Member not found for this startup.')
        return redirect('view_startup', startup_id=startup.id)

    # Prevent deleting the owner via this action
    if user == startup.owner:
        messages.error(request, 'Cannot remove the owner from the startup.')
        return redirect('view_startup', startup_id=startup.id)

    # Delete membership record
    membership.delete()

    # Automatically clean up the user account if they are an orphaned incubatee
    if user.role == 'incubatee':
        other_owned = user.owned_startups.exists()
        other_member = user.startups.exists()
        if not other_owned and not other_member:
            username_display = user.get_full_name() or user.username
            user.delete()
            messages.success(request, f'Member {username_display} removed and orphaned account automatically deleted.')
            return redirect('view_startup', startup_id=startup.id)

    messages.success(request, f'Member {user.get_full_name() or user.username} removed from {startup.name}.')
    return redirect('view_startup', startup_id=startup.id)

@login_required
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
    
    return redirect('view_startup', startup_id=startup.id)

@login_required
def submit_progress(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id)

    current_milestone = None
    current_deliverable = None
    for milestone in startup.milestones.order_by('milestone_progress'):
        if milestone.status != 'completed' and not milestone.is_locked():
            current_milestone = milestone
            current_deliverable = milestone.deliverables.filter(status__in=['pending', 'submitted']).order_by('id').first()
            break

    if request.method == 'POST':
        form = ProgressReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.startup = startup
            report.submitted_by = request.user
            report.save()
            messages.success(request, 'Report submitted.')
            # Redirect to the current active milestone for this startup so incubatees can see deliverables.
            if current_milestone:
                return redirect('view_milestone', startup_id=startup.id, milestone_id=current_milestone.id)
            return redirect('view_startup', startup_id=startup.id)
    else:
        initial = {}
        if current_milestone:
            initial['title'] = current_milestone.title or f"Milestone {current_milestone.milestone_progress}"
        if current_deliverable:
            initial['description'] = f"Submission report for {current_deliverable.name}"
        form = ProgressReportForm(initial=initial)

    return render(request, 'startups/submit_report.html', {
        'form': form,
        'startup': startup,
        'current_milestone': current_milestone,
        'current_deliverable': current_deliverable,
    })

@login_required
def view_milestone(request, startup_id, milestone_id):
    startup = get_object_or_404(Startup, id=startup_id)
    milestone = get_object_or_404(Milestone, id=milestone_id, startup=startup)
    deliverables = milestone.deliverables.all().order_by('id')
    
    # Check if milestone is locked
    is_locked = milestone.is_locked()
    
    # Only admins can bypass the lock
    if is_locked and request.user.role not in ['admin', 'super_admin']:
        messages.error(request, f'This milestone is locked. Complete the previous milestone first.')
        return redirect('view_startup', startup_id=startup_id)
    
    # Serialize deliverables data for the modal
    deliverables_data = []
    for d in deliverables:
        rls_dict = {rl.name: {'incubatee': rl.incubatee_level, 'admin': rl.admin_level} for rl in d.readiness_levels.all()}
        comments = [{'user': c.user.username, 'content': c.content, 'date': c.created_at.strftime("%b %d, %Y %H:%M")} for c in d.comments.order_by('-created_at')]
        admin_files = [{'id': f.id, 'url': f.file.url if f.file else f.link_url, 'name': f.file.name.split('/')[-1] if f.file else (f.link_title or f.link_url)} for f in d.files.filter(uploaded_by_role='admin') if f.file or f.link_url]
        incubatee_files = [{'id': f.id, 'url': f.file.url if f.file else f.link_url, 'name': f.file.name.split('/')[-1] if f.file else (f.link_title or f.link_url), 'is_text': bool(f.text_content), 'text_content': f.text_content} for f in d.files.filter(uploaded_by_role='incubatee') if f.file or f.link_url or f.text_content]
        
        global_template_data = None
        if d.template and d.template.admin_file:
            global_template_data = {
                'url': d.template.admin_file.url,
                'name': d.template.admin_file.name.split('/')[-1],
                'type': 'file'
            }
        elif d.template and d.template.admin_link:
            global_template_data = {
                'url': d.template.admin_link,
                'name': d.template.admin_link_title or get_link_title_safe(d.template.admin_link) or d.template.admin_link,
                'type': 'link'
            }
            
        deliverables_data.append({
            'obj': d,
            'rls_json': json.dumps(rls_dict),
            'comments_json': json.dumps(comments),
            'admin_files_json': json.dumps(admin_files),
            'incubatee_files_json': json.dumps(incubatee_files),
            'global_template_file_json': json.dumps(global_template_data) if global_template_data else "null"
        })

    rl_templates_db = RLTemplate.objects.all().prefetch_related('levels').order_by('id')
    rl_data = {}
    for rlt in rl_templates_db:
        rl_data[rlt.name] = {}
        for lvl in rlt.levels.all():
            rl_data[rlt.name][str(lvl.level)] = {
                'description': lvl.description
            }
    
    context = {
        'startup': startup,
        'milestone': milestone,
        'deliverables_data': deliverables_data,
        'is_locked': is_locked,
        'rl_templates': rl_templates_db,
        'rl_data_json': json.dumps(rl_data),
    }
    return render(request, 'startups/view_milestone.html', context)

@login_required
def update_milestone_status(request, startup_id, milestone_id):
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')
    
    startup = get_object_or_404(Startup, id=startup_id)
    milestone = get_object_or_404(Milestone, id=milestone_id, startup=startup)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Milestone.STATUS_CHOICES):
            milestone.status = new_status
            if new_status == 'completed':
                milestone.completed_at = timezone.now()
            milestone.save()
            messages.success(request, f'Milestone status updated to {milestone.get_status_display()}')
    
    return redirect('view_milestone', startup_id=startup_id, milestone_id=milestone_id)


@login_required
def add_custom_deliverable(request, milestone_id):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        milestone = get_object_or_404(Milestone, id=milestone_id)
        name = request.POST.get('name')
        requirements = request.POST.get('requirements')
        due_date = request.POST.get('due_date')
        
        try:
            Deliverable.objects.create(
                milestone=milestone,
                name=name,
                requirements=requirements,
                due_date=due_date or None,
                status='not_started'
            )
            messages.success(request, 'Custom deliverable added.')
        except Exception as e:
            messages.error(request, f'Failed to add custom deliverable: {str(e)}')
            
        return redirect('view_milestone', startup_id=milestone.startup.id, milestone_id=milestone.id)
    return redirect('dashboard')

@login_required
def edit_deliverable_page(request, deliverable_id):
    deliverable = get_object_or_404(Deliverable, id=deliverable_id)
    milestone = deliverable.milestone
    startup = milestone.startup
    
    is_locked = milestone.is_locked()
    if is_locked and request.user.role not in ['admin', 'super_admin']:
        messages.error(request, f'This milestone is locked. Complete the previous milestone first.')
        return redirect('view_startup', startup_id=startup.id)
        
    rls_dict = {rl.name: {'incubatee': rl.incubatee_level, 'admin': rl.admin_level} for rl in deliverable.readiness_levels.all()}
    
    global_template_data = None
    if deliverable.template and deliverable.template.admin_file:
        global_template_data = {
            'url': deliverable.template.admin_file.url,
            'name': deliverable.template.admin_file.name.split('/')[-1]
        }
    
    global_template_link = None
    global_template_link_title = None
    if deliverable.template and deliverable.template.admin_link:
        global_template_link = deliverable.template.admin_link
        global_template_link_title = deliverable.template.admin_link_title or get_link_title_safe(global_template_link)
        
    rl_templates_db = RLTemplate.objects.all().prefetch_related('levels')
    rl_data = {}
    rl_types = []
    for rlt in rl_templates_db:
        rl_types.append(rlt.name)
        rl_data[rlt.name] = {}
        for lvl in rlt.levels.all():
            rl_data[rlt.name][str(lvl.level)] = {
                'description': lvl.description
            }

    context = {
        'startup': startup,
        'milestone': milestone,
        'deliverable': deliverable,
        'admin_files': deliverable.files.filter(uploaded_by_role='admin'),
        'incubatee_files': deliverable.files.filter(uploaded_by_role='incubatee'),
        'comments': deliverable.comments.order_by('-created_at'),
        'rls_dict': json.dumps(rls_dict),
        'global_template_data': global_template_data,
        'global_template_link': global_template_link,
        'global_template_link_title': global_template_link_title,
        'rl_types': rl_types,
        'rl_data_json': json.dumps(rl_data),
    }
    return render(request, 'startups/edit_deliverable.html', context)

@login_required
def update_deliverable_details(request, deliverable_id):
    deliverable = get_object_or_404(Deliverable, id=deliverable_id)
    startup_id = deliverable.milestone.startup.id
    milestone_id = deliverable.milestone.id
    is_admin = request.user.role in ['admin', 'super_admin']

    if request.method == 'POST':
        action = request.POST.get('action') # 'save', 'revision', 'done'
        
        # Update requirements and due date (only admins can change these)
        if is_admin:
            requirements = request.POST.get('requirements')
            due_date = request.POST.get('due_date')
            if requirements is not None:
                deliverable.requirements = requirements
            if due_date:
                deliverable.due_date = due_date
            
        if is_admin:
            link = reverse('view_milestone', args=[startup_id, milestone_id])
            msg = f"Admin reviewed '{deliverable.name}'"
            members = list(deliverable.milestone.startup.members.all())
            recipients = set(members + [deliverable.milestone.startup.owner] if deliverable.milestone.startup.owner else members)
            for recipient in recipients:
                Notification.objects.create(recipient=recipient, message=msg, link=link)
            # Handle Readiness Level Checkboxes (Admin sets requirement)
            rl_types = RLTemplate.objects.values_list('name', flat=True)
            for rl_type in rl_types:
                is_checked = request.POST.get(f'{rl_type.lower()}_checked') == 'on'
                
                # If checked, ensure it exists. If not, delete it.
                if is_checked:
                    rl_obj, _ = Readiness.objects.get_or_create(deliverable=deliverable, name=rl_type)
                    # Admin can also provide a select level verdict for this
                    admin_level_val = request.POST.get(f'{rl_type.lower()}_admin_level')
                    if admin_level_val and admin_level_val != 'Select Level':
                        rl_obj.admin_level = admin_level_val
                        rl_obj.save()
                else:
                    Readiness.objects.filter(deliverable=deliverable, name=rl_type).delete()
                    
            # Handle Admin Actions
            if action == 'revision':
                deliverable.status = 'rejected'
                messages.warning(request, f'Revision requested for {deliverable.name}.')
                comment_text = (request.POST.get('revision_comment') or request.POST.get('comment') or '').strip()
                if comment_text:
                    comment_text = f"⚠️ REVISION REQUESTED:\n{comment_text}"
                
                # Check for new due date
                revision_due_date = request.POST.get('revision_due_date')
                if revision_due_date:
                    deliverable.due_date = revision_due_date
                
                # Check for annotated file upload
                revision_file = request.FILES.get('revision_file')
                if revision_file:
                    DeliverableFile.objects.create(
                        deliverable=deliverable,
                        file=revision_file,
                        uploaded_by_role='admin'
                    )

                # Send email notification to incubatees
                send_deliverable_status_email(
                    deliverable=deliverable,
                    action='revision',
                    admin_user=request.user,
                    comment=comment_text or None,
                )
            elif action == 'done':
                deliverable.status = 'approved'
                messages.success(request, f'Deliverable {deliverable.name} approved.')
                comment_text = (request.POST.get('revision_comment') or request.POST.get('comment') or '').strip()
                if comment_text:
                    comment_text = f"✅ DELIVERABLE APPROVED:\n{comment_text}"
                # Send email notification to incubatees
                send_deliverable_status_email(
                    deliverable=deliverable,
                    action='done',
                    admin_user=request.user,
                    comment=comment_text or None,
                )
                
        # Incubatee can update Readiness Level selections
        elif request.user.role == 'incubatee':
            # Incubatees only update levels for existing Readiness objects created by admin
            existing_rls = Readiness.objects.filter(deliverable=deliverable)
            for rl in existing_rls:
                level_val = request.POST.get(f'{rl.name.lower()}_level')
                if level_val and level_val != 'Select Level':
                    rl.incubatee_level = level_val
                    rl.save()

        # Both can add comments
        # We handle prefixed text from admin actions
        if action in ['revision', 'done']:
            # The text was already prefixed in the action handlers above
            pass
        else:
            comment_text = request.POST.get('comment')
            if comment_text:
                comment_text = comment_text.strip()
            
        if comment_text and comment_text.strip():
            Comment.objects.create(
                deliverable=deliverable,
                user=request.user,
                content=comment_text.strip()
            )

        deliverable.save()
        
        # Auto-complete milestone if all its deliverables are approved
        milestone = deliverable.milestone
        if milestone.status != 'completed':
            all_approved = not milestone.deliverables.exclude(status='approved').exists()
            if all_approved:
                milestone.status = 'completed'
                from django.utils import timezone
                milestone.completed_at = timezone.now()
                milestone.save()

        if not messages.get_messages(request):
            messages.success(request, 'Deliverable details updated successfully.')
            
    return redirect('edit_deliverable_page', deliverable_id=deliverable.id)

@login_required
def set_password(request):
    if request.user.has_usable_password():
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important, to update the session with the new password
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = SetPasswordForm(request.user)
    return render(request, 'set_password.html', {'form': form})

@login_required
def delete_deliverable_file(request, file_id):
    if request.method == 'POST':
        deliverable_file = get_object_or_404(DeliverableFile, id=file_id)
        startup = deliverable_file.deliverable.milestone.startup
        
        # Check permissions: Admin can delete anything. Incubatees can only delete their own startup's incubatee files.
        is_admin = request.user.role in ['admin', 'super_admin']
        is_member = request.user in startup.members.all() or request.user == startup.owner
        
        if is_admin or (is_member and deliverable_file.uploaded_by_role == 'incubatee'):
            # Delete physical file
            if deliverable_file.file:
                deliverable_file.file.delete(save=False)
            # Delete database record
            deliverable_file.delete()
            return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=403)

@login_required
def read_notification(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    return redirect(notif.link)

@login_required
def clear_notifications(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user).delete()
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def settings_view(request):
    user = request.user
    is_admin = user.role in ['admin', 'super_admin']
    
    # Forms
    password_form = PasswordChangeForm(user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_password':
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Password successfully updated!')
                return redirect('settings')
            else:
                messages.error(request, 'Please correct the errors below.')
        
        elif action == 'upload_picture':
            if 'profile_picture' in request.FILES:
                # Delete old picture file if exists
                if user.profile_picture:
                    user.profile_picture.delete(save=False)
                user.profile_picture = request.FILES['profile_picture']
                user.save()
                messages.success(request, 'Profile picture updated!')
            else:
                messages.error(request, 'Please select an image to upload.')
            return redirect('settings')
        
        elif action == 'remove_picture':
            if user.profile_picture:
                user.profile_picture.delete(save=False)
                user.profile_picture = None
                user.save()
                messages.success(request, 'Profile picture removed.')
            return redirect('settings')
                
    # Admin global templates
    milestone_templates = MilestoneTemplate.objects.all().order_by('milestone_progress') if is_admin else None
    cohorts = Cohort.objects.all().order_by('-start_date') if user.role == 'super_admin' else None
    rl_templates = RLTemplate.objects.all().prefetch_related('levels') if user.role == 'super_admin' else None

    context = {
        'is_admin': is_admin,
        'password_form': password_form,
        'milestone_templates': milestone_templates,
        'cohorts': cohorts,
        'rl_templates': rl_templates,
    }
    return render(request, 'settings/index.html', context)

@login_required
def add_milestone_template(request):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        latest_progress = MilestoneTemplate.objects.aggregate(max_progress=Max('milestone_progress'))['max_progress'] or 0
        progress = latest_progress + 1
        deliverable_count = int(request.POST.get('deliverables_count', 0))
        count = 1
        while MilestoneTemplate.objects.filter(milestone_progress=progress).exists():
            progress += 1
        
        custom_title = request.POST.get('title', '').strip()
        title = custom_title if custom_title else f"Milestone {progress}"
        description = ""
        
        try:
            newmilestone_template = MilestoneTemplate.objects.create(
                title=title,
                description=description,
                milestone_progress=int(progress)
            )

            for startup in Startup.objects.all():
                exist = Milestone.objects.filter(startup_id=startup.id, milestone_progress=progress).exists()
                if not exist:
                    Milestone.objects.create(
                        startup=startup,
                        milestone_progress=progress,
                        title=title,
                        description=description,
                        status='pending'
                    )
            while count <= deliverable_count:
                name = "Deliverable " + str(count)
                requirements = "Requirements for " + title
                
                DeliverableTemplate.objects.create(
                    milestone_template=newmilestone_template,
                    name=name,
                    requirements=requirements
                )
                count += 1

            for startup in Startup.objects.all():
                milestone = Milestone.objects.filter(startup_id=startup.id, milestone_progress=progress).first()
                if milestone:
                    for dt in newmilestone_template.deliverable_templates.all():
                        Deliverable.objects.create(
                            milestone=milestone,
                            template=dt,
                            name=dt.name,
                            requirements=dt.requirements or "See template requirements",
                            status='pending'
                        )


            messages.success(request, 'Milestone template added successfully.')
        except Exception as e:
            messages.error(request, f'Failed to add template: {str(e)}')
    
    return redirect('settings')


@login_required
def delete_milestone_template(request, template_id):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        template = get_object_or_404(MilestoneTemplate, id=template_id)
        milestone_progress = template.milestone_progress
        
        # Delete all Milestones with matching milestone_progress
        Milestone.objects.filter(milestone_progress=milestone_progress).delete()
        
        # Delete the templatecee
        template.delete()
        messages.success(request, 'Milestone template and related milestones deleted.')
        
    return redirect('settings')

@login_required
def add_deliverable_template(request):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        milestone_id = request.POST.get('milestone_template_id')
        requirements = request.POST.get('requirements')
        admin_file = request.FILES.get('admin_file')
        admin_link = request.POST.get('admin_link')
        
        try:
            mt = get_object_or_404(MilestoneTemplate, id=milestone_id)
            existing_count = mt.deliverable_templates.count()
            name = request.POST.get('name', f"Deliverable {existing_count + 1}")
            dt = DeliverableTemplate.objects.create(
                milestone_template=mt,
                name=name,
                requirements=requirements
            )
            
            new_files = request.FILES.getlist('new_files')
            for f in new_files:
                DeliverableTemplateResource.objects.create(template=dt, file=f)
                
            new_links = request.POST.getlist('new_links')
            for l in new_links:
                if l.strip():
                    DeliverableTemplateResource.objects.create(template=dt, link=l.strip())
            messages.success(request, 'Deliverable template added.')
        except Exception as e:
            messages.error(request, f'Failed to add deliverable: {str(e)}')
            
    return redirect('settings')

@login_required
def delete_deliverable_template(request, template_id):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        dt = get_object_or_404(DeliverableTemplate, id=template_id)
        dt.delete()
        messages.success(request, 'Deliverable template removed.')
        
    return redirect('settings')

@login_required
def edit_milestone_template(request, template_id, dt_id):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        
        # Milestone
        mt = get_object_or_404(MilestoneTemplate, id=template_id)
        mt.title = request.POST.get('title', mt.title)
        mt.description = request.POST.get('description', mt.description)
        mt.milestone_progress = request.POST.get('milestone_progress', mt.milestone_progress)
        mt.save()

        messages.success(request, 'Milestone template updated.')
        
    return redirect('settings')

@login_required
def edit_deliverable_template(request, template_id):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        dt = get_object_or_404(DeliverableTemplate, id=template_id)
        dt.name = request.POST.get('name', dt.name)
        dt.requirements = request.POST.get('requirements', dt.requirements)
        if 'admin_file' in request.FILES:
            dt.admin_file = request.FILES.get('admin_file')
        
        if 'admin_link' in request.POST:
            dt.admin_link = request.POST.get('admin_link')
            if dt.admin_link:
                dt.admin_link_title = get_link_title_safe(dt.admin_link)
            
        dt.save()

        # Handle multiple files and links
        new_files = request.FILES.getlist('new_files')
        for f in new_files:
            DeliverableTemplateResource.objects.create(template=dt, file=f)
            
        new_links = request.POST.getlist('new_links')
        for l in new_links:
            if l.strip():
                DeliverableTemplateResource.objects.create(template=dt, link=l.strip())

        messages.success(request, 'Deliverable template updated.')
        
    return redirect('settings')

@login_required
def add_cohort(request):
    if request.user.role != 'super_admin':
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        name = request.POST.get('name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        try:
            Cohort.objects.create(
                name=name,
                start_date=start_date or None,
                end_date=end_date or None
            )
            messages.success(request, 'Cohort added successfully.')
        except Exception as e:
            messages.error(request, f'Failed to add cohort: {str(e)}')
            
    return redirect('settings')

@login_required
def edit_cohort(request, cohort_id):
    if request.user.role != 'super_admin':
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        cohort = get_object_or_404(Cohort, id=cohort_id)
        cohort.name = request.POST.get('name', cohort.name)
        cohort.start_date = request.POST.get('start_date', cohort.start_date) or None
        cohort.end_date = request.POST.get('end_date', cohort.end_date) or None
        cohort.save()
        messages.success(request, 'Cohort updated successfully.')
        
    return redirect('settings')

@login_required
def delete_cohort(request, cohort_id):
    if request.user.role != 'super_admin':
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        cohort = get_object_or_404(Cohort, id=cohort_id)
        cohort.delete()
        messages.success(request, 'Cohort deleted successfully.')
        
    return redirect('settings')

@login_required
def add_rltemplate(request):
    if request.user.role != 'super_admin':
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        name = request.POST.get('name')
        try:
            RLTemplate.objects.create(name=name)
            messages.success(request, 'RL Template added successfully.')
        except Exception as e:
            messages.error(request, f'Failed to add RL Template: {str(e)}')
            
    return redirect('settings')

@login_required
def edit_rltemplate(request, template_id):
    if request.user.role != 'super_admin':
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        rltemplate = get_object_or_404(RLTemplate, id=template_id)
        rltemplate.name = request.POST.get('name', rltemplate.name)
        rltemplate.save()
        messages.success(request, 'RL Template updated successfully.')
        
    return redirect('settings')

@login_required
def delete_rltemplate(request, template_id):
    if request.user.role != 'super_admin':
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        rltemplate = get_object_or_404(RLTemplate, id=template_id)
        rltemplate.delete()
        messages.success(request, 'RL Template deleted successfully.')
        
    return redirect('settings')

@login_required
def add_rltemplate_level(request):
    if request.user.role != 'super_admin':
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        level = request.POST.get('level')
        description = request.POST.get('description')
        
        try:
            rltemplate = get_object_or_404(RLTemplate, id=template_id)
            RLTemplateLevel.objects.create(
                template=rltemplate,
                level=level,
                description=description
            )
            messages.success(request, 'RL Level added successfully.')
        except Exception as e:
            messages.error(request, f'Failed to add RL Level: {str(e)}')
            
    return redirect('settings')

@login_required
def edit_rltemplate_level(request, level_id):
    if request.user.role != 'super_admin':
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        rl_level = get_object_or_404(RLTemplateLevel, id=level_id)
        rl_level.level = request.POST.get('level', rl_level.level)
        rl_level.description = request.POST.get('description', rl_level.description)
        rl_level.save()
        messages.success(request, 'RL Level updated successfully.')
        
    return redirect('settings')

@login_required
def delete_rltemplate_level(request, level_id):
    if request.user.role != 'super_admin':
        return HttpResponse('Unauthorized', status=403)
        
    if request.method == 'POST':
        rl_level = get_object_or_404(RLTemplateLevel, id=level_id)
        rl_level.delete()
        messages.success(request, 'RL Level deleted successfully.')
        
    return redirect('settings')

@login_required
def reports_view(request):
    if request.user.role not in ['admin', 'super_admin']:
        messages.error(request, 'Unauthorized access to Reports.')
        return redirect('dashboard')
    cohorts = Cohort.objects.all().order_by('-start_date')
    startups = Startup.objects.all().select_related('cohort').order_by('name')
    return render(request, 'reports/index.html', {'cohorts': cohorts, 'startups': startups})

@login_required
def cohort_report(request):
    from datetime import date
    if request.user.role not in ['admin', 'super_admin']:
        messages.error(request, 'Unauthorized access to Reports.')
        return redirect('dashboard')
    cohort_id = request.GET.get('cohort_id')
    if not cohort_id:
        return redirect('reports')
    cohort = get_object_or_404(Cohort, id=cohort_id)
    startups = cohort.startups.prefetch_related('milestones__deliverables', 'members').all()
    
    total_startups = startups.count()

    
    total_members = 0
    total_progress = 0
    past_due_items = []
    today = date.today()
    
    for s in startups:
        s.current_progress = s.progress
        total_progress += s.current_progress
        s.team_size = s.members.count()
        total_members += s.team_size
        
        completed_milestones = s.milestones.filter(status='completed').order_by('-milestone_progress')
        s.latest_milestone = completed_milestones.first().title if completed_milestones.exists() else "None"
        
        for m in s.milestones.filter(status__in=['not-yet', 'pending']):
            if m.due_date and m.due_date < today:
                past_due_items.append({'startup': s.name, 'type': 'Milestone', 'name': m.title, 'due_date': m.due_date, 'status': m.get_status_display()})
                
        for m in s.milestones.all():
            for d in m.deliverables.filter(status__in=['pending', 'rejected']):
                if d.due_date and d.due_date < today:
                    past_due_items.append({'startup': s.name, 'type': 'Deliverable', 'name': d.name, 'due_date': d.due_date, 'status': d.get_status_display()})
                    
    avg_progress = int(total_progress / total_startups) if total_startups > 0 else 0
    
    return render(request, 'reports/cohort_report.html', {
        'cohort': cohort,
        'startups': startups,
        'total_startups': total_startups,
        'avg_progress': avg_progress,
        'total_members': total_members,

        'past_due_items': past_due_items
    })

@login_required
def startup_report(request):
    from datetime import date
    if request.user.role not in ['admin', 'super_admin']:
        messages.error(request, 'Unauthorized access to Reports.')
        return redirect('dashboard')
    startup_id = request.GET.get('startup_id')
    if not startup_id:
        return redirect('reports')
    startup = get_object_or_404(Startup, id=startup_id)
    milestones = startup.milestones.prefetch_related('deliverables__readiness_levels', 'deliverables__files').order_by('milestone_progress')
    
    startup.team_size = startup.members.count()
    completed_milestones = milestones.filter(status='completed').order_by('-milestone_progress')
    startup.latest_milestone = completed_milestones.first().title if completed_milestones.exists() else "None"
    
    rl_dict = {}
    past_due_items = []
    today = date.today()
    total_revisions = 0
    
    for m in milestones:
        if m.status in ['not-yet', 'pending'] and m.due_date and m.due_date < today:
            past_due_items.append({'type': 'Milestone', 'name': m.title, 'due_date': m.due_date, 'status': m.get_status_display()})
            
        for d in m.deliverables.all():
            if d.status in ['pending', 'rejected'] and d.due_date and d.due_date < today:
                past_due_items.append({'type': 'Deliverable', 'name': d.name, 'due_date': d.due_date, 'status': d.get_status_display()})
            total_revisions += d.files.count()
            for r in d.readiness_levels.all():
                if r.admin_level:
                    rl_dict[r.name] = r.admin_level
                    
    members_with_roles = startup.startupmember_set.select_related('user').all()
                    
    return render(request, 'reports/startup_report.html', {
        'startup': startup,
        'milestones': milestones,
        'latest_rls': rl_dict,
        'past_due_items': past_due_items,
        'total_revisions': total_revisions,
        'members_with_roles': members_with_roles
    })

@login_required
def cohort_report_csv(request):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse("Unauthorized", status=403)
    cohort_id = request.GET.get('cohort_id')
    if not cohort_id:
        return HttpResponse("No cohort specified", status=400)
    cohort = get_object_or_404(Cohort, id=cohort_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cohort_{cohort.id}_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Cohort Name', cohort.name])
    if cohort.start_date:
        writer.writerow(['Start Date', cohort.start_date.strftime('%Y-%m-%d')])
    writer.writerow([])
    
    startups = cohort.startups.prefetch_related('milestones__deliverables', 'members').all()
    for idx, s in enumerate(startups, 1):
        writer.writerow([f'--- STARTUP {idx} REPORT ---'])
        writer.writerow(['Startup Name', s.name])
        writer.writerow(['Description', s.description or '--'])
        s.team_size = s.members.count()
        writer.writerow(['Team Size', s.team_size])
        writer.writerow(['Overall Progress (%)', s.progress])
        
        milestones = s.milestones.prefetch_related('deliverables__files', 'deliverables__comments__user').order_by('milestone_progress')
        total_revisions = sum(d.files.count() for m in milestones for d in m.deliverables.all())
        writer.writerow(['Total Revisions', total_revisions])
        
        if s.progress == 100:
            last_milestone = s.milestones.filter(status='completed').order_by('-completed_at').first()
            if last_milestone and last_milestone.completed_at:
                writer.writerow(['Completed At', last_milestone.completed_at.strftime('%Y-%m-%d')])
        
        writer.writerow([])
        
        writer.writerow(['Team Members'])
        writer.writerow(['Name', 'Role', 'Email'])
        for member in s.startupmember_set.select_related('user').all():
            name = member.user.get_full_name() or member.user.username
            role = member.role or "Member"
            email = member.user.email or "--"
            writer.writerow([name, role, email])
        writer.writerow([])
        
        writer.writerow(['Milestone', 'Deliverable', 'Status', 'Due Date', 'Uploaded At', 'Revisions', 'Admin Notes'])
        for m in milestones:
            for d in m.deliverables.all():
                due = d.due_date.strftime('%Y-%m-%d') if d.due_date else '--'
                uploaded = d.uploaded_at.strftime('%Y-%m-%d') if d.uploaded_at else '--'
                revs = len(d.files.all())
                admin_notes = [c.content for c in d.comments.all() if c.user.role in ['admin', 'super_admin']]
                notes_str = " | ".join(admin_notes) if admin_notes else "--"
                writer.writerow([m.title, d.name, d.get_status_display(), due, uploaded, revs, notes_str])
        writer.writerow([])
        writer.writerow([])
        
    return response

@login_required
def startup_report_csv(request):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse("Unauthorized", status=403)
    startup_id = request.GET.get('startup_id')
    if not startup_id:
        return HttpResponse("No startup specified", status=400)
    startup = get_object_or_404(Startup, id=startup_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="startup_{startup.id}_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Startup Name', startup.name])
    writer.writerow(['Description', startup.description or '--'])
    cohort_name = startup.cohort.name if startup.cohort else 'Unassigned'
    writer.writerow(['Cohort', cohort_name])
    team_size = startup.members.count()
    writer.writerow(['Team Size', team_size])
    writer.writerow(['Overall Progress (%)', startup.progress])
    
    milestones = startup.milestones.prefetch_related('deliverables__files', 'deliverables__comments__user').order_by('milestone_progress')
    total_revisions = sum(d.files.count() for m in milestones for d in m.deliverables.all())
    writer.writerow(['Total Revisions', total_revisions])
    
    if startup.progress == 100:
        last_milestone = startup.milestones.filter(status='completed').order_by('-completed_at').first()
        if last_milestone and last_milestone.completed_at:
            writer.writerow(['Completed At', last_milestone.completed_at.strftime('%Y-%m-%d')])
    
    writer.writerow([])
    
    writer.writerow(['Team Members'])
    writer.writerow(['Name', 'Role', 'Email'])
    for member in startup.startupmember_set.select_related('user').all():
        name = member.user.get_full_name() or member.user.username
        role = member.role or "Member"
        email = member.user.email or "--"
        writer.writerow([name, role, email])
    writer.writerow([])
    
    writer.writerow(['Milestone', 'Deliverable', 'Status', 'Due Date', 'Uploaded At', 'Revisions', 'Admin Notes'])
    for m in milestones:
        for d in m.deliverables.all():
            due = d.due_date.strftime('%Y-%m-%d') if d.due_date else '--'
            uploaded = d.uploaded_at.strftime('%Y-%m-%d') if d.uploaded_at else '--'
            revs = len(d.files.all())
            admin_notes = [c.content for c in d.comments.all() if c.user.role in ['admin', 'super_admin']]
            notes_str = " | ".join(admin_notes) if admin_notes else "--"
            writer.writerow([m.title, d.name, d.get_status_display(), due, uploaded, revs, notes_str])
            
    return response

REPORT_STYLE = """
<style>
    @page { size: a4 portrait; margin: 1cm; }
    body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #333333; }
    h1 { color: #2C3E50; border-bottom: 2px solid #2C3E50; padding-bottom: 5px; font-size: 18pt; text-align: center; margin-bottom: 20px;}
    h2 { color: #2980B9; border-bottom: 1px solid #BDC3C7; font-size: 14pt; margin-top: 20px; padding-bottom: 3px; }
    h3 { color: #34495E; font-size: 12pt; margin-top: 15px; }
    p { margin: 5px 0; line-height: 1.4; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 20px; }
    th { background-color: #ECF0F1; color: #2C3E50; font-weight: bold; text-align: left; padding: 6px; border: 1px solid #BDC3C7; }
    td { padding: 6px; border: 1px solid #BDC3C7; }
    hr { border: 0; border-top: 1px solid #BDC3C7; margin: 20px 0; }
</style>
"""

@login_required
def cohort_report_docx(request, for_pdf=False):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse("Unauthorized", status=403)
    cohort_id = request.GET.get('cohort_id')
    if not cohort_id:
        return HttpResponse("No cohort specified", status=400)
    cohort = get_object_or_404(Cohort, id=cohort_id)
    
    startups = cohort.startups.prefetch_related('milestones__deliverables', 'members').all()
    for s in startups:
        s.team_size = s.members.count()
        completed = s.milestones.filter(status='completed').order_by('-milestone_progress')
        s.latest_milestone = completed.first().title if completed.exists() else "None"
        s.current_progress = s.progress
        
    icebox_logo_src = _get_img_src(request, '/static/img/logo-light-mode.png', for_pdf=for_pdf)
    
    html = f"""<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head><title>{cohort.name} Report</title>{REPORT_STYLE}</head>
<body>"""

    if icebox_logo_src:
        html += f'<div style="text-align: center; margin-bottom: 20px;"><img src="{icebox_logo_src}" style="width: 200px; height: auto;" alt="Icebox Logo"/></div>'
        
    html += f"<h1>{cohort.name} Report</h1>"
    html += f"<p><strong>Total Startups:</strong> {startups.count()}</p>"

    for idx, s in enumerate(startups, 1):
        team_size = s.members.count()
        progress = s.progress
        milestones = s.milestones.prefetch_related('deliverables__files', 'deliverables__comments__user').order_by('milestone_progress')
        total_revisions = sum(d.files.count() for m in milestones for d in m.deliverables.all())
        
        startup_logo_src = _get_img_src(request, s.logo.url, for_pdf=for_pdf) if s.logo else ""
        
        completed_at = None
        if progress == 100:
            last_milestone = s.milestones.filter(status='completed').order_by('-completed_at').first()
            if last_milestone and last_milestone.completed_at:
                completed_at = last_milestone.completed_at.strftime('%B %d, %Y')
        
        html += f"""
<hr />
<h2>Startup {idx}: {s.name}</h2>"""

        if startup_logo_src:
            html += f'<div style="margin-bottom: 15px;"><img src="{startup_logo_src}" style="width: 120px; height: auto;" alt="{s.name} Logo"/></div>'

        html += f"""
<p><strong>Description:</strong> {s.description or 'No description provided.'}</p>
<p><strong>Team Size:</strong> {team_size} member{'s' if team_size != 1 else ''}</p>
<p><strong>Overall Progress:</strong> {progress}%</p>
<p><strong>Total Revisions:</strong> {total_revisions}</p>"""

        if completed_at:
            html += f"<p><strong>Completed At:</strong> {completed_at}</p>"

        html += """
<h3>Team Members</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
    <tr>
        <th>Name</th>
        <th>Role</th>
        <th>Email</th>
    </tr>"""
        for member in s.startupmember_set.select_related('user').all():
            name = member.user.get_full_name() or member.user.username
            role = member.role or "Member"
            email = member.user.email or "--"
            html += f"""
    <tr>
        <td>{name}</td>
        <td>{role}</td>
        <td>{email}</td>
    </tr>"""
        
        html += """</table>
<h3>Milestones</h3>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
    <tr>
        <th>Milestone</th>
        <th>Deliverable</th>
        <th>Status</th>
        <th>Due Date</th>
        <th>Uploaded At</th>
        <th>Revisions</th>
        <th>Admin Notes</th>
    </tr>"""
        for m in milestones:
            for d in m.deliverables.all():
                due = d.due_date.strftime('%Y-%m-%d') if d.due_date else '--'
                uploaded = d.uploaded_at.strftime('%Y-%m-%d') if d.uploaded_at else '--'
                revs = len(d.files.all())
                admin_notes = [c.content for c in d.comments.all() if c.user.role in ['admin', 'super_admin']]
                notes_str = "<br/>".join(admin_notes) if admin_notes else "--"
                
                html += f"""
    <tr>
        <td>{m.title}</td>
        <td>{d.name}</td>
        <td>{d.get_status_display()}</td>
        <td>{due}</td>
        <td>{uploaded}</td>
        <td>{revs}</td>
        <td>{notes_str}</td>
    </tr>"""
        html += """</table>"""
        
    html += """</body></html>"""
    
    response = HttpResponse(html, content_type='application/msword')
    response['Content-Disposition'] = f'attachment; filename="cohort_{cohort.id}_report.doc"'
    return response

@login_required
def startup_report_docx(request, for_pdf=False):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse("Unauthorized", status=403)
    startup_id = request.GET.get('startup_id')
    if not startup_id:
        return HttpResponse("No startup specified", status=400)
    startup = get_object_or_404(Startup, id=startup_id)
    
    team_size = startup.members.count()
    cohort_name = startup.cohort.name if startup.cohort else 'Unassigned'
    progress = startup.progress
    
    milestones = startup.milestones.prefetch_related('deliverables__files', 'deliverables__comments__user').order_by('milestone_progress')
    total_revisions = sum(d.files.count() for m in milestones for d in m.deliverables.all())
    
    icebox_logo_src = _get_img_src(request, '/static/img/logo-light-mode.png', for_pdf=for_pdf)
    startup_logo_src = _get_img_src(request, startup.logo.url, for_pdf=for_pdf) if startup.logo else ""
    
    completed_at = None
    if progress == 100:
        last_milestone = startup.milestones.filter(status='completed').order_by('-completed_at').first()
        if last_milestone and last_milestone.completed_at:
            completed_at = last_milestone.completed_at.strftime('%B %d, %Y')
            
    html = f"""<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head><title>Startup Report: {startup.name}</title>{REPORT_STYLE}</head>
<body>"""

    if icebox_logo_src:
        html += f'<div style="text-align: center; margin-bottom: 20px;"><img src="{icebox_logo_src}" style="width: 200px; height: auto;" alt="Icebox Logo"/></div>'
        
    html += f"<h1>Startup Report: {startup.name}</h1>"
    
    if startup_logo_src:
        html += f'<div style="margin-bottom: 15px;"><img src="{startup_logo_src}" style="width: 120px; height: auto;" alt="{startup.name} Logo"/></div>'
        
    html += f"""
<p><strong>Description:</strong> {startup.description or 'No description provided.'}</p>
<p><strong>Cohort:</strong> {cohort_name}</p>
<p><strong>Team Size:</strong> {team_size} member{'s' if team_size != 1 else ''}</p>
<p><strong>Overall Progress:</strong> {progress}%</p>
<p><strong>Total Revisions:</strong> {total_revisions}</p>
"""
    if completed_at:
        html += f"<p><strong>Completed At:</strong> {completed_at}</p>"

    html += """
<h2>Team Members</h2>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
    <tr>
        <th>Name</th>
        <th>Role</th>
        <th>Email</th>
    </tr>"""
    for member in startup.startupmember_set.select_related('user').all():
        name = member.user.get_full_name() or member.user.username
        role = member.role or "Member"
        email = member.user.email or "--"
        html += f"""
    <tr>
        <td>{name}</td>
        <td>{role}</td>
        <td>{email}</td>
    </tr>"""
    html += """</table>"""
    html += """
<h2>Milestones</h2>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
    <tr>
        <th>Milestone</th>
        <th>Deliverable</th>
        <th>Status</th>
        <th>Due Date</th>
        <th>Uploaded At</th>
        <th>Revisions</th>
        <th>Admin Notes</th>
    </tr>"""
    
    for m in milestones:
        for d in m.deliverables.all():
            due = d.due_date.strftime('%Y-%m-%d') if d.due_date else '--'
            uploaded = d.uploaded_at.strftime('%Y-%m-%d') if d.uploaded_at else '--'
            revs = len(d.files.all())
            admin_notes = [c.content for c in d.comments.all() if c.user.role in ['admin', 'super_admin']]
            notes_str = "<br/>".join(admin_notes) if admin_notes else "--"
            
            html += f"""
    <tr>
        <td>{m.title}</td>
        <td>{d.name}</td>
        <td>{d.get_status_display()}</td>
        <td>{due}</td>
        <td>{uploaded}</td>
        <td>{revs}</td>
        <td>{notes_str}</td>
    </tr>"""
    html += """</table></body></html>"""
    
    response = HttpResponse(html, content_type='application/msword')
    response['Content-Disposition'] = f'attachment; filename="startup_{startup.id}_report.doc"'
    return response

@login_required
def startup_report_pdf(request):
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
    except ImportError:
        return HttpResponse("Please install xhtml2pdf (pip install xhtml2pdf) to use this feature.", status=501)
        
    docx_response = startup_report_docx(request, for_pdf=True)
    if docx_response.status_code != 200:
        return docx_response
        
    html_content = docx_response.content.decode('utf-8')
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        startup_id = request.GET.get('startup_id')
        response['Content-Disposition'] = f'attachment; filename="startup_{startup_id}_report.pdf"'
        return response
    return HttpResponse("Error generating PDF", status=500)

@login_required
def cohort_report_pdf(request):
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
    except ImportError:
        return HttpResponse("Please install xhtml2pdf (pip install xhtml2pdf) to use this feature.", status=501)
        
    docx_response = cohort_report_docx(request, for_pdf=True)
    if docx_response.status_code != 200:
        return docx_response
        
    html_content = docx_response.content.decode('utf-8')
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        cohort_id = request.GET.get('cohort_id')
        response['Content-Disposition'] = f'attachment; filename="cohort_{cohort_id}_report.pdf"'
        return response
    return HttpResponse("Error generating PDF", status=500)

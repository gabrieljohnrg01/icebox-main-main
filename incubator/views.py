from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from .models import User, Startup, StartupMember, ProgressReport, Milestone, Deliverable, DeliverableFile, Readiness, MilestoneReadiness, Comment, Notification, MilestoneTemplate, DeliverableTemplate, FBAnnouncement, Cohort, RLTemplate, RLTemplateLevel
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import translation
from django.utils.html import escape
from django.conf import settings
from .forms import LoginForm, StartupForm, AdminCreationForm, ProgressReportForm, StartupMemberForm
from .validators import validate_deliverable_file, validate_image_file
from django.db.models import Count, Exists, OuterRef, Prefetch, Max, Q
from django.shortcuts import HttpResponse
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
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
    return None


def _can_access_startup(user, startup):
    return (
        user.role in ['admin', 'super_admin']
        or user == startup.owner
        or startup.members.filter(id=user.id).exists()
    )


def _send_notification(recipient, message, link=''):
    """
    Safely creates a Notification ensuring message and link do not exceed max_length 255.
    """
    if not recipient:
        return None
    trimmed_msg = (message[:251] + '...') if len(message) > 254 else message
    trimmed_link = link[:255] if link else ''
    return Notification.objects.create(recipient=recipient, message=trimmed_msg, link=trimmed_link)


import json
import logging
import smtplib
from .email_utils import AccountEmailError, send_deliverable_status_email, send_new_account_credentials

logger = logging.getLogger(__name__)

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
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('login')
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'confirm_logout.html')

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
    startups = list(Startup.objects.select_related('owner', 'cohort').prefetch_related(
        'milestones',
    ).annotate(
        members_count=Count('startupmember')
    ))
    
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
        'total_startups': len(startups),
        'total_admins': admins.count(),
        'total_users': User.objects.count(),
        'deliverable_dates': json.dumps(deliverable_dates_dict),
        'upcoming_deliverables': upcoming_deliverables,
        'fb_announcements': FBAnnouncement.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/super_admin.html', context)

def admin_dashboard(request):
    startups = list(Startup.objects.select_related('owner', 'cohort').prefetch_related(
        'milestones',
    ).annotate(
        members_count=Count('startupmember')
    ))
    
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
        'total_startups': len(startups),
        'total_users': User.objects.count(),
        'deliverable_dates': json.dumps(deliverable_dates_dict),
        'upcoming_deliverables': upcoming_deliverables,
        'fb_announcements': FBAnnouncement.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/admin.html', context)

def incubatee_dashboard(request):
    startups = list(request.user.startups.select_related('cohort', 'owner').prefetch_related('milestones__deliverables').all())

    # Pre-calculate current milestone for each startup
    for startup in startups:
        startup.current_milestone = None
        for milestone in startup.milestones.all().order_by('milestone_progress'):
            if milestone.status != 'completed' and not milestone.is_locked():
                startup.current_milestone = milestone
                break

    if len(startups) == 1:
        return redirect('view_startup', startup_id=startups[0].id)

    context = {'startups': startups}
    return render(request, 'dashboard/incubatee.html', context)

@login_required
def add_admin(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            temporary_password = get_random_string(16)
            try:
                with transaction.atomic():
                    admin_user = form.save(commit=False)
                    admin_user.created_by = request.user
                    admin_user.set_password(temporary_password)
                    admin_user.must_change_password = True
                    admin_user.save()
                    send_new_account_credentials(
                        admin_user,
                        temporary_password,
                        request.build_absolute_uri(reverse('login')),
                    )
            except (AccountEmailError, smtplib.SMTPException, OSError):
                logger.exception("Failed to create administrator account or send credentials.")
                messages.error(request, 'The account could not be created because the credentials email could not be sent. Please try again.')
                return render(request, 'super_admin/add_admin.html', {'form': form})
            messages.success(request, f'Admin {admin_user.username} created!')
            return redirect('dashboard')
    else:
        form = AdminCreationForm()
    return render(request, 'super_admin/add_admin.html', {'form': form})

@login_required
@require_POST
def delete_user(request, user_id):
    # Allow Super Admin and Admin to access
    if request.user.role not in ['super_admin', 'admin']:
        return redirect('dashboard')
        
    target_user = get_object_or_404(User, id=user_id)
    
    # Protections
    if target_user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('dashboard')

    if target_user.role == 'super_admin':
        messages.error(request, 'Cannot delete Super Admin.')
        return redirect('dashboard')
        
    if request.user.role == 'admin':
        # Admin can ONLY delete Incubatees
        if target_user.role != 'incubatee':
            messages.error(request, 'Admins can only delete Incubatees.')
            return redirect('dashboard')

    # Prevent deleting user who owns active startups to protect data integrity
    if target_user.owned_startups.exists():
        startup_names = ", ".join([s.name for s in target_user.owned_startups.all()])
        messages.error(
            request, 
            f'Cannot delete user "{target_user.username}" because they own active startup(s): {startup_names}. '
            f'Please reassign startup ownership before deleting this user.'
        )
        return redirect('dashboard')
            
    target_user.delete()
    messages.success(request, f'User {target_user.username} deleted.')
    return redirect('dashboard')

@login_required
def startups_list(request):
    # Allow admins and super admins
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')

    startups = list(Startup.objects.select_related('cohort', 'owner').prefetch_related(
        'milestones',
        'milestones__deliverables'
    ))

    for startup in startups:
        startup.current_milestone = None
        for milestone in startup.milestones.all():
            if milestone.status != 'completed' and not milestone.is_locked():
                startup.current_milestone = milestone
                break

    context = {
        'startups': startups,
        'cohorts': Cohort.objects.all().order_by('-start_date'),
        'total_startups': len(startups),
        'total_users': User.objects.count(),
    }
    return render(request, 'startups/list.html', context)

@login_required
@require_POST
def archive_startup(request, startup_id):
    # Allow Super Admin and Admin
    if request.user.role not in ['super_admin', 'admin']:
        return redirect('dashboard')
        
    startup = get_object_or_404(Startup, id=startup_id)
    startup.is_archived = True
    startup.archived_at = timezone.now()
    startup.save(update_fields=['is_archived', 'archived_at'])
    
    admin_name = request.user.get_full_name() or request.user.username
    arch_msg = f"📁 Startup '{startup.name}' was archived by {admin_name}."
    recipients = set(list(startup.members.all()) + ([startup.owner] if startup.owner else []))
    for recipient in recipients:
        if recipient != request.user:
            _send_notification(recipient, arch_msg, reverse('startups_list'))

    messages.success(request, f'Startup "{startup.name}" has been archived successfully.')
    return redirect('startups_list')

@login_required
@require_POST
def unarchive_startup(request, startup_id):
    # Allow Super Admin and Admin
    if request.user.role not in ['super_admin', 'admin']:
        return redirect('dashboard')
        
    startup = get_object_or_404(Startup, id=startup_id)
    startup.is_archived = False
    startup.archived_at = None
    startup.save(update_fields=['is_archived', 'archived_at'])
    
    admin_name = request.user.get_full_name() or request.user.username
    unarch_msg = f"📂 Startup '{startup.name}' was restored from archive by {admin_name}."
    recipients = set(list(startup.members.all()) + ([startup.owner] if startup.owner else []))
    for recipient in recipients:
        if recipient != request.user:
            _send_notification(recipient, unarch_msg, reverse('view_startup', args=[startup.id]))

    messages.success(request, f'Startup "{startup.name}" has been restored from archive.')
    return redirect('view_startup', startup_id=startup.id)

# Alias for backward compatibility
delete_startup = archive_startup

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
                for position, dt in enumerate(mt.deliverable_templates.all()):
                    Deliverable.objects.create(
                        milestone=milestone,
                        position=position,
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
    startup = get_object_or_404(Startup.objects.select_related('cohort', 'owner'), id=startup_id)
    if not _can_access_startup(request.user, startup):
        return redirect('dashboard')

    milestones = list(startup.milestones.prefetch_related('deliverables').all())
    reports = startup.progress_reports.select_related('submitted_by').order_by('-submitted_at')
    
    # Calculate current milestone (first one that's not completed and not locked)
    current_milestone = None
    current_milestone_id = None
    current_deliverable = None
    for milestone in milestones:
        if milestone.status != 'completed' and not milestone.is_locked():
            current_milestone = milestone
            current_milestone_id = milestone.id
            current_deliverable = next((d for d in milestone.deliverables.all() if d.status in ['pending', 'submitted']), None)
            break
    
    completed_milestones_count = sum(1 for m in milestones if m.status == 'completed')
    total_milestones_count = len(milestones)
    startup_members = startup.members.all()
    
    context = {
        'startup': startup,
        'milestones': milestones,
        'reports': reports,
        'current_milestone_id': current_milestone_id,
        'current_milestone': current_milestone,
        'current_deliverable': current_deliverable,
        'startup_members': startup_members,
        'completed_milestones_count': completed_milestones_count,
        'total_milestones_count': total_milestones_count,
    }
    return render(request, 'startups/view.html', context)

@login_required
def edit_startup(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id)
    
    if not _can_access_startup(request.user, startup):
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
        file_names = []
        if request.FILES.getlist('file'):
            for f in request.FILES.getlist('file'):
                is_valid, err = validate_deliverable_file(f)
                if not is_valid:
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    continue
                DeliverableFile.objects.create(deliverable=deliverable, file=f, uploaded_by_role='admin')
                file_names.append(f.name)
        
        link_url = request.POST.get('link_url')
        link_title = None
        if link_url:
            link_title = get_link_title_safe(link_url) or link_url
            DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, link_title=link_title, uploaded_by_role='admin')
            
        link = reverse('edit_deliverable_page', args=[deliverable.id])
        admin_name = request.user.get_full_name() or request.user.username
        startup = deliverable.milestone.startup
        
        if file_names:
            names_str = ", ".join(file_names[:2]) + (f" (+{len(file_names)-2} more)" if len(file_names) > 2 else "")
            msg = f"📎 Admin {admin_name} added resource '{names_str}' to deliverable '{deliverable.name}' ({startup.name})"
        elif link_title:
            msg = f"🔗 Admin {admin_name} added resource link '{link_title}' to deliverable '{deliverable.name}' ({startup.name})"
        else:
            msg = f"📎 Admin {admin_name} attached a resource to deliverable '{deliverable.name}' ({startup.name})"

        members = list(startup.members.all())
        recipients = set(members)
        if startup.owner:
            recipients.add(startup.owner)
        for recipient in recipients:
            if recipient != request.user:
                _send_notification(recipient=recipient, message=msg, link=link)
            
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

    # Prevent incubatees from modifying locked milestones
    if request.user.role not in ['admin', 'super_admin'] and deliverable.milestone.is_locked():
        lock_msg = 'This milestone is locked. Complete previous milestones first.'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': lock_msg}, status=403)
        messages.error(request, lock_msg)
        return redirect('view_startup', startup_id=startup.id)

    if request.method == 'POST':
        file_names = []
        if request.FILES.getlist('file'):
            for f in request.FILES.getlist('file'):
                is_valid, err = validate_deliverable_file(f)
                if not is_valid:
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    continue
                DeliverableFile.objects.create(deliverable=deliverable, file=f, uploaded_by_role='incubatee')
                file_names.append(f.name)
                
        link_url = request.POST.get('link_url')
        link_title = None
        if link_url:
            link_title = get_link_title_safe(link_url) or link_url
            DeliverableFile.objects.create(deliverable=deliverable, link_url=link_url, link_title=link_title, uploaded_by_role='incubatee')
            
        text_content = request.POST.get('text_content')
        if text_content:
            DeliverableFile.objects.create(deliverable=deliverable, text_content=text_content, uploaded_by_role='incubatee')
            
        # Automatically update status to 'submitted' so the timeline and admin queue reflect it
        if deliverable.status in ['pending', 'not_started', 'rejected']:
            deliverable.status = 'submitted'
            deliverable.save()
            
        link = reverse('edit_deliverable_page', args=[deliverable.id])
        user_name = request.user.get_full_name() or request.user.username
        m_num = deliverable.milestone.milestone_progress
        
        if file_names:
            names_str = ", ".join(file_names[:2]) + (f" (+{len(file_names)-2} more)" if len(file_names) > 2 else "")
            msg = f"📥 {user_name} ({startup.name}) submitted file '{names_str}' for '{deliverable.name}' (M{m_num})"
        elif link_title:
            msg = f"📥 {user_name} ({startup.name}) submitted link '{link_title}' for '{deliverable.name}' (M{m_num})"
        elif text_content:
            snippet = text_content[:40] + ('...' if len(text_content) > 40 else '')
            msg = f"📥 {user_name} ({startup.name}) submitted response for '{deliverable.name}' (M{m_num}): \"{snippet}\""
        else:
            msg = f"📥 {user_name} ({startup.name}) submitted work for '{deliverable.name}' (Milestone {m_num})"

        admins = User.objects.filter(role__in=['admin', 'super_admin'])
        for admin in admins:
            if admin != request.user:
                _send_notification(recipient=admin, message=msg, link=link)
            
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
            
            base_username = f"{last_name.lower()}.{first_name.lower()}".replace(" ", "")
            temporary_password = get_random_string(16)
            try:
                with transaction.atomic():
                    user_defaults = {
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'middle_name': middle_name,
                        'contact_number': contact,
                        'role': 'incubatee',
                        'password': make_password(temporary_password),
                        'must_change_password': True,
                    }
                    user = None
                    created = False
                    counter = 0
                    while user is None:
                        username = base_username if counter == 0 else f'{base_username}{counter}'
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults=user_defaults,
                        )
                        if not created and user.email != email:
                            user = None
                            counter += 1

                    if not created:
                        if user.role != 'incubatee':
                            messages.error(request, 'Cannot add an admin account as a startup member.')
                            return redirect('add_member', startup_id=startup.id)
                        if StartupMember.objects.filter(startup=startup, user=user).exists():
                            messages.error(request, 'This user is already a member of this startup.')
                            return redirect('add_member', startup_id=startup.id)
                        StartupMember.objects.create(startup=startup, user=user, role=position)
                        messages.success(
                            request,
                            f'Existing member {user.get_full_name() or user.username} linked to {startup.name} successfully!',
                        )
                    else:
                        StartupMember.objects.create(
                            startup=startup,
                            user=user,
                            role=position,
                        )
                        send_new_account_credentials(
                            user,
                            temporary_password,
                            request.build_absolute_uri(reverse('login')),
                        )
            except (AccountEmailError, smtplib.SMTPException, OSError):
                logger.exception("Failed to create startup member account or send credentials.")
                messages.error(request, 'The account could not be created because the credentials email could not be sent. Please try again.')
                return render(request, 'startups/add_member.html', {'form': form, 'startup': startup})

            if created:
                messages.success(request, f'Member {first_name} added! Login credentials were sent to {email}.')
            if request.POST.get('action') == 'save_and_view':
                return redirect('view_startup', startup_id=startup.id)
            return redirect('add_member', startup_id=startup.id)
    else:
        form = StartupMemberForm()

    return render(request, 'startups/add_member.html', {'form': form, 'startup': startup})


@login_required
@require_POST
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
        
        for position, i in enumerate(range(1, deliverable_count + 1)):
            Deliverable.objects.create(
                milestone=m,
                position=position,
                name=f"Deliverable {i}",
                status='pending'
            )
            
        messages.success(request, f'Milestone {next_num} added!')
    
    return redirect('view_startup', startup_id=startup.id)

@login_required
def submit_progress(request, startup_id):
    startup = get_object_or_404(Startup, id=startup_id)
    if not _can_access_startup(request.user, startup):
        return redirect('dashboard')

    current_milestone = None
    current_deliverable = None
    for milestone in startup.milestones.order_by('milestone_progress'):
        if milestone.status != 'completed' and not milestone.is_locked():
            current_milestone = milestone
            current_deliverable = milestone.deliverables.filter(status__in=['pending', 'submitted']).first()
            break

    if request.method == 'POST':
        form = ProgressReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.startup = startup
            report.submitted_by = request.user
            report.save()
            
            user_name = request.user.get_full_name() or request.user.username
            report_msg = f"📊 {user_name} submitted progress report for {startup.name}: '{report.title}'"
            report_link = reverse('reports')
            for admin in User.objects.filter(role__in=['admin', 'super_admin']):
                if admin != request.user:
                    _send_notification(admin, report_msg, report_link)

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
    if not _can_access_startup(request.user, startup):
        return redirect('dashboard')

    deliverables = list(milestone.deliverables.select_related('template').prefetch_related(
        'readiness_levels',
        'comments__user',
        'files'
    ).order_by('position', 'id'))
    
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
        comments = [{'user': c.user.username, 'content': c.content, 'date': c.created_at.strftime("%b %d, %Y %H:%M")} for c in sorted(d.comments.all(), key=lambda c: c.created_at, reverse=True)]
        admin_files = [{'id': f.id, 'url': f.file.url if f.file else f.link_url, 'name': f.file.name.split('/')[-1] if f.file else (f.link_title or f.link_url)} for f in d.files.all() if f.uploaded_by_role == 'admin' and (f.file or f.link_url)]
        incubatee_files = [{'id': f.id, 'url': f.file.url if f.file else f.link_url, 'name': f.file.name.split('/')[-1] if f.file else (f.link_title or f.link_url), 'is_text': bool(f.text_content), 'text_content': f.text_content} for f in d.files.all() if f.uploaded_by_role == 'incubatee' and (f.file or f.link_url or f.text_content)]
        
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
    milestone_readiness_by_name = {
        assessment.name: assessment
        for assessment in milestone.readiness_levels.all()
    }
    milestone_readiness_rows = []
    for template in rl_templates_db:
        assessment = milestone_readiness_by_name.get(template.name)
        level_options = []
        for level in template.levels.all():
            value = f'Level {level.level}'
            level_options.append({
                'value': value,
                'description': level.description,
                'incubatee_selected': assessment is not None and assessment.incubatee_level == value,
                'admin_selected': assessment is not None and assessment.admin_level == value,
            })
        milestone_readiness_rows.append({
            'template': template,
            'assessment': assessment,
            'level_options': level_options,
        })

    rl_data = {}
    for rlt in rl_templates_db:
        rl_data[rlt.name] = {}
        for lvl in rlt.levels.all():
            rl_data[rlt.name][str(lvl.level)] = {
                'description': lvl.description
            }
    
    total_deliverables = len(deliverables_data)
    approved_count = sum(1 for d in deliverables if d.status == 'approved')
    in_review_count = sum(1 for d in deliverables if d.status == 'submitted')
    needs_attention_count = sum(1 for d in deliverables if d.status == 'rejected')
    pending_count = sum(1 for d in deliverables if d.status in ['pending', 'not_started'])

    context = {
        'startup': startup,
        'milestone': milestone,
        'deliverables_data': deliverables_data,
        'total_deliverables': total_deliverables,
        'approved_count': approved_count,
        'in_review_count': in_review_count,
        'needs_attention_count': needs_attention_count,
        'pending_count': pending_count,
        'is_locked': is_locked,
        'can_reorder_deliverables': request.user.role in ['admin', 'super_admin'] and not is_locked,
        'rl_templates': rl_templates_db,
        'milestone_readiness_rows': milestone_readiness_rows,
        'is_admin': request.user.role in ['admin', 'super_admin'],
        'rl_data_json': json.dumps(rl_data),
    }
    return render(request, 'startups/view_milestone.html', context)


@login_required
@require_POST
def update_milestone_readiness(request, startup_id, milestone_id):
    startup = get_object_or_404(Startup, id=startup_id)
    milestone = get_object_or_404(Milestone, id=milestone_id, startup=startup)
    if not _can_access_startup(request.user, startup):
        return HttpResponse('Forbidden', status=403)

    is_admin = request.user.role in ['admin', 'super_admin']
    if milestone.is_locked() and not is_admin:
        messages.error(request, 'This milestone is locked. Complete the previous milestone first.')
        return redirect('view_startup', startup_id=startup.id)

    with transaction.atomic():
        templates = RLTemplate.objects.prefetch_related('levels').order_by('id')
        for template in templates:
            field_prefix = f'milestone_rl_{template.id}'
            valid_levels = {f'Level {level.level}' for level in template.levels.all()}

            if is_admin:
                if request.POST.get(f'{field_prefix}_enabled') != 'on':
                    MilestoneReadiness.objects.filter(
                        milestone=milestone,
                        name=template.name,
                    ).delete()
                    continue

                assessment, _ = MilestoneReadiness.objects.get_or_create(
                    milestone=milestone,
                    name=template.name,
                )
                selected_level = request.POST.get(f'{field_prefix}_admin_level', '')
                if not selected_level or selected_level in valid_levels:
                    assessment.admin_level = selected_level or None
                assessment.save(update_fields=['admin_level'])
                continue

            assessment = MilestoneReadiness.objects.filter(
                milestone=milestone,
                name=template.name,
            ).first()
            if assessment is None:
                continue

            selected_level = request.POST.get(f'{field_prefix}_incubatee_level', '')
            if not selected_level or selected_level in valid_levels:
                assessment.incubatee_level = selected_level or None
                assessment.save(update_fields=['incubatee_level'])

    messages.success(request, 'Milestone readiness assessment updated.')
    return redirect('view_milestone', startup_id=startup.id, milestone_id=milestone.id)


@login_required
def reorder_deliverables(request, milestone_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)

    milestone = get_object_or_404(Milestone, id=milestone_id)
    startup = milestone.startup
    can_reorder = (
        request.user.role in ['admin', 'super_admin']
        or request.user == startup.owner
    )
    if not can_reorder:
        return JsonResponse({'error': 'You do not have permission to reorder deliverables.'}, status=403)
    if milestone.is_locked():
        return JsonResponse({'error': 'This milestone is locked.'}, status=403)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON request.'}, status=400)

    deliverable_ids = payload.get('deliverable_ids') if isinstance(payload, dict) else None
    if (
        not isinstance(deliverable_ids, list)
        or any(type(deliverable_id) is not int for deliverable_id in deliverable_ids)
        or len(deliverable_ids) != len(set(deliverable_ids))
    ):
        return JsonResponse({'error': 'A unique list of deliverable IDs is required.'}, status=400)

    with transaction.atomic():
        deliverables = list(milestone.deliverables.all())
        if set(deliverable_ids) != {deliverable.id for deliverable in deliverables}:
            return JsonResponse({'error': 'The deliverables do not match this milestone.'}, status=400)

        positions = {deliverable_id: position for position, deliverable_id in enumerate(deliverable_ids)}
        for deliverable in deliverables:
            deliverable.position = positions[deliverable.id]
        if deliverables:
            Deliverable.objects.bulk_update(deliverables, ['position'])

    return JsonResponse({'success': True})


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
            
            admin_name = request.user.get_full_name() or request.user.username
            m_title = milestone.title or f"Milestone {milestone.milestone_progress}"
            status_msg = f"📌 {admin_name} updated Milestone '{m_title}' ({startup.name}) status to '{milestone.get_status_display()}'."
            status_link = reverse('view_milestone', args=[startup.id, milestone.id])
            recipients = set(list(startup.members.all()) + ([startup.owner] if startup.owner else []))
            for recipient in recipients:
                if recipient != request.user:
                    _send_notification(recipient, status_msg, status_link)

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
            max_position = milestone.deliverables.aggregate(max_position=Max('position'))['max_position']
            Deliverable.objects.create(
                milestone=milestone,
                position=(max_position + 1) if max_position is not None else 0,
                name=name,
                requirements=requirements,
                due_date=due_date or None,
                status='pending'
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
    if not _can_access_startup(request.user, startup):
        return redirect('dashboard')
    
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
        'rls_dict_raw': rls_dict,
        'global_template_data': global_template_data,
        'global_template_link': global_template_link,
        'global_template_link_title': global_template_link_title,
        'rl_types': rl_types,
        'rl_data_json': json.dumps(rl_data),
        'rl_data_raw': rl_data,
    }
    return render(request, 'startups/edit_deliverable.html', context)

@login_required
def update_deliverable_details(request, deliverable_id):
    deliverable = get_object_or_404(Deliverable, id=deliverable_id)
    startup_id = deliverable.milestone.startup.id
    milestone_id = deliverable.milestone.id
    if not _can_access_startup(request.user, deliverable.milestone.startup):
        return redirect('dashboard')

    is_admin = request.user.role in ['admin', 'super_admin']

    # Prevent incubatees from modifying deliverables on locked milestones
    if not is_admin and deliverable.milestone.is_locked():
        messages.error(request, 'This milestone is locked. Complete previous milestones first.')
        return redirect('view_startup', startup_id=startup_id)

    if request.method == 'POST':
        action = request.POST.get('action') # 'save', 'revision', 'done'
        startup = deliverable.milestone.startup
        members = list(startup.members.all())
        recipients = set(members + ([startup.owner] if startup.owner else []))
        
        # Update requirements and due date (only admins can change these)
        req_or_date_changed = False
        if is_admin:
            requirements = request.POST.get('requirements')
            due_date = request.POST.get('due_date')
            if requirements is not None and requirements != deliverable.requirements:
                deliverable.requirements = requirements
                req_or_date_changed = True
            if due_date and str(due_date) != str(deliverable.due_date):
                deliverable.due_date = due_date
                req_or_date_changed = True
            
        if is_admin:
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
            admin_name = request.user.get_full_name() or request.user.username
            deliv_link = reverse('edit_deliverable_page', args=[deliverable.id])

            if action == 'revision':
                deliverable.status = 'rejected'
                messages.warning(request, f'Revision requested for {deliverable.name}.')
                raw_comment = (request.POST.get('revision_comment') or request.POST.get('comment') or '').strip()
                comment_text = f"⚠️ REVISION REQUESTED:\n{raw_comment}" if raw_comment else ""
                
                # Check for new due date
                revision_due_date = request.POST.get('revision_due_date')
                if revision_due_date:
                    deliverable.due_date = revision_due_date
                
                # Check for annotated file upload
                revision_file = request.FILES.get('revision_file')
                if revision_file:
                    is_valid, err = validate_deliverable_file(revision_file)
                    if not is_valid:
                        messages.error(request, f"Revision file rejected: {err}")
                    else:
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

                # Send precise notification to incubatees
                due_part = f" · New deadline: {revision_due_date}" if revision_due_date else ""
                note_part = f" · Note: \"{raw_comment[:45]}...\"" if len(raw_comment) > 45 else (f" · Note: \"{raw_comment}\"" if raw_comment else "")
                rev_msg = f"🔄 Revision requested for '{deliverable.name}' ({startup.name}) by {admin_name}{due_part}{note_part}"
                for recipient in recipients:
                    if recipient != request.user:
                        _send_notification(recipient, rev_msg, deliv_link)

            elif action == 'done':
                deliverable.status = 'approved'
                messages.success(request, f'Deliverable {deliverable.name} approved.')
                raw_comment = (request.POST.get('revision_comment') or request.POST.get('comment') or '').strip()
                comment_text = f"✅ DELIVERABLE APPROVED:\n{raw_comment}" if raw_comment else ""
                # Send email notification to incubatees
                send_deliverable_status_email(
                    deliverable=deliverable,
                    action='done',
                    admin_user=request.user,
                    comment=comment_text or None,
                )

                # Send precise notification to incubatees
                note_part = f" · Note: \"{raw_comment[:45]}...\"" if len(raw_comment) > 45 else (f" · Note: \"{raw_comment}\"" if raw_comment else "")
                app_msg = f"✅ Deliverable '{deliverable.name}' for {startup.name} was approved by {admin_name}{note_part}"
                for recipient in recipients:
                    if recipient != request.user:
                        _send_notification(recipient, app_msg, deliv_link)

            elif req_or_date_changed:
                save_msg = f"📝 Admin {admin_name} updated instructions/requirements for '{deliverable.name}' ({startup.name})."
                for recipient in recipients:
                    if recipient != request.user:
                        _send_notification(recipient, save_msg, deliv_link)
                
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
            # If standalone comment was posted (not action == revision/done), notify the other party
            if action not in ['revision', 'done']:
                deliv_link = reverse('edit_deliverable_page', args=[deliverable.id])
                snippet = comment_text[:50] + ('...' if len(comment_text) > 50 else '')
                if is_admin:
                    c_msg = f"💬 Admin {request.user.get_full_name() or request.user.username} commented on '{deliverable.name}' ({startup.name}): \"{snippet}\""
                    for recipient in recipients:
                        if recipient != request.user:
                            _send_notification(recipient, c_msg, deliv_link)
                else:
                    user_name = request.user.get_full_name() or request.user.username
                    c_msg = f"💬 {user_name} ({startup.name}) commented on '{deliverable.name}': \"{snippet}\""
                    for admin in User.objects.filter(role__in=['admin', 'super_admin']):
                        if admin != request.user:
                            _send_notification(admin, c_msg, deliv_link)

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
                
                m_title = milestone.title or f"Milestone {milestone.milestone_progress}"
                complete_msg = f"🎉 Milestone '{m_title}' for {startup.name} is completed! All deliverables approved."
                complete_link = reverse('view_milestone', args=[startup.id, milestone.id])
                
                all_party = set(recipients)
                all_party.update(User.objects.filter(role__in=['admin', 'super_admin']))
                for party_user in all_party:
                    if party_user != request.user:
                        _send_notification(party_user, complete_msg, complete_link)

        if not messages.get_messages(request):
            messages.success(request, 'Deliverable details updated successfully.')
            
    return redirect('edit_deliverable_page', deliverable_id=deliverable.id)

@login_required
def set_password(request):
    if request.user.has_usable_password() and not request.user.must_change_password:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.must_change_password = False
            user.save(update_fields=['password', 'must_change_password'])
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
                pic = request.FILES['profile_picture']
                is_valid, err = validate_image_file(pic)
                if not is_valid:
                    messages.error(request, err)
                    return redirect('settings')
                # Delete old picture file if exists
                if user.profile_picture:
                    user.profile_picture.delete(save=False)
                user.profile_picture = pic
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
                    max_position = milestone.deliverables.aggregate(max_position=Max('position'))['max_position']
                    next_position = (max_position + 1) if max_position is not None else 0
                    for position, dt in enumerate(newmilestone_template.deliverable_templates.all(), start=next_position):
                        Deliverable.objects.create(
                            milestone=milestone,
                            position=position,
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
    if request.user.role != 'super_admin':
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
def edit_milestone_template(request, template_id):
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

class PseudoCohort:
    def __init__(self, id_val, name_val, start_date=None):
        self.id = id_val
        self.name = name_val
        self.start_date = start_date

@login_required
def reports_view(request):
    if request.user.role not in ['admin', 'super_admin']:
        messages.error(request, 'Unauthorized access to Reports.')
        return redirect('dashboard')
    cohorts = Cohort.objects.all().order_by('-start_date')
    startups = Startup.objects.all().select_related('cohort').prefetch_related('members').order_by('name')
    for s in startups:
        s.team_size = s.members.count()
    progress_reports = ProgressReport.objects.select_related('startup', 'submitted_by').order_by('-submitted_at')[:50]
    return render(request, 'reports/index.html', {
        'cohorts': cohorts,
        'startups': startups,
        'progress_reports': progress_reports,
    })

@login_required
def cohort_report(request):
    from datetime import date
    if request.user.role not in ['admin', 'super_admin']:
        messages.error(request, 'Unauthorized access to Reports.')
        return redirect('dashboard')
    cohort_id = request.GET.get('cohort_id')
    if not cohort_id:
        return redirect('reports')
    
    if cohort_id == 'all':
        cohort = PseudoCohort('all', 'All Cohorts & Startups')
        startups = Startup.objects.prefetch_related('milestones__deliverables', 'members').all()
    elif cohort_id == 'unassigned':
        cohort = PseudoCohort('unassigned', 'Unassigned Startups')
        startups = Startup.objects.filter(cohort__isnull=True).prefetch_related('milestones__deliverables', 'members')
    else:
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
    progress_reports = startup.progress_reports.select_related('submitted_by').order_by('-submitted_at')
                    
    return render(request, 'reports/startup_report.html', {
        'startup': startup,
        'milestones': milestones,
        'latest_rls': rl_dict,
        'past_due_items': past_due_items,
        'total_revisions': total_revisions,
        'members_with_roles': members_with_roles,
        'progress_reports': progress_reports,
    })

@login_required
def cohort_report_csv(request):
    if request.user.role not in ['admin', 'super_admin']:
        return HttpResponse("Unauthorized", status=403)
    cohort_id = request.GET.get('cohort_id')
    if not cohort_id:
        return HttpResponse("No cohort specified", status=400)
    
    if cohort_id == 'all':
        cohort_name = 'All Cohorts & Startups'
        filename = 'all_startups_report.csv'
        start_date_val = None
        startups = Startup.objects.prefetch_related('milestones__deliverables', 'members').all()
    elif cohort_id == 'unassigned':
        cohort_name = 'Unassigned Startups'
        filename = 'unassigned_startups_report.csv'
        start_date_val = None
        startups = Startup.objects.filter(cohort__isnull=True).prefetch_related('milestones__deliverables', 'members')
    else:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        cohort_name = cohort.name
        filename = f'cohort_{cohort.id}_report.csv'
        start_date_val = cohort.start_date.strftime('%Y-%m-%d') if cohort.start_date else None
        startups = cohort.startups.prefetch_related('milestones__deliverables', 'members').all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['Cohort Name', cohort_name])
    if start_date_val:
        writer.writerow(['Start Date', start_date_val])
    writer.writerow([])
    
    # Remove redundant startups = cohort.startups...
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
            
    progress_reports = startup.progress_reports.select_related('submitted_by').order_by('-submitted_at')
    if progress_reports.exists():
        writer.writerow([])
        writer.writerow(['--- SUBMITTED PROGRESS REPORTS ---'])
        writer.writerow(['Date', 'Title', 'Submitted By', 'Achievements', 'Challenges', 'Next Steps', 'Description'])
        for pr in progress_reports:
            submitter = pr.submitted_by.get_full_name() or pr.submitted_by.username
            writer.writerow([
                pr.submitted_at.strftime('%Y-%m-%d %H:%M'),
                pr.title,
                submitter,
                pr.achievements or '--',
                pr.challenges or '--',
                pr.next_steps or '--',
                pr.description or '--',
            ])
            
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
    
    if cohort_id == 'all':
        cohort_name = 'All Cohorts & Startups'
        filename = 'all_startups_report.doc'
        startups = Startup.objects.prefetch_related('milestones__deliverables', 'members').all()
    elif cohort_id == 'unassigned':
        cohort_name = 'Unassigned Startups'
        filename = 'unassigned_startups_report.doc'
        startups = Startup.objects.filter(cohort__isnull=True).prefetch_related('milestones__deliverables', 'members')
    else:
        cohort = get_object_or_404(Cohort, id=cohort_id)
        cohort_name = cohort.name
        filename = f'cohort_{cohort.id}_report.doc'
        startups = cohort.startups.prefetch_related('milestones__deliverables', 'members').all()
    
    for s in startups:
        s.team_size = s.members.count()
        completed = s.milestones.filter(status='completed').order_by('-milestone_progress')
        s.latest_milestone = completed.first().title if completed.exists() else "None"
        s.current_progress = s.progress
        
    icebox_logo_src = _get_img_src(request, '/static/img/logo-light-mode.png', for_pdf=for_pdf)
    
    html = f"""<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head><title>{escape(cohort_name)} Report</title>{REPORT_STYLE}</head>
<body>"""

    if icebox_logo_src:
        html += f'<div style="text-align: center; margin-bottom: 20px;"><img src="{icebox_logo_src}" style="width: 200px; height: auto;" alt="Icebox Logo"/></div>'
        
    html += f"<h1>{escape(cohort_name)} Report</h1>"
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
<h2>Startup {idx}: {escape(s.name)}</h2>"""

        if startup_logo_src:
            html += f'<div style="margin-bottom: 15px;"><img src="{escape(startup_logo_src)}" style="width: 120px; height: auto;" alt="{escape(s.name)} Logo"/></div>'

        html += f"""
<p><strong>Description:</strong> {escape(s.description or 'No description provided.')}</p>
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
        <td>{escape(name)}</td>
        <td>{escape(role)}</td>
        <td>{escape(email)}</td>
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
                notes_str = "<br/>".join(escape(note) for note in admin_notes) if admin_notes else "--"
                
                html += f"""
    <tr>
        <td>{escape(m.title or '')}</td>
        <td>{escape(d.name)}</td>
        <td>{escape(d.get_status_display())}</td>
        <td>{due}</td>
        <td>{uploaded}</td>
        <td>{revs}</td>
        <td>{notes_str}</td>
    </tr>"""
        html += """</table>"""
        
    html += """</body></html>"""
    
    response = HttpResponse(html, content_type='application/msword')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
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
<head><title>Startup Report: {escape(startup.name)}</title>{REPORT_STYLE}</head>
<body>"""

    if icebox_logo_src:
        html += f'<div style="text-align: center; margin-bottom: 20px;"><img src="{icebox_logo_src}" style="width: 200px; height: auto;" alt="Icebox Logo"/></div>'
        
    html += f"<h1>Startup Report: {escape(startup.name)}</h1>"
    
    if startup_logo_src:
        html += f'<div style="margin-bottom: 15px;"><img src="{escape(startup_logo_src)}" style="width: 120px; height: auto;" alt="{escape(startup.name)} Logo"/></div>'
        
    html += f"""
<p><strong>Description:</strong> {escape(startup.description or 'No description provided.')}</p>
<p><strong>Cohort:</strong> {escape(cohort_name)}</p>
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
        <td>{escape(name)}</td>
        <td>{escape(role)}</td>
        <td>{escape(email)}</td>
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
            notes_str = "<br/>".join(escape(note) for note in admin_notes) if admin_notes else "--"
            
            html += f"""
    <tr>
        <td>{escape(m.title or '')}</td>
        <td>{escape(d.name)}</td>
        <td>{escape(d.get_status_display())}</td>
        <td>{due}</td>
        <td>{uploaded}</td>
        <td>{revs}</td>
        <td>{notes_str}</td>
    </tr>"""
    html += """</table>"""
    
    progress_reports = startup.progress_reports.select_related('submitted_by').order_by('-submitted_at')
    if progress_reports.exists():
        html += """
<h2>Submitted Progress Reports</h2>
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
    <tr>
        <th>Date</th>
        <th>Title</th>
        <th>Submitted By</th>
        <th>Achievements / Next Steps</th>
    </tr>"""
        for pr in progress_reports:
            submitter = pr.submitted_by.get_full_name() or pr.submitted_by.username
            date_str = pr.submitted_at.strftime('%B %d, %Y')
            achieve = escape(pr.achievements or 'None')
            next_st = escape(pr.next_steps or 'None')
            desc = escape(pr.description or '')
            html += f"""
    <tr>
        <td>{date_str}</td>
        <td><strong>{escape(pr.title)}</strong><br/><small>{desc}</small></td>
        <td>{escape(submitter)}</td>
        <td><strong>Achievements:</strong> {achieve}<br/><strong>Next Steps:</strong> {next_st}</td>
    </tr>"""
        html += """</table>"""
        
    html += """</body></html>"""
    
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
        if cohort_id == 'all':
            filename = 'all_startups_report.pdf'
        elif cohort_id == 'unassigned':
            filename = 'unassigned_startups_report.pdf'
        else:
            filename = f'cohort_{cohort_id}_report.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error generating PDF", status=500)

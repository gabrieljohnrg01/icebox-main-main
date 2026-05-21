from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('incubatee', 'Incubatee'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='incubatee')
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username

class Cohort(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Startup(models.Model):

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='startup_logos/', blank=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_startups')
    email = models.EmailField(max_length=120, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    cohort = models.ForeignKey(Cohort, on_delete=models.SET_NULL, null=True, blank=True, related_name='startups')
    
    members = models.ManyToManyField(User, through='StartupMember', related_name='startups')

    @property
    def progress(self):
        total = self.milestones.count()
        if total == 0:
            return 0
        completed = self.milestones.filter(status='completed').count()
        return int((completed / total) * 100)

    def __str__(self):
        return self.name

class StartupMember(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, blank=True, null=True)  # e.g., CEO, CTO
    joined_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.startup.name}"

class Milestone(models.Model):
    STATUS_CHOICES = (
        ('not-yet', 'Not Yet'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )
    
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='milestones')
    milestone_progress = models.IntegerField(blank=True, null=True) # Could be an index
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not-yet')
    due_date = models.DateField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def is_locked(self):
        """Check if this milestone is locked (previous milestone not completed)"""
        if self.milestone_progress == 1:
            return False  # First milestone is never locked
        
        previous_milestone = self.startup.milestones.filter(
            milestone_progress=self.milestone_progress - 1
        ).first()
        
        if previous_milestone:
            return previous_milestone.status != 'completed'
        return False

    @property
    def progress_percentage(self):
        total = self.deliverables.count()
        if total == 0:
            return 0
        completed = self.deliverables.filter(status='approved').count()
        return int((completed / total) * 100)

    def __str__(self):
        return f"{self.startup.name} - Milestone {self.milestone_progress}"

class Deliverable(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='deliverables')
    template = models.ForeignKey('DeliverableTemplate', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    due_date = models.DateField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class DeliverableFile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('incubatee', 'Incubatee'),
    )
    deliverable = models.ForeignKey(Deliverable, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='deliverables/', blank=True, null=True)
    link_url = models.URLField(max_length=500, blank=True, null=True)
    link_title = models.CharField(max_length=500, blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    uploaded_by_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.deliverable.name} - Submission"

class Readiness(models.Model):
    deliverable = models.ForeignKey(Deliverable, on_delete=models.CASCADE, related_name='readiness_levels')
    name = models.CharField(max_length=200)
    incubatee_level = models.CharField(max_length=50, blank=True, null=True)
    admin_level = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class Comment(models.Model):
    deliverable = models.ForeignKey(Deliverable, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment by {self.user.username}"

class ProgressReport(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='progress_reports')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    achievements = models.TextField(blank=True, null=True)
    challenges = models.TextField(blank=True, null=True)
    next_steps = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message}"

class MilestoneTemplate(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    milestone_progress = models.IntegerField(help_text="Order or index of the milestone")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Template: {self.title} (Index: {self.milestone_progress})"

class DeliverableTemplate(models.Model):
    milestone_template = models.ForeignKey(MilestoneTemplate, on_delete=models.CASCADE, related_name='deliverable_templates')
    name = models.CharField(max_length=200)
    requirements = models.TextField(blank=True, null=True)
    admin_file = models.FileField(upload_to='admin_templates/', null=True, blank=True)
    admin_link = models.URLField(max_length=500, blank=True, null=True)
    admin_link_title = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.milestone_template.title} - {self.name}"


class DeliverableTemplateResource(models.Model):
    template = models.ForeignKey(DeliverableTemplate, on_delete=models.CASCADE, related_name='resources')
    file = models.FileField(upload_to='admin_templates/', blank=True, null=True)
    link = models.URLField(max_length=500, blank=True, null=True)
    link_title = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.template.name} Resource'

class FBAnnouncement(models.Model):
    title = models.CharField(max_length=200, help_text="E.g., Status 1")
    text = models.CharField(max_length=500, help_text="Text of the status update")
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Keep only the 5 most recent
        if FBAnnouncement.objects.count() > 5:
            # Delete the oldest
            oldest = FBAnnouncement.objects.order_by('created_at').first()
            oldest.delete()

    def __str__(self):
        return self.title


class RLTemplate(models.Model):
    name = models.CharField(max_length=50, help_text="e.g. TRL, MRL, SRL")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class RLTemplateLevel(models.Model):
    template = models.ForeignKey(RLTemplate, on_delete=models.CASCADE, related_name='levels')
    level = models.IntegerField()
    description = models.TextField()

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f"{self.template.name} - Level {self.level}"

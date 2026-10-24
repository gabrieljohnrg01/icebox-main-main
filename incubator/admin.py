from django.contrib import admin

from .models import FBAnnouncement

@admin.register(FBAnnouncement)
class FBAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'text', 'created_at')
    ordering = ('-created_at',)

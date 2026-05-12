from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('set-password/', views.set_password, name='set_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Super Admin
    path('super-admin/add-admin/', views.add_admin, name='add_admin'),
    path('super-admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # Admin / Startup Management
    path('startups/', views.startups_list, name='startups_list'),
    path('startups/<int:startup_id>/delete/', views.delete_startup, name='delete_startup'),
    path('startups/add/', views.add_startup, name='add_startup'),
    path('notifications/<int:notification_id>/read/', views.read_notification, name='read_notification'),
    path('startups/<int:startup_id>/edit/', views.edit_startup, name='edit_startup'),
    path('startups/<int:startup_id>/', views.view_startup, name='view_startup'),
    path('startups/<int:startup_id>/add-member/', views.add_member, name='add_member'),
    path('startups/<int:startup_id>/add-milestone/', views.add_milestone, name='add_milestone'),
    path('startups/<int:startup_id>/members/<int:member_id>/delete/', views.delete_member, name='delete_member'),
    
    # Progress & Milestones
    path('startups/<int:startup_id>/submit-report/', views.submit_progress, name='submit_progress'),
    path('startups/<int:startup_id>/milestones/<int:milestone_id>/', views.view_milestone, name='view_milestone'),
    path('startups/<int:startup_id>/milestones/<int:milestone_id>/status/', views.update_milestone_status, name='update_milestone_status'),
    path('deliverables/<int:deliverable_id>/attach_admin/', views.attach_admin_file, name='attach_admin_file'),
    path('deliverables/<int:deliverable_id>/attach_incubatee/', views.attach_incubatee_file, name='attach_incubatee_file'),
    path('deliverables/<int:deliverable_id>/edit/', views.edit_deliverable_page, name='edit_deliverable_page'),
    path('deliverables/<int:deliverable_id>/update_details/', views.update_deliverable_details, name='update_deliverable_details'),
    path('deliverables/files/<int:file_id>/delete/', views.delete_deliverable_file, name='delete_deliverable_file'),
    
    # Settings & Templates
    path('settings/', views.settings_view, name='settings'),
    path('settings/templates/milestone/add/', views.add_milestone_template, name='add_milestone_template'),
    path('settings/templates/milestone/<int:template_id>/edit/', views.edit_milestone_template, name='edit_milestone_template'),
    path('settings/templates/milestone/<int:template_id>/delete/', views.delete_milestone_template, name='delete_milestone_template'),
    path('settings/templates/deliverable/add/', views.add_deliverable_template, name='add_deliverable_template'),
    path('settings/templates/deliverable/<int:template_id>/edit/', views.edit_deliverable_template, name='edit_deliverable_template'),
    path('settings/templates/deliverable/<int:template_id>/delete/', views.delete_deliverable_template, name='delete_deliverable_template'),
]

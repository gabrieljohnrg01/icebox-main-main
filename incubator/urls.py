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
    path('notifications/clear/', views.clear_notifications, name='clear_notifications'),
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
    path('milestones/<int:milestone_id>/add_custom_deliverable/', views.add_custom_deliverable, name='add_custom_deliverable'),
    
    # Settings & Templates
    path('settings/', views.settings_view, name='settings'),
    path('settings/templates/milestone/add/', views.add_milestone_template, name='add_milestone_template'),
    path('settings/templates/milestone/<int:template_id>/edit/', views.edit_milestone_template, name='edit_milestone_template'),
    path('settings/templates/milestone/<int:template_id>/delete/', views.delete_milestone_template, name='delete_milestone_template'),
    path('settings/templates/deliverable/add/', views.add_deliverable_template, name='add_deliverable_template'),
    path('settings/templates/deliverable/<int:template_id>/edit/', views.edit_deliverable_template, name='edit_deliverable_template'),
    path('settings/templates/deliverable/<int:template_id>/delete/', views.delete_deliverable_template, name='delete_deliverable_template'),
    path('settings/cohorts/add/', views.add_cohort, name='add_cohort'),
    path('settings/cohorts/<int:cohort_id>/edit/', views.edit_cohort, name='edit_cohort'),
    path('settings/cohorts/<int:cohort_id>/delete/', views.delete_cohort, name='delete_cohort'),
    path('settings/rltemplates/add/', views.add_rltemplate, name='add_rltemplate'),
    path('settings/rltemplates/<int:template_id>/edit/', views.edit_rltemplate, name='edit_rltemplate'),
    path('settings/rltemplates/<int:template_id>/delete/', views.delete_rltemplate, name='delete_rltemplate'),
    path('settings/rltemplates/levels/add/', views.add_rltemplate_level, name='add_rltemplate_level'),
    path('settings/rltemplates/levels/<int:level_id>/edit/', views.edit_rltemplate_level, name='edit_rltemplate_level'),
    path('settings/rltemplates/levels/<int:level_id>/delete/', views.delete_rltemplate_level, name='delete_rltemplate_level'),
    
    # Reports
    path('reports/', views.reports_view, name='reports'),
    path('reports/cohort/', views.cohort_report, name='cohort_report'),
    path('reports/startup/', views.startup_report, name='startup_report'),
    path('reports/cohort/csv/', views.cohort_report_csv, name='cohort_report_csv'),
    path('reports/cohort/docx/', views.cohort_report_docx, name='cohort_report_docx'),
    path('reports/startup/csv/', views.startup_report_csv, name='startup_report_csv'),
    path('reports/startup/docx/', views.startup_report_docx, name='startup_report_docx'),
    path('reports/cohort/pdf/', views.cohort_report_pdf, name='cohort_report_pdf'),
    path('reports/startup/pdf/', views.startup_report_pdf, name='startup_report_pdf'),
]

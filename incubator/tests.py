from django.test import TestCase, Client
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from .models import Startup, StartupMember, Milestone, Deliverable, Notification, MilestoneTemplate, DeliverableTemplate, ProgressReport, Comment, Readiness, MilestoneReadiness, DeliverableFile, Cohort, RLTemplate, RLTemplateLevel
from .views import get_link_title_safe
from django.utils import timezone
import datetime
import json
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username='testuser', password='testpass123', role='incubatee')
        self.assertEqual(user.role, 'incubatee')
        self.assertTrue(user.check_password('testpass123'))

    def test_user_str(self):
        user = User.objects.create_user(username='alice')
        self.assertEqual(str(user), 'alice')


class StartupModelTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.startup = Startup.objects.create(name='Test Startup', owner=self.owner)

    def test_startup_str(self):
        self.assertEqual(str(self.startup), 'Test Startup')

    def test_progress_no_milestones(self):
        self.assertEqual(self.startup.progress, 0)

    def test_progress_with_milestones(self):
        m1 = Milestone.objects.create(startup=self.startup, milestone_progress=1, title='M1', status='completed')
        Milestone.objects.create(startup=self.startup, milestone_progress=2, title='M2', status='pending')
        self.assertEqual(self.startup.progress, 50)


class MilestoneModelTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='o', password='p')
        self.startup = Startup.objects.create(name='S', owner=self.owner)

    def test_is_locked_first_milestone(self):
        m1 = Milestone.objects.create(startup=self.startup, milestone_progress=1, title='M1')
        self.assertFalse(m1.is_locked())

    def test_is_locked_previous_completed(self):
        m1 = Milestone.objects.create(startup=self.startup, milestone_progress=1, title='M1', status='completed')
        m2 = Milestone.objects.create(startup=self.startup, milestone_progress=2, title='M2')
        self.assertFalse(m2.is_locked())

    def test_is_locked_previous_not_completed(self):
        Milestone.objects.create(startup=self.startup, milestone_progress=1, title='M1', status='pending')
        m2 = Milestone.objects.create(startup=self.startup, milestone_progress=2, title='M2')
        self.assertTrue(m2.is_locked())

    def test_progress_percentage(self):
        m = Milestone.objects.create(startup=self.startup, milestone_progress=1, title='M1')
        self.assertEqual(m.progress_percentage, 0)
        d1 = Deliverable.objects.create(milestone=m, name='D1')
        Deliverable.objects.create(milestone=m, name='D2')
        d1.status = 'approved'
        d1.save()
        self.assertEqual(m.progress_percentage, 50)


class ViewAuthTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.sa = User.objects.create_user(username='sa', password='sa123456', role='super_admin')
        self.admin = User.objects.create_user(username='ad', password='ad123456', role='admin')
        self.inc = User.objects.create_user(username='inc', password='inc123456', role='incubatee')

    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_valid(self):
        response = self.client.post(reverse('login'), {'username': 'sa', 'password': 'sa123456'})
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_invalid(self):
        response = self.client.post(reverse('login'), {'username': 'sa', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirects_anon(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_super_admin(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_admin(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_incubatee(self):
        self.client.login(username='inc', password='inc123456')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username='sa', password='sa123456')
        # GET request renders confirmation page and does not log user out
        get_resp = self.client.get(reverse('logout'))
        self.assertEqual(get_resp.status_code, 200)
        # POST request logs out and redirects to login
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


class StartupCRUDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.sa = User.objects.create_user(username='sa', password='sa123456', role='super_admin')
        self.admin = User.objects.create_user(username='ad', password='ad123456', role='admin')
        self.inc = User.objects.create_user(username='inc', password='inc123456', role='incubatee')
        self.startup = Startup.objects.create(name='Existing', owner=self.inc)

    def test_startups_list_requires_admin(self):
        self.client.login(username='inc', password='inc123456')
        response = self.client.get(reverse('startups_list'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_startups_list_admin(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.get(reverse('startups_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Existing')

    def test_add_startup_get_admin(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.get(reverse('add_startup'))
        self.assertEqual(response.status_code, 200)

    def test_shared_form_enhancements_load_on_other_forms(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.get(reverse('add_member', args=[self.startup.id]))

        self.assertContains(response, 'js/form_enhancements.js?v=20261019-1')
        self.assertContains(response, 'css/main.css?v=20261019-3')

    def test_add_startup_refreshes_stylesheet_cache(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.get(reverse('add_startup'))

        self.assertContains(response, 'css/main.css?v=20261019-3')

    def test_add_startup_marks_and_validates_required_fields(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.post(reverse('add_startup'), {
            'name': '',
            'email': '',
            'contact_number': '',
            'starting_milestone': 1,
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)
        self.assertIn('email', response.context['form'].errors)
        self.assertIn('contact_number', response.context['form'].errors)
        self.assertEqual(response.content.count(b'class="required-indicator"'), 4)
        self.assertEqual(response.content.count(b'class="optional-indicator"'), 2)
        self.assertNotContains(response, 'Fields labeled')
        self.assertNotContains(response, 'color:red')
        self.assertFalse(Startup.objects.filter(name='').exists())

    def test_add_startup_post_creates_milestones(self):
        MilestoneTemplate.objects.create(title='T1', milestone_progress=1)
        MilestoneTemplate.objects.create(title='T2', milestone_progress=2)
        self.client.login(username='ad', password='ad123456')
        response = self.client.post(reverse('add_startup'), {
            'name': 'New Startup',
            'description': 'Desc',
            'email': 'new@test.com',
            'contact_number': '123',
            'starting_milestone': 1,
        })
        self.assertRedirects(response, reverse('add_member', args=[Startup.objects.get(name='New Startup').id]))
        self.assertTrue(Startup.objects.filter(name='New Startup').exists())
        self.assertEqual(Startup.objects.get(name='New Startup').milestones.count(), 2)

    def test_archive_startup_super_admin(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('archive_startup', args=[self.startup.id]))
        self.startup.refresh_from_db()
        self.assertTrue(self.startup.is_archived)
        self.assertIsNotNone(self.startup.archived_at)

        # Also test unarchive / restore
        unarchive_resp = self.client.post(reverse('unarchive_startup', args=[self.startup.id]))
        self.startup.refresh_from_db()
        self.assertFalse(self.startup.is_archived)
        self.assertIsNone(self.startup.archived_at)

    def test_archive_startup_incubatee_blocked(self):
        self.client.login(username='inc', password='inc123456')
        response = self.client.post(reverse('archive_startup', args=[self.startup.id]))
        self.startup.refresh_from_db()
        self.assertFalse(self.startup.is_archived)

    def test_get_does_not_archive_startup(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.get(reverse('archive_startup', args=[self.startup.id]))
        self.assertEqual(response.status_code, 405)
        self.startup.refresh_from_db()
        self.assertFalse(self.startup.is_archived)

    def test_view_startup(self):
        self.client.login(username='inc', password='inc123456')
        response = self.client.get(reverse('view_startup', args=[self.startup.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Existing')


class StartupAccessControlTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='owner', password='ownerpass', role='incubatee')
        self.outsider = User.objects.create_user(username='outsider', password='outsiderpass', role='incubatee')
        self.startup = Startup.objects.create(name='Private Startup', owner=self.owner)
        self.milestone = Milestone.objects.create(
            startup=self.startup,
            milestone_progress=1,
            title='Milestone 1',
        )
        self.deliverable = Deliverable.objects.create(milestone=self.milestone, name='Deliverable 1')
        self.client.login(username='outsider', password='outsiderpass')

    def test_nonmember_cannot_view_startup_or_milestone(self):
        startup_response = self.client.get(reverse('view_startup', args=[self.startup.id]))
        milestone_response = self.client.get(
            reverse('view_milestone', args=[self.startup.id, self.milestone.id])
        )

        self.assertRedirects(startup_response, reverse('dashboard'))
        self.assertRedirects(milestone_response, reverse('dashboard'))

    def test_nonmember_cannot_submit_progress_report(self):
        response = self.client.post(reverse('submit_progress', args=[self.startup.id]), {
            'title': 'Unauthorized report',
            'description': 'This should not be saved.',
        })

        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(ProgressReport.objects.count(), 0)

    def test_nonmember_cannot_read_or_update_deliverable(self):
        page_response = self.client.get(reverse('edit_deliverable_page', args=[self.deliverable.id]))
        update_response = self.client.post(
            reverse('update_deliverable_details', args=[self.deliverable.id]),
            {'action': 'save', 'comment': 'Unauthorized comment'},
        )

        self.assertRedirects(page_response, reverse('dashboard'))
        self.assertRedirects(update_response, reverse('dashboard'))
        self.assertFalse(Comment.objects.filter(deliverable=self.deliverable).exists())


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class MemberTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='ad', password='ad123456', role='admin')
        self.startup = Startup.objects.create(name='S', owner=self.admin)

    def test_add_member_creates_user(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.post(reverse('add_member', args=[self.startup.id]), {
            'first_name': 'John',
            'middle_name': 'M',
            'last_name': 'Doe',
            'position': 'CTO',
            'email': 'john@example.com',
            'contact_number': '1234567890',
        })
        self.assertTrue(User.objects.filter(username='doe.john').exists())
        user = User.objects.get(username='doe.john')
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.must_change_password)
        self.assertTrue(StartupMember.objects.filter(user=user, startup=self.startup).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Portal Link: http://testserver/login/', mail.outbox[0].body)
        self.assertIn('Username: doe.john', mail.outbox[0].body)
        self.assertIn('Temporary Password:', mail.outbox[0].body)

    def test_temporary_password_requires_change_and_expires(self):
        self.client.login(username='ad', password='ad123456')
        self.client.post(reverse('add_member', args=[self.startup.id]), {
            'first_name': 'John',
            'middle_name': '',
            'last_name': 'Doe',
            'position': 'CTO',
            'email': 'john@example.com',
            'contact_number': '1234567890',
        })
        user = User.objects.get(username='doe.john')
        temporary_password = mail.outbox[0].body.split('Temporary Password: ')[1].splitlines()[0]

        login_response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': temporary_password,
        })
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response['Location'], reverse('dashboard'))
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertRedirects(dashboard_response, reverse('set_password'))

        password_response = self.client.post(reverse('set_password'), {
            'new_password1': 'PermanentPassword123!',
            'new_password2': 'PermanentPassword123!',
        })
        self.assertEqual(password_response.status_code, 302)
        self.assertEqual(password_response['Location'], reverse('dashboard'))
        user.refresh_from_db()
        self.assertFalse(user.must_change_password)
        self.assertTrue(user.check_password('PermanentPassword123!'))
        self.assertFalse(user.check_password(temporary_password))
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertNotEqual(dashboard_response.get('Location'), reverse('set_password'))

    def test_add_member_links_existing_email(self):
        User.objects.create_user(username='existing', email='john@example.com', password='p')
        self.client.login(username='ad', password='ad123456')
        response = self.client.post(reverse('add_member', args=[self.startup.id]), {
            'first_name': 'John',
            'middle_name': '',
            'last_name': 'Doe',
            'position': 'CTO',
            'email': 'john@example.com',
            'contact_number': '1234567890',
        })
        self.assertEqual(StartupMember.objects.filter(startup=self.startup, user__username='existing').count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_add_member_uses_next_username_when_username_exists(self):
        User.objects.create_user(
            username='doe.john',
            email='different@example.com',
            password='p',
        )
        self.client.login(username='ad', password='ad123456')
        response = self.client.post(reverse('add_member', args=[self.startup.id]), {
            'first_name': 'John',
            'middle_name': '',
            'last_name': 'Doe',
            'position': 'CTO',
            'email': 'john@example.com',
            'contact_number': '1234567890',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='doe.john1', email='john@example.com').exists())
        self.assertTrue(StartupMember.objects.filter(startup=self.startup, user__username='doe.john1').exists())
        self.assertEqual(len(mail.outbox), 1)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AdminCreationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.super_admin = User.objects.create_user(
            username='sa',
            password='sa123456',
            role='super_admin',
        )

    def test_new_admin_receives_temporary_credentials(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('add_admin'), {
            'username': 'newadmin',
            'email': 'newadmin@example.com',
            'first_name': 'New',
            'last_name': 'Admin',
        })
        self.assertRedirects(response, reverse('dashboard'))

        admin_user = User.objects.get(username='newadmin')
        self.assertTrue(admin_user.has_usable_password())
        self.assertTrue(admin_user.must_change_password)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Username: newadmin', mail.outbox[0].body)
        self.assertIn('Temporary Password:', mail.outbox[0].body)


class MilestoneDeliverableTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.sa = User.objects.create_user(username='sa', password='sa123456', role='super_admin')
        self.startup = Startup.objects.create(name='S', owner=self.sa)
        self.m1 = Milestone.objects.create(startup=self.startup, milestone_progress=1, title='M1')
        self.m2 = Milestone.objects.create(startup=self.startup, milestone_progress=2, title='M2')

    def test_add_milestone(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('add_milestone', args=[self.startup.id]), {
            'title': 'Milestone 3',
            'deliverable_count': 0,
        })
        self.assertRedirects(response, reverse('view_startup', args=[self.startup.id]))
        self.assertEqual(self.startup.milestones.count(), 3)

    def test_custom_deliverable_uses_declared_pending_status(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('add_custom_deliverable', args=[self.m1.id]), {
            'name': 'Custom deliverable',
            'requirements': 'Requirements',
        })

        deliverable = self.m1.deliverables.get(name='Custom deliverable')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(deliverable.status, 'pending')

    def test_view_milestone_locked(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.get(reverse('view_milestone', args=[self.startup.id, self.m2.id]))
        # m2 is locked because m1 is not completed; but SA/admin can view
        self.assertEqual(response.status_code, 200)

    def test_update_milestone_status(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('update_milestone_status', args=[self.startup.id, self.m1.id]), {'status': 'completed'})
        self.assertRedirects(response, reverse('view_milestone', args=[self.startup.id, self.m1.id]))
        self.m1.refresh_from_db()
        self.assertEqual(self.m1.status, 'completed')


class MilestoneReadinessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.incubatee = User.objects.create_user(
            username='milestone_incubatee',
            password='incubateepass',
            role='incubatee',
        )
        self.startup = Startup.objects.create(name='Readiness Startup', owner=self.incubatee)
        self.milestone = Milestone.objects.create(
            startup=self.startup,
            milestone_progress=1,
            title='Milestone 1',
        )
        self.rl_template = RLTemplate.objects.create(name='TRL')
        RLTemplateLevel.objects.create(
            template=self.rl_template,
            level=1,
            description='Basic technology research',
        )
        self.client.force_login(self.incubatee)

    def test_milestone_page_shows_configured_assessment_category(self):
        response = self.client.get(reverse(
            'view_milestone',
            args=[self.startup.id, self.milestone.id],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Milestone Readiness Assessment')
        self.assertContains(response, 'TRL')
        content = response.content.decode()
        panel_start = content.index('id="milestone-readiness-assessment"')
        panel_end = content.index('</section>', panel_start)
        self.assertIn('Basic technology research', content[panel_start:panel_end])

    def test_admin_assigns_category_and_sets_verdict(self):
        admin = User.objects.create_user(username='readiness_admin', password='adminpass', role='admin')
        self.client.force_login(admin)

        response = self.client.post(
            reverse('update_milestone_readiness', args=[self.startup.id, self.milestone.id]),
            {
                f'milestone_rl_{self.rl_template.id}_enabled': 'on',
                f'milestone_rl_{self.rl_template.id}_admin_level': 'Level 1',
            },
        )

        assessment = MilestoneReadiness.objects.get(milestone=self.milestone, name='TRL')
        self.assertRedirects(response, reverse('view_milestone', args=[self.startup.id, self.milestone.id]))
        self.assertEqual(assessment.admin_level, 'Level 1')

    def test_member_self_assessment_does_not_change_deliverable_assessment(self):
        assessment = MilestoneReadiness.objects.create(milestone=self.milestone, name='TRL')
        deliverable = Deliverable.objects.create(milestone=self.milestone, name='Deliverable 1')
        deliverable_assessment = Readiness.objects.create(
            deliverable=deliverable,
            name='TRL',
            admin_level='Level 2',
        )

        response = self.client.post(
            reverse('update_milestone_readiness', args=[self.startup.id, self.milestone.id]),
            {
                f'milestone_rl_{self.rl_template.id}_incubatee_level': 'Level 1',
                f'milestone_rl_{self.rl_template.id}_admin_level': 'Level 1',
            },
        )

        assessment.refresh_from_db()
        deliverable_assessment.refresh_from_db()
        self.assertRedirects(response, reverse('view_milestone', args=[self.startup.id, self.milestone.id]))
        self.assertEqual(assessment.incubatee_level, 'Level 1')
        self.assertIsNone(deliverable_assessment.incubatee_level)
        self.assertEqual(deliverable_assessment.admin_level, 'Level 2')

    def test_member_cannot_assign_unassigned_category_or_set_admin_verdict(self):
        response = self.client.post(
            reverse('update_milestone_readiness', args=[self.startup.id, self.milestone.id]),
            {
                f'milestone_rl_{self.rl_template.id}_enabled': 'on',
                f'milestone_rl_{self.rl_template.id}_incubatee_level': 'Level 1',
                f'milestone_rl_{self.rl_template.id}_admin_level': 'Level 1',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(MilestoneReadiness.objects.filter(milestone=self.milestone).exists())

    def test_nonmember_cannot_update_milestone_assessment(self):
        outsider = User.objects.create_user(username='outsider', password='outsiderpass', role='incubatee')
        self.client.force_login(outsider)

        response = self.client.post(
            reverse('update_milestone_readiness', args=[self.startup.id, self.milestone.id]),
            {f'milestone_rl_{self.rl_template.id}_incubatee_level': 'Level 1'},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(MilestoneReadiness.objects.filter(milestone=self.milestone).exists())

    def test_locked_milestone_member_cannot_update_assessment(self):
        Milestone.objects.create(
            startup=self.startup,
            milestone_progress=1,
            title='Previous milestone',
            status='pending',
        )
        self.milestone.milestone_progress = 2
        self.milestone.save(update_fields=['milestone_progress'])

        response = self.client.post(
            reverse('update_milestone_readiness', args=[self.startup.id, self.milestone.id]),
            {f'milestone_rl_{self.rl_template.id}_incubatee_level': 'Level 1'},
        )

        self.assertRedirects(response, reverse('view_startup', args=[self.startup.id]))
        self.assertFalse(MilestoneReadiness.objects.filter(milestone=self.milestone).exists())


class DeliverableTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.sa = User.objects.create_user(username='sa', password='sa123456', role='super_admin')
        self.startup = Startup.objects.create(name='S', owner=self.sa)
        self.m = Milestone.objects.create(startup=self.startup, milestone_progress=1, title='M1')
        self.d = Deliverable.objects.create(milestone=self.m, name='D1')

    def test_update_deliverable_details_admin_approve(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('update_deliverable_details', args=[self.d.id]), {
            'action': 'done',
            'comment': 'Looks good',
        })
        self.assertRedirects(response, reverse('edit_deliverable_page', args=[self.d.id]))
        self.d.refresh_from_db()
        self.assertEqual(self.d.status, 'approved')
        self.assertTrue(Comment.objects.filter(deliverable=self.d, content__contains='Looks good').exists())

    def test_update_deliverable_details_admin_reject(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('update_deliverable_details', args=[self.d.id]), {
            'action': 'revision',
        })
        self.d.refresh_from_db()
        self.assertEqual(self.d.status, 'rejected')


class NotificationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.inc = User.objects.create_user(username='inc', password='inc123456', role='incubatee')
        self.notif = Notification.objects.create(recipient=self.inc, message='Hello', link='/dashboard/')

    def test_read_notification(self):
        self.client.login(username='inc', password='inc123456')
        response = self.client.get(reverse('read_notification', args=[self.notif.id]))
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.is_read)
        self.assertRedirects(response, '/dashboard/')


class PasswordlessLoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nopass', password='')
        self.user.set_unusable_password()
        self.user.save()

    def test_passwordless_login(self):
        response = self.client.post(reverse('login'), {'username': 'nopass', 'password': ''})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


class LinkTitleLookupTest(TestCase):
    def test_link_title_lookup_does_not_fetch_remote_content(self):
        self.assertIsNone(get_link_title_safe('http://127.0.0.1:8000/admin/'))


class ReportHtmlEscapingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin', password='adminpass', role='admin')
        self.client.login(username='admin', password='adminpass')
        self.cohort = Cohort.objects.create(name='Cohort <b>unsafe</b>')
        self.startup = Startup.objects.create(
            name='Startup <b>unsafe</b>',
            description='<script>alert(1)</script>',
            owner=self.admin,
            cohort=self.cohort,
        )
        milestone = Milestone.objects.create(
            startup=self.startup,
            milestone_progress=1,
            title='Milestone 1',
        )
        deliverable = Deliverable.objects.create(milestone=milestone, name='Deliverable 1')
        Comment.objects.create(
            deliverable=deliverable,
            user=self.admin,
            content='<img src=x onerror=alert(1)>',
        )

    def test_startup_report_escapes_user_content(self):
        response = self.client.get(reverse('startup_report_docx'), {'startup_id': self.startup.id})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<script>alert(1)</script>', response.content)
        self.assertNotIn(b'<img src=x onerror=alert(1)>', response.content)
        self.assertIn(b'&lt;script&gt;alert(1)&lt;/script&gt;', response.content)
        self.assertIn(b'&lt;img src=x onerror=alert(1)&gt;', response.content)

    def test_cohort_report_escapes_user_content(self):
        response = self.client.get(reverse('cohort_report_docx'), {'cohort_id': self.cohort.id})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<script>alert(1)</script>', response.content)
        self.assertNotIn(b'<img src=x onerror=alert(1)>', response.content)
        self.assertIn(b'&lt;script&gt;alert(1)&lt;/script&gt;', response.content)
        self.assertIn(b'&lt;img src=x onerror=alert(1)&gt;', response.content)


class SettingsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.sa = User.objects.create_user(username='sa', password='sa123456', role='super_admin')
        self.admin = User.objects.create_user(username='ad', password='ad123456', role='admin')

    def test_settings_view_super_admin(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)

    def test_settings_view_admin(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)

    def test_add_milestone_template(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('add_milestone_template'), {
            'title': 'New Template',
            'description': 'Desc',
            'deliverables_count': 2,
        })
        self.assertTrue(MilestoneTemplate.objects.filter(title='New Template').exists())

    def test_edit_milestone_template_route_updates_template(self):
        template = MilestoneTemplate.objects.create(title='Original', milestone_progress=1)
        self.client.login(username='sa', password='sa123456')

        response = self.client.post(reverse('edit_milestone_template', args=[template.id]), {
            'title': 'Updated',
            'description': 'Updated description',
            'milestone_progress': 2,
        })

        template.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(template.title, 'Updated')

    def test_delete_milestone_template(self):
        mt = MilestoneTemplate.objects.create(title='ToDelete', milestone_progress=1)
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('delete_milestone_template', args=[mt.id]))
        self.assertFalse(MilestoneTemplate.objects.filter(id=mt.id).exists())


class DeleteUserTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.sa = User.objects.create_user(username='sa', password='sa123456', role='super_admin')
        self.admin = User.objects.create_user(username='ad', password='ad123456', role='admin')
        self.inc = User.objects.create_user(username='inc', password='inc123456', role='incubatee')

    def test_delete_user_super_admin(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('delete_user', args=[self.inc.id]))
        self.assertFalse(User.objects.filter(id=self.inc.id).exists())

    def test_delete_admin_by_admin_blocked(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.post(reverse('delete_user', args=[self.inc.id]))
        # Admin can delete incubatee
        self.assertFalse(User.objects.filter(id=self.inc.id).exists())

    def test_delete_super_admin_blocked(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.post(reverse('delete_user', args=[self.sa.id]))
        self.assertTrue(User.objects.filter(id=self.sa.id).exists())

    def test_delete_user_by_incubatee_blocked(self):
        self.client.login(username='inc', password='inc123456')
        other = User.objects.create_user(username='other', password='p', role='incubatee')
        response = self.client.post(reverse('delete_user', args=[other.id]))
        self.assertTrue(User.objects.filter(id=other.id).exists())

    def test_get_does_not_delete_user(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.get(reverse('delete_user', args=[self.inc.id]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(id=self.inc.id).exists())


class DeleteMemberMethodTest(TestCase):
    def test_get_does_not_remove_member(self):
        client = Client()
        admin = User.objects.create_user(username='admin', password='adminpass', role='admin')
        member = User.objects.create_user(username='member', password='memberpass', role='incubatee')
        startup = Startup.objects.create(name='Startup', owner=admin)
        StartupMember.objects.create(startup=startup, user=member)
        client.login(username='admin', password='adminpass')

        response = client.get(reverse('delete_member', args=[startup.id, member.id]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(StartupMember.objects.filter(startup=startup, user=member).exists())


class IndexRedirectTest(TestCase):
    def test_index_redirects_anonymous(self):
        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('login'))

    def test_index_redirects_authenticated(self):
        user = User.objects.create_user(username='u', password='p')
        self.client.login(username='u', password='p')
        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('dashboard'))


class DeliverableReorderTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='milestone_owner', password='pass')
        self.outsider = User.objects.create_user(username='outsider', password='pass')
        self.startup = Startup.objects.create(name='Startup A', owner=self.owner)
        self.milestone_a = Milestone.objects.create(
            startup=self.startup, milestone_progress=1, title='Milestone A'
        )
        self.milestone_b = Milestone.objects.create(
            startup=self.startup, milestone_progress=2, title='Milestone B'
        )
        self.first = Deliverable.objects.create(milestone=self.milestone_a, name='First')
        self.second = Deliverable.objects.create(milestone=self.milestone_a, name='Second')
        self.other_first = Deliverable.objects.create(milestone=self.milestone_b, name='Other first')
        self.other_second = Deliverable.objects.create(milestone=self.milestone_b, name='Other second')
        self.client.force_login(self.owner)
        self.url = reverse('reorder_deliverables', args=[self.milestone_a.id])

    def test_reordering_persists_and_does_not_change_another_milestone(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'deliverable_ids': [self.second.id, self.first.id]}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(self.milestone_a.deliverables.values_list('name', flat=True)),
            ['Second', 'First'],
        )
        self.assertEqual(
            list(self.milestone_b.deliverables.values_list('name', flat=True)),
            ['Other first', 'Other second'],
        )

        page = self.client.get(reverse('view_milestone', args=[self.startup.id, self.milestone_a.id]))
        self.assertEqual(page.status_code, 200)
        self.assertLess(page.content.index(b'data-name="Second"'), page.content.index(b'data-name="First"'))

    def test_rejects_deliverables_from_a_different_milestone(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'deliverable_ids': [self.first.id, self.other_first.id]}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.first.refresh_from_db()
        self.other_first.refresh_from_db()
        self.assertEqual(self.first.position, 0)
        self.assertEqual(self.other_first.position, 0)

    def test_rejects_users_outside_the_startup(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            self.url,
            data=json.dumps({'deliverable_ids': [self.second.id, self.first.id]}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)


class SecurityPatchesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.sa = User.objects.create_user(username='sec_sa', password='password123', role='super_admin')
        self.admin = User.objects.create_user(username='sec_admin', password='password123', role='admin')
        self.inc = User.objects.create_user(username='sec_inc', password='password123', role='incubatee')
        self.startup = Startup.objects.create(name='Security Startup', owner=self.inc)
        self.m1 = Milestone.objects.create(startup=self.startup, milestone_progress=1, status='in_progress', title='M1')
        self.m2 = Milestone.objects.create(startup=self.startup, milestone_progress=2, status='pending', title='M2')
        self.d1 = Deliverable.objects.create(milestone=self.m1, name='D1', status='in_progress')
        self.d2 = Deliverable.objects.create(milestone=self.m2, name='D2', status='pending')

    def test_file_upload_rejects_html_and_executable(self):
        self.client.login(username='sec_inc', password='password123')
        bad_file = SimpleUploadedFile("exploit.html", b"<script>alert(1)</script>", content_type="text/html")
        response = self.client.post(
            reverse('attach_incubatee_file', args=[self.d1.id]),
            {'file': bad_file}
        )
        self.assertEqual(DeliverableFile.objects.filter(deliverable=self.d1).count(), 0)

    def test_file_upload_accepts_valid_pdf(self):
        self.client.login(username='sec_inc', password='password123')
        good_file = SimpleUploadedFile("report.pdf", b"%PDF-1.4 sample content", content_type="application/pdf")
        response = self.client.post(
            reverse('attach_incubatee_file', args=[self.d1.id]),
            {'file': good_file}
        )
        self.assertEqual(DeliverableFile.objects.filter(deliverable=self.d1).count(), 1)

    def test_milestone_lock_blocks_incubatee_action_on_locked_milestone(self):
        self.client.login(username='sec_inc', password='password123')
        self.assertTrue(self.m2.is_locked())
        good_file = SimpleUploadedFile("doc.pdf", b"%PDF-1.4 ...", content_type="application/pdf")
        # Attaching file to locked milestone deliverable should be blocked
        response = self.client.post(
            reverse('attach_incubatee_file', args=[self.d2.id]),
            {'file': good_file}
        )
        self.assertEqual(DeliverableFile.objects.filter(deliverable=self.d2).count(), 0)
        self.assertRedirects(response, reverse('view_startup', args=[self.startup.id]))
        # Updating details on locked milestone deliverable should also redirect away
        resp2 = self.client.post(
            reverse('update_deliverable_details', args=[self.d2.id]),
            {'action': 'save'}
        )
        self.assertRedirects(resp2, reverse('view_startup', args=[self.startup.id]))

    def test_delete_user_protects_startup_owner(self):
        self.client.login(username='sec_sa', password='password123')
        response = self.client.post(reverse('delete_user', args=[self.inc.id]))
        # User and startup should still exist
        self.assertTrue(User.objects.filter(id=self.inc.id).exists())
        self.assertTrue(Startup.objects.filter(id=self.startup.id).exists())

    def test_delete_user_prevents_self_deletion(self):
        self.client.login(username='sec_sa', password='password123')
        response = self.client.post(reverse('delete_user', args=[self.sa.id]))
        self.assertTrue(User.objects.filter(id=self.sa.id).exists())

    def test_milestone_template_deletion_restricted_to_super_admin(self):
        mt = MilestoneTemplate.objects.create(title='Template Test', milestone_progress=99)
        # Standard admin is rejected (403)
        self.client.login(username='sec_admin', password='password123')
        resp_admin = self.client.post(reverse('delete_milestone_template', args=[mt.id]))
        self.assertEqual(resp_admin.status_code, 403)
        self.assertTrue(MilestoneTemplate.objects.filter(id=mt.id).exists())

        # Super admin succeeds
        self.client.login(username='sec_sa', password='password123')
        resp_sa = self.client.post(reverse('delete_milestone_template', args=[mt.id]))
        self.assertEqual(resp_sa.status_code, 302)
        self.assertFalse(MilestoneTemplate.objects.filter(id=mt.id).exists())


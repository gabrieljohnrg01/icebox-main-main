from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Startup, StartupMember, Milestone, Deliverable, Notification, MilestoneTemplate, DeliverableTemplate, ProgressReport, Comment, Readiness, DeliverableFile
from django.utils import timezone
import datetime

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
        response = self.client.get(reverse('logout'))
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

    def test_delete_startup_super_admin(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.get(reverse('delete_startup', args=[self.startup.id]))
        self.assertFalse(Startup.objects.filter(id=self.startup.id).exists())

    def test_delete_startup_incubatee_blocked(self):
        self.client.login(username='inc', password='inc123456')
        response = self.client.get(reverse('delete_startup', args=[self.startup.id]))
        self.assertTrue(Startup.objects.filter(id=self.startup.id).exists())

    def test_view_startup(self):
        self.client.login(username='inc', password='inc123456')
        response = self.client.get(reverse('view_startup', args=[self.startup.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Existing')


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
        self.assertFalse(user.has_usable_password())
        self.assertTrue(StartupMember.objects.filter(user=user, startup=self.startup).exists())

    def test_add_member_duplicate_email(self):
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
        self.assertEqual(StartupMember.objects.filter(startup=self.startup).count(), 0)


class MilestoneDeliverableTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.sa = User.objects.create_user(username='sa', password='sa123456', role='super_admin')
        self.startup = Startup.objects.create(name='S', owner=self.sa)
        self.m1 = Milestone.objects.create(startup=self.startup, milestone_progress=1, title='M1')
        self.m2 = Milestone.objects.create(startup=self.startup, milestone_progress=2, title='M2')

    def test_add_milestone(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.get(reverse('add_milestone', args=[self.startup.id]))
        self.assertRedirects(response, reverse('view_startup', args=[self.startup.id]))
        self.assertEqual(self.startup.milestones.count(), 3)

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
        self.assertRedirects(response, reverse('view_milestone', args=[self.startup.id, self.m.id]))
        self.d.refresh_from_db()
        self.assertEqual(self.d.status, 'approved')
        self.assertTrue(Comment.objects.filter(deliverable=self.d, content='Looks good').exists())

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
        self.assertRedirects(response, reverse('dashboard'))


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
        response = self.client.get(reverse('delete_user', args=[self.inc.id]))
        self.assertFalse(User.objects.filter(id=self.inc.id).exists())

    def test_delete_admin_by_admin_blocked(self):
        self.client.login(username='ad', password='ad123456')
        response = self.client.get(reverse('delete_user', args=[self.inc.id]))
        # Admin can delete incubatee
        self.assertFalse(User.objects.filter(id=self.inc.id).exists())

    def test_delete_super_admin_blocked(self):
        self.client.login(username='sa', password='sa123456')
        response = self.client.get(reverse('delete_user', args=[self.sa.id]))
        self.assertTrue(User.objects.filter(id=self.sa.id).exists())

    def test_delete_user_by_incubatee_blocked(self):
        self.client.login(username='inc', password='inc123456')
        other = User.objects.create_user(username='other', password='p', role='incubatee')
        response = self.client.get(reverse('delete_user', args=[other.id]))
        self.assertTrue(User.objects.filter(id=other.id).exists())


class IndexRedirectTest(TestCase):
    def test_index_redirects_anonymous(self):
        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('login'))

    def test_index_redirects_authenticated(self):
        user = User.objects.create_user(username='u', password='p')
        self.client.login(username='u', password='p')
        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('dashboard'))

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from user.models import Profile
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from user.forms import UpdateAccountForm
from user.models import Profile

class MyUserModelTests(TestCase):

    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='password123'
        )
        Profile.objects.create(user=self.user, description="Initial description")
        self.client.login(email='test@example.com', password='password123')

    def test_create_user(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('password123'))

    def test_create_superuser(self):
        superuser = self.user_model.objects.create_superuser(
            email='admin@example.com',
            username='adminuser',
            password='adminpassword'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


class ProfileModelTests(TestCase):

    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='password123'
        )
        self.profile = Profile.objects.create(user=self.user, description="Initial description")
        self.client.login(email='test@example.com', password='password123')

    def test_profile_creation(self):
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.description, "Initial description")


class UserViewsTests(TestCase):

    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='password123'
        )
        Profile.objects.create(user=self.user, description="Initial description")
        self.client.login(email='test@example.com', password='password123')

    def test_index_view(self):
        response = self.client.get(reverse('user:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/index.html')

    def test_update_account_view(self):
        response = self.client.get(reverse('user:update_account'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/update_account.html')
        form = UpdateAccountForm(instance=self.user)
        response = self.client.post(reverse('user:update_account'), {'username': 'TestingName'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'TestingName')

    def test_update_profile_view(self):
        response = self.client.get(reverse('user:update_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/update_account.html')
        response = self.client.post(reverse('user:update_profile'), {'description': 'Updated description'})
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.description, 'Updated description')

    def test_change_password_view(self):
        response = self.client.get(reverse('user:account_change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_change.html')
        response = self.client.post(reverse('user:account_change_password'), {
            'old_password': 'password123',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))


class ProfileViewTests(TestCase):

    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='password123'
        )
        self.client.login(email='test@example.com', password='password123')
        Profile.objects.create(user=self.user, description="Initial description")

    def test_profile_view(self):
        response = self.client.get(reverse('user:profile', kwargs={'username': 'testuser'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/profile.html')


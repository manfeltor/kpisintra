from django.test import TestCase

# Create your tests here.

from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser, Company
from .forms import CustomUserCreationForm, CompanyForm

class UsersAppTestCase(TestCase):

    def setUp(self):
        # Set up initial data
        self.company = Company.objects.create(name="Test Company", omni=True, interior=False, wh=True)
        self.superuser = CustomUser.objects.create_superuser(
            username="admin",
            password="adminpass",
            email="admin@test.com"
        )
        self.staff_user = CustomUser.objects.create_user(
            username="staff",
            password="staffpass",
            email="staff@test.com",
            role=CustomUser.MANAGER,
            company=self.company
        )
        self.client = Client()

    # View Tests
    def test_login_view_success(self):
        response = self.client.post(reverse('login'), {'username': 'admin', 'password': 'adminpass'})
        self.assertRedirects(response, reverse('home'))

    def test_login_view_invalid_credentials(self):
        response = self.client.post(reverse('login'), {'username': 'admin', 'password': 'wrongpass'})
        self.assertTemplateUsed(response, 'landing.html')
        self.assertContains(response, 'Usuario y/o contraseña inválidos')

    def test_create_user_view_get(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('create_user'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_user.html')

    def test_create_user_view_post(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse('create_user'), {
            'username': 'newuser',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'role': CustomUser.EMPLOYEE
        })
        self.assertRedirects(response, reverse('list_users'))
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())

    def test_user_list_view(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('list_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.staff_user.username)

    def test_delete_user(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse('delete_user', args=[self.staff_user.id]))
        self.assertRedirects(response, reverse('list_users'))
        self.assertFalse(CustomUser.objects.filter(id=self.staff_user.id).exists())

    def test_companies_list_view(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('list_companies'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.company.name)

    def test_modify_company_view(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('modify_company', args=[self.company.id]), {
            'omni': False,
            'interior': True,
            'wh': True
        })
        self.assertRedirects(response, reverse('list_companies'))
        self.company.refresh_from_db()
        self.assertFalse(self.company.omni)
        self.assertTrue(self.company.interior)

    # Model Tests
    def test_custom_user_model(self):
        self.assertEqual(str(self.staff_user), 'staff')
        self.assertTrue(self.staff_user.is_management)

    def test_company_model(self):
        self.assertEqual(str(self.company), 'Test Company')

    # Form Tests
    def test_custom_user_creation_form_valid(self):
        form = CustomUserCreationForm(data={
            'username': 'formuser',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'role': CustomUser.CLIENT,
        })
        self.assertTrue(form.is_valid())

    def test_company_form_valid(self):
        form = CompanyForm(data={
            'omni': False,
            'interior': True,
            'wh': False
        })
        self.assertTrue(form.is_valid())

    # URL Tests
    def test_urls(self):
        self.client.force_login(self.superuser)
        urls = [
            reverse('login'),
            reverse('logout'),
            reverse('create_user'),
            reverse('list_users'),
            reverse('delete_user', args=[self.staff_user.id]),
            reverse('list_companies'),
            reverse('modify_company', args=[self.company.id]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200 if 'login' not in url else 302)
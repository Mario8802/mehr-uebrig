from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from .forms import BudgetForm
from .models import Budget, MONEY_FIELDS

class BudgetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='mario', password='test-long-password-821!')
        cls.other = get_user_model().objects.create_user(username='other', password='test-long-password-456!')

    def payload(self, **overrides):
        return {'month': '2026-09', **{key: '0' for key in MONEY_FIELDS}, 'income': '2400',
                'rent': '850', 'energy': '110', 'food': '320', 'transport': '80',
                'phone': '45', 'insurance': '120', 'other': '180', 'cut': '10', **overrides}

    def test_decimal_calculation(self):
        data = self.payload()
        budget = Budget(**{key: Decimal(data[key]) for key in MONEY_FIELDS}, cut=10)
        self.assertEqual(budget.total, Decimal('1705'))
        self.assertEqual(budget.remaining, Decimal('695'))
        self.assertEqual(budget.saving, Decimal('62.50'))
        budget.income = Decimal('1000')
        self.assertEqual(budget.remaining, Decimal('-705'))

    def test_guest_can_preview_but_cannot_save(self):
        self.assertContains(self.client.get('/'), 'Was bleibt für dich?')
        response = self.client.post('/', self.payload())
        self.assertRedirects(response, reverse('login'))
        self.assertFalse(Budget.objects.exists())

    def test_save_then_update_one_month_and_create_another(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.post('/', self.payload()), '/?month=2026-09')
        self.client.post('/', self.payload(income='2500.25'))
        self.assertEqual(Budget.objects.count(), 1)
        self.assertEqual(Budget.objects.get().income, Decimal('2500.25'))
        self.client.post('/', self.payload(month='2026-10'))
        self.assertEqual(Budget.objects.count(), 2)
        response = self.client.get('/?month=2026-09')
        self.assertEqual(response.context['initial']['income'], '2500.25')

    def test_users_cannot_read_or_overwrite_each_others_budget(self):
        victim = Budget.objects.create(user=self.other, month=date(2026, 9, 1), income='9876.54')
        self.client.force_login(self.user)
        response = self.client.get(f'/?month=2026-09&user={self.other.pk}&id={victim.pk}')
        self.assertEqual(response.context['initial']['income'], '0')
        self.assertNotContains(response, '9876.54')
        self.client.post('/', self.payload(user=self.other.pk, id=victim.pk))
        victim.refresh_from_db()
        self.assertEqual(victim.income, Decimal('9876.54'))
        self.assertTrue(Budget.objects.filter(user=self.user).exists())

    def test_invalid_values_are_rejected_without_saving(self):
        self.client.force_login(self.user)
        for key, value in [('income', '-1'), ('rent', '1000001'), ('cut', '51'), ('food', 'NaN'), ('month', 'nope'), ('phone', '1.001')]:
            with self.subTest(key=key):
                response = self.client.post('/', self.payload(**{key: value}))
                self.assertEqual(response.status_code, 400)
                self.assertFalse(Budget.objects.exists())

    def test_csrf_is_required_for_saving(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/', self.payload()).status_code, 403)
        self.assertFalse(Budget.objects.exists())

    def test_database_rejects_duplicate_month(self):
        Budget.objects.create(user=self.user, month=date(2026, 9, 1))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Budget.objects.create(user=self.user, month=date(2026, 9, 1))

    def test_database_rejects_negative_expense(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Budget.objects.create(user=self.user, month=date(2026, 9, 1), rent=-1)

    def test_registration_login_and_post_logout(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser', 'password1': 'Some-unique-passphrase-891!', 'password2': 'Some-unique-passphrase-891!',
        })
        self.assertRedirects(response, '/')
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.client.post(reverse('logout'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.post(reverse('login'), {'username': 'newuser', 'password': 'Some-unique-passphrase-891!'}), '/')

    def test_private_budget_response_is_not_cacheable(self):
        self.client.force_login(self.user)
        response = self.client.get('/')
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_month_form_normalizes_to_first_day(self):
        form = BudgetForm(self.payload())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['month'], date(2026, 9, 1))

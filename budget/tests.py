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
        self.assertContains(self.client.get('/'), 'Dein Geld. Dein Plan')
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
            'username': 'newuser', 'email': 'new@example.com', 'password1': 'Some-unique-passphrase-891!', 'password2': 'Some-unique-passphrase-891!',
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

    def test_budget_fields_render_without_javascript(self):
        response = self.client.get('/')
        for key in MONEY_FIELDS:
            self.assertContains(response, f'name="{key}"')
        self.client.force_login(self.user)
        self.client.post('/', self.payload(food='', other=''))
        record = Budget.objects.get(user=self.user)
        self.assertEqual(record.food, Decimal('0'))
        self.assertEqual(record.other, Decimal('0'))

    def test_delete_requires_confirmation_and_ownership(self):
        record = Budget.objects.create(user=self.user, month=date(2026, 9, 1))
        self.client.force_login(self.other)
        url = reverse('delete_budget', args=[record.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Budget.objects.filter(pk=record.pk).exists())
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Budget.objects.filter(pk=record.pk).exists())

    def test_csv_contains_only_the_owned_saved_budget(self):
        record = Budget.objects.create(user=self.user, month=date(2026, 9, 1), income='2000.45')
        url = reverse('export_budget', args=[record.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers['Content-Disposition'])
        self.assertIn('2000,45', response.content.decode())
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_password_reset_email_and_token_work_end_to_end(self):
        import re
        from django.core import mail
        from django.test import override_settings
        self.user.email = 'mario@example.com'
        self.user.save()
        with override_settings(PASSWORD_RESET_ENABLED=True, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            response = self.client.post(reverse('password_reset'), {'email': self.user.email})
            self.assertRedirects(response, reverse('password_reset_done'))
            self.assertEqual(len(mail.outbox), 1)
            link = re.search(r'http://testserver([^\s]+)', mail.outbox[0].body).group(1)
            response = self.client.get(link)
            self.assertEqual(response.status_code, 302)
            reset_url = response.url
            self.assertContains(self.client.get(reset_url), 'Wähle ein neues Passwort')
            password = 'Brand-new-passphrase-2026!'
            self.assertRedirects(self.client.post(reset_url, {'new_password1': password, 'new_password2': password}), reverse('password_reset_complete'))
            self.user.refresh_from_db()
            self.assertTrue(self.user.check_password(password))
            self.assertContains(self.client.get(link), 'abgelaufen')

    def test_reset_without_email_service_is_honest(self):
        from django.test import override_settings
        with override_settings(PASSWORD_RESET_ENABLED=False):
            response = self.client.post(reverse('password_reset'), {'email': 'x@example.com'})
            self.assertEqual(response.status_code, 503)
            self.assertContains(response, 'noch nicht eingerichtet', status_code=503)

    def test_login_lockout_cannot_be_bypassed_by_cookie_or_user_agent_rotation(self):
        from django.test import override_settings
        with override_settings(AXES_FAILURE_LIMIT=3):
            for attempt in range(3):
                response = Client().post(reverse('login'), {'username': self.user.username, 'password': 'wrong'}, HTTP_USER_AGENT=f'browser-{attempt}')
            self.assertEqual(response.status_code, 429)
            response = Client().post(reverse('login'), {'username': self.user.username, 'password': 'test-long-password-821!'}, HTTP_USER_AGENT='another-browser')
            self.assertEqual(response.status_code, 429)
            response = Client().post(reverse('login'), {'username': self.other.username, 'password': 'test-long-password-456!'})
            self.assertEqual(response.status_code, 302)

    def test_password_change_preserves_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('password_change'), {
            'old_password': 'test-long-password-821!',
            'new_password1': 'Changed-even-longer-827!', 'new_password2': 'Changed-even-longer-827!',
        })
        self.assertRedirects(response, reverse('password_change_done'))
        self.assertIn('_auth_user_id', self.client.session)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Changed-even-longer-827!'))

    def test_health_detects_database_failure_without_leaking_details(self):
        from unittest.mock import patch
        from django.db import OperationalError
        self.assertEqual(self.client.get(reverse('health')).json(), {'status': 'ok'})
        with patch('budget.views.connection.cursor', side_effect=OperationalError('private-credentials')):
            response = self.client.get(reverse('health'))
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private-credentials', response.content.decode())

    def test_production_https_redirect_and_cookie_flags(self):
        from django.test import override_settings
        with override_settings(SECURE_SSL_REDIRECT=True, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True):
            self.assertEqual(self.client.get('/').status_code, 301)
            response = self.client.get('/', secure=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.cookies['csrftoken']['secure'])

    def test_round_half_up_matches_frontend(self):
        record = Budget(food=Decimal('0.10'), other=Decimal('0.20'), cut=5)
        self.assertEqual(record.saving, Decimal('0.02'))

import csv
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_GET
from .forms import BudgetForm, RegistrationForm
from .models import Budget, CATEGORIES, MONEY_FIELDS


def parse_month(value):
    try:
        result = datetime.strptime(value, '%Y-%m').date().replace(day=1)
        if 2000 <= result.year <= 2100:
            return result
    except (ValueError, TypeError):
        pass
    return timezone.localdate().replace(day=1)


@never_cache
@require_http_methods(['GET', 'POST'])
def dashboard(request):
    if request.method == 'POST' and not request.user.is_authenticated:
        return redirect('login')
    month = parse_month(request.POST.get('month') if request.method == 'POST' else request.GET.get('month'))
    record = Budget.objects.filter(user=request.user, month=month).first() if request.user.is_authenticated else None
    form = BudgetForm(request.POST if request.method == 'POST' else None, instance=record,
                      initial={'month': month.strftime('%Y-%m')})
    status = 200
    if request.method == 'POST':
        if form.is_valid():
            values = {key: form.cleaned_data[key] for key in [*MONEY_FIELDS, 'cut']}
            Budget.objects.update_or_create(user=request.user, month=form.cleaned_data['month'], defaults=values)
            messages.success(request, 'Dein Monatsbudget wurde gespeichert.')
            return redirect('/?month=' + form.cleaned_data['month'].strftime('%Y-%m'))
        status = 400
    initial = {key: str(getattr(record, key)) if record else '0' for key in MONEY_FIELDS}
    initial['cut'] = record.cut if record else 10
    if request.method == 'POST':
        initial.update({key: request.POST.get(key, '') for key in [*MONEY_FIELDS, 'cut']})
    history = Budget.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, 'dashboard.html', {
        'initial': initial, 'month': month.strftime('%Y-%m'), 'month_date': month,
        'budget_form': form, 'expense_fields': [(key, form[key]) for key, _ in CATEGORIES],
        'history': history, 'has_budget': record is not None, 'record': record,
        'total': record.total if record else 0, 'remaining': record.remaining if record else 0,
        'saving': record.saving if record else 0,
    }, status=status)


@never_cache
@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Dein Konto ist bereit. Lege jetzt dein erstes Budget an.')
        return redirect('dashboard')
    return render(request, 'registration/register.html', {'form': form})


class BudgetPasswordResetView(PasswordResetView):
    def dispatch(self, request, *args, **kwargs):
        if not settings.PASSWORD_RESET_ENABLED:
            return render(request, 'registration/reset_unavailable.html', status=503)
        return super().dispatch(request, *args, **kwargs)


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def delete_budget(request, pk):
    record = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        month = record.month.strftime('%Y-%m')
        record.delete()
        messages.success(request, 'Das Monatsbudget wurde gelöscht.')
        return redirect('/?month=' + month)
    return render(request, 'delete_budget.html', {'record': record})


@login_required
@never_cache
@require_GET
def export_budget(request, pk):
    record = get_object_or_404(Budget, pk=pk, user=request.user)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="budget-{record.month:%Y-%m}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Monat', 'Kategorie', 'Betrag (EUR)'])
    for key, label in [('income', 'Nettoeinkommen'), *CATEGORIES]:
        writer.writerow([f'{record.month:%Y-%m}', label, str(getattr(record, key)).replace('.', ',')])
    writer.writerow([f'{record.month:%Y-%m}', 'Verfügbar', str(record.remaining).replace('.', ',')])
    return response


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})

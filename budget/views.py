from datetime import datetime
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .forms import BudgetForm
from .models import Budget, MONEY_FIELDS


def parse_month(value):
    try:
        return datetime.strptime(value, '%Y-%m').date().replace(day=1)
    except (ValueError, TypeError):
        return timezone.localdate().replace(day=1)


@never_cache
@require_http_methods(['GET', 'POST'])
def dashboard(request):
    if request.method == 'POST' and not request.user.is_authenticated:
        return redirect('login')
    month = parse_month(request.POST.get('month') if request.method == 'POST' else request.GET.get('month'))
    record = Budget.objects.filter(user=request.user, month=month).first() if request.user.is_authenticated else None
    form = BudgetForm(request.POST if request.method == 'POST' else None, instance=record)
    status = 200
    if request.method == 'POST':
        if form.is_valid():
            # Ignore any client-supplied user or record ID. The session owns the budget.
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
        'initial': initial, 'month': month.strftime('%Y-%m'), 'budget_form': form,
        'history': history, 'has_budget': record is not None,
    }, status=status)


@never_cache
@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Dein Konto ist bereit. Lege jetzt dein erstes Budget an.')
        return redirect('dashboard')
    return render(request, 'registration/register.html', {'form': form})

from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

CATEGORIES = [
    ('rent', 'Wohnen & Betriebskosten'), ('energy', 'Strom & Heizung'),
    ('food', 'Lebensmittel'), ('transport', 'Mobilität'),
    ('phone', 'Internet & Handy'), ('insurance', 'Versicherungen & Raten'),
    ('other', 'Freizeit & Sonstiges'),
]
MONEY_FIELDS = ['income'] + [key for key, _ in CATEGORIES]

def money_field():
    return models.DecimalField(max_digits=9, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000000)])

class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    month = models.DateField()
    income = money_field()
    rent = money_field()
    energy = money_field()
    food = money_field()
    transport = money_field()
    phone = money_field()
    insurance = money_field()
    other = money_field()
    cut = models.PositiveSmallIntegerField(default=10, validators=[MaxValueValidator(50)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month']
        constraints = [
            models.UniqueConstraint(fields=['user', 'month'], name='unique_user_month'),
            models.CheckConstraint(condition=models.Q(month__day=1), name='month_first_day'),
            models.CheckConstraint(condition=models.Q(cut__gte=0, cut__lte=50), name='valid_cut'),
        ] + [models.CheckConstraint(condition=models.Q(**{f'{key}__gte': 0, f'{key}__lte': 1000000}),
                                    name=f'valid_{key}') for key in MONEY_FIELDS]

    @property
    def total(self):
        return sum((getattr(self, key) for key, _ in CATEGORIES), Decimal('0'))

    @property
    def remaining(self):
        return self.income - self.total

    @property
    def saving(self):
        return ((self.food + self.transport + self.phone + self.other) * Decimal(self.cut) / 100).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

    def __str__(self):
        return f'{self.user_id}: {self.month:%Y-%m}'

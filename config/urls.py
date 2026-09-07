from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from budget import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('health/', views.health, name='health'),
    path('budgets/<int:pk>/delete/', views.delete_budget, name='delete_budget'),
    path('budgets/<int:pk>/export/', views.export_budget, name='export_budget'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password-reset/', views.BudgetPasswordResetView.as_view(), name='password_reset'),
    path('accounts/password-reset/sent/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('accounts/password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('admin/', admin.site.urls),
]

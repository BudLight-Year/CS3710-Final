from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
from allauth.account.views import login, logout, signup
from allauth.account.views import PasswordResetView, PasswordResetDoneView, PasswordResetFromKeyView, PasswordResetFromKeyDoneView, ConfirmEmailView
from .views import CustomPasswordChangeView, ProfileView, become_advertiser
from .forms import CustomAuthenticationForm

app_name = "user"
urlpatterns = [
    path("", views.index, name="index"),
    path('signup/', signup, name='account_signup'),
    path('login/', login, name='account_login'),    
    path("logout/", logout, name='account_logout'),
    path('password/change/', CustomPasswordChangeView.as_view(), name='account_change_password'),
    path('password/reset/', PasswordResetView.as_view(), name='account_reset_password'),
    path('password/reset/done/', PasswordResetDoneView.as_view(), name='account_reset_password_done'),
    path('password/reset/key/<uidb36>-<key>/', PasswordResetFromKeyView.as_view(), name='account_reset_password_from_key'),
    path('password/reset/key/done/', PasswordResetFromKeyDoneView.as_view(), name='account_reset_password_from_key_done'),
    path('confirm-email/<key>/', ConfirmEmailView.as_view(), name='account_confirm_email'),
    path("update-account/", views.update_account, name='update_account'),
    path("update-profile/", views.update_profile, name='update_profile'),
    path("change-password/", views.change_password, name='change_password'),
    path('password-reset/', auth_views.PasswordResetView.as_view(success_url=reverse_lazy('user:password_reset_done')), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('user:password_reset_complete')), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('profile/<str:username>/', ProfileView.as_view(), name='profile'),
    path('become-advertiser/', become_advertiser, name='become_advertiser'),
]

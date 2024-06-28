from django.urls import path, include
from .api import UserApi, LoginApi, PasswordResetRequestView, PasswordResetView
from knox import views as knox_views

urlpatterns = [
    path('api/auth', include('knox.urls')),
    path('api/auth/login', LoginApi.as_view()),
    path('api/auth/user', UserApi.as_view()),
    path('api/auth/logout', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('api/auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('api/auth/password-reset-confirm/', PasswordResetView.as_view(), name='password_reset_confirm'),

]

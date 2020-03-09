from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.base_view, name='base'),
    path('login_info/', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='registrations/login.html'), name='login'),
    path('retry/', auth_views.LoginView.as_view(template_name='registrations/retry_signup.html'), name='retry'),
    path('logout/', views.logout, name='logout'),
    path('login/signup_email/', views.signup_email, name='signup_email'),
    path('oauth/', include('social_django.urls', namespace='social'))
]

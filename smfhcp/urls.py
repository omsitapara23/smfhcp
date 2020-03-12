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
    path('login/login_user/', views.login_user, name='login_user'),
    path('send_invite/', views.send_invite, name='send_invite'),
    path('doctor_signup/<int:otp>/', views.doctor_signup, name='doctor_signup'),
    path('create_profile/', views.create_profile, name='create_profile'),
    path('view_profile/<str:user_name>', views.view_profile, name='view_profile'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('oauth/', include('social_django.urls', namespace='social'))
]

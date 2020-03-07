from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from smfhcpApp.settings import LOGOUT_REDIRECT_URL

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='registrations/login.html'), name='login'),
    path('logout/', views.logout, name='logout'),
    path('oauth/', include('social_django.urls', namespace='social'))
]

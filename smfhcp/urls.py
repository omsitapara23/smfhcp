from django.urls import path, include
import smfhcp.views.base as base_views
import smfhcp.views.auth as auth_views
import smfhcp.views.password as password_views
import smfhcp.views.profile as profile_views
import smfhcp.views.post as post_views
import smfhcp.views.search as search_views


urlpatterns = [
    path('', base_views.base_view, name='base'),
    path('login_info/', auth_views.index, name='index'),
    path('trending/', base_views.trending_view, name='trending'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout, name='logout'),
    path('login/signup_email/', auth_views.signup_email, name='signup_email'),
    path('login/login_user/', auth_views.login_user, name='login_user'),
    path('send_invite/', auth_views.send_invite, name='send_invite'),
    path('doctor_signup/<int:otp>/', auth_views.doctor_signup, name='doctor_signup'),
    path('create_profile/', auth_views.create_profile, name='create_profile'),
    path('view_profile/<str:user_name>', profile_views.view_profile, name='view_profile'),
    path('update_profile/', profile_views.update_profile, name='update_profile'),
    path('create_post/case_study/', post_views.create_case_study, name='create_case_study'),
    path('create_post/general_post/', post_views.create_general_post, name='create_general_post'),
    path('view_post/<str:post_id>', post_views.view_post, name='view_post'),
    path('follow_or_unfollow/', profile_views.follow_or_unfollow, name='follow_or_unfollow'),
    path('add_comment/', post_views.add_comment, name='add_comment'),
    path('add_reply/', post_views.add_reply, name='add_reply'),
    path('forgot_password/', password_views.forgot_password, name='forgot_password'),
    path('reset_password/<str:user_name>/<str:otp>', password_views.reset_password, name='reset_password'),
    path('get_follow_list/', profile_views.get_follow_list, name='get_follow_list'),
    path('search/', search_views.search, name='search'),
    path('tagged/<str:tag>', search_views.tagged, name='tagged'),
    path('oauth/', include('social_django.urls', namespace='social'))
]

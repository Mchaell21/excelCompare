from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("login/request-otp/", views.request_otp_login, name="request_otp"),
     path("login/verify-otp/", views.login_otp_view, name="login_otp"),

    # Kelola User (khusus superadmin)
    path("manage/", views.user_manage, name="manage"),
    path("manage/create/", views.user_create, name="user_create"),
    path("manage/edit/<uuid:user_id>/", views.user_create, name="user_edit"),
    path("manage/<uuid:user_id>/toggle-active/",
         views.user_toggle_active, name="user_toggle_active"),
    path("manage/<uuid:user_id>/change-role/",
         views.user_change_role, name="user_change_role"),
    path("manage/<uuid:user_id>/reset-password/",
         views.user_reset_password, name="user_reset_password"),

     # User Profile & Password
    path("profile/", views.user_profile, name="profile"),
    path("profile/change-password/", views.change_password, name="change_password"),
    
    # Telegram Confirmation & Disconnect
    path("profile/telegram/confirm/", views.telegram_confirm, name="telegram_confirm"),
    path("profile/telegram/disconnect/", views.telegram_disconnect, name="telegram_disconnect"),
]

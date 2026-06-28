from django.urls import path

from .ajax import ajax_login_view
from apps.accounts.ajax import ajax_register_view
from .views import UserLoginView, UserLogoutView, register_view


app_name = "accounts"


urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("ajax_register_view/", ajax_register_view, name="ajax_register"),
    path("ajax/login/", ajax_login_view, name="ajax_login"),
]
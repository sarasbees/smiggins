from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home", views.home, name="home"),
    path("login", views.login, name="login"),
    path("signup", views.signup, name="signup"),
    path("settings", views.settings, name="settings"),
    path("logout", views.logout, name="logout"),
    path("robots.txt", views.robots, name="robots"),
    path("u/<str:username>", views.user, name="user"),
    path("p/<int:post_id>", views.post, name="post"),
    path("c/<int:comment_id>", views.comment, name="comment")
]
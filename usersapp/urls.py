from django.contrib.auth import views as auth_views
from django.urls import path
from .views import login_view, create_user_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('create_user/', create_user_view, name='create_user'),
]
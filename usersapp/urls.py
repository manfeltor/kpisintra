from django.contrib.auth import views as auth_views
from django.urls import path
from .views import login_view, create_user_view, user_list_view, delete_user

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('create_user/', create_user_view, name='create_user'),
    path('listusers/', user_list_view, name='list_users'),
    path('delete-user/<int:user_id>/', delete_user, name='delete_user'),
]
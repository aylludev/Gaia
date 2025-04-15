from django.urls import path
from hades.views.login.views import LoginFormView, LogoutView
from hades.views.user.views import *

app_name = 'hades'

urlpatterns = [
    path('login/', LoginFormView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/list/', UserListView.as_view(), name='user_list'),
    path('user/add/', UserCreateView.as_view(), name='user_add'),
    path('user/update/<int:pk>/', UserUpdateView.as_view(), name='user_edit'),
    path('profile/update/', ProfileUpdateView.as_view(), name='user_profile'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/change/password/', PasswordUpdateView.as_view(), name='profile_change_password'),
    path('change/group/<int:pk>/', UserChangeGroup.as_view(), name='change_group'),
]

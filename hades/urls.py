from django.urls import path
from hades.views.login.views import LoginFormView, LogoutView, UserCreateView

app_name = 'hades'

urlpatterns = [
    path('login/', LoginFormView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', UserCreateView.as_view(), name='register'),
]

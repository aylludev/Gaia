from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views.generic import RedirectView, CreateView
from Gaia import settings
from django.contrib.auth import login, logout
from hades.forms import UserForm
from hades.models import User
from django.urls import reverse_lazy
from django.http import JsonResponse

class LoginFormView(LoginView):
    template_name = "user/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar Sesión'
        return context

class LogoutView(RedirectView):
    pattern_name = 'hades:login'

    def dispatch(self, request, *args, **kwargs):
        logout(request)
        return super().dispatch(request, *args, **kwargs)

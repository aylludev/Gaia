from datetime import datetime
from django.contrib.auth.models import Group
from crum import get_current_request
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy

class IsSuperuserMixin:
    def dispatch(self, request, *args, **kwargs):
        if  request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        return redirect('index')
    
    def context_data(self, **kwargs):
        context = super().context_data(**kwargs)
        context['date_now'] = datetime.now()
        return context

class ValidatePermissionsMixin:
    permission_required = ''
    url_redirect = None

    def get_perms(self):
        perms=[]
        if isinstance(self.permission_required, list):
            perms.append(self.permission_required)
        else:
            perms = list(self.permission_required)
        return perms
    
    def get_url_redirect(self):
        if self.url_redirect is None:
            return reverse_lazy('core:dashboard')
        return self.url_redirect

    def dispatch(self, request, *args, **kwargs):
        request = get_current_request()
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if 'group' in request.session:
            group_data = request.session['group']

            # Verificar si es un id y convertirlo a un objeto Group
            if isinstance(group_data, int):
                group = Group.objects.get(id=group_data)
            elif isinstance(group_data, dict):
                group = Group.objects.get(id=group_data['id'])
            else:
                group = group_data

            perms = self.get_perms()
            for p in perms:
                if not group.permissions.filter(codename=p).exists():
                    messages.error(request, 'No tienes permisos para acceder a esta sección.')
                    return HttpResponseRedirect(self.get_url_redirect())
                return super().dispatch(request, *args, **kwargs)
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return HttpResponseRedirect(self.get_url_redirect())
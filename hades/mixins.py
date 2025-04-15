from datetime import datetime
from crum import get_current_request
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.models import Group

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
    permission_required = ''  # Puede ser 'codename' o ['codename1', 'codename2']
    url_redirect = None  # URL a redirigir si no tiene permiso

    def get_perms(self):
        perms = []
        if isinstance(self.permission_required, str):
            perms.append(self.permission_required)
        else:
            perms = list(self.permission_required)
        return perms

    def get_url_redirect(self):
        return self.url_redirect or reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        group_data = request.session.get('group')
        if group_data:
            group_id = group_data[0]['id']
            group = Group.objects.filter(id=group_id).first()
            if group:
                for perm in self.get_perms():
                    if not group.permissions.filter(codename=perm).exists():
                        messages.error(request, 'No tiene permiso para ingresar a este módulo')
                        return HttpResponseRedirect(self.get_url_redirect())
                return super().dispatch(request, *args, **kwargs)
        messages.error(request, 'Debe tener un grupo asignado en sesión')
        return HttpResponseRedirect(self.get_url_redirect())
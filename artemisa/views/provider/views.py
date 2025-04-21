from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from artemisa.forms import ProviderForm
from hades.mixins import ValidatePermissionRequiredMixin
from artemisa.models import Provider
from datetime import datetime

class ProviderListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = Provider
    template_name = 'provider/list.html'
    permission_required = 'view_provider'

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = []
                for i in Provider.objects.all():
                    data.append(i.to_json())
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Proveedores'
        context['create_url'] = reverse_lazy('artemisa:provider_create')
        context['list_url'] = reverse_lazy('artemisa:provider_list')
        context['entity'] = 'Proveedores'
        return context


class ProviderCreateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, CreateView):
    model = Provider
    form_class = ProviderForm
    template_name = 'form.html'
    success_url = reverse_lazy('artemisa:provider_list')
    permission_required = 'add_provider'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                form = self.get_form()
                form.instance.created_by = request.user
                data = form.save()
            else:
                data['error'] = 'No ha ingresado a ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creación un Proveedor'
        context['entity'] = 'Proveedores'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        return context

class ProviderUpdateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, UpdateView):
    model = Provider
    form_class = ProviderForm
    template_name = 'form.html'
    success_url = reverse_lazy('artemisa:provider_list')
    permission_required = 'change_provider'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'edit':
                form = self.get_form()
                form.instance.updated_by = request.user
                form.instance.updated_at = datetime.now()
                data = form.save()
            else:
                data['error'] = 'No ha ingresado a ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edición un Proveedor'
        context['entity'] = 'Proveedores'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        return context


class ProviderDeleteView(LoginRequiredMixin, ValidatePermissionRequiredMixin, DeleteView):
    model = Provider
    template_name = 'delete.html'
    success_url = reverse_lazy('artemisa:provider_list')
    permission_required = 'delete_provider'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            self.object.delete()
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminación de un Proveedor'
        context['entity'] = 'Proveedores'
        context['list_url'] = self.success_url
        return context

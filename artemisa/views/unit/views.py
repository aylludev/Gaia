from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from artemisa.forms import UnitMeasureForm
from artemisa.models import UnitMeasure
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from hades.mixins import ValidatePermissionRequiredMixin
from datetime import datetime

class UnitListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = UnitMeasure
    template_name = 'unit/list.html'
    permission_required = 'view_unitmeasure'

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = []
                position = 1
                for i in UnitMeasure.objects.all():
                    item = i.to_json()
                    item['position'] = position
                    data.append(item)
                    position += 1
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Unidades de Medida'
        context['create_url'] = reverse_lazy('artemisa:unit_create')
        context['list_url'] = reverse_lazy('artemisa:unit_list')
        context['entity'] = 'Unidades de Medida'
        return context
    
class UnitCreateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, CreateView):
    model = UnitMeasure
    form_class = UnitMeasureForm
    template_name = 'form.html'
    success_url = reverse_lazy('artemisa:unit_list')
    permission_required = 'add_unitmeasure'
    url_redirect = success_url

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                form = self.get_form()
                form.instance.created_by = request.user
                data = form.save()
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Unidad de Medida'
        context['list_url'] = self.success_url
        context['entity'] = 'Unidades de Medida'
        context['action'] = 'add'
        return context
    
class UnitUpdateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, UpdateView):
    model = UnitMeasure
    form_class = UnitMeasureForm
    template_name = 'form.html'
    success_url = reverse_lazy('artemisa:unit_list')
    permission_required = 'change_unitmeasure'
    url_redirect = success_url

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
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Unidad de Medida'
        context['list_url'] = self.success_url
        context['entity'] = 'Unidades de Medida'
        context['action'] = 'edit'
        return context

class UnitDeleteView(LoginRequiredMixin, ValidatePermissionRequiredMixin, DeleteView):
    model = UnitMeasure
    template_name = 'delete.html'
    success_url = reverse_lazy('artemisa:unit_list')
    permission_required = 'delete_unitmeasure'
    url_redirect = success_url

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'delete':
                self.object = self.get_object()
                self.object.delete()
                data['success'] = True
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Unidad de Medida'
        context['list_url'] = self.success_url
        context['entity'] = 'Unidades de Medida'
        return context
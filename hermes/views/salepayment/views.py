from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from ilitia.models import Sale
from hermes.models import SalePayment
from hermes.forms import SalePaymentForm
from hades.mixins import ValidatePermissionRequiredMixin
from django.db.models import Sum, DecimalField, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.shortcuts import get_object_or_404
from datetime import datetime

class SalePaymentListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = Sale
    template_name = 'salepayment/list.html'
    permission_required = 'view_salepayment'

    def post(self, request, *args, **kwargs):
        try:
            action = request.POST.get('action', '')
            if action == 'searchdata':
                # Parámetros de paginación de DataTables
                start = int(request.POST.get('start', 0))
                length = int(request.POST.get('length', 10))
                search_value = request.POST.get('search[value]', '')
                draw = int(request.POST.get('draw', 1))

                # Parámetros de ordenamiento
                order_column_index = int(request.POST.get('order[0][column]', 3))
                order_dir = request.POST.get('order[0][dir]', 'desc')

                # Mapeo de columnas para ordenamiento
                columns = ['id', 'invoice_number', 'cli__names', 'date_joined', 'total', 'id', 'id', 'id', 'id']
                order_column = columns[order_column_index] if order_column_index < len(columns) else 'date_joined'

                if order_dir == 'desc':
                    order_column = '-' + order_column

                # Queryset base
                queryset = Sale.objects.filter(type_payment='CREDIT').select_related('cli')

                # Filtro de búsqueda
                if search_value:
                    queryset = queryset.filter(
                        Q(invoice_number__icontains=search_value) |
                        Q(cli__names__icontains=search_value) |
                        Q(cli__last_names__icontains=search_value)
                    )

                # Total de registros
                records_total = Sale.objects.filter(type_payment='CREDIT').count()
                records_filtered = queryset.count()

                # Aplicar ordenamiento
                queryset = queryset.order_by(order_column)

                # Aplicar paginación
                queryset = queryset[start:start + length]

                # Preparar datos
                result_data = []
                for i in queryset:
                    total_paid = (SalePayment.objects.filter(sale=i).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField()))['total']) + i.down_payment
                    pending_balance = i.total - total_paid
                    days_to_expiration = (i.date_joined.date() - datetime.now().date()).days + i.days_to_pay
                    result_data.append({
                        **i.to_json(),
                        'total_paid': format(total_paid, '.2f'),
                        'pending_balance': format(pending_balance, '.2f'),
                        'days_to_expiration': days_to_expiration
                    })

                # Respuesta para DataTables
                data = {
                    'draw': draw,
                    'recordsTotal': records_total,
                    'recordsFiltered': records_filtered,
                    'data': result_data
                }
                return JsonResponse(data, safe=False)
            elif action == 'search_details_prod':
                data = []
                sale_id = request.POST.get('id')
                if sale_id:
                    for i in SalePayment.objects.filter(sale_id=sale_id):
                        data.append(i.to_json())
                return JsonResponse(data, safe=False)
            else:
                data = {'error': 'Acción no válida'}
                return JsonResponse(data, safe=False)
        except Exception as e:
            # Para searchdata, retornar formato DataTables
            if request.POST.get('action', '') == 'searchdata':
                data = {
                    'draw': int(request.POST.get('draw', 1)),
                    'recordsTotal': 0,
                    'recordsFiltered': 0,
                    'data': [],
                    'error': str(e)
                }
            else:
                data = {'error': str(e)}
            return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Cuentas por Cobrar'
        context['create_url'] = reverse_lazy('artemisa:purchase_create')
        context['list_url'] = reverse_lazy('hermes:salepayment_list')
        context['entity'] = 'Cuentas por Cobrar'
        return context

class SalePaymentCreateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, CreateView):
    model = SalePayment
    form_class = SalePaymentForm
    template_name = 'salepayment/create.html'
    success_url = reverse_lazy('hermes:salepayment_list')
    permission_required = 'add_salepayment'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        # Obtener el objeto Purchase usando el pk de la URL
        self.sale = get_object_or_404(Sale, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                form = self.get_form()
                form.instance.created_by = request.user
                form.instance.sale = self.sale  # Asignar la compra al formulario
                data = form.save()
            else:
                data['error'] = 'No ha ingresado a ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)

    def get_form(self, form_class=None):
        # Inicializar el formulario con la compra obtenida
        form = super().get_form(form_class)
        form.instance.sale = self.sale
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creación un Pago de Compra'
        context['entity'] = 'Abono de créditos con proveedores'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['sale'] = self.sale  # Pasar la compra al contexto
        context['pending_balance'] = self.sale.total - (SalePayment.objects.filter(sale=self.sale).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField()))['total']) - self.sale.down_payment
        context['comp'] = {
            'name': 'AGROINSUMOS MERKO SUR',
            'nit': '1085928681-1',
            'address': 'La Victoria',
            'city': 'Ipiales',
            'vendor': 'Alexander Palles',
            'tel': '3156692427',
        }
        return context
    
class SalePaymentDetailView(LoginRequiredMixin, ValidatePermissionRequiredMixin, DetailView):
    model = Sale
    template_name = 'salepayment/detail.html'
    permission_required = 'view_sale'
    url_redirect = reverse_lazy('hermes:salepayment_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalles de la Compra'
        context['entity'] = 'Creditos'
        context['purchase_payment'] = SalePayment.objects.filter(sale=self.object)
        context['purchase_payments'] = (SalePayment.objects.filter(sale=self.object).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField()))['total']) + self.object.down_payment
        context['pending_balance'] = self.object.total - context['purchase_payments']
        context['list_url'] = self.url_redirect
        context['date'] = datetime.now()
        context['comp'] = {
            'name': 'AGROINSUMOS MERKO SUR',
            'nit': '1085928681-1',
            'address': 'La Victoria',
            'city': 'Ipiales',
            'vendor': 'Alexander Palles',
            'tel': '3156692427',
        }
        return context

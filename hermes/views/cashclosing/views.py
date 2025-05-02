from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView
from hermes.forms import CashClosingForm
from hades.mixins import ValidatePermissionRequiredMixin
from hermes.models import CashClosing, SalePayment
from ilitia.models import Sale
from datetime import datetime
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce


class CashClosingListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = CashClosing
    template_name = 'cashclosing/list.html'
    permission_required = 'view_clashclosing'

    def post(self, request, *args, **kwargs):
        data = []
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = []
                for i in CashClosing.objects.all():
                    user = i.created_by.to_json()
                    data.append(i.to_json())
                    data[-1]['created_by'] = user
                    print(data)
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Cierre de Caja'
        context['create_url'] = reverse_lazy('hermes:cashclosing_create')
        context['list_url'] = reverse_lazy('hermes:cashclosing_list')
        context['entity'] = 'Cierre de Caja'
        return context

class CashClosingCreateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, CreateView):
    model = CashClosing
    form_class = CashClosingForm
    template_name = 'cashclosing/create copy.html'
    success_url = reverse_lazy('hermes:salepayment_list')
    permission_required = 'add_cashclosing'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        # Obtener el último cierre de caja del usuario
        self.last_cash_closing = CashClosing.objects.filter(created_by=request.user).first()
        print(self.last_cash_closing.date)

        if self.last_cash_closing:
            self.sales = Sale.objects.filter(created_by=request.user, date_joined__gt=self.last_cash_closing.date)
        else:
            self.sales = Sale.objects.filter(created_by=request.user)

        if self.last_cash_closing:
            self.salespayments = SalePayment.objects.filter(sale__created_by=request.user, payment_date__gte=self.last_cash_closing.date)
        else:
            self.salespayments = SalePayment.objects.filter(sale__created_by=request.user)
        
        # Calcular los totales
        self.total_sales_cash = self.sales.filter(type_payment='CASH').aggregate(total=Coalesce(Sum('total'), Decimal('0.00'), output_field=DecimalField()))['total']
        self.total_sales_credit = self.sales.filter(type_payment='CREDIT').aggregate(total=Coalesce(Sum('down_payment'), Decimal('0.00'), output_field=DecimalField()))['total']
        self.total_salespayments = self.salespayments.aggregate(total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField()))['total']
        self.total = self.total_sales_cash + self.total_sales_credit + self.total_salespayments
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                form = self.get_form()
                form.instance.last_login = self.last_cash_closing.date if self.last_cash_closing else datetime.now()
                form.instance.created_by = self.request.user
                form.instance.total_cash = self.total
                data = form.save()
                data['success'] = 'Cierre de caja creado correctamente'
            else:
                data['error'] = 'No ha ingresado a ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creación un Pago de Compra'
        context['entity'] = 'Abono de créditos con proveedores'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['date'] = datetime.now()
        context['sales'] = self.sales  # Pasar la compras al contexto
        context['salespayments'] = self.salespayments  # Pasar los pagos al contexto
        context['total_sales_cash'] = self.total_sales_cash
        context['total_sales_credit'] = self.total_sales_credit
        context['total_salespayments'] = self.total_salespayments
        context['total'] = self.total
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
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from artemisa.models import Purchase, Product
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from datetime import timedelta
from collections import defaultdict
from ilitia.models import Sale, Client
from hermes.models import SalePayment
from decimal import Decimal
from django.utils import timezone
from hades.models import User
from datetime import datetime
from django.utils.timezone import localtime
from core.models import Currency
from django.shortcuts import redirect


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name='dashboard.html'

    def get(self, request, *args, **kwargs):
        request.user.get_group_sessions()
        return super().get(request, *args, **kwargs)
    
    def sales_last_month(self):
        data = 0
        today = timezone.now()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        data  = Sale.objects.filter(date_joined__range=(first_day_last_month, last_day_last_month)).aggregate(total=Coalesce(Sum('total'), 0, output_field=DecimalField()))['total']
        return data

    def sales_by_week(self):
        data = []
        try:
            # Obtener fecha local con zona horaria
            hoy = timezone.localdate()

            # Calcular inicio y fin de semana
            inicio_semana = hoy - timedelta(days=hoy.weekday())  # Lunes
            fin_semana = inicio_semana + timedelta(days=6)       # Domingo

            # Inicializar estructura: lista de 7 días por tipo de pago
            tipo_pago_totales = defaultdict(lambda: [0] * 7)

            # Filtrar ventas entre el rango de fechas
            ventas = Sale.objects.filter(date_joined__date__range=[inicio_semana, fin_semana])

            for venta in ventas:
                local_fecha = localtime(venta.date_joined)
                dia_semana = local_fecha.weekday()  # 0 = lunes, 6 = domingo

                if venta.type_payment == 'CASH':
                    tipo_pago_totales["CASH"][dia_semana] += float(venta.total)
                else:
                    tipo_pago_totales["CASH"][dia_semana] += float(venta.down_payment)

                if venta.type_payment == 'CREDIT':
                    tipo_pago_totales["CREDIT"][dia_semana] += float(venta.total - venta.down_payment)


            # Formatear datos para frontend (gráfico o tabla)
            data = [{'name': tipo, 'data': dias} for tipo, dias in tipo_pago_totales.items()]
            return data
        
        except Exception as e:
            return data

        
    def salepayment(self):
        total_pending_balance = 0
        expired_balance = 0
        try:
            for i in Sale.objects.filter(type_payment='CREDIT'):
                total_paid = (SalePayment.objects.filter(sale=i).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField()))['total']) + i.down_payment
                pending_balance = i.total - total_paid
                days_to_expiration = (i.date_joined.date() - datetime.now().date()).days + i.days_to_pay
                if pending_balance > 0:
                    total_pending_balance += pending_balance
                    if days_to_expiration < 0:
                        expired_balance += pending_balance
        except Exception as e:
            print(f"Error al obtener cuentas por pagar: {e}")
        return total_pending_balance, expired_balance
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales_goal = 60000000  # Meta de ventas
        context['num_sales'] = Sale.objects.filter(date_joined__year=timezone.now().year).count()
        context['num_cli'] = Client.objects.filter().count()
        context['num_prod'] = Product.objects.filter().count()
        context['sales'] = self.sales_by_week()  # Agregar datos de ventas al contexto
        context['sales_last_month'] = self.sales_last_month()  # Agregar ventas del mes pasado al contexto
        context['sales_month'] = Sale.objects.filter(date_joined__month=timezone.now().month).aggregate(total=Coalesce(Sum('total'), 0, output_field=DecimalField()))['total']
        context['sales_targets'] = sales_goal
        context['users'] = User.objects.filter(is_active=True)
        context['pending_balance'] = self.salepayment()[0]
        context['expired_balance'] = self.salepayment()[1]
        return context


class ArtemisaView(LoginRequiredMixin, TemplateView):
    template_name = 'artemisa/index.html'

    def get(self, request, *args, **kwargs):
        # Obtener las sesiones del grupo del usuario
        request.user.get_group_sessions()
        return super().get(request, *args, **kwargs)
    
    def purchase_provider(self):
        data = []
        try:
            year = timezone.now().year
            provider_totals = defaultdict(lambda: [0] * 12)
            purchases = Purchase.objects.filter(date__year=year).select_related('provider')

            for purchase in purchases:
                month = purchase.date.month - 1
                provider_totals[purchase.provider.names][month] += float(purchase.total)
            
            data = [{'name': provider, 'data': total} for provider, total in provider_totals.items()]
            print(f"Datos de compras mensuales por proveedor: {data}")
            return data
        except Exception as e:
            print(f"Error al obtener las compras mensuales por proveedor: {e}")
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chart_data'] = self.purchase_provider()  # Agregar datos de proveedores al contexto
        context['total_purchases'] = Purchase.objects.filter(date__year=timezone.now().year).aggregate(total=Coalesce(Sum('total'), 0, output_field=DecimalField()))['total']
        return context

def set_currency(request, code):
    currency = Currency.objects.filter(code=code).first()
    if currency:
        request.session['currency'] = currency.code
    return redirect(request.META.get('HTTP_REFERER', '/'))

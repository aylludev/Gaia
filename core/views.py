from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from artemisa.models import Purchase, Product
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from datetime import timedelta
from collections import defaultdict
from ilitia.models import Sale, Client
from django.utils import timezone

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
            # Lunes de esta semana
            hoy = timezone.now().date()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=7)

            tipo_pago_totales = defaultdict(lambda: [0] * 7)
            ventas = Sale.objects.filter(date_joined__range=[inicio_semana, fin_semana])

            for venta in ventas:
                dia_semana = venta.date_joined.weekday()  # 0 = lunes
                if venta.type_payment == 'CASH':
                    tipo_pago_totales["CASH"][dia_semana] += float(venta.total)
                else:
                    tipo_pago_totales["CASH"][dia_semana] += float(venta.down_payment)
                
                if venta.type_payment == 'CREDIT':
                    tipo_pago_totales["CREDIT"][dia_semana] += float(venta.total - venta.down_payment)

            data = [{'name': tipo, 'data': dias} for tipo, dias in tipo_pago_totales.items()]
            return data
        except Exception as e:
            print(f"Error al obtener ventas semanales: {e}")
            return data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['num_sales'] = Sale.objects.filter(date_joined__year=timezone.now().year).count()
        context['num_cli'] = Client.objects.filter().count()
        context['num_prod'] = Product.objects.filter().count()
        context['sales'] = self.sales_by_week()  # Agregar datos de ventas al contexto
        context['sales_last_month'] = self.sales_last_month()  # Agregar ventas del mes pasado al contexto
        context['sales_month'] = Sale.objects.filter(date_joined__month=timezone.now().month).aggregate(total=Coalesce(Sum('total'), 0, output_field=DecimalField()))['total']
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

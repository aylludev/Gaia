from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from artemisa.models import Purchase, PurchaseDetail
from datetime import datetime
from django.http import JsonResponse
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce, TruncMonth
from calendar import monthrange
from datetime import date, timedelta
from collections import defaultdict
import calendar


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name='dashboard.html'

    def get(self, request, *args, **kwargs):
        request.user.get_group_sessions()
        return super().get(request, *args, **kwargs)

class ArtemisaView(LoginRequiredMixin, TemplateView):
    template_name = 'artemisa/index.html'

    def get(self, request, *args, **kwargs):
        # Obtener las sesiones del grupo del usuario
        request.user.get_group_sessions()
        return super().get(request, *args, **kwargs)
    
    def purchase_provider(self):
        data = []
        try:
            year = datetime.now().year
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
        context['total_purchases'] = Purchase.objects.filter(date__year=datetime.now().year).aggregate(total=Coalesce(Sum('total'), 0, output_field=DecimalField()))['total']
        return context

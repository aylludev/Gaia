from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from artemisa.models import Purchase, PurchaseDetail
from datetime import datetime
from django.http import JsonResponse
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce, TruncMonth
from calendar import monthrange
from datetime import date, timedelta


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
            # Obtener el rango de fechas de las compras
            first_purchase = Purchase.objects.order_by('date').first()
            last_purchase = Purchase.objects.order_by('-date').first()

            if not first_purchase or not last_purchase:
                return data  # Si no hay compras, devolver lista vacía

            start_date = first_purchase.date.replace(day=1)  # Primer día del mes de la primera compra
            end_date = last_purchase.date.replace(day=1)  # Primer día del mes de la última compra

            # Generar todos los meses dentro del rango
            all_months = []
            current_date = start_date
            while current_date <= end_date:
                all_months.append(current_date.strftime('%B %Y'))  # Formatear el mes como texto
                current_date += timedelta(days=monthrange(current_date.year, current_date.month)[1])

            # Obtener los montos comprados agrupados por mes y proveedor
            monthly_purchases = (
                Purchase.objects.annotate(month=TruncMonth('date'))  # Truncar la fecha al mes
                .values('month', 'provider__names')  # Agrupar por mes y proveedor
                .annotate(total=Coalesce(Sum('total'), 0, output_field=DecimalField()))  # Sumar el total de compras
                .order_by('provider__names', 'month')  # Ordenar por proveedor y mes
            )

            # Crear un diccionario para mapear los datos por proveedor
            providers_dict = {}
            for purchase in monthly_purchases:
                provider_name = purchase['provider__names']
                month = purchase['month'].strftime('%B %Y')
                total = float(purchase['total'])

                if provider_name not in providers_dict:
                    providers_dict[provider_name] = {m: 0 for m in all_months}  # Inicializar con 0 para todos los meses

                providers_dict[provider_name][month] = total  # Asignar el total al mes correspondiente

            # Formatear los datos en el formato solicitado
            for provider_name, monthly_data in providers_dict.items():
                data.append({
                    'name': provider_name,
                    'data': [monthly_data[month] for month in all_months],  # Ordenar los datos por mes
                })
            print(data)  # Imprimir los datos para depuración

        except Exception as e:
            print(f"Error al obtener las compras mensuales por proveedor: {e}")
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chart_data'] = self.purchase_provider()  # Agregar datos de proveedores al contexto
        return context

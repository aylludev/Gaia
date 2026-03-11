from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from artemisa.models import Purchase, Product, Category
from django.db.models import Sum, DecimalField, Count
from django.db.models.functions import Coalesce
from datetime import timedelta, datetime, date
import json
from collections import defaultdict
from ilitia.models import Sale, Client, DetSale
from hermes.models import SalePayment
from decimal import Decimal
from django.utils import timezone
from hades.models import User
from django.utils.timezone import localtime
from core.models import Currency
from django.shortcuts import redirect

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_active_group_name(self):
        """Obtiene el nombre del grupo activo de forma segura"""
        active_group = self.request.session.get('group')
        
        # Manejar diferentes formatos de grupo en sesión
        if isinstance(active_group, list) and active_group:
            return active_group[0].get('name', '')
        elif isinstance(active_group, dict):
            return active_group.get('name', '')
        elif isinstance(active_group, str):
            return active_group
        
        # Fallback: primer grupo del usuario (solo si el signal falló)
        if self.request.user.groups.exists():
            group = self.request.user.groups.first()
            self.request.session['group'] = [{'id': group.id, 'name': group.name}]
            return group.name
        
        return ''

    def get_sales_queryset(self):
        """Retorna el queryset de ventas filtrado por grupo activo"""
        active_group = self.get_active_group_name()
        if active_group == 'Admin GAIA':
            return Sale.objects.all()
        else:
            return Sale.objects.filter(created_by=self.request.user)

    def sales_last_month(self):
        """Ventas del mes anterior - Versión optimizada"""
        try:
            today = timezone.now()
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            
            queryset = self.get_sales_queryset().filter(
                date_joined__range=(first_day_last_month, last_day_last_month)
            )
            
            result = queryset.aggregate(
                total=Coalesce(Sum('total'), 0, output_field=DecimalField())
            )['total']
            
            return float(result) if result else 0.0

        except Exception as e:
            return 0.0

    def sales_by_week(self):
        """Ventas de la semana actual - Versión optimizada"""
        data = []

        try:
            hoy = timezone.localdate()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            
            ventas = self.get_sales_queryset().filter(
                date_joined__date__range=[inicio_semana, fin_semana]
            ).select_related('created_by')

            tipo_pago_totales = defaultdict(lambda: [0] * 7)

            for venta in ventas:
                local_fecha = localtime(venta.date_joined)
                dia_semana = local_fecha.weekday()

                if venta.type_payment == 'CASH':
                    tipo_pago_totales["CASH"][dia_semana] += float(venta.total)
                else:
                    tipo_pago_totales["CASH"][dia_semana] += float(venta.down_payment)
                
                if venta.type_payment == 'CREDIT':
                    tipo_pago_totales["CREDIT"][dia_semana] += float(venta.total - venta.down_payment)

            data = [{'name': tipo, 'data': dias} for tipo, dias in tipo_pago_totales.items()]
            return data

        except Exception as e:
            return [data]

    def salepayment(self):
        total_pending_balance = 0
        expired_balance = 0
        try:
            for i in self.get_sales_queryset().filter(type_payment='CREDIT'):
                total_paid = (SalePayment.objects.filter(sale=i).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField()))['total']) + i.down_payment
                pending_balance = i.total - total_paid
                days_to_expiration = (i.date_joined.date() - datetime.now().date()).days + i.days_to_pay
                if pending_balance > 0:
                    total_pending_balance += pending_balance
                    if days_to_expiration < 0:
                        expired_balance += pending_balance
        except Exception as e:
            pass
        return total_pending_balance, expired_balance

    def convert_to_liters(self, quantity, unit):
        """Convierte una cantidad a litros según la unidad de medida"""
        quantity = float(quantity)

        # Conversiones a litros
        conversions = {
            'Lt': 1,           # Litro
            'mL': 0.001,       # Mililitro
            'cc': 0.001,       # Centímetro cúbico (igual a mL)
            'Gl': 4,           # Galón (4 litros)
        }

        if unit in conversions:
            return quantity * conversions[unit]

        # Si no es una unidad de volumen, retornar 0
        return 0

    def foliar_products_sales(self):
        """Obtiene productos foliares (código FA) y sus litros totales vendidos del mes actual"""
        import json
        from django.db.models import F
        data = {'products': [], 'sales': [], 'products_json': '[]', 'sales_json': '[]', 'items': []}
        try:
            # Obtener primer y último día del mes actual
            today = timezone.now()
            first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Obtener detalles de venta de productos con código que empiece con FA del mes actual
            # Filtrar por usuario logueado o mostrar todo si es Admin GAIA
            active_group = self.get_active_group_name()
            if active_group == 'Admin GAIA':
                det_sales = DetSale.objects.filter(
                    prod__code__startswith='FA',
                    sale__date_joined__gte=first_day_of_month
                ).select_related('prod', 'prod__unit', 'sale')
            else:
                det_sales = DetSale.objects.filter(
                    prod__code__startswith='FA',
                    sale__date_joined__gte=first_day_of_month,
                    sale__created_by=self.request.user
                ).select_related('prod', 'prod__unit', 'sale')

            # Agrupar por nombre base del producto y sumar litros
            # El nombre base se obtiene quitando la presentación (lo que está entre paréntesis al final)
            product_liters = defaultdict(float)

            for det in det_sales:
                # Obtener nombre base (sin la presentación)
                name = det.prod.name
                # Si el nombre contiene paréntesis, extraer solo la parte antes
                if '(' in name:
                    base_name = name.split('(')[0].strip()
                else:
                    base_name = name

                # Convertir a litros según la unidad de medida
                liters_per_unit = self.convert_to_liters(
                    det.prod.unit.quantity,
                    det.prod.unit.unit
                )

                # Calcular litros totales: cantidad vendida × litros por unidad
                total_liters = float(det.cant) * liters_per_unit
                product_liters[base_name] += total_liters

            # Ordenar por litros vendidos (descendente)
            sorted_products = sorted(product_liters.items(), key=lambda x: x[1], reverse=True)

            # Preparar datos para el gráfico
            products_list = []
            sales_list = []
            items_list = []
            total_liters_sold = 0

            for product_name, liters in sorted_products:
                products_list.append(product_name)
                sales_list.append(round(liters, 2))
                items_list.append({
                    'name': product_name,
                    'sales': f"{round(liters, 2)} L"
                })
                total_liters_sold += liters

            # Agregar total al final de la lista
            items_list.append({
                'name': 'TOTAL',
                'sales': f"{round(total_liters_sold, 2)} L",
                'is_total': True
            })

            data['products'] = products_list
            data['sales'] = sales_list
            data['products_json'] = json.dumps(products_list)
            data['sales_json'] = json.dumps(sales_list)
            data['items'] = items_list
            data['total_liters'] = round(total_liters_sold, 2)

        except Exception as e:
            pass

        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'sales_last_month': self.sales_last_month(),
            'sales': self.sales_by_week(),
            'sales_targets' : 60000000,
            'active_group': self.get_active_group_name(),
            'today': timezone.localdate(),
            'num_sales' : self.get_sales_queryset().count(),
            'num_cli' : Client.objects.count(),
            'num_prod' : Product.objects.count(),
            'pending_balance': self.salepayment()[0],
            'expired_balance' : self.salepayment()[1],
            'users': User.objects.filter(is_active=True),
            'foliar_products': self.foliar_products_sales(),
        })
        return context


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard para administradores con estadísticas globales"""
    template_name = 'admin_dashboard.html'

    def sales_last_month(self):
        """Ventas del mes anterior - Total global"""
        try:
            today = timezone.now()
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)

            result = Sale.objects.filter(
                date_joined__range=(first_day_last_month, last_day_last_month)
            ).aggregate(
                total=Coalesce(Sum('total'), 0, output_field=DecimalField())
            )['total']

            return float(result) if result else 0.0
        except Exception as e:
            return 0.0

    def sales_month(self):
        """Ventas del mes actual - Total global"""
        try:
            today = timezone.now()
            first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            result = Sale.objects.filter(
                date_joined__gte=first_day_of_month
            ).aggregate(
                total=Coalesce(Sum('total'), 0, output_field=DecimalField())
            )['total']

            return float(result) if result else 0.0
        except Exception as e:
            return 0.0

    def sales_by_week(self):
        """Ventas de la semana actual - Total global"""
        data = []
        try:
            hoy = timezone.localdate()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)

            ventas = Sale.objects.filter(
                date_joined__date__range=[inicio_semana, fin_semana]
            )

            tipo_pago_totales = defaultdict(lambda: [0] * 7)

            for venta in ventas:
                local_fecha = localtime(venta.date_joined)
                dia_semana = local_fecha.weekday()

                if venta.type_payment == 'CASH':
                    tipo_pago_totales["CASH"][dia_semana] += float(venta.total)
                else:
                    tipo_pago_totales["CASH"][dia_semana] += float(venta.down_payment)

                if venta.type_payment == 'CREDIT':
                    tipo_pago_totales["CREDIT"][dia_semana] += float(venta.total - venta.down_payment)

            data = [{'name': tipo, 'data': dias} for tipo, dias in tipo_pago_totales.items()]
            return data
        except Exception as e:
            return [data]

    def salepayment(self):
        """Cuentas por cobrar - Total global"""
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
            pass
        return total_pending_balance, expired_balance

    def convert_to_liters(self, quantity, unit):
        """Convierte una cantidad a litros según la unidad de medida"""
        quantity = float(quantity)
        conversions = {
            'Lt': 1,
            'mL': 0.001,
            'cc': 0.001,
            'Gl': 4,
        }
        if unit in conversions:
            return quantity * conversions[unit]
        return 0

    def foliar_products_sales(self):
        """Productos foliares - Total global del mes actual"""
        import json
        data = {'products': [], 'sales': [], 'products_json': '[]', 'sales_json': '[]', 'items': []}
        try:
            today = timezone.now()
            first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Todas las ventas del mes (sin filtrar por usuario)
            det_sales = DetSale.objects.filter(
                prod__code__startswith='FA',
                sale__date_joined__gte=first_day_of_month
            ).select_related('prod', 'prod__unit', 'sale')

            product_liters = defaultdict(float)

            for det in det_sales:
                name = det.prod.name
                if '(' in name:
                    base_name = name.split('(')[0].strip()
                else:
                    base_name = name

                liters_per_unit = self.convert_to_liters(
                    det.prod.unit.quantity,
                    det.prod.unit.unit
                )
                total_liters = float(det.cant) * liters_per_unit
                product_liters[base_name] += total_liters

            sorted_products = sorted(product_liters.items(), key=lambda x: x[1], reverse=True)

            products_list = []
            sales_list = []
            items_list = []
            total_liters_sold = 0

            for product_name, liters in sorted_products:
                products_list.append(product_name)
                sales_list.append(round(liters, 2))
                items_list.append({
                    'name': product_name,
                    'sales': f"{round(liters, 2)} L"
                })
                total_liters_sold += liters

            items_list.append({
                'name': 'TOTAL',
                'sales': f"{round(total_liters_sold, 2)} L",
                'is_total': True
            })

            data['products'] = products_list
            data['sales'] = sales_list
            data['products_json'] = json.dumps(products_list)
            data['sales_json'] = json.dumps(sales_list)
            data['items'] = items_list
            data['total_liters'] = round(total_liters_sold, 2)

        except Exception as e:
            pass

        return data

    def sales_by_user(self):
        """Ventas por vendedor del mes actual"""
        data = []
        try:
            today = timezone.now()
            first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            sales = Sale.objects.filter(
                date_joined__gte=first_day_of_month
            ).values('created_by__first_name', 'created_by__last_name').annotate(
                total=Sum('total'),
                count=Count('id')
            ).order_by('-total')

            for sale in sales:
                name = f"{sale['created_by__first_name']} {sale['created_by__last_name']}"
                data.append({
                    'name': name.strip() or 'Sin nombre',
                    'total': float(sale['total']),
                    'count': sale['count']
                })
        except Exception as e:
            pass
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'sales_last_month': self.sales_last_month(),
            'sales_month': self.sales_month(),
            'sales': self.sales_by_week(),
            'sales_targets': 60000000,
            'today': timezone.localdate(),
            'num_sales': Sale.objects.count(),
            'num_cli': Client.objects.count(),
            'num_prod': Product.objects.count(),
            'pending_balance': self.salepayment()[0],
            'expired_balance': self.salepayment()[1],
            'users': User.objects.filter(is_active=True),
            'foliar_products': self.foliar_products_sales(),
            'sales_by_user': self.sales_by_user(),
            'entity': 'Dashboard Administrativo',
        })
        return context


class SalesReportBySellerView(LoginRequiredMixin, TemplateView):
    """Informe de ventas por mes de cada usuario vendedor"""
    template_name = 'sales_report_by_seller.html'

    def sales_by_seller_month(self):
        """Ventas por vendedor agrupadas por mes — últimos 12 meses"""
        data = []
        try:
            months = self.get_last_12_months()
            month_index = {(y, m): i for i, (y, m) in enumerate(months)}
            start_date = date(months[0][0], months[0][1], 1)

            seller_totals = defaultdict(lambda: [0] * 12)
            total_monthly = [0] * 12

            sales = Sale.objects.filter(
                date_joined__date__gte=start_date
            ).select_related('created_by')

            for sale in sales:
                key = (sale.date_joined.year, sale.date_joined.month)
                if key not in month_index:
                    continue
                idx = month_index[key]
                seller_name = f"{sale.created_by.first_name} {sale.created_by.last_name}".strip()
                if not seller_name:
                    seller_name = sale.created_by.username
                seller_totals[seller_name][idx] += float(sale.total)
                total_monthly[idx] += float(sale.total)

            data = [{'name': seller, 'data': totals} for seller, totals in seller_totals.items()]
            data.append({'name': 'TOTAL', 'data': total_monthly})

        except Exception as e:
            print(f"Error in sales_by_seller_month: {e}")

        return json.dumps(data)

    def get_last_12_months(self):
        """Returns list of (year, month) tuples for the last 12 months, oldest first"""
        today = timezone.localdate()
        months = []
        year, month = today.year, today.month
        for _ in range(12):
            months.insert(0, (year, month))
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        return months

    def get_month_labels(self, months):
        """Returns short labels like 'Mar 2025' for the given (year, month) tuples"""
        names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        return [f"{names[m-1]} {y}" for y, m in months]

    def convert_to_liters(self, quantity, unit):
        """Convierte una cantidad a litros según la unidad de medida"""
        quantity = float(quantity)
        conversions = {
            'Lt': 1,
            'mL': 0.001,
            'cc': 0.001,
            'Gl': 4,
        }
        if unit in conversions:
            return quantity * conversions[unit]
        return 0

    def foliar_products_by_seller(self):
        """Litros de productos FA por vendedor, discriminado por mes — últimos 12 meses"""
        from decimal import Decimal
        data = []
        try:
            months = self.get_last_12_months()
            month_index = {(y, m): i for i, (y, m) in enumerate(months)}
            start_date = date(months[0][0], months[0][1], 1)

            det_sales = DetSale.objects.filter(
                prod__code__startswith='FA',
                sale__date_joined__date__gte=start_date
            ).select_related('prod', 'prod__unit', 'sale', 'sale__created_by')

            # Agrupar por vendedor, mes y tipo de pago
            # cash_liters[vendedor][mes] = litros de contado
            # credit_paid_liters[vendedor][mes] = litros de crédito pagados
            # credit_pending_liters[vendedor][mes] = litros de crédito pendientes

            seller_cash_liters = defaultdict(lambda: [0] * 12)
            seller_credit_paid_liters = defaultdict(lambda: [0] * 12)
            seller_credit_pending_liters = defaultdict(lambda: [0] * 12)

            total_cash = [0] * 12
            total_credit_paid = [0] * 12
            total_credit_pending = [0] * 12

            for det in det_sales:
                key = (det.sale.date_joined.year, det.sale.date_joined.month)
                if key not in month_index:
                    continue
                month = month_index[key]

                seller_name = f"{det.sale.created_by.first_name} {det.sale.created_by.last_name}".strip()
                if not seller_name:
                    seller_name = det.sale.created_by.username

                liters_per_unit = self.convert_to_liters(
                    det.prod.unit.quantity,
                    det.prod.unit.unit
                )

                total_liters = float(det.cant) * liters_per_unit

                if det.sale.type_payment == 'CASH':
                    seller_cash_liters[seller_name][month] += total_liters
                    total_cash[month] += total_liters
                else:
                    # Venta a crédito - calcular proporción pagada
                    # Total de la venta
                    sale_total = float(det.sale.total)

                    # Calcular total pagado (cuota inicial + pagos)
                    down_payment = float(det.sale.down_payment)
                    payments = SalePayment.objects.filter(sale=det.sale).aggregate(
                        total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
                    )['total']
                    total_paid = down_payment + float(payments)

                    # Calcular porcentaje pagado
                    if sale_total > 0:
                        percentage_paid = total_paid / sale_total
                    else:
                        percentage_paid = 0

                    # Distribuir litros según porcentaje pagado
                    liters_paid = total_liters * percentage_paid
                    liters_pending = total_liters * (1 - percentage_paid)

                    seller_credit_paid_liters[seller_name][month] += liters_paid
                    seller_credit_pending_liters[seller_name][month] += liters_pending
                    total_credit_paid[month] += liters_paid
                    total_credit_pending[month] += liters_pending

            # Convertir a formato para ApexCharts
            # Estrategia: Crear un objeto con la estructura correcta para barras apiladas agrupadas
            # Necesitamos que ApexCharts agrupe por vendedor, con cada segmento de la barra mostrando tipo de pago

            series_data = []
            grand_total_cash = 0
            grand_total_credit_paid = 0
            grand_total_credit_pending = 0

            # Obtener lista única de vendedores
            all_sellers = set()
            all_sellers.update(seller_cash_liters.keys())
            all_sellers.update(seller_credit_paid_liters.keys())
            all_sellers.update(seller_credit_pending_liters.keys())

            # Ordenar vendedores alfabéticamente
            sorted_sellers = sorted(all_sellers)

            # Agregar vendedor TOTAL
            sorted_sellers.append('TOTAL')

            # Crear 3 series (una por tipo de pago)
            # Cada serie tiene datos para todos los vendedores en cada mes

            # Para cada mes, crear un array con [vendedor1_cash, vendedor2_cash, ..., total_cash]
            cash_series = []
            credit_paid_series = []
            credit_pending_series = []

            for month_idx in range(12):
                month_cash = []
                month_credit_paid = []
                month_credit_pending = []

                for seller in sorted_sellers:
                    if seller == 'TOTAL':
                        month_cash.append(round(total_cash[month_idx], 2))
                        month_credit_paid.append(round(total_credit_paid[month_idx], 2))
                        month_credit_pending.append(round(total_credit_pending[month_idx], 2))
                    else:
                        month_cash.append(round(seller_cash_liters[seller][month_idx], 2))
                        month_credit_paid.append(round(seller_credit_paid_liters[seller][month_idx], 2))
                        month_credit_pending.append(round(seller_credit_pending_liters[seller][month_idx], 2))

                cash_series.append(month_cash)
                credit_paid_series.append(month_credit_paid)
                credit_pending_series.append(month_credit_pending)

            # Calcular totales
            for seller in sorted_sellers:
                if seller != 'TOTAL':
                    grand_total_cash += sum(seller_cash_liters[seller])
                    grand_total_credit_paid += sum(seller_credit_paid_liters[seller])
                    grand_total_credit_pending += sum(seller_credit_pending_liters[seller])

            # Estructura de datos para el frontend
            data = {
                'series_json': json.dumps({
                    'cash': cash_series,
                    'credit_paid': credit_paid_series,
                    'credit_pending': credit_pending_series
                }),
                'sellers_json': json.dumps(sorted_sellers),
                'total_liters': round(grand_total_cash + grand_total_credit_paid + grand_total_credit_pending, 2),
                'total_cash': round(grand_total_cash, 2),
                'total_credit_paid': round(grand_total_credit_paid, 2),
                'total_credit_pending': round(grand_total_credit_pending, 2)
            }

        except Exception as e:
            print(f"Error in foliar_products_by_seller: {e}")
            import traceback
            traceback.print_exc()
            data = {
                'series_json': json.dumps([]),
                'total_liters': 0,
                'total_cash': 0,
                'total_credit_paid': 0,
                'total_credit_pending': 0
            }

        return data

    def sales_by_payment_type(self):
        """Ventas totales por mes discriminadas por tipo de pago — últimos 12 meses"""
        from decimal import Decimal

        data = {
            'series_json': json.dumps([]),
            'total_cash': 0,
            'total_recovered': 0,
            'total_not_recovered': 0
        }

        try:
            months = self.get_last_12_months()
            month_index = {(y, m): i for i, (y, m) in enumerate(months)}
            start_date = date(months[0][0], months[0][1], 1)

            monthly_cash = [0] * 12
            monthly_recovered = [0] * 12
            monthly_not_recovered = [0] * 12

            sales = Sale.objects.filter(date_joined__date__gte=start_date)

            for sale in sales:
                key = (sale.date_joined.year, sale.date_joined.month)
                if key not in month_index:
                    continue
                idx = month_index[key]

                if sale.type_payment == 'CASH':
                    monthly_cash[idx] += float(sale.total)
                else:
                    down_payment = float(sale.down_payment)
                    payments = SalePayment.objects.filter(sale=sale).aggregate(
                        total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
                    )['total']
                    total_paid = down_payment + float(payments)
                    pending = float(sale.total) - total_paid
                    monthly_recovered[idx] += total_paid
                    monthly_not_recovered[idx] += pending

            series = [
                {'name': 'Contado', 'data': [round(v, 2) for v in monthly_cash]},
                {'name': 'Cartera Recuperada', 'data': [round(v, 2) for v in monthly_recovered]},
                {'name': 'Cartera No Recuperada', 'data': [round(v, 2) for v in monthly_not_recovered]},
            ]

            data = {
                'series_json': json.dumps(series),
                'total_cash': round(sum(monthly_cash), 2),
                'total_recovered': round(sum(monthly_recovered), 2),
                'total_not_recovered': round(sum(monthly_not_recovered), 2),
            }

        except Exception as e:
            print(f"Error in sales_by_payment_type: {e}")
            import traceback
            traceback.print_exc()

        return data

    def get_sellers_summary(self):
        """Resumen de ventas por vendedor — últimos 12 meses"""
        summary = []
        try:
            months = self.get_last_12_months()
            start_date = date(months[0][0], months[0][1], 1)

            sellers_data = Sale.objects.filter(
                date_joined__date__gte=start_date
            ).values(
                'created_by__first_name',
                'created_by__last_name',
                'created_by__username'
            ).annotate(
                total_sales=Sum('total'),
                count_sales=Count('id')
            ).order_by('-total_sales')

            for seller in sellers_data:
                name = f"{seller['created_by__first_name']} {seller['created_by__last_name']}".strip()
                if not name:
                    name = seller['created_by__username']

                summary.append({
                    'name': name,
                    'total': float(seller['total_sales']),
                    'count': seller['count_sales'],
                    'average': float(seller['total_sales']) / seller['count_sales'] if seller['count_sales'] > 0 else 0
                })

        except Exception as e:
            pass

        return summary

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        months = self.get_last_12_months()
        labels = self.get_month_labels(months)
        context.update({
            'title': 'Informe de Ventas por Vendedor',
            'entity': 'Informe de Ventas por Vendedor',
            'sales_data': self.sales_by_seller_month(),
            'sellers_summary': self.get_sellers_summary(),
            'foliar_data': self.foliar_products_by_seller(),
            'payment_type_data': self.sales_by_payment_type(),
            'month_labels': json.dumps(labels),
            'period_label': f"{labels[0]} - {labels[-1]}",
        })
        return context


class ArtemisaView(LoginRequiredMixin, TemplateView):
    template_name = 'artemisa/index.html'

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
            return data
        except Exception as e:
            pass
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

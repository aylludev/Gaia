from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from ilitia.models import Sale, Client
from hermes.models import SalePayment
from hades.mixins import ValidatePermissionRequiredMixin
from django.db.models import Sum, DecimalField, Q, F, Count
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import datetime


class RecoveredPortfolioListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = Sale
    template_name = 'credits/recovered.html'
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
                columns = ['id', 'invoice_number', 'cli__names', 'date_joined', 'total', 'id', 'id']
                order_column = columns[order_column_index] if order_column_index < len(columns) else 'date_joined'

                if order_dir == 'desc':
                    order_column = '-' + order_column

                # Queryset base - filtrar solo ventas a crédito con saldo pendiente <= 0
                queryset = Sale.objects.filter(type_payment='CREDIT').select_related('cli').annotate(
                    total_payments=Coalesce(Sum('payments__amount'), Decimal('0.00'), output_field=DecimalField()),
                    pending=F('total') - F('down_payment') - F('total_payments')
                ).filter(pending__lte=0)

                # Filtro de búsqueda
                if search_value:
                    queryset = queryset.filter(
                        Q(invoice_number__icontains=search_value) |
                        Q(cli__names__icontains=search_value) |
                        Q(cli__last_names__icontains=search_value)
                    )

                # Total de registros (también con saldo pendiente <= 0)
                base_queryset = Sale.objects.filter(type_payment='CREDIT').annotate(
                    total_payments=Coalesce(Sum('payments__amount'), Decimal('0.00'), output_field=DecimalField()),
                    pending=F('total') - F('down_payment') - F('total_payments')
                ).filter(pending__lte=0)
                records_total = base_queryset.count()
                records_filtered = queryset.count()

                # Aplicar ordenamiento
                queryset = queryset.order_by(order_column)

                # Aplicar paginación
                queryset = queryset[start:start + length]

                # Preparar datos
                result_data = []
                for i in queryset:
                    total_paid = (SalePayment.objects.filter(sale=i).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField()))['total']) + i.down_payment
                    result_data.append({
                        **i.to_json(),
                        'total_paid': format(total_paid, '.2f'),
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
        context['title'] = 'Cartera Recuperada'
        context['list_url'] = reverse_lazy('hermes:recovered_portfolio_list')
        context['entity'] = 'Cartera Recuperada'
        return context


class RecoveredPortfolioDetailView(LoginRequiredMixin, ValidatePermissionRequiredMixin, DetailView):
    model = Sale
    template_name = 'credits/detail.html'
    permission_required = 'view_salepayment'
    url_redirect = reverse_lazy('hermes:recovered_portfolio_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle de Crédito Recuperado'
        context['entity'] = 'Cartera Recuperada'
        context['sale_payment_list'] = SalePayment.objects.filter(sale=self.object)
        context['total_paid'] = (SalePayment.objects.filter(sale=self.object).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField()))['total']) + self.object.down_payment
        context['pending_balance'] = self.object.total - context['total_paid']
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


class ClientPortfolioListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = Client
    template_name = 'credits/client_portfolio.html'
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
                order_column_index = int(request.POST.get('order[0][column]', 0))
                order_dir = request.POST.get('order[0][dir]', 'asc')

                # Mapeo de columnas para ordenamiento
                columns = ['names', 'dni', 'cellphone', 'id', 'id', 'id']
                order_column = columns[order_column_index] if order_column_index < len(columns) else 'names'

                if order_dir == 'desc':
                    order_column = '-' + order_column

                # Obtener clientes con deuda pendiente
                # Primero obtenemos las ventas a crédito con saldo pendiente > 0
                clients_with_debt = Sale.objects.filter(
                    type_payment='CREDIT'
                ).annotate(
                    total_payments=Coalesce(Sum('payments__amount'), Decimal('0.00'), output_field=DecimalField()),
                    pending=F('total') - F('down_payment') - F('total_payments')
                ).filter(pending__gt=0).values_list('cli_id', flat=True).distinct()

                # Queryset de clientes con deuda
                queryset = Client.objects.filter(id__in=clients_with_debt)

                # Filtro de búsqueda
                if search_value:
                    queryset = queryset.filter(
                        Q(names__icontains=search_value) |
                        Q(last_names__icontains=search_value) |
                        Q(dni__icontains=search_value)
                    )

                # Total de registros
                records_total = Client.objects.filter(id__in=clients_with_debt).count()
                records_filtered = queryset.count()

                # Aplicar ordenamiento
                queryset = queryset.order_by(order_column)

                # Aplicar paginación
                queryset = queryset[start:start + length]

                # Preparar datos
                result_data = []
                for client in queryset:
                    # Calcular deuda total del cliente
                    sales_with_debt = Sale.objects.filter(
                        cli=client,
                        type_payment='CREDIT'
                    ).annotate(
                        total_payments=Coalesce(Sum('payments__amount'), Decimal('0.00'), output_field=DecimalField()),
                        pending=F('total') - F('down_payment') - F('total_payments')
                    ).filter(pending__gt=0)

                    total_debt = sum(sale.pending for sale in sales_with_debt)
                    total_sales = sales_with_debt.count()

                    result_data.append({
                        'id': client.id,
                        'full_name': f"{client.names} {client.last_names}",
                        'dni': client.dni or '-',
                        'cellphone': client.cellphone or '-',
                        'total_sales': total_sales,
                        'total_debt': format(total_debt, '.2f'),
                    })

                # Respuesta para DataTables
                data = {
                    'draw': draw,
                    'recordsTotal': records_total,
                    'recordsFiltered': records_filtered,
                    'data': result_data
                }
                return JsonResponse(data, safe=False)
            elif action == 'get_client_sales':
                # Obtener ventas pendientes de un cliente específico
                data = []
                client_id = request.POST.get('id')
                if client_id:
                    sales = Sale.objects.filter(
                        cli_id=client_id,
                        type_payment='CREDIT'
                    ).annotate(
                        total_payments=Coalesce(Sum('payments__amount'), Decimal('0.00'), output_field=DecimalField()),
                        pending=F('total') - F('down_payment') - F('total_payments')
                    ).filter(pending__gt=0)

                    for sale in sales:
                        data.append({
                            'id': sale.id,
                            'invoice_number': sale.invoice_number,
                            'date_joined': sale.date_joined.strftime('%Y-%m-%d'),
                            'total': format(sale.total, '.2f'),
                            'pending': format(sale.pending, '.2f'),
                        })
                return JsonResponse(data, safe=False)
            else:
                data = {'error': 'Acción no válida'}
                return JsonResponse(data, safe=False)
        except Exception as e:
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
        context['title'] = 'Cartera por Cliente'
        context['list_url'] = reverse_lazy('hermes:client_portfolio_list')
        context['entity'] = 'Cartera por Cliente'
        return context

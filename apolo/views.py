from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from ilitia.models import DetSale
from artemisa.models import Product
from apolo.forms import ReportForm

from django.db.models.functions import Coalesce
from django.db.models import Sum, DecimalField

from django.utils.timezone import make_aware
from datetime import datetime


class ReportSaleView(TemplateView):
    template_name = 'sale/report.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST.get('action', '')
            if action == 'search_product_qty':
                product_id = request.POST.get('product_id')
                start_date = request.POST.get('start_date', '')
                end_date = request.POST.get('end_date', '')

                if not product_id:
                    return JsonResponse({'error': 'ID de producto requerido'}, status=400)

                detsales = DetSale.objects.filter(prod_id=product_id)

                
                if start_date and end_date:
                    start = make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
                    end = make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
                    detsales = detsales.filter(sale__date_joined__range=[start, end])


                total_qty = detsales.aggregate(
                    total=Coalesce(Sum('cant'), 0)
                )['total']

                total_subtotal = detsales.aggregate(
                    total=Coalesce(Sum('subtotal'), 0, output_field=DecimalField())
                )['total']

                data = {
                    'product_id': product_id,
                    'total_quantity': total_qty,
                    'total_subtotal': format(total_subtotal, '.2f'),
                }
            else:
                data['error'] = 'Acción no válida'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Reporte de Ventas'
        context['entity'] = 'Reportes'
        context['list_url'] = reverse_lazy('apolo:sale_report')
        context['form'] = ReportForm()
        context['products'] = Product.objects.all()
        return context

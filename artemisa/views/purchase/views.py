import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Sum, F, DecimalField
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DeleteView, DetailView, UpdateView
from artemisa.forms import PurchaseForm, ProviderForm
from hades.mixins import ValidatePermissionRequiredMixin
from artemisa.models import Purchase, Product, PurchaseDetail, Provider
from datetime import datetime

class PurchaseListView(LoginRequiredMixin, ValidatePermissionRequiredMixin, ListView):
    model = Purchase
    template_name = 'purchase/list.html'
    permission_required = 'view_purchase'

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = []
                for i in Purchase.objects.filter():
                    data.append(i.to_json())
            elif action == 'search_details_prod':
                data = []
                for i in PurchaseDetail.objects.filter(purchase_id=request.POST['id']):
                    data.append(i.to_json())
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Compras'
        context['create_url'] = reverse_lazy('artemisa:purchase_create')
        context['list_url'] = reverse_lazy('artemisa:purchase_list')
        context['entity'] = 'Compras'
        return context


class PurchaseCreateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'purchase/create.html'
    success_url = reverse_lazy('artemisa:purchase_list')
    permission_required = 'add_purchase'
    url_redirect = success_url

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'search_products':
                data = []
                ids_exclude = json.loads(request.POST['ids'])
                term = request.POST['term'].strip()
                products = Product.objects.all()
                if len(term):
                    products = products.filter(name__icontains=term)
                for i in products.exclude(id__in=ids_exclude)[0:10]:
                    item = i.to_json()
                    item['value'] = i.name
                    # item['text'] = i.name
                    data.append(item)
            elif action == 'search_autocomplete':
                data = []
                ids_exclude = json.loads(request.POST['ids'])
                term = request.POST['term'].strip()
                data.append({'id': term, 'text': term})
                products = Product.objects.filter(name__icontains=term)
                for i in products.exclude(id__in=ids_exclude)[0:10]:
                    item = i.to_json()
                    item['text'] = i.name
                    data.append(item)
            elif action == 'add':
                with transaction.atomic():
                    buy = json.loads(request.POST['vents'])
                    print(buy)
                    purchase = Purchase()
                    purchase.date = buy['date']
                    purchase.invoice_number = buy['invoice_number']
                    purchase.provider_id = buy['provider']
                    purchase.subtotal = float(buy['subtotal'])
                    purchase.iva = float(buy['iva'])
                    purchase.discount_total = float(buy['discount_total'])
                    purchase.total = float(buy['total'])
                    purchase.type_payment = buy['type_payment']
                    purchase.days_to_pay = int(buy['days_to_pay'])
                    purchase.down_payment = float(buy['down_payment'])
                    purchase.observation = buy['observation']
                    purchase.created_by = request.user
                    purchase.save()
                    for i in buy['products']:
                        det = PurchaseDetail()
                        det.purchase_id = purchase.id
                        det.product_id = i['id']
                        det.cant = int(i['cant'])
                        det.price = float(i['purchase_price'])
                        det.discount = float(i['discount'])
                        det.subtotal = float(i['subtotal'])
                        det.save()
                        det.product.purchase_price = det.price
                        det.product.stock += det.cant
                        det.product.save()
                    data = {'id': purchase.id}
            elif action == 'search_clients':
                data = []
                term = request.POST['term']
                clients = Provider.objects.filter(Q(names__icontains=term) | Q(dni__icontains=term))[0:10]
                for i in clients:
                    item = i.to_json()
                    item['text'] = i.get_full_name()
                    data.append(item)
            elif action == 'create_client':
                with transaction.atomic():
                    frmClient = Provider(request.POST)
                    data = frmClient.save()
            else:
                data['error'] = 'No ha ingresado a ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creación de una Compra'
        context['entity'] = 'Compra'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['det'] = []
        context['frmClient'] = ProviderForm()
        return context

class PurchaseUpdateView(LoginRequiredMixin, ValidatePermissionRequiredMixin, UpdateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'purchase/create.html'
    success_url = reverse_lazy('artemisa:purchase_list')
    permission_required = 'add_purchase'
    url_redirect = success_url

    def get_form(self, form_class=None):
        instance = self.get_object()
        form = PurchaseForm(instance=instance)
        form.fields['provider'].queryset = Provider.objects.filter(id=instance.provider.id)
        return form

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'search_products':
                data = []
                ids_exclude = json.loads(request.POST['ids'])
                term = request.POST['term'].strip()
                products = Product.objects.all()
                if len(term):
                    products = products.filter(name__icontains=term)
                for i in products.exclude(id__in=ids_exclude)[0:10]:
                    item = i.to_json()
                    item['value'] = i.name
                    # item['text'] = i.name
                    data.append(item)
            elif action == 'search_autocomplete':
                data = []
                ids_exclude = json.loads(request.POST['ids'])
                term = request.POST['term'].strip()
                data.append({'id': term, 'text': term})
                products = Product.objects.filter(name__icontains=term)
                for i in products.exclude(id__in=ids_exclude)[0:10]:
                    item = i.to_json()
                    item['text'] = i.name
                    data.append(item)
            elif action == 'edit':
                with transaction.atomic():
                    buy = json.loads(request.POST['vents'])
                    purchase = Purchase()
                    purchase.date = buy['date']
                    purchase.invoice_number = buy['invoice_number']
                    purchase.provider_id = buy['provider']
                    purchase.subtotal = float(buy['subtotal'])
                    purchase.iva = float(buy['iva'])
                    purchase.discount_total = float(buy['discount_total'])
                    purchase.total = float(buy['total'])
                    purchase.type_payment = buy['type_payment']
                    purchase.days_to_pay = int(buy['days_to_pay'])
                    purchase.down_payment = float(buy['down_payment'])
                    purchase.observation = buy['observation']
                    purchase.updated_by = request.user
                    purchase.updated_at = datetime.now()
                    purchase.save()
                    purchase.purchasedetail_set.all().delete()
                    for i in buy['products']:
                        det = PurchaseDetail()
                        det.purchase_id = purchase.id
                        det.product_id = i['id']
                        det.cant = int(i['cant'])
                        det.price = float(i['purchase_price'])
                        det.discount = float(i['discount'])
                        det.subtotal = float(i['subtotal'])
                        det.save()
                        det.product.purchase_price = det.price
                        det.product.stock += det.cant
                        det.product.save()
                    data = {'id': purchase.id}
            elif action == 'search_clients':
                data = []
                term = request.POST['term']
                clients = Provider.objects.filter(Q(names__icontains=term) | Q(dni__icontains=term))[0:10]
                for i in clients:
                    item = i.to_json()
                    item['text'] = i.get_full_name()
                    data.append(item)
            elif action == 'create_client':
                with transaction.atomic():
                    frmClient = Provider(request.POST)
                    data = frmClient.save()
            else:
                data['error'] = 'No ha ingresado a ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)
    
    def get_details_product(self):
        data = []
        try:
            for i in PurchaseDetail.objects.filter(purchase_id=self.get_object().id):
                item = i.product.to_json()
                item['cant'] = i.cant
                item['discount'] = i.discount
                data.append(item)
                print(data)
        except:
            pass
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edición de una Compra'
        context['entity'] = 'Compra'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['det'] = json.dumps(self.get_details_product())
        context['frmClient'] = ProviderForm()
        return context

class PurchaseDeleteView(LoginRequiredMixin, ValidatePermissionRequiredMixin, DeleteView):
    model = Purchase
    template_name = 'delete.html'
    success_url = reverse_lazy('artemisa:purchase_list')
    permission_required = 'delete_purchase'
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            self.object.delete()
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminación de una Compra'
        context['entity'] = 'Compra'
        context['list_url'] = self.success_url
        return context

class PurchaseDetailView(LoginRequiredMixin, ValidatePermissionRequiredMixin, DetailView):
    model = Purchase
    template_name = 'purchase/detail.html'
    permission_required = 'view_purchase'
    url_redirect = reverse_lazy('artemisa:purchase_list')
    context_object_name = 'purchase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase = self.get_object()

        # Obtener los detalles de la compra
        details = purchase.purchasedetail_set.all().values(
            'product__name', 'price', 'cant', 'discount', 'subtotal'
        )

        # Calcular el total del descuento
        total_discount = purchase.purchasedetail_set.aggregate(
            total_discount=Sum(F('discount') * F('price') * F('cant') / 100, output_field=DecimalField())
        )['total_discount'] or 0  # Si no hay descuentos, devolver 0

        # Agregar datos al contexto
        context['purchase'] = purchase
        context['details'] = details
        context['total_discount'] = total_discount  # Enviar el total del descuento al template
        context['title'] = 'Detalle de la Compra'
        context['comp'] = {
            'name': 'AGROINSUMOS MERKO SUR',
            'nit': '1085928681-1',
            'address': 'La Victoria',
            'city': 'Ipiales',
            'vendor': 'Alexander Palles',
            'tel': '3156692427',
        }
        context['entity'] = 'Compra'
        context['list_url'] = self.url_redirect
        context['action'] = 'detail'
        return context
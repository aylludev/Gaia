from django.urls import path
from hermes.views.purchasepayment.views import *
from hermes.views.salepayment.views import *
from hermes.views.cashclosing.views import *
app_name = 'hermes'

urlpatterns = [
    # Cuentas por pagar
    path('purchasepayment/list/', PurchasePaymentListView.as_view(), name='purchasepayment_list'),
    path('purchase/<int:pk>/purchasepayment/create/', PurchasePaymentCreateView.as_view(), name='purchasepayment_create'),
    path('purchase/<int:pk>/purchasepayment/detail/', PurchasePaymentDetailView.as_view(), name='purchasepayment_detail'),
    # Cuentas por cobrar
    path('salepayment/list/', SalePaymentListView.as_view(), name='salepayment_list'),
    path('sale/<int:pk>/salepayment/create/', SalePaymentCreateView.as_view(), name='salepayment_create'),
    path('sale/<int:pk>/salepayment/detail/', SalePaymentDetailView.as_view(), name='salepayment_detail'),
    # Cierre de Caja
    path('cashclosing/list/', CashClosingListView.as_view(), name='cashclosing_list'),
    path('cashclosing/create/', CashClosingCreateView.as_view(), name='cashclosing_create'),
]
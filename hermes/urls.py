from django.urls import path
from hermes.views.purchasepayment.views import *

app_name = 'hermes'

urlpatterns = [
    # Cuentas por pagar
    path('purchasepayment/list/', PurchasePaymentListView.as_view(), name='purchasepayment_list'),
    path('purchase/<int:pk>/purchasepayment/create/', PurchasePaymentCreateView.as_view(), name='purchasepayment_create'),
    path('purchase/<int:pk>/purchasepayment/detail/', PurchasePaymentDetailView.as_view(), name='purchasepayment_detail'),
]
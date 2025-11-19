from django.urls import path
from hermes.views.purchasepayment.views import *
from hermes.views.salepayment.views import *
from hermes.views.cashclosing.views import *
from hermes.views.credits.views import RecoveredPortfolioListView, RecoveredPortfolioDetailView, ClientPortfolioListView
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
    path('salepayment/<int:pk>/update/', SalePaymentUpdateView.as_view(), name='salepayment_update'),
    path('salepayment/<int:pk>/delete/', SalePaymentDeleteView.as_view(), name='salepayment_delete'),
    # Cartera Recuperada
    path('credits/recovered/', RecoveredPortfolioListView.as_view(), name='recovered_portfolio_list'),
    path('credits/<int:pk>/detail/', RecoveredPortfolioDetailView.as_view(), name='recovered_portfolio_detail'),
    # Cartera por Cliente
    path('credits/client-portfolio/', ClientPortfolioListView.as_view(), name='client_portfolio_list'),
    # Cierre de Caja
    path('cashclosing/list/', CashClosingListView.as_view(), name='cashclosing_list'),
    path('cashclosing/create/', CashClosingCreateView.as_view(), name='cashclosing_create'),
]
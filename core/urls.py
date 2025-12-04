from django.urls import path
from core import views

app_name = 'core'

urlpatterns = [
    path('set-currency/<str:code>', views.set_currency, name='set_currency'),
    path('reports/sales-by-seller/', views.SalesReportBySellerView.as_view(), name='sales_report_by_seller'),
]


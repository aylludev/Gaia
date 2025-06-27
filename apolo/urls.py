from django.urls import path

from apolo.views import ReportSaleView

app_name = 'apolo'

urlpatterns = [
    # reports
    path('sale/', ReportSaleView.as_view(), name='sale_report'),
]
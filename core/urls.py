from django.urls import path
from core import views

app_name = 'core'

urlpatterns = [
    path('set-currency/<str:code>', views.set_currency, name='set_currency'),
]


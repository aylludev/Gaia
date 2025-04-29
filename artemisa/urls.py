from django.urls import path
from artemisa.views.category.views import *
from artemisa.views.product.views import *
from artemisa.views.unit.views import *
from artemisa.views.provider.views import *
from artemisa.views.purchase.views import *

app_name = 'artemisa'

urlpatterns = [
    # Category
    path('category/list/', CategoryListView.as_view(), name='category_list'),
    path('category/add/', CategoryCreateView.as_view(), name='category_create'),
    path('category/update/<int:pk>/', CategoryUpdateView.as_view(), name='category_update'),
    path('category/delete/<int:pk>/', CategoryDeleteView.as_view(), name='category_delete'),
    # Product
    path('product/list/', ProductListView.as_view(), name='product_list'),
    path('product/add/', ProductCreateView.as_view(), name='product_create'),
    path('product/update/<int:pk>/', ProductUpdateView.as_view(), name='product_update'),
    path('product/delete/<int:pk>/', ProductDeleteView.as_view(), name='product_delete'),
    path('product/pdf/', InventoryPdfView.as_view(), name='product_pdf'),
    # Unit Measure
    path('unit/list/', UnitListView.as_view(), name='unit_list'),
    path('unit/add/', UnitCreateView.as_view(), name='unit_create'),
    path('unit/update/<int:pk>/', UnitUpdateView.as_view(), name='unit_update'),
    path('unit/delete/<int:pk>/', UnitDeleteView.as_view(), name='unit_delete'),
    # Provider
    path('provider/list/', ProviderListView.as_view(), name='provider_list'),
    path('provider/add/', ProviderCreateView.as_view(), name='provider_create'),
    path('provider/update/<int:pk>/', ProviderUpdateView.as_view(), name='provider_update'),
    path('provider/delete/<int:pk>/', ProviderDeleteView.as_view(), name='provider_delete'),
    # Purchase
    path('purchase/list/', PurchaseListView.as_view(), name='purchase_list'),
    path('purchase/add/', PurchaseCreateView.as_view(), name='purchase_create'),
    path('purchase/update/<int:pk>/', PurchaseUpdateView.as_view(), name='purchase_update'),
    path('purchase/delete/<int:pk>/', PurchaseDeleteView.as_view(), name='purchase_delete'),
    path('purchase/detail/<int:pk>/', PurchaseDetailView.as_view(), name='purchase_detail'),
]
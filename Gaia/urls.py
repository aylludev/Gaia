from django.contrib import admin
from django.urls import path, include
from homepage.views import IndexView
from core.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='homepage'),
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('hades/', include('hades.urls', namespace='hades')),
]

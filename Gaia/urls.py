from django.contrib import admin
from django.urls import path, include
from homepage.views import IndexView
from core.views import DashboardView, ArtemisaView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='homepage'),
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('hades/', include('hades.urls', namespace='hades')),
    #Artemisa
    path('artemisa/', ArtemisaView.as_view(), name='artemisa'),
    path('artemisa/', include('artemisa.urls', namespace='artemisa')),
    path('ilitia/', include('ilitia.urls', namespace='ilitia')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

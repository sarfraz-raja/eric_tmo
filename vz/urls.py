from django.urls import path
from vz import views

app_name = 'vz'
urlpatterns = [
    path('script/', views.script_vz, name="script_vz"),
    path('sitelist/', views.sitelist_vz, name="sitelist_vz"),
    ]

# from django.conf import settings
# from django.conf.urls.static import static
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

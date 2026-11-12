from django.urls import path
from tmobile import views

app_name = 'tmobile'
urlpatterns = [
    path('script/', views.script_tmobile, name="script_tmobile"),
    path('sitelist/', views.sitelist_tmobile, name="sitelist_tmobile"),
    path('convert/', views.convert_tmobile, name="convert_tmobile"),
    path('convert/template/', views.convert_template_tmobile, name="convert_template_tmobile"),
    ]

# from django.conf import settings
# from django.conf.urls.static import static
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

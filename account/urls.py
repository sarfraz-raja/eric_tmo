from django.urls import path
from account import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('login/<token>', views.autologin, name='autologin'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dbupdate/', views.dbupdate, name='dbupdate'),
    path('dbupdatelist/', views.dbupdatelist, name='dbupdatelist'),
    path('Hellpassword',views.create_user,name='create_user'),
    path('users_with_groups',views.users_with_groups,name='users_with_groups'),
    path('edit_user', views.edit_user ,name="edit_user"),
    path('create_user', views.create_user ,name="create_user"),
    
    path('autodelete',views.autodelete,name='autodelete')
    # path("register/", views.register ,name="register"),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

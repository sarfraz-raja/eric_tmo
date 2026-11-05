from django.contrib import admin

from .models import Mme, Amf, SW, Client, VZJob

# Register your models here.
admin.site.register(Mme)
admin.site.register(Amf)
admin.site.register(SW)
admin.site.register(Client)
admin.site.register(VZJob)

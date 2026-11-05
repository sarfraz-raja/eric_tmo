from django.contrib import admin

admin.site.site_header = "mScripter Services Admin Portal"
admin.site.site_title = "mScripter Admin"
admin.site.index_title = "Welcome to mScripter Admin Portal "

from .models import DBUpdate
admin.site.register(DBUpdate)

# from .models import Help
# admin.site.register(Help)

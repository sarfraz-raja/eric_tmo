from django.contrib import admin
from .models import Software
from .models import MMEPool
from .models import TermPointToMme
from .models import AMFPool
from .models import TermPointToAmf
from .models import MoName
from .models import MoDetail
from .models import MoRelation
from .models import MoAttribute
from .models import Client
from .models import ScriptJob


# Register your models here.
admin.site.register(MMEPool)
admin.site.register(AMFPool)
admin.site.register(TermPointToMme)
admin.site.register(TermPointToAmf)
admin.site.register(Software)
admin.site.register(Client)
admin.site.register(MoName)
admin.site.register(MoDetail)
admin.site.register(MoRelation)
admin.site.register(MoAttribute)
admin.site.register(ScriptJob)

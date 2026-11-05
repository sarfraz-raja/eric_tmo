from django.db import models
from django.contrib.auth.models import User


class DBUpdate(models.Model):
    appname = models.CharField(max_length=100, blank=True, null=True, default='')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_dbupdate')
    remark = models.CharField(max_length=100, blank=False, null=False, default='DB Update')
    status = models.CharField(max_length=20, blank=True, null=True, default='Running')
    script = models.CharField(max_length=100, blank=True, null=True, default='')
    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return F'{self.appname} : {self.user} : {self.create_dt}'

    class Meta:
        db_table = 'account_dbupdate'
        unique_together = ('appname', 'user', 'create_dt')
        ordering = ('-update_dt',)

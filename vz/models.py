from django.db import models
from django.contrib.auth.models import User


class Mme(models.Model):
    mmepool = models.CharField(max_length=50, blank=False)
    mmename = models.CharField(max_length=50, blank=False)
    mmeid = models.CharField(max_length=50, blank=False)
    version = models.CharField(max_length=50, blank=False)
    ip = models.CharField(max_length=50, blank=False)

    def __str__(self) -> str:
        return F'{self.mmepool}  {self.mmename}  {self.mmeid}  {self.version}  {self.ip}'

    class Meta:
        db_table = 'vz_mme'
        unique_together = ('mmepool', 'mmeid')
        verbose_name = 'MME'


class Amf(models.Model):
    amfpool = models.CharField(max_length=50, blank=False)
    amfname = models.CharField(max_length=50, blank=False)
    amfid = models.CharField(max_length=50, blank=False)
    version = models.CharField(max_length=50, blank=False)
    ip = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return F'{self.amfpool}  {self.amfname}  {self.version}  {self.amfid}  {self.ip}'

    class Meta:
        db_table = 'vz_amf'
        unique_together = ('amfpool', 'amfid')
        verbose_name = 'AMF'


class SW(models.Model):
    name = models.CharField(max_length=50, blank=False)
    ne_version = models.CharField(max_length=50, blank=False)
    release_version = models.CharField(max_length=50, blank=False)

    def __str__(self): return F'{self.name}  {self.ne_version}  {self.release_version}'

    class Meta:
        db_table = 'vz_sw'
        unique_together = ('name',)
        verbose_name = 'SW'


class Client(models.Model):
    market = models.CharField(max_length=50, blank=False)
    usm = models.CharField(max_length=50, blank=False)
    sw = models.CharField(max_length=50, blank=False)
    mmepool = models.CharField(max_length=50, blank=False)
    amfpool = models.CharField(max_length=50, blank=False)
    timezone = models.CharField(max_length=50, blank=False)
    gnbidlength = models.CharField(max_length=50, blank=False)
    plmn = models.CharField(max_length=550, blank=False, null=False)

    def __str__(self): return F'{self.market}  {self.usm}  {self.sw}  {self.mmepool}  {self.amfpool}'

    class Meta:
        db_table = 'vz_client'
        unique_together = ('market', 'sw', 'usm')
        verbose_name = 'Client'


class VZJob(models.Model):
    client = models.ForeignKey(Client, on_delete=models.SET_DEFAULT, default=1)
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=1)
    site = models.CharField(max_length=100, blank=False, null=False, default='Error')
    status = models.CharField(max_length=100, blank=False, null=False, default='Queued')
    script = models.CharField(max_length=100, blank=False, null=False, default='')
    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)

    def __str__(self): return F'{self.site}  {self.status}'

    class Meta:
        db_table = 'vz_job'
        verbose_name = 'Job'
        ordering = ('-update_dt',)


# class MoRelation(models.Model):
#     parent = models.CharField(max_length=100)
#     child = models.CharField(max_length=100)
#     tag = models.CharField(max_length=100)
#     software = models.ForeignKey(Software, on_delete=models.CASCADE)
#
#     def __str__(self): return F'{self.software.swname}  {self.parent}  {self.child}  {self.tag}'
#
#     class Meta:
#         db_table = 'vz_morelation'
#         unique_together = ('parent', 'child', 'software', 'tag')
#         verbose_name = 'MoRelation'
#
#
# class MoAttribute(models.Model):
#     software = models.ForeignKey(Software, on_delete=models.CASCADE)
#     moc = models.CharField(max_length=100)
#     attribute = models.CharField(max_length=100)
#
#     def __str__(self): return F'{self.software.swname}  {self.moc}  {self.attribute}'
#
#     class Meta:
#         db_table = 'vz_moattribute'
#         unique_together = ('software', 'moc')
#         verbose_name = 'MoAttribute'
#
#
# class MoName(models.Model):
#     software = models.ForeignKey(Software, on_delete=models.CASCADE)
#     moc = models.CharField(max_length=100, blank=False, null=False)
#     moid = models.CharField(max_length=100, null=False, blank=True)
#     motype = models.CharField(max_length=20, null=False, blank=False)
#
#     def __str__(self): return F'{self.software.swname}  {self.moc}  {self.moid}  {self.motype}'
#
#     class Meta:
#         db_table = 'vz_moname'
#         unique_together = ('software', 'moc', 'moid', 'motype')
#         verbose_name = 'MoName'
#
#
# class MoDetail(models.Model):
#     mo = models.ForeignKey(MoName, on_delete=models.CASCADE)
#     parameter = models.CharField(max_length=100, blank=False, null=False)
#     value = models.CharField(max_length=11000, null=False, default='')
#     flag = models.BooleanField(default=True)
#
#     def __str__(self): return F'{self.mo.__str__()}  {self.parameter}  {self.value}  {self.flag}'
#
#     class Meta:
#         db_table = 'vz_modetail'
#         unique_together = ('mo', 'parameter')
#         verbose_name = 'MoDetail'
#

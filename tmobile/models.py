from django.db import models
from django.contrib.auth.models import User


class MMEPool(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self): return self.name

    class Meta:
        db_table = 'tmobile_mmepool'
        unique_together = ('name',)
        verbose_name = 'MMEPool'


class TermPointToMme(models.Model):
    mmepool = models.ForeignKey(MMEPool, on_delete=models.CASCADE)
    mmeName = models.CharField(max_length=50, blank=False)
    termPointToMmeId = models.CharField(max_length=50, blank=False)
    ipAddress1 = models.CharField(max_length=50, blank=False)
    ipAddress2 = models.CharField(max_length=50, blank=False)
    ipv6Address1 = models.CharField(max_length=50, blank=False)
    ipv6Address2 = models.CharField(max_length=50, blank=False)
    mmeSupportLegacyLte = models.CharField(max_length=50, blank=False)
    mmeSupportNbIoT = models.CharField(max_length=50, blank=False)

    def __str__(self): return F'{self.mmepool.name}  {self.mmeName}  {self.termPointToMmeId}  {self.ipAddress1}  {self.ipAddress2}  ' \
                              F'{self.ipv6Address1}  {self.ipv6Address2}  {self.mmeSupportLegacyLte}  {self.mmeSupportNbIoT}'

    class Meta:
        db_table = 'tmobile_termpointmme'
        unique_together = ('mmepool', 'mmeName')
        verbose_name = 'TermPointToMMe'


class AMFPool(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self): return self.name

    class Meta:
        db_table = 'tmobile_amfpool'
        unique_together = ('name',)
        verbose_name = 'AMFPool'


class TermPointToAmf(models.Model):
    amfpool = models.ForeignKey(AMFPool, on_delete=models.CASCADE)
    amfName = models.CharField(max_length=50, blank=False)
    defaultAmf = models.CharField(max_length=50, blank=False)
    ipv4Address1 = models.CharField(max_length=50, blank=False)
    ipv4Address2 = models.CharField(max_length=50, blank=False)
    ipv6Address1 = models.CharField(max_length=50, blank=False)
    ipv6Address2 = models.CharField(max_length=50, blank=False)
    termPointToAmfId = models.CharField(max_length=50, blank=False)

    def __str__(self): return F'{self.amfpool.__str__()}  {self.amfName}  {self.defaultAmf}  {self.ipv4Address1}  {self.ipv4Address2}  ' \
                              F'{self.ipv6Address1}  {self.ipv6Address2}  {self.termPointToAmfId}'

    class Meta:
        db_table = 'tmobile_termpointamf'
        unique_together = ('amfpool', 'termPointToAmfId')
        verbose_name = 'TermPointToAmf'


class Software(models.Model):
    swname = models.CharField(max_length=50, blank=False)

    def __str__(self): return F'{self.swname}'

    class Meta:
        db_table = 'tmobile_software'
        unique_together = ('swname',)
        verbose_name = 'Software'


class Client(models.Model):
    mname = models.CharField(max_length=50, blank=False)
    enm = models.CharField(max_length=50, blank=False)
    software = models.ForeignKey(Software, on_delete=models.CASCADE)
    mmepool = models.ForeignKey(MMEPool, on_delete=models.CASCADE)
    amfpool = models.ForeignKey(AMFPool, on_delete=models.CASCADE)
    NTPServer1 = models.CharField(max_length=50, blank=False)
    NTPServer2 = models.CharField(max_length=50, blank=False)
    NTPServer3 = models.CharField(max_length=50, blank=False)
    NTPServer4 = models.CharField(max_length=50, blank=False)
    timeZone = models.CharField(max_length=50, blank=False)

    def __str__(self): return F'{self.software.swname}  {self.mname}  {self.enm}  {self.mmepool.name}  {self.amfpool.name}'

    class Meta:
        db_table = 'tmobile_client'
        unique_together = ('software', 'mname', 'enm')
        verbose_name = 'Client'


class MoRelation(models.Model):
    parent = models.CharField(max_length=100)
    child = models.CharField(max_length=100)
    tag = models.CharField(max_length=100)
    software = models.ForeignKey(Software, on_delete=models.CASCADE)

    def __str__(self): return F'{self.software.swname}  {self.parent}  {self.child}  {self.tag}'

    class Meta:
        db_table = 'tmobile_morelation'
        unique_together = ('parent', 'child', 'software', 'tag')
        verbose_name = 'MoRelation'


class MoAttribute(models.Model):
    software = models.ForeignKey(Software, on_delete=models.CASCADE)
    moc = models.CharField(max_length=100)
    attribute = models.CharField(max_length=100)

    def __str__(self): return F'{self.software.swname}  {self.moc}  {self.attribute}'

    class Meta:
        db_table = 'tmobile_moattribute'
        unique_together = ('software', 'moc')
        verbose_name = 'MoAttribute'


class MoName(models.Model):
    software = models.ForeignKey(Software, on_delete=models.CASCADE)
    moc = models.CharField(max_length=100, blank=False, null=False)
    moid = models.CharField(max_length=100, null=False, blank=True)
    motype = models.CharField(max_length=20, null=False, blank=False)

    def __str__(self): return F'{self.software.swname}  {self.moc}  {self.moid}  {self.motype}'

    class Meta:
        db_table = 'tmobile_moname'
        unique_together = ('software', 'moc', 'moid', 'motype')
        verbose_name = 'MoName'


class MoDetail(models.Model):
    mo = models.ForeignKey(MoName, on_delete=models.CASCADE)
    parameter = models.CharField(max_length=100, blank=False, null=False)
    value = models.CharField(max_length=11000, null=False, default='')
    bbversion = models.CharField(max_length=15, blank=True, null=False, default="")
    flag = models.BooleanField(default=True)
    backupflag = models.BooleanField(null=True, blank=True, default=None)

    def __str__(self): return F'{self.mo.__str__()}  {self.parameter}  {self.value}  {self.flag}'

    class Meta:
        db_table = 'tmobile_modetail'
        unique_together = ('mo', 'parameter')
        verbose_name = 'MoDetail'


class ScriptJob(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tmobile_scriptjob')
    sites = models.CharField(max_length=500, blank=True, null=True, default='')
    status = models.CharField(max_length=100, blank=True, null=True, default='Queued')
    script = models.CharField(max_length=100, blank=True, null=True, default='')
    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)

    def __str__(self): return F'{self.sites}  {self.status}'

    class Meta:
        db_table = 'tmobile_scriptjob'
        verbose_name = 'TMOScriptJob'
        ordering = ('-update_dt',)

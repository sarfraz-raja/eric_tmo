from django import template

# Third-party app imports

# Realative imports of the 'app-name' package


register = template.Library()


@register.filter('has_group')
def has_group(request, group_name):
    """
    Verifica se este usuário pertence a um grupo
    """
    groups = request.user.groups.all().values_list('name', flat=True)
    return True if group_name in groups else False

@register.filter(name='headerheadurl')
def headerheadurl_filter(value):
    urlhead={
        "/": "/// GS Audit & Scripting",
        "/ATT/scriptlist/": "Script List for AT&T LTE/5G",
        "/T-Mobile/script/": "T-Mobile LTE/NR Scripting",
        "/T-Mobile/sitelist/": "Script List for T-Mobile LTE/NR",
        "/ATT/GSAudit/": "AT&T LTE/NR GS Audit",
        "/ATT/GSAuditList/": "AT&T LTE/NR GS Audit Report",
        "/ATT/script/": "AT&T LTE/5G Scripting",
        "/NBR/script/": "NBR CleanUp Scripting",
        "/NBR/sitelist/": "Script List for NBR CleanUp",
        "/dbupdate/": "DB Update",
        "/dbupdatelist/": "DB Update List"
    }
    return urlhead[value] if value in urlhead else ""

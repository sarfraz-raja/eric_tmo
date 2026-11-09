import os
import re
from datetime import datetime
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from common_func.django_user_func import get_paginated_list, save_file
from common_func.custom_log import Custom_Log
from django.urls import reverse

from .models import Software, Client, ScriptJob
from .tmobile_jobs import tmobile_job


def check_user_group(user):
    return user.groups.filter(name='tmobile').exists() or user.is_superuser


@login_required(login_url='/')
@user_passes_test(check_user_group, login_url='/')
def script_tmobile(request):
    if request.method == 'POST':
        sites = re.sub('[^a-zA-Z0-9_-]', '', request.POST.get('siteid'))
        # cname = request.POST.get('cname')
        swrel = request.POST.get('swrel')
        mname = request.POST.get('mname')
        swenm = request.POST.get('sw_enm')
        debug = request.POST.get('debug') == 'on'
        user = User.objects.get(username=request.user.username)
        software = Software.objects.get(swname=swrel)
        client = Client.objects.get(software=software, mname=mname, enm=swenm)  # cname=cname, 
        script_job = ScriptJob.objects.create(client=client, sites=sites, user=user)
        script_job.save()
        curr_dt = datetime.now().strftime('%Y%m%d%H%M%S')
        base_dir, zip_file = save_file(request, 'software_log', curr_dt, location=sites, activity='tmobile')
        base_dir, cix_file = save_file(request, 'ciqfile', curr_dt, location=sites, activity='tmobile')
        tmobile_job(script_job_id=script_job.id, cix_file=cix_file, zip_file=zip_file, base_dir=base_dir, sites=sites, debug=debug)
        return HttpResponseRedirect('/T-Mobile/sitelist/')
    else:
        client_tmo = {}
        cols = ['software__swname', 'mname', 'enm']
        qs = Client.objects.all().values(*cols)
        for row in [[_.get(col) for col in cols] for _ in qs if _.get('software__swname') > 'TMO_24_Q4']:
            t = client_tmo
            for col in row:
                t[col] = t.get(col, {})
                t = t[col]
    return render(request, 'script_tmobile.html', {'customer1': client_tmo})


@login_required(login_url='/')
@user_passes_test(check_user_group, login_url='/')
def sitelist_tmobile(request):
    jobs = ScriptJob.objects.all()
    if not request.user.is_superuser: jobs = jobs.filter(user=request.user)
    jobs = get_paginated_list(request, jobs)
    return render(request, 'sitelist_tmobile.html', {'jobs': jobs})

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

from .models import Client, VZJob
from .ix.vz_job import vz_job


def check_user_group(user):
    return user.groups.filter(name='vz').exists() or user.is_superuser


@login_required(login_url='/')
@user_passes_test(check_user_group, login_url='/')
def script_vz(request):
    if request.method == 'POST':
        client = Client.objects.get(market=request.POST.get('market'), usm=request.POST.get('usm'), sw=request.POST.get('sw'))
        user = User.objects.get(username=request.user.username)
        site = re.sub('[^a-zA-Z0-9_-]', '', request.POST.get('siteid'))
        script_job = VZJob.objects.create(client=client, user=user, site=site)
        script_job.save()
        curr_dt = datetime.now().strftime('%Y%m%d%H%M%S')
        sw_log = None
        # base_dir, sw_log = save_file(request, 'software_log', curr_dt, location=site, activity='vz')
        base_dir, cqfile = save_file(request, 'cqfile', curr_dt, location=site, activity='vz')
        print(F'{base_dir}---{cqfile}')
        vz_job(job_id=script_job.id, cqfile=cqfile, sw_log=sw_log, base_dir=base_dir, curr_dt=curr_dt)
        return HttpResponseRedirect('/VZ/sitelist/')
    else:
        clints = {}
        cols = ['market', 'usm', 'sw']
        qs = Client.objects.all().values(*cols)
        for row in [[_.get(col) for col in cols] for _ in qs if _.get('sw') != 'Removed']:
            t = clints
            for col in row:
                t[col] = t.get(col, {})
                t = t[col]
    return render(request, 'script_vz.html', {'clints': clints})


@login_required(login_url='/')
@user_passes_test(check_user_group, login_url='/')
def sitelist_vz(request):
    jobs = VZJob.objects.all()
    if not request.user.is_superuser: jobs = jobs.filter(user=request.user)
    jobs = get_paginated_list(request, jobs)
    return render(request, 'sitelist_vz.html', {'jobs': jobs})

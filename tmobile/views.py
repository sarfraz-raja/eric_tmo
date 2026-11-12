import os
import re
from datetime import datetime
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from common_func.django_user_func import get_paginated_list, save_file
from common_func.custom_log import Custom_Log
from django.urls import reverse

from .models import Software, Client, ScriptJob, MoAttribute
from .tmobile_jobs import tmobile_job
from . import csv_xml_convert as cxc

CONVERT_MAX_UPLOAD = 50 * 1024 * 1024


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
        debug_local = request.get_host().split(':')[0] in ('localhost', '127.0.0.1')
        user = User.objects.get(username=request.user.username)
        software = Software.objects.get(swname=swrel)
        client = Client.objects.get(software=software, mname=mname, enm=swenm)  # cname=cname, 
        script_job = ScriptJob.objects.create(client=client, sites=sites, user=user)
        script_job.save()
        curr_dt = datetime.now().strftime('%Y%m%d%H%M%S')
        base_dir, zip_file = save_file(request, 'software_log', curr_dt, location=sites, activity='tmobile')
        base_dir, cix_file = save_file(request, 'ciqfile', curr_dt, location=sites, activity='tmobile')
        tmobile_job(script_job_id=script_job.id, cix_file=cix_file, zip_file=zip_file, base_dir=base_dir, sites=sites, debug=debug, debug_local=debug_local)
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


class InMemoryUploadHandler(MemoryFileUploadHandler):
    # Uploaded file stays in memory only (never a temp file on disk), bigger requests are dropped
    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        self.activated = content_length <= CONVERT_MAX_UPLOAD


def attachment(content, file_name, content_type):
    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = F'attachment; filename="{file_name}"'
    return response


@login_required(login_url='/')
@user_passes_test(check_user_group, login_url='/')
@csrf_exempt
def convert_tmobile(request):
    # upload handlers must be set before the CSRF check reads request.POST, so CSRF is checked inside
    if request.method == 'POST': request.upload_handlers = [InMemoryUploadHandler(request)]
    return convert_tmobile_protected(request)


@csrf_protect
def convert_tmobile_protected(request):
    if request.method != 'POST':
        return render(request, 'convert_tmobile.html', {'columns': cxc.TEMPLATE_COLUMNS, 'max_mb': CONVERT_MAX_UPLOAD // (1024 * 1024)})
    action, upload = request.POST.get('action'), request.FILES.get('file')
    if upload is None:
        too_big = int(request.META.get('CONTENT_LENGTH') or 0) > CONVERT_MAX_UPLOAD
        return JsonResponse({'error': F'File is larger than {CONVERT_MAX_UPLOAD // (1024 * 1024)} MB' if too_big else 'Select a file'}, status=400)
    stem = os.path.splitext(os.path.basename(upload.name))[0]
    try:
        text = cxc.decode(upload.read())
        if action == 'csv_to_xml':
            ns_map = dict(cxc.FALLBACK_NS) | dict(MoAttribute.objects.values_list('moc', 'attribute'))
            files, _, _ = cxc.csv_to_xml(text, stem, ns_map, split_by_message_id=request.POST.get('split') == 'on')
            if len(files) == 1: return attachment(files[0][1].encode('utf-8'), files[0][0], 'application/xml')
            return attachment(cxc.zip_files(files), F'{cxc.safe_name(stem)}_xml.zip', 'application/zip')
        if action == 'xml_to_csv':
            csv_text, _ = cxc.xml_to_csv(text)
            return attachment(csv_text.encode('utf-8-sig'), F'{cxc.safe_name(stem)}.csv', 'text/csv')
        return JsonResponse({'error': 'Unknown action'}, status=400)
    except cxc.ConvertError as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='/')
@user_passes_test(check_user_group, login_url='/')
def convert_template_tmobile(request):
    return attachment(cxc.template_csv().encode('utf-8-sig'), 'csv_to_xml_template.csv', 'text/csv')

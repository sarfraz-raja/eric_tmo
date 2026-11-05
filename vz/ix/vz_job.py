from .BaseUSID import BaseUSID
from django.conf import settings
from common_func.custom_log import Custom_Log
from vz.models import VZJob, SW

import os
import shutil
import importlib
from datetime import datetime


def vz_job(*, job_id, cqfile, sw_log, base_dir, curr_dt) -> None:
    script_job = VZJob.objects.get(id=job_id)
    site = script_job.site
    client = script_job.client
    sw = SW.objects.get(name=client.sw)
    usm = client.usm
    script_job.status = 'Running'
    script_job.save()
    print(F'{base_dir}---{site}---{curr_dt}')
    log_file = os.path.join(base_dir, F'{site}_{curr_dt}.log')
    custom_log = Custom_Log(log_file=log_file, activity='VZ Scripting')
    log = custom_log.log
    log.info(F'Started running job for VZ Site : {site}')
    try:
        log.info(F'Loading/Extracting data from CQ files into memory!!!')
        usid = BaseUSID(client=client, sw=sw, usm=usm, log=log, site=site, base_dir=base_dir, cqfile=cqfile, sw_log=sw_log)
        log.info(F'Data Successfully loaded into memory!!!')
        for node in usid.site_dict.keys():
            custom_log.log.info(F'Writing Scripts for {node}')
            for module in script_job_module():
                log.info(F'Writing Scripts for VZ Node {node} ---->{module}')
                self = getattr(importlib.import_module(F'vz.ix.{module}'), module)(usid, node)
                self.run()
        log.info(F'Job completed for VZ Site : {site}, Status: Successful!!!')
        script_job.status = 'Completed'
    except:
        log.exception("message")
        log.info(F'Job completed for VZ Site : {site}, Status: Failed!!!')
        script_job.status = 'Failed'

    custom_log.release()
    # shutil.copy(log_file, base_dir)
    shutil.make_archive(base_dir, 'zip', base_dir)
    shutil.rmtree(base_dir)
    # os.remove(log_file)
    script_job.script = os.path.basename(base_dir + '.zip')
    script_job.save()


def script_job_module():
    return [
        'A_01_OAM', 'A_02_ENB_NE_Grow',  'A_03_GNB_NE_Grow',
    ]

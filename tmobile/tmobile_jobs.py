import os
import shutil
import importlib
from datetime import datetime
from django.conf import settings
from common_func.custom_log import Custom_Log
from tmobile.models import ScriptJob
from tmobile.tmo_ix.tmo_usid_data import tmo_usid_data
from tmobile.tmo_ix.tmo_debug_csv import files_snapshot, write_debug_csv


def tmobile_job(script_job_id, cix_file, zip_file, base_dir, sites, debug=False, debug_local=False):
    script_job = ScriptJob.objects.get(id=script_job_id)
    client = script_job.client
    script_job.status = 'Running'
    script_job.save()
    # script_list = script_job_files(sw=script_job.client.software.swname)

    curr_dt = datetime.now().strftime('%Y%m%d%H%M%S')
    log_file = os.path.join(settings.MEDIA_ROOT, 'tmobile', F'{sites}_{curr_dt}.log')
    custom_log = Custom_Log(log_file=log_file, activity='T-Mobile Scripting')
    log = custom_log.log
    log.info(F'Started running job for T-Mobile Site : {sites}')
    log.info(F'Market: {script_job.client.mname}')
    log.info(F'ENM : {script_job.client.enm}')
    log.info(F'SW : {script_job.client.software.swname}')
    log.info(F'SiteID: {sites}')
    try:
        log.info(F'Loading/Extracting data from CIQ and DCGK files into memory!!!')
        usid = tmo_usid_data(client=client, base_dir=base_dir, log=log, cix_file=cix_file, zip_file=zip_file, sites=sites)
        usid.debug_csv, usid.debug_csv_local = debug, debug_local
        log.info(F'Data Successfully loaded into memory!!!')
        log.info(F'Debug (CSV files): {"ON" if debug else "OFF"}')
        for node in set().union(usid.gnodeb.keys(), usid.enodeb.keys()):
            usid.script_dict = {'AP': False, 'SB': '', 'SE': '', 'SI': '', 'conf': []}
            log.info(F'Writing Scripts for T-Mobile Node {node}!!!')
            for module in script_job_files(sw=''):
                if str(module[:2]).lower() not in ['lt', 'nr', 'c0', 'c1', 'c2', 'te']: continue
                elif module[:3] == 'lte' and node not in usid.enodeb.keys(): continue
                elif module[:2] == 'nr' and node not in usid.gnodeb.keys(): continue
                log.info(F'Writing Scripts for T-Mobile Node {node} ---->{module}')
                files_before = files_snapshot(base_dir) if debug else None
                self = getattr(importlib.import_module(F'tmobile.tmo_ix.{module}'), module)(usid=usid, node=node)
                self.run()
                if debug: write_debug_csv(self, files_before)
        log.info(F'Job completed for T-Mobile Site : {sites}, Status: Successful!!!')
        script_job.status = 'Completed'
    except:
        log.exception("message")
        log.info(F'Job completed for T-Mobile Site : {sites}, Status: Failed!!!')
        script_job.status = 'Failed'


    custom_log.release()
    shutil.copy(log_file, base_dir)
    shutil.make_archive(base_dir, 'zip', base_dir)
    script_job.script = os.path.basename(base_dir + '.zip')
    script_job.save()
    shutil.rmtree(base_dir)
    os.remove(log_file)


def script_job_files(sw=''):
    return [
        'C01_ProjectInfo', 'C02_SiteBasic', 'C03_SiteEquipment', 'C04_SiteInstallation',

        'C07_01a_Transport', 'C07_01b_lte_nr_InternalRouting', 'C07_02_Equipment', 'lte_10_RadioCutOver',
        'C08_lte_01_ENodeBFunction', 'C08_lte_02_TermPointToMme', 'C08_lte_03_eNodeBMOs', 'C08_lte_04_ENodeBPara',
        'C09_nr_01_GNBFunction', 'C09_nr_02_TermPointToAmf', 'C09_nr_03_gNodeBMOs',
        'C07_nr_20_lte_20_Idle',
        'lte_04_Delete_EUtranCell',
        'lte_03_eNodeBMOs_mos', 'lte_05_CellMOs_mos',
        'lte_05_CellMOs', 'lte_06_CellPara', 'lte_07_Relations', 'lte_09_BaseLine',
        'lte_12_GUtraRelation',

        'nr_04_NRCell',
        'nr_05_EUtranRelation',
        'nr_09a_BaseLine', 'nr_09b_NRLB_Para', 'nr_09c_N41_Para', 'nr_09d_N41_BWP',
        'nr_10_Intra_CellRelation',
        'nr_10c1_ExternalGNBCUCP', 'nr_10c2_NRRel_Inter_gNodeB',
        'nr_11_NRFreqProfile_v13', 'nr_12_NR_CA',
        'nr_13_NRRel_EAST_para', 'nr_14_NRRel_EAST_UeGroup_v6',
        'nr_15_VoNR_scripts', 'nr_16_BWP_Salina_scripts',
        'nr_17_WPS_Bundle_FDD_TDD',
        'C05_NodeInfo',
        'test_000_lte', 'test_000_nr',
    ]

import sys
import os
import pandas as pd
from django.db import transaction
from common_func.custom_log import Custom_Log

from vz.models import Mme, Amf
from vz.models import SW, Client

from django.conf import settings
custom_log_db = Custom_Log(log_file=os.path.join(settings.MEDIA_ROOT, 'dbupdate', F'test.log'), activity='Updating DB Tables')

sw = SW()
pd_sheets = None
sw_name = 'test'


@transaction.atomic
def load_mme_pool_list():
    table_name = 'Mme'
    df = dataprocess_form_excell(table_name)
    if len(df.index) > 0:
        df = df[['mmepool', 'mmename', 'mmeid', 'version', 'ip']]
        for index, row in df.iterrows():
            o_d = row.to_dict()
            obj, created = Mme.objects.update_or_create(mmepool=o_d['mmepool'], mmeid=o_d['mmeid'], defaults=o_d)
            custom_log_db.log.info(F'{table_name}--{created}---{obj}')
        custom_log_db.log.info(F'{table_name} Updated Complete!!!')
    else: custom_log_db.log.info(F'--------------> No Data for {table_name} <--------------')


@transaction.atomic
def load_anf_pool_list():
    table_name = 'Amf'
    df = dataprocess_form_excell(table_name)
    if len(df.index) > 0:
        df = df[['amfpool', 'amfname', 'amfid', 'version', 'ip']]
        for index, row in df.iterrows():
            o_d = row.to_dict()
            obj, created = Amf.objects.update_or_create(amfpool=o_d['amfpool'], amfid=o_d['amfid'], defaults=o_d)
            custom_log_db.log.info(F'{table_name}--{created}---{obj}')
        custom_log_db.log.info(F'{table_name} Updated Complete!!!')
    else: custom_log_db.log.info(F'--------------> No Data for {table_name} <--------------')


@transaction.atomic
def load_software():
    table_name = 'SW'
    df = dataprocess_form_excell(table_name)
    if len(df.index) > 0:
        df = df[['name', 'ne_version', 'release_version']]
        for index, row in df.iterrows():
            o_d = row.to_dict()
            obj, created = SW.objects.update_or_create(name=o_d['name'], defaults=o_d)
            custom_log_db.log.info(F'{table_name}--{created}---{obj}')
        custom_log_db.log.info(F'{table_name} Updated Complete!!!')
    else: custom_log_db.log.info(F'--------------> No Data for {table_name} <--------------')


@transaction.atomic
def load_customer():
    table_name = 'Client'
    df = dataprocess_form_excell(table_name)
    if len(df.index) > 0:
        df = df[['market', 'usm', 'sw', 'mmepool', 'amfpool', 'timezone', 'gnbidlength', 'plmn']]
        if len(df.index) > 0:
            for index, row in df.iterrows():
                o_d = row.to_dict()
                obj, created = Client.objects.update_or_create(market=o_d['market'], usm=o_d['usm'], sw=o_d['sw'], defaults=o_d)
                custom_log_db.log.info(F'{table_name}--{created}---{obj}')
            custom_log_db.log.info(F'Client Updated Complete!!!')
        else: custom_log_db.log.info(F'--------------> No Data for {table_name} <--------------')
    else: custom_log_db.log.info(F'--------------> No Data for {table_name} <--------------')


def dataprocess_form_excell(sheets_name):
    df_sheet = pd.DataFrame([])
    if sheets_name in pd_sheets.sheet_names:
        df_sheet = pd_sheets.parse(sheets_name).astype(str)
        if len(df_sheet.index):
            df_sheet = df_sheet.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df_sheet


def dbupdate_vz(db_update_file, custom_log_defined):
    global custom_log_db
    global pd_sheets
    global sw
    global sw_name
    try:
        custom_log_db = custom_log_defined
        sw_name = os.path.basename(db_update_file).split('.')[0]
        pd_sheets = pd.ExcelFile(db_update_file)
        load_mme_pool_list()
        load_anf_pool_list()
        load_software()
        load_customer()
        return True
    except:
        return False

import copy
from xml.dom.minidom import Document, Element
import os
import re
import json
import numpy as np
from django.db.models import Q
from .tmo_usid_data import tmo_usid_data
from . import tmo_debug_csv
from tmobile.models import MoAttribute, MoDetail, MoName, MoRelation


maxNoOfPagingRecords_dict = {3000: '4', 5000: '7', 10000: '16', 20000: '16', 15000: '16'}


class tmo_xml_base:
    def __init__(self, usid: tmo_usid_data, node: str = None):
        self.usid = usid
        self.node = node
        self.motype = 'default'
        self.script_list = []
        self.config_files_in_ap = False
        self.mo_dict = {}
        self.script_file = ''
        self.csv_enabled = False
        self.csv_failed = False
        self.csv_rows = []
        self.csv_root_ldn = ''
        if self.__class__.__name__.startswith('C'):
            self.relative_path = [F'02_REMOTE', self.node, F'{"_".join(self.__class__.__name__.split("_")[1:])}_{self.node}.xml']
        else:
            self.relative_path = [F'02_REMOTE', self.node, F'{self.__class__.__name__}_{self.node}.xml']

        self.MoName = MoName
        self.MoDetail = MoDetail
        self.MoRelation = MoRelation
        self.mo_attr = {_.moc: _.attribute for _ in MoAttribute.objects.filter(software=self.usid.client.software)}

        self.site = self.usid.sites.get(F'site_{self.node}')
        self.enbdata = self.usid.enodeb.get(self.node, {})
        self.gnbdata = self.usid.gnodeb.get(self.node, {})
        self.df_enb_cell = self.usid.df_enb_cell.copy().loc[(self.usid.df_enb_cell.postsite == self.node)]
        self.df_gnb_cell = self.usid.df_gnb_cell.copy().loc[(self.usid.df_gnb_cell.postsite == self.node)]
        self.market_dict = {
            'tri_la': ['Escondido', 'Vegas', 'ElMonte', 'Torrance', 'SimiValley', 'Irvine', 'Riverside'],
            'ncal': ['SanFrancisco', 'SantaClara', 'Stockton', 'WestOakland', 'WestSacramento'],
            'long_island': ['Syosset_LI'],
            'new_york': ['Syosset'],
            'charlotte': ['Charlotte'],
            'hawaii': ['Hawaii'],
            'philadelphia': ['Philadelphia'],
            'washington_dc': ['Beltsville'],
            'excalibur': ['Atlanta', 'Jacksonville', 'Miami', 'Orlando', 'Tampa', 'Excalibur'],
        }
        self.bbversion = 'G3' if 'CXP2010174' in self.enbdata.get('sw', self.gnbdata.get('sw')) else 'G2'

    def initialize_var(self): pass
    def special_formate_scripts(self): pass

    def cr_file_path(self):
        self.script_file = os.path.join(self.usid.base_dir, *self.relative_path)
        out_dir = os.path.dirname(self.script_file)
        if not os.path.exists(out_dir): os.makedirs(out_dir)

    def write_script_file(self) -> None:
        if len(self.script_list) == 0: return
        if type(self.script_list[0]) is str:
            self.relative_path[-1] = self.relative_path[-1][:-3] + 'mos'
        self.cr_file_path()
        if type(self.script_list[0]) is str:
            with open(self.script_file, 'w') as f: f.write('\n'.join(self.mos_files_start() + self.script_list + self.mos_files_end()))
        elif self.script_list[0].firstChild is not None:
            with open(self.script_file, 'w') as f:
                for index, elem in enumerate(self.script_list):
                    if len(self.script_list) == 1: f.write(elem.toprettyxml(encoding='UTF-8', indent='  ').decode('utf-8').strip() + '\n')
                    elif index > 0:
                        f.write(elem.toprettyxml(encoding='UTF-8', indent='  ').decode('utf-8').replace(
                            '<?xml version="1.0" encoding="UTF-8"?>', '').strip() + '\n]]>]]>\n')
                    else: f.write(elem.toprettyxml(encoding='UTF-8', indent='  ').decode('utf-8').strip() + '\n]]>]]>\n')

    def run(self) -> None:
        self.initialize_var()
        self.write_script_file()
        self.special_formate_scripts()

    def create_elm_with_attr(self, tmp_dict, tag_name, tag_end, attr=None) -> Element:
        mo = self.create_and_add_mo_para_to_xml_doc(tmp_dict, tag_name, tag_end)
        if attr:
            for key in attr: mo.setAttribute(key, attr[key])
        return mo

    def reconfig_ap_file_path_to_remote(self) -> None:
        if self.config_files_in_ap and self.enbdata.get('BBChange', self.gnbdata.get('BBChange')):
            self.relative_path = ['01_AP', self.node, self.node, self.relative_path[-1]]
            self.usid.script_dict['conf'].append(self.relative_path[-1])

    def write_backup_script_file(self, *, script_list) -> None:
        if len(script_list) == 0: return
        relative_path = copy.deepcopy(self.relative_path)
        relative_path.insert(-1, 'BACKUP_SCRIPT')
        # relative_path[-1] = 'BACKUP_MOS_SCRIPT' + relative_path[-1]
        if type(script_list[0]) is str: relative_path[-1] = relative_path[-1][:-3] + 'mos'
        script_file = os.path.join(self.usid.base_dir, *relative_path)
        if not os.path.exists(os.path.dirname(script_file)): os.makedirs(os.path.dirname(script_file))
        if type(script_list[0]) is str:
            with open(script_file, 'w') as f: f.write('\n'.join(self.mos_files_start() + script_list + self.mos_files_end()))
        elif script_list[0].firstChild is not None:
            with open(script_file, 'w') as f:
                for index, elem in enumerate(script_list):
                    if len(script_list) == 1: f.write(elem.toprettyxml(encoding='UTF-8', indent='  ').decode('utf-8').strip() + '\n')
                    elif index > 0:
                        f.write(elem.toprettyxml(encoding='UTF-8', indent='  ').decode('utf-8').replace(
                            '<?xml version="1.0" encoding="UTF-8"?>', '').strip() + '\n]]>]]>\n')
                    else: f.write(elem.toprettyxml(encoding='UTF-8', indent='  ').decode('utf-8').strip() + '\n]]>]]>\n')



    def ap_xml_element_form_dict(self, *, mo_name: str, para_dict: dict) -> Element:
        doc = Document()
        xml_mo = doc.createElement(mo_name)
        for para in para_dict.keys():
            if para == 'attributes':
                for attr in para_dict['attributes'].keys(): xml_mo.setAttribute(attr, str(para_dict['attributes'][attr]))
            elif type(para_dict[para]) in [int, str]:
                elm = doc.createElement(str(para))
                elm.appendChild(doc.createTextNode(para_dict[para]))
                xml_mo.appendChild(elm)
            elif type(para_dict[para]) is dict:
                xml_mo.appendChild(self.ap_xml_element_form_dict(mo_name=para, para_dict=para_dict[para]))
            elif type(para_dict[para]) is list:
                for val in para_dict[para]:
                    if type(val) is dict:
                        xml_mo.appendChild(self.ap_xml_element_form_dict(mo_name=para, para_dict=val))
                    else:
                        elm = doc.createElement(str(para))
                        elm.appendChild(doc.createTextNode(val))
                        xml_mo.appendChild(elm)
        return xml_mo

    def ap_xml_document_form_dict(self, *, mo_name: str, para_dict: dict) -> Document:
        """ :rtype: Element """
        doc = Document()
        xml_mo = doc.createElement(mo_name)
        for para in para_dict.keys():
            if para == 'attributes':
                for attr in para_dict['attributes'].keys(): xml_mo.setAttribute(attr, str(para_dict['attributes'][attr]))
            elif type(para_dict[para]) in [int, str]:
                elm = doc.createElement(str(para))
                elm.appendChild(doc.createTextNode(para_dict[para]))
                xml_mo.appendChild(elm)
            elif type(para_dict[para]) is dict:
                xml_mo.appendChild(self.ap_xml_element_form_dict(mo_name=para, para_dict=para_dict[para]))
            elif type(para_dict[para]) is list:
                for val in para_dict[para]:
                    if type(val) is dict:
                        xml_mo.appendChild(self.ap_xml_element_form_dict(mo_name=para, para_dict=val))
                    else:
                        elm = doc.createElement(str(para))
                        elm.appendChild(doc.createTextNode(val))
                        xml_mo.appendChild(elm)
        doc.appendChild(xml_mo)
        return doc

    def create_and_add_mo_para_to_xml_doc(self, moadddict, moname, moattribute):
        doc = Document()
        cmo = doc.createElement(moname)
        if moattribute != '': cmo.setAttribute('xmlns', 'urn:com:ericsson:ecim:' + moattribute)
        for key, value in moadddict.items():
            for spvalue in value.split("@@"): cmo.appendChild(self.add_str_type_para_to_xml_doc(doc, key, spvalue))
        return cmo

    def add_str_type_para_to_xml_doc(self, doc, key, value):
        p1 = doc.createElement(str(key))
        if '##' in value:
            for spvalue in value.split("##"):
                key1, value1 = spvalue.split("=", 1)
                p3 = doc.createElement(str(key1))
                value3 = doc.createTextNode(self.check_text_element(str(value1)))
                p3.appendChild(value3)
                p1.appendChild(p3)
        else:
            p1.appendChild(doc.createTextNode(self.check_text_element(str(value))))
        return p1

    def add_space_seperated_type_para_to_xml_doc(self, doc, p1, key, value):
        for spvalue in value.split(" "):
            p3 = doc.createElement(str(key))
            value3 = doc.createTextNode(self.check_text_element(str(spvalue)))
            p3.appendChild(value3)
            p1.appendChild(p3)
        return p1

    def check_text_element(self, in_str, change_me=True):
        if in_str is not None: in_str = in_str.strip('"')
        if (in_str is None) or (in_str == 'None'): return ''
        elif (',' in in_str) and ('ManagedElement' not in in_str) and (not in_str.startswith('SubNetwork')):
            in_str = F'ManagedElement={self.node},{in_str}'
        elif ('ManagedElement' in in_str) and (F'ManagedElement={self.node}' not in in_str):
            if change_me:
                tmp_ref = {_.split('=')[0]: _.split('=')[-1] for _ in
                           in_str.split(',')[in_str.split(',').index([_ for _ in in_str.split(',') if 'ManagedElement' in _][0]):]}
                if tmp_ref.get('ManagedElement'): tmp_ref['ManagedElement'] = self.node
                in_str = ','.join([key + '=' + tmp_ref[key] for key in tmp_ref])
        elif re.match('.*\s\((.*)\)$', in_str):
            in_str = re.match('.*\s\((.*)\)$', in_str).group(1)
        return in_str

    def mo_add_form_dict_xml(self, para_dict: dict, moname: str = 'ManagedElement', change_me: bool = True):
        doc = Document()
        cmo = doc.createElement(moname)
        if self.mo_attr.get(moname):
            cmo.setAttribute('xmlns', F'urn:com:ericsson:ecim:{self.mo_attr.get(moname)}')
        for key in para_dict:
            if 'xmlns' == key: cmo.setAttribute('xmlns', str(para_dict[key]))
            elif para_dict[key] is None or type(para_dict[key]) is int or type(para_dict[key]) is str:
                if para_dict[key] is None or self.check_text_element(str(para_dict[key]), change_me) in [None, 'None', '']: continue
                elm = doc.createElement(str(key))
                text_node = doc.createTextNode(self.check_text_element(str(para_dict[key]), change_me))
                elm.appendChild(text_node)
                cmo.appendChild(elm)
            elif type(para_dict[key]) is dict: cmo.appendChild(self.mo_add_form_dict_xml(para_dict[key], key, change_me))
            elif type(para_dict[key]) is list:
                for item in para_dict[key]:
                    if type(item) is not dict:
                        if (self.check_text_element(str(item), change_me) is None) or (self.check_text_element(str(item), change_me) == ''): continue
                        elm = doc.createElement(str(key))
                        elm.appendChild(doc.createTextNode(self.check_text_element(str(item), change_me)))
                        cmo.appendChild(elm)
                    else: cmo.appendChild(self.mo_add_form_dict_xml(item, key, change_me))
        return cmo

    # MOS Script Creation from dict start
    def mos_script_list_form_dict(self, *, para_dict: dict = None, mo_fdn: str = None) -> list:
        if para_dict is [None, 'None', '', {}, []] or mo_fdn in [None, 'None', '', {}, []]: return []
        if para_dict.get('managedElementId') is not None: mo_fdn = F'ManagedElement={self.node}'
        script = []
        if para_dict.get('attributes') is not None:
            tmp_dict = dict((k, v) for k, v in para_dict.items() if k[0].islower())
            script.extend(self.mos_script_mo_form_dict(mo_fdn=mo_fdn, para_dict=tmp_dict))
        for para in para_dict.keys():
            if para[0].isupper():
                if type(para_dict[para]) is list:
                    for child_mo in para_dict[para]:
                        script.extend(self.mos_script_list_form_dict(
                            para_dict=child_mo, mo_fdn=F'{mo_fdn},{para}={child_mo.get(self.get_moc_id(para))}'))
                if type(para_dict[para]) is dict:
                    script.extend(self.mos_script_list_form_dict(
                        para_dict=para_dict[para], mo_fdn=F'{mo_fdn},{para}={para_dict[para].get(self.get_moc_id(para))}'))
        return script

    def mos_script_mo_form_dict(self, *, mo_fdn: str, para_dict: dict) -> list:
        if 'attributes' not in para_dict.keys(): return [F'## Error on Dict Creation {mo_fdn}', '']
        script = []
        s_type = para_dict.get('attributes').get('xc:operation')
        mo_id = self.get_moc_id(self.get_end_moc(mo_fdn))
        mo_id_val = para_dict[mo_id]
        para_list = [_ for _ in para_dict if _ not in ['attributes', mo_id] and self.non_null_flag(val=para_dict[_])]
        if s_type == 'create':
            script += ([F'crn {mo_fdn}'] + [F'{k} {self.mos_norm_value(para_dict.get(k))}' for k in para_list] + ['end'])
        elif s_type == 'update':
            script += ([F'ld {mo_fdn}$'] + [F'set {mo_fdn}$ {k} {self.mos_norm_value(para_dict.get(k))}' for k in para_list])
        elif s_type == 'delete': script.append(F'del {mo_fdn}$')
        script.append('')
        return script

    def mos_norm_value(self, val):
        """
        Special Character --- *()[]\+<>= and space
        Special characters are any characters other than the supported characters.
        These characters must be wrapped in quotes to be accepted in the scope name or attribute value part of the command.
        *()[]\+<>= and space - Special C
        :rtype: str
        """
        val_type = type(val)
        if val_type in [int, bool]: val = str(val).lower()
        if val_type is dict and val.get('attributes', {}).get('xc:operation', '') == 'delete': return '<empty>'
        elif val_type in [list, dict] and len(val) == 0: return ''
        elif val_type == list:
            if type(val[0]) is dict: return ';'.join([self.mos_norm_value(_) for _ in val])
            else: return ' '.join([self.mos_norm_value(_) for _ in val])
        elif val_type == dict: return ','.join([F'{_}={self.mos_norm_value(val.get(_))}' for _ in val])
        elif len([_ for _ in ['{', '[', '('] if str(val).startswith(_)]) > 0: return val
        elif re.match('(.*)\s\((.*)\)$', val): return re.match('(.*)\s\((.*)\)$', val).group(1)
        # elif re.match('(.*),(.*)=(.*)$', val) and 'ManagedElement=' not in val:
        #     return F'"{self.usid.dnPrefix},MeContext={self.node},ManagedElement={self.node},{val}"'
        # elif re.match('(.*),(.*)=(.*)$', val) and 'SubNetwork=' not in val and 'ManagedElement=' in val:
        #     return F'"{self.usid.dnPrefix},MeContext={self.node},ManagedElement={self.node},{re.match(".*ManagedElement=([^,]*),(.*)$", val).group(2)}"'
        # elif len([_ for _ in ['*', '(', ')', '[', ']', '\\', '+', '<', '>', '=', ' ', ',', ':'] if _ in str(val)]) > 0:
        #     return F'"{val}"'
        else: return val

    # MOS Script Creation from dict End

    @staticmethod
    def get_end_mo_name(mo: str) -> str: return mo.split(',')[-1].split('=')[0]

    @staticmethod
    def lower_first_char(in_str: str) -> str: return in_str[0].lower() + in_str[1:]

    @staticmethod
    def get_moc_id(moc: str) -> str: return moc[0].lower() + moc[1:] + 'Id'

    @staticmethod
    def get_end_moc(mo: str) -> str: return mo.split(',')[-1].split('=')[0]

    def get_mo_related_attributes(self, mo):
        qs = getattr(mo, 'modetail_set').filter((Q(flag=True)) & (Q(bbversion='') | Q(bbversion__contains=self.bbversion))).order_by('parameter').distinct().values('parameter', 'value')
        ret_dict = {self.get_moc_id(mo.moc): mo.moid}
        ret_dict.update({self.lower_first_char(_.get('parameter')): json.loads(_.get('value')) if _.get('value') else '' for _ in qs})
        return ret_dict

    def get_db_attributes(self, moc):
        qs = self.MoDetail.objects.filter((Q(mo__software=self.usid.client.software) & Q(mo__moc=moc) & Q(mo__motype=self.motype) & Q(flag=True))
                                          & (Q(bbversion='') | Q(bbversion__contains=self.bbversion))).order_by('parameter').distinct().values('parameter', 'value')
        return {_.get('parameter'): json.loads(_.get('value')) if _.get('value') else '' for _ in qs}

    def get_db_backupflag_attributes(self, moc, moid):
        qs = self.MoDetail.objects.filter((Q(mo__software=self.usid.client.software) & Q(mo__moc=moc) & Q(mo__moid=moid) & Q(mo__motype=self.motype)
                                           & Q(flag=True) & Q(backupflag=True))
                                          & (Q(bbversion='') | Q(bbversion__contains=self.bbversion))).values('parameter', 'value')
        return {_.get('parameter'): json.loads(_.get('value')) if _.get('value') else '' for _ in qs}

    def get_mo_attributes(self, moc, moid=''):
        mos = self.MoName.objects.filter(moc=moc, software=self.usid.client.software, motype=self.motype)
        for mo in mos:
            if mo.moid == moid: break
        ret_dict = self.get_mo_related_attributes(mo) if 'mo' in locals() else {}
        ret_dict.update({self.get_moc_id(moc): moid})
        return ret_dict

    def update_db_attr_with_mo_data(self, moc, site, mo):
        ret_dict = self.get_mo_attributes(moc)
        mo_data = site.site_extract_data(mo) if site else {}
        for key in ret_dict: ret_dict[key] = mo_data.get(key, ret_dict[key])
        return ret_dict

    def update_db_with_mo_for_siteid_and_fdn(self, moc, site, mo):
        ret_dict = self.get_mo_attributes(moc)
        site = None if (site in [None, '']) | (mo in [None, '']) else self.usid.sites.get(F'site_{site}')
        mo_data = site.site_extract_data(mo) if site else {}
        for key in ret_dict: ret_dict[key] = mo_data.get(key, ret_dict[key])
        return ret_dict

    def append_equipment_elems(self, site, parent_mo, parent_mo_tag, moc: str):
        db_dict = self.get_mo_attributes(moc)
        for c_mo in site.find_mo_ending_with_parent_str(moc, parent_mo_tag):
            db_dict_c = db_dict.copy()
            tmp_dict = site.site_extract_data(c_mo)
            for key in db_dict_c: db_dict_c[key] = tmp_dict.get(key, db_dict[key])
            parent_mo.appendChild(self.mo_add_form_dict_xml(db_dict_c, moc))

    @staticmethod
    def validate_db_moid(*, moid: str) -> bool: return False if moid in [None, 'None', '', 'XX', 'nan', np.nan, '""'] or ',' in moid else True

    @staticmethod
    def validate_db_mo(*, mo: str) -> bool: return False if mo in [None, 'None', '', 'nan', np.nan, '""'] else True

    def db_append_child_tags(self, motype, rel_tag, csv_parent=''):
        ret_mos = []
        mo_tag_ins = self.MoName.objects.filter(moc=motype, software=self.usid.client.software, motype=self.motype)
        if mo_tag_ins.exists():
            for mo_tag_in in mo_tag_ins:
                if self.validate_db_moid(moid=mo_tag_in.moid): ret_mos.append(self.append_child_tags(mo_tag_in, rel_tag=rel_tag, csv_parent=csv_parent))
        return ret_mos

    def append_child_tags(self, motype, rel_tag, csv_parent=''):
        mo_dict = self.get_mo_related_attributes(motype)
        csv_mo = F'{csv_parent},{motype.moc}={motype.moid}'.lstrip(',')
        if self.csv_enabled: tmo_debug_csv.track_mo(self, mo_name=csv_mo, moid=motype.moid, final=mo_dict, default=mo_dict, default_source='MOC')
        parent_mo = self.mo_add_form_dict_xml(mo_dict, motype.moc)
        for children in self.MoRelation.objects.filter(parent=motype.moc, tag=rel_tag, software=self.usid.client.software):
            for child in self.MoName.objects.filter(moc=children.child, software=self.usid.client.software, motype=self.motype):
                if (self.validate_db_moid(moid=child.moid) and
                        child.modetail_set.filter((Q(flag=True)) & (Q(bbversion='') | Q(bbversion__contains=self.bbversion))).exists()):
                    child_mo = self.append_child_tags(child, rel_tag, csv_parent=csv_mo)
                    parent_mo.appendChild(child_mo)
        return parent_mo

    def log_append_child_tags(self, moc, tag, parent_str='', pre_site=''):
        ret_mos = []
        site = self.usid.sites.get(F'site_{pre_site}')
        mos = site.find_mo_ending_with_parent_str(moc, parent_str) if site and parent_str != '' else []
        if len(mos) > 0:
            for mo in mos:
                mo_attrs_db = {self.get_moc_id(moc): '1'}
                mo_attrs_db.update(self.get_db_attributes(self.get_end_moc(mo)))
                mo_attrs_site = site.get_mo_attr_str(mo)
                db_preferred = self.get_db_backupflag_attributes(self.get_end_moc(mo), mo.split('=')[-1])
                csv_default, csv_source = dict(mo_attrs_db), {}
                for key in mo_attrs_db:
                    if key in db_preferred: mo_attrs_db[key] = db_preferred[key]
                    else: mo_attrs_db[key] = mo_attrs_site.get(key, mo_attrs_db[key])
                    csv_source[key] = 'MOC (backupflag)' if key in db_preferred else 'DCGK' if key in mo_attrs_site else 'MOC'
                if self.csv_enabled:
                    tmo_debug_csv.track_mo(self, mo_name=self.csv_ldn(mo), moid=mo.split('=')[-1], final=mo_attrs_db, default=csv_default,
                                           dcgk=mo_attrs_site, source=csv_source, dcgk_site=pre_site)
                moc_tag = self.get_end_moc(mo)
                ret_mo = self.mo_add_form_dict_xml(mo_attrs_db, moc_tag)
                for children in self.MoRelation.objects.filter(parent=moc, tag=tag, software=self.usid.client.software):
                    for child in self.log_append_child_tags(children.child, tag, mo, pre_site):
                        ret_mo.appendChild(child)
                ret_mos.append(ret_mo)
        else:
            ret_mos.extend(self.db_append_child_tags(moc, tag, csv_parent=self.csv_ldn(parent_str) if parent_str else self.csv_root_ldn))
        return ret_mos

    def csv_ldn(self, mo: str) -> str: return re.sub(r'^.*?ManagedElement=[^,]*,?', '', mo)

    def get_mo_dict_from_site_or_db(self, *, moc: str, mo_id: str, node: str = '', parent: str = '') -> dict:
        mo = None
        if node == '': node = self.node
        site = self.usid.sites.get(F'site_{node}')
        if node is not None and site is not None:
            mo = site.find_mo_ending_with_parent_str_with_id(moc, mo_id, parent)
            if len(mo) > 0: tmp_dict = self.update_db_attr_with_mo_data(moc, site, mo[0])
            else: tmp_dict = self.get_mo_attributes(moc, mo_id)
        else: tmp_dict = self.get_mo_attributes(moc, mo_id)
        tmp_dict.update({self.lower_first_char(moc) + 'Id': mo_id})
        return tmp_dict

    def get_mo_dict_for_id_tag(self, moc: str, moid: str, prev_site: str = None, parent: str = ''):
        mo = None
        site = self.usid.sites.get(F'site_{prev_site}')
        if prev_site is not None and site is not None:
            mos = site.find_mo_ending_with_parent_str_with_id(moc, moid, parent)
            if len(mos) > 0:
                mo = mos[0]
                tmp_dict = self.update_db_attr_with_mo_data(moc, site, mo)
            else: tmp_dict = self.get_mo_attributes(moc, moid)
        else: tmp_dict = self.get_mo_attributes(moc, moid)
        tmp_dict.update({self.lower_first_char(moc) + 'Id': moid})
        return tmp_dict, mo

    def union_of_mo_cosite_create_xml_script(self, *, moc: str) -> list:
        db_dict = self.get_mo_attributes(moc)
        air_profile_id_dict = {}
        ret_mos = []
        for site_key in self.usid.sites:
            site = self.usid.sites.get(site_key)
            air_profile_mos = site.find_mo_ending_with_parent_str(moc)
            for air_profile_mo in air_profile_mos:
                moid = air_profile_mo.split(',')[-1]
                if moid in air_profile_id_dict: continue
                air_profile_id_dict[moid] = True
                data_dict = site.site_extract_data(air_profile_mo)
                data_dict = {key: data_dict.get(key) for key in db_dict}
                ret_mos.append(self.mo_add_form_dict_xml(data_dict, moc))
        return ret_mos

    def mo_para_db_dict(self, mo, site):
        mo_attrs_db = {self.lower_first_char(self.get_end_mo_name(mo)) + 'Id': '1'}
        mo_attrs_db.update(self.get_db_attributes(self.get_end_mo_name(mo)))
        mo_attrs_site = site.get_mo_attr_str(mo)
        for key in mo_attrs_db: mo_attrs_db[key] = mo_attrs_site.get(key, mo_attrs_db[key])
        return mo_attrs_db

    def ap_rcp_msg_cap(self) -> Document:
        doc = Document()
        mo1 = doc.createElement('hello')
        mo1.setAttribute('xmlns', 'urn:ietf:params:xml:ns:netconf:base:1.0')
        doc.appendChild(mo1)
        mo1.appendChild(self.mo_add_form_dict_xml(para_dict={'capability': ['urn:ietf:params:netconf:base:1.0']},
                                                  moname='capabilities', change_me=False))
        return doc

    @staticmethod
    def null_flag(*, val) -> bool: return str(val) in ['', '""', '[]', '{}', 'None', 'null', 'empty', ]

    @staticmethod
    def non_null_flag(*, val) -> bool: return str(val) not in ['', '""', '[]', '{}', 'None', 'null', 'empty', ]

    def check_if_mo_exist_for_ldn_get_fdn(self, *, node: str, mo_ldn: str) -> str or None:
        mo_fdn = None
        if F'site_{node}' in self.usid.sites and len(self.usid.sites.get(F'site_{node}').get_mos_w_end_str(mo_ldn=mo_ldn)) > 0:
            mo_fdn = self.usid.sites.get(F'site_{node}').get_mos_w_end_str(mo_ldn=mo_ldn)
            if len(mo_fdn) > 1:
                self.usid.log.info(F'Error : !!! Multiple MOs Found in DCGK, Please validate Scripts !!!')
                self.usid.log.info(mo_fdn)
            mo_fdn = mo_fdn[0]
        return mo_fdn

    def get_mo_dict_from_moc_node_ldn_moid(self, *, moc: str, node: str, mo_ldn: str, moid: str) -> dict:
        ret_dict = self.get_mo_attributes(moc=moc)
        if F'site_{node}' in self.usid.sites and mo_ldn in len(self.usid.sites.get(F'site_{node}').get_mos_w_end_str(mo_ldn=mo_ldn)) > 0:
            mo_fdn = self.usid.sites.get(F'site_{node}').get_mos_w_end_str(mo_ldn=mo_ldn)
            if len(mo_fdn) > 1:
                self.usid.log.info(F'Error : !!! Multiple MOs Found in DCGK, Please validate Scripts !!!')
                self.usid.log.info(mo_fdn)
            mo_fdn = mo_fdn[0]
            mo_data = self.usid.sites.get(F'site_{node}').site_extract_data(mo=mo_fdn)
            ret_dict |= {_: mo_data.get(_, ret_dict[_]) for _ in ret_dict}
        if self.non_null_flag(val=moid):
            ret_dict |= {self.get_moc_id(moc): moid}
        elif self.get_moc_id(moc) not in ret_dict.keys():
            ret_dict |= {self.get_moc_id(moc): '1'}
        return ret_dict

    def netconf_value_update(self, val) -> str:
        if self.null_flag(val=val): return ''
        else: val = str(val).strip('"')
        if ',' in val and '=' in val:
            if 'ManagedElement=' in val: val = re.match('.*ManagedElement=[^,]*,(.*)', val).group(1)
            val = F'ManagedElement={self.node},{val}'
        elif re.match('.*\s\((.*)\)$', val): val = re.match('.*\s\((.*)\)$', val).group(1)
        return val

    def netconf_para_element(self, para, val) -> object:
        val = self.netconf_value_update(val)
        if (para in [None, 'None', 'null', 'empty', '', '""', [], {}] or
                val in [None, 'None', 'null', 'empty', '', '""', [], {}]): return None
        doc = Document()
        ele = doc.createElement(para)
        if val == 'XMLemptyELEMENT': return ele
        ele.appendChild(doc.createTextNode(val))
        return ele

    def netconf_mo_form_dict(self, para_dict: dict, moc: str = 'ManagedElement') -> Element:
        doc = Document()
        xml_mo = doc.createElement(moc)
        mo_attribute = self.mo_attr.get(moc)
        mocId = self.get_moc_id(moc)
        del_flag = False
        if mo_attribute: xml_mo.setAttribute('xmlns', F'urn:com:ericsson:ecim:{mo_attribute}')
        if 'attributes' in para_dict.keys():
            for attr in para_dict['attributes'].keys():
                if para_dict['attributes'][attr] in ['create', 'update']: continue
                xml_mo.setAttribute(attr, str(para_dict['attributes'][attr]))
                if para_dict['attributes'][attr] == 'delete': del_flag, mocId = True, self.get_moc_id(moc)
        for para in para_dict.keys():
            if para_dict[para] in [None, 'None', 'null', 'empty', '""', [], {}] or para == 'attributes': continue
            elif del_flag is True and mocId != para: continue
            elif type(para_dict[para]) is dict: xml_mo.appendChild(self.netconf_mo_form_dict(para_dict[para], para))
            elif type(para_dict[para]) is list:
                for val in para_dict[para]:
                    if type(val) is dict: xml_mo.appendChild(self.netconf_mo_form_dict(val, para))
                    else:
                        element = self.netconf_para_element(para, val)
                        if element is not None: xml_mo.appendChild(element)
            elif type(para_dict[para]) in [int, str]:
                element = self.netconf_para_element(para, para_dict[para])
                if element is not None: xml_mo.appendChild(element)
        return xml_mo

    def get_mo_dict_from_moc_node_fdn_moid(self, *, moc: str, node: str = None, mo_fdn: str = None, moid: str = None) -> dict:
        tmp_dict = self.get_mo_dict_for_moc_node_fdn(moc=moc, node=node, mo_fdn=mo_fdn)
        if self.non_null_flag(val=moid):
            tmp_dict |= {self.get_moc_id(moc): moid}
        elif self.get_moc_id(moc) not in tmp_dict.keys():
            tmp_dict |= {self.get_moc_id(moc): '1'}
        # if not self.validate_mo_exist_on_site_with_no_eq_change(fdn=mo_fdn):
        #     tmp_dict['attributes'] = {'xc:operation': 'create'}
        return tmp_dict

    def get_mo_dict_for_moc_node_fdn(self, *, moc: str, node: str = None, mo_fdn: str = None) -> dict:
        ret_dict = self.get_mo_attributes(moc=moc)
        if F'site_{node}' in self.usid.sites and mo_fdn in self.usid.sites.get(F'site_{node}').mo_list:
            mo_data = self.usid.sites.get(F'site_{node}').site_extract_data(mo=mo_fdn)
            ret_dict |= {_: mo_data.get(_, ret_dict[_]) for _ in ret_dict}
        return ret_dict

    def get_db_para_dict_with_child(self, *, moc: str, db_moid: str, moid: str, rel_tag: str):
        ret_dict = {}
        db_mo = self.MoName.objects.filter(moc=moc, software=self.usid.client.software, motype=self.motype, moid=db_moid)
        if db_mo.exists():
            db_mo = db_mo[0]
            ret_dict = self.get_mo_related_attributes(db_mo)
            ret_dict |= {'attributes': {'xc:operation': 'create'}, self.get_moc_id(moc=moc): moid}
            if moc.endswith('UeCfg') and moid == 'Base': ret_dict |= {'attributes': {'xc:operation': 'update'}}
            for children in self.MoRelation.objects.filter(parent=db_mo.moc, tag=rel_tag, software=self.usid.client.software):
                for child in self.MoName.objects.filter(moc=children.child, software=self.usid.client.software, motype=self.motype):
                    if child.moid.split(',')[0] == db_moid.split(',')[-1]:
                        if child.moc not in ret_dict.keys(): ret_dict[child.moc] = []
                        ret_dict[child.moc].append(self.get_db_para_dict_with_child(moc=child.moc, db_moid=child.moid,
                                                                                    moid=child.moid.split(',')[-1], rel_tag=rel_tag))

        return ret_dict

    def rcp_msg_capabilities(self) -> Document:
        return self.ap_xml_document_form_dict(
            mo_name='hello',
            para_dict={
                'attributes': {'xmlns': 'urn:ietf:params:xml:ns:netconf:base:1.0'},
                'capabilities': {'capability': ['urn:ietf:params:netconf:base:1.0', 'urn:com:ericsson:ebase:2.0.0']},
                # 'capabilities': {'capability': ['urn:ietf:params:netconf:base:1.0', 'urn:com:ericsson:ebase:0.1.0',
                #                                 'urn:com:ericsson:ebase:1.1.0']}
            }
        )

    def rcp_msg_close(self) -> Document:
        return self.ap_xml_document_form_dict(
            mo_name='rpc',
            para_dict={'attributes': {'message-id': 'Closing', 'xmlns': 'urn:ietf:params:xml:ns:netconf:base:1.0'}, 'close-session': ''}
        )

    def main_rcp_msg_start(self, *, msg_id: str = '1') -> tuple[Document, Element]:
        doc = self.ap_xml_document_form_dict(
            mo_name='rpc',
            para_dict={
                'attributes': {'message-id': msg_id, 'xmlns': 'urn:ietf:params:xml:ns:netconf:base:1.0'},
                'edit-config': {'target': {'running': {}}, 'config': {'attributes': {'xmlns': 'urn:ietf:params:xml:ns:netconf:base:1.0'}}},
            }
        )
        config = doc.getElementsByTagName("config")[0]
        return doc, config

    def paging_max_records(self):
        return maxNoOfPagingRecords_dict.get(self.usid.df_enb_cell.loc[(
                (self.usid.df_enb_cell.postsite == self.node) &
                self.usid.df_enb_cell.celltype.isin(['FDD', 'TDD']))].dlchannelbandwidth.astype(int).min(), '16')

    def append_mos_equipment_elems(self, site, parent_fdn, mo_tag, parent_ldn):
        lines = []
        db_dict = self.get_mo_attributes(mo_tag)
        for c_mo in site.find_mo_ending_with_parent_str(mo_tag, parent_fdn):
            db_dict_c = db_dict.copy()
            tmp_dict = site.site_extract_data(c_mo)
            for key in db_dict_c: db_dict_c[key] = tmp_dict.get(key, db_dict[key])
            lines.extend(self.create_mos_script_from_dict(
                db_dict_c, mo_tag, F'{parent_ldn},{mo_tag}={db_dict_c.get(F"{mo_tag[:1].lower() + mo_tag[1:]}Id")}'))
        return lines

    def union_of_mo_cosite_create_mos_script(self, moname, parentmo):
        db_dict = self.get_mo_attributes(moname)
        db_mo_dict = {}
        ret_mos = []
        for site_key in self.usid.sites:
            site = self.usid.sites.get(site_key)
            union_mo = site.find_mo_ending_with_parent_str(moname)
            for mo in union_mo:
                moid = mo.split(',')[-1]
                if moid in db_mo_dict.keys(): continue
                db_mo_dict[moid] = True
                data_dict = site.site_extract_data(mo)
                data_dict = {key: data_dict.get(key) for key in db_dict}
                if len(parentmo) > 0: mo_name = F'{parentmo},{moid}'
                else: mo_name = moid
                ret_mos.extend(self.create_mos_script_from_dict(para_dict=data_dict, moname=moname, moc=mo_name))
        return ret_mos

    def create_mos_script_from_dict(self, para_dict, moname, moc='', change_me=True) -> list:
        cmo = []
        if len(moc) > 0:
            cmo.append(F'crn {moc}')
            for key in para_dict:
                if (str(key).lower() == F'{moname}Id'.lower()) or (para_dict[key] is None) or (para_dict[key] == ''): continue
                elif type(para_dict[key]) is int or type(para_dict[key]) is str:
                    if (self.mos_check_text_element(str(para_dict[key]), change_me) is None) or \
                            (self.mos_check_text_element(str(para_dict[key]), change_me) == ''): continue
                    val = self.mos_check_text_element(str(para_dict[key]), change_me)
                    cmo.append(F'{str(key)} {val}')
                elif type(para_dict[key]) is dict:
                    val = self.parameter_dict_values(para_dict=para_dict[key], change_me=True, delime=',')
                    if len(val) > 1: cmo.append(F'{str(key)} {val[:-1]}')
                elif type(para_dict[key]) is list:
                    val = self.parameter_list_values(para_dict[key])
                    if len(val) > 1: cmo.append(F'{str(key)} {val[:-1]}')
            cmo.extend(['end', ''])
        return cmo

    def parameter_dict_values(self, para_dict, change_me=True, delime=',') -> str:
        val = ''
        if len(para_dict) != 0:
            for keys in para_dict:
                if type(para_dict[keys]) is dict: val += self.parameter_dict_values(para_dict[keys], delime=';')
                elif type(para_dict[keys]) is list:
                    val += F'{keys}={self.parameter_list_values(para_list=para_dict[keys], change_me=True, delime=" ")},'
                elif (self.mos_check_text_element(str(para_dict[keys]), change_me) is None) or \
                        (self.mos_check_text_element(str(para_dict[keys]), change_me) == ''):
                    val += F'{str(keys)}=,'
                else: val += F'{keys}={self.mos_check_text_element(str(para_dict[keys]), change_me)}{delime}'
        return val.replace(',;', ';').replace(' ,', ',')

    def parameter_list_values(self, para_list, change_me=True, delime=',') -> str:
        val = ''
        for item in para_list:
            if type(item) is dict: val += self.parameter_dict_values(para_dict=item, change_me=True, delime=',') + ';'
            elif type(item) is list: val += self.parameter_list_values(para_list=item, change_me=True, delime=delime)
            elif ((self.mos_check_text_element(str(item), change_me) == 'None') or
                  (self.mos_check_text_element(str(item), change_me) == '')): continue
            else: val += self.mos_check_text_element(str(item), change_me) + delime
        return val.replace(',;', ';').replace(' ,', ',')

    def mos_check_text_element(self, in_str, change_me=True):
        if in_str is not None: in_str = in_str.strip('"')
        if (in_str is None) or (in_str == 'None'):
            return ''
        elif 'ManagedElement' in in_str:  # and (F'ManagedElement={self.node}' not in in_str)
            if change_me:
                tmp_ref = {_.split('=')[0]: _.split('=')[-1] for _ in
                           in_str.split(',')[in_str.split(',').index([_ for _ in in_str.split(',') if 'ManagedElement' in _][0]) + 1:]}
                in_str = ','.join([key + '=' + tmp_ref[key] for key in tmp_ref])
        elif re.match(r'(.*)\s\((.*)\)$', in_str):
            in_str = re.match(r'(.*)\s\((.*)\)$', in_str).group(1)
        return in_str

    def mos_files_start(self) -> list:
        return [F"""
unset all
$date = `date +%Y%m%d_%H%M%S`
l+ LogFile_{self.relative_path[-1].split('.')[0]}_$date.log
lt all
pv $nodename
if $nodename != {self.node}
    print ERROR: Node Name Mismatch. Wrong Node. ABORT !!!
    return
    l-
fi
confbdl+
gs+
cvms pre_{self.__class__.__name__.split("_", maxsplit=2)[2][:20]}_$date

"""]

    def mos_files_end(self) -> list:
        return [F"""
$date = `date +%Y%m%d_%H%M%S`
### cvms post_{self.__class__.__name__.split("_", maxsplit=2)[2][:20]}_$date
unset all
confbdl-
gs
l-
"""]

    def get_market_sbnw_dict(self, market=''):
        market_sbnw_dict = {
            'excalibur': ['Atlanta', 'Jacksonville', 'Miami', 'Orlando', 'Tampa', 'Excalibur'],
            'tri_la': ['Escondido', 'Vegas', 'ElMonte', 'Torrance', 'SimiValley', 'Irvine', 'Riverside'],

        }
        return market_sbnw_dict.get(market, ['!!! Error Cahek market_sbnw_dict on tool!!!'])

    def get_lock_cells(self):
        return [F"""
####:----------------> Lock EUtranCell & NbIotCell, NRCellDU, NRSectorCarrier, MME & AMF <----------------:####
##  ####:----------------> Soft Power Reduction (Start)
##  hget NRSectorCarrier txPowerRatio|txPowerChangeRate
##  mr NRSC
##  ma NRSC NRSectorCarrier=
##  for $mo in NRSC
##      get $mo nRSectorCarrierId > $scID
##      get $mo txPowerRatio > $pwr[$scID]
##      set $mo txPowerChangeRate 5
##      set $mo txPowerRatio 10
##  done
##  wait 50s
##  hget NRSectorCarrier txPowerRatio|txPowerChangeRate

mr unlock_cell
ma unlock_cell ^EUtranCell[FT]DD|NbIotCell|NRCellDU|NRSectorCarrier|TermPointToMme|TermPointToAmf= ^administrativestate$ 1
st unlock_cell
if $nr_of_mos > 0
    bls unlock_cell
    wait 30
fi
get unlock_cell ^operationalState$ 1
if $nr_of_mos > 0
    wait 100
fi
get unlock_cell ^operationalState$ 1
if $nr_of_mos > 0
    bl unlock_cell
fi
st unlock_cell

"""]

    def get_unlock_cells(self):
        return ["""
####:----------------> UnLock EUtranCell & NbIotCell, NRCellDU, NRSectorCarrier, MME & AMF <----------------:####
pr unlock_cell
if $nr_of_mos > 0
    deb unlock_cell
    wait 30
    lst unlock_cell
fi
mr unlock_cell

###  ####:----------------> Soft Power Reduction (End)
###  for $mo in NRSC
###    get $mo nRSectorCarrierId > $scID
###    set $mo txPowerChangeRate 1
###    set $mo txPowerRatio $pwr[$scID]
###  done
"""]

    def get_node_certificate(self):
        return ["""
####:----------------> NodeCredential & TrustCategory for  Https & CliTls <----------------:####
get ,NodeCredential= nodeCredentialId > $nn
get ,TrustCategory= TrustCategoryId > $tt
get SystemFunctions=1,SysM=1,HttpM=1,Https=1$ nodeCredential > $no
get SystemFunctions=1,SysM=1,HttpM=1,Https=1$ trustCategory > $tr
if $no !~ NodeCredential
    set SystemFunctions=1,SysM=1,HttpM=1,Https=1$ nodeCredential SecM=1,CertM=1,NodeCredential=$nn
fi
if $tr !~ TrustCategory
    set SystemFunctions=1,SysM=1,HttpM=1,Https=1$ trustCategory SecM=1,CertM=1,TrustCategory=$tt
fi
get SystemFunctions=1,SysM=1,CliTls=1$ nodeCredential > $no
get SystemFunctions=1,SysM=1,CliTls=1$ trustCategory > $tr
if $no !~ NodeCredential
    set SystemFunctions=1,SysM=1,CliTls=1$ nodeCredential SecM=1,CertM=1,NodeCredential=$nn
fi
if $tr !~ TrustCategory
    set SystemFunctions=1,SysM=1,CliTls=1$ trustCategory SecM=1,CertM=1,TrustCategory=$tt
fi
set SystemFunctions=1,SysM=1,CliTls=1$ administrativeState 1
unset $nn
unset $tt
unset $no
unset $tr

        """]

    def get_vswr_script(self):
        return ["""
####:----------------> FieldReplaceableUnit ---> vswrSupervisionSensitivity & vswrSupervisionActive <----------------:####
mr auxdevice
ma auxdevice ^FieldReplaceableUnit=
for $mo in auxdevice
    get $mo ^fieldReplaceableUnitId$ > $zz
    get $mo productData > $productData
    $prodname = $productData[productName] -s \\x020 -g
    $prodnumber = $productData[productNumber] -s \\x020 -g
    if $prodname ~ ^RUS.1B.*
        set FieldReplaceableUnit=$zz,RfPort=[AR]$ administrativeState 1
        set FieldReplaceableUnit=$zz,RfPort=B$ administrativeState 0
        set FieldReplaceableUnit=$zz,RfPort=[ABR]$ vswrSupervisionSensitivity 100
        set FieldReplaceableUnit=$zz,RfPort=A$ vswrSupervisionActive true
        set FieldReplaceableUnit=$zz,RfPort=B$ vswrSupervisionActive false
    else if $prodname ~ ^RU-.*
        set FieldReplaceableUnit=$zz,RfPort=A$ administrativeState 1
        set FieldReplaceableUnit=$zz,RfPort=B$ administrativeState 0
        set FieldReplaceableUnit=$zz,RfPort=[AB]$ vswrSupervisionSensitivity 100
        set FieldReplaceableUnit=$zz,RfPort=A vswrSupervisionActive true
        set FieldReplaceableUnit=$zz,RfPort=B vswrSupervisionActive false
    else if $prodname ~ ^RRUS32B.*
        set FieldReplaceableUnit=$zz,RfPort=[ABCDR]$ administrativeState 1
        set FieldReplaceableUnit=$zz,RfPort=[ABCDR]$ vswrSupervisionSensitivity 100
        set FieldReplaceableUnit=$zz,RfPort=[ABCD]$ vswrSupervisionActive true
    else if $prodname ~ ^RRUS.1.*
        set FieldReplaceableUnit=$zz,RfPort=[ABR]$ administrativeState 1
        set FieldReplaceableUnit=$zz,RfPort=[ABR]$ vswrSupervisionSensitivity 100
        set FieldReplaceableUnit=$zz,RfPort=[AB]$ vswrSupervisionActive true
    else if $prodname ~ ^RRUS.*
        set FieldReplaceableUnit=$zz,RfPort=[ABCDR]$ administrativeState 1
        set FieldReplaceableUnit=$zz,RfPort=[ABCDR]$ vswrSupervisionSensitivity 100
        set FieldReplaceableUnit=$zz,RfPort=[ABCD]$ vswrSupervisionActive true
    else if $prodname ~ ^Radio4455.* || $prodname ~ ^Radio4449.* || $prodname ~ ^Radio4480.* || $prodname ~ ^Radio2260.* || $prodname ~ ^Radio4415.* || $prodname ~ ^Radio4478.* || $prodname ~ ^Radio2203*
        set FieldReplaceableUnit=$zz,RfPort=[ABCDR]$ administrativeState 1
        set FieldReplaceableUnit=$zz,RfPort=[ABCDR]$ vswrSupervisionSensitivity 100
        set FieldReplaceableUnit=$zz,RfPort=[ABCD]$ vswrSupervisionActive true
        set FieldReplaceableUnit=$zz,RfPort=[ABCD],FreqBandData= vswrSupervisionActive true
        set FieldReplaceableUnit=$zz,RfPort=[ABCD],FreqBandData= vswrSupervisionSensitivity 100
    fi
    if $prodnumber ~ ^KRC118050/1 || $prodnumber ~ ^KRC118034/1 || $prodnumber ~ ^KRC161254/1 || $prodnumber ~ ^KRC161601/1
        set FieldReplaceableUnit=$zz,RfPort=[ABCDR]$ vswrSupervisionSensitivity -1
        set FieldReplaceableUnit=$zz,RfPort=[ABCDR]$ vswrSupervisionActive false
    fi
done
mr auxdevice
unset $productData
unset $prodnumber
unset $prodname
        """]

    def get_nr_freq_rel_cellrel_functions(self):
        return ["""
####:----------------> Functions for NRNetwork, NRFrequency, NRFreqRelation & NRCellRelation <----------------:####
pr GNBCUCPFunction=1,NRNetwork=1$
if $nr_of_mos = 0
    cr GNBCUCPFunction=1,NRNetwork=1
fi

func createnrfrequency
    pr $frqldn$
    if $nr_of_mos = 0
        crn $frqldn
        arfcnValueNRDl $arfcnval
        smtcScs $smtcscs
        smtcPeriodicity $smtcperiodicity
        smtcOffset $smtcoffset
        smtcDuration $smtcduration
        end
    fi
endfunc

func createnrfreqprofile
    lpr GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$arfcnval
    lpr GNBCUCPFunction=1,Mcpc=1,McpcPSCellNrFreqRelProfile=$arfcnval
endfunc

#######################else if $arfcnval >= 499200 && $arfcnval <= 537999
#####################    $creselpro = 7
#######################else if $arfcnval >= 2054166 && $arfcnval <= 2084999
#####################    $creselpro = 7

func createnrfreqrelation
    ## NRFreqRelation ---> cellReselectionPriority is N71=4, N41=7 & mmWave=7
    if $arfcnval >= 123400 && $arfcnval <= 130400
        $creselpro = 4
    else if $arfcnval >= 386000 && $arfcnval <= 398000
        $creselpro = 7
    else
      $creselpro = 7
    fi
    pr $nrfreqrelldn$
    if $nr_of_mos = 0
        crn $nrfreqrelldn
        cellReselectionPriority 7
        nRFrequencyRef $frqldn
        pMax 23
        qOffsetFreq 0
        qRxLevMin -140
        sIntraSearchP 62
        tReselectionNR 2
        threshXHighP 4
        threshXLowP 0
        end
        set $nrfreqrelldn$ cellReselectionPriority $creselpro
    fi
endfunc

func createnrcellrelation
    pr $nrcellrelldn$
    if $nr_of_mos = 0
        crn $nrcellrelldn
        isRemoveAllowed false
        nRCellRef $targetcucell
        nRFreqRelationRef $nrfreqrelldn
        end
    fi
endfunc

        """]

    def get_sc_features_dict(self, sw='', script_type=''):
        lte_dict = {
            'Logical': ["""
####:----------------------> Logical FeatureState <----------------------:####
## CPRI Compression for BB6648
get SystemFunctions=1,Lm=1,FeatureState=CXC4012051 ^licenseState$ ^1
if $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4012051 featureState 1
fi

## if non MSMM false, if MSMM on any sector true
get ^FieldReplaceableUnit= isSharedWithExternalMe true
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011018 featureState 1
fi

## No of Cells
st ENodeBFunction=1,EUtranCell[FT]DD=
if $nr_of_mos > 3
   ## 6 Cell Support
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011317 featureState 1
else if $nr_of_mos > 6
   ## 7-12 Cell Support
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011317 featureState 1
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011356 featureState 1
else if $nr_of_mos > 12
   ## Support for 13-18 cells in single eNodeB
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011317 featureState 1
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011356 featureState 1
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011917 featureState 1
fi

## Optimized Release Control Activation
get SystemFunctions=1,Lm=1,FeatureState=CXC4012485 ^licenseState$ ^1
if $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4012485 featureState 1
else
   l echo "ERROR: ----Optimized RRC Connection Release Control (CXC4012485) is unavailable----"
fi

## SUPPLEMENTARY DL ONLY CELL Activation
get ^EUtranCell[FT]DD= ^isDlOnly$ ^true
if $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011567 featureState 1
fi

pr SystemFunctions=1,Lm=1,FeatureState=CXC4012052
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012052 featureState 1
fi

## FeatureState for NbIotCell
pr ENodeBFunction=1,NbIotCell=
if $nr_of_mos > 0
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012081 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012079 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012508 featureState 1
fi

## FeatureState for Category M Access & Category M Connected Mode Mobility
get ENodeBFunction=1,EUtranCellFDD= catm1SupportEnabled true
if $nr_of_mos > 0
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012082 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012187 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012319 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012359 featureState 1
    scw L4911:1
fi

## Quad Antenna
set SystemFunctions=1,Lm=1,FeatureState=CXC4010609 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011427 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011667 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011056 featureState 1     

"""],
            'ALL': ["""
set SystemFunctions=1,Lm=1,FeatureState=CXC4011823 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010319 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010320 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010609 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010613 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010616 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010618 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010620 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010717 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010723 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010770 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010856 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010912 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010949 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010956 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010959 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010960 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010961 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010962 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010963 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010964 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010967 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010974 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010990 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011011 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011033 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011034 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011050 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011055 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011056 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011059 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011060 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011061 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011062 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011064 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011067 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011069 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011074 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011075 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011157 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011163 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011183 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011245 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011251 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011252 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011255 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011317 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011319 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011327 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011345 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011356 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011366 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011370 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011373 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011376 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011378 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011427 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011443 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011444 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011476 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011477 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011479 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011482 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011485 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011515 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011554 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011559 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011666 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011667 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011711 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011714 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011807 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011811 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011813 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011815 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011820 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011823 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011838 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011918 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011937 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011938 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011939 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011946 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011969 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011980 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011999 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4012003 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012018 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012036 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012070 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012079 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012097 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012259 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012260 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012271 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012324 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012371 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012381 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012385 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012485 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012504 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012563 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4040008 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012578 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012637 featureState 1
                    """],
            'FDD': ["""
####:---> LTE FDD Features <---:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4012344 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011929 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012081 featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4011996 featureState 0
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012157 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4010841 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4010973 featureState 0
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012257 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4012218 featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4011973 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011253 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011914 featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4040009 featureState 0

//set SystemFunctions=1,Lm=1,FeatureState=CXC4012034 featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012015 featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4011710 featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4010955 featureState 0
//set SystemFunctions=1,Lm=1,FeatureState=CXC4010980 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011967 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011422 featureState 1

scw 83:0,869:0,2095:0,2123:0,145:1,2959:0,4467:0,L5319:1
## CATM HY58469
get SystemFunctions=1,Lm=1,FeatureState=CXC4012359 featureState$ ^1
if $nr_of_mos > 0
   scw L4911:1
fi
pv $mibprefix
if $mibprefix ~ Syosset
   scw 1449:7
else
   scw 1449:4
fi
"""],
            'TDD': ["""
####:---> Features for L41 (L2500 - TDD, AAS)  <---:####
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012344 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011929 featureState 0
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012081 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011996 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012157 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010841 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010973 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012257 featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012218 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011973 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011253 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011914 featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4040009 featureState 1

set SystemFunctions=1,Lm=1,FeatureState=CXC4040018 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012356 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012199 featureState 1

####:---> NO SC defined on 23Q2 on L41 TDD Cells <---:####
                    """],
            'TMO_26_Q3': {'ALL': [""""""], 'FDD': [""""""], 'TDD': [""""""], },
            'TMO_26_Q2': {'ALL': [""""""], 'FDD': [""""""], 'TDD': [""""""], },
            'TMO_26_Q1': {'ALL': [""""""], 'FDD': [""""""], 'TDD': [""""""], },
            'TMO_25_Q4': {'ALL': [""""""], 'FDD': [""""""], 'TDD': [""""""], },
            'TMO_25_Q3': {'ALL': [""""""], 'FDD': [""""""], 'TDD': [""""""], },
        }
        nr_dict = {
            'ALL': ["""
####:---> NR Features <---:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4011823 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012379 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012375 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012273 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4040008 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012325 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012492 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012475 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012479 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012477 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012478 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012558 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012592 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012591 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012637 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012531 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012534 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012538 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012373 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012549 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012548 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012650 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012710 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012731 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012728 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012661 featureState 1

## 10GE Port Capability
pr SystemFunctions=1,Lm=1,FeatureState=CXC4011838
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011838 featureState 1
fi
## CPRI Compression
pr SystemFunctions=1,Lm=1,FeatureState=CXC4012051
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012051 featureState 1
fi

####Update for G3 Nodes Only
pr SystemFunctions=1,Lm=1,FeatureState=CXC4012763
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012763 featureState 1
fi

## Gen3 and above
pr upgradepackage=.*/2
if $nr_of_mos != 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012493 featureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012690 featureState 1
fi

###  PP 166 disable for retail store Picos
mr RDOT_check 
ma RDOT_check FieldReplaceableUnit productData IRU.*88..*
pr RDOT_check
if $nr_of_mos != 0
    scw PP166:0
fi

##  Activation RCDS parameter
get PowerSaving ranCompDeepSleepEnabled > $RCDS
if $RCDS = true
	scw RC960:1
fi

##  NR Downlink Beam Optimizer
get FeatureState=CXC4012589 featureState$ > $CXC4012589_state
pr NRCellDU=[QS]
$NRDlBeamOptim_qs_count = $nr_of_mos
if $GenCheck = Gen3or4 && $CXC4012589_state ~ 1 && $NRDlBeamOptim_qs_count = 0
    scw RP1810:2
fi

##    v3 - 24.Q4 TMO inclusion of SC RP1334 for N71 nodes (PDSCH ACK/NACK Aware PDCCH Link Adaptation )
if $K_Cell_Present = 1 && $RP6672_Present = 1
    scw RP1334:2 NR-FR1-FDD
else if $K_Cell_Present = 1
    scw RP1334:2
fi

## RACH backoff (G3+ FDD and TDD)
if $GenCheck = Gen3or4
	scw RP3141:90,RP3142:5,RP2701:20,RP2702:0,RP2703:50,RP2861:12
fi
if $A_Cell_Present = 1 && $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $RP6672_Present = 1 && $QSH_Cell_Present = 0
	scw RP3155:11 NR-FR1-C2-TDD
	scw RP3155:7 NR-FR1-FDD
else if $A_Cell_Present = 1 && $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $RP6672_Present = 0 && $QSH_Cell_Present = 0
	scw RP3155:11 NR-FR1-C1-TDD
	scw RP3155:7 NR-FR1-C1-FDD
else if $A_Cell_Present = 1 && $IJK_Cell_Present = 0 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
	scw RP3155:11
else if $A_Cell_Present = 0 && $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
	scw RP3155:7
fi

## (BSW) UL SU MIMO / MU-MIMO upto 4L
mr ULSU_4L_LayerCheck
ma ULSU_4L_LayerCheck GNBDUFunction=1,NRCellDU=[A] ulMaxMuMimoLayers 4|6|8
pr ULSU_4L_LayerCheck
if $nr_of_mos != 0
	$ULSU_4L_LayerCheck = 1
else
	$ULSU_4L_LayerCheck = 0
fi
$ULSU_4L_RadioCheck = 0
get FieldReplaceableUnit productData AIR.*64...*B41
if $nr_of_mos != 0
	$ULSU_4L_RadioCheck = 1
fi
$UL_SU_MIMO_CXC = 0
$UL_MU_MIMO_CXC = 0
get FeatureState=CXC4012493 featureState$ > $UL_SU_MIMO_CXC
get FeatureState=CXC4012330 featureState$ > $UL_MU_MIMO_CXC
if $GenCheck = Gen3or4 && $A_Cell_Present = 1 && $QSH_Cell_Present = 0 && $UL_SU_MIMO_CXC ~ 1 && $UL_MU_MIMO_CXC ~ 1 && $ULSU_4L_RadioCheck = 1 && $ULSU_4L_LayerCheck = 1
	UL_SU_MIMO_Config
fi

##   Addition of 26Q1 BSW Features 16 DRB per UE support(CXC4012831) and Advanced rate control scheduling(CXC4012839)
if $GenCheck = Gen3or4
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012831 FeatureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012839 FeatureState 1
fi

## Prioritized Call Queuing
## Optimized Safe-Mode Scheduling FDD & TDD (Coreset 0, TDD 5QI-1 AFR)
## Service Adaptive PDCP parameters*
## NR CA 5CC FDD* & NR CA 6CC 3T+3F*
if $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
	set SystemFunctions=1,Lm=1,FeatureState=CXC4012593 featureState 1
	set SystemFunctions=1,Lm=1,FeatureState=CXC4012856 featureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012869 featureState 1
	set GNBDUFunction=1,AdmissionControl=1,CallQueuing=1,CallQueuingProfile=Default queueRrcRequestMode 1
	scw RP3065:1
	set SystemFunctions=1,Lm=1,FeatureState=CXC4012682 featureState 1
    
    ## NRCA DL 6CC FDD (26Q1 Rollover)
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012761 featureState 1
    set NRCellDU= additionalPucchForCaEnabled 1
fi

## Enabling NR PCI Conflict Reporting (STA-00628371)
if $GenCheck = Gen2
    set PciHandling=1 pciConflictHandlingEnabled true
fi

// 26.Q2-v3 - activate Augmented Observablility Framework feature (CXC4012884)
if $GenCheck = Gen3or4
    set CXC4012884 featureState 1
fi

// 26.Q2-v4 - Corset0 for TDD
// 26.Q2-v5 - add RC926:1 as WA for  Intra-gnb Prep failures
if $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
    scw RP3065:1,RC926:1
fi

"""],
            'FDD': ["""
####:---> N71 (N600) and/or  N2 (N1900) and/or  N4 (N2100)<---:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4012424 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012324 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012800 featureState 1

####:-------------------> N71 (N600) and/or N2 (N1900) and/or N4 (N2100)<-------------------:####

##    25Q2-v3 - SCs ported from 25Q1 FB and added back RP2625 for Gen2 BB only
if $GenCheck = Gen2
    scw RP2625:1
fi

##    Short term fix for BoCS. Long term solution targetted for 26Q1
scw RC960:1

"""],
            'TDD': ["""
####:-------------------> N41 (N2500) <-------------------:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4012272 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012330 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012347 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012354 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012406 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012570 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012589 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012590 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012510 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012596 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012634 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012832 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012795 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012781 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012782 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012710 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012749 featureState 1

set GNBDUFunction=1,UeCC=1,DlBeamOptProfile=1,DlBeamOptProfileUeCfg=Base pdcchBeamOptMode 3
set NRCellDU=A.* maxPf3Resources 4
set NRCellDU=A pdcchLaBfGainFraction 75

#################################// Added - Pre-req to check if the Q1 BWP feature enhancement is set or not for SC RP1869:0.
get BWPSetUeCfg=2 bwpSwitchingFilterRelaxation$ > $BWPact
if $BWPact ~ false
	scw RP1869:0
fi

#################################// 24.Q4-v2 - 2-symbol PDCCH activation
get FieldReplaceableUnit productData AIR.*64.*B41
if $nr_of_mos != 0
	scw RP2508:1
fi

"""],

            'TMO_26_Q3': {
                'ALL': ["""scw RC554:200,RC555:480,PP166:0"""],
                'FDD': ["""scw RP1672:3"""],
                'TDD': ["""scw RP2624:6,RP2572:0"""],
            },
            'TMO_26_Q2': {
                'ALL': [""""""],
                'FDD': ["""scw RP1672:3,RC554:200,RC555:480,PP166:0"""],
                'TDD': ["""scw RP2624:3,RP2572:0,RC554:200,RC555:480,PP166:0"""],
            },
            'TMO_26_Q1': {
                'ALL': [""""""],
                'FDD': ["""scw RP1672:3,RC554:200,RC555:480,PP166:0"""],
                'TDD': ["""scw RP2624:3,RP2572:0,RC554:200,RC555:480,PP166:0"""],
            },
            'TMO_25_Q4': {
                'ALL': [""""""],
                'FDD': ["""
##    Coreset0 handling SP 12
pr NRCellDU=[QS]
$CoreSetSP12_qs_count = $nr_of_mos
if $CoreSetSP12_qs_count = 0
    scw RP2624:6,RP2830:3,RP2928:3,RP2927:4,RP2831:5
fi

##    Coreset0 handling SP 13
pr NRCellDU=[QS]
$CoreSetSP13_qs_count = $nr_of_mos
if $GenCheck = Gen3or4 && $CoreSetSP13_qs_count = 0
    scw RP3065:1,RP3067:5
fi

scw RP2624:3,RP2572:0,RP1459:4,RP1545:4,RC554:200,RC555:480,PP166:0
                """],
                'TDD': [""""""],
            },
            'TMO_25_Q3': {
                'ALL': [""""""],
                'FDD': [""""""],
                'TDD': ["""scw RP2624:3,RP2572:0,RP1459:4,RP1545:4,RC554:200,RC555:480,RP1810:2"""],
            },
        }
        lines = []
        if script_type.startswith('LTE'):
            lines += lte_dict['ALL'] + lte_dict[script_type[-3:]] + lte_dict[sw]['ALL'] + lte_dict[sw][script_type[-3:]]
        elif script_type.startswith('NR'):
            lines += nr_dict['ALL'] + nr_dict[script_type[-3:]] + nr_dict[sw]['ALL'] + nr_dict[sw][script_type[-3:]]
        elif script_type.startswith('LTE_Logical'):
            return lte_dict['Logical']
        return [F'####:----------------> Feature & System Constant <----------------:####', 'scg'] + lines + ['scg', '']

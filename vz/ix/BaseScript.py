from .BaseUSID import BaseUSID

from xml.dom.minidom import Document
import numpy as np
import copy
import os
import sys
import re
import json
import csv


class BaseScript:
    def __init__(self, usid: BaseUSID, node: str):
        self.usid = usid
        self.node = node
        self.site = None
        self.site_dict = dict

        self.log = self.usid.log
        self.set_client_db()
        self.sc_name = self.__class__.__name__ + '_' + self.node
        self.script = {'txt': [], 'csv': {}, 'xml': []}
        self.set_node_site_and_para_for_dcgk()


    def set_client_db(self):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "___.settings")
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        # from vz.models import MoAttribute, MoRelation, MoName, MoDetail
        # self.mo_attr = {_.moc: _.attribute for _ in MoAttribute.objects.filter(software=self.usid.client.software)}
        # self.MoRelation = MoRelation

        # self.MoName = MoName
        # self.MoDetail = MoDetail
        self.motype = 'default'

    def set_node_site_and_para_for_dcgk(self):
        self.site_dict = self.usid.site_dict.get(self.node, {})
        print(self.site_dict)
        # self.site = self.usid.sites.get(F'site_{self.node}')

        # self.me = self.usid.enodeb.get(self.node, {}).get('me', self.usid.gnodeb.get(self.node, {}).get('me', None))
        # self.eq_flag = self.usid.enodeb.get(self.node, {}).get('equ_change', self.usid.gnodeb.get(self.node, {}).get('equ_change', False))
        # if self.eq_flag is None: self.eq_flag = True
        # self.no_eq_change_with_dcgk_flag = self.eq_flag is False and self.site is not None
        # sc_name = '_'.join(self.__class__.__name__.split('_')[1:]) + '_' + self.node
        # self.relative_path = {
        #     'txt': ['script', self.node, F'{sc_name}.txt'],
        #     'csv': ['script', self.node, F'{sc_name}.csv'],
        #     'xml': ['script', self.node, F'{sc_name}.xml']
        # }



    def create_script_from_mo_dict(self):
        pass
        # for mo_fdn in self.mo_dict:
        #     self.script['csv'].extend(self.cmedit_list_form_dict('csv', mo_fdn, self.mo_dict.get(mo_fdn, {})))
        #     self.script['xml'].extend(self.cmedit_list_form_dict('xml', mo_fdn, self.mo_dict.get(mo_fdn, {})))

    @staticmethod
    def write_csv_script(*, csv_dict: dict, file_name: str) -> None:
        """ : rtype: None """
        with open(file_name, 'w', newline='') as csvfile:
            for r in csv_dict.keys():
                csvfile.write(F'@{r}\n')
                fieldnames = csv_dict[r]['fieldnames'].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                if len(csv_dict[r]) == 1:
                    writer.writerow(csv_dict[r]['fieldnames'])
                else:
                    for rr in csv_dict[r].keys():
                        if rr == 'fieldnames': continue
                        writer.writerow(csv_dict[r][rr])

    def write_script_file(self) -> None:
        """ :rtype: None """
        for sc in self.script.keys():
            if len(self.script[sc]) == 0: continue
            script_file = os.path.join(self.usid.base_dir, 'script', self.node, F'{self.sc_name}.{sc}')
            if not os.path.exists(os.path.dirname(script_file)): os.makedirs(os.path.dirname(script_file))
            if sc == 'csv':
                self.write_csv_script(csv_dict=self.script[sc], file_name=script_file)
            else:
                with open(script_file, 'w') as f:
                    f.write('\n'.join(self.script[sc]))
            self.script[sc] = []

    def special_formate_scripts(self):
        pass

    def create_msg(self):
        pass

    def run(self):
        self.set_client_db()
        self.create_msg()
        self.create_script_from_mo_dict()
        self.write_script_file()
        self.special_formate_scripts()

from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base
from . import tmo_debug_csv


class C08_lte_04_ENodeBPara(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0 or (self.enbdata['BBChange'] is False and self.enbdata['ENodeBFunction'] is not None): return
        self.reconfig_ap_file_path_to_remote()
        self.csv_enabled = self.usid.debug_csv
        self.script_list.extend([self.ap_rcp_msg_cap(), self.create_rpc_msg(), self.rcp_msg_close()])

    def create_rpc_msg(self):
        self.motype = 'Lrat'
        doc, config = self.main_rcp_msg_start(msg_id='enodeb_para')
        me_mo = self.mo_add_form_dict_xml({'managedElementId': self.node}, 'ManagedElement')
        config.appendChild(me_mo)
        enb_mo = self.mo_add_form_dict_xml({'eNodeBFunctionId': 1}, 'ENodeBFunction')
        me_mo.appendChild(enb_mo)
        if self.csv_enabled:
            tmo_debug_csv.track_mo(self, mo_name=F'ManagedElement={self.node}', moid=None, final={'managedElementId': self.node},
                                   default_source=self.__class__.__name__)
            tmo_debug_csv.track_mo(self, mo_name='ENodeBFunction=1', moid=None, final={'eNodeBFunctionId': 1}, default_source=self.__class__.__name__)
        self.csv_root_ldn = 'ENodeBFunction=1'
        tag = 'eNBMO'
        parent = 'ENodeBFunction'
        parent_str = '' if self.enbdata.get("ENodeBFunction") is None else self.enbdata.get("ENodeBFunction")
        children = self.MoRelation.objects.filter(parent=parent, tag=tag, software=self.usid.client.software)
        for child in children:
            mos = self.log_append_child_tags(moc=child.child, tag=tag, parent_str=parent_str, pre_site=self.enbdata.get("postsite"))
            for mo in mos: enb_mo.appendChild(mo)
        return doc
    

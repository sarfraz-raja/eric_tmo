import copy
from os import remove

from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C30_lte_30_post_para(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0: return
        if len(self.enbdata) == 0 or (self.enbdata['BBChange'] is False and self.enbdata['ENodeBFunction'] is not None): return
        self.reconfig_ap_file_path_to_remote()
        self.script_list.extend([self.ap_rcp_msg_cap(), self.create_rpc_msg(), self.rcp_msg_close()])

    def create_rpc_msg(self):
        self.motype = 'Lrat'

    def enb_post_parameter_update(self):
        # doc, config = self.main_rcp_msg_start(msg_id='ENodeBFunction')
        # me_mo = self.mo_add_form_dict_xml(para_dict={'managedElementId': self.node}, moname='ManagedElement')
        # config.appendChild(me_mo)
        if self.enbdata.get("ENodeBFunction") is None: return
        # ENodeBFunction
        enb_ldn = F'ManagedElement={self.node},ENodeBFunction=1'
        enb_dict = {'managedElementId': self.node, 'ENodeBFunction': {'eNodeBFunctionId': '1'}}
        remove_dict = {
            'ENodeBFunction': ['eNBId', 'eNodeBPlmnId', 'sctpRef', 'upIpAddressRef']
        }
        # ENodeBFunction
        moc = 'ENodeBFunction'
        child_dict, _ = self.get_mo_dict_for_id_tag('ENodeBFunction', '1', self.node if self.site else None)
        child_dict.update({
            'eNodeBFunctionId': '1',
            'eNBId': self.enbdata['nodeid'],
            'eNodeBPlmnId': self.enbdata['plmnlist'],
            'sctpRef': 'Transport=1,SctpEndpoint=LTE',
            'upIpAddressRef': F'Transport=1,Router={self.enbdata["lte"]},InterfaceIPv4={self.enbdata["lte_interface"]},AddressIPv4=1'
        })
        if moc in remove_dict.keys():
            for para in remove_dict[moc]: child_dict.pop(para, None)
        self.mo_dict[enb_ldn] = copy.deepcopy(enb_dict)
        self.mo_dict[enb_ldn][moc] = copy.deepcopy(child_dict)
        # ENodeBFunction - Child MOs
        tag = 'eNBMO'
        parent = 'ENodeBFunction'
        parent_str = self.enbdata.get("ENodeBFunction")
        children = self.MoRelation.objects.filter(parent=parent, tag=tag, software=self.usid.client.software)
        for child in children:
            mos = self.log_append_child_tags(moc=child.child, tag=tag, parent_str=parent_str, pre_site=self.enbdata.get("postsite"))
            for mo in mos: enb_mo.appendChild(mo)

        # me_mo.appendChild(self.mo_add_form_dict_xml(tmp_dict, 'ENodeBFunction'))
        # return doc

    def log_append_child_tags(self, moc, tag, parent_str='', pre_site=''):
        ret_mos = []
        site = self.usid.sites.get(F'site_{pre_site}')
        mos = site.find_mo_ending_with_parent_str(moc, parent_str) if site and parent_str != '' else []
        if len(mos) > 0:
            for mo in mos:
                mo_attrs_db = {self.get_moc_id(moc): '1'}
                mo_attrs_db.update(self.get_db_attributes(self.get_end_moc(mo)))
                mo_attrs_site = site.get_mo_attr_str(mo)
                for key in mo_attrs_db: mo_attrs_db[key] = mo_attrs_site.get(key, mo_attrs_db[key])
                moc_tag = self.get_end_moc(mo)
                ret_mo = self.mo_add_form_dict_xml(mo_attrs_db, moc_tag)
                for children in self.MoRelation.objects.filter(parent=moc, tag=tag, software=self.usid.client.software):
                    for child in self.log_append_child_tags(children.child, tag, mo, pre_site):
                        ret_mo.appendChild(child)
                ret_mos.append(ret_mo)
        else:
            ret_mos.extend(self.db_append_child_tags(moc, tag))
        return ret_mos
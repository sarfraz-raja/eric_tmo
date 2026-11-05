from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C08_lte_01_ENodeBFunction(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        if len(self.enbdata) == 0 or (self.enbdata['BBChange'] is False and self.enbdata['ENodeBFunction'] is not None): return
        self.reconfig_ap_file_path_to_remote()
        self.script_list.extend([self.ap_rcp_msg_cap(), self.create_rpc_msg(), self.rcp_msg_close()])

    def create_rpc_msg(self):
        self.motype = 'Lrat'
        doc, config = self.main_rcp_msg_start(msg_id='ENodeBFunction')
        me_mo = self.mo_add_form_dict_xml(para_dict={'managedElementId': self.node}, moname='ManagedElement')
        config.appendChild(me_mo)
        tmp_dict, _ = self.get_mo_dict_for_id_tag('ENodeBFunction', '1', self.node if self.site else None)
        tmp_dict.update({
            'eNodeBFunctionId': '1',
            'eNBId': self.enbdata['nodeid'],
            'eNodeBPlmnId': self.enbdata['plmnlist'],
            'sctpRef': 'Transport=1,SctpEndpoint=LTE',
            'upIpAddressRef': F'Transport=1,Router={self.enbdata["lte"]},InterfaceIPv4={self.enbdata["lte_interface"]},AddressIPv4=1'
        })
        me_mo.appendChild(self.mo_add_form_dict_xml(tmp_dict, 'ENodeBFunction'))
        return doc

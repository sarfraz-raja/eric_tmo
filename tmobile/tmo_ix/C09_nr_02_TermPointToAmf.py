from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C09_nr_02_TermPointToAmf(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0 or (self.gnbdata['BBChange'] is False and self.gnbdata['GNBDUFunction'] is not None): return
        self.reconfig_ap_file_path_to_remote()
        self.script_list.extend([self.ap_rcp_msg_cap(), self.create_rpc_msg(), self.rcp_msg_close()])

    def create_rpc_msg(self):
        self.motype = 'GNBCUCP'
        doc, config1 = self.main_rcp_msg_start(msg_id='TermPointToAmf')
        temp_dict = {'managedElementId': self.node, 'GNBCUCPFunction': {'gNBCUCPFunctionId': '1', 'TermPointToAmf': []}}
        if self.gnbdata.get('GNBDUFunction') is None:
            for term_point_amf in self.usid.client.amfpool.termpointtoamf_set.all():
                tmp_dict_1 = {'termPointToAmfId': term_point_amf.termPointToAmfId, 'administrativeState': '1 (UNLOCKED)',
                              'ipv4Address1': term_point_amf.ipv4Address1, 'ipv4Address2': term_point_amf.ipv4Address2,
                              'ipv6Address1': term_point_amf.ipv6Address1, 'ipv6Address2': term_point_amf.ipv6Address2,
                              'defaultAmf': term_point_amf.defaultAmf}
                temp_dict['GNBCUCPFunction']['TermPointToAmf'].append(tmp_dict_1)
        else:
            mos = self.site.find_mo_ending_with_parent_str('TermPointToAmf', '')
            for mo in mos:
                mo_data = self.mo_para_db_dict(mo, self.site)
                temp_dict['GNBCUCPFunction']['TermPointToAmf'].append(mo_data)
        config1.appendChild(self.mo_add_form_dict_xml(temp_dict, 'ManagedElement'))
        return doc

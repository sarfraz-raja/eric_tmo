from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C08_lte_02_TermPointToMme(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0 or (self.enbdata['BBChange'] is False and self.enbdata['ENodeBFunction'] is not None): return
        self.reconfig_ap_file_path_to_remote()
        self.script_list.extend([self.ap_rcp_msg_cap(), self.create_rpc_msg(), self.rcp_msg_close()])

    def create_rpc_msg(self):
        self.motype = 'Lrat'
        if self.usid.df_enb_cell.loc[(self.usid.df_enb_cell.postsite == self.node) &
                                     self.usid.df_enb_cell.celltype.isin(['IOT'])].shape[0] > 0: iot_mme = True
        else: iot_mme = False

        doc, config = self.main_rcp_msg_start(msg_id='mme')
        temp_dict = {'managedElementId': self.node, 'ENodeBFunction': {'eNodeBFunctionId': '1', 'TermPointToMme': []}}
        if self.enbdata.get('ENodeBFunction') is None:
            for term_point_mme in self.usid.client.mmepool.termpointtomme_set.all():
                if (not iot_mme) and (term_point_mme.mmeSupportNbIoT == 'true') and (term_point_mme.mmeSupportLegacyLte == 'false'): continue
                tmp_dict_1 = {'termPointToMmeId': term_point_mme.termPointToMmeId, 'administrativeState': '1 (UNLOCKED)',
                              'ipAddress1': term_point_mme.ipAddress1, 'ipAddress2': term_point_mme.ipAddress2,
                              'ipv6Address1': term_point_mme.ipv6Address1, 'ipv6Address2': term_point_mme.ipv6Address2,
                              'mmeSupportNbIoT': term_point_mme.mmeSupportNbIoT, 'mmeSupportLegacyLte': term_point_mme.mmeSupportLegacyLte}
                temp_dict['ENodeBFunction']['TermPointToMme'].append(tmp_dict_1)
        else:
            mos = self.site.find_mo_ending_with_parent_str('TermPointToMme', '')
            for mo in mos: temp_dict['ENodeBFunction']['TermPointToMme'].append(self.mo_para_db_dict(mo, self.site))
        config.appendChild(self.mo_add_form_dict_xml(temp_dict, 'ManagedElement'))
        return doc

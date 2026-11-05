from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C08_lte_03_eNodeBMOs(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        if len(self.enbdata) == 0: return
        self.reconfig_ap_file_path_to_remote()
        self.dcgk_flag = None if self.enbdata.get('BBChange', True) else False
        self.script_list = [self.ap_rcp_msg_cap(), self.create_rpc_msg(), self.rcp_msg_close()]

    def create_rpc_msg(self):
        self.motype = 'Lrat'
        doc, config = self.main_rcp_msg_start(msg_id='enodeb_mos')
        me_mo = self.mo_add_form_dict_xml({'managedElementId': self.node}, 'ManagedElement')
        config.appendChild(me_mo)
        enb_mo = self.mo_add_form_dict_xml({'eNodeBFunctionId': 1, 'allowMocnCellLevelCommonTac': 'true'}, 'ENodeBFunction')
        me_mo.appendChild(enb_mo)
        # AirIfLoadProfile
        for mo in self.union_of_mo_cosite_create_xml_script(moc='AirIfLoadProfile'): enb_mo.appendChild(mo)
        # Relations & External MOs
        for mo_r in self.eutran_network(): enb_mo.appendChild(mo_r)
        for mo_r in self.gutra_network(): enb_mo.appendChild(mo_r)
        for mo_r in self.utran_network(): enb_mo.appendChild(mo_r)
        for mo_r in self.geran_network(): enb_mo.appendChild(mo_r)
        return doc

    def eutran_network(self):
        # --- EUtraNetwork ---> EUtranFrequency ---
        nw_mo = self.mo_add_form_dict_xml({'eUtraNetworkId': self.enbdata.get('EUtraNetwork')}, 'EUtraNetwork')
        nw_ldn = F'ENodeBFunction=1,EUtraNetwork={self.enbdata.get("EUtraNetwork")}'
        for _, row in self.usid.df_enb_ef.loc[(self.usid.df_enb_ef.postsite == self.node) & (self.usid.df_enb_ef.flag != self.dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('EUtranFrequency', row.postsite, row.fdn)
            temp_dict.update({'eUtranFrequencyId': row.freqid, 'arfcnValueEUtranDl': row.earfcndl})
            nw_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'EUtranFrequency'))

        # --- EUtraNetwork ---> ExternalENodeBFunction, TermPointToENB, ExternalEUtranCellFDD, ExternalEUtranCellTDD ---
        df_enx = self.usid.df_enb_ex.loc[(self.usid.df_enb_ex.postsite == self.node) & (self.usid.df_enb_ex.flag != self.dcgk_flag)]
        df_fdd = self.usid.df_enb_ec.loc[(self.usid.df_enb_ec.postsite == self.node) & (self.usid.df_enb_ec.flag != self.dcgk_flag)]
        for xid in set(list(df_enx.xid.unique()) + list(df_fdd.xid.unique())):
            if df_enx.loc[df_enx.xid == xid].shape[0] > 0:
                row_ext_enb = df_enx.loc[df_enx.xid == xid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalENodeBFunction', row_ext_enb.postsite, row_ext_enb.fdn)
                temp_dict.update({'externalENodeBFunctionId': row_ext_enb.xid,
                                  'eNBId': row_ext_enb.enbid,
                                  'eNodeBPlmnId': row_ext_enb.plmn})
                ext_mo = self.mo_add_form_dict_xml(temp_dict, 'ExternalENodeBFunction')
                if not (row_ext_enb.x2id is None):
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('TermPointToENB', row_ext_enb.postsite, row_ext_enb.x2fdn)
                    temp_dict.update({'termPointToENBId': row_ext_enb.x2id})
                    if row_ext_enb.ipv4 is not None: temp_dict.update({'ipAddress': row_ext_enb.ipv4})
                    ext_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'TermPointToENB'))
            else:
                ext_mo = self.mo_add_form_dict_xml({'externalENodeBFunctionId': xid}, 'ExternalENodeBFunction')
            for _, row in (df_fdd.loc[df_fdd.xid == xid]).iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn(F'ExternalEUtranCell{row.celltype}', row.postsite, row.fdn)
                temp_dict.update({
                    F'externalEUtranCell{row.celltype}Id': row.xcellid,
                    'localCellId': row.cellid, 'tac': row.tac,
                    'physicalLayerCellIdGroup': int(row.pci) // 3, 'physicalLayerSubCellId': int(row.pci) % 3,
                    'eutranFrequencyRef': F'{nw_ldn},EUtranFrequency={row.freqid}',
                })
                ext_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, F'ExternalEUtranCell{row.celltype}'))
            nw_mo.appendChild(ext_mo)
        return [nw_mo]

    def gutra_network(self):
        nw_mo = self.mo_add_form_dict_xml({'gUtraNetworkId': self.enbdata.get('GUtraNetwork')}, 'GUtraNetwork')
        # ---GUtraNetwork---
        df_nrx = self.usid.df_enb_nx.loc[(self.usid.df_enb_nx.postsite == self.node) & (self.usid.df_enb_nx.flag != self.dcgk_flag)]
        df_nrc = self.usid.df_enb_nc.loc[(self.usid.df_enb_nc.postsite == self.node) & (self.usid.df_enb_nc.flag != self.dcgk_flag)]
        nw_ldn = F'ENodeBFunction=1,GUtraNetwork={self.enbdata.get("GUtraNetwork")}'
        # GUtranSyncSignalFrequency
        for _, row in self.usid.df_enb_nf.loc[(self.usid.df_enb_nf.postsite == self.node) & (self.usid.df_enb_nf.flag != self.dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GUtranSyncSignalFrequency', row.postsite, row.fdn)
            temp_dict.update({'gUtranSyncSignalFrequencyId': row.freqid,
                              'arfcn': row.arfcn,
                              'smtcScs': row.smtcScs,
                              'smtcPeriodicity': row.smtcPeriodicity,
                              'smtcOffset': row.smtcOffset,
                              'smtcDuration': row.smtcDuration})
            nw_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'GUtranSyncSignalFrequency'))
        # ExternalGNodeBFunction, TermPointToGNB, ExternalGUtranCell
        for xid in set(list(df_nrx.xid.unique()) + list(df_nrc.xid.unique())):
            if df_nrx.loc[df_nrx.xid == xid].shape[0] > 0:
                row = df_nrx.loc[df_nrx.xid == xid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalGNodeBFunction', row.postsite, row.fdn)
                temp_dict.update({'externalGNodeBFunctionId': xid,
                                  'gNodeBId': row.gnbid,
                                  'gNodeBIdLength': row.gnblen,
                                  'gNodeBPlmnId': row.plmn})
                ext_mo = self.mo_add_form_dict_xml(temp_dict, 'ExternalGNodeBFunction')
                if row.x2id is not None:
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('TermPointToGNB', row.postsite, row.x2fdn)
                    temp_dict.update({'termPointToGNBId': row.x2id,
                                      'ipAddress': row.ipv4,
                                      'ipv6Address': row.xt_ipv6,
                                      'domainName': row.xt_domain})
                    ext_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'TermPointToGNB'))
            else:
                ext_mo = self.mo_add_form_dict_xml({'externalGNodeBFunctionId': xid}, 'ExternalGNodeBFunction')
            for _, row in df_nrc.loc[df_nrc.xid == xid].iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalGUtranCell', row.postsite, row.fdn)
                temp_dict.update({'externalGUtranCellId': row.xcellid,
                                  'localCellId': row.cellid,
                                  'isRemoveAllowed': row.israllowed,
                                  'absSubFrameOffset': row.abssub,
                                  'absTimeOffset': row.abstime,
                                  'physicalLayerCellIdGroup': row.pci // 3, 'physicalLayerSubCellId': row.pci % 3,
                                  'gUtranSyncSignalFrequencyRef': F'{nw_ldn},GUtranSyncSignalFrequency={row.freqid}'})
                ext_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'ExternalGUtranCell'))
            nw_mo.appendChild(ext_mo)
        return [nw_mo]

    def utran_network(self):
        nw_ldn = F'ENodeBFunction=1,UtraNetwork={self.enbdata.get("UtraNetwork")}'
        nw_mo = self.mo_add_form_dict_xml({'utraNetworkId': self.enbdata["UtraNetwork"]}, 'UtraNetwork')
        df_ufrq = self.usid.df_enb_uf.loc[(self.usid.df_enb_uf.postsite == self.node) & (self.usid.df_enb_uf.flag != self.dcgk_flag)]
        df_ufdd = self.usid.df_enb_uc.loc[(self.usid.df_enb_uc.postsite == self.node) & (self.usid.df_enb_uc.flag != self.dcgk_flag)]

        # --- UtraNetwork ---> UtranFrequency & ExternalUtranCellFDD ---
        for freqid in set(list(df_ufrq.freqid.unique()) + list(df_ufdd.freqid.unique())):
            if df_ufrq.loc[df_ufrq.freqid == freqid].shape[0] > 0:
                row_frq = df_ufrq.loc[df_ufrq.freqid == freqid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('UtranFrequency', row_frq.postsite, row_frq.fdn)
                temp_dict.update({'utranFrequencyId': row_frq.freqid,
                                  'arfcnValueUtranDl': row_frq.uarfcn})
                ufq_mo = self.mo_add_form_dict_xml(temp_dict, 'UtranFrequency')
            else:
                ufq_mo = self.mo_add_form_dict_xml({'utranFrequencyId': freqid}, 'UtranFrequency')
            for _, row in (df_ufdd.loc[df_ufdd.freqid == freqid]).iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalUtranCellFDD', row.postsite, row.fdn)
                temp_dict.update({'externalUtranCellFDDId': row.xcellid,
                                  'cellIdentity': row.cellid,
                                  'plmnIdentity': row.plmn,
                                  'lac': row.lac,
                                  'rac': row.rac,
                                  'physicalCellIdentity': row.pci})
                ufq_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'ExternalUtranCellFDD'))
            nw_mo.appendChild(ufq_mo)
        return [nw_mo]

    def geran_network(self):
        nw_ldn = F'ENodeBFunction=1,GeraNetwork={self.enbdata.get("GeraNetwork")}'
        nw_mo = self.mo_add_form_dict_xml({'geraNetworkId': self.enbdata.get('GeraNetwork')}, 'GeraNetwork')
        # GeranFreqGroup
        for _, row in self.usid.df_enb_gs.loc[(self.usid.df_enb_gs.postsite == self.node) & (self.usid.df_enb_gs.flag != self.dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GeranFreqGroup', row.postsite, row.fdn)
            temp_dict.update({'geranFreqGroupId': row.gfreqgid,
                              'frequencyGroupId': row.group})
            nw_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'GeranFreqGroup'))
        # GeranFrequency
        for _, row in self.usid.df_enb_gf.loc[(self.usid.df_enb_gf.postsite == self.node) & (self.usid.df_enb_gf.flag != self.dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GeranFrequency', row.postsite, row.fdn)
            temp_dict.update({'geranFrequencyId': row.freqid,
                              'arfcnValueGeranDl': row.bcch,
                              'bandIndicator': row.band,
                              'geranFreqGroupRef': F'{nw_ldn},GeranFreqGroup={row.gfreqgid}'})
            nw_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'GeranFrequency'))
        # ExternalGeranCell
        for _, row in self.usid.df_enb_gc.loc[(self.usid.df_enb_gc.postsite == self.node) & (self.usid.df_enb_gc.flag != self.dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalGeranCell', row.postsite, row.fdn)
            temp_dict.update({'externalGeranCellId': row.xcellid,
                              'ncc': row.ncc, 'bcc': row.bcc,
                              'cellIdentity': row.ci,
                              'plmnIdentity': row.plmn,
                              'lac': row.lac,
                              'geranFrequencyRef': F'{nw_ldn},GeranFrequency={row.freqid}'})
            nw_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'ExternalGeranCell'))
        return [nw_mo]

    def unlic_band_prof(self):
        # UnlicensedBandProfile
        mos = []
        if self.usid.df_enb_cell.loc[self.usid.df_enb_cell.freqband == '46'].shape[0] > 0:
            unlic_band_mo=[]
            if self.site:
                unlic_band_mo = self.site.find_mo_ending_with_parent_str('UnlicensedBandProfile', '.*EUtraNetwork=1')
            if len(unlic_band_mo) == 0:
                tmp_dict = {
                    'eUtraNetworkId': 1,
                    'UnlicensedBandProfile': {
                        'unlicensedBandProfileId': 1,
                        'unlicensedBandProfileList': [
                            {'channelCharacteristic': 'CHANNEL_ENABLED', 'maxUnlicensedTxPower': '210',
                             'unlicensedBand': 'BAND_46D', 'unlicensedEarfcn': 'EARFCN_52740'},
                            {'channelCharacteristic': 'CHANNEL_ENABLED', 'maxUnlicensedTxPower': '210',
                             'unlicensedBand': 'BAND_46D', 'unlicensedEarfcn': 'EARFCN_52940'},
                            {'channelCharacteristic': 'CHANNEL_ENABLED', 'maxUnlicensedTxPower': '210',
                             'unlicensedBand': 'BAND_46D', 'unlicensedEarfcn': 'EARFCN_53140'},
                            {'channelCharacteristic': 'CHANNEL_ENABLED', 'maxUnlicensedTxPower': '210',
                             'unlicensedBand': 'BAND_46D', 'unlicensedEarfcn': 'EARFCN_53340'},
                            {'channelCharacteristic': 'CHANNEL_ENABLED', 'maxUnlicensedTxPower': '210',
                             'unlicensedBand': 'BAND_46D', 'unlicensedEarfcn': 'EARFCN_53540'},
                        ]
                    }
                }
                mos.append(self.mo_add_form_dict_xml(tmp_dict, 'EUtraNetwork'))
        return mos

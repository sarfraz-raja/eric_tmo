from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class lte_03_eNodeBMOs_mos(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0: return
        self.motype = 'Lrat'
        self.dcgk_flag = None if self.enbdata.get('BBChange', True) else False
        self.write_backup_script_file(script_list=self.create_mos_msg())
        # self.script_list = self.create_mos_msg()

    def create_mos_msg(self):
        lines = []
        parent_mo = 'ENodeBFunction=1'
        lines.extend([F'set {parent_mo}$ allowMocnCellLevelCommonTac true', F''])
        # AirIfLoadProfile
        lines.extend(self.union_of_mo_cosite_create_mos_script(moname='AirIfLoadProfile', parentmo=parent_mo))

        lines.extend(self.eutra_network())
        lines.extend(self.gutra_network())
        lines.extend(self.utra_network())
        lines.extend(self.gera_network())
        return lines

    def eutra_network(self):
        lines = []
        nw_ldn = F'ENodeBFunction=1,EUtraNetwork={self.enbdata.get("EUtraNetwork")}'
        # --- EUtraNetwork ---> EUtranFrequency ---
        tmp_lines = []
        for _, row in self.usid.df_enb_ef.loc[(self.usid.df_enb_ef.postsite == self.node) &
                                              (self.usid.df_enb_ef.flag != self.dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('EUtranFrequency', row.postsite, row.fdn)
            temp_dict.update({'eUtranFrequencyId': row.freqid, 'arfcnValueEUtranDl': row.earfcndl})
            tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'EUtranFrequency', F'{nw_ldn},EUtranFrequency={row.freqid}'))
        if len(tmp_lines) > 0: lines = lines + ['####:----------------> EUtranFrequency <----------------:####'] + tmp_lines

        # --- EUtraNetwork ---> ExternalENodeBFunction, TermPointToENB, ExternalEUtranCellFDD, ExternalEUtranCellTDD ---
        df_enx = self.usid.df_enb_ex.loc[(self.usid.df_enb_ex.postsite == self.node) & (self.usid.df_enb_ex.flag != self.dcgk_flag)]
        df_fdd = self.usid.df_enb_ec.loc[(self.usid.df_enb_ec.postsite == self.node) & (self.usid.df_enb_ec.flag != self.dcgk_flag)]
        tmp_lines = []
        for xid in set(list(df_enx.xid.unique()) + list(df_fdd.xid.unique())):
            ldn = F'{nw_ldn},ExternalENodeBFunction={xid}'
            if df_enx.loc[df_enx.xid == xid].shape[0] > 0:
                row_ext_enb = df_enx.loc[df_enx.xid == xid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalENodeBFunction', row_ext_enb.postsite, row_ext_enb.fdn)
                temp_dict.update({'externalENodeBFunctionId': row_ext_enb.xid,
                                  'eNBId': row_ext_enb.enbid,
                                  'eNodeBPlmnId': row_ext_enb.plmn})
                tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'ExternalENodeBFunction', ldn))
                if row_ext_enb.x2id is not None:
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('TermPointToENB', row_ext_enb.postsite, row_ext_enb.x2fdn)
                    temp_dict.update({'termPointToENBId': row_ext_enb.x2id})
                    if row_ext_enb.ipv4 is not None: temp_dict.update({'ipAddress': row_ext_enb.ipv4})
                    tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'TermPointToENB', F'{ldn},TermPointToENB={row_ext_enb.x2id}'))
            for _, row in df_fdd.loc[df_fdd.xid == xid].iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn(F'ExternalEUtranCell{row.celltype}', row.postsite, row.fdn)
                temp_dict.update({F'externalEUtranCell{row.celltype}Id': row.xcellid,
                                  'localCellId': row.cellid, 'tac': row.tac,
                                  'physicalLayerCellIdGroup': int(row.pci) // 3, 'physicalLayerSubCellId': int(row.pci) % 3,
                                  'eutranFrequencyRef': F'{nw_ldn},EUtranFrequency={row.freqid}'})
                tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, F'ExternalEUtranCell{row.celltype}',
                                                                  F'{ldn},ExternalEUtranCell{row.celltype}={row.xcellid}'))
        if len(tmp_lines) > 0:
            lines = lines + ['####:----------------> ExternalENodeBFunction, TermPointToENB, ExternalEUtranCellFDD & '
                             'ExternalEUtranCellTDD <----------------:####'] + tmp_lines

        if len(lines) > 0:
            lines = ['####:----------------> EUtraNetwork <----------------:####', F'crn {nw_ldn}', 'end', ''] + lines

        return lines + ['', '']

    def gutra_network(self):
        lines = []
        nw_ldn = F'ENodeBFunction=1,GUtraNetwork={self.enbdata.get("GUtraNetwork")}'
        # ---GUtraNetwork---
        df_nrx = self.usid.df_enb_nx.loc[(self.usid.df_enb_nx.postsite == self.node) & (self.usid.df_enb_nx.flag != self.dcgk_flag)]
        df_nrc = self.usid.df_enb_nc.loc[(self.usid.df_enb_nc.postsite == self.node) & (self.usid.df_enb_nc.flag != self.dcgk_flag)]
        # GUtranSyncSignalFrequency
        tmp_lines = []
        for _, row in self.usid.df_enb_nf.loc[(self.usid.df_enb_nf.postsite == self.node) &
                                              (self.usid.df_enb_nf.flag != self.dcgk_flag)].iterrows():
            mo_ldn = F'{nw_ldn},GUtranSyncSignalFrequency={row.freqid}'
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GUtranSyncSignalFrequency', row.postsite, row.fdn)
            temp_dict.update({'gUtranSyncSignalFrequencyId': row.freqid,
                              'arfcn': row.arfcn,
                              'smtcScs': row.smtcScs,
                              'smtcPeriodicity': row.smtcPeriodicity,
                              'smtcOffset': row.smtcOffset,
                              'smtcDuration': row.smtcDuration})
            tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'GUtranSyncSignalFrequency', mo_ldn))
        if len(tmp_lines) > 0: lines = lines + ['####:----------------> GUtranSyncSignalFrequency <----------------:####'] + tmp_lines
        # ExternalGNodeBFunction
        tmp_lines = []
        for xid in set(list(df_nrx.xid.unique()) + list(df_nrc.xid.unique())):
            ldn = F'{nw_ldn},ExternalGNodeBFunction={xid}'
            if df_nrx.loc[df_nrx.xid == xid].shape[0] > 0:
                row = df_nrx.loc[df_nrx.xid == xid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalGNodeBFunction', row.postsite, row.fdn)
                temp_dict.update({'externalGNodeBFunctionId': xid,
                                  'gNodeBId': row.gnbid,
                                  'gNodeBIdLength': row.gnblen,
                                  'gNodeBPlmnId': row.plmn})
                tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'ExternalGNodeBFunction', ldn))
                if row.x2id is not None:
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('TermPointToGNB', row.postsite, row.x2fdn)
                    temp_dict.update({'termPointToGNBId': row.x2id,
                                      'ipAddress': row.ipv4,
                                      'ipv6Address': row.xt_ipv6,
                                      'domainName': row.xt_domain})
                    tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'TermPointToGNB', F'{ldn},TermPointToGNB={row.x2id}'))
            for _, row in df_nrc.loc[df_nrc.xid == xid].iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalGUtranCell', row.postsite, row.fdn)
                temp_dict.update({'externalGUtranCellId': row.xcellid,
                                  'localCellId': row.cellid,
                                  'isRemoveAllowed': row.israllowed,
                                  'absSubFrameOffset': row.abssub,
                                  'absTimeOffset': row.abstime,
                                  'physicalLayerCellIdGroup': row.pci // 3, 'physicalLayerSubCellId': row.pci % 3,
                                  'gUtranSyncSignalFrequencyRef': F'{nw_ldn},GUtranSyncSignalFrequency={row.freqid}'})
                tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'ExternalGUtranCell', F'{ldn},ExternalGUtranCell={row.xcellid}'))
        if len(tmp_lines) > 0:
            lines = lines + ['####:----------------> ExternalGNodeBFunction, TermPointToGNB & ExternalGUtranCell <----------------:####'] + tmp_lines
        if len(lines) > 0:
            lines = ['####:----------------> GUtraNetwork <----------------:####', F'crn {nw_ldn}', 'end', ''] + lines

        return lines + ['', '']

    def utra_network(self):
        lines = []
        nw_ldn = F'ENodeBFunction=1,UtraNetwork={self.enbdata.get("UtraNetwork")}'
        df_frq = self.usid.df_enb_uf.loc[(self.usid.df_enb_uf.postsite == self.node) & (self.usid.df_enb_uf.flag != self.dcgk_flag)]
        df_fdd = self.usid.df_enb_uc.loc[(self.usid.df_enb_uc.postsite == self.node) & (self.usid.df_enb_uc.flag != self.dcgk_flag)]
        # UtranFrequency & ExternalUtranCellFDD
        for freqid in set(list(df_frq.freqid.unique()) + list(df_fdd.freqid.unique())):
            ldn = F'{nw_ldn},UtranFrequency={freqid}'
            if df_frq.loc[df_frq.freqid == freqid].shape[0] > 0:
                row = df_frq.loc[df_frq.freqid == freqid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('UtranFrequency', row.postsite, row.fdn)
                temp_dict.update({'utranFrequencyId': row.freqid,
                                  'arfcnValueUtranDl': row.uarfcn})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'UtranFrequency', ldn))
            for _, row in df_fdd.loc[df_fdd.freqid == freqid].iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalUtranCellFDD', row.postsite, row.fdn)
                temp_dict.update({'externalUtranCellFDDId': row.xcellid,
                                  'cellIdentity': row.cellid,
                                  'plmnIdentity': row.plmn,
                                  'lac': row.lac,
                                  'rac': row.rac,
                                  'physicalCellIdentity': row.pci})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'ExternalUtranCellFDD', F'{ldn},ExternalUtranCellFDD={row.xcellid}'))
        if len(lines) > 0:
            lines = ['####:----------------> UtraNetwork <----------------:####', F'crn {nw_ldn}', 'end', ''] + lines

        return lines + ['', '']

    def gera_network(self):
        lines = []
        nw_ldn = F'ENodeBFunction=1,GeraNetwork={self.enbdata.get("GeraNetwork")}'
        tmp_lines = []
        for _, row in self.usid.df_enb_gs.loc[(self.usid.df_enb_gs.postsite == self.node) &
                                              (self.usid.df_enb_gs.flag != self.dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GeranFreqGroup', row.postsite, row.fdn)
            temp_dict.update({'geranFreqGroupId': row.gfreqgid,
                              'frequencyGroupId': row.group})
            tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'GeranFreqGroup', F'{nw_ldn},GeranFreqGroup={row.gfreqgid}'))
        if len(tmp_lines) > 0: lines = lines + ['####:----------------> GeranFreqGroup <----------------:####'] + tmp_lines

        tmp_lines = []
        for _, row in self.usid.df_enb_gf.loc[(self.usid.df_enb_gf.postsite == self.node) &
                                              (self.usid.df_enb_gf.flag != self.dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GeranFrequency', row.postsite, row.fdn)
            temp_dict.update({'geranFrequencyId': row.freqid,
                              'arfcnValueGeranDl': row.bcch,
                              'bandIndicator': row.band,
                              'geranFreqGroupRef': F'{nw_ldn},GeranFreqGroup={row.gfreqgid}'})
            tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'GeranFrequency', F'{nw_ldn},GeranFrequency={row.freqid}'))
        if len(tmp_lines) > 0: lines = lines + ['####:----------------> GeranFrequency <----------------:####'] + tmp_lines

        tmp_lines = []
        for _, row in self.usid.df_enb_gc.loc[(self.usid.df_enb_gc.postsite == self.node) &
                                              (self.usid.df_enb_gc.flag != self.dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalGeranCell', row.postsite, row.fdn)
            temp_dict.update({'externalGeranCellId': row.xcellid,
                              'ncc': row.ncc,
                              'bcc': row.bcc,
                              'cellIdentity': row.ci,
                              'plmnIdentity': row.plmn,
                              'lac': row.lac,
                              'geranFrequencyRef': F'{nw_ldn},GeranFrequency={row.freqid}'})
            tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'ExternalGeranCell', F'{nw_ldn},ExternalGeranCell={row.xcellid}'))
        if len(tmp_lines) > 0: lines = lines + ['####:----------------> ExternalGeranCell <----------------:####'] + tmp_lines

        if len(lines) > 0:
            lines = ['####:----------------> GeraNetwork <----------------:####', F'crn {nw_ldn}', 'end', ''] + lines

        return lines + ['', '']

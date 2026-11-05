from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class lte_07_Relations(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0: return
        self.motype = 'Lrat'
        self.script_list += self.gutra_relations_mos()
        self.script_list += self.geran_relations_mos()

    def gutra_relations_mos(self):
        lines = []
        nw_ldn = F'ENodeBFunction=1,GUtraNetwork={self.enbdata.get("GUtraNetwork")}'
        df_rel = self.usid.df_enb_nr.loc[self.usid.df_enb_nr.postsite == self.node]
        df_cell = self.usid.df_enb_ne.loc[self.usid.df_enb_ne.postsite == self.node]
        celltype_dict = {'FDD': 'EUtranCellFDD', 'FDDId': 'eUtranCellFDDId', 'TDD': 'EUtranCellTDD', 'TDDId': 'eUtranCellTDDId'}

        for _, row in self.usid.df_enb_cell.loc[(self.usid.df_enb_cell.postsite == self.node) &
                                                self.usid.df_enb_cell.celltype.isin(['FDD', 'TDD'])].iterrows():
            cell_ldn = F'ENodeBFunction=1,{celltype_dict.get(row.celltype)}={row.postcell}'
            dcgk_flag = None if row.addcell else False

            for relid in set(list(df_rel.loc[(df_rel.postcell == row.postcell) & (df_rel.flag != dcgk_flag)].relid.unique()) +
                             list(df_cell.loc[(df_cell.postcell == row.postcell) & (df_cell.flag != dcgk_flag)].relid.unique())):
                ldn = F'{cell_ldn},GUtranFreqRelation={relid}'
                if df_rel.loc[(df_rel.postcell == row.postcell) & (df_rel.relid == relid) & (df_rel.flag != dcgk_flag)].shape[0] > 0:
                    row_rel = df_rel.loc[(df_rel.postcell == row.postcell) & (df_rel.relid == relid) & (df_rel.flag != dcgk_flag)].iloc[0]
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GUtranFreqRelation', row_rel.presite, row_rel.fdn)
                    temp_dict.update({'gUtranFreqRelationId': row_rel.relid,
                                      'cellReselectionPriority': row_rel.creprio,
                                      'gUtranSyncSignalFrequencyRef': F'{nw_ldn},GUtranSyncSignalFrequency={row_rel.freqid}'})
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'GUtranFreqRelation', ldn))
                # ---GeranCellRelation---
                for _, row_c in df_cell.loc[(df_cell.postcell == row.postcell) & (df_cell.relid == relid) & (df_cell.flag != dcgk_flag)].iterrows():
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GUtranCellRelation', row_c.presite, row_c.fdn)
                    temp_dict.update({'gUtranCellRelationId': row_c.crelid, 'isRemoveAllowed': row_c.israllowed,
                                      'neighborCellRef': F'{nw_ldn},ExternalGNodeBFunction={row_c.xid},ExternalGUtranCell={row_c.xcellid}'})
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'GUtranCellRelation', F'{ldn},GUtranCellRelation={row_c.crelid}'))

        if len(lines) > 0:
            lines = [F'####:----------------> GUtranFreqRelation & GUtranCellRelation <----------------:####'] + lines + \
                    ['', '']
        return lines

    def geran_relations_mos(self):
        lines = []
        nw_ldn = F'ENodeBFunction=1,GeraNetwork={self.enbdata.get("GeraNetwork")}'
        df_rel = self.usid.df_enb_gr.loc[self.usid.df_enb_gr.postsite == self.node]
        df_cell = self.usid.df_enb_ge.loc[self.usid.df_enb_ge.postsite == self.node]
        celltype_dict = {'FDD': 'EUtranCellFDD', 'FDDId': 'eUtranCellFDDId', 'TDD': 'EUtranCellTDD', 'TDDId': 'eUtranCellTDDId'}

        for _, row in self.usid.df_enb_cell.loc[(self.usid.df_enb_cell.postsite == self.node) & self.usid.df_enb_cell.celltype.isin(['FDD', 'TDD'])].iterrows():
            cell_ldn = F'ENodeBFunction=1,{celltype_dict.get(row.celltype)}={row.postcell}'
            dcgk_flag = None if row.addcell else False
            # ---GeranFreqGroupRelation---
            for relid in set(list(df_rel.loc[(df_rel.postcell == row.postcell) & (df_rel.flag != dcgk_flag)].relid.unique()) +
                             list(df_cell.loc[(df_cell.postcell == row.postcell) & (df_cell.flag != dcgk_flag)].relid.unique())):
                ldn = F'{cell_ldn},GeranFreqGroupRelation={relid}'
                if df_rel.loc[(df_rel.postcell == row.postcell) & (df_rel.relid == relid) & (df_rel.flag != dcgk_flag)].shape[0] > 0:
                    row_rel = df_rel.loc[(df_rel.postcell == row.postcell) & (df_rel.relid == relid) & (df_rel.flag != dcgk_flag)].iloc[0]
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GeranFreqGroupRelation', row_rel.presite, row_rel.fdn)
                    temp_dict.update({'geranFreqGroupRelationId': row_rel.relid, 'cellReselectionPriority': row_rel.creprio,
                                      'geranFreqGroupRef': F'{nw_ldn},GeranFreqGroup={row_rel.gfreqgid}'})
                    if row_rel.fdn is None and self.usid.client.mname in self.market_dict.get("tri_la"):
                        temp_dict.update({'cellReselectionPriority': '0', 'csFallbackPrio': '7', 'csFallbackPrioEC': '7', 'nccPermitted': '11111111'})
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'GeranFreqGroupRelation', ldn))
                # ---GeranCellRelation---
                for _, row_cell in df_cell.loc[(df_cell.postcell == row.postcell) & (df_cell.relid == relid) & (df_cell.flag != dcgk_flag)].iterrows():
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GeranCellRelation', row_cell.presite, row_cell.fdn)
                    temp_dict.update({'geranCellRelationId': row_cell.crelid,
                                      'extGeranCellRef': F'{nw_ldn},ExternalGeranCell={row_cell.xcellid}'})
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'GeranCellRelation', F'{ldn},GeranCellRelation={row_cell.crelid}'))

        if len(lines) > 0:
            lines = [F'####:----------------> GeranFreqGroupRelation & GeranCellRelation <----------------:####'] + lines + \
                    ['', '']
        return lines

    def gutra_network(self):
        lines = []
        nw_ldn = F'ENodeBFunction=1,GUtraNetwork={self.enbdata.get("GUtraNetwork")}'
        dcgk_flag = 'all' if self.enbdata.get('BBChange', True) else 'log'
        # ---GUtraNetwork---
        df_nrx = self.usid.df_enb_nx.loc[(self.usid.df_enb_nx.postsite == self.node) & (self.usid.df_enb_nx.flag != dcgk_flag)]
        df_nrc = self.usid.df_enb_nc.loc[(self.usid.df_enb_nc.postsite == self.node) & (self.usid.df_enb_nc.flag != dcgk_flag)]

        # GUtranSyncSignalFrequency
        tmp_lines = []
        for _, row in self.usid.df_enb_nf.loc[(self.usid.df_enb_nf.postsite == self.node) & (self.usid.df_enb_nf.flag != dcgk_flag)].iterrows():
            mo_ldn = F'{nw_ldn},GUtranSyncSignalFrequency={row.freqid}'
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GUtranSyncSignalFrequency', row.postsite, row.fdn)
            temp_dict.update({'gUtranSyncSignalFrequencyId': row.freqid, 'arfcn': row.arfcn, 'smtcScs': row.smtcScs,
                              'smtcPeriodicity': row.smtcPeriodicity, 'smtcOffset': row.smtcOffset, 'smtcDuration': row.smtcDuration})
            tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'GUtranSyncSignalFrequency', mo_ldn))
        if len(tmp_lines) > 0: lines = lines + ['####:----------------> GUtranSyncSignalFrequency <----------------:####'] + tmp_lines
        # ExternalGNodeBFunction
        tmp_lines = []
        for xid in set(list(df_nrx.xid.unique()) + list(df_nrc.xid.unique())):
            ldn = F'{nw_ldn},ExternalGNodeBFunction={xid}'
            if df_nrx.loc[df_nrx.xid == xid].shape[0] > 0:
                row = df_nrx.loc[df_nrx.xid == xid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalGNodeBFunction', row.postsite, row.fdn)
                temp_dict.update({'externalGNodeBFunctionId': row.xid, 'gNodeBId': row.gnbid, 'gNodeBIdLength': row.gnblen, 'gNodeBPlmnId': row.plmn})
                tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'ExternalGNodeBFunction', ldn))
                if row.x2id is not None:
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('TermPointToGNB', row.postsite, row.x2fdn)
                    temp_dict.update({'termPointToGNBId': row.x2id, 'ipAddress': row.ipv4, 'ipv6Address': row.xt_ipv6, 'domainName': row.xt_domain})
                    tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'TermPointToGNB', F'{ldn},TermPointToGNB={row.x2id}'))
            for _, row in df_nrc.loc[df_nrc.xid == xid].iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalGUtranCell', row.postsite, row.fdn)
                temp_dict.update({'externalGUtranCellId': row.xcellid, 'localCellId': row.cellid, 'isRemoveAllowed': row.israllowed,
                                  'absSubFrameOffset': row.abssub, 'absTimeOffset': row.abstime,
                                  'physicalLayerCellIdGroup': row.pci // 3, 'physicalLayerSubCellId': row.pci % 3})
                tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'ExternalGUtranCell', F'{ldn},ExternalGUtranCell={row.xcellid}'))
        if len(tmp_lines) > 0:
            lines = lines + ['####:----------------> ExternalGNodeBFunction, TermPointToGNB & ExternalGUtranCell <----------------:####'] + tmp_lines
        # GUtraNetwork
        if len(lines) > 0:
            lines = ['####:----------------> GUtraNetwork <----------------:####', F'crn {nw_ldn}', 'end', ''] + lines + \
                    ['', '']

        return lines

    def geran_network(self):
        lines = []
        nw_ldn = F'ENodeBFunction=1,GeraNetwork={self.enbdata.get("GeraNetwork")}'
        dcgk_flag = 'all' if self.enbdata.get('BBChange', True) else 'log'
        # GeranFreqGroup
        tmp_lines = []
        for _, row in self.usid.df_enb_gs.loc[(self.usid.df_enb_gs.postsite == self.node) & (self.usid.df_enb_gs.flag != dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GeranFreqGroup', row.postsite, row.fdn)
            temp_dict.update({'geranFreqGroupId': row.gfreqgid, 'frequencyGroupId': row.group})
            tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'GeranFreqGroup', F'{nw_ldn},GeranFreqGroup={row.gfreqgid}'))
        if len(tmp_lines) > 0: lines = lines + ['####:----------------> GeranFreqGroup <----------------:####'] + tmp_lines

        # GeranFrequency
        tmp_lines = []
        for _, row in self.usid.df_enb_gf.loc[(self.usid.df_enb_gf.postsite == self.node) & (self.usid.df_enb_gf.flag != dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('GeranFrequency', row.postsite, row.fdn)
            temp_dict.update({'geranFrequencyId': row.freqid, 'arfcnValueGeranDl': row.bcch, 'bandIndicator': row.band,
                              'geranFreqGroupRef': F'{nw_ldn},GeranFreqGroup={row.gfreqgid}'})
            tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'GeranFrequency', F'{nw_ldn},GeranFrequency={row.freqid}'))
        if len(tmp_lines) > 0: lines = lines + ['####:----------------> GeranFrequency <----------------:####'] + tmp_lines

        # ExternalGeranCell
        tmp_lines = []
        for _, row in self.usid.df_enb_gc.loc[(self.usid.df_enb_gc.postsite == self.node) & (self.usid.df_enb_gc.flag != dcgk_flag)].iterrows():
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('ExternalGeranCell', row.postsite, row.fdn)
            temp_dict.update({'externalGeranCellId': row.xcellid, 'ncc': row.ncc, 'bcc': row.bcc,
                              'cellIdentity': row.ci, 'plmnIdentity': row.plmn, 'lac': row.lac,
                              'geranFrequencyRef': F'{nw_ldn},GeranFrequency={row.freqid}'})
            tmp_lines.extend(self.create_mos_script_from_dict(temp_dict, 'ExternalGeranCell', F'{nw_ldn},ExternalGeranCell={row.xcellid}'))
        if len(tmp_lines) > 0: lines = lines + ['####:----------------> ExternalGeranCell <----------------:####'] + tmp_lines

        # GeraNetwork
        if len(lines) > 0:
            lines = ['####:----------------> GeraNetwork <----------------:####', F'crn {nw_ldn}', 'end', ''] + lines

        return lines + ['', '']

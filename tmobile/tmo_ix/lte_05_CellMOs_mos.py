from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class lte_05_CellMOs_mos(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0: return
        self.motype = 'Lrat'
        self.write_backup_script_file(script_list=self.create_mos_msg())

    def create_mos_msg(self):
        lines = []
        tmp_celltype = {'FDD': 'EUtranCellFDD', 'FDDId': 'eUtranCellFDDId', 'TDD': 'EUtranCellTDD',
                        'TDDId': 'eUtranCellTDDId', 'IOT': 'NbIotCell', 'IOTId': 'NbIotCellId'}
        for _, row in self.usid.df_enb_cell.loc[self.usid.df_enb_cell.postsite == self.node].iterrows():
            if row.addcell:
                lines.extend([F'#############:- Create Cell {row.postcell} -:#############', ''])
                ecell_ldn = F'ENodeBFunction=1,{tmp_celltype.get(row.celltype)}={row.postcell}'
                temp_dict_cell = self.update_db_with_mo_for_siteid_and_fdn(tmp_celltype.get(row.celltype), row.presite, row.fdn)
                # ---SectorCarrier---
                if row.celltype in ['FDD', 'TDD']:
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('SectorCarrier', row.presite, row.scfdn)
                    temp_dict.update({
                        'sectorCarrierId': row.sc,
                        'configuredMaxTxPower': row.confpow,
                        'noOfRxAntennas': row.noofrx if str(row.noofrx) != '0' else '',
                        'noOfTxAntennas': row.nooftx if str(row.nooftx) != '0' else '',
                        'sectorFunctionRef': F'NodeSupport=1,SectorEquipmentFunction={row.sef}',
                    })
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'SectorCarrier', F'ENodeBFunction=1,SectorCarrier={row.sc}'))
                if row.celltype == 'FDD':
                    temp_dict_cell.update({
                        'eUtranCellFDDId': row.postcell,
                        'administrativeState': '0 (LOCKED)',
                        'cellRange': row.cellrange,
                        'cellId': row.cellid,
                        'earfcndl': row.earfcndl,
                        'earfcnul': row.earfcnul,
                        'dlChannelBandwidth': row.dlchannelbandwidth,
                        'ulChannelBandwidth': row.ulchannelbandwidth,
                        'physicalLayerCellIdGroup': int(row.physicallayercellid) // 3,
                        'physicalLayerSubCellId': int(row.physicallayercellid) % 3,
                        'rachRootSequence': row.rachrootsequence,
                        'tac': row.tac,
                        'isDlOnly': row.isdlonly,
                        'latitude': row.latitude,
                        'longitude': row.longitude,
                        'altitude': row.altitude,
                        'eutranCellCoverage': row.eutrancellcoverage,
                        'userLabel': row.userlabel,
                        'sectorCarrierRef': F'ENodeBFunction=1,SectorCarrier={row.sc}',
                    })
                elif row.celltype == 'TDD':
                    temp_dict_cell.update({
                        'eUtranCellTDDId': row.postcell,
                        'administrativeState': '0 (LOCKED)',
                        'cellRange': row.cellrange,
                        'cellId': row.cellid,
                        'earfcn': row.earfcndl,
                        'channelBandwidth': row.dlchannelbandwidth,
                        'physicalLayerCellIdGroup': int(row.physicallayercellid) // 3,
                        'physicalLayerSubCellId': int(row.physicallayercellid) % 3,
                        'rachRootSequence': row.rachrootsequence,
                        'tac': row.tac,
                        'isDlOnly': row.isdlonly,
                        'latitude': row.latitude,
                        'longitude': row.longitude,
                        'altitude': row.altitude,
                        'eutranCellCoverage': row.eutrancellcoverage,
                        'userLabel': row.userlabel,
                        'sectorCarrierRef': F'ENodeBFunction=1,SectorCarrier={row.sc}',
                        'isLaa': 'false',
                    })
                elif row.celltype == 'IOT':
                    temp_dict_cell.update({
                        'administrativeState': '0 (LOCKED)',
                        'nbIotCellId': row.postcell,
                        'cellId': row.cellid,
                        'nbIotCellType': row.nbiotcelltype,
                        'tac': row.tac,
                        'earfcndl': row.earfcndl,
                        'earfcnul': row.earfcnul,
                        'physicalLayerCellId': row.physicallayercellid,
                        'eutranCellRef': F'ENodeBFunction=1,EUtranCellFDD={row.postcellref}',
                        'sectorCarrierRef': F'ENodeBFunction=1,SectorCarrier={row.sc}',
                    })
                lines.extend(self.create_mos_script_from_dict(temp_dict_cell, tmp_celltype.get(row.celltype), ecell_ldn))

        # ---Relations---
        for _, row in self.usid.df_enb_cell.loc[(self.usid.df_enb_cell.postsite == self.node) &
                                                (self.usid.df_enb_cell.celltype.isin(['FDD', 'TDD']))].iterrows():
            cell_ldn = F'ENodeBFunction=1,{tmp_celltype.get(row.celltype)}={row.postcell}'
            lines.extend([F'#############:- Create Relations for {row.postcell} -:#############', ''])
            lines.extend(self.eutran_network(postcell=row.postcell, addcell=row.addcell, cell_ldn=cell_ldn))
            lines.extend(self.utra_network(postcell=row.postcell, addcell=row.addcell, cell_ldn=cell_ldn))

        if len(lines) > 0:
            default_parameter = [F'set ENodeBFunction=1,Paging=1$ maxNoOfPagingRecords {self.paging_max_records()}',
                                 F'set ENodeBFunction=1,EUtranCell[FT]DD=.*,UtranFreqRelation= cellReselectionPriority 0',
                                 F'set ENodeBFunction=1,EUtranCell[FT]DD=.*,UtranFreqRelation= cellReselectionPriority 0',
                                 F'']
            lines = default_parameter + lines

        return lines

    def eutran_network(self, postcell, addcell, cell_ldn):
        lines = []
        dcgk_flag = None if addcell else False
        nw_ldn = F'ENodeBFunction=1,EUtraNetwork={self.enbdata["EUtraNetwork"]}'
        df_rel = self.usid.df_enb_er.loc[(self.usid.df_enb_er.postsite == self.node) & (self.usid.df_enb_er.postcell == postcell) &
                                         (self.usid.df_enb_er.flag != dcgk_flag)]
        df_cell = self.usid.df_enb_ee.loc[(self.usid.df_enb_ee.postsite == self.node) & (self.usid.df_enb_ee.postcell == postcell) &
                                          (self.usid.df_enb_ee.flag != dcgk_flag)]
        # --- EUtraNetwork ---> EUtranFreqRelation, EUtranCellRelation ---
        for relid in set(list(df_rel.relid.unique()) + list(df_cell.relid.unique())):
            rel_ldn = F'{cell_ldn},EUtranFreqRelation={relid}'
            if df_rel.loc[df_rel.relid == relid].shape[0] > 0:
                row_rel = df_rel.loc[df_rel.relid == relid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('EUtranFreqRelation', row_rel.presite, row_rel.fdn)
                temp_dict.update({'eUtranFreqRelationId': row_rel.relid,
                                  'cellReselectionPriority': row_rel.creprio,
                                  'connectedModeMobilityPrio': row_rel.cprio,
                                  'voicePrio': row_rel.vprio,
                                  'threshXHigh': row_rel.thhigh,
                                  'threshXLow': row_rel.thlow,
                                  'userLabel': '',
                                  'eutranFrequencyRef': F'{nw_ldn},EUtranFrequency={row_rel.freqid}'})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'EUtranFreqRelation', rel_ldn))
            for _, row in df_cell.loc[df_cell.relid == relid].iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('EUtranCellRelation', row.presite, row.fdn)
                temp_dict.update({'eUtranCellRelationId': row.crelid,
                                  'isRemoveAllowed': row.israllowed,
                                  'sCellCandidate': row.scell,
                                  'neighborCellRef': row.extcell})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'EUtranCellRelation', F'{rel_ldn},EUtranCellRelation={row.crelid}'))
        return lines

    def utra_network(self, postcell, addcell, cell_ldn):
        lines = []
        dcgk_flag = None if addcell else False
        nw_ldn = F'ENodeBFunction=1,UtraNetwork={self.enbdata.get("UtraNetwork")}'
        df_rel = self.usid.df_enb_ur.loc[(self.usid.df_enb_ur.postsite == self.node) & (self.usid.df_enb_ur.postcell == postcell) &
                                         (self.usid.df_enb_ur.flag != dcgk_flag)]
        df_cell = self.usid.df_enb_ue.loc[(self.usid.df_enb_ue.postsite == self.node) & (self.usid.df_enb_ue.postcell == postcell) &
                                          (self.usid.df_enb_ue.flag != dcgk_flag)]
        # --- UtraNetwork ---> UtranFreqRelation & UtranCellRelation---
        for relid in set(list(df_rel.relid.unique()) + list(df_cell.relid.unique())):
            rel_ldn = F'{cell_ldn},UtranFreqRelation={relid}'
            if df_rel.loc[df_rel.relid == relid].shape[0] > 0:
                row_rel = df_rel.loc[df_rel.relid == relid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('UtranFreqRelation', row_rel.presite, row_rel.fdn)
                temp_dict.update({'utranFreqRelationId': row_rel.relid,
                                  'cellReselectionPriority': row_rel.creprio,
                                  'csFallbackPrio': row_rel.csprio,
                                  'csFallbackPrioEC': row_rel.csprioec,
                                  'userLabel': '',
                                  'utranFrequencyRef': F'{nw_ldn},UtranFrequency={row_rel.freqid}'})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'UtranFreqRelation', rel_ldn))
            for _, row in df_cell.loc[df_cell.relid == relid].iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('UtranCellRelation', row.presite, row.fdn)
                temp_dict.update({'utranCellRelationId': row.crelid,
                                  'externalUtranCellFDDRef': F'{nw_ldn},UtranFrequency={row.freqid},ExternalUtranCellFDD={row.xcellid}'})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'UtranCellRelation', F'{rel_ldn},UtranCellRelation={row.crelid}'))
        return lines

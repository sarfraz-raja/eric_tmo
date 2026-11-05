from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class lte_05_CellMOs(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0: return
        self.motype = 'Lrat'
        self.script_list.extend([self.rcp_msg_capabilities(), self.create_rpc_msg(), self.rcp_msg_close()])

    def create_rpc_msg(self):
        doc, config = self.main_rcp_msg_start(msg_id='cell_mos')
        me_mo = self.mo_add_form_dict_xml({'managedElementId': self.node}, 'ManagedElement')
        config.appendChild(me_mo)
        enb_mo = self.mo_add_form_dict_xml({'eNodeBFunctionId': 1}, 'ENodeBFunction')
        me_mo.appendChild(enb_mo)
        enb_mo.appendChild(self.mo_add_form_dict_xml({'pagingId': 1, 'maxNoOfPagingRecords': self.paging_max_records()}, 'Paging'))
        tmp_celltype = {'FDD': 'EUtranCellFDD', 'FDDId': 'eUtranCellFDDId', 'TDD': 'EUtranCellTDD', 'TDDId': 'eUtranCellTDDId',
                        'IOT': 'NbIotCell', 'IOTId': 'NbIotCellId'}
        for _, row in self.usid.df_enb_cell.loc[(self.usid.df_enb_cell.postsite == self.node)].iterrows():
            if row.addcell:
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
                    enb_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'SectorCarrier'))
                # ---Cell---
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn(tmp_celltype.get(row.celltype), row.presite, row.fdn)
                if row.celltype == 'FDD':
                    temp_dict.update({
                        'eUtranCellFDDId': row.postcell,
                        'administrativeState': '0 (LOCKED)',
                        'cellBarred': '0 (BARRED)',
                        'cellRange': row.cellrange,
                        'cellId': row.cellid,
                        'earfcndl': row.earfcndl,
                        'earfcnul': row.earfcnul,
                        'dlChannelBandwidth': row.dlchannelbandwidth,
                        'ulChannelBandwidth': row.ulchannelbandwidth,
                        'physicalLayerCellIdGroup': int(row.physicallayercellid) // 3,
                        'physicalLayerSubCellId': int(row.physicallayercellid) % 3,
                        'primaryPlmnReserved': 'true',
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
                    temp_dict.update({
                        'eUtranCellTDDId': row.postcell,
                        'administrativeState': '0 (LOCKED)',
                        'cellBarred': '0 (BARRED)',
                        'cellRange': row.cellrange,
                        'cellId': row.cellid,
                        'earfcn': row.earfcndl,
                        'channelBandwidth': row.dlchannelbandwidth,
                        'physicalLayerCellIdGroup': int(row.physicallayercellid) // 3,
                        'physicalLayerSubCellId': int(row.physicallayercellid) % 3,
                        'primaryPlmnReserved': 'true',
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
                    temp_dict.update({
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
            else:
                temp_dict = {tmp_celltype.get(F'{row.celltype}Id'): row.postcell}

            ecell_mo = self.mo_add_form_dict_xml(temp_dict, tmp_celltype.get(row.celltype))
            for rel_mo in self.eutran_network(postcell=row.postcell, addcell=row.addcell): ecell_mo.appendChild(rel_mo)
            for rel_mo in self.utra_network(postcell=row.postcell, addcell=row.addcell): ecell_mo.appendChild(rel_mo)
            enb_mo.appendChild(ecell_mo)
        return doc

    def eutran_network(self, postcell, addcell):
        rel_mos = []
        dcgk_flag = None if addcell else False
        # logVal = 'all' if addcell else 'dcgk_flag'
        nw_ldn = F'ENodeBFunction=1,EUtraNetwork={self.enbdata["EUtraNetwork"]}'
        df_rel = self.usid.df_enb_er.loc[(self.usid.df_enb_er.postsite == self.node) & (self.usid.df_enb_er.postcell == postcell) &
                                         (self.usid.df_enb_er.flag != dcgk_flag)]
        df_cell = self.usid.df_enb_ee.loc[(self.usid.df_enb_ee.postsite == self.node) & (self.usid.df_enb_ee.postcell == postcell) &
                                          (self.usid.df_enb_ee.flag != dcgk_flag)]
        # --- EUtraNetwork ---> EUtranFreqRelation & EUtranCellRelation ---
        for relid in set(list(df_rel.relid.unique()) + list(df_cell.relid.unique())):
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
            else: temp_dict = {'eUtranFreqRelationId': relid}
            rel_mo = self.mo_add_form_dict_xml(temp_dict, 'EUtranFreqRelation')
            # ---EUtranCellRelation---
            for _, row in df_cell.loc[df_cell.relid == relid].iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('EUtranCellRelation', row.presite, row.fdn)
                temp_dict.update({'eUtranCellRelationId': row.crelid,
                                  'isRemoveAllowed': row.israllowed,
                                  'sCellCandidate': row.scell,
                                  'neighborCellRef': row.extcell})
                rel_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'EUtranCellRelation'))
            rel_mos.append(rel_mo)
        return rel_mos

    def utra_network(self, postcell, addcell):
        rel_mos = []
        dcgk_flag = None if addcell else False
        nw_ldn = F'ENodeBFunction=1,UtraNetwork={self.enbdata.get("UtraNetwork")}'
        df_rel = self.usid.df_enb_ur.loc[(self.usid.df_enb_ur.postsite == self.node) & (self.usid.df_enb_ur.postcell == postcell) &
                                         (self.usid.df_enb_ur.flag != dcgk_flag)]
        df_cell = self.usid.df_enb_ue.loc[(self.usid.df_enb_ue.postsite == self.node) & (self.usid.df_enb_ue.postcell == postcell) &
                                          (self.usid.df_enb_ue.flag != dcgk_flag)]
        # --- UtraNetwork ---> UtranFreqRelation & UtranCellRelation---
        for relid in set(list(df_rel.relid.unique()) + list(df_cell.relid.unique())):
            if df_rel.loc[df_rel.relid == relid].shape[0] > 0:
                row_rel = df_rel.loc[df_rel.relid == relid].iloc[0]
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('UtranFreqRelation', row_rel.presite, row_rel.fdn)
                temp_dict.update({'utranFreqRelationId': row_rel.relid,
                                  'cellReselectionPriority': row_rel.creprio,
                                  'csFallbackPrio': row_rel.csprio,
                                  'csFallbackPrioEC': row_rel.csprioec,
                                  'userLabel': '',
                                  'utranFrequencyRef': F'{nw_ldn},UtranFrequency={row_rel.freqid}'})
            else: temp_dict = {'utranFreqRelationId': relid}
            rel_mo = self.mo_add_form_dict_xml(temp_dict, 'UtranFreqRelation')
            for _, row in df_cell.loc[df_cell.relid == relid].iterrows():
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('UtranCellRelation', row.presite, row.fdn)
                temp_dict.update({'utranCellRelationId': row.crelid,
                                  'externalUtranCellFDDRef': F'{nw_ldn},UtranFrequency={row.freqid},ExternalUtranCellFDD={row.xcellid}'})
                rel_mo.appendChild(self.mo_add_form_dict_xml(temp_dict, 'UtranCellRelation'))
            rel_mos.append(rel_mo)
        return rel_mos

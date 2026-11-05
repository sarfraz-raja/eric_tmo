import copy
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base
from .tmo_data import get_cell_type


# 'A': 'N2500', 'K': 'N600', 'J': 'N1900', 'I': 'N2100',
# 'T': 'L2500', 'L': 'L2100', 'B': 'L1900', 'D': 'L700', 'E': 'L600', 'C': 'L850', 'F': 'AWS3', 'G': 'B46_LAA',
# 'X': 'NB-IOT 700', 'Y': 'NB-IOT PCS', 'Z': 'NB-IOT AWS',
#
# lte_nr_rel_para_dict = {
#     'N2500_L2100': {'cellReselectionPriority': '6', 'eUtranFallbackPrioEc': '6', 'tReselectionEUtra': '2',
#                     'threshXHighP': '', 'threshXLowP': '', 'voicePrio': ''}
# }

class nr_05_EUtranRelation(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.usid.df_enb_cell.index) == 0: return
        self.motype = 'GNBCUCP'
        me_dict = self.eutran_relations()
        if len(me_dict) > 0:
            self.write_backup_script_file(script_list=self.mos_script_list_form_dict(para_dict=me_dict, mo_fdn='ManagedElement'))
            doc, config = self.main_rcp_msg_start(msg_id='EUtranRelation')
            config.appendChild(self.netconf_mo_form_dict(para_dict=me_dict, moc='ManagedElement'))
            self.script_list = [self.rcp_msg_capabilities(), doc, self.rcp_msg_close()]

    def eutran_relations(self) -> dict:
        nw_ldn = F'GNBCUCPFunction=1,EUtraNetwork={self.gnbdata["EUtraNetwork"]}'
        mos_list = []
        ref_mos = {
            'McpcPCellEUtranFreqRelProfile': ['Mcpc', 'McpcPCellEUtranFreqRelProfile', 'McpcPCellEUtranFreqRelProfileUeCfg'],
            'OffloadEUtranFreqRelProfile': ['TrafficOffload', 'OffloadEUtranFreqRelProfile', 'OffloadEUtranFreqRelProfileUeCfg'],
            'TrStSaEUtranFreqRelProfile': ['TrafficSteering', 'TrStSaEUtranFreqRelProfile', 'TrStSaEUtranFreqRelProfileUeCfg'],
            'UeMCEUtranFreqRelProfile': ['UeMC', 'UeMCEUtranFreqRelProfile', 'UeMCEUtranFreqRelProfileUeCfg'],
        }
        me_dict = {
            'managedElementId': self.node,
            'GNBCUCPFunction': {
                'gNBCUCPFunctionId': '1',
                'Mcpc': {'mcpcId': '1', 'McpcPCellEUtranFreqRelProfile': []},
                'TrafficOffload': {'trafficOffloadId': '1', 'OffloadEUtranFreqRelProfile': []},
                'TrafficSteering': {'trafficSteeringId': '1', 'TrStSaEUtranFreqRelProfile': []},
                'UeMC': {'ueMCId': '1', 'UeMCEUtranFreqRelProfile': []},
                'EUtraNetwork': {'eUtraNetworkId': self.gnbdata['EUtraNetwork'], 'EUtranFrequency': [], 'ExternalENodeBFunction': []},
                'NRCellCU': [],
            },
        }
        df_earfcn = self.usid.df_enb_cell.loc[self.usid.df_enb_cell.celltype.isin(['FDD', 'TDD'])][
            ['postsite', 'postcell', 'celltype', 'enbid', 'cellid', 'earfcndl',
             'dlchannelbandwidth', 'physicallayercellid', 'tac', 'freqband']]
        # ['postcell', 'celltype', 'enbid', 'cellid', 'earfcndl', 'dlchannelbandwidth', 'physicallayercellid', 'tac']
        # .drop_duplicates(subset=["earfcndl"])
        df_earfcn['lte_prb'] = df_earfcn.dlchannelbandwidth.apply(lambda x: str(int(int(x)/200)))

        if self.usid.client.mname in self.market_dict.get('tri_la', '') + self.market_dict.get('ncal', ''):
            df_earfcn['lte_carrier'] = df_earfcn.postcell.apply(lambda x: int(x[-1]) > 1)
            df_earfcn = df_earfcn.loc[((df_earfcn.celltype != 'TDD') &
                                       (~(df_earfcn.postcell.str.contains('^B') & (df_earfcn.lte_carrier))))]
        for earfcndl in df_earfcn.earfcndl.unique():
            mo_ldn = F'{nw_ldn},EUtranFrequency={earfcndl}'
            mo_fdn = self.check_if_mo_exist_for_ldn_get_fdn(node=self.node, mo_ldn=mo_ldn)
            if mo_fdn and not self.gnbdata['BBChange']: pass
            else:
                me_dict['GNBCUCPFunction']['EUtraNetwork']['EUtranFrequency'].append({
                    'attributes': {'xc:operation': 'create'},
                    'eUtranFrequencyId': mo_ldn.split('=')[-1],
                    'arfcnValueEUtranDl': earfcndl
                })
            mos_list += [mo_ldn]
        for postsite in df_earfcn.postsite.unique():
            ext_mo = {}
            ext_flag = False
            enbid = self.usid.enodeb[postsite]['nodeid']
            pLMNId = copy.deepcopy(self.usid.enodeb[postsite]['plmnlist'])
            del pLMNId['mncLength']
            mo_ldn = F'{nw_ldn},ExternalENodeBFunction=auto310_260_3_{enbid}'
            mo_fdn = self.check_if_mo_exist_for_ldn_get_fdn(node=self.node, mo_ldn=mo_ldn)
            if (mo_fdn and not self.gnbdata['BBChange']) or (mo_ldn in mos_list):
                ext_mo = {'externalENodeBFunctionId': mo_ldn.split('=')[-1]}
                mo_ldn_x2 = F'{ext_mo},TermPointToENodeB=auto1'
                mo_fdn_x2 = self.check_if_mo_exist_for_ldn_get_fdn(node=self.node, mo_ldn=mo_ldn_x2)
                if mo_fdn is None:
                    ext_mo['TermPointToENodeB'] = {
                        'attributes': {'xc:operation': 'create'},
                        'termPointToENodeBId': mo_ldn_x2.split('=')[-1],
                        'administrativeState': '1 (UNLOCKED)'
                    }
                    ext_flag = True
                mos_list += [mo_fdn_x2]
            else:
                ext_mo = {
                    'attributes': {'xc:operation': 'create'}, 'externalENodeBFunctionId': mo_ldn.split('=')[-1],
                    'eNodeBId': enbid, 'isRemoveAllowed': 'false',
                    'pLMNId': {'mcc': self.usid.enodeb[postsite]['plmnlist']['mcc'], 'mnc': self.usid.enodeb[postsite]['plmnlist']['mnc']},
                    'TermPointToENodeB': {'attributes': {'xc:operation': 'create'}, 'termPointToENodeBId': 'auto1',
                                          'administrativeState': '1 (UNLOCKED)'}
                }
                ext_flag = True
            for ext_cell in df_earfcn.loc[(df_earfcn.postsite == postsite)].itertuples():
                ext_cells_ldn = F'{mo_ldn},ExternalEUtranCell=310260-{enbid}-{ext_cell.cellid}'
                mo_fdn_ext_cell = self.check_if_mo_exist_for_ldn_get_fdn(node=self.node, mo_ldn=ext_cells_ldn)
                if (mo_fdn_ext_cell and not self.gnbdata['BBChange']) or (ext_cells_ldn in mos_list): pass
                else:
                    if 'ExternalEUtranCell' not in ext_mo.keys(): ext_mo['ExternalEUtranCell'] = []
                    ext_mo['ExternalEUtranCell'].append({
                        'attributes': {'xc:operation': 'create'}, 'externalEUtranCellId': ext_cells_ldn.split('=')[-1],
                        'cellLocalId': ext_cell.cellid, 'physicalLayerCellId': ext_cell.physicallayercellid, 'tac': ext_cell.tac,
                        'eUtranFrequencyRef': F'{nw_ldn},EUtranFrequency={ext_cell.earfcndl}',
                    })
                    ext_flag = True
            if ext_flag:
                me_dict['GNBCUCPFunction']['EUtraNetwork']['ExternalENodeBFunction'].append(copy.deepcopy(ext_mo))
                ext_flag = False
            mos_list += [mo_ldn]
        for nr_cell in self.df_gnb_cell.itertuples():
            cell_ldn = F'GNBCUCPFunction=1,NRCellCU={nr_cell.postcell}'
            cell_mo = {'nRCellCUId': nr_cell.postcell, 'EUtranFreqRelation': [], 'EUtranCellRelation': []}
            for ext_cell in df_earfcn.itertuples():
                ext_cells_ldn = (F'{nw_ldn},ExternalENodeBFunction=auto310_260_3_{ext_cell.enbid},'
                                 F'ExternalEUtranCell=310260-{ext_cell.enbid}-{ext_cell.cellid}')
                # EUtranCellRelation
                cell_rel_ldn = F'{cell_ldn},EUtranCellRelation={ext_cell.postcell}'
                ext_flag = True
                if cell_rel_ldn not in mos_list:
                    if not self.gnbdata['BBChange'] and not nr_cell.addcell and \
                            self.check_if_mo_exist_for_ldn_get_fdn(node=self.node, mo_ldn=cell_rel_ldn) is None:
                        for mo_fdn in self.site.find_mos_with_end_str(end_str=F'{cell_ldn},EUtranCellRelation=[^,=]*'):
                            if ext_cells_ldn in self.site.get_para_value_for_mo(mo=mo_fdn, para='neighborCellRef'):
                                ext_flag = False
                                break
                    if ext_flag:
                        cell_mo['EUtranCellRelation'].append({
                            'attributes': {'xc:operation': 'create'}, 'eUtranCellRelationId': ext_cell.postcell,
                            'isHoAllowed': 'true', 'isRemoveAllowed': 'false',
                            'neighborCellRef': ext_cells_ldn
                        })
                    mos_list += [cell_rel_ldn]
                # EUtranFreqRelation
                rel_ldn = F'{cell_ldn},EUtranFreqRelation={ext_cell.earfcndl}'
                if rel_ldn not in mos_list:
                    ref_dict = {
                        'eUtranFrequencyRef': F'GNBCUCPFunction=1,EUtraNetwork=1,EUtranFrequency={ext_cell.earfcndl}',
                        'offloadEUtranFreqRelProfileRef': 'GNBCUCPFunction=1,TrafficOffload=1,OffloadEUtranFreqRelProfile=Default',
                        'trStSaEUtranFreqRelProfileRef': 'GNBCUCPFunction=1,TrafficSteering=1,TrStSaEUtranFreqRelProfile=Default',
                        'mcpcPCellEUtranFreqRelProfileRef': '',
                        'ueMCEUtranFreqRelProfileRef': '',
                    }
                    nr_cell_type = get_cell_type(cell=nr_cell.postcell)
                    if nr_cell_type:
                        ref_id = '_'.join([ext_cell.earfcndl, nr_cell_type, nr_cell.postcell[-1]])
                        ref_dict.update({
                            'mcpcPCellEUtranFreqRelProfileRef': F'GNBCUCPFunction=1,Mcpc=1,McpcPCellEUtranFreqRelProfile={ref_id}',
                            'ueMCEUtranFreqRelProfileRef': F'GNBCUCPFunction=1,UeMC=1,UeMCEUtranFreqRelProfile={ref_id}'
                        })
                        for ref in ref_dict:
                            if ref_dict[ref].split('=')[-1] != ref_id: continue
                            ref_mo_dict = {}
                            mo_ldn = ref_dict[ref]
                            moc = mo_ldn.split(',')[-1].split('=')[0]
                            mo_fdn_ref = self.check_if_mo_exist_for_ldn_get_fdn(node=self.node, mo_ldn=mo_ldn)
                            if (mo_ldn in mos_list) or (mo_fdn_ref and not self.gnbdata['BBChange']): continue
                            elif mo_fdn_ref and self.gnbdata['BBChange']:
                                mos_list += [mo_ldn]
                                ref_mo_dict = self.get_mo_dict_from_moc_node_fdn_moid(
                                    moc=moc, node=self.node, mo_fdn=mo_fdn_ref, moid=mo_ldn.split('=')[-1])
                                if len(ref_mos[moc]) == 3:
                                    ref_mo_dict[ref_mos[moc][2]] = []
                                    for child in self.site.find_mos_list_from_fdn_moc(mo_fdn=mo_fdn_ref, moc=ref_mos[moc][2]):
                                        child_mo_dict = self.get_mo_dict_from_moc_node_fdn_moid(
                                            moc=ref_mos[moc][2], node=self.node, mo_fdn=child, moid=child.split('=')[-1])
                                        if ref_mos[moc][2].endswith('UeCfg') and child.split('=')[-1] == 'Base':
                                            child_mo_dict |= {'attributes': {'xc:operation': 'update'}}
                                        ref_mo_dict[ref_mos[moc][2]].append(copy.deepcopy(child_mo_dict))
                            else:
                                mos_list += [mo_ldn]
                                ref_mo_dict = self.get_db_para_dict_with_child(moc=moc, db_moid='CU', moid=mo_ldn.split('=')[-1], rel_tag='GNBCUCP')
                            if len(ref_mo_dict) > 0: me_dict['GNBCUCPFunction'][ref_mos[moc][0]][moc].append(copy.deepcopy(ref_mo_dict))
                    # EUtranFreqRelation
                    rel_mo_dict = {}
                    rel_fdn = self.check_if_mo_exist_for_ldn_get_fdn(node=self.node, mo_ldn=rel_ldn)
                    if rel_fdn and not self.gnbdata['BBChange']: pass
                    elif rel_fdn and self.gnbdata['BBChange']:
                        rel_mo_dict = self.get_mo_dict_from_moc_node_fdn_moid(
                            moc='EUtranFreqRelation', node=self.node, mo_fdn=rel_fdn, moid=rel_ldn.split('=')[-1])
                        rel_mo_dict |= ref_dict
                    else:
                        rel_mo_dict = self.get_mo_dict_from_moc_node_fdn_moid(
                            moc='EUtranFreqRelation', node=self.node, mo_fdn=rel_ldn, moid=rel_ldn.split('=')[-1])
                        rel_mo_dict |= ref_dict
                        # 'A': 'N2500', 'K': 'N600', 'J': 'N1900', 'I': 'N2100',
                        # 'T': 'L2500', 'L': 'L2100', 'B': 'L1900', 'D': 'L700', 'E': 'L600', 'C': 'L850', 'F': 'AWS3', 'G': 'B46_LAA',
                        # 'X': 'NB-IOT 700', 'Y': 'NB-IOT PCS', 'Z': 'NB-IOT AWS',
                        rel_mo_dict |= {
                            'attributes': {'xc:operation': 'create'},
                            'allowedMeasBandwidth': str(int(int(ext_cell.dlchannelbandwidth) / 200)),
                            'cellReselectionPriority': '6' if ext_cell.freqband in ['4', '66'] else '5' if ext_cell.freqband in ['2']
                            else '3' if ext_cell.freqband in ['71'] else '2',
                            'eUtranFallbackPrioEc': '6' if (nr_cell.postcell[0] == 'A' and ext_cell.freqband in ['4', '66']) or
                            (nr_cell.postcell[0] == 'J' and ext_cell.freqband in ['2']) or
                            (nr_cell.postcell[0] == 'K' and ext_cell.freqband in ['71']) or
                            (nr_cell.postcell[0] == 'I' and ext_cell.freqband in ['2']) else '0',
                            'voicePrio': '5' if (nr_cell.postcell[0] == 'A' and ext_cell.freqband in ['2']) else
                            '6' if (nr_cell.postcell[0] == 'A' and ext_cell.freqband in ['4', '66']) or
                            (nr_cell.postcell[0] == 'J' and ext_cell.freqband in ['2']) or
                            (nr_cell.postcell[0] == 'K' and ext_cell.freqband in ['71']) or
                            (nr_cell.postcell[0] == 'I' and ext_cell.freqband in ['2']) else '0',
                            'tReselectionEUtra': '1' if nr_cell.postcell[0] == 'K' else '2',
                            'threshXHighP': '10' if nr_cell.postcell[0] == 'K' and ext_cell.freqband in ['2', '4', '66'] else None,
                            'qRxLevMin': '-124',
                            'userLabel': ext_cell.earfcndl,
                        }
                    if len(rel_mo_dict) > 0: cell_mo['EUtranFreqRelation'].append(copy.deepcopy(rel_mo_dict))
                    mos_list += [rel_ldn]
            if len(cell_mo['EUtranFreqRelation']) > 0 or len(cell_mo['EUtranCellRelation']) > 0:
                me_dict['GNBCUCPFunction']['NRCellCU'].append(copy.deepcopy(cell_mo))
        # Remove empty MOs
        for mos in ref_mos:
            if len(me_dict['GNBCUCPFunction'][ref_mos[mos][0]][ref_mos[mos][1]]) == 0: del me_dict['GNBCUCPFunction'][ref_mos[mos][0]]
        if len(me_dict['GNBCUCPFunction']['NRCellCU']) == 0: del me_dict['GNBCUCPFunction']['NRCellCU']
        if len(me_dict['GNBCUCPFunction']['EUtraNetwork']['EUtranFrequency']) == 0: del me_dict['GNBCUCPFunction']['EUtraNetwork']['EUtranFrequency']
        if len(me_dict['GNBCUCPFunction']['EUtraNetwork']['ExternalENodeBFunction']) == 0:
            del me_dict['GNBCUCPFunction']['EUtraNetwork']['ExternalENodeBFunction']
        if len(me_dict['GNBCUCPFunction']) == 1: del me_dict['GNBCUCPFunction']
        if len(me_dict) == 1: me_dict = {}

        return me_dict

    @staticmethod
    def activity_check(activity=''):
        return [
            F'',
            F'####:----------------> {activity} Check <----------------:####',
            F'hget GNBCUCPFunction=1,EUtraNetwork=.*,EUtranFrequency= arfcnValueEUtranDl|userLabel',
            F'hget NRCellCU=.*,EUtranFreqRelation= allowedMeasBandwidth|cellReselectionPriority|connectedModeMobilityPrio|eUtranFallbackPrioEc|voicePrio',
            F'hget ,UeMCEUtranFreqRelProfileUeCfg= connModePrioPCell',
            F'',
            F'',
        ]

import copy
import re
import numpy as np
from django.db.models import Q
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C09_nr_03_gNodeBMOs(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0 or (self.gnbdata['BBChange'] is False and self.gnbdata['GNBDUFunction'] is not None): return
        self.reconfig_ap_file_path_to_remote()
        self.script_list.extend([self.ap_rcp_msg_cap(), self.create_rpc_msg(), self.rcp_msg_close()])

    def create_rpc_msg(self):
        doc, config = self.main_rcp_msg_start(msg_id='gnb_mos')
        me_mo = self.mo_add_form_dict_xml({'managedElementId': self.node}, 'ManagedElement')
        config.appendChild(me_mo)

        # GNBCUCPFunction
        self.custom_moc = ['CUCP5qiTable', 'UeGroupSelection', 'ResourcePartitions']
        cucp_mo = self.mo_add_form_dict_xml({'gNBCUCPFunctionId': '1'}, 'GNBCUCPFunction')
        me_mo.appendChild(cucp_mo)
        self.motype = 'GNBCUCP'
        self.default_mocs = ['IntraFreqMC', ]
        children = self.MoRelation.objects.filter(parent='GNBCUCPFunction', tag=self.motype, software=self.usid.client.software)
        for child in children:
            mos = self.db_append_child_tags(child.child, rel_tag=self.motype)
            for mo in mos: cucp_mo.appendChild(mo)
        moc_dict = {
            'CUCP5qiTable': {
                'id': ['1', 'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000', 'SD_6000', 'SD_6001',
                       'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                'CUCP5qi': {'id': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '128', '129']}
            },
            'UeGroupSelection': {
                'id': ['1'],
                'UeAdmissionGroupDefinition': {'id': ['E911_Users', 'WPS_Users']},
                'UeGroupSelectionProfile': {'id': ['14', '2', 'GalaxyA53', 'HSI', 'Pixel_6', 'SD_2000', 'SD_3001', 'SD_6000', 'SD_6001',
                                                   'SD_9000', 'SD_9001', 'SD_9002', 'VoNR']},
            },
            'ResourcePartitions': {'id': ['1'], 'ResourcePartition': {
                'id': ['FWA', 'SA', 'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000',
                       'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                'ResourcePartitionMember': {'id': ['1']}}},

        }
        if self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.contains('^A'))].shape[0] > 0:
            moc_dict['CUCP5qiTable']['id'].append('2')
            moc_dict['UeGroupSelection']['UeServiceGroupDefinition'] = {'id': ['1', '2', '3']}
            moc_dict['ResourcePartitions']['ResourcePartition']['id'].append('NSA')
        if self.bbversion in 'G3G4':
            moc_dict['UeCC'] = {'id': ['1'],
                                'UlDataSplit': {'id': ['Default_endc', 'Default_nrdc'], 'UlDataSplitUeCfg': {'id': ['Base']}},
                                'InitialCg': {'id': ['Default'], 'InitialCgUeCfg': {'id': ['Base']}}}
            moc_dict['UeCovMeas'] = {'id': ['1'], 'UcmEUtranFreqRelProfile': {'id': ['Default']}}
            moc_dict['UeNoDrb'] = {'id': ['1'], 'UeNoDrbPCellProfile': {'id': ['Default'], 'UeNoDrbPCellProfileUeCfg': {'id': ['Base']}}}
            moc_dict['EnergyPerformance'] = {'id': ['1'], 'EpBoCS': {
                'id': ['1'], 'EpBoosterAdvCfg': {'id': ['Default']}, 'EpBoosterCellProfile': {'id': ['Default']}}}
            if self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.contains('^A'))].shape[0] > 0:
                moc_dict['EnergyPerformance']['EpBoCS']['EpBoosterAdvCfg']['id'].append('1')
                moc_dict['EnergyPerformance']['EpBoCS']['EpBoosterCellProfile']['id'].append('1')


        moc_dict['UeUlResMon'] = {'id': ['1'], 'UlQualMcpcMeasCfg': {'id': ['Default']}}
        if self.bbversion in 'G3G4':
            moc_dict['UeUlResMon']['UlBufferMonCfg'] = {'id': ['Default']}
            moc_dict['PeriodicUeMeas'] = {'id': ['1'], 'PuemCellProfile': {'id': ['Default'], 'PuemCellProfileUeCfg': {'id': ['Base']}}}
            moc_dict['PmUeMeas'] = {'id': ['1'], 'PmUeIntraFreqCellProfile': {'id': ['Default']}}
            moc_dict['PriorityService'] = {'id': ['1']}


        for mo in self.db_append_child_special_method(moc_dict=moc_dict): cucp_mo.appendChild(mo)

        # GNBCUUPFunction
        self.custom_moc = ['CUUP5qiTable', 'ResourcePartitions', 'AqmCfg', 'DcDlCfg', 'DcUlCfg', 'Drb', 'UserPlaneProfile', 'L4sCfg']
        cuup_mo = self.mo_add_form_dict_xml({'gNBCUUPFunctionId': '1'}, 'GNBCUUPFunction')
        me_mo.appendChild(cuup_mo)
        self.motype = 'GNBCUUP'
        children = self.MoRelation.objects.filter(parent='GNBCUUPFunction', tag=self.motype, software=self.usid.client.software)
        for child in children:
            mos = self.db_append_child_tags(child.child, rel_tag=self.motype)
            for mo in mos: cuup_mo.appendChild(mo)
        moc_dict = {
            'CUUP5qiTable': {
                'id': ['1', 'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000', 'SD_6000', 'SD_6001',
                       'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                'CUUP5qi': {'id': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '128', '129']}
            },
            'ResourcePartitions': {'id': ['1'], 'ResourcePartition': {
                'id': ['FWA', 'SA', 'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000', 'SD_6000', 'SD_6001',
                       'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                'ResourcePartitionMember': {'id': ['1']}}},
            'UeCC': {'id': ['1'],
                     'AqmCfg': {'id': ['Conversational_Video', 'Default_application_signaling', 'Default_conversational_media',
                                       'Default_other', 'Non-Conversational_Video', 'Real_Time_Gaming',
                                       'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_6000', 'SD_6001',
                                       'SD_9000', 'SD_9001', 'SD_9002', 'WPS_User']},
                     'DcDlCfg': {'id': ['Default']},
                     'Drb': {'id': ['5QI6_L4S', 'Conversational_Video', 'Default_application_signaling', 'Default_conversational_media',
                                    'Default_other', 'L10H20_L4S', 'L4H10_L4S', 'L8H16_L4S', 'Non-Conversational_Video', 'Real_Time_Gaming',
                                    'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_6000', 'SD_6001',
                                    'SD_9000', 'SD_9001', 'SD_9002', 'WPS_User'],
                             'DrbUeCfg': {'id': ['Base']}},
                     'L4sCfg': {'id': ['1', 'L10H20_L4S', 'L4H10_L4S', 'L8H16_L4S']},
                     'UserPlaneProfile': {'id': ['Default'], 'UserPlaneProfileUeCfg': {'id': ['Base']}},
                     }
        }
        if self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.contains('^A'))].shape[0] > 0:
            moc_dict['CUUP5qiTable']['id'].append('2')
            moc_dict['ResourcePartitions']['ResourcePartition']['id'].append('NSA')
        if self.usid.client.software.swname[:9] > 'TMO_24_Q4' and self.bbversion in 'G3G4':
            moc_dict['UeCC']['DcUlCfg'] = {'id': ['Default']}

        for mo in self.db_append_child_special_method(moc_dict=moc_dict):
            cuup_mo.appendChild(mo)

        # GNBDUFunction
        self.custom_moc = ['DU5qiTable', 'ResourcePartitions', 'CaSCellHandling',
                           'AqmCfg', 'Bsr', 'CgSwitch', 'CgSwitchCfg', 'ConfiguredGrant', 'DlMimo', 'DrbUp', 'DrxProfile',
                           'Harq', 'L4sCfg', 'LinkAdaptation', 'PdcchReuseForPdsch', 'PowerControl', 'Prescheduling', 'PuschRep',
                           'Rach', 'RadioLinkControl', 'RimOffload', 'SchedulingProfile', 'SoftAcAssist', 'SrHandling',
                           'SrPeriodicity', 'UeBb', 'UlWfPortSwitch', 'RadioBearerTable', 'ContentionControl', 'EnergyEfficiency',
                           'MassiveMimoSleep']
        du_mo = self.mo_add_form_dict_xml({'gNBDUFunctionId': '1'}, 'GNBDUFunction')
        me_mo.appendChild(du_mo)
        self.motype = 'GNBDU'
        children = self.MoRelation.objects.filter(parent='GNBDUFunction', tag=self.motype, software=self.usid.client.software)
        for child in children:
            mos = self.db_append_child_tags(child.child, rel_tag=self.motype)
            for mo in mos: du_mo.appendChild(mo)

        moc_dict = {
            'RadioBearerTable': {'id': ['1'], 'SignalingRadioBearer': {'id': ['1']}},
            'ContentionControl': {'id': ['1'], 'SessionLimit': {'id': ['Default', 'WPS_NSA', 'WPS_SA'],
                                                                'ContentionControl': {'id': ['Default', 'MMBB_WPS']}}},
            'DU5qiTable': {
                'id': ['1', 'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002',
                       'SD_4000', 'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001',
                       'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                'DU5qi': {'id': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '128', '129']}
            },
            'ResourcePartitions': {'id': ['1'], 'ResourcePartition': {
                'id': ['FWA', 'SA', 'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002',
                       'SD_4000', 'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001',
                       'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                'ResourcePartitionMember': {'id': ['1']}}},
            'UeCA': {'id': ['1'],
                     'CaSCellHandling': {'id': ['1', 'Default'], 'CaSCellHandlingUeCfg': {'id': ['Base', 'SA', ]}}},
            'UeCC': {'id': ['1'],
                     'AqmCfg': {'id': ['Conversational_Video', 'Default_application_signaling', 'Default_conversational_media',
                                       'Default_conversational_media', 'Default_other', 'Non-Conversational_Video', 'Real_Time_Gaming',
                                       'SD_2000', 'SD_3001', 'SD_3002', 'SD_6000', 'SD_6001']},
                     'Bsr': {'id': ['1'], 'BsrUeCfg': {'id': ['Base', 'LowLatency', 'VoNR']}},
                     'CgSwitch': {'id': ['Default'], 'CgSwitchUeCfg': {'id': ['Base']}},
                     'CgSwitchCfg': {'id': ['Default']},
                     'ConfiguredGrant': {'id': ['1'], 'ConfiguredGrantUeCfg': {'id': ['Base']}},
                     'DlMimo': {'id': ['1'], 'DlMimoUeCfg': {'id': ['Base']}},
                     'DrbUp': {'id': ['Conversational_Video', 'Default_application_signaling', 'Default_conversational_media',
                                      'Default_conversational_media', 'Default_other', 'Non-Conversational_Video', 'Real_Time_Gaming',
                                      'SD_2000', 'SD_3001', 'SD_3002', 'SD_6000', 'SD_6001'],
                               'DrbUpUeCfg': {'id': ['Base'], }},
                     'DrxProfile': {'id': ['Default'], 'DrxProfileUeCfg': {'id': ['Base', 'VONR'], 'PuschRepRel16Drx': {'id': ['1']}}},
                     'Harq': {'id': ['1'], 'HarqUeCfg': {'id': ['Base', 'SD_2000', 'SD_6000', 'SD_6001', 'VoNR']}},
                     'L4sCfg': {'id': ['1', 'L10H20_L4S', 'L4H10_L4S', 'L8H16_L4S']},
                     'LinkAdaptation': {
                         'id': ['1'],
                         'LinkAdaptationUeCfg': {
                             'id': ['Base', 'VoNR', 'SD_10000', 'SD_2000', 'SD_3000', 'SD_3001', 'SD_3002',
                                    'SD_4000', 'SD_6000', 'SD_6001', 'SD_7000', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                             'DlLinkAdaptation': {'id': ['1']},
                             'PdcchLinkAdaptation': {'id': ['1']},
                             'UlLinkAdaptation': {'id': ['1']}}},
                     'PdcchReuseForPdsch': {'id': ['Default'], 'PdcchReuseForPdschUeCfg': {'id': ['Base']}},
                     'PowerControl': {'id': ['1'], 'PowerControlUeCfg': {'id': ['Base', '1']}},
                     'Prescheduling': {'id': ['1'], 'PreschedulingUeCfg': {'id': ['Base', 'SD_2000', 'SD_6000', 'SD_6001']}},
                     'PuschRep': {'id': ['Default', 'VoNR_Dynamic'], 'PuschRepUeCfg': {'id': ['Base']}},
                     'Rach': {'id': ['Default'], 'RachUeCfg': {'id': ['Base']}},
                     'RadioLinkControl': {'id': ['1'],
                                          'DrbRlc': {'id': ['Default', 'IMS-SIP', 'Video', 'VoNR', 'gaming'], 'DrbRlcUeCfg': {'id': ['Base']}},
                                          'UeAdaptiveRlc': {'id': ['1'], 'UeAdaptiveRlcUeCfg': {'id': ['Base']}}},
                     'RimOffload': {'id': ['1'], 'RimOffloadUeCfg': {'id': ['Base']}},
                     'SchedulingProfile': {
                         'id': [
                             '5QI129', '5QI6', '5QI7', '5QI8', '5QI9',
                             # 'NSA_5QI129', 'NSA_5QI6', 'NSA_5QI7', 'NSA_5QI8', 'NSA_5QI9',
                             'SD_10000_SST_1_5QI6', 'SD_10001_SST_1_5QI6', 'SD_2000_SST_1_5QI6', 'SD_2001_SST_1_5QI6',
                             'SD_3000_SST_1_5QI6', 'SD_3001_SST_1_5QI6', 'SD_3002_SST_1_5QI6',
                             'SD_4000_SST_1_5QI6', 'SD_6000_SST_1_5QI6', 'SD_6001_SST_1_5QI6',
                             'SD_7000_SST_1_5QI6', 'SD_8000_SST_1_5QI6', 'SD_8001_SST_1_5QI6',
                             'SD_9000_SST_1_5QI6', 'SD_9001_SST_1_5QI6', 'SD_9002_SST_1_5QI6',
                             'WPS_2X_User_5QI128', 'WPS_Slice_User_5QI128', 'WPS_Slice_User_5QI6', 'WPS_User_5QI128',

                             'SD_2000_SST_1_5QI7', 'SD_2000_SST_1_5QI8', 'SD_2000_SST_1_5QI9',
                             'SD_4000_SST_1_5QI7', 'SD_4000_SST_1_5QI8', 'SD_4000_SST_1_5QI9',
                             'SD_6000_SST_1_5QI7', 'SD_6000_SST_1_5QI8', 'SD_6000_SST_1_5QI9',
                             'SD_8000_SST_1_5QI7', 'SD_8000_SST_1_5QI8', 'SD_8000_SST_1_5QI9'],
                         'DlRateBasedPriority': {'id': '1'}, 'DlResourceBasedPriority': {'id': '1'},
                         'UlRateBasedPriority': {'id': '1'}, 'UlResourceBasedPriority': {'id': '1'}},
                     'SoftAcAssist': {'id': ['1'], 'SoftAcAssistUeCfg': {'id': ['Base', 'HSI']}},
                     'SrHandling': {
                         'id': ['5QI_5', 'Default', 'SD_2000', 'SD_6000', 'SD_6001'],
                         'SrHandlingUeCfg': {'id': ['Base']}},
                     'SrPeriodicity': {
                         'id': ['Default'], 'SrPeriodicityCovAdaptUeCfg': {'id': ['Base']},
                         'SrPeriodicityUeCfg': {'id': ['Base', 'SD_2000', 'SD_6000']}},
                     'UeBb': {
                         'id': ['1'],
                         'UeBbProfile': {
                             'id': ['Default'],
                             'UeBbProfileUeCfg': {
                             'id': ['Base', 'SD_2000', 'SD_3001', 'SD_6000', 'SD_6001', 'SD_9000_1', 'SD_9002', 'VoNR']}}},          #'NSA'
                     'UlWfPortSwitch': {
                         'id': ['1'],
                         'UlWfPortSwitchUeCfg': {'id': ['Base']}},
                     # 'UlServiceDefinition': {'id': ['1'], 'UlServiceDefinitionUeCfg': {'id': ['Base'], 'UlService': {'id': ['1']}}},
                     },
        }
        # GEN3 BB and Above Features - BB6630 and BB5216 Excluded
        if self.bbversion in 'G2': del moc_dict['ContentionControl']
        if self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.contains('^A'))].shape[0] > 0:
            moc_dict['BWP'] = {'id': [
                'BW100_DenseSS_DL', 'BW100_DenseSS_UL', 'BW100_Init_DL', 'BW100_Init_UL', 'BW100_SparseSS_DL', 'BW100_SparseSS_UL',
                'BW40_DenseSS_DL', 'BW40_DenseSS_UL', 'BW40_Init_DL', 'BW40_Init_UL', 'BW40_SparseSS_DL', 'BW40_SparseSS_UL']}
            moc_dict['BWPSet'] = {'id': ['1', '6'],
                                  'BWPSetUeCfg': {'id': ['1', '2', '3', '4'], 'BWPSetCfg': {'id': ['0', '1']}},
                                  'DynPowerOpt': {'id': ['1', '2']}}
            moc_dict['DU5qiTable']['id'].append('2')
            moc_dict['ResourcePartitions']['ResourcePartition']['id'].append('NSA')
            moc_dict['UeCA']['CaSCellHandling']['CaSCellHandlingUeCfg']['id'].append('NSA')
            moc_dict['UeCC']['SchedulingProfile']['id'].extend(['NSA_5QI6', 'NSA_5QI7', 'NSA_5QI8', 'NSA_5QI9', 'NSA_5QI129'])
            moc_dict['UeCC']['UeBb']['UeBbProfile']['UeBbProfileUeCfg']['id'].append('NSA')
        else:
            moc_dict['UeCC']['SoftAcAssist']['SoftAcAssistUeCfg']['id'].extend(['HSI'])
        if self.bbversion in 'G3G4':
            moc_dict['EnergyEfficiency'] = {'id': ['1'], 'EnergyOptPwrAlloc': {'id': ['Default'], 'EnergyOptPwrAllocUeCfg': {'id': ['Base']}}}
        if len([True for _ in self.df_gnb_cell.frutypecix if
                len([radio for radio in _ if re.match('AIR.*64.*', radio)]) > 0]) > 0:
            moc_dict['MassiveMimoSleep'] = {
                'id': ['1'], 'MMimoSleepProfile': {'id': ['1']},
                'MMimoSleepTimeGroup': {'id': ['1'], 'MMimoSleepTimeWindow': {'id': ['1']}}}

        for mo in self.db_append_child_special_method(moc_dict=moc_dict):
            du_mo.appendChild(mo)


        return doc

    @staticmethod
    def validate_db_moid(*, moid: str) -> bool:
        return True if moid in [None, 'None', '', 'XX', 'nan', np.nan, '""'] or ',' in moid else False

    def db_append_child_tags(self, motype, rel_tag):
        ret_mos = []
        if motype in self.custom_moc: return ret_mos
        mo_tag_ins = self.MoName.objects.filter(moc=motype, software=self.usid.client.software, motype=self.motype)
        if mo_tag_ins.exists():
            for mo_tag_in in mo_tag_ins:
                if self.validate_db_moid(moid=mo_tag_in.moid): continue
                ret_mos.append(self.append_child_tags(mo_tag_in, rel_tag=rel_tag))
        return ret_mos

    def append_child_tags(self, motype, rel_tag):
        parent_mo = self.mo_add_form_dict_xml(self.get_mo_related_attributes(motype), motype.moc)
        for children in self.MoRelation.objects.filter(parent=motype.moc, tag=rel_tag, software=self.usid.client.software):
            for child in self.MoName.objects.filter(moc=children.child, software=self.usid.client.software, motype=self.motype):
                if self.validate_db_moid(moid=child.moid): continue
                if child.modetail_set.filter((Q(flag=True)) & (Q(bbversion='') | Q(bbversion__contains=self.bbversion))).exists():
                    child_mo = self.append_child_tags(child, rel_tag)
                    parent_mo.appendChild(child_mo)
        return parent_mo

    def db_append_child_special_method(self, moc_dict):
        ret_mos = []
        for moc in moc_dict.keys():
            if moc == 'id' or moc_dict[moc].get('id') is None: continue
            mo_tag_ins = self.MoName.objects.filter(moc=moc, software=self.usid.client.software, motype=self.motype)
            for mo_tag_in in mo_tag_ins:
                if mo_tag_in.moid in moc_dict[moc].get('id'):
                    ret_mos.append(self.append_child_tags_special_method(motype=mo_tag_in, moc_dict=moc_dict[moc], moid=mo_tag_in.moid))
        return ret_mos

    def append_child_tags_special_method(self, motype, moc_dict, moid):
        mo_dict = self.get_mo_related_attributes(motype)
        mo_dict |= {self.get_moc_id(moc=motype.moc): mo_dict.get(self.get_moc_id(moc=motype.moc)).split(',')[-1]}
        parent_mo = self.mo_add_form_dict_xml(copy.deepcopy(mo_dict), motype.moc)
        for moc in moc_dict.keys():
            if moc == 'id' or moc_dict[moc].get('id') is None: continue
            moid_list = [F'{moid},{_}' for _ in moc_dict[moc].get('id')]
            for moc_c in self.MoName.objects.filter(moc=moc, software=self.usid.client.software, motype=self.motype):
                if moc_c.moid not in moid_list: continue
                child_mo = self.append_child_tags_special_method(moc_c, moc_dict=moc_dict[moc], moid=moc_c.moid)
                parent_mo.appendChild(child_mo)
        return parent_mo

    def special_formate_scripts(self):
        import fileinput
        import sys
        import os

        def replace_method(file, searchExp, replaceExp, nodename):
            for line in fileinput.input(file, inplace=1):
                if 'selectionCriteria' in line:
                    line = line.replace(F'ManagedElement={nodename},', '')
                #     line = line.replace(searchExp, replaceExp).replace('&amp;', '&').replace(F'ManagedElement={nodename},', '')
                sys.stdout.write(line)

        if os.path.exists(self.script_file) and os.path.isfile(self.script_file):
            replace_method(self.script_file, '&gt;', '>', self.node)

import copy
import re
from xml.etree.ElementTree import Element


import numpy as np
from django.db.models import Q
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C09_nr_03_gNodeBMOs(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0 or (self.gnbdata['BBChange'] is False and
                                      self.gnbdata['GNBDUFunction'] is not None): return
        self.reconfig_ap_file_path_to_remote()
        rcp_msg = self.create_rpc_msg()
        if len(rcp_msg) > 0:
            self.script_list.extend([self.rcp_msg_capabilities()] + rcp_msg + [self.rcp_msg_close()])

        # self.script_list.extend([self.rcp_msg_capabilities(), self.create_rpc_msg(), self.rcp_msg_close()])

    def create_rpc_msg(self) -> list:
        rcp_msgs = []
        doc, config = self.main_rcp_msg_start(msg_id='gnb_mos')
        me_mo = self.mo_add_form_dict_xml({'managedElementId': self.node}, 'ManagedElement')
        config.appendChild(me_mo)

        moc_dict = self.get_nr_moc_dict()

        # Special Method for getting unique MOs Scripts
        self.motype = 'GNBDU'
        UeCC_mod_dict = copy.deepcopy(moc_dict['GNBDU']['UeCC'])
        for moc in UeCC_mod_dict:
            if moc == 'id': continue
            doc, config = self.main_rcp_msg_start(msg_id=F'GNBDUFunction=1,UeCC=1,{moc}')
            me_mo = self.mo_add_form_dict_xml({'managedElementId': self.node}, 'ManagedElement')
            config.appendChild(me_mo)
            xml_mo = self.mo_add_form_dict_xml({'gNBDUFunctionId': '1'}, 'GNBDUFunction')
            me_mo.appendChild(xml_mo)
            uecc_mo = self.mo_add_form_dict_xml({'ueCCId': '1'}, 'UeCC')
            xml_mo.appendChild(uecc_mo)
            parent_ldn = F'{self.dcgk_function_ldn()},UeCC=1' if self.dcgk_function_ldn() else None
            for mo in self.sub_mo_db_append_child_special_method(moc_dict=UeCC_mod_dict, sub_moc=moc, parent_ldn=parent_ldn):
                uecc_mo.appendChild(mo)
            rcp_msgs.append(doc)

        # Complete MOs
        for mo_type in moc_dict.keys():
            self.motype = mo_type
            doc, config = self.main_rcp_msg_start(msg_id=F'{mo_type}Function')
            me_mo = self.mo_add_form_dict_xml({'managedElementId': self.node}, 'ManagedElement')
            config.appendChild(me_mo)
            xml_mo = self.mo_add_form_dict_xml({self.get_moc_id(moc=F'{mo_type}Function'): '1'}, F'{mo_type}Function')
            me_mo.appendChild(xml_mo)
            for mo in self.db_append_child_special_method(moc_dict=moc_dict[mo_type], parent_ldn=self.dcgk_function_ldn()):
                xml_mo.appendChild(mo)
            rcp_msgs.append(doc)
        return rcp_msgs

    # Old Tested
    # def create_rpc_msg(self) -> list:
    #     rcp_msgs = []
    #     doc, config = self.main_rcp_msg_start(msg_id='gnb_mos')
    #     me_mo = self.mo_add_form_dict_xml({'managedElementId': self.node}, 'ManagedElement')
    #     config.appendChild(me_mo)
    #
    #     moc_dict = self.get_nr_moc_dict()
    #     # Special rcp massage for GNBDUFunction=1,UeCC=1 which doesn't go through in combined script
    #     tmp_mo = {'UeCC': moc_dict['GNBDU']['UeCC'].copy()}
    #     ldn = 'GNBDUFunction=1,UeCC=1'
    #     mo_dict = {'managedElementId': self.node, 'GNBDUFunction': {'gNBDUFunctionId': '1', 'UeCC': {'ueCCId': '1'}}}
    #     # Complete MOs
    #     for mo_type in moc_dict.keys():
    #         self.motype = mo_type
    #         xml_mo = self.mo_add_form_dict_xml({self.get_moc_id(moc=F'{mo_type}Function'): '1'}, F'{mo_type}Function')
    #         for mo in self.db_append_child_special_method(moc_dict=moc_dict[mo_type]):
    #             xml_mo.appendChild(mo)
    #         me_mo.appendChild(xml_mo)
    #     return [doc]

    def get_nr_moc_dict(self) -> dict:
        # bb_type = self.enbdata.get('BBType', self.gnbdata.get('BBType'))

        moc_dict = {
            # GNBCUUPFunction
            'GNBCUUP': {
                'UeCC': {
                    'id': ['1'],
                    'AqmCfg': {'id': [
                        'Conversational_Video', 'Default_application_signaling', 'Default_conversational_media',
                        'Default_other', 'Non-Conversational_Video', 'Real_Time_Gaming',
                        'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000',
                        'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002',
                        'WPS_User'
                    ]},
                    'DcDlCfg': {'id': ['Default']},
                    # ----------- G3G4 Nodes
                    'DcUlCfg': {'id': ['Default']},
                    'L4sCfg': {'id': ['1', 'L10H20_L4S', 'L4H10_L4S', 'L8H16_L4S']},
                    'Drb': {'id': [
                        '5QI6_L4S', 'Conversational_Video', 'Default_application_signaling', 'Default_conversational_media',
                        'Default_other', 'L10H20_L4S', 'L4H10_L4S', 'L8H16_L4S', 'Non-Conversational_Video', 'Real_Time_Gaming',
                        'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000',
                        'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002', 'WPS_User'
                    ], 'DrbUeCfg': {'id': ['Base']}, },
                    'UserPlaneProfileCfg': {'id': ['']},
                    # ----------- No MOs Create, G3G4 Nodes
                    'UserPlaneProfileCgCat': {'id': [], 'UserPlaneProfileCgCatCfg': {'id': []}},
                    'UserPlaneProfile': {'id': ['Default'], 'UserPlaneProfileUeCfg': {'id': ['Base']}},
                },
                'CUUP5qiTable': {
                    'id': ['1', 'SD_1000', 'SD_10000', 'SD_10001', 'SD_1001', 'SD_2000', 'SD_2001',
                           'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000', 'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001',
                           'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                    'CUUP5qi': {'id': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '128', '129']},
                },
                'CardinalityLimits': {'id': ['1']},
                'DataPacketGenerator': {'id': [], 'DataPacketGeneratorUeCfg': {'id': []}},
                'GtpuSupervision': {'id': ['1'], 'GtpuSupervisionProfile': {'id': ['S1', 'X2']}},
                'ResourcePartitions': {
                    'id': ['1'],
                    'ResourcePartition': {
                        'id': ['FWA', 'SA', 'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000',
                               'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                        'ResourcePartitionMember': {'id': ['1']}},
                },
                # ----------- No MOs Create
                'EP_NgU': {'id': []},
                'EP_XnU': {'id': []},
                'PpControlTermination': {'id': [], 'PpControlLink': {'id': []}},
                'RpUserPlaneTermination': {'id': [], 'RpUserPlaneLink': {'id': []}},
                'S1UTermination': {'id': [], 'S1ULink': {'id': []}},
                'X2UTermination': {'id': [], 'X2ULink': {'id': []}},
                # 'TermPointToRsr': {'id': []},
                # 'Prototypes': {'id': [], 'PrototypeEntry': {'id': []}},
                # -----------
                # ----------- Custom Based on CQ Input
                'EndpointResource': {'id': [], 'LocalIPsecEndpoint': {'id': [], }, 'LocalIpEndpoint': {'id': []}},
                # -----------
            },



            # GNBCUCPFunction
            'GNBCUCP': {
                'UeCC': {
                    'id': ['1'],
                    'CapabilityHandling': {'id': ['1'], 'CapabilityHandlingUeCfg': {'id': ['Base']}},
                    'InactivityProfile': {'id': ['Default'], 'InactivityProfileUeCfg': {'id': ['Base', '1']}},
                    'Rohc': {'id': ['1'], 'RohcUeCfg': {'id': ['Base']}},
                    'RrcInactiveProfile': {'id': ['Default'], 'RrcInactiveProfileUeCfg': {'id': ['Base', 'blocklist']}},
                    'Rrc': {'id': ['1'], 'RrcUeCfg': {'id': ['Base']}},
                    'UaiProfile': {'id': ['Default'], 'UaiProfileUeCfg': {'id': ['Base']}},
                    # ----------- G3G4 Nodes
                    'DrbData': {'id': ['Default'], 'DrbDataUeCfg': {'id': ['Base']}},
                    'InitialCg': {'id': ['Default'], 'InitialCgUeCfg': {'id': ['Base']}},
                    'RrcInactiveEdrx': {'id': ['Default'], 'RrcInactiveEdrxUeCfg': {'id': ['Base']}},
                    'UlDataSplit': {'id': ['Default_endc', 'Default_nrdc'], 'UlDataSplitUeCfg': {'id': ['Base']}},
                    # -----------
                },
                'AdmissionControl': {
                    'id': ['1'],
                    'AdmissionLimit': {'id': ['Default']},
                    'AdmissionPriority': {
                        'id': ['Default', 'TMO_WPS'],
                        'AdmissionPriorityUeCfg': {'id': ['Base', 'E911_Users', 'SA_Traffic', 'Slicing_Users', 'VoNR', 'WPS']}},
                    'Uac': {'id': ['1'], 'UacProfile': {'id': ['Default', 'TMO_WPS'], 'BarringGroup': {'id': ['Default', 'WPS']}}},
                },
                'AnrFunction': {
                    'id': ['1'],
                    'AnrFunctionEUtran': {'id': ['1'], 'AnrFunctionEUtranUeCfg': {'id': ['Base']}},
                    'AnrFunctionNR': {'id': ['1'], 'AnrFunctionNRUeCfg': {'id': ['Base'], 'AnrPLMNTable': {'id': []}}},
                    # ----------- Only G3G4
                    'AnrPLMNTable': {'id': []},
                },
                'NrdcSnTermination': {'id': ['SnTerminationProhibited'], 'NrdcSnTerminationUeCfg': {'id': ['Default']}},
                'CUCP5qiTable': {
                    'id': ['1', 'SD_1000', 'SD_10000', 'SD_10001', 'SD_1001', 'SD_2000', 'SD_2001',
                           'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000', 'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000',
                           'SD_9001', 'SD_9002'],
                    'CUCP5qi': {'id': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '128', '129']},
                },
                'CarrierAggregation': {
                    'id': ['1'],
                    'CaCellMeasProfile': {'id': ['Default'], 'CaCellMeasProfileUeCfg': {'id': ['Base']}},
                    'CaCellProfile': {'id': ['Default'], 'CaCellProfileUeCfg': {
                        'id': ['Base', 'VoNR', 'MotoEdge_Austin_Wingtech', 'Austin_Wingtech', 'MotoEdge', 'Sercomm']}},
                    'CaFreqRelMeasProfile': {'id': ['Default'], 'CaFreqRelMeasProfileUeCfg': {'id': ['Base']}},
                },
                'EmCall': {'id': ['1']},
                'EsiSelectiveUeTracing': {'id': ['Default', 'TMO_WPS'], 'EsiSelectiveUeTracingCfg': {'id': ['Default', 'WPS']}},
                'IntraFreqMC': {
                    'id': ['1'],
                    'IntraFreqMCCellProfile': {'id': ['Default'], 'IntraFreqMCCellProfileUeCfg': {'id': ['Base']}},
                    # ----------- G3G4 Nodes
                    'IntraFreqMCLtmCellProfile': {'id': ['Default'], 'IntraFreqMCLtmCellProfileUeCfg': {'id': ['Base']}},
                },
                'Mcfb': {'id': ['1'], 'McfbCellProfile': {'id': ['Default'], 'McfbCellProfileUeCfg': {'id': ['Base']}}, },
                'UeUlResMon': {
                    'id': ['1'],
                    # ----------- G3G4 Nodes
                    'UlBufferMonCfg': {'id': ['Default']},
                    'UlQualMcpcMeasCfg': {'id': ['Default']},
                },
                'Mcpc': {
                    'id': ['1'],
                    'McpcNrdcPSCellProfile': {'id': ['Default'], 'McpcNrdcPSCellProfileUeCfg': {'id': ['Base']}, },
                    'McpcPCellEUtranFreqRelProfile': {'id': ['Default'], 'McpcPCellEUtranFreqRelProfileUeCfg': {'id': ['Base']}},
                    'McpcPCellNrFreqRelProfile': {'id': ['Default'], 'McpcPCellNrFreqRelProfileUeCfg': {'id': ['Base']}},
                    'McpcPCellProfile': {'id': ['Default'], 'McpcPCellProfileUeCfg': {'id': ['Base']}},
                    'McpcPSCellNrFreqRelProfile': {'id': ['Default'], 'McpcPSCellNrFreqRelProfileUeCfg': {'id': ['Base']}},
                    'McpcPSCellProfile': {'id': ['Default'], 'McpcPSCellProfileUeCfg': {'id': ['Base']}},
                },
                'Mdt': {'id': ['1'], 'MdtCellProfile': {'id': ['Default'], 'MdtCellProfileUeCfg': {'id': ['Base']}}, },
                'Nccm': {'id': ['1'], 'NccmUeCfg': {'id': ['Default']}},
                'NrdcControl': {'id': ['1'], 'NrdcMnCellProfile': {'id': ['Default'], 'NrdcMnCellProfileUeCfg': {'id': ['Base']}}, },
                'PciHandling': {
                    'id': ['1'],
                    'PciConflictEUtran': {'id': ['1'], 'PciConflictEUtranUeCfg': {'id': ['Base', 'VONR']}},
                    'PciConflictNR': {'id': ['1'], 'PciConflictNRUeCfg': {'id': ['Base', 'VONR']}},
                },
                'Periodic': {'id': ['1'], 'PeriodicCellProfile': {'id': ['Default'], 'PeriodicCellProfileUeCfg': {'id': ['Base']}}, },
                # ----------- G3G4 Nodes
                'PeriodicUeMeas': {'id': ['1'], 'PuemCellProfile': {'id': ['Default'], 'PuemCellProfileUeCfg': {'id': ['Base']}}},
                'PmUeMeas': {'id': ['1'], 'PmUeIntraFreqCellProfile': {'id': ['Default']}, },
                'PriorityService': {'id': ['1']},
                'UeNoDrb': {'id': ['1'], 'UeNoDrbPCellProfile': {'id': ['Default'], 'UeNoDrbPCellProfileUeCfg': {'id': ['Base']}}, },
                # -----------
                # ----------- Only G2 Nodes
                'QciProfileEndcConfigExt': {'id': ['1']},
                'RelaxedRrmMeas': {'id': [], 'RelaxedRrmMeasCellProfile': {'id': []}, },
                'ResourcePartitions': {'id': ['1'], 'ResourcePartition': {
                    'id': ['FWA', 'SA', 'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000',
                           'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                    'ResourcePartitionMember': {'id': ['1']}}, },
                'SecurityHandling': {'id': ['1']},
                'TrafficOffload': {
                    'id': ['1'],
                    'OffloadCellProfile': {'id': ['Default'], 'OffloadCellProfileUeCfg': {'id': ['Base', 'VoNR', 'WPS_User']}},
                    'OffloadEUtranFreqRelProfile': {'id': ['Default'], 'OffloadEUtranFreqRelProfileUeCfg': {'id': ['Base']}},
                    'OffloadNrFreqRelProfile': {'id': ['Default'], 'OffloadNrFreqRelProfileUeCfg': {'id': ['Base']}},
                },
                'TrafficSteering': {
                    'id': ['1'],
                    'TrStPSCellNrFreqRelProfile': {'id': ['Default'], 'TrStPSCellNrFreqRelProfileUeCfg': {'id': ['Base']}},
                    'TrStPSCellProfile': {'id': ['Default'], 'TrStPSCellProfileUeCfg': {'id': ['Base']}},
                    'TrStSaCellProfile': {'id': ['Default'], 'TrStSaCellProfileUeCfg': {'id': ['Base']}},
                    'TrStSaEUtranFreqRelProfile': {'id': ['Default'], 'TrStSaEUtranFreqRelProfileUeCfg': {'id': ['Base']}},
                    'TrStSaNrFreqRelProfile': {'id': ['Default'], 'TrStSaNrFreqRelProfileUeCfg': {'id': ['Base']}},
                },
                'UeCovMeas': {
                    'id': ['1'],
                    'UcmCellProfile': {'id': ['Default'], 'UcmCellProfileUeCfg': {'id': ['Base', 'VoNR']}},
                    # ----------- Only G3G4
                    'UcmEUtranFreqRelProfile': {'id': ['Default']},
                    'UcmNrFreqRelProfile': {'id': ['Default']},
                },
                'UeGroupSelection': {
                    'id': ['1'],
                    'Chipsets': {'id': []},
                    'ImeiSvs': {'id': ['BSW_Cond_GA', 'DCSC_Problematic_UE', 'S24_Ultra_ULCA', 'N41_Mobility_Blocking']},
                    'ImeiSvGroups': {
                        'id': ['1'],
                        'ImeiSvGroup': {'id': ['BSW_Cond_GA', 'Google', 'Motorola', 'Others', 'S24_Ultra_ULCA',
                                               'Samsung', 'S24_FanSE_ULCA', 'S24_Fan_ULCA', 'S24_UltraSE_ULCA',
                                               'N41_Mobility_Blocking']}},
                    'PrefUeGroupSelectionProfile': {'id': []},
                    'UeAdmissionGroupDefinition': {'id': ['E911_Users', 'SA_Traffic', 'Slicing_Users',
                                                          'VoNR', 'WPS_Users', ]},
                    'UeGroupSelectionProfile': {
                        'id': ['14', '2', 'GalaxyA53', 'HSI', 'Pixel_6', 'Pixel_6B', 'SD_2000', 'SD_3001', 'SD_6000', 'SD_6001',
                               'SD_9000', 'SD_9001', 'SD_9002', 'VoNR', 'MotoEdge_Austin_Wingtech', 'pCellOnlyUe']
                    },
                    'UeMobilityGroupDefinition': {'id': ['Default', 'BSW_Cond_GA', '9', 'MotoG5G2024', 'N41_Mobility_Blocking']},
                    'UeServiceGroupDefinition': {'id': ['Sercomm', 'RRCinactive_ProblemDevice']},
                },
                'UeMC': {
                    'id': ['1'],
                    'UeMCCellProfile': {'id': ['Default'], 'UeMCCellProfileUeCfg': {'id': ['Base', 'VoNR']}},
                    'UeMCEUtranFreqRelProfile': {'id': ['Default'], 'UeMCEUtranFreqRelProfileUeCfg': {'id': ['Base', 'VoNR']}},
                    'UeMCNrFreqRelProfile': {'id': ['Default'], 'UeMCNrFreqRelProfileUeCfg': {'id': ['Base', 'VoNR']}},
                    'UeMCUeCfg': {'id': ['Base']},
                },
                # ----------- Only G3G4 Nodes with B41 Cells Only
                'EnergyPerformance': {'id': ['1'], 'EpBoCS': {'id': ['1'], 'EpBoosterAdvCfg': {'id': ['Default']},
                                                              'EpBoosterCellProfile': {'id': ['Default']}, }},
                'TimeSchedulingGroup': {'id': ['1'], 'TimeSchedulingWindow': {'id': ['1']}},
                # -----------



                # ----------- No MOs Create
                'TermPointToGNBCUUP': {'id': []},
                'TermPointToGNBDU': {'id': []},
                # ----------- Only G3G4
                'BlockedGNodeB': {'id': []},
                'CardinalityLimits': {'id': []},
                'CellGroupCategoryDefinition': {'id': []},
                # -----------
                # -----------
                # ----------- Custom Based on CQ Input
                'TermPointToAmf': {'id': [], 'TnlAssociation': {'id': [], }},
                'EndpointResource': {'id': [], 'LocalA1Endpoint': {'id': []}, 'LocalDnsEndpoint': {'id': []},
                                     'LocalIpEndpoint': {'id': []}, 'LocalSctpEndpoint': {'id': []}, },
                'NRCellCU': {'id': [], 'AdditionalPLMNInfo': {'id': []}, 'DESManagementFunction': {'id': []},
                             'EUtranCellRelation': {'id': []}, 'EUtranFreqRelation': {'id': []},
                             'NRCellRelation': {'id': []}, 'NRFreqRelationTemplate': {'id': []}, 'NRFreqRelation': {'id': []},
                             'RibTmRelation': {'id': []}, },
                'NRNetwork': {
                    'id': [], 'ExternalGNBCUCPFunction': {
                        'id': [], 'ExternalNRCellCU': {'id': []}, 'ExternalBroadcastPLMNInfo': {'id': []}, 'TermPointToGNodeB': {'id': []}, },
                    'NRFrequency': {'id': [], 'NRFrequencyUeCfg': {'id': []}, },
                },
                'EUtraNetwork': {'id': [], 'EUtranFrequency': {'id': []}, 'ExternalENodeBFunction': {
                    'id': [], 'ExternalEUtranCell': {'id': []}, 'TermPointToENodeB': {'id': [], 'DirectIPsec': {'id': []}}},
                                 },
                # -----------
            },



            # GNBDUFunction
            'GNBDU': {
                'UeCC': {
                    'id': ['1'],
                    'AqmCfg': {
                        'id': ['Conversational_Video', 'Default_application_signaling', 'Default_conversational_media',
                               'Default_other', 'Non-Conversational_Video', 'Real_Time_Gaming',
                               'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_6000', 'SD_6001',
                               'SD_9000', 'SD_9001', 'SD_9002', 'WPS_User'],
                    },
                    'Bsr': {
                        'id': ['1'],
                        'BsrUeCfg': {'id': ['Base', 'LowLatency', 'LowLatency_high', 'LowLatency_mid', 'VoNR']}
                    },
                    'ConfiguredGrant': {'id': ['1'], 'ConfiguredGrantUeCfg': {'id': ['Base', 'SD_6000', 'SD_6001']}},
                    'DlMimo': {'id': ['1'], 'DlMimoUeCfg': {'id': ['Base']}},

                    'CgSwitchCfg': {'id': ['Default']},
                    'CgSwitch': {'id': ['Default'], 'CgSwitchUeCfg': {'id': ['Base']}},
                    # ----------- Only G3G4
                    'CsiProfile': {'id': ['1'], 'CsiProfileUeCfg': {'id': ['Base', 'VoNR']}},
                    'DlBeamOptProfile': {'id': ['1'], 'DlBeamOptProfileUeCfg': {'id': ['Base', 'HIS']}},
                    'OutOfCov': {'id': ['1'], 'OutOfCovUeCfg': {'id': ['Base']}},
                    'SrbPriority': {
                        'id': ['Default'],
                        'SrbPriorityUeCfg': {'id': ['Base', 'E911_Users', 'SA_Traffic', 'Slicing_Users', 'VoNR', 'WPS']},
                    },
                    'UeAmbr': {'id': ['Default'], 'UeAmbrUeCfg': {'id': ['Base']}, },
                    'UlCgSwitchCfg': {'id': ['Default'], },
                    'UlCgSwitch': {'id': ['Default'], 'UlCgSwitchUeCfg': {'id': ['Base']}, },
                    'UlMimo': {'id': ['1'], 'UlMimoUeCfg': {'id': ['Base', 'OneTxPort', 'HSI', 'VoNR']}},
                    # -----------
                    'DrbUp': {
                        'id': ['Conversational_Video', 'Default_application_signaling', 'Default_conversational_media',
                               'Default_other', 'Non-Conversational_Video', 'Real_Time_Gaming',
                               'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_6000', 'SD_6001',
                               'SD_9000', 'SD_9001', 'SD_9002', 'WPS_User'],
                        'DrbUpUeCfg': {'id': ['Base']},
                    },
                    'DrxProfile': {
                        'id': ['Default'],
                        'DrxProfileUeCfg': {'id': ['Base', 'DRX_OFF', 'SD_6001', 'VONR'], 'PuschRepRel16Drx': {'id': ['1']}}
                    },
                    'Harq': {'id': ['1'], 'HarqUeCfg': {'id': ['Base', 'SD_2000', 'SD_6000', 'SD_6001', 'WPS_User', 'VoNR']}, },
                    'L4sCfg': {'id': ['1', 'L10H20_L4S', 'L4H10_L4S', 'L8H16_L4S']},
                    'LinkAdaptation': {
                        'id': ['1'],
                        'LinkAdaptationUeCfg': {
                            'id': ['Base', 'SD_10000', 'SD_2000', 'SD_6000', 'SD_6001', 'VoNR', ],
                            'DlLinkAdaptation': {'id': ['1']},
                            'PdcchLinkAdaptation': {'id': ['1']},
                            'UlLinkAdaptation': {'id': ['1']},
                        },
                    },
                    'LogicalChannel': {'id': ['Default', 'IMS_Voice'], 'LogicalChannelUeCfg': {'id': ['Base']}},
                    'PdcchReuseForPdsch': {'id': ['Default'], 'PdcchReuseForPdschUeCfg': {'id': ['Base']}},
                    'PowerControl': {'id': ['1'], 'PowerControlUeCfg': {'id': ['Base', '1', 'VoNR']}},
                    'Prescheduling': {'id': ['1'], 'PreschedulingUeCfg': {'id': ['Base', 'SD_2000', 'SD_3001', 'SD_6000', 'SD_6001', 'SD_900X']}},
                    'PuschRep': {'id': ['Default', 'VoNR_Dynamic'], 'PuschRepUeCfg': {'id': ['Base']}},
                    'Rach': {'id': ['Default'], 'RachUeCfg': {'id': ['Base']}},
                    'RadioLinkControl': {
                        'id': ['1'],
                        'DrbRlc': {'id': ['Default', 'IMS-SIP', 'Video', 'VoNR', 'gaming'], 'DrbRlcUeCfg': {'id': ['Base']}},
                        'UeAdaptiveRlc': {'id': ['1'], 'UeAdaptiveRlcUeCfg': {'id': ['Base']}},
                    },
                    'ResourceAllocTypeDl': {'id': ['Default'], 'ResourceAllocTypeDlUeCfg': {'id': ['Base']}},
                    'RimOffload': {'id': ['1'], 'RimOffloadUeCfg': {'id': ['Base']}},
                    'SchedulingProfile': {
                        'id': [
                            '5QI129', '5QI6', '5QI7', '5QI8', '5QI9', 'RPS_64',
                            'SD_10000_SST_1_5QI6', 'SD_10001_SST_1_5QI6', 'SD_2000_SST_1_5QI6', 'SD_2001_SST_1_5QI6',
                            'SD_3000_SST_1_5QI6', 'SD_3001_SST_1_5QI6', 'SD_3002_SST_1_5QI6',
                            'SD_4000_SST_1_5QI6', 'SD_6000_SST_1_5QI6', 'SD_6001_SST_1_5QI6',
                            'SD_7000_SST_1_5QI6', 'SD_8000_SST_1_5QI6', 'SD_8001_SST_1_5QI6',
                            'SD_9000_SST_1_5QI6', 'SD_9001_SST_1_5QI6', 'SD_9002_SST_1_5QI6',
                            'WPS_2X_User_5QI128', 'WPS_Slice_User_5QI128', 'WPS_Slice_User_5QI6', 'WPS_User_5QI128',
                            'SD_2000_SST_1_5QI7', 'SD_2000_SST_1_5QI8', 'SD_2000_SST_1_5QI9',
                            'SD_4000_SST_1_5QI7', 'SD_4000_SST_1_5QI8', 'SD_4000_SST_1_5QI9',
                            'SD_6000_SST_1_5QI7', 'SD_6000_SST_1_5QI8', 'SD_6000_SST_1_5QI9',
                            'SD_8000_SST_1_5QI7', 'SD_8000_SST_1_5QI8', 'SD_8000_SST_1_5QI9'
                            # 'NSA_5QI129', 'NSA_5QI6', 'NSA_5QI7', 'NSA_5QI8', 'NSA_5QI9',
                        ],
                        'DlDelayBasedPriority': {'id': '1'},
                        'DlRateBasedPriority': {'id': '1'},
                        'DlResourceBasedPriority': {'id': '1'},
                        'UlDelayBasedPriority': {'id': '1'},
                        'UlRateBasedPriority': {'id': '1'},
                        'UlResourceBasedPriority': {'id': '1'},
                        # ----------- Only G3G4
                        'DlLatencyBasedPriority': {'id': '1'},
                        'UlLatencyBasedPriority': {'id': '1'},
                        # -----------

                    },
                    'SoftAcAssist': {'id': ['1'], 'SoftAcAssistUeCfg': {'id': ['Base', 'HSI']}},
                    'SrHandling': {'id': ['5QI_5', 'Default', 'SD_2000', 'SD_6000', 'SD_6001'], 'SrHandlingUeCfg': {'id': ['Base']}},
                    'SrPeriodicity': {'id': ['Default'], 'SrPeriodicityCovAdaptUeCfg': {'id': ['Base']},
                                      'SrPeriodicityUeCfg': {'id': ['Base', 'SD_2000', 'SD_6000']}, },
                    'UlServiceDefinition': {
                        'id': ['1'],
                        'UlServiceDefinitionUeCfg': {'id': ['Base', 'SD_2000', 'SD_6000', 'SD_6001', 'VoNR'], 'UlService': {'id': ['1']}}
                    },
                    'UlWfPortSwitch': {'id': ['1'], 'UlWfPortSwitchUeCfg': {'id': ['Base', 'VoNR', 'VoNR_OneTxPort', 'OneTxPort']}},

                    'UeBb': {
                        'id': ['1'],
                        'UeBbProfile': {'id': ['Default'], 'UeBbProfileUeCfg': {
                            # NSA for N41
                            'id': ['Base', 'SD_2000', 'SD_3001', 'SD_6000', 'SD_6001', 'SD_9000_1', 'SD_9002', 'VoNR',
                                   'HSI', 'MotoRazr25']}, },
                    },
                    # 26.Q1 G3G4
                    'UplinkComp': {'id': ['1'], 'UplinkCompUeCfg': {'id': ['Base']}}
                },
                'AdmissionControl': {
                    'id': ['1'],
                    'CallQueuing': {'id': ['1'], 'CallQueuingProfile': {'id': ['Default']}},
                    'CchLoadProfile': {'id': ['Default']},
                },
                # Only G3G4
                'ContentionControl': {
                    'id': ['1'],
                    'SessionLimit': {'id': ['Default', 'WPS_NSA', 'WPS_SA'], 'FlowLimit': {'id': ['Default', 'MMBB_WPS']}},
                },
                'DU5qiTable': {
                    'id': ['1', 'SD_1000', 'SD_10000', 'SD_10001', 'SD_1001', 'SD_2000', 'SD_2001',
                           'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000', 'SD_6000', 'SD_6001',
                           'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                    'DU5qi': {'id': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '128', '129']}
                },
                'DUQos': {
                    'id': ['1'],
                    'AutomatedQos': {'id': ['1'], 'RrpController': {'id': ['NO_AUTO_CONTROL']}},
                    'ExtCaPriority': {'id': ['1', 'Default']},
                    'QosPriorityShift': {'id': ['1'], 'CellPriorityShift': {'id': ['1']}},
                },
                # Only G3G4
                'EnergyEfficiency': {
                    'id': ['1'],
                    'EnergyOptPwrAlloc': {
                        'id': ['Default'],
                        'EnergyOptPwrAllocUeCfg': {'id': ['Base', 'VoNR']}},
                    'EnergyOptScheduling': {'id': ['Default']},
                    'EnergyOptSymAlloc': {'id': ['Default', 'EOSyA']},
                },
                # Only for N41 and AIR 66 and 66 Antenna
                'MassiveMimoSleep': {'id': ['1'], 'MMimoSleepProfile': {'id': ['1']},
                                     'MMimoSleepTimeGroup': {'id': ['1'], 'MMimoSleepTimeWindow': {'id': ['1']}}, },
                'Paging': {'id': ['1']},
                'QosPriorityMapping': {
                    'id': ['1'],
                    'PriorityDomainMapping': {'id': ['5QI1', '5QI2', '5QI5', '5QI6_7_8_9', '5QI_128_WPS_User', '5QI_6_SLICE_900X']}
                },
                'RadioBearerTable': {'id': ['1'], 'SignalingRadioBearer': {'id': ['1']}},
                'ResourcePartitions': {
                    'id': ['1'],
                    'ResourcePartition': {
                        'id': ['FWA', 'SA', 'SD_10000', 'SD_10001', 'SD_2000', 'SD_2001', 'SD_3000', 'SD_3001', 'SD_3002', 'SD_4000',
                               'SD_6000', 'SD_6001', 'SD_7000', 'SD_7001', 'SD_8000', 'SD_8001', 'SD_9000', 'SD_9001', 'SD_9002'],
                        'ResourcePartitionMember': {'id': ['1']}, },
                },
                'ResourceAllocationPolicies': {
                    'id': ['1'],
                    'ResourceShareLimit': {'id': []},
                    'ResourceAllocationPolicy': {
                        'id': ['FWA', 'SD_10000', 'SD_2000', 'SD_4000', 'SD_6000', 'SD_6001', 'SD_8000', 'SD_8001',
                               'SD_9000', 'SD_9001', 'SD_9002', 'eMBB'], 'ServicePolicy': {'id': []}},
                    'CellResourceMapping': {
                        'id': ['1'],
                        'PartitionMapping': {
                            'id': ['FWA', 'SD_10000', 'SD_2000', 'SD_4000', 'SD_6000', 'SD_6001', 'SD_8000', 'SD_8001',
                                   'SD_9000', 'SD_9001', 'SD_9002', 'eMBB']}},
                },
                # Only G3G4 systemCreated
                'RimRSGlobal': {'id': ['1'], 'RimRSSet': {'id': []}},
                # -----------
                'Rrc': {'id': ['1']},
                'SrPeriodicityPoolSet': {'id': ['1']},
                'TermPointToGNBCUCP': {'id': ['1']},
                # Only G3G4
                'TrafficDefinitions': {
                    'id': ['1'],
                    'TrafficDefinition': {'id': ['Default', 'WPS'], 'TrafficSet': {'id': ['Default', 'Default_ENDC']},
                                          'TrafficSetMember': {'id': ['Default_SA', 'Default_ENDC']}}
                },
                'UeCA': {
                    'id': ['1'],
                    'CaSCellHandling': {'id': ['1', 'Default'], 'CaSCellHandlingUeCfg': {'id': ['Base', 'SA', 'VoNR']}}
                },

                # ----------- preliminary
                # 'PrototypeConfig': {'id': [], 'PrototypeConfigUeCfg': {'id': [], 'PrototypeEntry': {'id': []}}},
                # 'UplinkComp': {'id': ['1'], 'UplinkCompUeCfg': {'id': ['Base']}},
                # -----------
                # ----------- MOs not found in DCGKs
                'Aes': {'id': []},
                # Only G3G4 systemCreated
                'ExtENodeBPartnerFunction': {'id': [], 'LteInterMeLink': {'id': []}},

                # -----------
                # ----------- Only for N41, It's defined by smart script
                'BWPSet': {'id': [], 'BWPSetUeCfg': {'id': [], 'BWPSetCfg': {'id': []}}, 'DynPowerOpt': {'id': [], }},
                'BWP': {'id': []},
                # -----------
                'CardinalityLimits': {'id': []},
                'CtsFunction': {'id': [], 'TermPointToCts': {'id': []}},
                'DUQosModifier': {'id': [], 'DUModified5qi': {'id': [], 'DUModified5qiUeCfg': {'id': []}}},
                'NRSynchronization': {'id': []},
                # -----------
                # ----------- Only G3G4
                'SssgSwitch': {'id': [], 'SssgSwitchPwrOpt': {'id': []}, 'SssgSwitchUeCfg': {'id': []}},
                # ----------- Only G2
                'TrafficGroups': {'id': [], 'TrafficGroup': {'id': [], 'TrafficGroupMember': {'id': []}}},
                # ----------- Based on CQ Input
                'EndpointResource': {'id': [], 'LocalIpEndpoint': {'id': []}, 'LocalSctpEndpoint': {'id': []}},
                'NRSectorCarrier': {
                    'id': [], 'AesMMimoSleep': {'id': []}, 'CommonBeamforming': {'id': [], 'Beam': {'id': []}},
                    'NRPimCancellationConfig': {'id': []}, 'PowerBackoffDir': {'id': []}, 'PowerBackoff': {'id': []},
                },
                'NRCellDU': {'id': [], 'AdditionalPLMNInfo': {'id': []}, 'CellPortionRd': {'id': []}, 'DlOuterLoop': {'id': []}},
                'ExtGNBDUPartnerFunction': {'id': [], 'InterMeLink': {'id': []}},
                # -----------
            },
        }
        # MOs additions
        # NR LB Additions
        # if self.df_gnb_cell.loc[self.df_gnb_cell.postcell.str.startswith(('K', 'J', 'I'))].shape[0] > 0:

        # N2 MOs additions
        if self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.contains('^J'))].shape[0] > 0:
            moc_dict['GNBCUCP']['UeGroupSelection']['UeServiceGroupDefinition']['id'].append('RedCap_UE')
        # N41 MOs additions
        if self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.contains('^A'))].shape[0] > 0:
            moc_dict['GNBCUCP']['CUCP5qiTable']['id'].append('2')
            moc_dict['GNBCUUP']['CUUP5qiTable']['id'].append('2')
            moc_dict['GNBDU']['DU5qiTable']['id'].append('2')
            moc_dict['GNBCUCP']['ResourcePartitions']['ResourcePartition']['id'].append('NSA')
            moc_dict['GNBCUUP']['ResourcePartitions']['ResourcePartition']['id'].append('NSA')
            moc_dict['GNBDU']['ResourcePartitions']['ResourcePartition']['id'].append('NSA')
            moc_dict['GNBCUCP']['UeGroupSelection']['UeServiceGroupDefinition']['id'].extend(['1', '2', '3'])

            moc_dict['GNBDU']['UeCA']['CaSCellHandling']['CaSCellHandlingUeCfg']['id'].append('NSA')
            moc_dict['GNBDU']['UeCC']['SchedulingProfile']['id'].extend(['NSA_5QI6', 'NSA_5QI7', 'NSA_5QI8', 'NSA_5QI9', 'NSA_5QI129'])
            moc_dict['GNBDU']['UeCC']['UeBb']['UeBbProfile']['UeBbProfileUeCfg']['id'].append('NSA')
            if self.bbversion in 'G3G4':
                moc_dict['GNBCUCP']['EnergyPerformance']['EpBoCS']['EpBoosterAdvCfg']['id'].append('1')
                moc_dict['GNBCUCP']['EnergyPerformance']['EpBoCS']['EpBoosterCellProfile']['id'].append('1')
        else:
            if 'TimeSchedulingGroup' in moc_dict['GNBCUCP'].keys(): del moc_dict['GNBCUCP']['TimeSchedulingGroup']
            if 'EnergyPerformance' in moc_dict['GNBCUCP']['EnergyPerformance'].keys():
                del moc_dict['GNBCUCP']['EnergyPerformance']['EpBoCS']
            moc_dict['GNBDU']['UeCC']['SoftAcAssist']['SoftAcAssistUeCfg']['id'].append('HSI')
        # Only for N41 and AIR  6648 and 6649 Antenna
        if len([True for _ in self.df_gnb_cell.frutypecix if len([radio for radio in _ if re.match(r'AIR.*64.*', radio)]) > 0]) == 0:
            del moc_dict['GNBDU']['MassiveMimoSleep']

        # Removed MOCs for G2 Nodes where it doesn't exist
        if self.bbversion in 'G2':
            # TMO Specific
            for moc in ['PmUeMeas', 'PriorityService']:
                if moc in moc_dict['GNBCUCP'].keys(): del moc_dict['GNBCUCP'][moc]
            # Only in G3G4 Nodes
            for moc in ['AnrPLMNTable', 'BlockedGNodeB', 'CardinalityLimits', 'CellGroupCategoryDefinition', 'EnergyPerformance',
                        'IntraFreqMCLtmCellProfile', 'McpcNrdcPSCellProfileUeCfg', 'PeriodicUeMeas', 'RelaxedRrmMeas', 'TimeSchedulingGroup',
                        'UeNoDrb']:
                if moc in moc_dict['GNBCUCP'].keys(): del moc_dict['GNBCUCP'][moc]
            if 'DrbData' in moc_dict['GNBCUCP']['UeCC'].keys(): del moc_dict['GNBCUCP']['UeCC']['DrbData']
            if 'InitialCg' in moc_dict['GNBCUCP']['UeCC'].keys(): del moc_dict['GNBCUCP']['UeCC']['InitialCg']
            if 'RrcInactiveEdrx' in moc_dict['GNBCUCP']['UeCC'].keys(): del moc_dict['GNBCUCP']['UeCC']['RrcInactiveEdrx']
            if 'UlDataSplit' in moc_dict['GNBCUCP']['UeCC'].keys(): del moc_dict['GNBCUCP']['UeCC']['UlDataSplit']
            if 'UcmEUtranFreqRelProfile' in moc_dict['GNBCUCP']['UeCovMeas'].keys(): del moc_dict['GNBCUCP']['UeCovMeas']['UcmEUtranFreqRelProfile']
            if 'UlBufferMonCfg' in moc_dict['GNBCUCP']['UeUlResMon'].keys(): del moc_dict['GNBCUCP']['UeUlResMon']['UlBufferMonCfg']
            # Only in G3G4 Nodes
            if 'DcUlCfg' in moc_dict['GNBCUUP']['UeCC'].keys(): del moc_dict['GNBCUUP']['UeCC']['DcUlCfg']
            if 'UserPlaneProfileCfg' in moc_dict['GNBCUUP']['UeCC'].keys(): del moc_dict['GNBCUUP']['UeCC']['UserPlaneProfileCfg']
            if 'UserPlaneProfileCgCat' in moc_dict['GNBCUUP']['UeCC'].keys(): del moc_dict['GNBCUUP']['UeCC']['UserPlaneProfileCgCat']
            # Only in G3G4 Nodes
            for moc in ['Aes', 'CtsFunction', 'EnergyEfficiency', 'ExtENodeBPartnerFunction', 'SssgSwitch', 'TrafficDefinitions', ]:
                if moc in moc_dict['GNBDU'].keys(): del moc_dict['GNBDU'][moc]
            for moc in ['CsiProfile', 'DlBeamOptProfile', 'OutOfCov', 'SrbPriority', 'UeAmbr', 'UlCgSwitchCfg',
                        'UlCgSwitch', 'UplinkComp', 'UlMimo']:
                if moc in moc_dict['GNBDU']['UeCC'].keys(): del moc_dict['GNBDU']['UeCC'][moc]
            if 'AesMMimoSleep' in moc_dict['GNBDU']['NRSectorCarrier'].keys(): del moc_dict['GNBDU']['NRSectorCarrier']['AesMMimoSleep']
            if 'AiDlLinkAdaptation' in moc_dict['GNBDU']['UeCC']['LinkAdaptation']['LinkAdaptationUeCfg'].keys():
                del moc_dict['GNBDU']['UeCC']['LinkAdaptation']['LinkAdaptationUeCfg']['AiDlLinkAdaptation']
            if 'DlLatencyBasedPriority' in moc_dict['GNBDU']['UeCC']['SchedulingProfile'].keys():
                del moc_dict['GNBDU']['UeCC']['SchedulingProfile']['DlLatencyBasedPriority']
            if 'UlLatencyBasedPriority' in moc_dict['GNBDU']['UeCC']['SchedulingProfile'].keys():
                del moc_dict['GNBDU']['UeCC']['SchedulingProfile']['UlLatencyBasedPriority']
            # TMO Specific ---- GEN3 BB and Above Features - BB6630 and BB5216 Excluded
            if 'ContentionControl' in moc_dict['GNBDU'].keys(): del moc_dict['GNBDU']['ContentionControl']
        # Removed MOCs for G3G4 Nodes where it doesn't exist
        if self.bbversion in 'G3G4':
            if 'QciProfileEndcConfigExt' in moc_dict['GNBCUCP'].keys(): del moc_dict['GNBCUCP']['QciProfileEndcConfigExt']
            if 'TrafficGroups' in moc_dict['GNBDU'].keys(): del moc_dict['GNBDU']['TrafficGroups']

        # TMO_25_Q2 Start
        if self.usid.client.software.swname[:9] < 'TMO_25_Q2':
            for moc in ['PeriodicUeMeas', 'PmUeMeas', 'PriorityService']:
                if moc in moc_dict['GNBCUCP'].keys(): del moc_dict['GNBCUCP'][moc]
            # ToDo: Check and validate      Only in G3G4 Nodes
            if 'UeUlResMon' in moc_dict['GNBCUCP'].keys(): del moc_dict['GNBCUCP']['UeUlResMon']

        return moc_dict



    def dcgk_function_ldn(self) -> str or None:
        # DCGK LDN of GNBDUFunction / GNBCUCPFunction / GNBCUUPFunction for existing node, None for new node
        return self.gnbdata.get(F'{self.motype}Function') if self.site else None

    def update_mo_dict_with_dcgk(self, mo_dict: dict, mo_name, ldn: str or None) -> dict:
        # Same as log_append_child_tags: DB gives parameter list, DCGK value gets preference, backupflag True keeps DB value
        # MO references (...Ref) stay from DB, MO instances are created from moc_dict so DCGK reference may point to missing MO
        if ldn is None or self.site.dcg.get(ldn) is None: return mo_dict
        mo_attrs_site = self.site.get_mo_attr_str(ldn)
        moc_id = self.get_moc_id(moc=mo_name.moc)
        # DB id value not same as DB moid (Excel data mismatch, e.g. moid Sercomm with id RedCap_UE): keep DB values
        if str(mo_dict.get(moc_id)) != mo_name.moid.split(',')[-1]: return mo_dict
        db_preferred = [self.lower_first_char(_) for _ in self.get_db_backupflag_attributes(mo_name.moc, mo_name.moid)]
        for key in mo_dict:
            if key == moc_id or key.endswith('Ref') or key in db_preferred: continue
            mo_dict[key] = mo_attrs_site.get(key, mo_dict[key])
        return mo_dict

    def db_append_child_special_method(self, *, moc_dict, parent_ldn: str = None) -> list:
        ret_mos = []
        for moc in moc_dict.keys():
            if moc == 'id' or moc_dict[moc].get('id') is None or len(moc_dict[moc].get('id')) == 0: continue
            mo_names = self.MoName.objects.filter(moc=moc, software=self.usid.client.software, motype=self.motype)
            for mo_name in mo_names:
                if mo_name.moid in moc_dict[moc].get('id'):
                    xml_mo = self.append_child_tags_special_method(mo_name=mo_name, moc_dict=moc_dict[moc], moid=mo_name.moid, parent_ldn=parent_ldn)
                    if xml_mo: ret_mos.append(xml_mo)
        return ret_mos

    def sub_mo_db_append_child_special_method(self, *, moc_dict, sub_moc: str, moid: str = '1', parent_ldn: str = None) -> list:
        ret_mos = []
        for moc in moc_dict.keys():
            if moc == 'id' or moc_dict[moc].get('id') is None or len(moc_dict[moc].get('id')) == 0: continue
            if moc != sub_moc: continue
            mo_names = self.MoName.objects.filter(moc=moc, software=self.usid.client.software, motype=self.motype)
            moid_list = [F'{moid},{_}' for _ in moc_dict[moc].get('id')]
            for mo_name in mo_names:
                if mo_name.moid in moid_list:
                    xml_mo = self.append_child_tags_special_method(mo_name=mo_name, moc_dict=moc_dict[moc], moid=mo_name.moid, parent_ldn=parent_ldn)
                    if xml_mo: ret_mos.append(xml_mo)
        return ret_mos

    def append_child_tags_special_method(self, mo_name, moc_dict, moid, parent_ldn: str = None) -> Element or None:
        mo_dict = self.get_mo_related_attributes(mo_name)
        mo_dict |= {self.get_moc_id(moc=mo_name.moc): mo_dict.get(self.get_moc_id(moc=mo_name.moc)).split(',')[-1]}
        ldn = F'{parent_ldn},{mo_name.moc}={moid.split(",")[-1]}' if parent_ldn else None
        mo_dict = self.update_mo_dict_with_dcgk(mo_dict, mo_name, ldn)
        parent_mo = self.mo_add_form_dict_xml(copy.deepcopy(mo_dict), mo_name.moc)
        for moc in moc_dict.keys():
            if moc == 'id' or moc_dict[moc].get('id') is None or len(moc_dict[moc].get('id')) == 0: continue
            moid_list = [F'{moid},{_}' for _ in moc_dict[moc].get('id')]
            for moc_c in self.MoName.objects.filter(moc=moc, software=self.usid.client.software, motype=self.motype):
                # print(F'{moc} -> {moid_list} -> {moc_c.moid}')
                if moc_c.moid not in moid_list: continue
                child_mo = self.append_child_tags_special_method(moc_c, moc_dict=moc_dict[moc], moid=moc_c.moid, parent_ldn=ldn)
                if child_mo: parent_mo.appendChild(child_mo)
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


    # @staticmethod
    # def validate_db_moid(*, moid: str) -> bool:
    #     return True if moid in [None, 'None', '', 'XX', 'nan', np.nan, '""'] or ',' in moid else False
    #
    # def db_append_child_tags(self, motype, rel_tag):
    #     ret_mos = []
    #     if motype in self.custom_moc: return ret_mos
    #     mo_tag_ins = self.MoName.objects.filter(moc=motype, software=self.usid.client.software, motype=self.motype)
    #     if mo_tag_ins.exists():
    #         for mo_tag_in in mo_tag_ins:
    #             if self.validate_db_moid(moid=mo_tag_in.moid): continue
    #             ret_mos.append(self.append_child_tags(mo_tag_in, rel_tag=rel_tag))
    #     return ret_mos
    #
    # def append_child_tags(self, motype, rel_tag):
    #     parent_mo = self.mo_add_form_dict_xml(self.get_mo_related_attributes(motype), motype.moc)
    #     for children in self.MoRelation.objects.filter(parent=motype.moc, tag=rel_tag, software=self.usid.client.software):
    #         for child in self.MoName.objects.filter(moc=children.child, software=self.usid.client.software, motype=self.motype):
    #             if self.validate_db_moid(moid=child.moid): continue
    #             if child.modetail_set.filter((Q(flag=True)) & (Q(bbversion='') | Q(bbversion__contains=self.bbversion))).exists():
    #                 child_mo = self.append_child_tags(child, rel_tag)
    #                 parent_mo.appendChild(child_mo)
    #     return parent_mo
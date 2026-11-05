import re
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_04_NRCell(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.addcell].index) == 0: return
        self.script_list = self.create_mos_msg()

    def create_mos_msg(self):
        lines = []
        for _, row in self.df_gnb_cell.loc[self.df_gnb_cell.addcell].iterrows():
            lines.append(F'####:----------------> NRSectorCarrier, CommonBeamforming, NRCellDU & NRCellCU for {row.postcell} <----------------:####')
            self.motype = 'GNBDU'
            sc_ldn = F'GNBDUFunction=1,NRSectorCarrier={row.sc}'
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('NRSectorCarrier', row.presite, row.scfdn)
            temp_dict.update({
                'nRSectorCarrierId': row.sc, 'administrativeState': '0 (LOCKED)',
                'arfcnDL': row.arfcndl, 'arfcnUL': row.arfcnul,
                'bSChannelBwDL': row.bschannelbwdl, 'bSChannelBwUL': row.bschannelbwul,
                'configuredMaxTxPower': row.confpow,
                'sectorEquipmentFunctionRef': F'NodeSupport=1,SectorEquipmentFunction={row.sef}',
            })
            if str(row.postcell)[0] == 'A': temp_dict.update({'ueAssistedPrecodingOptEnabled': 'false'})
            elif str(row.postcell)[0] == 'M': temp_dict.update({'ueAssistedPrecodingOptEnabled': 'false'})
            elif str(row.postcell)[0] == 'N': temp_dict.update({'ueAssistedPrecodingOptEnabled': 'false'})
            elif str(row.postcell)[0] == 'O': temp_dict.update({'ueAssistedPrecodingOptEnabled': 'false'})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'NRSectorCarrier', sc_ldn))
            if str(row.postcell)[0] == 'A':
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('CommonBeamforming', row.presite, F'{row.scfdn},CommonBeamforming=1')
                temp_dict.update({'commonBeamformingId': '1'})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'CommonBeamforming', F'{sc_ldn},CommonBeamforming=1'))
            # CgSwitchCfg, CgSwitch, CgSwitchUeCfg
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('CgSwitchCfg', None, None)
            temp_dict.update({'cgSwitchCfgId': row.postcell, 'dlScgLowQualThresh': '-30' if str(row.postcell)[0] == 'A' else '30'})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'CgSwitchCfg', F'GNBDUFunction=1,UeCC=1,CgSwitchCfg={row.postcell}'))
            tmp_ldn = F'GNBDUFunction=1,UeCC=1,CgSwitch={row.postcell}'
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('CgSwitch', None, None)
            temp_dict.update({'cgSwitchId': row.postcell})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'CgSwitch', tmp_ldn))
            lines.extend([
                F'ld {tmp_ldn},CgSwitchUeCfg=Base',
                F'set {tmp_ldn},CgSwitchUeCfg=Base$ cgSwitchCfgRef GNBDUFunction=1,UeCC=1,CgSwitchCfg={row.postcell}',
                F'',
            ])

            # UlCgSwitchCfg, UlCgSwitch, UlCgSwitchUeCfg
            # if self.usid.client.software.swname[:9] > 'TMO_24_Q3' and self.bbversion in 'G3G4':
            if self.bbversion in 'G3G4':
                tmp_ldn = F'GNBDUFunction=1,UeCC=1,UlCgSwitchCfg={row.postcell}'
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('UlCgSwitchCfg', None, None)
                temp_dict.update({'ulCgSwitchCfgId': row.postcell, 'ulScgLowQualHyst': '40'})
                if str(row.postcell)[0] == 'A': temp_dict.update({'ulScgLowQualThresh': '100'})
                else: temp_dict.update({'ulScgLowQualThresh': '70'})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'UlCgSwitchCfg', tmp_ldn))
                tmp_ldn = F'GNBDUFunction=1,UeCC=1,UlCgSwitch={row.postcell}'
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('UlCgSwitch', None, None)
                temp_dict.update({'ulCgSwitchId': row.postcell})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'UlCgSwitch', tmp_ldn))
                lines.extend([
                    F'ld {tmp_ldn},UlCgSwitchUeCfg=Base',
                    F'set {tmp_ldn},UlCgSwitchUeCfg=Base$ ulCgSwitchCfgRef GNBDUFunction=1,UeCC=1,UlCgSwitchCfg={row.postcell}',
                    F'',
                ])



            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('NRCellDU', None, None)
            temp_dict.update({
                'nRCellDUId': row.postcell,
                'cellLocalId': row.cellid,
                'nRPCI': row.nrpci,
                'nRSectorCarrierRef': sc_ldn,
                'nRTAC': row.nrtac,
                'rachRootSequence': row.rachrootsequence,
                'ssbSubCarrierSpacing': row.ssbsubcarrierspacing,
                'subCarrierSpacing': row.ssbsubcarrierspacing,
                'ssbFrequency': '0',
                'administrativeState': '0 (LOCKED)',
                'cellBarred': '0 (BARRED)',
                'cellReservedForOperator': '0 (RESERVED)',
                'endcCgSwitchRef': F'GNBDUFunction=1,UeCC=1,CgSwitch={row.postcell}',
                'nrdcCgSwitchRef': F'GNBDUFunction=1,UeCC=1,CgSwitch={row.postcell}'
            })
            if self.bbversion in 'G3G4':
                temp_dict.update({'endcUlCgSwitchRef': F'GNBDUFunction=1,UeCC=1,UlCgSwitch={row.postcell}',
                              'nrdcUlCgSwitchRef': F'GNBDUFunction=1,UeCC=1,UlCgSwitch={row.postcell}'})
            if row.arfcndl == row.arfcnul:
                temp_dict.update({'tddUlDlPattern': '1 (TDD_ULDL_PATTERN_01)',
                                  'tddSpecialSlotPattern': '1 (TDD_SPECIAL_SLOT_PATTERN_01)'})
            # N600
            if row.postcell[0] == 'K':
                temp_dict.update({
                    'qRxLevMin': '-116', 'pdcchSymbConfig': '4 (STATIC_3)', 'redCap1RxEnabled': 'true', 'redCap2RxEnabled': 'true',
                    'redCapUeLimit': '1 (BASIC)', 'bandListManual': ['71'],
                    'puschModeOnFddSCell': '1 (SHORT_SRS_CONSEC_SL_OVERLAP)',
                })
                if row.bschannelbwdl == '20': temp_dict.update({'pdcchSymbConfig': '3 (ADAPT_MAX_3)'})
            # N1900
            if row.postcell[0] == 'J':
                temp_dict.update({
                    'qRxLevMin': '-120', 'pdcchLaBfGainFraction': '0', 'pdcchLaSinrOffset': '-15',
                    'pdcchSymbConfig': '1 (STATIC_2)', 'redCap1RxEnabled': 'true', 'redCap2RxEnabled': 'true',
                    'redCapUeLimit': '1 (BASIC)', 'dlDmrsMuxSinrThresh': '-10',
                    'bandListManual': ['25'],
                    'puschModeOnFddSCell': '1 (SHORT_SRS_CONSEC_SL_OVERLAP)',
                })
                if row.arfcndl == '398000' and row.bschannelbwdl == '10':
                    temp_dict.update({'ulAvailableCrbs': '27'})
                elif row.arfcndl == '397500' and row.bschannelbwdl == '15':
                    temp_dict.update({'ulAvailableCrbs': '52'})
                elif row.arfcndl == '397000' and row.bschannelbwdl == '20':
                    temp_dict.update({'ulAvailableCrbs': '79'})
                elif row.arfcndl == '396500' and row.bschannelbwdl == '25':
                    temp_dict.update({'ulAvailableCrbs': '106'})
            # N2100
            if row.postcell[0] == 'I':
                temp_dict.update({
                    'qRxLevMin': '-120', 'pdcchLaSinrOffset': '-15', 'pdcchSymbConfig': '1 (STATIC_2)',
                    'bandListManual': ['66'], 'puschModeOnFddSCell': '1 (SHORT_SRS_CONSEC_SL_OVERLAP)',
                })

            # N2500
            if str(row.postcell)[0] == 'A':
                temp_dict.update({
                    'tddSpecialSlotPattern': '1 (TDD_SPECIAL_SLOT_PATTERN_01)',
                    'tddUlDlPattern': '1 (TDD_ULDL_PATTERN_01)',
                    'dlDmrsMuxSinrThresh': '-10', 'qRxLevMin': '-118', 'pZeroUePuschOffset256Qam': '0',
                    'pdcchSymbConfig': '2 (ADAPT_MAX_2)',
                    'nrLteCoexistence': 'true', 'ulCaTimeAlignmentMode': '0 (N_TA_O_STANDARD)',
                    'puschModeOnFddSCell': '0 (LONG)',
                    'subCarrierSpacing': '30', 'ssbSubCarrierSpacing': '30', 'ssbTimeShiftEnabled': 'true',
                    'csiRsConfig16P': {'csiRsControl16Ports': '0 (OFF)', 'i11Restriction': '', 'i12Restriction': ''},
                    'csiRsConfig2P': {'aRestriction': '', 'csiRsControl2Ports': '0 (OFF)'},
                    'csiRsConfig32P': {'csiRsControl32Ports': '1 (EIGHT_TWO_N1AZ)', 'i11Restriction': 'FFFFFFFF', 'i12Restriction': 'FF'},
                    'csiRsConfig4P': {'csiRsControl4Ports': '0 (OFF)', 'i11Restriction': ''},
                    'csiRsConfig8P': {'csiRsControl8Ports': '1 (FOUR_ONE_N1AZ)', 'i11Restriction': 'FFFF', 'i12Restriction': ''},
                    'csiRsShiftingPrimary': '1 (ACTIVATED_AUTOMATIC)', 'csiRsShiftingSecondary': '1 (ACTIVATED_AUTOMATIC)',
                    'bandListManual': ['41'],
                })
                if row.bschannelbwdl == '60': temp_dict.update({'ulAvailableCrbs': '135'})

                if len([_ for _ in row.frutypecix if re.match('AIR.*64.*', _)]) > 0:
                    temp_dict.update({
                        'ssbPowerBoostMMimoSleep': '3', 'advancedDlSuMimoEnabled': 'true',
                        'advDlBfWhenAllSrsPortsUsable': 'true', 'maxNoOfAdvancedDlMuMimoLayers': '16',
                        'dlMaxMuMimoLayers': '8', 'ulMaxMuMimoLayers': '4',
                        'pairwiseSrsCorrelationThresh': ['850', '990'],
                    })
            # CBAND
            if row.postcell[0] == 'Q' or row.postcell[0] == 'S':
                temp_dict.update({'bandListManual': ['77'], })
            # mmWave
            if row.postcell[0] == 'M':
                temp_dict.update({
                    'bandListManual': ['261'], 'ul256QamEnabled': 'false', 'ssbDuration': '3',
                    'rachPreambleFormat': '3 (RACH_PREAMBLE_FORMAT_03)', 'maxUeSpeed': '0 (UP_TO_10KMPH)',
                    'pdcchSymbConfig': '0 (MINIMUM)', 'fixWideBeamsForPeriodicSr': '0 (FIX_WB_FOR_PERIODIC_SR_NONE)',
                    'cellRange': '1100', 'tddUlDlPattern': '0 (TDD_ULDL_PATTERN_00)', 'secondaryCellOnly': 'true',
                })
            # mmWave
            if row.postcell[0] == 'N':
                temp_dict.update({
                    'bandListManual': ['260'], 'ul256QamEnabled': 'false', 'ssbDuration': '3',
                    'rachPreambleFormat': '3 (RACH_PREAMBLE_FORMAT_03)', 'maxUeSpeed': '0 (UP_TO_10KMPH)',
                    'pdcchSymbConfig': '0 (MINIMUM)', 'fixWideBeamsForPeriodicSr': '0 (FIX_WB_FOR_PERIODIC_SR_NONE)',
                    'cellRange': '1100', 'tddUlDlPattern': '0 (TDD_ULDL_PATTERN_00)', 'secondaryCellOnly': 'true',
                })
            # mmWave
            if row.postcell[0] == 'O':
                temp_dict.update({
                    'cellRange': '1100',
                    'bandListManual': ['258'], 'ul256QamEnabled': 'false', 'ssbDuration': '3',
                    'rachPreambleFormat': '3 (RACH_PREAMBLE_FORMAT_03)', 'maxUeSpeed': '0 (UP_TO_10KMPH)',
                    'pdcchSymbConfig': '0 (MINIMUM)', 'fixWideBeamsForPeriodicSr': '0 (FIX_WB_FOR_PERIODIC_SR_NONE)',
                    'tddSpecialSlotPattern': '6 (TDD_SPECIAL_SLOT_PATTERN_06)',
                    'tddUlDlPattern': '5 (TDD_ULDL_PATTERN_05)', 'additionalPucchForCaEnabled': 'false',
                    'caPerCcFairnessWeightUlEnabled': 'false', 'caSCellHandlingRef': '', 'dftSOfdmMsg3Enabled': 'false',
                    'dftSOfdmPuschEnabled': 'false', 'dlDmrsMuxSinrThresh': '-10', 'dlSmallDataRobustness': '0 (OFF)',
                    'imsEmSupportEnabled': 'false', 'pZeroNomPucch': '-96', 'pZeroNomPuschGrant': '-100',
                    'pZeroUePuschOffset256Qam': '0', 'pdcchLaBfGainFraction': '100', 'pdschAllowedInDmrsSym': 'false',
                    'qRxLevMin': '-116', 'rachPreambleDetThrFraction': '10', 'rachPreambleRecTargetPower': '-110',
                    'secondaryCellOnly': 'true', 'rimDetectionEnabled': 'false',
                })
            # energyOptSymAllocRef
            if self.bbversion in 'G3G4':
                if row.postcell[0] in ['A', 'Q', 'S', 'M', 'N', 'O'] or int(row.bschannelbwdl) < 10:
                    temp_dict['energyOptSymAllocRef'] = 'GNBDUFunction=1,EnergyEfficiency=1,EnergyOptSymAlloc=Default'
                elif row.postcell[0] in ['I', 'J', 'K'] or int(row.bschannelbwdl) >= 10:
                    temp_dict['energyOptSymAllocRef'] = 'GNBDUFunction=1,EnergyEfficiency=1,EnergyOptSymAlloc=EOSyA'

            lines.extend(self.create_mos_script_from_dict(temp_dict, 'NRCellDU',
                                                          F'GNBDUFunction=1,NRCellDU={row.postcell}'))

            if self.usid.client.mname not in ['Norton', 'EastProvidence', 'Bloomfield']:
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('AdditionalPLMNInfo', row.presite, row.scfdn)
                temp_dict.update({'additionalPLMNInfoId': '1', 'nRTAC': row.nrtac})
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'AdditionalPLMNInfo',
                                                              F'GNBDUFunction=1,NRCellDU={row.postcell},AdditionalPLMNInfo=1'))

            # NRCellCU
            self.motype = 'GNBCUCP'
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('IntraFreqMCCellProfile', None, None)
            temp_dict.update({'intraFreqMCCellProfileId': row.postcell})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'IntraFreqMCCellProfile',
                                                          F'GNBCUCPFunction=1,IntraFreqMC=1,IntraFreqMCCellProfile={row.postcell}'))

            # temp_dict = self.update_db_with_mo_for_siteid_and_fdn('IntraFreqMCCellProfileUeCfg', None, None)
            # temp_dict.update({'intraFreqMCCellProfileUeCfgId': 'Base'})
            # lines.extend(self.create_mos_script_from_dict(temp_dict, 'IntraFreqMCCellProfileUeCfg', F'GNBCUCPFunction=1,IntraFreqMC=1,IntraFreqMCCellProfile={row.postcell},IntraFreqMCCellProfileUeCfg=Base'))

            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('McfbCellProfile',  None, None)
            temp_dict.update({'mcfbCellProfileId': row.postcell})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'McfbCellProfile',
                                                          F'GNBCUCPFunction=1,Mcfb=1,McfbCellProfile={row.postcell}'))

            # temp_dict = self.update_db_with_mo_for_siteid_and_fdn('McfbCellProfileUeCfg', None, None)
            # temp_dict.update({'mcfbCellProfileUeCfgId': 'Base'})
            # lines.extend(self.create_mos_script_from_dict(temp_dict, 'McfbCellProfileUeCfg', F'GNBCUCPFunction=1,Mcfb=1,McfbCellProfile={row.postcell},McfbCellProfileUeCfg=Base'))
            
            lines += [
                F'ld GNBCUCPFunction=1,Mcfb=1,McfbCellProfile={row.postcell},McfbCellProfileUeCfg=Base',
                F'set GNBCUCPFunction=1,Mcfb=1,McfbCellProfile={row.postcell},McfbCellProfileUeCfg=Base$ epsFallbackOperation 2',
                F'set GNBCUCPFunction=1,Mcfb=1,McfbCellProfile={row.postcell},McfbCellProfileUeCfg=Base$ epsFallbackOperationEm 1',
                F'',
            ]
            
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('McpcPCellProfile',  None, None)
            temp_dict.update({'mcpcPCellProfileId': row.postcell})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'McpcPCellProfile', F'GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile={row.postcell}'))
            if row.postcell[0] == 'A' and row.postcell[-1] == '1':
                lines.extend([F"""
ld GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile={row.postcell},McpcPCellProfileUeCfg=Base
set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile={row.postcell},McpcPCellProfileUeCfg=Base rsrpCriticalPcOffset powerClass=PC_1_5,thresholdOffset=-3
set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile={row.postcell},McpcPCellProfileUeCfg=Base rsrpSearchZonePcOffset powerClass=PC_1_5,thresholdOffset=-3
set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile={row.postcell},McpcPCellProfileUeCfg=Base rsrpCandidateA5PcOffset powerClass=PC_1_5,threshold1Offset=-3,threshold2Offset=-3
set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile={row.postcell},McpcPCellProfileUeCfg=Base rsrpCandidateB2PcOffset powerClass=PC_1_5,threshold1Offset=-3
set GNBCUCPFunction=1,TrafficSteering=1,TrStSaCellProfile=Default,TrStSaCellProfileUeCfg=Base rsrpPCellCandidatePcOffset powerClass=PC_1_5,threshold2Offset=-3
                """])
            temp_dict = self.get_mo_attributes(moc='McpcPCellProfileUeCfg', moid='CU,VoNR')
            temp_dict.update({'mcpcPCellProfileUeCfgId': 'VoNR'})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'McpcPCellProfileUeCfg',
                                                          F'GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile={row.postcell},McpcPCellProfileUeCfg=VoNR'))

            # temp_dict = self.update_db_with_mo_for_siteid_and_fdn('McpcPCellProfileUeCfg', None, None)
            # temp_dict.update({'mcpcPCellProfileUeCfgId': 'Base'})
            # lines.extend(self.create_mos_script_from_dict(temp_dict, 'McpcPCellProfileUeCfg', F'GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile={row.postcell},McpcPCellProfileUeCfg=Base'))

            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('McpcPSCellProfile',  None, None)
            temp_dict.update({'mcpcPSCellProfileId': row.postcell})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'McpcPSCellProfile', F'GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile={row.postcell}'))

            # temp_dict = self.update_db_with_mo_for_siteid_and_fdn('McpcPSCellProfileUeCfg', None, None)
            # temp_dict.update({'mcpcPSCellProfileUeCfgId': 'Base'})
            # lines.extend(self.create_mos_script_from_dict(temp_dict, 'McpcPSCellProfileUeCfg', F'GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile={row.postcell},McpcPSCellProfileUeCfg=Base'))

            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('UeMCCellProfile',  None, None)
            temp_dict.update({'ueMCCellProfileId': row.postcell})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'UeMCCellProfile', F'GNBCUCPFunction=1,UeMC=1,UeMCCellProfile={row.postcell}'))

            ca_ldn = F'GNBCUCPFunction=1,CarrierAggregation=1,CaCellMeasProfile={row.postcell}'
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('CaCellMeasProfile', None, None)
            temp_dict.update({'caCellMeasProfileId': row.postcell})
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'CaCellMeasProfile', ca_ldn))

            lines += [
                F'ld {ca_ldn},CaCellMeasProfileUeCfg=Base',
                F'set {ca_ldn},CaCellMeasProfileUeCfg=Base$ rsrpBetterSCell hysteresis=150,offset=150,timeToTrigger=5120',
                F'set {ca_ldn},CaCellMeasProfileUeCfg=Base$ rsrpSCellCoverage hysteresis=10,threshold=-122,timeToTrigger=640,timeToTriggerA1=-1',
                F'set {ca_ldn},CaCellMeasProfileUeCfg=Base$ rsrqSCellCoverage hysteresis=10,threshold=-430,timeToTrigger=640,timeToTriggerA1=-1',
                F'',
            ]

            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('NRCellCU', None, None)
            temp_dict.update({
                'nRCellCUId': row.postcell, 'cellLocalId': row.cellid,
                'transmitSib2': 'false', 'transmitSib4': 'false', 'transmitSib5': 'false',
                'intraFreqMCCellProfileRef': F'GNBCUCPFunction=1,IntraFreqMC=1,IntraFreqMCCellProfile={row.postcell}',
                'mcfbCellProfileRef': F'GNBCUCPFunction=1,Mcfb=1,McfbCellProfile={row.postcell}',
                'mcpcPCellProfileRef': F'GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile={row.postcell}',
                'mcpcPSCellProfileRef': F'GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile={row.postcell}',
                'ueMCCellProfileRef': F'GNBCUCPFunction=1,UeMC=1,UeMCCellProfile={row.postcell}',
                'caCellMeasProfileRef': ca_ldn,
                'nRFrequencyRef': '',
            })
            # mmWave
            if row.postcell[0] == 'O':
                temp_dict.update({
                    'hiPrioDetEnabled': 'false', 'interfaceSupervision': '3 (X2_ONLY)', 'sNonIntraSearchP': '0',
                })
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'NRCellCU',
                                                          F'GNBCUCPFunction=1,NRCellCU={row.postcell}'))

        # Parameter Setting and Post Values
        lines += [
            """
ld ,McpcPCellProfileUeCfg=
lset McpcPCellProfileUeCfg= lowHighFreqPrioClassification 5
lset McpcPCellProfileUeCfg= mcpcQuantityList 0
lset McpcPCellProfileUeCfg= rsrpCriticalEnabled true
lset McpcPCellProfileUeCfg= rsrpSearchTimeRestriction -1
lset McpcPCellProfileUeCfg= rsrpSearchZone hysteresis=20,threshold=-50,timeToTrigger=320,timeToTriggerA1=320

####:----------------> Post Check <----------------:####
lt all
hget ^SectorCarrier|NRSectorCarrier= configuredMaxTxPower|noOf.xAntennas|sectorFunctionRef|reservedBy|arfcn|bSChannelBw
st sec
hget ^EUtranCell.DD|^NbIotCell|^NRCellDU [el]State|primaryPlmnReserved|cellBarred|sectorCarrierRef|^cellReservedForOperator$|^cellid$|^cellLocalId$|^physicalLayerCellId$|^earfcndl$|^channelBandwidth$|^dlchannelBandwidth$|^earfcn$|sectorCarrierRef|^cellReservedForOperator$
hget ^NRCellCU=.* ^cellLocalId$|^transmitSib|CellProfileRef
get McpcPCellProfileUeCfg=Base rsrpCriticalPcOffset|rsrpSearchZonePcOffset|rsrpCandidateA5PcOffset|rsrpCandidateB2PcOffset
get TrStSaCellProfileUeCfg=Base rsrpPCellCandidatePcOffset
"""
        ]

        return lines + ['', '']

from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_13_NRRel_EAST_para(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if self.usid.client.mname not in ['Bloomfield', 'Norfolk', 'Philadelphia', 'Salina']: return

        self.relative_path.insert(-2, 'NR_NR_Relations')
        if len(self.usid.df_gnb_cell.postsite.unique()) > 1:
            self.script_list += self.pre_post_check('Pre') + self.east_market_settings() + self.pre_post_check('Post')


    def east_market_settings(self):
        lines = [
            F'pr GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=3.*,McpcPCellNrFreqRelProfileUeCfg=Base',
            F'if $nr_of_mos > 0',
            F'	set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=3.*,McpcPCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate false',
            F'fi',
            F'',
            F'pr GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=3.*,UeMCNrFreqRelProfileUeCfg=Base',
            F'if $nr_of_mos > 0',
            F'	set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=3.*,UeMCNrFreqRelProfileUeCfg=Base connModeAllowedPCell true',
            F'	set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=3.*,UeMCNrFreqRelProfileUeCfg=Base connModeAllowedPSCell false',
            F'fi',
            F'',
            F'pr GNBCUCPFunction=1,Mcpc=1,McpcPSCellNrFreqRelProfile=3.*,McpcPSCellNrFreqRelProfileUeCfg=Base',
            F'if $nr_of_mos > 0',
            F'  set GNBCUCPFunction=1,Mcpc=1,McpcPSCellNrFreqRelProfile=3.*,McpcPSCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate true',
            F'fi',
            F'',

            F'',
        ]
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.postcell.str.startswith('J', na=False)].index) > 0:
            lines += [
                F'pr GNBDUFunction=1,NRCellDU=J.*',
                F'if $nr_of_mos > 0',
                F'  set GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=J.*,McfbCellProfileUeCfg=Base epsFallbackOperation 2',
                F'  set GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=J.*,McfbCellProfileUeCfg=Base epsFbAtSessionSetup 1',
                F'  set GNBCUCPFunction=1,NRCellCU=J.* transmitSib2 true',
                F'  set GNBCUCPFunction=1,NRCellCU=J.* transmitSib4 true',
                F'  set GNBCUCPFunction=1,NRCellCU=J.* transmitSib5 true',
                F'fi',
                F'',
                F'pr GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=12.*,UeMCNrFreqRelProfileUeCfg=Base',
                F'if $nr_of_mos > 0',
                F'  set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=12.*,UeMCNrFreqRelProfileUeCfg=Base connModePrioPCell 3',
                F'fi',
                F'',
                F'pr GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=5.*,UeMCNrFreqRelProfileUeCfg=Base',
                F'if $nr_of_mos > 0',
                F'  set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=5.*,UeMCNrFreqRelProfileUeCfg=Base connModePrioPCell 7',
                F'fi',
                F'',

            ]
        return lines

    def pre_post_check(self, activity):
        return [
            F'#################################################################################################',
            F'####:----------------> {activity} Check <----------------:####',
            F'hget ^NRCellDU=.* ^ssb(FrequencyAutoSelected|Frequency|SubCarrierSpacing|Periodicity|Offset|Duration)$',
            F'hget ^NRCellCU=.* ^smtc(Periodicity|Offset|Duration)$|transmitSib(2|4|5)$',
            F'hget ^NRFrequency=.* arfcnValueNRDl|^band(List|ListManual)|gscn$|^smtc(Duration|Offset|Periodicity|Scs)$',
            F'hget ^NRFreqRelation=.* cellReselectionPriority|nRFrequencyRef|qRxLevMin|^tReselectionNR$|threshXHighP|threshXLowP',
            F'hget UeMCNrFreqRelProfileUeCfg= connModeAllowedPCell|connModeAllowedPSCell',
            F'hget McpcPSCellNrFreqRelProfileUeCfg= inhibitMeasForCellCandidate',
            F'#################################################################################################',
            F'',
            ]
    
    def cr_file_path(self):
        if len(self.script_list) == 0: return
        import os
        self.script_file = os.path.join(self.usid.base_dir, *self.relative_path)
        out_dir = os.path.dirname(self.script_file)
        if not os.path.exists(out_dir): os.makedirs(out_dir)

from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_10_Intra_CellRelation(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.addcell].index) == 0: return

        self.relative_path.insert(-2, 'NR_NR_Relations')
        self.nrnwmo = F'GNBCUCPFunction=1,NRNetwork={self.gnbdata.get("NRNetwork")}'
        self.script_list += self.activity_check('Pre') + self.nr_freqrel_intera_site_relation() + self.activity_check('Post')

    def nr_freqrel_intera_site_relation(self):
        lines = []
        nr_freq_id = '$arfcnval-$smtcscs'
        lines.extend(self.get_nr_freq_rel_cellrel_functions())
        lines.extend([
            F'####:----------------> NRFrequency, NRFreqRelation & NRCellRelation <----------------:####',
            F'func val_cr_nrfreq_rel_cellrel',
            F'    for $cu_cell in cucells',
            F'        get $cu_cell ^nRCellCUId$ > $scellcuid',
            F'        $nrcellldn = ldn($cu_cell)',
            F'        $nrfreqrelldn = $nrcellldn,NRFreqRelation=$arfcnval',
            F'        $nrcellrelldn = $nrcellldn,NRCellRelation=$ducelllid',
            F'        createnrfreqrelation',
            F'        if $scellcuid != $ducelllid',
            F'            createnrcellrelation',
            F'        fi',
            F'    done',
            F'endfunc',
            F'',
            
            F'',
            F'mr ducells',
            F'mr cucells',
            F'ma ducells GNBDUFunction=1,NRCellDU=',
            F'ma cucells GNBCUCPFunction=1,NRCellCU=',
            F'for $mo in ducells',
            F'    $ducellldn = ldn($MO)',
            F'    get $mo ^ssbPeriodicity$ > $smtcperiodicity',
            F'    get $mo ^ssbSubCarrierSpacing$ > $smtcscs',
            F'    get $mo ^ssbOffset$ > $smtcoffset',
            F'    if $smtcoffset = ',
            F'        get $mo ^ssbOffsetAutoSelected$ > $smtcoffset',
            F'    fi',
            F'    get $mo ^ssbDuration$ > $smtcduration',
            F'    if $smtcduration = ',
            F'        get $mo ^ssbDurationAutoSelected$ > $smtcduration',
            F'    fi',
            F'    get $mo ^ssbFrequency$ > $arfcnval',
            F'    if $arfcnval = 0 || $arfcnval = ',
            F'        get $mo ^ssbFrequencyAutoSelected$ > $arfcnval',
            F'    fi',
            F'    get $mo ^nRCellDUId$ > $ducelllid',
            F'    $targetcucell = GNBCUCPFunction=1,NRCellCU=$ducelllid',
            F'    pr GNBCUCPFunction=1,NRCellCU=$ducelllid$',
            F'    if $nr_of_mos > 0 && $arfcnval !=',
            F'        $frqldn = GNBCUCPFunction=1,NRNetwork=1,NRFrequency={nr_freq_id}',
            F'        $targetcucell = GNBCUCPFunction=1,NRCellCU=$ducelllid',
            F'        createnrfrequency',
            F'        createnrfreqprofile',
            F'        val_cr_nrfreq_rel_cellrel',
            F'    else',
            F'        print ERROR: !!! ssbFrequencyAutoSelected for NRCellDU ---> $ducelllid <--- is empty, Please Validate !!!',
            F'    fi',
            F'done',
            F'mr ducells',
            F'mr cucells',
            F'',
        ])
        ll = []
        for _, s_row in self.df_gnb_cell.iterrows():
            for _, t_row in self.usid.df_gnb_cell.iterrows():
                if s_row.postcell[0] == t_row.postcell[0] == 'A' and s_row.postcell[-1] == '1' and t_row.postcell[-1] == '2' and \
                        s_row.postcell[-2] == t_row.postcell[-2]:
                    t_nci = int(self.usid.gnodeb.get(t_row.postsite).get("nodeid")) * \
                            (2 ** (36 - int(self.usid.gnodeb.get(t_row.postsite).get("gNBIdLength")))) + int(t_row.cellid)
                    ll.extend([
                        F'####:----------------> NR CA Enablement for N41 {s_row.postcell} to {t_row.postcell} <----------------:####',
                        F'pr GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation={t_row.postcell}$',
                        F'if $nr_of_mos > 0',
                        F'    set GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation={t_row.postcell}$ coverageIndicator 2',
                        F'    set GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation={t_row.postcell}$ isHoAllowed true',
                        F'    set GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation={t_row.postcell}$ isRemoveAllowed false',
                        F'    set GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation={t_row.postcell}$ sCellCandidate 1',
                        F'fi',
                        F'pr GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation=auto{t_nci}$',
                        F'if $nr_of_mos > 0',
                        F'    set GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation=auto{t_nci}$ coverageIndicator 2',
                        F'    set GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation=auto{t_nci}$ isHoAllowed true',
                        F'    set GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation=auto{t_nci}$ isRemoveAllowed false',
                        F'    set GNBCUCPFunction=1,NRCellCU={s_row.postcell},NRCellRelation=auto{t_nci}$ sCellCandidate 1',
                        F'fi',
                        F'',
                    ])
        if len(ll) > 0: ll = ['####:----------------> NR CA Enablement for N41 1st Carrier and N41 2nd Carrier <----------------:####'] + ll
        lines = lines + ll
        lines.extend([
            F'####:----------------> Parameter Setting <----------------:####',
            F'pr GNBCUCPFunction=1,NRCellCU=',
            F'set GNBCUCPFunction=1,NRCellCU= transmitSib2 true',
            F'set GNBCUCPFunction=1,NRCellCU= transmitSib5 true',
            F'set GNBCUCPFunction=1,NRCellCU= mcpcPCellEnabled true',
            F'',
        ])
        return lines
    
    def nr_ca_b41_1c_2c(self):
        lines = []
        if self.df_gnb_cell.loc[self.df_gnb_cell.addcell].shape[0] > 0:
            aa = 1
        return lines
    
    @staticmethod
    def activity_check(activity):
        return [
            F'####:----------------> {activity} Check <----------------:####',
            F'hget GNBDUFunction=1,RadioBearerTable=1,DataRadioBearer=1$ dlMaxRetxThreshold',
            F'hget ^NRCellDU=.* ^ssb(FrequencyAutoSelected|Frequency|SubCarrierSpacing|Periodicity|Offset|Duration)$',
            F'hget ^NRCellCU=.* ^smtc(Periodicity|Offset|Duration)$|transmitSib(2|4|5)$',
            F'hget ^NRFrequency=.* arfcnValueNRDl|^band(List|ListManual)|gscn$|^smtc(Duration|Offset|Periodicity|Scs)$',
            F'hget ^NRFreqRelation=.* cellReselectionPriority|nRFrequencyRef|qRxLevMin|^tReselectionNR$|threshXHighP|threshXLowP',
        ]
    
    def cr_file_path(self):
        if len(self.script_list) == 0: return
        import os
        self.script_file = os.path.join(self.usid.base_dir, *self.relative_path)
        out_dir = os.path.dirname(self.script_file)
        if not os.path.exists(out_dir): os.makedirs(out_dir)

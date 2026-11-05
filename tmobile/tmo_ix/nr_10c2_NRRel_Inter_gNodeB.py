from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_10c2_NRRel_Inter_gNodeB(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.usid.df_gnb_cell.postsite.unique()) <= 1: return

        self.relative_path.insert(-2, 'NR_NR_Relations')
        self.nrnwmo = F'GNBCUCPFunction=1,NRNetwork={self.gnbdata.get("NRNetwork")}'
        self.script_list += self.pre_post_check('Pre') + self.nr_relation_creation() + self.pre_post_check('Post')

    def nr_relation_creation(self):
        lines = []
        lines.extend(self.get_nr_freq_rel_cellrel_functions())
        gnodebids = [str(self.usid.gnodeb[_]["nodeid"]) for _ in self.usid.gnodeb.keys() if _ != self.node] + \
                    [str(_) for _ in self.usid.gnodeb.keys() if _ != self.node]
        lines.extend([
            F'####:----------------> NRFreqRelation & NRCellRelation for ExternalNRCellCU with gNBId --- {gnodebids} <----------------:####',
            F'func get_nrfreq',
            F'    mr nrfreqrels',
            F'    ma nrfreqrels $nrcellldn,NRFreqRelation= ^nRFrequencyRef$ $frqldn',
            F'    for $nrfreqrel in nrfreqrels',
            F'        $nrfreqrelldn = ldn($nrfreqrel)',
            F'    done',
            F'    mr $nrfreqrel',
            F'    mr nrfrerels',
            F'endfunc',
            F'',
            F'func val_cr_nrfreq_rel_cellrel',
            F'  for $cu_cell in cucells',
            F'      get $cu_cell ^nRCellCUId$ > $scellcuid',
            F'      $nrcellldn = ldn($cu_cell)',
            F'      $nrfreqrelldn = $nrcellldn,NRFreqRelation=$arfcnval',
            F'      $nrcellrelldn = $nrcellldn,NRCellRelation=$ducelllid',
            F'      get $nrcellldn,NRFreqRelation= ^nRFrequencyRef$ $frqldn',
            F'      if $nr_of_mos > 0',
            F'          get_nrfreq',
            F'      else',
            F'          createnrfreqrelation',
            F'      fi',
            F'      if $scellcuid != $ducelllid',
            F'          createnrcellrelation',
            F'      fi',
            F'  done',
            F'endfunc',
            F'',
    
            F'lt all',
            F'mr cucells',
            F'mr extgnbs',
            F'mr extcucells',
            F'ma cucells GNBCUCPFunction=1,NRCellCU=',
            F'ma extgnbs ^ExternalGNBCUCPFunction=.*({"|".join(gnodebids)})',
            F'for $extgnb in extgnbs',
            F'    $extgnb = ldn($extgnb)',
            F'    ma extcucells $extgnb,ExternalNRCellCU=',
            F'done',
            F'pr extcucells',
            F'for $extcell in extcucells',
            F'  get $extcell ^externalNRCellCUId$ > $ducelllid',
            F'  get $extcell ^nRFrequencyRef$ > $frqldn',
            F'  get $frqldn ^arfcnValueNRDl$ > $arfcnval',
            F'  $targetcucell = ldn($extcell)',
            F'  createnrfreqprofile',
            F'  val_cr_nrfreq_rel_cellrel',
            F'done',
            F'mr cucells',
            F'mr extnrcells',
            F'',
            F'',
        ])

        lines.extend([
            F'####:----------------> Parameter Setting <----------------:####',
            F'set GNBCUCPFunction=1,NRCellDU= administrativeState 0',
            F'wait 30',
            F'set GNBCUCPFunction=1,NRCellCU= transmitSib2 true',
            F'set GNBCUCPFunction=1,NRCellCU= transmitSib4 true',
            F'set GNBCUCPFunction=1,NRCellCU= transmitSib5 true',
            F'set GNBCUCPFunction=1,NRCellCU= mcpcPCellEnabled true',
            F'',
        ])
        
        return lines
    
    def pre_post_check(self, activity):
        return [
            F'#################################################################################################',
            F'##############################################################',
            F'####:----------------> {activity} Check <----------------:####',
            F'hget ^NRCellDU=.* ^ssb(FrequencyAutoSelected|Frequency|SubCarrierSpacing|Periodicity|Offset|Duration)$',
            F'hget ^NRCellCU=.* ^smtc(Periodicity|Offset|Duration)$|transmitSib(2|4|5)$',
            F'hget ^NRFrequency=.* arfcnValueNRDl|^band(List|ListManual)|gscn$|^smtc(Duration|Offset|Periodicity|Scs)$',
            F'hget ^NRFreqRelation=.* cellReselectionPriority|nRFrequencyRef|qRxLevMin|^tReselectionNR$|threshXHighP|threshXLowP',
            F'#################################################################################################',
            F'',
            F'',
            ]
    
    def cr_file_path(self):
        if len(self.script_list) == 0: return
        import os
        self.script_file = os.path.join(self.usid.base_dir, *self.relative_path)
        out_dir = os.path.dirname(self.script_file)
        if not os.path.exists(out_dir): os.makedirs(out_dir)

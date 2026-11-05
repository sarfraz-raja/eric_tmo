from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class lte_12_GUtraRelation(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0: return
        if (len(self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD', 'TDD'])].index) == 0 or
                len(self.usid.gnodeb) == 0):
            return
        self.motype = 'Lrat'
        self.relative_path[-2] = 'LTE_NR_Relations'
        self.gutranmo = F'ENodeBFunction=1,GUtraNetwork={self.enbdata.get("GUtraNetwork")}'
        self.df_cell = self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD', 'TDD'])]
        self.script_list.extend(self.pre_post_check('Pre'))
        self.script_list.extend(self.externalgnb_mos_create())
        self.script_list.extend(self.gutranfreq_rel_cell_rel_creation_update())
        self.script_list.extend(self.enb_endc_creation_parameter_update())
        self.script_list.extend(self.east_parameter_for_n19())
        self.script_list.extend(self.pre_post_check('Post'))

    def cr_file_path(self):
        if len(self.script_list) == 0: return
        import os
        self.script_file = os.path.join(self.usid.base_dir, *self.relative_path)
        out_dir = os.path.dirname(self.script_file)
        if not os.path.exists(out_dir): os.makedirs(out_dir)

    def externalgnb_mos_create(self):
        lines = [F"""
####:----------------> GUtraNetwork & ExternalGNodeBFunction <----------------:####
pr {self.gutranmo}$
if $nr_of_mos = 0
    crn {self.gutranmo}
    end
fi
        """]

        lines1 = []
        lines2 = []
        lines3 = ["""
        """
            
            F'wait 60', F'lt all', F'']
        for gnb in self.usid.gnodeb.keys():
            extenbmo = F'{self.gutranmo},ExternalGNodeBFunction={self.usid.gnodeb[gnb]["nodeid"]}'
            lines1.extend([F"""
func ExternalGNBFor{gnb}
    get {self.gutranmo},ExternalGNodeBFunction=.* gNodeBId {self.usid.gnodeb[gnb]["nodeid"]}
    if $nr_of_mos = 0
        crn {extenbmo}
        gNodeBPlmnId {','.join([F'{_}={self.usid.gnodeb[gnb]["plmnlist"][_]}' for _ in self.usid.gnodeb[gnb]['plmnlist']])}
        gNodeBId {self.usid.gnodeb[gnb]["nodeid"]}
        gNodeBIdLength {self.usid.gnodeb[gnb]["gNBIdLength"]}
        end
    fi
    pr {extenbmo},TermPointToGNB=1
    if $nr_of_mos = 0
        crn {extenbmo},TermPointToGNB=1
        administrativeState 1
        ipAddress {self.usid.gnodeb[gnb]["lte_ip"]}
        ipv6Address ::
        end
    fi
endfunc            
            """])

            lines2.extend([F"""
####:----------------> ExternalGNodeBFunction & TermPointToGNB for {gnb} <----------------:####
$extinput = readinput(\\n Is Cells on gNodeB {gnb} is Enable [ yes , no ]?: )
$extinput = $extinput -s \\x020 -g
if $extinput != no && $extinput != yes
    print !!!Input Not provided!!!
    l-
    return
else if $extinput = yes
    ExternalGNBFor{gnb}
fi            
            """])

            lines3.extend([F"""
get {extenbmo},TermPointToGNB=1$ operationalState 1
if $nr_of_mos = 0
    bl {extenbmo},TermPointToGNB=1$
    wait 5
    st {extenbmo},TermPointToGNB=1$
    deb {extenbmo},TermPointToGNB=1$
    wait 30
fi
lt all
lst {extenbmo}
lpr {extenbmo}
print ALART: Check if ExternalGUtranCell are auto created for the NR Node {gnb}
wait 10            
            """])
        lines += lines1 + lines2 + lines3 + ['']
        return lines

    def gutranfreq_rel_cell_rel_creation_update(self):
        gnodebids = [str(self.usid.gnodeb[_]["nodeid"]) for _ in self.usid.gnodeb.keys()] + [str(_) for _ in self.usid.gnodeb.keys()]
        lines = []
        for k in self.market_dict.keys():
            lines.extend([F"{'if ' if len(lines) == 0 else 'else if '}{' || '.join(['$mibprefix ~ ' + _ for _ in self.market_dict.get(k)])}",
                          F"   ${k} = 1"])
        lines = ['$tri_la = 0'] + lines
        lines = ["""
####:----------------> EUtranCellFDD / EUtranCellTDD ---> GUtranFreqRelation, GUtranCellRelation <----------------:####
## No GUtranFreqRelation is Created for L2500(L41)
$tri_la = 0
pv $mibprefix
        """]
        for i, k in enumerate(self.market_dict.keys()):
            lines.extend([F"{'if ' if i == 0 else 'else if '}{' || '.join(['$mibprefix ~ ' + _ for _ in self.market_dict.get(k)])}",
                          F"   ${k} = 1"])
        lines += ['fi', '']

        lines.extend([F"""
## GUtranCellRelation for Tri_LA and NCAL Market is set to true
$isremovevalue = false
## if $tri_la = 1 || $ncal = 1
##     $isremovevalue = true
## fi

## GUtranFreqRelation ---> cellReselectionPriority is N71=4, N25=7, N41=7 & mmWave=7
## GUtranFreqRelation ---> endcB1MeasPriority is  N71=3 N25=5, N41=5 & mmWave=7
func para_freqrel
    if $band ~ ^71.*
        $creselpro = 4
        $endcb1 = 4
    else if $arfcn >= 123400 && $arfcn <= 130400
        $creselpro = 4
        $endcb1 = 4
    else if $band ~ ^25.* 
        $creselpro = 7
        $endcb1 = 5
    else if $arfcn >= 386000 && $arfcn <= 398000
        $creselpro = 7
        $endcb1 = 5
    else if $band ~ ^41.*
        $creselpro = 7
        $endcb1 = 5
    else if $arfcn >= 499200 && $arfcn <= 537999
        $creselpro = 7
        $endcb1 = 5
    else if $band ~ ^257.* || $band ~ ^260.* || $band ~ ^261.*
        $creselpro = 7
        $endcb1 = 7
    else if $arfcn >= 2054166 && $arfcn <= 2084999
        $creselpro = 7
        $endcb1 = 7
    else
        $creselpro = 7
        $endcb1 = 5
    fi
endfunc                    

func cr_freq_rel
    pr $freqrelldn$
    if $nr_of_mos = 0
        para_freqrel
        crn $freqrelldn
        cellReselectionPriority -1
        connectedModeMobilityPrio -1
        endcB1MeasPriority $endcb1
        gUtranSyncSignalFrequencyRef $freq
        allowedPlmnList mcc=310,mnc=260,mncLength=3
        anrMeasOn true
        deriveSsbIndexFromCell false
        b1ThrRsrpFreqOffset 0
        b1ThrRsrqFreqOffset 0
        pMaxNR 33
        qOffsetFreq 0
        qQualMin 0
        qRxLevMin -124
        threshXHigh 4
        threshXHighQ 0
        threshXLow 0
        threshXLowQ 0
        end
        set $freqrelldn$ cellReselectionPriority $creselpro
        set $freqrelldn$ endcB1MeasPriority $endcb1
    fi
endfunc

func cr_cellrel
    pr $cellrelldn$
    if $nr_of_mos = 0
        crn $cellrelldn
        neighborCellRef $extcell
        isRemoveAllowed $isremovevalue
        end
    fi
endfunc

func val_d_e_cells
    if $arfcn >= 499200 && $arfcn <= 537999 && $tri_la = 1
        $rel_flag = 0
        $cell_rel_flag = 0
    fi
endfunc

func val_cr_gutran_freqrel_cellrel
    for $cell in ecells
        $rel_flag = 1
        $cell_rel_flag = 1
        get $cell ^EUtranCell.DDId$ > $cellid
        $cellldn = ldn($cell)
        if $arfcn = 516270 && $philadelphia = 1
            $rel_flag = 0
            $cell_rel_flag = 0
        else if $cellid ~ ^D.* || $cellid ~ ^E.*
            val_d_e_cells
        fi
        if $rel_flag = 1
            $freqrelldn = $cellldn,GUtranFreqRelation=$arfcn
            cr_freq_rel
        fi
        if $cell_rel_flag = 1
            $cellrelldn = $cellldn,GUtranFreqRelation=$arfcn,GUtranCellRelation=$cellrelid
            cr_cellrel
        fi
    done
endfunc

lt all
mr ecells
ma ecells ENodeBFunction=1,EUtranCell[FT]DD=
mr extgutrancells
ma extgutrancells ExternalGUtranCell=.*({"|".join(gnodebids)})
for $mo in extgutrancells
    get $mo ^gUtranSyncSignalFrequencyRef$ > $freq
    get $freq ^arfcn$ > $arfcn
    get $freq ^band$ > $band
    get $mo ^externalGUtranCellId$ > $cellrelid
    $extcell = ldn($mo)
    val_cr_gutran_freqrel_cellrel
done
mr extgutrancells
mr ecells

### turn off ANR initiated Measurements towards N19 to avoid alarms since no ENDC towards this band
lset EUtranCell.DD=[L|B|F|T].*,GUtranFreqRelation=3.* anrMeasOn false
        """])
        return lines

    def enb_endc_creation_parameter_update(self):
        lines = []
        if self.df_cell.loc[self.df_cell.postcell.str.contains('^T')].shape[0] > 0 and \
                (self.df_cell.loc[self.df_cell.postcell.str.contains('^T')].shape[0] == self.df_cell.shape[0]):
            return lines
        elif self.df_cell.loc[self.df_cell.postcell.str.startswith(('L', 'B', 'F'), na=False)].shape[0] == 0: return lines
        else:
            lines.extend(["""
####:----------------> Feature <----------------:####
## Basic Intelligent Connectivity
set SystemFunctions=1,Lm=1,FeatureState=CXC4012218$ featureState 1

####:----------------> PmFlexCounterFilter & EndcProfile <----------------:####
cr ENodeBFunction=1,PmFlexCounterFilter=endcFilter0
cr ENodeBFunction=1,PmFlexCounterFilter=endcFilter1
cr ENodeBFunction=1,PmFlexCounterFilter=endcFilter2
set ENodeBFunction=1,PmFlexCounterFilter=endcFilter0$ endcFilterMin 0
set ENodeBFunction=1,PmFlexCounterFilter=endcFilter0$ endcFilterEnabled true
set ENodeBFunction=1,PmFlexCounterFilter=endcFilter1$ endcFilterMin 1
set ENodeBFunction=1,PmFlexCounterFilter=endcFilter1$ endcFilterEnabled true
set ENodeBFunction=1,PmFlexCounterFilter=endcFilter2$ endcFilterMin 2
set ENodeBFunction=1,PmFlexCounterFilter=endcFilter2$ endcFilterEnabled true

cr ENodeBFunction=1,EndcProfile=1
cr ENodeBFunction=1,EndcProfile=2
cr ENodeBFunction=1,EndcProfile=3
set ENodeBFunction=1,EndcProfile=1$ meNbS1TermReqArpLev 0
set ENodeBFunction=1,EndcProfile=2$ splitNotAllowedUeArpLev 15
set ENodeBFunction=1,EndcProfile=[13]$ splitNotAllowedUeArpLev 0
set ENodeBFunction=1,EndcProfile=[23]$ meNbS1TermReqArpLev 15
set ENodeBFunction=1,QciTable=default,QciProfilePredefined=qci[6789]$ endcProfileRef ENodeBFunction=1,EndcProfile=1
set ENodeBFunction=1,QciTable=default,QciProfilePredefined=qci[1234]$ endcProfileRef ENodeBFunction=1,EndcProfile=2
set ENodeBFunction=1,QciTable=default,QciProfilePredefined=qci5$ endcProfileRef ENodeBFunction=1,EndcProfile=3

####:----------------> ENodeBFunction, LoadBalancingFunction <----------------:####
####:----------------> EUtranCellFDD Parameter Setting for L2100, L1900 & AWS3 <----------------:####
set ENodeBFunction=1$ endcSplitAllowedNonDynPwrShUe true
set ENodeBFunction=1,LoadBalancingFunction=1$ lbAllowedForEndcUe false

mr efddcells
ma efddcells ^EUtranCellFDD=[LBF].*
for $mo in efddcells
  get $mo ^eUtranCellFDDId > $ecellid
  get $mo ^dlChannelBandwidth$ > $dlchabw
  if $dlchabw > 5000
      set $mo extGUtranCellRef
      set $mo primaryUpperLayerInd 1
      set $mo endcAllowedPlmnList mcc=310,mnc=260,mncLength=3
      set ENodeBFunction=1,EUtranCellFDD=$ecellid,UeMeasControl=1$ endcMeasTime 2000
      set ENodeBFunction=1,EUtranCellFDD=$ecellid,UeMeasControl=1,ReportConfigB1GUtra=1$ hysteresisB1 1
      set ENodeBFunction=1,EUtranCellFDD=$ecellid,UeMeasControl=1,ReportConfigB1GUtra=1$ timeToTriggerB1 80
  fi
  if $tri_la = 1 && $dlchabw > 5000
      set $mo zzzTemporary59 0
      set ENodeBFunction=1,EUtranCellFDD=$ecellid,UeMeasControl=1,ReportConfigB1GUtra=1$ b1Thresholdrsrp -113
  else if $dlchabw > 5000
      set ENodeBFunction=1,EUtranCellFDD=$ecellid,UeMeasControl=1,ReportConfigB1GUtra=1$ b1Thresholdrsrp -116
  fi
done
mr efddcells
unset $mo
unset $ecellid
unset $dlchabw
pr EUtranCellFDD=[ED].*,GUtranFreqRelation=
if $nr_of_mos > 0
  set EUtranCellFDD=[ED].*,GUtranFreqRelation= allowedPlmnList mcc=310,mnc=260,mncLength=3
fi
            """])
        return lines
    
    def east_parameter_for_n19(self):
        lines = []
        if self.usid.client.mname not in ['Bloomfield', 'Norfolk', 'Philadelphia', 'Salina']: return lines
        if len(self.usid.df_gnb_cell.loc[self.usid.df_gnb_cell.postcell.str.startswith('J', na=False)].index) == 0: return lines
        if len(self.df_enb_cell.loc[self.df_enb_cell.postcell.str.startswith(('L', 'B', 'F'), na=False)].index) == 0: return lines
        lines.extend(["""
####:----------------> EAST Market Parameter Settings for N1900 <----------------:####
pr ENodeBFunction=1,EUtranCellFDD=[LBF].*
if $nr_of_mos > 0
    set ENodeBFunction=1,EUtranCellFDD=[LBF].* mappingInfo mappingInfoSIB24=8
    set ENodeBFunction=1,EUtranCellFDD=[LBF].* systemInformationBlock24 tReselectionNR=2,tReselectionNRSfHigh=100,tReselectionNRSfMedium=100
    set EUtranCellFDD=[LBF].*,UeMeasControl=1 rwrToNRAllowed false
fi

pr ENodeBFunction=1,EUtranCellFDD=[LBF].*,GUtranFreqRelation=3.*
if $nr_of_mos > 0
    set ENodeBFunction=1,EUtranCellFDD=[LBF].*,GUtranFreqRelation=3.* endcB1MeasPriority -1
    set ENodeBFunction=1,EUtranCellFDD=[LBF].*,GUtranFreqRelation=3.* cellReselectionPriority 7
    set ENodeBFunction=1,EUtranCellFDD=[LBF].*,GUtranFreqRelation=3.* cellReselectionSubPriority  2
fi
            """])
        return lines

    @staticmethod
    def pre_post_check(activity):
        return ["""
####:----------------> {activity} Check <----------------:####
scg
hget ENodeBFunction=1$ intraRanIpAddressRef|endcSplitAllowedNonDynPwrShUe
hget ^EUtranCell[FT]DD= primaryUpperLayerInd|endcAllowedPlmnList
hget ^UeMeasControl=1 endcMeasTime
hget ^ReportConfigB1GUtra=1 b1Thresholdrsrp|hysteresisB1|timeToTriggerB1
print Please Note: !!! Restart of Node is need if change in intraRanIpAddressRef is done to takes affect !!!
            """]

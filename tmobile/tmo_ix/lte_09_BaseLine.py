from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class lte_09_BaseLine(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0: return
        self.motype = 'Lrat'
        self.script_list += self.blstart() + self.parameter_check() + self.get_lock_cells()
        if self.df_enb_cell.loc[self.df_enb_cell.addcell].shape[0] > 0:
            self.script_list += (self.get_systemconstants_featurestate() + self.nodeparameter() +
                                 self.cellparameter() + self.market_specific_settings())
        if self.usid.df_enb_cell.loc[self.usid.df_enb_cell.addcell].shape[0] > 0:
            self.script_list += self.freq_cell_relation()
        self.script_list += self.wps_mocn_settings() + self.mfbi_settings()
        if self.usid.df_enb_cell.loc[self.usid.df_enb_cell.addcell].shape[0] > 0:
            self.script_list += self.software_update()
        self.script_list += self.get_unlock_cells() + self.parameter_check()

    def blstart(self):
        return [F"""
####:----------------> BL Supports for Carrier L2100, L1900, L700, L600, L2500 <----------------:####
####:----------------> BL Revised on 09/07/2024 <----------------:####
pv $momversion
if $momversion ~ ERBS
    print ERROR: Wrong File selected for This Site !!!
    l-
    return
fi
pr ENodeBFunction=1,EUtranCell[FT]DD=
if $nr_of_mos = 0
    print ERROR: EUtranCellFDD/EUtranCellTDD not found !!!"
l-
return
fi        

####:----------------> Logic <----------------:####
pv $mibprefix
$BBType = None
$RadioType = None
get ^FieldReplaceableUnit= ^productData$ Baseband.*6630
if $nr_of_mos > 0
    $BBType = BB6630
fi
get ^FieldReplaceableUnit= ^productData$ Baseband.*6648
if $nr_of_mos > 0
    $BBType = BB6648
fi
get ^FieldReplaceableUnit= ^productData$ Processor.*6651
if $nr_of_mos > 0
    $BBType = BB6651
fi
get ^FieldReplaceableUnit= ^productData$ Baseband.*5216
if $nr_of_mos > 0
    $BBType = BB5216
fi
get ^FieldReplaceableUnit= productData AIR.*6488.*B41
if $nr_of_mos > 0
    $RadioType = AIR6488B41
fi
get ^FieldReplaceableUnit= productData AIR.*6449.*B41
if $nr_of_mos > 0
    $RadioType = AIR6449B41
fi

$fdd_flag = 0
$tdd_flag = 0
$iot_flag = 0
pr ENodeBFunction=1,EUtranCellFDD=
if $nr_of_mos > 0
    $fdd_flag = 1
fi
pr ENodeBFunction=1,EUtranCellTDD=
if $nr_of_mos > 0
    $tdd_flag = 1
fi
pr ENodeBFunction=1,NbIotCell=
if $nr_of_mos > 0
    $iot_flag = 1
fi

$excalibur = 0
if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("excalibur")])}
   $excalibur = 1
fi

func getsectorval
    $var6 = $6
endfunc
        """]

    def get_systemconstants_featurestate(self):
        # sw_version = self.usid.client.software.swname[:9]
        # System Constant & Feature
        lines = []
        if (self.enbdata.get('BBChange', True)) or (self.df_enb_cell.shape[0] == self.df_enb_cell.loc[self.df_enb_cell.addcell].shape[0]):
            if self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['TDD'])].shape[0] > 0:
                lines.extend(self.get_sc_features_dict(sw=self.usid.client.software.swname[:9], script_type='LTE_TDD'))
            if self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD'])].shape[0] > 0:
                lines.extend(self.get_sc_features_dict(sw=self.usid.client.software.swname[:9], script_type='LTE_FDD'))

        # New/Old Logical FeatureState
        if self.df_enb_cell.loc[self.df_enb_cell.addcell & self.df_enb_cell.celltype.isin(['FDD', 'TDD'])].shape[0] > 0:
            lines.extend([F"""
####:---> Logical FeatureState <---:####
#### CPRI Compression for BB6648
get SystemFunctions=1,Lm=1,FeatureState=CXC4012051 ^licenseState$ ^1
if $BBType ~ BB6648 && $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4012051 featureState 1
fi

#### CPRI Compression for BB6651
get SystemFunctions=1,Lm=1,FeatureState=CXC4012051 ^licenseState$ ^1
if $BBType ~ BB6651 && $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4012051 featureState 1
fi

#### if non MSMM false, if MSMM on any sector true
get ^FieldReplaceableUnit= isSharedWithExternalMe true
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011018 featureState 1
fi
get ^SectorEquipmentFunction= mixedModeRadio true
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011018 featureState 1
fi

#### No of Cells
st ENodeBFunction=1,EUtranCell[FT]DD=
if $nr_of_mos > 3
   ## 6 Cell Support
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011317 featureState 1
else if $nr_of_mos > 6
   ## 7-12 Cell Support
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011317 featureState 1
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011356 featureState 1
else if $nr_of_mos > 12
   ## Support for 13-18 cells in single eNodeB
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011317 featureState 1
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011356 featureState 1
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011917 featureState 1
fi

#### Optimized Release Control Activation
get SystemFunctions=1,Lm=1,FeatureState=CXC4012485 ^licenseState$ ^1
if $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4012485 featureState 1
else
   l echo "ERROR: ----Optimized RRC Connection Release Control (CXC4012485) is unavailable----"
fi

#### SUPPLEMENTARY DL ONLY CELL Activation
get ^EUtranCell[FT]DD= ^isDlOnly$ ^true
if $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011567 featureState 1
fi

pr SystemFunctions=1,Lm=1,FeatureState=CXC4012051
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012051 featureState 1
fi

pr SystemFunctions=1,Lm=1,FeatureState=CXC4012052
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012052 featureState 1
fi

#### FeatureState for NbIotCell
pr ENodeBFunction=1,NbIotCell=
if $nr_of_mos > 0
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012081 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012079 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012508 featureState 1
fi

#### FeatureState for Category M Access & Category M Connected Mode Mobility
get ENodeBFunction=1,EUtranCellFDD= catm1SupportEnabled true
if $nr_of_mos > 0
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012082 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012187 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012319 featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012359 featureState 1
    scw L4911:1
fi
            """])

            # Quad Antenna
            if self.df_enb_cell.loc[self.df_enb_cell.addcell].shape[0] > 0:
                lines.extend([F"""
#### Quad Antenna
set SystemFunctions=1,Lm=1,FeatureState=CXC4010609 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011427 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011667 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011056 featureState 1                
                """])
    
            if (self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD'])]["sc"].nunique(dropna=True) > self.df_enb_cell.loc[
                        self.df_enb_cell.celltype.isin(['FDD'])]["sef"].nunique(dropna=True)) or (self.df_enb_cell.loc[
                                self.df_enb_cell.celltype.isin(['TDD'])]["sc"].nunique(dropna=True) > self.df_enb_cell.loc[
                                        self.df_enb_cell.celltype.isin(['TDD'])]["sef"].nunique(dropna=True)):
                lines.extend(['set SystemFunctions=1,Lm=1,FeatureState=CXC4011802 featureState 1', ''])
        return lines
    
    def nodeparameter(self):
        lines = []
        lines.extend(self.get_node_certificate())
        lines.extend(self.get_vswr_script())
        lines.extend([F"""
####:----------------> Node Parameter <----------------:####
set ENodeBFunction=1$ endcS1OverlapMode true
set SystemFunctions=1,Fm=1$ heartbeatInterval 100
set SystemFunctions=1,SwM=1$ fallbackTimer 1800
set NodeSupport=1,TimeSettings=1$ gpsToUtcLeapSeconds 0

####:----> PlmnInfo <----:####
pr ENodeBFunction=1,PlmnInfo=1$
if $nr_of_mos = 0
   crn ENodeBFunction=1,PlmnInfo=1
   actualPlmn mcc=310,mnc=260,mncLength=3
   plmnWhiteList mcc=310,mnc=260,mncLength=3
   end
else
   set ENodeBFunction=1,PlmnInfo=1$ plmnWhiteList mcc=310,mnc=260,mncLength=3
fi

pr ENodeBFunction=1,PlmnInfo=2$
if $nr_of_mos > 0
   del ENodeBFunction=1,PlmnInfo=2$
fi

####:----> TimerProfile <----:####
pr ENodeBFunction=1,TimerProfile=A$
if $nr_of_mos = 0
   crn ENodeBFunction=1,TimerProfile=A
   tRelocOverall 10
   tRrcConnReest 3
   tRrcConnectionReconfiguration 10
   tWaitForRrcConnReest 10
   end
fi
if $tdd_flag = 1
    set ENodeBFunction=1,TimerProfile=A$ tRrcConnectionReconfiguration 6
    set ENodeBFunction=1,TimerProfile=A$ tWaitForRrcConnReest 6
    set ENodeBFunction=1,CarrierAggregationFunction=1$ sCellSelectionMode 2
else if $fdd_flag = 1
    set ENodeBFunction=1,TimerProfile=A$ tRrcConnectionReconfiguration 10
    set ENodeBFunction=1,TimerProfile=A$ tWaitForRrcConnReest 10
fi
set ENodeBFunction=1,QciTable=default,QciProfilePredefined=qci1$ timerProfileRef ENodeBFunction=1,TimerProfile=A

####:----> QciProfilePredefined <----:####
if $fdd_flag = 1
    set ENodeBFunction=1,QciTable=default,QciProfilePredefined=default$ resourceAllocationStrategy 0
fi

####:----------------> PmFlexCounterFilter = uePowerClassFilter2, plmnFilter(0 & 1), plmnFilter1_QCI(1, 5, 6, 7, 8, 9) <----------------:####
pr ENodeBFunction=1,PmFlexCounterFilter=uePowerClassFilter2$
if $nr_of_mos = 0 && $tdd_flag = 1
    crn ENodeBFunction=1,PmFlexCounterFilter=uePowerClassFilter2
    uePowerClassFilterEnabled  true
    uePowerClassFilterMax  2
    uePowerClassFilterMin  2
    end
fi

pr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter0$
if $nr_of_mos = 0
    cr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter0
fi
pr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1$
if $nr_of_mos = 0
    cr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1
fi
pr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI1$
if $nr_of_mos = 0
    cr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI1
fi
pr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI5$
if $nr_of_mos = 0
    cr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI5
fi
pr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI6$
if $nr_of_mos = 0
    cr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI6
fi
pr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI7$
if $nr_of_mos = 0
    cr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI7
fi
pr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI8$
if $nr_of_mos = 0
    cr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI8
fi
pr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI9$
if $nr_of_mos = 0
    cr ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI9
fi

set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter0$ plmnFilterMax 0
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter0$ plmnFilterMin 0
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1$ plmnFilterMax 1
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1$ plmnFilterMin 1
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter[01]$ plmnFilterEnabled true
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI[156789]$ plmnFilterMax 1
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI[156789]$ plmnFilterMin 1
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI1$ qciFilterMax 1
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI1$ qciFilterMin 1
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI5$ qciFilterMax 5
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI5$ qciFilterMin 5
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI6$ qciFilterMax 6
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI6$ qciFilterMin 6
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI7$ qciFilterMax 7
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI7$ qciFilterMin 7
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI8$ qciFilterMax 8
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI8$ qciFilterMin 8
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI9$ qciFilterMax 9
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI9$ qciFilterMin 9
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI[156789]$ plmnFilterEnabled true
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI[156789]$ qciFilterEnabled true
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter[01]$ reportAppCounterOnly true
set1x ENodeBFunction=1,PmFlexCounterFilter=plmnFilter1_QCI[156789]$ reportAppCounterOnly true
commit

####:----------------> UlCompGroup  for L2100 -> 1, L1900(1C) -> 2, L700 -> 3, L600 -> 4, L1900(2C) -> 5 <----------------:####
func getsectorval
    $var6 = $6
endfunc

func funcCreateUlCompGroup
    crn ENodeBFunction=1,UlCompGroup=$ulcompid
    sectorCarrierRef $secref
    administrativeState 1
    end
endfunc

func funcUlCompGroupInitiate
    $zz = $1
    $ulcompid = $2
    get ^EUtranCellFDD=$zz$ ^isDlOnly$ > $isdlonly
    get ^EUtranCellFDD=$zz$ ^earfcnul$ > $earfcnul
    if $nr_of_mos > 1 && $isdlonly = false
        $secref =
        mr eCellFDDss
        ma cellfdd ^EUtranCellFDD= ^earfcnul$ $earfcnul
        for $zz in cellfdd
            get $zz ^sectorCarrierRef$ > $seccarrval
            getsectorval $seccarrval
            $secref = $secref $var6
        done
        mr cellfdd
        funcCreateUlCompGroup
    fi
    unset $zz
    unset $ulcompid
    unset $isdlonly
    unset $earfcnul
    unset $seccarrval
    unset $secref
    unset $var6
endfunc

funcUlCompGroupInitiate L.* 1 L2100-1C
funcUlCompGroupInitiate D.* 3 L700-1C
funcUlCompGroupInitiate C.* 3 L850-1C
funcUlCompGroupInitiate E.* 4 L600-1C
funcUlCompGroupInitiate B.*1 2 L1900-1C
funcUlCompGroupInitiate B.*2 5 L1900-2C

####:----------------> RlfProfile=1 <----------------:####
pv $mibprefix
## set RlfProfile=1 --- t311 3sec for West
if $mibprefix ~ ElPaso || $mibprefix ~ Albuquerque || $mibprefix ~ Boise || $mibprefix ~ Draper || $mibprefix ~ Bothell 
    set ENodeBFunction=1,RlfProfile=1$ t311 3000
else if $mibprefix ~ ElMonte || $mibprefix ~ Escondido || $mibprefix ~ Fresno || $mibprefix ~ Irvine || $mibprefix ~ LasVegas 
    set ENodeBFunction=1,RlfProfile=1$ t311 3000
else if $mibprefix ~ Riverside || $mibprefix ~ SanFrancisco || $mibprefix ~ SantaClara || $mibprefix ~ SimiValley || $mibprefix ~ Stockton
    set ENodeBFunction=1,RlfProfile=1$ t311 3000
else if $mibprefix ~ Torrance || $mibprefix ~ Vegas || $mibprefix ~ WestOakland || $mibprefix ~ WestSacramento || $mibprefix ~ Hawaii
    set ENodeBFunction=1,RlfProfile=1$ t311 3000
else
    get ENodeBFunction=1,RlfProfile=1$ t311
fi
## set RlfProfile=1 --- t311 10sec for NE region
if $mibprefix ~ Syosset || $mibprefix ~ Wayne || $mibprefix ~ Bloomfield || $mibprefix ~ Syosset_LI || $mibprefix ~ Norton 
    set ENodeBFunction=1,RlfProfile=1$ t311 10000
else if $mibprefix ~ EastProvidence || $mibprefix ~ Philadelphia || $mibprefix ~ Beltsville || $mibprefix ~ Norfolk || $mibprefix ~ Salina 
    set ENodeBFunction=1,RlfProfile=1$ t311 10000
else if  $mibprefix ~ Charlotte || $mibprefix ~ Norcross
    set ENodeBFunction=1,RlfProfile=1$ t311 10000
else
    get ENodeBFunction=1,RlfProfile=1$ t311
fi

if $tdd_flag = 1
    set ^ENodeBFunction=1$ timeAndPhaseSynchCritical true
    set ^ENodeBFunction=1$ srsAllocationV2TddAasEnabled true
    set ^ENodeBFunction=1$ zzzTemporary21 0
    set ENodeBFunction=1,AnrFunction=1,AnrFunctionEUtran=1$ anrUesThreshInterFMax 20
    set ENodeBFunction=1,AnrFunction=1,AnrFunctionEUtran=1$ anrUesThreshInterFMin 1
    set ENodeBFunction=1,EUtranCellTDD= noOfPucchFormat3PrbPairs 2
    set ENodeBFunction=1,EUtranCellTDD=.*,UeMeasControl=1,ReportConfigA5=1$ a5Threshold1Rsrp -119
    set ENodeBFunction=1,EUtranCellTDD=.*,UeMeasControl=1,ReportConfigA5=1$ a5Threshold2Rsrp -115
fi
        """])
        return lines

    def cellparameter(self):
        lines = []
        lines.extend([F"""
####:----------------> Parameter Setting for EUtranCellFDD & EUtranCellTDD <----------------:####
####:---> networkSignallingValue -> [B12 = 6 (NS_06), Other = 1 (NS_01)] , This has been removed as Requested from RF <---:####
####:---> cellSubscriptionCapacity -> 10000 for 5Mhz; 20000 for 10MHz; 30000 for 15MHz; 40000 for 20MHz <---:####

mr eutrancells
ma eutrancells ^EUtranCell[FT]DD= ^primaryPlmnReserved$ true
for $mo in eutrancells
    #### get $mo ^freqBand$ > $fband
    #### if $fband = 12
    ####     set $mo networkSignallingValue 6
    #### else
    ####     set $mo networkSignallingValue 1
    #### fi
    get $mo ^dlChannelBandwidth$|^channelBandwidth$ > $bw
    if $bw = 5000
       set $mo cellSubscriptionCapacity 10000
    else if $bw = 10000
       set $mo cellSubscriptionCapacity 20000
    else if $bw = 15000
       set $mo cellSubscriptionCapacity 30000
    else if $bw = 20000
       set $mo cellSubscriptionCapacity 40000
    fi
done
mr eutrancells
#### unset $fband
unset $mo
unset $bw

####:----------------> Parameter Setting for EUtranCellFDD Only<----------------:####
#### mappingInfoCe for catm1SupportEnabled cells
mr catm1cells
ma newfddcells ^EUtranCellFDD= ^catm1SupportEnabled$ true
for $mo in newfddcells
    set $mo mappingInfoCe mappingInfoSIB3=2,mappingInfoSIB4=4,mappingInfoSIB5=3
done
unset $mo
mr catm1cells

func noofpucch_dus
    set ENodeBFunction=1,EUtranCellFDD= noOfPucchCqiUsers 640
    set ENodeBFunction=1,EUtranCellFDD= noOfPucchSrUsers 640
    mr allfddcells
    ma allfddcells ^EUtranCellFDD=
    for $mo in allfddcells
        get $mo ulChannelBandwidth > $ulchabw
        if $ulchabw = 20000
            set $mo noOfPucchSrUsers 480
            set $mo noOfPucchCqiUsers 480
        fi
    done
    mr allfddcells
    unset $mo
    unset $ulchabw
endfunc

func parameterforfddcells
    mr newfddcells
    ma newfddcells ^EUtranCellFDD= ^primaryPlmnReserved$ true
    for $mo in newfddcells
        get $mo ^eUtranCellFDDId$ > $fddid
        if $fddid ~ ^L.*
            set $mo crsGain 300
            set $mo prioAdditionalFreqBandList 66
            set $mo mfbiFreqBandIndPrio true
        else if $fddid ~ ^B.*
            set $mo crsGain 300
            set ENodeBFunction=1,EUtranCellFDD=$fddid,UeMeasControl=1,ReportConfigB1GUtra=1$ timeToTriggerB1 80
        else if $fddid ~ ^D.*
            set $mo catm1SupportEnabled true
            set $mo crsGain 300
            set ENodeBFunction=1,EUtranCellFDD=$fddid,UeMeasControl=1,ReportConfigSearch=1$ a1a2SearchThresholdRsrp -106
            set ENodeBFunction=1,EUtranCellFDD=$fddid,UeMeasControl=1,ReportConfigA5=1$ a5Threshold1Rsrp -106
            set ENodeBFunction=1,EUtranCellFDD=$fddid,UeMeasControl=1,ReportConfigA5=1$ a5Threshold2Rsrp -115
        else if $fddid ~ ^E.*
            set $mo mappingInfo mappingInfoSIB24=8
            set ENodeBFunction=1,EUtranCellFDD=$fddid,UeMeasControl=1,ReportConfigSearch=1$ a1a2SearchThresholdRsrp -106
            set ENodeBFunction=1,EUtranCellFDD=$fddid,UeMeasControl=1,ReportConfigA5=1$ a5Threshold1Rsrp -106
            set ENodeBFunction=1,EUtranCellFDD=$fddid,UeMeasControl=1,ReportConfigA5=1$ a5Threshold2Rsrp -115
        fi
    done
    mr newfddcells
endfunc

if $fdd_flag = 1
    parameterforfddcells
fi

#### Improved handling of failed ENDC Setup - LTE FDD B2 and B4 Only (ENDC Bands) - Mixed Mode FDD and LTE FDD Nodes
set EUtranCellFDD=[L|B|F].* loopingEndcProtectionEnabled true

####:----------------> Parameter Setting for EUtranCellTDD L41 (L2500) Only <----------------:####
func parameterfortddcells
    ####:----> Node Parameter <----:####
    set ENodeBFunction=1$ srsAllocationV2TddAasEnabled true
    set ENodeBFunction=1$ timeAndPhaseSynchCritical true
    set ENodeBFunction=1$ zzzTemporary21 0
    set ENodeBFunction=1,AnrFunction=1,AnrFunctionEUtran=1$ anrUesThreshInterFMax 20
    set ENodeBFunction=1,AnrFunction=1,AnrFunctionEUtran=1$ anrUesThreshInterFMin 1
    set ENodeBFunction=1,CarrierAggregationFunction=1$ sCellSelectionMode 2
    set ENodeBFunction=1,LoadBalancingFunction=1$ lbHitRateEUtranRemoveThreshold 2
    set ENodeBFunction=1,TimerProfile=A$ tRrcConnReest 3
    
    #### 22Q4 Addition
    set ENodeBFunction=1,EUtranCellFDD= noOfPucchFormat3PrbPairs 2
    set ENodeBFunction=1,EUtranCellTDD= noOfPucchFormat3PrbPairs 2
    get FieldReplaceableUnit= productData AIR.*6419.*B41
    if $nr_of_mos != 0
        set ENodeBFunction=1,EUtranCellTDD= zzzTemporary73 15
    fi

    ####:----> Cell Parameter <----:####
    mr newtddcells
    ma newtddcells ^EUtranCellTDD= ^primaryPlmnReserved$ true
    set newtddcells crsGain 300
    for $mo in newtddcells
        get $mo ^eUtranCellTDDId$ > $cell_tdd_id
        set ENodeBFunction=1,EUtranCellTDD=$cell_tdd_id,UeMeasControl=1,ReportConfigSCellA1A2=1$ a1a2ThresholdRsrpBidir -119
    done
    mr newtddcells
endfunc

if $tdd_flag = 1
    parameterfortddcells
fi
        """])
        
        # EUtranCellFDD, EUtranCellTDD ---> PmUeMeasControl ---> ueMeasIntraFreq1
        new_lines = []
        for _, row in self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD', 'TDD'])].iterrows():
            if self.usid.df_enb_ef.loc[(self.usid.df_enb_ef.postsite == self.node) &
                                       (self.usid.df_enb_ef.earfcndl == row.earfcndl)].shape[0] > 0:
                cell_ldn = F'ENodeBFunction=1,EUtranCell{row.celltype}={row.postcell}'
                cell_pm_ldn = F'{cell_ldn},UeMeasControl=1,PmUeMeasControl=1'
                frq = self.usid.df_enb_ef.loc[(self.usid.df_enb_ef.postsite == self.node) &
                                              (self.usid.df_enb_ef.earfcndl == row.earfcndl), 'freqid'].iloc[0]
                new_lines.extend([
                    F'set {cell_pm_ldn}$ ueMeasIntraFreq1 eutranFrequencyRef=ENodeBFunction=1,EUtraNetwork=1,EUtranFrequency={frq},'
                    F'reportConfigEUtraIntraFreqPmRef={cell_ldn},UeMeasControl=1,ReportConfigEUtraIntraFreqPm=1',
                    F'set {cell_pm_ldn}$ ueMeasIntraFreq2 eutranFrequencyRef=ENodeBFunction=1,EUtraNetwork=1,EUtranFrequency={frq},'
                    F'reportConfigEUtraIntraFreqPmRef={cell_ldn},UeMeasControl=1,ReportConfigEUtraIntraFreqPm=2',
                ])
        if len(new_lines) > 0:
            lines += ['####:----------------> PmUeMeasControl Setting <----------------:####'] + new_lines + ['', '']
        return lines

    def freq_cell_relation(self):
        lines = []
        # EUtranFreqRelation, UtranFreqRelation
        lines.extend([F"""
####:----------------> Parameter Setting for EUtranFreqRelation <----------------:####
pr ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=.*,ExternalEUtranCell[FT]DD=
if $nr_of_mos > 0
    set ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=.*,ExternalEUtranCell[FT]DD= pciConflict 0,0,0,0,0
    set ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=.*,ExternalEUtranCell[FT]DD= lbEUtranCellOffloadCapacity 1000
fi
pr ENodeBFunction=1,UtraNetwork=1,UtranFrequency=.*,ExternalUtranCellFDD=
if $nr_of_mos > 0
    set ENodeBFunction=1,UtraNetwork=1,UtranFrequency=.*,ExternalUtranCellFDD= srvccCapability 1
    set ENodeBFunction=1,UtraNetwork=1,UtranFrequency=.*,ExternalUtranCellFDD= isRemoveAllowed true
fi

####:----------------> Parameter Setting for EUtranFrequency <----------------:####
####:----------------> Parameter Setting for EUtranFreqRelation <----------------:####
####:---> allowedMeasBandwidth 15=3MHz, 25=5MHz, 50=10MHz, 75=15MHz, 100=20MHz <---:####
####:--> apply allowedMeasBandwidth on EUtranFreqRelation="earfcn" based on bandwidth of EUtranCellFDD/EUtranCellTDD <---:####
$earfcnbwdict = 0
mr ecells
ma ecells ENodeBFunction=1,EUtranCell[FT]DD=
for $ecell in ecells
    get $ecell ^earfcndl$|^earfcn$ > $earfcn
    get $ecell ^dlChannelBandwidth$|^channelBandwidth$ > $earfcnbwdict[$earfcn]
done
mr ecells
unset $ecell
unset $earfcn

mr efreqrelations
ma efreqrelations ENodeBFunction=1,EUtranCell.DD=.*,EUtranFreqRelation=
for $mo in efreqrelations
   get $mo eutranFrequencyRef > $eutranFrequencyRefVal
   get $eutranFrequencyRefVal arfcnValueEUtranDl > $arfcn
   l echo $earfcnbwdict[$arfcnValueEUtranDlVal]
   if $earfcnbwdict[$arfcn] = 3000
      set $mo allowedMeasBandwidth 15
   else if $earfcnbwdict[$arfcn] = 5000
      set $mo allowedMeasBandwidth 25
   else if $earfcnbwdict[$arfcn] = 10000
      set $mo allowedMeasBandwidth 50
   else if $earfcnbwdict[$arfcn] = 15000
      set $mo allowedMeasBandwidth 75
   else if $earfcnbwdict[$arfcn] = 20000
      set $mo allowedMeasBandwidth 100
   fi
done
mr efreqrelations
unset $earfcnbwdict
unset $mo
unset $eutranFrequencyRefVal
unset $arfcn

pr ENodeBFunction=1,EUtranCellFDD=.*,EUtranFreqRelation=
if $nr_of_mos > 0 && $excalibur != 1
    set ENodeBFunction=1,EUtranCellFDD=.*,EUtranFreqRelation= voicePrio 6
    set ENodeBFunction=1,EUtranCellFDD=.*,EUtranFreqRelation= threshXHigh 8
    set ENodeBFunction=1,EUtranCellFDD=.*,EUtranFreqRelation= threshXLow 0
fi

#### ---- lbActivationThreshold ---- ####
func lbactivationthreshold_for_l600_l700_freq
    set ENodeBFunction=1,LoadBalancingFunction=1$ lbThreshold 80
    set ENodeBFunction=1,LoadBalancingFunction=1$ lbCeiling 800
    set ENodeBFunction=1,LoadBalancingFunction=1$ lbRateOffsetLoadThreshold 1000
    set ENodeBFunction=1,EUtranCell[FT]DD= cellCapMaxCellSubCap 1000000
    set ENodeBFunction=1,EUtranCell[FT]DD= cellCapMinCellSubCap 0
    set1x ENodeBFunction=1,QciTable=default,QciProfileOperatorDefined=qci128$ qciSubscriptionQuanta 600
    set1x ENodeBFunction=1,QciTable=default,QciProfilePredefined=qci6$ qciSubscriptionQuanta 600
    set1x ENodeBFunction=1,QciTable=default,QciProfilePredefined=qci7$ qciSubscriptionQuanta 300
    set1x ENodeBFunction=1,QciTable=default,QciProfilePredefined=qci8$ qciSubscriptionQuanta 150
    set1x ENodeBFunction=1,QciTable=default,QciProfilePredefined=qci9$ qciSubscriptionQuanta 150
    commit
    
    $freq_l700_l600_5mhz = (5035|68...)
    $freq_not_L700_L600_5mhz = (41490|41292|41094|41463|1125|1150|675|2300)
    lset EUtranCell[FT]DD=.*.,EUtranFreqRelation= lbActivationThreshold 0
    lset ENodeBFunction=1,EUtranCell.DD=[BLFT].*,EUtranFreqRelation=$freq_l700_l600_5mhz lbActivationThreshold 1000
    unset $freq_l700_l600_5mhz
    unset $freq_not_L700_L600_5mhz
endfunc

pv $mibprefix
// west and excalibur markets
if {'|| '.join([F'$mibprefix ~ {_} ' for _ in ['ElPaso', 'Albuquerque', 'Boise', 'Draper', 'Bothell', 'ElMonte', 'Escondido', 'Fresno',
                                               'Irvine', 'LasVegas', 'Riverside', 'SanFrancisco', 'SantaClara', 'SimiValley',
                                               'Stockton', 'Torrance', 'Vegas', 'WestOakland', 'WestSacramento', 'Hawaii', 'Atlanta',
                                               'Jacksonville', 'Miami', 'Orlando', 'Tampa', 'Excalibur']])}
    set ENodeBFunction=1,LoadBalancingFunction=1 lbRateOffsetLoadThreshold 1000
    set EUtranCell.DD=.*,EUtranFreqRelation= lbActivationThreshold 0
    lbactivationthreshold_for_l600_l700_freq
fi

// NE markets
if {'|| '.join([F'$mibprefix ~ {_} ' for _ in ['Syosset', 'Wayne', 'Bloomfield', 'Syosset_LI', 'Norton', 'EastProvidence',
                                               'Philadelphia', 'Beltsville', 'Norfolk', 'Salina', 'Charlotte', 'Norcross']])}
    set ENodeBFunction=1,LoadBalancingFunction=1 lbRateOffsetLoadThreshold 6500
    set EUtranCell.DD=.*,EUtranFreqRelation= lbActivationThreshold 0
fi

####:----------------> Parameter Setting for EUtranFreqRelation <----------------:####
pr ENodeBFunction=1,EUtranCell[FT]DD=.*,EUtranFreqRelation=.*,EUtranCellRelation=
if $nr_of_mos > 0
    set ENodeBFunction=1,EUtranCell[FT]DD=.*,EUtranFreqRelation=.*,EUtranCellRelation= cellIndividualOffsetEUtran 0
    set ENodeBFunction=1,EUtranCell[FT]DD=.*,EUtranFreqRelation=.*,EUtranCellRelation= lbBnrAllowed true
    set ENodeBFunction=1,EUtranCell[FT]DD=.*,EUtranFreqRelation=.*,EUtranCellRelation= lbCovIndicated false
fi
        
####:----------------> Parameter Setting for UtranFreqRelation <----------------:####
pr ENodeBFunction=1,EUtranCell[FT]DD=.*,UtranFreqRelation=
if $nr_of_mos > 0 && $excalibur != 1
    set ENodeBFunction=1,EUtranCell[FT]DD=.*,UtranFreqRelation= connectedModeMobilityPrio -1
fi

mr utranrel
ma utranrel ^UtranFreqRelation=
for $mo in utranrel
    acc $mo setMaxNrUtranCellRelations
    32
done
mr utranrel

####:----------------> Parameter Setting for UtranCellRelation <----------------:####
pr ENodeBFunction=1,EUtranCell[FT]DD=.*,UtranFreqRelation=.*,UtranCellRelation=
if $nr_of_mos > 0
    set ENodeBFunction=1,EUtranCell[FT]DD=.*,UtranFreqRelation=.*,UtranCellRelation= lbBnrAllowed false
    set ENodeBFunction=1,EUtranCell[FT]DD=.*,UtranFreqRelation=.*,UtranCellRelation= lbCovIndicated false
fi

####:----------------> Parameter Setting for GeranFreqGroupRelation <----------------:####
pr ENodeBFunction=1,EUtranCell[FT]DD=.*,GeranFreqGroupRelation=
if $nr_of_mos > 0 && $excalibur != 1
    set ENodeBFunction=1,EUtranCell[FT]DD=.*,GeranFreqGroupRelation= csFallbackPrio 0
    set ENodeBFunction=1,EUtranCell[FT]DD=.*,GeranFreqGroupRelation= csFallbackPrioEC 0
    set ENodeBFunction=1,EUtranCell[FT]DD=.*,GeranFreqGroupRelation= connectedModeMobilityPrio -1
fi
        
        """])
        # EUtranCellRelation
        lines.extend(['####:----------------> Parameter Setting for EUtranCellRelation <----------------:####'])
        if self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD', 'TDD'])].shape[0] > 0:
            for _, row in self.usid.df_enb_ee.loc[(self.usid.df_enb_ee.postsite == self.node) &
                                                  (~(self.usid.df_enb_ee.scell == '2 (AUTO)'))].iterrows():
                s_celltype = self.df_enb_cell.loc[(self.df_enb_cell.postcell == row.postcell), 'celltype'].iloc[0]
                lines.extend([
                    F'set ENodeBFunction=1,EUtranCell{s_celltype}={row.postcell},EUtranFreqRelation={row.relid},EUtranCellRelation={row.crelid}$ sCellCandidate {row.scell[0]}',
                    F'set ENodeBFunction=1,EUtranCell{s_celltype}={row.postcell},EUtranFreqRelation={row.relid},EUtranCellRelation={row.crelid}$ isRemoveAllowed false'
                ])
        return lines

    def software_update(self):
        lines = []
        if self.usid.client.software.swname[:9] > 'TMO_24_Q4':
            lines += [
                '####:----------------> LTE Parameter Setting for 25Q1 SW <----------------:####',
                'set FmAlarmType=Radio.*Alert.* isNotified 0',
                ''
            ]
        return lines


    def market_specific_settings(self):
        lines = [F"""
####:----------------> Market Specific Parameter Setting <----------------:####
#### Escondido, Vegas, ElMonte, Torrance, SimiValley, Irvine, Riverside
####:----> ENDC_Periodic_NR_Search activate in L19 and L21 <----:####
func tri_la_endc_periodic_nr_search_market_settings
    if $fdd_flag = 1
        set ENodeBFunction=1,EUtranCellFDD=B.*,UeMeasControl=1 endcMeasTime 2000
        set ENodeBFunction=1,EUtranCellFDD=B.*,UeMeasControl=1 endcMeasRestartTime 15000
        set ENodeBFunction=1,EUtranCellFDD=B.*,UeMeasControl=1 endcB1MeasWindow 300
        set ENodeBFunction=1,EUtranCellFDD=L.*,UeMeasControl=1 endcMeasTime 2000
        set ENodeBFunction=1,EUtranCellFDD=L.*,UeMeasControl=1 endcMeasRestartTime 15000
        set ENodeBFunction=1,EUtranCellFDD=L.*,UeMeasControl=1 endcB1MeasWindow 300
        set ENodeBFunction=1,EUtranCellFDD=F.*,UeMeasControl=1 endcMeasTime 2000
        set ENodeBFunction=1,EUtranCellFDD=F.*,UeMeasControl=1 endcMeasRestartTime 15000
        set ENodeBFunction=1,EUtranCellFDD=F.*,UeMeasControl=1 endcB1MeasWindow 300
    fi
endfunc
        
func tri_la_lte_gms_relation_market_settings
    pr ENodeBFunction=1,EUtranCell.DD=.*,GeranFreqGroupRelation=
    if $nr_of_mos > 0
        set ENodeBFunction=1,EUtranCell.DD=.*,GeranFreqGroupRelation= cellReselectionPriority 0
        set ENodeBFunction=1,EUtranCell.DD=.*,GeranFreqGroupRelation= csFallbackPrio 7
        set ENodeBFunction=1,EUtranCell.DD=.*,GeranFreqGroupRelation= csFallbackPrioEC 7
        set ENodeBFunction=1,EUtranCell.DD=.*,GeranFreqGroupRelation= nccPermitted 11111111
    fi
endfunc

####:----> LTE EUtranFreqRelation -> caFreqPriority <----:####
////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////
///// Source			Target		T_Band	caFreqPriority	eutranfreqrelationid                          
///// EUtranCellFDD		B41			B2		-1				40090                                     
///// EUtranCellFDD		B25			T1		-1				8665                                      
///// EUtranCellFDD		B2_2C		F1		2				675                                       
///// EUtranCellFDD		B12			B1		2				5035                                      
///// EUtranCellFDD		850			C1		2				8750                                      
///// EUtranCellFDD		AWS3		E1		3				66903                                     
///// EUtranCellFDD		B71			E1		3				68661|68886                               
///// EUtranCellFDD		B2_1C		L1		4				1150                                      
///// EUtranCellFDD		B66			D1		6				2300                                      
/////																									  
///// EUtranCellTDD		B41			T2		6				40090                                     
///// EUtranCellTDD		other_B41	B25		-1				68661|675|5035|2300|66903|68886|1150|8665 
////////////////////////////////////////////////////////////////////////////////////////////////////////
F'func tri_la_cafreqpriority_market_settings
    unset $fdd_caFreqPrio
    unset $tdd_caFreqPrio
    
    $fdd_caFreqPrio[40090] = -1
    $fdd_caFreqPrio[8665] = -1
    $fdd_caFreqPrio[675] = 2
    $fdd_caFreqPrio[5035] = 2
    $fdd_caFreqPrio[8750] = 2
    $fdd_caFreqPrio[66903] = 3
    $fdd_caFreqPrio[68661] = 3
    $fdd_caFreqPrio[68886] = 3
    $fdd_caFreqPrio[1150] = 4
    $fdd_caFreqPrio[2300] = 6
    for $var in $fdd_caFreqPrio
        get ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$var$ caFreqPriority
        if $nr_of_mos > 0
            set ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$var$ caFreqPriority $fdd_caFreqPrio[$var]
        fi
    done

    $tdd_caFreqPrio[40090] = 6
    $tdd_caFreqPrio[8665] = -1
    $tdd_caFreqPrio[675] = -1
    $tdd_caFreqPrio[5035] = -1
    $tdd_caFreqPrio[8750] = -1
    $tdd_caFreqPrio[66903] = -1
    $tdd_caFreqPrio[68661] = -1
    $tdd_caFreqPrio[68886] = -1
    $tdd_caFreqPrio[1150] = -1
    $tdd_caFreqPrio[2300] = -1
    for $var in $tdd_caFreqPrio
        get ENodeBFunction=1,EUtranCellTDD=.*.,EUtranFreqRelation=$var$ caFreqPriority
        if $nr_of_mos > 0
            set ENodeBFunction=1,EUtranCellTDD=.*.,EUtranFreqRelation=$var$ caFreqPriority $tdd_caFreqPrio[$var]
        fi
    done
    
    get EUtranCell[FT]DD=.*.,EUtranFreqRelation= caFreqPriority
    unset $fdd_caFreqPrio
    unset $tdd_caFreqPrio
    unset $var
endfunc

#### Long Island Market - Syosset_LI
func long_island_market_setting
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012034 featureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012371 featureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011443 featureState 1
    set ENodeBFunction=1,EUtranCell[FT]DD= cellCapMinMaxWriProt true
    if $tdd_flag = 1
        set ^SectorCarrier= digitalTilt 10
        set ENodeBFunction=1,EUtranCellTDD=T noOfPucchCqiUsers 320
        set ENodeBFunction=1,EUtranCellTDD=T noOfPucchSrUsers 320
        set ENodeBFunction=1,EUtranCellTDD=T crsGain 177
        set ENodeBFunction=1,EUtranCellTDD=T.*,UeMeasControl=1,ReportConfigSCellA1A2=1$ a1a2ThresholdRsrpBidir -119
    fi
endfunc


#### New York Market - Syosset
func new_york_market_setting
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011443 featureState 1
    if $tdd_flag = 1
        set ENodeBFunction=1,EUtranCellTDD=T crsGain 0
        set ENodeBFunction=1,EUtranCellTDD=T pdschTypeBGain 0
    fi
endfunc

####  Market - Charlotte
func charlotte_market_setting
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011346 featureState 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011247 featureState 0
endfunc

####  Hawaii Market - Hawaii
func hawaii_market_setting
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011346$  featureState 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011247$  featureState 0
    if $fdd_flag = 1
        set ENodeBFunction=1,EUtranCellFDD=.*,UeMeasControl=1$ searchefforttime 0
        set ENodeBFunction=1,EUtranCellFDD=.*,UeMeasControl=1,ReportConfigSearch=1$ a2CriticalThresholdRsrp -126
    fi
endfunc

#### Philadelphia Market - Philadelphia
func philadelphia_market_setting
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011714$ featureState 1
endfunc

#### SanFrancisco Market - SanFrancisco, SantaClara, WestOakland
func ncal_market_setting
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011700 featureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011922 featureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011981 featureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011980 featureState 1
endfunc

#### Washington DC Market - Beltsville
func washington_dc_market_setting
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011346 featureState 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011716 featureState 0
endfunc


####:- excalibur_market_settings -:####
func none_excalibur_market_settings
    set ENodeBFunction=1,RadioBearerTable=default,MACConfiguration=1$ ulTtiBundlingMaxHARQTx 7
    mr ecell
    ma ecell ENodeBFunction=1,EUtranCellFDD=
    if $fdd_flag = 1
        set ecell ttiBundlingSwitchThresHyst 40
        set ecell ttiBundlingSwitchThres 150
        set ecell ttiBundlingAfterReest 1
        set ecell ttiBundlingAfterHO 1
        set ecell pdcchTargetBlerVolte 6
        set ecell pdcchOuterLoopUpStepVolte 9
        set ecell pdcchOuterLoopInitialAdjVolte -30
        set ecell ulHarqVolteBlerTarget 4
        set ecell ttiBundlingAtSetup 1
        set ecell pdcchCovImproveSrb true
        set ecell pdcchCovImproveQci1 true
        set ecell pdcchCovImproveDtx true
    fi
    for $mo in ecell
        get $mo dlChannelBandwidth$ > $dlchabw
        if $dlchabw = 20000
            set $mo pdcchPowerBoostMax 6
        else if $dlchabw = 15000
            set $mo pdcchPowerBoostMax 3
        else if $dlchabw = 10000
            set $mo pdcchPowerBoostMax 3
        else if $dlchabw = 5000
            set $mo pdcchPowerBoostMax 0
        fi
    done
    mr ecell
    unset $mo
    unset $dlchabw
endfunc

func excalibur_market_settings
    if $fdd_flag = 1
        set ENodeBFunction=1,EUtranCellFDD= pdcchTargetBlerVolte 22
        set ENodeBFunction=1,EUtranCellFDD= pdcchOuterLoopUpStepVolte 6
        set ENodeBFunction=1,EUtranCellFDD= pdcchOuterLoopInitialAdjVolte -70
    fi
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011914 featureState 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011253 featureState 0
endfunc

func la_la_north_parameter_market_settings
    mr cells
    ma cells ^EUtranCell[FT]DD=
    for $mo in cells
        get $mo ^eUtranCell[FT]DDId$ > $cellid
        set ENodeBFunction=1,EUtranCell[FT]DD=$cellid,UeMeasControl=1,ReportConfigEUtraInterFreqLb=1$ a5Threshold1Rsrp -140
        set ENodeBFunction=1,EUtranCell[FT]DD=$cellid,UeMeasControl=1,ReportConfigEUtraInterFreqLb=1$ a5Threshold2Rsrp  -117
        if $cellid ~ ^B.* && $cellid ~ ^B.*2$
            set ENodeBFunction=1,EUtranCell[FT]DD=$cellid,UeMeasControl=1,ReportConfigSearch=1$ a1a2SearchThresholdRsrp -105
        else if $cellid ~ ^B.* || $cellid ~ ^T.* || $cellid ~ ^L.*
            set ENodeBFunction=1,EUtranCell[FT]DD=$cellid,UeMeasControl=1,ReportConfigSearch=1$ a1a2SearchThresholdRsrp -118
        else if $cellid ~ ^D.*
            set ENodeBFunction=1,EUtranCell[FT]DD=$cellid,UeMeasControl=1,ReportConfigSearch=1$ a1a2SearchThresholdRsrp -105
        else if $cellid ~ ^E.*
            set ENodeBFunction=1,EUtranCell[FT]DD=$cellid,UeMeasControl=1,ReportConfigSearch=1$ a1a2SearchThresholdRsrp -116
        fi
    done
    mr cells
endfunc

pv $mibprefix
if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("tri_la")])}
    tri_la_endc_periodic_nr_search_market_settings
    tri_la_cafreqpriority_market_settings
    tri_la_lte_gms_relation_market_settings
else if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("ncal")])}
    ncal_market_setting
else if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("long_island")])}
    long_island_market_setting
else if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("new_york")])}
    new_york_market_setting
else if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("charlotte")])}
    charlotte_market_setting
else if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("hawaii")])}
    hawaii_market_setting
else if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("philadelphia")])}
    philadelphia_market_setting
else if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("washington_dc")])}
    washington_dc_market_setting
fi


if {" || ".join(["$mibprefix ~ " + _ for _ in ["ElMonte", "Torrance", "SimiValley"]])}
    la_la_north_parameter_market_settings
fi


if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("excalibur")])}
    excalibur_market_settings
else
    none_excalibur_market_settings
fi
        """]
        # lines.extend([
        #     # F'',
        #     # F'    $AWS3 = (66903)',
        #     # F'    pv $AWS3',
        #     # F'    $B41 = (40090|40270)',
        #     # F'    pv $B41',
        #     # F'    $B66 = (2300)',
        #     # F'    pv $B66',
        #     # F'    $B2_1C = (1150)',
        #     # F'    pv $B2_1C',
        #     # F'    $B2_2C = (675)',
        #     # F'    pv $B2_2C',
        #     # F'    $B71 = (68661|68886)',
        #     # F'    pv $B71',
        #     # F'    $B12 = (5035)',
        #     # F'    pv $B12',
        #     # F'    $B25 = (8665)',
        #     # F'    pv $B25',
        #     # F'    $other_B41 = (68661|675|5035|2300|66903|68886|1150|8665)',
        #     # F'    pv $other_B41',
        #     # F'    ',
        #     # F'    get ENodeBFunction=1,EUtranCell[FT]DD=.*.,EUtranFreqRelation= caFreqPriority',
        #     # F'    if $fdd_flag = 1',
        #     # F'        set ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$AWS3 caFreqPriority 3',
        #     # F'        set ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$B41 caFreqPriority -1',
        #     # F'        set ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$B66 caFreqPriority 6',
        #     # F'        set ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$B2_1C caFreqPriority 4',
        #     # F'        set ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$B2_2C caFreqPriority 2',
        #     # F'        set ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$B71 caFreqPriority 3',
        #     # F'        set ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$B12 caFreqPriority 2',
        #     # F'        set ENodeBFunction=1,EUtranCellFDD=.*.,EUtranFreqRelation=$B25 caFreqPriority -1',
        #     # F'    fi',
        #     # F'    if $tdd_flag = 1',
        #     # F'        set ENodeBFunction=1,EUtranCellTDD=.*.,EUtranFreqRelation=$B41 caFreqPriority 6',
        #     # F'        set ENodeBFunction=1,EUtranCellTDD=.*.,EUtranFreqRelation=$other_B41 caFreqPriority -1',
        #     # F'    fi',
        # ])
        return lines

    @staticmethod
    def mfbi_settings():
        return ["""
####:----------------> MFBI Parameter Setting <----------------:####
set ENodeBFunction=1$ mfbiSupportPolicy true
// set ENodeBFunction=1$ mfbiSupport true
set ENodeBFunction=1$ useBandPrioritiesInScellEval true
set ENodeBFunction=1$ caAwareMfbiIntraCellHo true
set ENodeBFunction=1$ mfbiFbipOnX2Enabled true
set ENodeBFunction=1$ prioritizeAdditionalBands false
set EUtranCell[FT]DD= spectrumEmissionReqMapping
mr ecells
ma ecells ENodeBFunction=1,EUtranCellFDD= ^freqBand$ ^4$
if $nr_of_mos > 0
    set ecells prioAdditionalFreqBandList 66
    set ecells mfbiFreqBandIndPrio true
fi
mr ecells
mr eutranfreq
ma eutranfreq ENodeBFunction=1,EUtraNetwork=1,EUtranFrequency= ^freqBand$ ^4$
if $nr_of_mos > 0
    set eutranfreq mfbiFreqBandIndPrio true
    set eutranfreq prioAdditionalFreqBandList 66
fi
mr eutranfreq
ma eutranfreq ENodeBFunction=1,EUtraNetwork=1,EUtranFrequency= ^freqBand$ ^2$
for $mo in eutranfreq
    get $mo ^additionalFreqBandList$ 25
    if $nr_of_mos > 0
        set $mo excludeAdditionalFreqBandList 25
    fi
done
mr eutranfreq
unset $mo
pr ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=
if $nr_of_mos > 0
    set ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction= mfbiSupport true
fi
        """]


    @staticmethod
    def wps_mocn_settings():
        return ["""
####:----------------> MOCN Deletion 07-26-2023 FA_Disable_RwR <----------------:####
## Shared LTE RAN
set SystemFunctions=1,Lm=1,FeatureState=CXC4010960$ featureState 1
## Basic Intelligent Connectivity
set SystemFunctions=1,Lm=1,FeatureState=CXC4012218$ featureState 1
set ENodeBFunction=1$  allowMocnCellLevelCommonTac true

lt all
func plmn_cleaner_fdd
  for $itr in mycellFDD
      get $itr ^EUtranCell.DDId > $mycell
      get ^EUtranCellFDD=$mycell endcAllowedPlmnList 490
      if $nr_of_mos != 0
          set ^EUtranCellFDD=$mycell endcAllowedPlmnList mcc=310,mnc=260,mnclength=3
          print 311-490_Removed
      fi
  done
endfunc

## Hardcode this to all EARFCNs >=80Mhz Add as many var names as needed
func cmp_check
  for $itr in mycellTDDFDD
      get $itr ^EUtranCell.DDId > $mycell
      lset EUtranCell.DD=$mycell,GUtranFreqRelation=.* allowedPlmnList mcc=310,mnc=260,mncLength=3
      lset EUtranCell.DD=$mycell,GUtranFreqRelation=.* connectedModeMobilityPrio -1
  done
endfunc

set1 ENodeBFunction=1,EUtranCell[FT]DD= additionalPlmnList mcc=1,mnc=1,mncLength=2;mcc=1,mnc=1,mncLength=2;mcc=1,mnc=1,mncLength=2;mcc=1,mnc=1,mncLength=2;mcc=1,mnc=1,mncLength=2
set ^EUtranCell(FDD=|TDD=T) additionalPlmnReservedList true true true true true

pr ENodeBFunction=1,PlmnInfo=2$
if $nr_of_mos > 0
   del ENodeBFunction=1,PlmnInfo=2$
fi

## Disabling RwR only from L2100, L1900 & L2500 towards NR##
lset EUtrancellFDD=[L|B|F].*,UeMeasControl=1 rwrToNRAllowed false
lset EUtrancellTDD=.*,UeMeasControl=1 rwrToNRAllowed false
lset EUtrancellFDD=[L|B|F].*,UeMeasControl=1 nrB1MeasAtEndcEnabled false
            
            
            
##Allowing Mobility only within 310 260##
mr LTEFREREL
ma LTEFREREL EUtrancell.DD=.*,EUtranFreqRelation= 
$YellowC = no
for $mo in LTEFREREL
    $L2LREL = ldn($mo)
    print $L2LREL
    get $L2LREL ^allowedPlmnList 250
    if $nr_of_mos != 0
        $YellowC = yes
    fi
    get $L2LREL ^allowedPlmnList 490
    if $nr_of_mos != 0 && $YellowC = yes
        lset $L2LREL allowedPlmnList mcc=312,mnc=250,mnclength=3
    else if $nr_of_mos != 0 && $YellowC = no
        lset $L2LREL allowedPlmnList
    fi
    $YellowC = no
done

### Restrict RWR to NR to MCC=311,MNC=490(*whitelist MCC=310,mnc=260) from AWS/PCS LTE only towards N2500####
mr mycellFDD
ma mycellFDD ^EUtranCell.DD=[L|B|F].*
mr mycellTDDFDD
ma mycellTDDFDD ^EUtranCell.DD=[L|B|F|T].*
cmp_check

### turn off ANR initiated Measurements towards N19 to avoid alarms since no ENDC towards this band
lset EUtranCell.DD=[L|B|F|T].*,GUtranFreqRelation=3.* anrMeasOn false

###Allow ENDC only for 310/260 ## To be run Only on Cells where ENDC defination exists with both 310 260 and 311 490##
get mycellFDD admin
if $nr_of_mos != 0
  plmn_cleaner_fdd
fi

####:----------------> WPS ACTIVATION <----------------:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4011711 featurestate 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011807 featurestate 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011062 featurestate 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011060 featurestate 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011811 featurestate 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011378 featurestate 1

####:- AdmissionControl -:####
set ENodeBFunction=1,AdmissionControl=1$ nrOfPaConnReservationsPerCell 20
set ENodeBFunction=1,AdmissionControl=1$ paArpOverride 6
set ENodeBFunction=1,AdmissionControl=1$ arpBasedPreEmptionState 1
set ENodeBFunction=1,AdmissionControl=1$ preemptInactTimerMin 15
set ENodeBFunction=1,AdmissionControl=1$ resourceReservationForPAState 1
set ENodeBFunction=1,AdmissionControl=1$ admNrRrcDifferentiationThr 1000
set ENodeBFunction=1,AdmissionControl=1$ dlAdmDifferentiationThr 800
set ENodeBFunction=1,AdmissionControl=1$ dlAdmOverloadThr 850
set ENodeBFunction=1,AdmissionControl=1$ ulAdmDifferentiationThr 800
set ENodeBFunction=1,AdmissionControl=1$ ulAdmOverloadThr 850

####:- EUtranCellFDD & EUtranCellTDD -:####
set ENodeBFunction=1,EUtranCell[FT]DD= lbabDecr 30
set ENodeBFunction=1,EUtranCell[FT]DD= lbabIncr 60
set ENodeBFunction=1,EUtranCell[FT]DD= lbabPeriod 60
set ENodeBFunction=1,EUtranCell[FT]DD= lbabThreshRejectRateHigh 950
set ENodeBFunction=1,EUtranCell[FT]DD= lbabThreshRejectRateLow 930
set ENodeBFunction=1,EUtranCell[FT]DD= lbabThreshTimeHigh 60
set ENodeBFunction=1,EUtranCell[FT]DD= lbabThreshTimeLow 10
set ENodeBFunction=1,EUtranCell[FT]DD= lbabMinBarringFactor 0
set ENodeBFunction=1,EUtranCell[FT]DD= acBarringInfoPresent true
set ENodeBFunction=1,EUtranCell[FT]DD= acBarringForCsfb acBarringFactor=95,acBarringForSpecialAC=false false false false false,acBarringTime=4
set ENodeBFunction=1,EUtranCell[FT]DD= acBarringForMoData acBarringFactor=95,acBarringForSpecialAC=false false false false false,acBarringTime=4
set ENodeBFunction=1,EUtranCell[FT]DD= acBarringForMoSignalling acBarringFactor=95,acBarringForSpecialAC=false false false false false,acBarringTime=4
set ENodeBFunction=1,EUtranCell[FT]DD= acBarringPresence acBarringForMoDataPresence=2,acBarringForMoSignPresence=2,acBarringForCsfbPresence=2
            """]

    @staticmethod
    def parameter_check():
        return ["""
####:----------------> Status <----------------:####
alt
scg
lst . ^0
hget SystemFunctions=1,Lm=1,FeatureState= ^description$|^licenseState$|^featureState$
hget ^FieldReplaceableUnit= productData|administrativeState|operationalState|isSharedWithExternalMe
lst FieldReplaceableUnit
lst Sector
st EUtranCellTDD|EUtranCellFDD|NRCellDU|SctpEndpoint|TermPointToMme|TermPointToAmf
        """]

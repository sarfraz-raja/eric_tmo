from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C21_21_BaseLine(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.addcell].index) == 0: return

        self.script_list += (
                self.activity_check('Pre') + self.bl_start() + self.get_lock_cells() + self.featurestate_systemconstant() +
                self.parameter_settings() + self.software_update() + self.get_unlock_cells() + self.activity_check('Post')
        )
        #     Change made
        if len(self.gnbdata) > 0 and len(self.enbdata) > 0:
            self.relative_path[-1] = 'nr_lte_' + self.relative_path[-1]
            self.script_list += self.lte_baseline()
            self.script_list += self.nr_baseline()

            # NR BaseLine

        elif len(self.enbdata) > 0:
            self.relative_path[-1] = 'lte_' + self.relative_path[-1]
            self.script_list += self.lte_baseline()


        elif len(self.gnbdata) > 0:
            self.relative_path[-1] = 'nr_' + self.relative_path[-1]
            self.script_list += (
                    self.activity_check('Pre') + self.bl_start() + self.get_lock_cells() +
                    self.featurestate_systemconstant() + self.parameter_settings() + self.software_update() +
                    self.get_unlock_cells() + self.activity_check('Post')
            )
        if len(self.script_list) > 0:
            self.script_list = self.activity_check('Pre') + self.script_list + self.activity_check('Post')

    def lte_baseline(self) -> list:
        # LTE BaseLine
        self.motype = 'Lrat'
        lines = ['', '', '',
                 '##################################################',
                 '####:------------> LTE BaseLine <------------:####',
                 '##################################################',
                 '', '', '']
        # System Constants & Feature
        if (self.enbdata.get('BBChange', True)) or (self.df_enb_cell.shape[0] == self.df_enb_cell.loc[self.df_enb_cell.addcell].shape[0]):
            if self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['TDD'])].shape[0] > 0:
                lines += self.get_sc_features_dict(sw=self.usid.client.software.swname[:9], script_type='LTE_TDD')
            if self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD'])].shape[0] > 0:
                lines += self.get_sc_features_dict(sw=self.usid.client.software.swname[:9], script_type='LTE_FDD')
        if self.df_enb_cell.loc[self.df_enb_cell.addcell & self.df_enb_cell.celltype.isin(['FDD', 'TDD'])].shape[0] > 0:
            lines += self.get_sc_features_dict(sw=self.usid.client.software.swname[:9], script_type='LTE_Logical')
            if (self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD'])]["sc"].nunique(dropna=True) > self.df_enb_cell.loc[
                        self.df_enb_cell.celltype.isin(['FDD'])]["sef"].nunique(dropna=True)) or (self.df_enb_cell.loc[
                                self.df_enb_cell.celltype.isin(['TDD'])]["sc"].nunique(dropna=True) > self.df_enb_cell.loc[
                                        self.df_enb_cell.celltype.isin(['TDD'])]["sef"].nunique(dropna=True)):
                lines += ['set SystemFunctions=1,Lm=1,FeatureState=CXC4011802$ featureState 1', '']
        # Node Parameter
        lines += [F"""
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

"""]



        # lines += (
        #         self.bl_start() + self.get_lock_cells() +
        #         self.featurestate_systemconstant() + self.parameter_settings() + self.software_update() +
        #         self.get_unlock_cells() + self.activity_check('Post')
        # )
        return lines

    def nr_baseline(self) -> list:
        self.motype = 'GNBDU'
        lines = ['', '', '',
                 '#################################################',
                 '####:------------> NR BaseLine <------------:####',
                 '#################################################',
                 '', '', '']
        lines += (
                self.activity_check('Pre') + self.bl_start() + self.get_lock_cells() +
                self.featurestate_systemconstant() + self.parameter_settings() + self.software_update() +
                self.get_unlock_cells() + self.activity_check('Post')
        )
        return lines

    def bl_start(self):
        lines = [F"""
####:----------------> Logic <----------------:####
pv $momversion
if $momversion ~ ERBS
    print ERROR: Wrong File selected for This Site !!!
    l-
    return
fi

pv $mibprefix
$excalibur = 0
if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("excalibur")])}
   $excalibur = 1
fi
$air_64_b41_flag = ''
$BBType = 
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
    $air_64_b41_flag = AIR6488B41
fi

$lte_tdd_flag = 0
$lte_fdd_flag = 0
$nr_fdd_flag = 0
$nr_fdd_flag = 0
$n41_flag = 0
$n77_flag = 0
$n2_flag = 0
$n4_flag = 0
$fdd_flag = 0
$tdd_flag = 0
$iot_flag = 0
pr GNBDUFunction=1,NRCellDU=A
if $nr_of_mos > 0
    $n41_flag = 1
    $nr_tdd_flag = 1
fi
pr GNBDUFunction=1,NRCellDU=[KJI].*
if $nr_of_mos > 0
    $nr_fdd_flag = 1
fi
pr ENodeBFunction=1,EUtranCellFDD=
if $nr_of_mos > 0
    $lte_fdd_flag = 1
fi
pr ENodeBFunction=1,EUtranCellTDD=
if $nr_of_mos > 0
    $lte_tdd_flag = 1
fi

func getsectorval
    $var6 = $6
endfunc

"""]
        return lines

    def get_sc_features_dict(self, sw='', script_type=''):
        lte_dict = {
            'Logical': ["""
####:----------------------> Logical FeatureState <----------------------:####
#### CPRI Compression for BB6648
get SystemFunctions=1,Lm=1,FeatureState=CXC4012051$ ^licenseState$ ^1
if $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4012051$ featureState 1
fi

#### if non MSMM false, if MSMM on any sector true
get ^FieldReplaceableUnit= isSharedWithExternalMe true
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011018$ featureState 1
fi

#### No of Cells
st ENodeBFunction=1,EUtranCell[FT]DD=
if $nr_of_mos > 3
   ## 6 Cell Support
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011317$ featureState 1
else if $nr_of_mos > 6
   ## 7-12 Cell Support
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011317$ featureState 1
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011356$ featureState 1
else if $nr_of_mos > 12
   ## Support for 13-18 cells in single eNodeB
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011317$ featureState 1
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011356$ featureState 1
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011917$ featureState 1
fi

#### Optimized Release Control Activation
get SystemFunctions=1,Lm=1,FeatureState=CXC4012485$ ^licenseState$ ^1
if $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4012485$ featureState 1
else
   l echo "ERROR: ----Optimized RRC Connection Release Control (CXC4012485) is unavailable----"
fi

#### SUPPLEMENTARY DL ONLY CELL Activation
get ^EUtranCell[FT]DD= ^isDlOnly$ ^true
if $nr_of_mos > 0
   set SystemFunctions=1,Lm=1,FeatureState=CXC4011567$ featureState 1
fi

pr SystemFunctions=1,Lm=1,FeatureState=CXC4012052$
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012052$ featureState 1
fi

#### FeatureState for NbIotCell
pr ENodeBFunction=1,NbIotCell=
if $nr_of_mos > 0
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012081$ featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012079$ featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012508$ featureState 1
fi

#### FeatureState for Category M Access & Category M Connected Mode Mobility
get ENodeBFunction=1,EUtranCellFDD= catm1SupportEnabled true
if $nr_of_mos > 0
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012082$ featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012187$ featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012319$ featureState 1
    lset SystemFunctions=1,Lm=1,FeatureState=CXC4012359$ featureState 1
fi

#### Quad Antenna
set SystemFunctions=1,Lm=1,FeatureState=CXC4010609$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011427$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011667$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011056$ featureState 1     

"""],
            'ALL': ["""
set SystemFunctions=1,Lm=1,FeatureState=CXC4011823$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010319$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010320$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010609$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010613$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010616$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010618$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010620$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010717$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010723$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010770$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010856$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010912$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010949$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010956$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010959$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010960$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010961$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010962$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010963$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010964$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010967$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010974$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010990$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011011$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011033$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011034$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011050$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011055$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011056$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011059$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011060$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011061$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011062$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011064$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011067$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011069$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011074$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011075$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011157$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011163$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011183$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011245$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011251$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011252$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011255$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011317$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011319$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011327$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011345$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011356$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011366$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011370$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011373$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011376$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011378$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011427$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011443$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011444$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011476$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011477$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011479$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011482$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011485$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011515$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011554$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011559$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011666$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011667$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011711$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011714$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011807$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011811$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011813$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011815$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011820$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011823$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011838$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011918$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011937$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011938$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011939$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011946$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011969$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011980$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011999$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4012003$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012018$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012036$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012070$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012079$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012097$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012259$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012260$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012271$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012324$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012371$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012381$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012385$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012485$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012504$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012563$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4040008$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012578$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012637$ featureState 1
                    """],

            'FDD': ["""
####:---> LTE FDD Features <---:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4012344 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011929 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012081$ featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4011996$ featureState 0
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012157$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4010841$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4010973$ featureState 0
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012257$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4012218$ featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4011973$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011253$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011914$ featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4040009$ featureState 0

//set SystemFunctions=1,Lm=1,FeatureState=CXC4012034$ featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012015$ featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4011710$ featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4010955$ featureState 0
//set SystemFunctions=1,Lm=1,FeatureState=CXC4010980$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011967$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011422$ featureState 1

scw 83:0,869:0,2095:0,2123:0,145:1,2959:0,4467:0,L5319:1
#### CATM HY58469
get SystemFunctions=1,Lm=1,FeatureState=CXC4012359$ featureState$ ^1
if $nr_of_mos > 0
   scw L4911:1
fi
pv $mibprefix
if $mibprefix ~ Syosset
   scw 1449:7
else
   scw 1449:4
fi
"""],

            'TDD': ["""
####:---> Features for L41 (L2500 - TDD, AAS)  <---:####
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012344$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011929$ featureState 0
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012081$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011996$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012157$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010841$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4010973$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012257$ featureState 1
//set SystemFunctions=1,Lm=1,FeatureState=CXC4012218$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011973$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4011253$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4011914$ featureState 0
set SystemFunctions=1,Lm=1,FeatureState=CXC4040009$ featureState 1

set SystemFunctions=1,Lm=1,FeatureState=CXC4040018$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012356$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012199$ featureState 1

####:---> NO SC defined on 23Q2 on L41 TDD Cells <---:####
                    """],
            'TMO_25_Q2': {
                'ALL': [""""""],
                'FDD': [""""""],
                'TDD': [""""""],
            },
            'TMO_25_Q1': {
                'ALL': [""""""],
                'FDD': [""""""],
                'TDD': [""""""],
            },
            'TMO_24_Q4': {
                'ALL': [""""""],
                'FDD': [""""""],
                'TDD': [""""""],
            },
        }
        nr_dict = {
            'ALL': ["""
####:---> NR Features <---:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4011823$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012379$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012375$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012273$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4040008$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012325$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012492$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012475$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012479$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012477$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012478$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012558$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012592$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012591$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012637$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012531$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012534$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012538$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012373$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012549$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012548$ featureState 1
#### 10GE Port Capability
pr SystemFunctions=1,Lm=1,FeatureState=CXC4011838$
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4011838$ featureState 1
fi
#### CPRI Compression
pr SystemFunctions=1,Lm=1,FeatureState=CXC4012051$
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012051$ featureState 1
fi
#### CPRI Compression
#### NR Enhanced Slicing Observability
#### NR QoS-Aware Uplink Throughput Observability
set SystemFunctions=1,Lm=1,FeatureState=CXC4012731$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012728$ featureState 1

#### 24Q4 SW Update
set SystemFunctions=1,Lm=1,FeatureState=CXC4012661$ featureState 1
####Update for G3 Nodes Only
pr SystemFunctions=1,Lm=1,FeatureState=CXC4012763$
if $nr_of_mos > 0
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012763$ featureState 1
fi

                    """],
            'FDD': ["""
####:---> N71 (N600) and/or  N2 (N1900)<---:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4012424$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012324$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012800$ featureState 1

####:-------------------> N71 (N600) and/or N2 (N1900) <-------------------:####
scw RC554:200,RC555:480,RP1672:3,RP2624:3,RP2625:1

//#v3 - 24.Q4 TMO inclusion of SC RP1334 for N71 nodes (PDSCH ACK/NACK Aware PDCCH Link Adaptation )
pr GNBDUFunction=1,NRCellDU=K
if $nr_of_mos > 0
 scw RP1334:2
fi

                    """],
            'TDD': ["""
####:-------------------> N41 (N2500) <-------------------:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4012272$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012330$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012347$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012354$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012406$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012570$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012589$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012590$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012510$ featureState 1

scw RP2624:3,RP2625:1,RP2572:0,RP1988:7,RP1810:2,RP146:4,RP1459:4,RP1545:4,RC554:200,RC555:480
set Lm=1,FeatureState=CXC4012589$ featureState 1
set NRCellDU pdcchLaBfGainFraction 75
get Lm=1,FeatureState=CXC4012510$ ^featureState$ ^1
if $nr_of_mos > 0
    scw RP970:30,RP1022:0
fi
get BWPSetUeCfg=2$ bwpSwitchingFilterRelaxation$ false
if $nr_of_mos > 0
    scw RP1869:0
fi
get FieldReplaceableUnit productData AIR.*64...*B41
if $nr_of_mos != 0
    scw RP2508:1
    set NRCellDU=A.* dlMaxMuMimoLayers 8
fi
"""],

            'TMO_25_Q1': {
                'ALL': ["""
set SystemFunctions=1,Lm=1,FeatureState=CXC4012650$ featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012710$ featureState 1

#####  PP 166 disable for retail store Picos
mr RDOT_check 
ma RDOT_check FieldReplaceableUnit productData IRU.*88..*
pr RDOT_check
if $nr_of_mos = 0
$RDOT_check1 = 0
else
$RDOT_check1 = 1
fi

print $RDOT_check1

if $RDOT_check1 = 1
scw PP166:0
fi
                """],
                'FDD': ["""
####:-------------------> N71 (N600) and/or N2 (N1900) <-------------------:####
//#v3 - 24.Q4 TMO inclusion of SC RP1334 for N71 nodes (PDSCH ACK/NACK Aware PDCCH Link Adaptation )
pr GNBDUFunction=1,NRCellDU=K
if $nr_of_mos > 0
    scw RP1334:2
fi
                """],
                'TDD': ["""
####:-------------------> N41 (N2500) <-------------------:####
set SystemFunctions=1,Lm=1,FeatureState=CXC4012596$ featureState 1

####  Activation RCDS parameters, requires baseband restart
get PowerSaving ranCompDeepSleepEnabled > $RCDS
if $RCDS = true
    scw RC960:1
fi

"""],
            },
            'TMO_24_Q4': {
                'ALL': [""""""],
                'FDD': ["""
####:-------------------> N71 (N600) and/or N2 (N1900) <-------------------:####
"""],
                'TDD': ["""
####:-------------------> N41 (N2500) <-------------------:####
scw RP2508:1
scw RP2519:2343642,RP2357:66389,RP588:405416456,RP558:51811722,RP2648:2
scd RP268
get FieldReplaceableUnit productData AIR.*64...*B41
if $nr_of_mos != 0
    set NRCellDU=A.* dlMaxMuMimoLayers 8
    scw RP2508:1
    scw RP2519:2343642,RP2357:66389,RP588:405416456,RP558:51811722,RP2648:2
    scd RP268
fi
"""],
            },
        }
        lines = []
        if script_type.startswith('LTE'):
            lines += lte_dict['ALL'] + lte_dict[script_type[-3:]] + lte_dict[sw]['ALL'] + lte_dict[sw][script_type[-3:]]
        elif script_type.startswith('NR'):
            lines += nr_dict['ALL'] + nr_dict[script_type[-3:]] + nr_dict[sw]['ALL'] + nr_dict[sw][script_type[-3:]]
        elif script_type.startswith('LTE_Logical'):
            return lte_dict['Logical']
        return [F'####:----------------> Feature & System Constant <----------------:####', 'scg'] + lines + ['scg', '']

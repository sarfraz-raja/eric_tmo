from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base
from .tmo_data import global_amos_logic
import re


class nr_09c_N41_Para(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.addcell].index) == 0: return
        if self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.startswith('A'))].shape[0] == 0: return
        if self.df_gnb_cell.loc[(self.df_gnb_cell.addcell &
                                 self.df_gnb_cell.postcell.str.startswith('A'))].shape[0] == 0: return
        self.air_6648_6649 = len([True for _ in self.df_gnb_cell.frutypecix if
                                  len([radio for radio in _ if re.match('AIR.*64.*', radio)]) > 0]) > 0
        self.script_list += self.get_lock_cells()
        self.script_list += global_amos_logic()
        self.script_list += self.parameter_settings()
        self.script_list += self.software_update()
        self.script_list += self.get_unlock_cells()
        if len(self.script_list) > 0:
            self.script_list = self.activity_check('Pre') + self.script_list + self.activity_check('Post')

    def parameter_settings(self):
        lines = [F"""

####:----------------> Pre Check <----------------:####
pr GNBDUFunction=1,NRCellDU=A
if $nr_of_mos = 0
    print  ERROR: B41 NR cell found !!!
    l-
    return
fi

####:----------------> Configuration for N41 Cells Only <----------------:####
set GNBCUCPFunction=1,ResourcePartitions=1,ResourcePartition=FWA$ related5qiTableRef GNBCUCPFunction=1,CUCP5qiTable=2
set GNBCUUPFunction=1,ResourcePartitions=1,ResourcePartition=FWA$ related5qiTableRef GNBCUUPFunction=1,CUUP5qiTable=2
set GNBDUFunction=1,ResourcePartitions=1,ResourcePartition=FWA$ related5qiTableRef GNBDUFunction=1,DU5qiTable=2

#### GNBDUFunction=1,SrPeriodicityPoolSet=1
pr GNBDUFunction=1,SrPeriodicityPoolSet=1$
if $nr_of_mos != 0
    set1x GNBDUFunction=1,SrPeriodicityPoolSet=1$ fddTddUlDlPattern 1
    set1x GNBDUFunction=1,SrPeriodicityPoolSet=1$ noOfSrResourcesPool1 2
    set1x GNBDUFunction=1,SrPeriodicityPoolSet=1$ noOfSrResourcesPool3 53
    set1x GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool1 7
    set1x GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool2 9
    set1x GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool3 10
    set1x GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool4 11
    set1x GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool5 12
    set1x GNBDUFunction=1,SrPeriodicityPoolSet=1$ subCarrierSpacing 30
    commit
fi

set GNBCUCPFunction=1,ResourcePartitions=1,ResourcePartition=FWA related5qiTableRef GNBCUCPFunction=1,CUCP5qiTable=2
set GNBCUCPFunction=1,ResourcePartitions=1,ResourcePartition=SA related5qiTableRef GNBCUCPFunction=1,CUCP5qiTable=2
set GNBCUUPFunction=1,ResourcePartitions=1,ResourcePartition=FWA related5qiTableRef GNBCUUPFunction=1,CUUP5qiTable=2
set GNBCUUPFunction=1,ResourcePartitions=1,ResourcePartition=SA related5qiTableRef GNBCUUPFunction=1,CUUP5qiTable=2
set GNBDUFunction=1,ResourcePartitions=1,ResourcePartition=FWA related5qiTableRef GNBDUFunction=1,DU5qiTable=2
set GNBDUFunction=1,ResourcePartitions=1,ResourcePartition=SA related5qiTableRef GNBDUFunction=1,DU5qiTable=2


get FieldReplaceableUnit productData AIR.*64...*B41
if $nr_of_mos = 0
    l echo $date1 "Radio does not have AIR6449_6419B41"
else
    set GNBDUFunction=1,NRCellDU=A ssbPowerBoostMMimoSleep 3
fi

func getsectorval
    $var6 = $6
endfunc

mr nrcelldus
ma nrcelldus GNBDUFunction=1,NRCellDU=A
for $mo in nrcelldus
    get $mo nRSectorCarrierRef > $nrseccarrier
    getsectorval $nrseccarrier
    $nrseccarrier = $var6
    pr $nrseccarrier,CommonBeamforming=1$
    if $nr_of_mos > 0
        set $nrseccarrier,CommonBeamforming=1$ coverageShape 1
        set $nrseccarrier,CommonBeamforming=1$ digitalTilt 0
    fi
done
mr nrcelldus
unset $mo
unset $nrseccarrier
unset $var6

set GNBCUUPFunction=1$ dcDlPdcpInitialScgRate 100
set GNBCUCPFunction=1$ nasInactivityTime 10
set GNBCUUPFunction=1$ dcDlAggActTime 1
set GNBDUFunction=1,Rrc=1$ n310 10
set GNBDUFunction=1,DU5qiTable=1,DU5qi=1$ puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=VoNR_Dynamic
set GNBDUFunction=1,DU5qiTable=1,DU5qi=6$ schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI6
set GNBDUFunction=1,DU5qiTable=1,DU5qi=7$ schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI7
set GNBDUFunction=1,DU5qiTable=1,DU5qi=8$ schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI8
set GNBDUFunction=1,DU5qiTable=1,DU5qi=9$ schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI9
set GNBDUFunction=1,DU5qiTable=1,DU5qi=129$ schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI129

set GNBCUCPFunction=1,QciProfileEndcConfigExt=1$ initialUplinkConf 1
set GNBCUUPFunction=1,CUUP5qiTable=[12],CUUP5qi=[6789]$ estimatedE2ERTT 100
set GNBCUUPFunction=1,CUUP5qiTable=[12],CUUP5qi=128$ estimatedE2ERTT 100
set GNBCUUPFunction=1,CUUP5qiTable=[12],CUUP5qi=129$ estimatedE2ERTT 100

pr GNBCUCPFunction=1,UeGroupSelection=1$
if $nr_of_mos = 0
    cr GNBCUCPFunction=1,UeGroupSelection=1
fi
pr GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2$
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2
    ueGroupId 2
    ueGroupPriority 15
    selectionCriteria 5qi>=5
    end
else
    set GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2$ ueGroupId 2
    set GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2$ ueGroupPriority 15
    set GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2$ selectionCriteria 5qi>=5
fi

pr GNBDUFunction=1,UeCA=1$
if $nr_of_mos = 0
    cr GNBDUFunction=1,UeCA=1
fi
pr GNBDUFunction=1,UeCA=1,CaSCellHandling=1$
if $nr_of_mos = 0
    cr GNBDUFunction=1,UeCA=1,CaSCellHandling=1
fi
pr GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA
    sCellActDeactDataThres 100
    sCellActDeactDataThresHyst 20
    sCellDeactDelayTimer 80
    sCellActProhibitTimer 10
    sCellDeactProhibitTimer 250
    ueGroupList 2 1
    end
else
    set GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA$ sCellActDeactDataThresHyst 20
    set GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA$ sCellDeactDelayTimer 80
    set GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA$ sCellDeactProhibitTimer 250
fi
pr GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=NSA
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=NSA
    sCellActDeactDataThres 100
    sCellActDeactDataThresHyst 20
    sCellDeactDelayTimer 80
    sCellActProhibitTimer 10
    sCellDeactProhibitTimer 250
    ueGroupList 14
    end
else
    set GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=NSA$ sCellActDeactDataThresHyst 20
    set GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=NSA$ sCellDeactDelayTimer 80
    set GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=NSA$ sCellDeactProhibitTimer 250
fi
set GNBDUFunction=1,NRCellDU= caSCellHandlingRef GNBDUFunction=1,UeCA=1,CaSCellHandling=1



##################################################################################
### BoCS 1.5 AAS radio check
##################################################################################
func BOCS_RA1
    ### BoCS 1.5 AAS radio check
    get SysM=1,TimeM=1,DateAndTime=1 timeZone > $TimeZ
    l echo "TimeZone current setting value are" $TimeZ
    if $TimeZ =  
        l echo "No TimeZone is currently set on the node EXIT"
        set GNBCUCPFunction=1,NRCellCU epBoCSMode 0
    fi
    
    cr GNBCUCPFunction=1,EnergyPerformance=1,EPBoCS=1,EPBoosterAdvCfg=1
    cr GNBCUCPFunction=1,EnergyPerformance=1,EPBoCS=1,EPBoosterCellProfile=1
    cr GNBCUCPFunction=1,TimeSchedulingGroup=1
    cr GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1
    set TimeSchedulingGroup=1,TimeSchedulingWindow=1 epBoosterCellProfileRef EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1
    set GNBCUCPFunction=1,EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 epBoosterAdvCfgRef EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1
    set GNBCUCPFunction=1,NRCellCU=A epBoCSTimeSchedulingGroupRef GNBCUCPFunction=1,TimeSchedulingGroup=1
    
    get NRCellCU=A.*,DESManagementFunction=1 desSwitch > $DEAS
    if $DEAS = true
        set NRCellCU=A.*,DESManagementFunction=1 desSwitch false
        set GNBCUCPFunction=1,NRCellCU=A.* epBoCSMode 1
    fi
    
    set GNBCUCPFunction=1,EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 wakeupRequiredTime 600
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1  wakeupPeriodicEsDuration 120
    set EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 sleepUcfThreshBooster 1500
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 sleepFilterTimePercentage 90
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 sleepRelBoosterFilterTimePerc 90
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 sleepEvaluateTimeWindow 360
    set EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 wakeupUcfThresh 2500
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 sleepUcfWakeupThreshFactor 40
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 wakeupFilterTimePercentage 80
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 wakeupEvaluateTimeWindow 600
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 wakeupMissingSampleTime 300
    
    //set GNBCUCPFunction=1 altDepHBoCSEnabled true (in pre script) 
    #### NR Flexible DL Resource Allocation Type - AAS Radio check
    set CXC4012772 featurestate 1
    set GNBDUFunction=1,UeCC=1,ResourceAllocTypeDl=Default,ResourceAllocTypeDlUeCfg=Base prefUeResourceAllocDlTypeFr1 2
endfunc

#####  MUST BE AAS Radio 6449/6419 
mr AAS_check 
ma AAS_check FieldReplaceableUnit productData AIR.*64...*B41
pr AAS_check
if $nr_of_mos != 0
    $BOCS_RA1 = yes
else
    $BOCS_RA1 = no
fi
if $BOCS_RA1 = no
    l echo $date1 "Radio does not have AIR6449_6419B41"
    break
else
    BOCS_RA1
fi

{'' if self.air_6648_6649 else '#### '}BOCS_RA1

### BoCS 1.5  continuation 
### configure energy performance-related cells , co-sector , inter-frequency , inter-Radio
//NRRelations
// epLoadMonitoringEnabled

func Validate_intra_Inter
    get ENEPER_Cell nRCellRef ^NRCellCU=
    if $nr_of_mos > 0
        set GNBCUCPFunction=1 resourceStatusReportF1Enabled true
    fi
endfunc

func LoadMonitor_Enable
    for $x in ENEPER_Cell
        $TAR_REL = ldn($x) 
        $NRCell = $TAR_REL -s ,NRCellRelation=.*
        get $NRCell cellLocalId > $src_Cellid
        get $TAR_REL nRCellRef > $EXTCell
        get $EXTCell cellLocalId > $Ext_Cellid
        if $src_Cellid  = 301 && $Ext_Cellid = 1
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 301 && $Ext_Cellid = 21
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 302 && $Ext_Cellid = 2
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 302 && $Ext_Cellid = 22
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 303 && $Ext_Cellid = 3
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 303 && $Ext_Cellid = 23
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 304 && $Ext_Cellid = 4
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 304 && $Ext_Cellid = 24
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 311 && $Ext_Cellid = 1
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 311 && $Ext_Cellid = 21
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 312 && $Ext_Cellid = 2
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 312 && $Ext_Cellid = 22
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 313 && $Ext_Cellid = 3
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 313 && $Ext_Cellid = 23
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 314 && $Ext_Cellid = 4
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 314 && $Ext_Cellid = 24
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 321 && $Ext_Cellid = 1
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 321 && $Ext_Cellid = 21
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 322 && $Ext_Cellid = 2
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 322 && $Ext_Cellid = 22
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 323 && $Ext_Cellid = 3
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 323 && $Ext_Cellid = 23
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 324 && $Ext_Cellid = 4
            set $TAR_REL epLoadMonitoringEnabled true
        else if $src_Cellid  = 324 && $Ext_Cellid = 24
            set $TAR_REL epLoadMonitoringEnabled true
        fi
    done
endfunc

ma ENEPER_Cell
ma ENEPER_Cell NRCellCU=A.*NRCellRelation= coverageIndicator !0
for $mo in ENEPER_Cell
    $ldn = ldn($mo) 
    get $ldn  nRFreqRelationRef > $TestFreq
    if $TestFreq ~ NRFreqRelation=5
        mr ENEPER_Cell $ldn
    fi
done

pr ENEPER_Cell
if $nr_of_mos > 0
    Validate_intra_Inter
    LoadMonitor_Enable
fi

###########################################
## Auto DST for BoCS 1.5
###########################################
func Bocs_TimeWindow_Update
    $dst_var1[dayRule] = 0
    get TimeSettings daylightSavingTimeStartDate > $dst_var1
    if $dst_var1[dayRule] = 0
        ##On U.S, 2nd week of March are DST starting date and 1st week of Nov are DST Ending
        set TimeSettings daylightSavingTimeStartDate dayRule=Sun>=8,month=3,time=02:00
        set TimeSettings daylightSavingTimeEndDate dayRule=Sun>=1,month=11,time=02:00
        set TimeSettings daylightSavingTimeOffset 1:00
    fi
    ### Change the time window to 6 AM till mid night local time. Note that the value we are setting are in LocalTime with timeOffset
    get SysM=1,TimeM=1,DateAndTime=1 timeZone > $TimeZ
    
    if $TimeZ = US/Hawaii
    set TimeSettings timeOffset -10:00
    fi
    if $TimeZ = US/Pacific
    set TimeSettings timeOffset -08:00
    fi
    if $TimeZ = US/Mountain
    set TimeSettings timeOffset -07:00
    fi
    if $TimeZ = US/Central
    set TimeSettings timeOffset -06:00
    fi
    if $TimeZ = US/Eastern
    set TimeSettings timeOffset -05:00
    fi
    
    //Set TimeSchedulingWindow(UTC)
    if $TimeZ = US/Eastern
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  10:45
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 06:00
    fi
    if $TimeZ = US/Central
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  11:45
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 07:00
    fi
    if $TimeZ = US/Mountain
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  12:45
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 08:00
    fi
    if $TimeZ = US/Pacific
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  13:45
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 09:00
    fi
    if $TimeZ = US/Hawaii
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  15:45
    set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 11:00
    fi
endfunc

pr NRCellDU=[QS]
$AutoDST_qs_count = $nr_of_mos
pr NRCellDU=[A]
if $nr_of_mos != 0 && $AutoDST_qs_count = 0
    Bocs_TimeWindow_Update
    ###################################################################################################
    ## BOCS optimized parameters update (TDD NR only)
    ###################################################################################################
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 sleepEvaluateTimeWindow 360
    set EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 sleepUcfThreshBooster 3500
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 sleepUcfWakeupThreshFactor 60
fi

{'' if self.air_6648_6649 else '#### '}Bocs_TimeWindow_Update

##### 25Q2 Updates

#### NR Booster Carrier Sleep-TDD Traffic Based
mr epBoCSMode_1
ma epBoCSMode_1 NRCellCU= epBoCSMode 1
if $nr_of_mos != 0
    set epBoCSMode_1 epBoCSMode 2
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 wakeupPeriodicEsDuration 0
    set EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 sleepUcfThreshBooster 2500
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 sleepEvaluateTimeWindow 600
fi

#### NR Capacity Boost MB - formerly known as Reciprocity Enhancement (2x SRS capacity)*
func NRCapConfiguration
    set NRCellDU=[AQS] srsHoppingBandwidth 0
    hget nrcelldu=[AQS] advancedDlSuMimoEnabled|srsHoppingBandwidth|tddSpecialSlotPattern|tddUlDlPattern true 0 !2 !2
    mr NRCellDUVerification_PreCheck1
    ma NRCellDUVerification_PreCheck1 hget_group
    set FeatureState=CXC4012790 featureState 1
    set1 NRCellDUVerification_PreCheck1 srsCapacityBoostEnabled true
endfunc

pr upgradepackage=.*/2
if $nr_of_mos != 0
    $NRCapBoost_Gen3 = Yes
fi
get FieldReplaceableUnit productData AIR.*64...*B??.*
if $nr_of_mos != 0
    $NRCapBoost_AIR = Yes
fi
pr NRCellDU=[AQS]
$number_of_AQS = $nr_of_mos
if $number_of_AQS < 7
    $NRCapBoost_CellCount = Yes
fi
get FeatureState=CXC4012510 featureState$ > $NRCapBoost_PreLicense1
if $NRCapBoost_Gen3 = Yes && $NRCapBoost_AIR = Yes && $NRCapBoost_CellCount = Yes && $NRCapBoost_PreLicense1 ~ 1
    $PreCheck1 = 1
fi
if $PreCheck1 = 1
    NRCapConfiguration
fi

#### NR Booster Carrier Sleep-TDD Traffic Based
mr epBoCSMode_1
ma epBoCSMode_1 NRCellCU= epBoCSMode 1
if $nr_of_mos != 0
    set epBoCSMode_1 epBoCSMode 2
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 wakeupPeriodicEsDuration 0
    set EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 sleepUcfThreshBooster 2500
    set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 sleepEvaluateTimeWindow 600
fi

#### NR Capacity Boost MB - formerly known as Reciprocity Enhancement (2x SRS capacity)*
func NRCapConfiguration
    set NRCellDU=[AQS] srsHoppingBandwidth 0
    hget nrcelldu=[AQS] advancedDlSuMimoEnabled|srsHoppingBandwidth|tddSpecialSlotPattern|tddUlDlPattern true 0 !2 !2
    mr NRCellDUVerification_PreCheck1
    ma NRCellDUVerification_PreCheck1 hget_group
    set FeatureState=CXC4012790 featureState 1
    set1 NRCellDUVerification_PreCheck1 srsCapacityBoostEnabled true
endfunc
pr upgradepackage=.*/2
if $nr_of_mos != 0
    $NRCapBoost_Gen3 = Yes
fi
get FieldReplaceableUnit productData AIR.*64...*B??.*
if $nr_of_mos != 0
    $NRCapBoost_AIR = Yes
fi
pr NRCellDU=[AQS]
$number_of_AQS = $nr_of_mos
if $number_of_AQS < 7
    $NRCapBoost_CellCount = Yes
fi
get FeatureState=CXC4012510 featureState$ > $NRCapBoost_PreLicense1
if $NRCapBoost_Gen3 = Yes && $NRCapBoost_AIR = Yes && $NRCapBoost_CellCount = Yes && $NRCapBoost_PreLicense1 ~ 1
    NRCapConfiguration
fi

//24.Q4-v2 SRS Port Validation feature activation
get FieldReplaceableUnit productData AIR.*64...*B41
if $nr_of_mos != 0
    scw RP2508:1
fi
{'' if self.air_6648_6649 else '#### '}scw RP2508:1

set FmAlarmType=Radio.*Alert.* isNotified 0

//25.Q1-v3 - CB MU MIMO prototype enhancement feature into the 24.Q2 Post upgrade scripts
get FieldReplaceableUnit productData AIR.*64...*B41
if $nr_of_mos != 0
set CXC4012406  featurestate 1
set NRCellDU=A.* dlMaxMuMimoLayers 8
fi

###################################
## Energy-optimized Slot Allocation
###################################
set FeatureState=CXC4012795 featureState 1
set GNBDUFunction=1,RadioBearerTable=1,SignalingRadioBearer=1 rlcAckPduDelayMode 0
set GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default,DrbRlcUeCfg=Base rlcAckPduDelayMode 3

####################
## Priority Paging
####################
set SystemFunctions=1,Lm=1,FeatureState=CXC4012781 featureState 1
set GNBDUFunction=1,AdmissionControl=1 pagingPrioThreshold 6
set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users selectionCriteria rrcEstResCause == emergency || arp==6 || pagingPrio == 6
set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=WPS_Users selectionCriteria 5qi==128 || rrcEstResCause==mps-PriorityAccess || qci==128 || arp<6 || pagingPrio<6

##########################
## MPS priority indication
##########################
set SystemFunctions=1,Lm=1,FeatureState=CXC4012782 featureState 1
cr GNBCUCPFunction=1,PriorityService=1
set GNBCUCPFunction=1,PriorityService=1 mpsPriorityForRwr true
set GNBCUCPFunction=1,PriorityService=1 arp5qiPairList arp=0,profile5QI=128;arp=6,profile5QI=1

####################
## DL L4S 
####################
set SystemFunctions=1,Lm=1,FeatureState=CXC4012710 featureState 1
cr GNBCUUPFunction=1,UeCC=1,L4sCfg=1
set GNBCUUPFunction=1,UeCC=1,L4sCfg=1 dlL4sHighThresh 40
set GNBCUUPFunction=1,UeCC=1,L4sCfg=1 dlL4sLowThresh 20
set GNBCUUPFunction=1,UeCC=1,L4sCfg=1  dlL4sMode 1
cr GNBCUUPFunction=1,UeCC=1,Drb=5QI6_L4S
lt Drb
set GNBCUUPFunction=1,UeCC=1,Drb=5QI6_L4S,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_other
set GNBCUUPFunction=1,UeCC=1,Drb=5QI6_L4S,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set GNBCUUPFunction=1,UeCC=1,Drb=5QI6_L4S,DrbUeCfg=Base l4sCfgRef GNBCUUPFunction=1,UeCC=1,L4sCfg=1
set GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=5QI6_L4S
set GNBCUUPFunction=1,CUUP5qiTable=2,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=5QI6_L4S

###############################################
## UL L4S
###############################################
set SystemFunctions=1,Lm=1,FeatureState=CXC4012749 featureState 1
cr GNBDUFunction=1,UeCC=1,L4sCfg=1
set GNBDUFunction=1,UeCC=1,L4sCfg=1 ulL4sHighThresh 40
set GNBDUFunction=1,UeCC=1,L4sCfg=1 ulL4slowThresh 20
set GNBDUFunction=1,UeCC=1,L4sCfg=1 ulL4sMode 1     
set DU5qiTable=1,DU5qi=6 l4sCfgRef GNBDUFunction=1,UeCC=1,L4sCfg=1
set DU5qiTable=2,DU5qi=6 l4sCfgRef GNBDUFunction=1,UeCC=1,L4sCfg=1

####  Activation RCDS parameters, requires baseband restart
get PowerSaving ranCompDeepSleepEnabled > $RCDS
if $RCDS = true
scw RC960:1
fi

## Uplink Configured Grant 
set CXC4012596 FeatureState 1

## Activate NR Service-Adaptive Prescheduling feature
##set SystemFunctions=1,Lm=1,FeatureState=CXC4012547 featureState 1
## Create UE Grouping for SD_6001

get GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=SD_6001
pr GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=SD_6001
if $nr_of_mos = 0
crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=SD_6001
selectionCriteria snssai==0x01001771
ueGroupId 6
ueGroupPriority 98
end
fi

set GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=SD_6001 ueGroupPriority 98

## Create UeBbProfile for SD_6001
ldc GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default
pr UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=SD_6001
if $nr_of_mos = 0
crn GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=SD_6001
ueGroupList 6
end
fi
set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=SD_6001 ueGroupList 6

ldc GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default
pr GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR
if $nr_of_mos = 0
crn GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR
ueGroupList 1
end
fi
set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR ueGroupList 1
set NRCellDU=* ueBbProfileRef GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default

## Create Configure Grant for SD_6001
pr GNBDUFunction=1,UeCC=1,ConfiguredGrant=1,ConfiguredGrantUeCfg=SD_6001
if $nr_of_mos = 0
crn GNBDUFunction=1,UeCC=1,ConfiguredGrant=1,ConfiguredGrantUeCfg=SD_6001
configuredGrantMode 1
configuredGrantDataSize 0
configuredGrantPeriodicity 10
userLabel UL_grant_SD_6001
end
fi

set GNBDUFunction=1,UeCC=1,ConfiguredGrant=1,ConfiguredGrantUeCfg=SD_6001 configuredGrantMode 1
//set GNBDUFunction=1,UeCC=1,ConfiguredGrant=1,ConfiguredGrantUeCfg=SD_6001 configuredGrantDataSize 0
//set GNBDUFunction=1,UeCC=1,ConfiguredGrant=1,ConfiguredGrantUeCfg=SD_6001 configuredGrantPeriodicity 10
set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=SD_6001 configuredGrantUeCfgRef GNBDUFunction=1,UeCC=1,ConfiguredGrant=1,ConfiguredGrantUeCfg=SD_6001

//set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR configuredGrantUeCfgRef GNBDUFunction=1,UeCC=1,ConfiguredGrant=1,ConfiguredGrantUeCfg=VoNR

## Create Pre Scheduling for SD_6001
pr GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=SD_6001
if $nr_of_mos = 0
crn GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=SD_6001
preschedulingUeMode 0
end
fi
set GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=SD_6001 preschedulingUeMode 0
set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=SD_6001 preschedulingUeCfgRef GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=SD_6001

## Adjust - FOA Testing Value Only - 
set UeGroupSelection=1,UeGroupSelectionProfile=SD_6001 ueGroupPriority 98

## Configure DRX profile
pr GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=SD_6001
if $nr_of_mos = 0
crn GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=SD_6001
drxEnabled false
ueGroupList 6
end
fi

set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=SD_6001 ueGroupList 6
set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=SD_6001 drxEnabled false

## Remove UE group 6 from NRCA profile
set GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=VoNR ueGroupList 1


"""]

        return lines

    def software_update(self):
        lines = []
        # TMO_25_Q4
        if self.usid.client.software.swname[:9] > 'TMO_25_Q3':
            lines += [F"""
####:----------------> Parameter Setting for 25Q4 SW <----------------:####
################ (BSW) UL SU MIMO / MU-MIMO upto 4L ################
func UL_SU_MIMO_Config
	scw RP904:2
	scw RP3290:0
endfunc

mr ULSU_4L_LayerCheck
ma ULSU_4L_LayerCheck GNBDUFunction=1,NRCellDU=[A] ulMaxMuMimoLayers 4|6|8
pr ULSU_4L_LayerCheck
if $nr_of_mos != 0
	$ULSU_4L_LayerCheck = 1
else
	$ULSU_4L_LayerCheck = 0
fi

$ULSU_4L_RadioCheck = 0
get FieldReplaceableUnit productData AIR.*64...*B41
if $nr_of_mos != 0
	$ULSU_4L_RadioCheck = 1
fi

$UL_SU_MIMO_CXC = 0
$UL_MU_MIMO_CXC = 0
get FeatureState=CXC4012493 featureState$ > $UL_SU_MIMO_CXC
get FeatureState=CXC4012330 featureState$ > $UL_MU_MIMO_CXC
if $GenCheck = Gen3or4 && $A_Cell_Present = 1 && $QSH_Cell_Present = 0 && $UL_SU_MIMO_CXC ~ 1 && $UL_MU_MIMO_CXC ~ 1 && $ULSU_4L_RadioCheck = 1 && $ULSU_4L_LayerCheck = 1
	UL_SU_MIMO_Config
fi

###################################################################################################################################################
###################################################################################################################################################

"""]

        return lines

    @staticmethod
    def activity_check(activity):
        return [F"""
####:----------------> {activity} Check <----------------:####
alt
scg
hget SystemFunctions=1,Lm=1,FeatureState= ^description$|^licenseState$|^featureState$
st EUtranCellTDD|EUtranCellFDD|NRCellDU|SctpEndpoint|TermPointToMme|TermPointToAmf
hget GNBDUFunction=1,NRCellDU=.* nrTAC|secondaryCellOnly|cellBarred|cellReservedForOperator|cellReservedForOperator|state
hget ^NRCellDU= ssbFrequencyAutoSelected|ssbFrequency|subCarrierSpacing|ssbsubcarrierspacing|ssbFrequency|'
ssbPeriodicity|ssbDurationAutoSelected|ssbDuration
hget GNBCUCPFunction=1,NRCellCU= transmitSib|mcfbCellProfileRef|nRFrequencyRef
        """]

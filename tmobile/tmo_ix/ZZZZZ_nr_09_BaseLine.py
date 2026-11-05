from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base
import re


class nr_09_BaseLine(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.addcell].index) == 0: return
        self.air_6648_6649 = len([True for _ in self.df_gnb_cell.frutypecix if
                                  len([radio for radio in _ if re.match('AIR.*64.*', radio)]) > 0]) > 0
        self.script_list += self.bl_start()
        self.script_list += self.get_lock_cells()
        self.script_list += self.featurestate_systemconstant()
        self.script_list += self.parameter_settings()
        self.script_list += self.software_update()
        self.script_list += self.get_unlock_cells()
        if len(self.script_list) > 0:
            self.script_list = self.activity_check('Pre') + self.script_list + self.activity_check('Post')

    def bl_start(self):
        return [
            F"""
####:----------------> BL Supports for Carrier N71 (N600), N41 (N2500) <----------------:####
####:----------------> BL Revised on 01-27-2022 <----------------:####
####:----------------> Pre Check <----------------:####
pr GNBDUFunction=1,NRCellDU=
if $nr_of_mos = 0
    print  ERROR: No NR cell defined !!!
    l-
    return
fi
lst GNBDUFunction=1,NRCellDU=(M|N)
if $nr_of_mos > 0
    print ERROR: mmWave Node does not supporting SA !!!
    l-
    return
fi

####:----------------> Logic <----------------:####
pv $mibprefix
$BBType = None
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

$n41_flag = 0
$n71_flag = 0
$n2_flag = 0
$fdd_flag = 0
$tdd_flag = 0
pr GNBDUFunction=1,NRCellDU=A
if $nr_of_mos > 0
    $n41_flag = 1
fi
pr GNBDUFunction=1,NRCellDU=K
if $nr_of_mos > 0
    $n71_flag = 1
fi
pr GNBDUFunction=1,NRCellDU=J
if $nr_of_mos > 0
    $n2_flag = 1
fi
pr ENodeBFunction=1,EUtranCellFDD=
if $nr_of_mos > 0
    $fdd_flag = 1
fi
pr ENodeBFunction=1,EUtranCellTDD=
if $nr_of_mos > 0
    $tdd_flag = 1
fi

$excalibur = 0
if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("excalibur")])}
   $excalibur = 1
fi

func getsectorval
    $var6 = $6
endfunc
        """]

    def featurestate_systemconstant(self):
        # System Constant & Feature
        lines = []
        if self.df_gnb_cell.shape[0] > 0 and self.df_gnb_cell.shape[0] != self.df_gnb_cell.loc[self.df_gnb_cell.addcell].shape[0]: return lines
        if 0 < self.df_gnb_cell.loc[self.df_gnb_cell.addcell].shape[0] == self.df_gnb_cell.shape[0]:
            if self.df_gnb_cell.loc[self.df_gnb_cell.postcell.str.startswith(('K', 'J', 'I'))].shape[0] > 0:
                lines += self.get_sc_features_dict(sw=self.usid.client.software.swname[:9], script_type='NR_FDD')
            if self.df_gnb_cell.loc[self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.startswith('A')].shape[0] > 0:
                lines += self.get_sc_features_dict(sw=self.usid.client.software.swname[:9], script_type='NR_TDD')
        return lines

    def parameter_settings(self):
        lines = ['####:----------------> Parameter Setting <----------------:####']
        if 0 < self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.startswith('A'))].shape[0] == \
                self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.startswith('A'))].shape[0]:
            lines += [
                F'####:----------------> Configuration for N41 Cells Only <----------------:####',
                F'set GNBCUCPFunction=1,ResourcePartitions=1,ResourcePartition=FWA$ related5qiTableRef GNBCUCPFunction=1,CUCP5qiTable=2',
                F'set GNBCUUPFunction=1,ResourcePartitions=1,ResourcePartition=FWA$ related5qiTableRef GNBCUUPFunction=1,CUUP5qiTable=2',
                F'set GNBDUFunction=1,ResourcePartitions=1,ResourcePartition=FWA$ related5qiTableRef GNBDUFunction=1,DU5qiTable=2',
                F'',
                F'#### GNBDUFunction=1,SrPeriodicityPoolSet=1',
                F'pr GNBDUFunction=1,SrPeriodicityPoolSet=1$',
                F'if $nr_of_mos != 0',
                F'set GNBDUFunction=1,SrPeriodicityPoolSet=1$ fddTddUlDlPattern 1',
                F'set GNBDUFunction=1,SrPeriodicityPoolSet=1$ noOfSrResourcesPool1 2',
                F'set GNBDUFunction=1,SrPeriodicityPoolSet=1$ noOfSrResourcesPool3 53',
                F'set GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool1 7',
                F'set GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool2 9',
                F'set GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool3 10',
                F'set GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool4 11',
                F'set GNBDUFunction=1,SrPeriodicityPoolSet=1$ srPeriodicityPool5 12',
                F'set GNBDUFunction=1,SrPeriodicityPoolSet=1$ subCarrierSpacing 30',
                F'fi',
                F'',
                F'set GNBCUCPFunction=1,ResourcePartitions=1,ResourcePartition=FWA related5qiTableRef GNBCUCPFunction=1,CUCP5qiTable=2',
                F'set GNBCUCPFunction=1,ResourcePartitions=1,ResourcePartition=SA related5qiTableRef GNBCUCPFunction=1,CUCP5qiTable=2',
                F'set GNBCUUPFunction=1,ResourcePartitions=1,ResourcePartition=FWA related5qiTableRef GNBCUUPFunction=1,CUUP5qiTable=2',
                F'set GNBCUUPFunction=1,ResourcePartitions=1,ResourcePartition=SA related5qiTableRef GNBCUUPFunction=1,CUUP5qiTable=2',
                F'set GNBDUFunction=1,ResourcePartitions=1,ResourcePartition=FWA related5qiTableRef GNBDUFunction=1,DU5qiTable=2',
                F'set GNBDUFunction=1,ResourcePartitions=1,ResourcePartition=SA related5qiTableRef GNBDUFunction=1,DU5qiTable=2',
                F'',
                F'',

            ]
        lines.extend(self.get_vswr_script())
        if 0 < self.df_gnb_cell.loc[self.df_gnb_cell.addcell].shape[0] == self.df_gnb_cell.shape[0]:
            lines.extend(self.get_node_certificate())

        lines.extend([F"""
#### ####:----------------> nrTAC Update <----------------:####
#### get GNBDUFunction=1,NRCellDU= nRTAC > $nrtac
#### if $nrtac < 65535
####    d2h $nrtac > $nrtac
####    $nrtac = $nrtac00 -s 0x
####    h2d $nrtac > $nrtac
####    set GNBDUFunction=1,NRCellDU= nrTAC $nrtac
####    set GNBDUFunction=1,NRCellDU=.*,AdditionalPLMNInfo=1$ nRTAC $nrtac
#### fi
#### unset $nrtac

####:----------------> Default Parameter Setting <----------------:####

#### NR FR1 DL SCell Mitigation for SRS Antenna Switching in SpCell
set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base srsImpactHandling 1
st ^nrcelldu=O
if $nr_of_mos != 0
set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base srsImpactHandling 0
fi

set BrM=1,BrmBackupManager=1,BrmBackupHousekeeping=1$ maxStoredManualBackups 20
set Fm=1$ heartbeatInterval 100
set GNBDUFunction=1,TermPointToGNBCUCP=1$ administrativeState 1

####:----> 20.Q4 EPS Fallback <----:####
mr nrcellcus
ma nrcellcus GNBCUCPFunction=1,NRCellCU=
for $mo in nrcellcus
    set $mo mcpcPSCellEnabled true
    get $mo ^nRCellCUId$ > $nrcellcuid
    pr GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=$nrcellcuid$
    if $nr_of_mos = 0
        cr GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=$nrcellcuid
        set $mo mcfbCellProfileRef GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=$nrcellcuid
    fi
done
mr nrcellcus
unset $mo
unset $nrcellcuid

ld McfbCellProfileUeCfg=Base
set GNBCUCPFunction=1,Mcfb=1$ voiceEpsFbPossible true
set GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=.*,McfbCellProfileUeCfg=Base$ epsFbAtSessionSetup 1
set GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=.*,McfbCellProfileUeCfg=Base$ epsFallbackOperation 2
set GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=.*,McfbCellProfileUeCfg=Base$ epsFallbackOperationEm 1


####:----------------> Band Parameter Setting <----------------:####
####:----------------> N71 (N600) <----------------:####
if $n71_flag = 1
    set NRCellDU=[J|I|K] nrLteCoexistence false
    ## set GNBDUFunction=1,NRCellDU=K qRxLevMin -116
    set GNBDUFunction=1,Rrc=1$ n310 20
    set GNBCUCPFunction=1,QciProfileEndcConfigExt=1$ initialUplinkConf 0
    set GNBCUCPFunction=1$ nasInactivityTime 5
    set GNBCUUPFunction=1$ dcDlAggActTime 10
    set GNBCUCPFunction=1,AnrFunction=1,AnrFunctionNR=1,AnrFunctionNRUeCfg=Base anrRsrpThreshold -114
    set GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=Base preschedulingUeMode 0
fi

####:----------------> N2 (N1900) <----------------:####
if $n2_flag = 1
    set NRCellDU=[J|I|K] nrLteCoexistence false
    ## set GNBDUFunction=1,NRCellDU=J qRxLevMin -120
    set GNBDUFunction=1,NRCellDU=J pdcchLaBfGainFraction 0
    set GNBDUFunction=1,Rrc=1$ n310 20
    set GNBCUCPFunction=1,QciProfileEndcConfigExt=1$ initialUplinkConf 0
    set GNBCUCPFunction=1$ nasInactivityTime 10
    set GNBCUUPFunction=1$ dcDlAggActTime 1
    set GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=Base preschedulingUeMode 0
fi

####:----------------> N41 (N2500) <----------------:####
func n41_ssbPowerBoostMMimoSleep
    get FieldReplaceableUnit productData AIR.*64...*B41
    if $nr_of_mos = 0
        l echo $date1 "Radio does not have AIR6449_6419B41"
    else
        set GNBDUFunction=1,NRCellDU=A ssbPowerBoostMMimoSleep 3
    fi
endfunc

func n41_settings
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
endfunc

if $n41_flag = 1
    n41_ssbPowerBoostMMimoSleep
    n41_settings
    
    set PowerSaving=1$ ranCompDeepSleepEnabled false
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
    set GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=Base preschedulingUeMode 1
fi


####:----------------> 22Q3 & 22Q4 Update <----------------:####
#### Create UeBBProfile for UEs with voice data bearer
pr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR$
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
    dlMaxBitrate -1
    dlMcsTable 1
    linkAdaptationUeMode 3
    ulMcsTable 1
    end
else
    set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR$ dlMaxBitrate -1
    set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR$ dlMcsTable 1
    set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR$ linkAdaptationUeMode 3
    set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR$ ulMcsTable 1
fi

set GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=Base$ dlHarqMode 2
pr GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR$
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR
    dlHarqMode 1
    ulHarqMode 1
    end
else
    set GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR$ dlHarqMode 1
    set GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR$ ulHarqMode 1
fi

pr GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR$
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR
    reTxBsrTimer 1280
    srGrantSize 32
    end
else
    set GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR$ reTxBsrTimer 1280
    set GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR$ srGrantSize 32
fi

pr GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default$
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default
    ueConfGroupType 1
    end
else
    set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default$ ueConfGroupType 1
fi

pr GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR$
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR
    bsrUeCfgRef GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR
    harqUeCfgRef GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR
    linkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
    ueGroupList 1
    end
else
    set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR$ bsrUeCfgRef GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR
    set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR$ harqUeCfgRef GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR
    set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR$ linkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
    set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR$ ueGroupList 1
fi

lt all
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,UlLinkAdaptation=1$ ulMaxMcsIndex 16
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR$ ulMcsTable 0
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base$ linkAdaptationUeMode 3

set GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=Base preschedulingDataSize 108

####:----------------> 22Q3 addition - NRCA Data Aware Carrier Management <----------------:####
func n41_n2_22Q4_settings
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
endfunc
if $n2_flag = 1 || $n41_flag = 1 
    n41_n2_22Q4_settings
fi

####:----------------> 23.Q2 v9 QoS_SR_handling_correction <----------------:####
pr GNBDUFunction=1,UeCC=1,SrHandling=5QI_5$
if $nr_of_mos == 0
  crn GNBDUFunction=1,UeCC=1,SrHandling=5QI_5
  ueConfGroupType 1
  end
fi
lt SrHandling
lt SrHandlingUeCfg
set GNBDUFunction=1,UeCC=1,SrHandling=5QI_5,SrHandlingUeCfg=Base$ srHandlingMode 1
set GNBDUFunction=1,UeCC=1,SrHandling=default,SrHandlingUeCfg=Base$ srHandlingMode 1
set GNBDUFunction=1,UeCC=1,SrHandling=5QI_5,SrHandlingUeCfg=Base$ conditional5qi 1
set GNBDUFunction=1,DU5qiTable=1,DU5qi=5$ srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=5QI_5
set GNBDUFunction=1,DU5qiTable=2,DU5qi=5$ srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=5QI_5

####:----------------> 23.Q3 & 23.Q4 Update <----------------:####
set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VoNR drxRetransmissionTimerUl 16
set GNBCUCPFunction=1,AnrFunction=1 promoteCellRelMobAttThresh 100
set GNBCUCPFunction=1,AnrFunction=1 demoteCellRelMobAttThresh 50

"""])
        lines.extend(["""####:----------------> Market Settings <----------------:####"""])
        return lines

    def software_update(self):
        lines = []
        lines += ["""
####:----------------> LTE Parameter Setting for 24Q2 SW <----------------:####
set GNBCUUPFunction=1,UeCC=1,UserPlaneProfile=Default,UserPlaneProfileUeCfg=Base dcDlAggCgPrio 1 
set GNBCUUPFunction=1,UeCC=1,UserPlaneProfile=Default,UserPlaneProfileUeCfg=Base dcDlAggAgeDiffPreferredCg 2 
set GNBCUUPFunction=1,UeCC=1,UserPlaneProfile=Default,UserPlaneProfileUeCfg=Base dlPdcpPreferredCg  1 
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_other                 aqmMode 1       
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_conversational_media  aqmMode 2 
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_application_signaling aqmMode 0
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_other                 tDiscardDl 280       
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_conversational_media  tDiscardDl 80 
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_application_signaling tDiscardDl 80

cr GNBCUUPFunction=1,UeCC=1,Drb=Conversational_Video
cr GNBCUUPFunction=1,UeCC=1,Drb=Real_Time_Gaming
cr GNBCUUPFunction=1,UeCC=1,Drb=Non-Conversational_Video
cr GNBCUUPFunction=1,UeCC=1,Drb=SD_2000
cr GNBCUUPFunction=1,UeCC=1,Drb=SD_3001
cr GNBCUUPFunction=1,UeCC=1,Drb=SD_3002
cr GNBCUUPFunction=1,UeCC=1,Drb=SD_6000
cr GNBCUUPFunction=1,UeCC=1,Drb=SD_6001

crn GNBCUUPFunction=1,UeCC=1,AqmCfg=Conversational_Video
aqmMode 2
tDiscardDl  130
tOooUlDelivery 150 
end

crn GNBCUUPFunction=1,UeCC=1,AqmCfg=Real_Time_Gaming
aqmMode 2
tDiscardDl  30
tOooUlDelivery 150
end

crn GNBCUUPFunction=1,UeCC=1,AqmCfg=Non-Conversational_Video
aqmMode 2
tDiscardDl  280
tOooUlDelivery 150
end

crn GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_2000
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  10
tOooUlDelivery 150 
end

crn GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_3001
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  70
tOooUlDelivery 150 
end

crn GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_6000
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  70
tOooUlDelivery 150 
end

crn GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_6001
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  70
tOooUlDelivery 150 
end

crn GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_3002
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  35
tOooUlDelivery 150 
end

lt all 
set GNBCUUPFunction=1,UeCC=1,Drb=Conversational_Video,DrbUeCfg=Base     aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=Conversational_Video
set GNBCUUPFunction=1,UeCC=1,Drb=Real_Time_Gaming,DrbUeCfg=Base		    aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=Real_Time_Gaming
set GNBCUUPFunction=1,UeCC=1,Drb=Non-Conversational_Video,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=Non-Conversational_Video
set GNBCUUPFunction=1,UeCC=1,Drb=SD_2000,DrbUeCfg=Base 					aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_2000
set GNBCUUPFunction=1,UeCC=1,Drb=SD_3001,DrbUeCfg=Base  				aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_3001
set GNBCUUPFunction=1,UeCC=1,Drb=SD_3002,DrbUeCfg=Base  				aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_3002
set GNBCUUPFunction=1,UeCC=1,Drb=SD_6000,DrbUeCfg=Base  				aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_6000
set GNBCUUPFunction=1,UeCC=1,Drb=SD_6001,DrbUeCfg=Base  				aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_6001
set GNBCUUPFunction=1,UeCC=1,Drb=Conversational_Video,DrbUeCfg=Base     dcDlCfgRef  GNBCUUPFunction=1,UeCC=1,DcDlCfg=default
set GNBCUUPFunction=1,UeCC=1,Drb=Real_Time_Gaming,DrbUeCfg=Base		 	dcDlCfgRef  GNBCUUPFunction=1,UeCC=1,DcDlCfg=default  
set GNBCUUPFunction=1,UeCC=1,Drb=Non-Conversational_Video,DrbUeCfg=Base dcDlCfgRef  GNBCUUPFunction=1,UeCC=1,DcDlCfg=default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_2000,DrbUeCfg=Base 				    dcDlCfgRef  GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_3001,DrbUeCfg=Base  				dcDlCfgRef  GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_6000,DrbUeCfg=Base  				dcDlCfgRef  GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_6001,DrbUeCfg=Base  				dcDlCfgRef  GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_3002,DrbUeCfg=Base  				dcDlCfgRef  GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default

set ,CUUP5qi=2                      			  drbRef      GNBCUUPFunction=1,UeCC=1,Drb=Conversational_Video
set ,CUUP5qi=3                      			  drbRef      GNBCUUPFunction=1,UeCC=1,Drb=Real_Time_Gaming
set ,CUUP5qi=4                      			  drbRef      GNBCUUPFunction=1,UeCC=1,Drb=Non-Conversational_Video
set CUUP5qiTable=SD_2000,CUUP5qi=6                drbRef      GNBCUUPFunction=1,UeCC=1,Drb=SD_2000
set CUUP5qiTable=SD_3001,CUUP5qi=6                drbRef      GNBCUUPFunction=1,UeCC=1,Drb=SD_3001
set CUUP5qiTable=SD_6000,CUUP5qi=6                drbRef      GNBCUUPFunction=1,UeCC=1,Drb=SD_6000
set CUUP5qiTable=SD_6001,CUUP5qi=6                drbRef      GNBCUUPFunction=1,UeCC=1,Drb=SD_6001
set CUUP5qiTable=SD_3002,CUUP5qi=6                drbRef      GNBCUUPFunction=1,UeCC=1,Drb=SD_3002

set GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default                dcDlAggAllowed    true
set GNBCUUPFunction=1                                       altDepHServAdapUPProfEnabled true 

set GNBDUFunction=1,UeCC=1,AqmCfg=Default_other                 aqmMode 1       
set GNBDUFunction=1,UeCC=1,AqmCfg=Default_conversational_media  aqmMode 2 
set GNBDUFunction=1,UeCC=1,AqmCfg=Default_application_signaling aqmMode 0
set GNBDUFunction=1,UeCC=1,AqmCfg=Default_other                 tDiscardDl 280       
set GNBDUFunction=1,UeCC=1,AqmCfg=Default_conversational_media  tDiscardDl 80 
set GNBDUFunction=1,UeCC=1,AqmCfg=Default_application_signaling tDiscardDl 80
cr GNBDUFunction=1,UeCC=1,DrbUp=Conversational_Video
cr GNBDUFunction=1,UeCC=1,DrbUp=Real_Time_Gaming
cr GNBDUFunction=1,UeCC=1,DrbUp=Non-Conversational_Video
cr GNBDUFunction=1,UeCC=1,DrbUp=SD_2000
cr GNBDUFunction=1,UeCC=1,DrbUp=SD_3001
cr GNBDUFunction=1,UeCC=1,DrbUp=SD_6000
cr GNBDUFunction=1,UeCC=1,DrbUp=SD_6001
cr GNBDUFunction=1,UeCC=1,DrbUp=SD_3002

crn GNBDUFunction=1,UeCC=1,AqmCfg=Conversational_Video
aqmMode 2
tDiscardDl  130
end

crn GNBDUFunction=1,UeCC=1,AqmCfg=Real_Time_Gaming
aqmMode 2
tDiscardDl  30
end

crn GNBDUFunction=1,UeCC=1,AqmCfg=Non-Conversational_Video
aqmMode 2
tDiscardDl  280
end

crn GNBDUFunction=1,UeCC=1,AqmCfg=SD_2000
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  10
end

crn GNBDUFunction=1,UeCC=1,AqmCfg=SD_3001
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  70 
end

crn GNBDUFunction=1,UeCC=1,AqmCfg=SD_6000
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  70 
end

crn GNBDUFunction=1,UeCC=1,AqmCfg=SD_6001
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  70 
end

crn GNBDUFunction=1,UeCC=1,AqmCfg=SD_3002
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  35 
end

lt all 
set  GNBDUFunction=1,UeCC=1,DrbUp=Conversational_Video,DrbUpUeCfg=Base		aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=Conversational_Video
set  GNBDUFunction=1,UeCC=1,DrbUp=Real_Time_Gaming,DrbUpUeCfg=Base			aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=Real_Time_Gaming
set  GNBDUFunction=1,UeCC=1,DrbUp=Non-Conversational_Video,DrbUpUeCfg=Base	aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=Non-Conversational_Video
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_2000,DrbUpUeCfg=Base					aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_2000
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_3001,DrbUpUeCfg=Base    				aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_3001
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_6000,DrbUpUeCfg=Base    				aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_6000
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_6001,DrbUpUeCfg=Base    				aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_6001
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_3002,DrbUpUeCfg=Base    				aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_3002
set ,DU5qi=2                      			  drbUpRef      GNBDUFunction=1,UeCC=1,DrbUp=Conversational_Video
set ,DU5qi=3                      			  drbUpRef      GNBDUFunction=1,UeCC=1,DrbUp=Real_Time_Gaming
set ,DU5qi=4                      			  drbUpRef      GNBDUFunction=1,UeCC=1,DrbUp=Non-Conversational_Video
set DU5qiTable=SD_2000,DU5qi=6                drbUpRef      GNBDUFunction=1,UeCC=1,DrbUp=SD_2000
set DU5qiTable=SD_3001,DU5qi=6                drbUpRef      GNBDUFunction=1,UeCC=1,DrbUp=SD_3001
set DU5qiTable=SD_6000,DU5qi=6                drbUpRef      GNBDUFunction=1,UeCC=1,DrbUp=SD_6000
set DU5qiTable=SD_6001,DU5qi=6                drbUpRef      GNBDUFunction=1,UeCC=1,DrbUp=SD_6001
set DU5qiTable=SD_3002,DU5qi=6                drbUpRef      GNBDUFunction=1,UeCC=1,DrbUp=SD_3002

set GNBDUFunction=1                                       altDepHServAdapUPProfEnabled true

del GNBCUUPFunction=1,UeCC=1,Drb=SD_PDB10
del GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_PDB10
del GNBDUFunction=1,UeCC=1,DrbUp=SD_PDB10
del GNBDUFunction=1,UeCC=1,AqmCfg=SD_PDB10

lt all
set GNBCUCPFunction=1,UeCC=1,Rrc=1,RrcUeCfg= dedicatedSib1AtHo true

################ 5Qi129 Addition ############
$SQIT_HSI = DU5qiTable=1
get GNBDUFunction=1,ResourcePartitions=1,ResourcePartition=FWA related5qiTableRef > $SQIT_HSI

if $SQIT_HSI ~ DU5qiTable=2
$TABLEID = 2
$TID = [1|2]
else
$TABLEID = 1
$TID = 1
fi

u+s
ldel DU5qiTable=$TID,DU5qi=9$
ldel CUUP5qiTable=$TID,CUUP5qi=9$
ldel CUCP5qiTable=$TID,CUCP5qi=9$
u-

l sed -i 's/5qi=9/5qi=129/g' $undocommandfile
l sed -i 's/profile5qi 9/profile5qi 129/g' $undocommandfile
l sed -i 's/schedulingProfileRef.*/schedulingProfileRef /g' $undocommandfile 
run $undocommandfile

if $TABLEID = 2 
crn GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI129
dlCaSchedulingMode 0
essResourceAllocationMode 0
relativePriority 1
relativePriorityMode 0
userLabel NSA_5QI129
end
set DU5qiTable=1,DU5qi=129 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI129
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI129
if $nr_of_mos = 0
crn GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI129
dlCaSchedulingMode 0
essResourceAllocationMode 0
relativePriority 2
relativePriorityMode 0
userLabel 5QI129
end
else 
set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI129 relativePriority 2
fi

set DU5qiTable=$TABLEID,DU5qi=129 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI129

###### Update Relative Priority SA/NSA/Slicing Scheduling Profiles########
set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI6 relativepriority 128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI7 relativepriority 32
set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI8 relativepriority 16
set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI9 relativepriority 8

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI[6789]
if $nr_of_mos > 0
    set GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI6 relativepriority 64
    set GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI7 relativepriority 16
    set GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI8 relativepriority 8
    set GNBDUFunction=1,UeCC=1,SchedulingProfile=NSA_5QI9 relativepriority 4
fi

set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_3000_SST_1_5QI6 relativePriority  256
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_3001_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_3001_SST_1_5QI6 relativePriorityMode 2
set DU5qiTable=SD_3001,DU5qi=6 packetDelayBudget 70
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_3002_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_3002_SST_1_5QI6 relativePriorityMode 2
set DU5qiTable=SD_3002,DU5qi=6 packetDelayBudget 35
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_6000_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_6000_SST_1_5QI6 relativePriorityMode 2
set DU5qiTable=SD_6000,DU5qi=6 packetDelayBudget 70
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_6001_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_6001_SST_1_5QI6 relativePriorityMode 2
set DU5qiTable=SD_6001,DU5qi=6 packetDelayBudget 70
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_2000_SST_1_5QI6 relativePriority  256
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_4000_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_7000_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_8000_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_8001_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6 relativePriority  128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_10000_SST_1_5QI6 relativePriority  128

#### Script for activating the feature "RCPD_Resource_Starvation"#
lt all
#### Check Dl/UlResourceBasedPriority Mo if not available then create it

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,DlResourceBasedPriority=1
if $nr_of_mos = 0
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,DlResourceBasedPriority=1
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,DlResourceBasedPriority=1
if $nr_of_mos = 0
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,DlResourceBasedPriority=1
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,DlResourceBasedPriority=1
if $nr_of_mos = 0
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,DlResourceBasedPriority=1
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,UlResourceBasedPriority=1
if $nr_of_mos = 0
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,UlResourceBasedPriority=1
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,UlResourceBasedPriority=1
if $nr_of_mos = 0
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,UlResourceBasedPriority=1
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,UlResourceBasedPriority=1
if $nr_of_mos = 0
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,UlResourceBasedPriority=1
fi

### Set dlResourceLimitMode to "LIMITED" or "LIMITED_TO_CELL_LIMIT" based upon requirement and dl/ulDrbPriorityLimit to 15 (for slice 9000 and 9001) and 10 (for slice 9002)

set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,DlResourceBasedPriority=1 dlResourceLimitMode LIMITED_TO_CELL_LIMIT
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,UlResourceBasedPriority=1 ulResourceLimitMode LIMITED_TO_CELL_LIMIT
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,DlResourceBasedPriority=1 dlResourceLimitMode LIMITED_TO_CELL_LIMIT
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,UlResourceBasedPriority=1 ulResourceLimitMode LIMITED_TO_CELL_LIMIT
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,DlResourceBasedPriority=1 dlResourceLimitMode LIMITED_TO_CELL_LIMIT
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,UlResourceBasedPriority=1 ulResourceLimitMode LIMITED_TO_CELL_LIMIT
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,DlResourceBasedPriority=1 dlDrbPriorityLimit 15
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,UlResourceBasedPriority=1 ulDrbPriorityLimit 15
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,DlResourceBasedPriority=1 dlDrbPriorityLimit 15
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,UlResourceBasedPriority=1 ulDrbPriorityLimit 15
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,DlResourceBasedPriority=1 dlDrbPriorityLimit 10 
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,UlResourceBasedPriority=1 ulDrbPriorityLimit 10

####Check and create CellPriorityShift MO and set cellDl/UlDrbPriorityLimitBase to 15

pr GNBDUFunction=1,DUQos=1,QosPriorityShift=1
if $nr_of_mos = 0
cr GNBDUFunction=1,DUQos=1,QosPriorityShift=1
fi

pr GNBDUFunction=1,DUQos=1,QosPriorityShift=1,CellPriorityShift=1 
if $nr_of_mos = 0
cr GNBDUFunction=1,DUQos=1,QosPriorityShift=1,CellPriorityShift=1 
fi

set NRCellDU= cellPriorityShiftRef GNBDUFunction=1,DUQos=1,QosPriorityShift=1,CellPriorityShift=1

set GNBDUFunction=1,DUQos=1,QosPriorityShift=1,CellPriorityShift=1 cellDlDrbPriorityLimitBase 75
set GNBDUFunction=1,DUQos=1,QosPriorityShift=1,CellPriorityShift=1 cellUlDrbPriorityLimitBase 75

### set ulDemotedRelativePriority to true

set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,UlRateBasedPriority=1 ulDemotedRelativePriority true
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,UlRateBasedPriority=1 ulDemotedRelativePriority true
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,UlRateBasedPriority=1 ulDemotedRelativePriority true

##### NR Enhanced Slicing Observability (CXC4012731)###########
###NR QoS-Aware Uplink Throughput Observability (CXC4012728) #####
lt all
set CXC4012731 featurestate 1
set CXC4012728 featurestate 1

#####  Legacy HSI/G5 SD_1001 Addition #########
set1 NRCellDU sNSSAIList sd=16777215,sst=1; sd=1000,sst=1; sd=1001,sst=1; sd=2000,sst=1; sd=3000,sst=1; sd=3001,sst=1; sd=3002,sst=1; sd=4000,sst=1; sd=5000,sst=1; sd=5001,sst=1;sd=5002,sst=1; sd=6000,sst=1; sd=6001,sst=1; sd=7000,sst=1; sd=8000,sst=1; sd=8001,sst=1; sd=9000,sst=1; sd=9001,sst=1; sd=9002,sst=1; sd=10000,sst=1
set1 GNBCUUPFunction=1 sNSSAIList sd=16777215,sst=1; sd=1000,sst=1; sd=1001,sst=1; sd=2000,sst=1; sd=3000,sst=1; sd=3001,sst=1; sd=3002,sst=1; sd=4000,sst=1; sd=5000,sst=1; sd=5001,sst=1;sd=5002,sst=1; sd=6000,sst=1; sd=6001,sst=1; sd=7000,sst=1; sd=8000,sst=1; sd=8001,sst=1; sd=9000,sst=1; sd=9001,sst=1; sd=9002,sst=1; sd=10000,sst=1
lt all

#### Set SD_1001 in FWA RRP Profile #############
set ,ResourcePartition=FWA,ResourcePartitionMember=1 sNSSAIList sd=1000,sst=1; sd=1001,sst=1

######  Starvation cleanup missed in PUS #
### set ulDemotedRelativePriority to true
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,UlRateBasedPriority=1 ulDemotedRelativePriority true
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,UlRateBasedPriority=1 ulDemotedRelativePriority true
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,UlRateBasedPriority=1 ulDemotedRelativePriority true
#### set bit rate as per the slice requirement
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9000_SST_1_5QI6,UlRateBasedPriority=1 ulPrioritizedRate 5000
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9001_SST_1_5QI6,DlRateBasedPriority=1 dlPrioritizedRate 10000
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,DlRateBasedPriority=1 dlPrioritizedRate 2000
set GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_9002_SST_1_5QI6,UlRateBasedPriority=1 ulPrioritizedRate 2000

        """]

        if self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.contains('^K'))].shape[0] > 0 or \
                self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.contains('^J'))].shape[0] > 0 or \
                self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.contains('^I'))].shape[0] > 0:
            lines += ["""
###########################################
####  REDCAP Activation NR N25/N71 FDD ONLY
###########################################
set FeatureState=CXC4012800 featureState 1
set NRCellDU=[K|J] redCap1RxEnabled true
set NRCellDU=[K|J] redCap2RxEnabled true

## Disable redcap towards N41 freqrelation
mr n41freq
ma n41freq nrfrequency bandlist 41
mr n41freqreln
ma n41freqreln n41freq reservedby
set n41freqreln redCapEnabled false
mr n41freqreln
mr n41freq

## Enable redcap towards N71 relations
mr n71freq
ma n71freq nrfrequency bandlist 71
mr n71freqreln
ma n71freqreln n71freq reservedby
set n71freqreln redCapEnabled true
mr n71freqreln
mr n71freq

## Enable redcap towards N25 relations
mr n25freq
ma n25freq nrfrequency bandlist 25
mr n25freqreln
ma n25freqreln n25freq reservedby
set n25freqreln redCapEnabled true
mr n25freqreln
mr n25freq
set NRCellDU=[K|J] redCapUeLimit 1

crn GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=RedCap_UE
selectionCriteria redCapUe==1
ueServiceGroupId 7
ueServiceGroupPriority 99
Userlabel redcap
end

//##################################################################################################################
//# NR LB Parameters/SCs that require cells to be in LOCKED state
//##################################################################################################################

//#v11 - Update to accommodate set NRCellDU=[K|J|I] PuschModeOnFddSCell 1 as a part of of TMO 24Q2_LTE_NR_FDD_PUS_update_v3
set NRCellDU=[K|J|I] PuschModeOnFddSCell 1
get 0 networkManagedElementId > $NodeID
$siteid = `$gawk -v node=$NodeID 'BEGIN { print substr(node, 2, 8)}'`
if $siteid = SF03044A || $siteid = SFY5025A || $siteid = SD06198A || $siteid = SD06321A || $siteid = SD06392A || $siteid = SD06441A || $siteid = SD06767A || $siteid = SD06785A || $siteid = SD06800A || $siteid = SD06943A || $siteid = SD08023A || $siteid = SD08034A || $siteid = SD08087A || $siteid = SD08105A || $siteid = SD08143A || $siteid = SD08156A || $siteid = SD08191A || $siteid = SD08263A || $siteid = SD08398A || $siteid = IE04651A || $siteid = LA02716X || $siteid = SV00302A || $siteid = SV00535A || $siteid = SV00540A || $siteid = SV11437E || $siteid = SV13570A || $siteid = SV90079A || $siteid = HI01124A || $siteid = HI01128A || $siteid = HI01129A || $siteid = HI01136A || $siteid = HI01166B || $siteid = HI01410H || $siteid = HI01530A || $siteid = HI04197A || $siteid = HI04202B || $siteid = HI04226C || $siteid = VG20023A || $siteid = VG21009A || $siteid = VG21014A || $siteid = VG21034A || $siteid = VA1091ZA || $siteid = BK09008A || $siteid = 4BG0450A || $siteid = 4BG0467A || $siteid = 4BG0482A || $siteid = 4BG0487A || $siteid = 4BG0489A || $siteid = 4DR1040A || $siteid = 4LA0142A || $siteid = 4MN0625A || $siteid = 4NB0113A || $siteid = 4PR0330A || $siteid = 4WA0545B || $siteid = 4WA0546B || $siteid = NE2109ZA || $siteid = A2A0203A || $siteid = A2A2101A || $siteid = 6MD2278B || $siteid = 6MD4582A || $siteid = 6WP1374B || $siteid = FLYY901A || $siteid = 7WDC704A || $siteid = PH0141ZA || $siteid = PH0146ZA || $siteid = PH0147ZA || $siteid = PH0148ZA || $siteid = PHY9001A || $siteid = 8SU0481A || $siteid = 3ALA016C || $siteid = 3CAS062C || $siteid = 3ESA464D || $siteid = 3GER229A || $siteid = 3JES309A || $siteid = 3JES311C || $siteid = 3JES462A || $siteid = 3NIB796A || $siteid = 3SAA033H || $siteid = 3SLS739A || $siteid = 3WAA218A || $siteid = 3WRJ719A || $siteid = NY10023A || $siteid = NY10026A || $siteid = NY10039A || $siteid = NY10901A || $siteid = UP10196A || $siteid = UP10310A || $siteid = UP10350A || $siteid = UP10363A || $siteid = UP10498A || $siteid = UP10511A || $siteid = UP10803A || $siteid = UP1083ZA || $siteid = UP1085ZA || $siteid = UP1086ZA || $siteid = UP20279A || $siteid = UP30054A || $siteid = UP30065A || $siteid = UP30255A || $siteid = UP30696A || $siteid = UP30698A || $siteid = UP30767A || $siteid = UP30806A || $siteid = UP30821A || $siteid = UP30822A || $siteid = UP40170A || $siteid = UP40191A || $siteid = UP40257A || $siteid = UP40278A || $siteid = UP40318A || $siteid = UP40398A || $siteid = UP40516A || $siteid = UP40608A || $siteid = UP40614A || $siteid = UP40628A || $siteid = UP40638A || $siteid = UP40833A || $siteid = UP50054A || $siteid = UP50723A || $siteid = UP50727A || $siteid = UP50735A || $siteid = UP50740A || $siteid = NJ06732Q || $siteid = 2AD9410A || $siteid = 2CL4722A || $siteid = 2MN4747A || $siteid = 1CH2487A || $siteid = 1CH5559A || $siteid = 1CH5564A || $siteid = 1CH5566A || $siteid = 1CH5567A || $siteid = 1CH5569C || $siteid = 1CH5571D || $siteid = 1CH6270I || $siteid = 1CH6409C || $siteid = 1CH6473A || $siteid = 1CH6474A || $siteid = 1CH6922B || $siteid = 1CH8197A || $siteid = 1CH8208A || $siteid = 1CH8783A || $siteid = 1CH9639A || $siteid = 1CH9698A || $siteid = 1CH9701A || $siteid = PH0142ZA || $siteid = PH0149ZA || $siteid = PH0176ZA || $siteid = CT11604B || $siteid = CTHA826A
    print "no ulca time alignment required "
else 
    print "ulca time alignment required" 
    mr SECBATCH
    ma SECBATCH NRSectorCarrier administrativeState 1
    mr SECBATCH NRSectorCarrier reservedBy NRCellDU=A 
    bl SECBATCH
    wait 10
    lset NRCellDU=[J|I|K] nrLteCoexistence false
    lset NRCellDU=[J|I|K] ulcatimealignmentmode 1
    deb SECBATCH
    wait 10
fi
mr SECBATCH

                """]
        # 24Q4 Updates
        if self.usid.client.software.swname[:9] > 'TMO_24_Q3':
            lines += ["""
######################
#### NR PCI Conflicts
######################
#### Enable Feature
set GNBCUCPFunction=1,PciHandling=1 pciConflictHandlingEnabled true

#### Configure Feature
set PciHandling=1,PciConflictNR=1 pciConflictDetectionThreshNr 75
set PciHandling=1,PciConflictEUtran=1 pciConflictDetectionThreshLTE 75
set PciHandling=1,PciConflictNR=1,PciConflictNRUeCfg=Base pciConflictMobilityNcgiMeas 1
set PciHandling=1,PciConflictNR=1,PciConflictNRUeCfg=Base pciConflictDetectionNcgiMeas 1

#### pciConflictDrxOnDurationTimer 39 translates to 10 msec
set PciHandling=1,PciConflictNR=1,PciConflictNRUeCfg=Base pciConflictDrxOnDurationTimer 39

#### pciConflictDrxInactivityTimer 16 translates to 200 msec
set PciHandling=1,PciConflictNR=1,PciConflictNRUeCfg=Base pciConflictDrxInactivityTimer 16

#### pciConflictDrxLongCycle 12 translates to 320 msec
set PciHandling=1,PciConflictNR=1,PciConflictNRUeCfg=Base pciConflictDrxLongCycle 12

set PciHandling=1,PciConflictEUtran=1,PciConflictEUtranUeCfg=Base pciConflictDetectionEcgiMeas 1

#### pciConflictDrxOnDurationTimer 36 translates to 5 msec
set PciHandling=1,PciConflictEUtran=1,PciConflictEUtranUeCfg=Base pciConflictDrxOnDurationTimer 36

#### pciConflictDrxInactivityTimer 9 translates to 20 msec
set PciHandling=1,PciConflictEUtran=1,PciConflictEUtranUeCfg=Base pciConflictDrxInactivityTimer 9

#### pciConflictDrxLongCycle 12 translates to 320 msec
set PciHandling=1,PciConflictEUtran=1,PciConflictEUtranUeCfg=Base pciConflictDrxLongCycle 12

#### Exclude VONR UEs from measuring NCGI for NR
crn GNBCUCPFunction=1,PciHandling=1,PciConflictNR=1,PciConflictNRUeCfg=VONR 
pciConflictDetectionNcgiMeas 0 
pciConflictDrxInactivityTimer 9 
pciConflictDrxLongCycle 12 
pciConflictDrxOnDurationTimer 36 
pciConflictMobilityNcgiMeas 0 
prefUeGroupList 
ueConfGroupList 
ueGroupList 1 
end 

#### Exclude VONR UEs from measuring ECGI for EUtran
crn GNBCUCPFunction=1,PciHandling=1,PciConflictEUtran=1,PciConflictEUtranUeCfg=VONR 
pciConflictDetectionEcgiMeas 0 
pciConflictDrxInactivityTimer 9 
pciConflictDrxLongCycle 12 
pciConflictDrxOnDurationTimer 36 
prefUeGroupList 
ueConfGroupList 
ueGroupList 1 
end

#### NR PCI Conflict Reporting (25Q1 fix + 25Q2)
pr upgradepackage=.*/2
if $nr_of_mos != 0
    set PciHandling=1 pciConflictHandlingEnabled true
    set PciHandling=1,PciConflictEUtran=1,PciConflictEUtranUeCfg=Base pciConflictDrxInactivityTimer 9
    set PciHandling=1,PciConflictEUtran=1,PciConflictEUtranUeCfg=Base pciConflictDrxOnDurationTimer 39
    set PciHandling=1,PciConflictNR=1,PciConflictNRUeCfg=Base pciConflictDrxInactivityTimer 9
    set PciHandling=1,PciConflictEUtran=1,PciConflictEUtranUeCfg=Base pciConflictTargetSelectMode 3
    set PciHandling=1,PciConflictNR=1,PciConflictNRUeCfg=Base pciConflictTargetSelectMode 3
    set PciHandling=1,PciConflictEUtran=1,PciConflictEUtranUeCfg=Base pciConflictMobilityEcgiMeas 1
fi

##################################################################
#### GEN3 BB and Above Features - BB6630 and BB5216 Excluded 
##################################################################

pr upgradepackage=.*/2
if $nr_of_mos != 0 
    $GEN3BB = yes
else
    $GEN3BB = no
fi

if $nr_of_mos != 0
    #### WPS Service Admission and Preemption
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012764 featureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012765 featureState 1
    
    crn GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_SA
    maxNoOfSessions 
    end
    crn GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_NSA
    maxNoOfSessions 
    end
    lt SessionLimit
    crn GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_SA,FlowLimit=MMBB_WPS
    maxNoOfFlows 
    flowLimit5qiList 6,7,8,9,128,129
    end
    crn GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_NSA,FlowLimit=MMBB_WPS
    maxNoOfFlows
    flowLimit5qiList 6,7,8,9,128,129
    end
    
    cr GNBDUFunction=1,TrafficGroups=1,TrafficGroup=WPS
    lt TrafficGroup
    set GNBDUFunction=1,TrafficGroups=1,TrafficGroup=WPS,TrafficGroupMember=Default_SA sessionLimitRef GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_SA
    set GNBDUFunction=1,TrafficGroups=1,TrafficGroup=WPS,TrafficGroupMember=Default_ENDC sessionLimitRef GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_NSA
    set NRCellDU trafficGroupRef GNBDUFunction=1,TrafficGroups=1,TrafficGroup=WPS
    set GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_SA,FlowLimit=MMBB_WPS preemptionEnabled true
    
    #### Periodic UE Measurements
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012763$ featureState 1
    set GNBCUCPFunction=1,NRCellCU= puemEnabled true
    set GNBCUCPFunction=1,PeriodicUeMeas=1,PuemCellProfile=Default puemCellTargetIntensity 360
    set GNBCUCPFunction=1,PeriodicUeMeas=1,PuemCellProfile=Default,PuemCellProfileUeCfg=Base puemReportConfigPeriodical includeBeamMeas=true
    set GNBCUCPFunction=1,PeriodicUeMeas=1,PuemCellProfile=Default,PuemCellProfileUeCfg=Base puemReportConfigPeriodical maxNoOfRsIndexesToReport=1
    set GNBCUCPFunction=1,PeriodicUeMeas=1,PuemCellProfile=Default,PuemCellProfileUeCfg=Base puemReportConfigPeriodical maxReportCells=8
    set GNBCUCPFunction=1,PeriodicUeMeas=1,PuemCellProfile=Default,PuemCellProfileUeCfg=Base puemReportConfigPeriodical reportAddNeighMeas=true
    set GNBCUCPFunction=1,PeriodicUeMeas=1,PuemCellProfile=Default,PuemCellProfileUeCfg=Base puemReportConfigPeriodical reportAmount=4
    set GNBCUCPFunction=1,PeriodicUeMeas=1,PuemCellProfile=Default,PuemCellProfileUeCfg=Base puemReportConfigPeriodical reportInterval=6
    set GNBCUCPFunction=1,PeriodicUeMeas=1,PuemCellProfile=Default,PuemCellProfileUeCfg=Base puemReportConfigPeriodical reportQuantityCell=6
    set GNBCUCPFunction=1,PeriodicUeMeas=1,PuemCellProfile=Default,PuemCellProfileUeCfg=Base puemReportConfigPeriodical reportQuantityRsIndex=6
fi

lst GNBDUFunction=1,NRCellDU=[K|J|I]
if $nr_of_mos != 0 && $GEN3BB = yes
    set GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_SA,FlowLimit=MMBB_WPS maxNoOfFlows 500
    set GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_NSA,FlowLimit=MMBB_WPS maxNoOfFlows 250 
fi

lst GNBDUFunction=1,NRCellDU=A
if $nr_of_mos != 0 && $GEN3BB = yes
    set GNBDUFunction=1,NRCellDU=A.* pdcchSymbConfig 2
    set GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_SA,FlowLimit=MMBB_WPS maxNoOfFlows 1000
    set GNBDUFunction=1,ContentionControl=1,SessionLimit=WPS_NSA,FlowLimit=MMBB_WPS maxNoOfFlows 500
fi
                """]
            if self.air_6648_6649:
                lines += ["""
    ############# Checks for DST updates ##################
    ############ DST Enhancement Settings ##################
    set PowerSaving=1 ranCompDeepSleepEnabled false
    
    get SysM=1,TimeM=1,DateAndTime=1 timeZone > $TimeZ
    get NRSectorCarrier massiveMimoSleepEnabled > $sleepEnabled_var1
    get FieldReplaceableUnit productData AIR.*64...*B41
    if $nr_of_mos != 0 && $sleepEnabled_var1 !~ 0 && $TimeZ = US/Hawaii
        set TimeSettings timeOffset -10:00
        set TimeSettings daylightSavingTimeStartDate dayRule=Sun>=8,month=3,time=02:00
        set TimeSettings daylightSavingTimeEndDate dayRule=Sun>=1,month=11,time=02:00
        set TimeSettings daylightSavingTimeOffset 1:00
    else if $nr_of_mos != 0 && $sleepEnabled_var1 !~ 0 && $TimeZ = US/Pacific
        set TimeSettings timeOffset -08:00
        set TimeSettings daylightSavingTimeStartDate dayRule=Sun>=8,month=3,time=02:00
        set TimeSettings daylightSavingTimeEndDate dayRule=Sun>=1,month=11,time=02:00
        set TimeSettings daylightSavingTimeOffset 1:00
    else if $nr_of_mos != 0 && $sleepEnabled_var1 !~ 0 && $TimeZ = US/Mountain
        set TimeSettings timeOffset -07:00
        set TimeSettings daylightSavingTimeStartDate dayRule=Sun>=8,month=3,time=02:00
        set TimeSettings daylightSavingTimeEndDate dayRule=Sun>=1,month=11,time=02:00
        set TimeSettings daylightSavingTimeOffset 1:00
    else if $nr_of_mos != 0 && $sleepEnabled_var1 !~ 0 && $TimeZ = US/Central
        set TimeSettings timeOffset -06:00
        set TimeSettings daylightSavingTimeStartDate dayRule=Sun>=8,month=3,time=02:00
        set TimeSettings daylightSavingTimeEndDate dayRule=Sun>=1,month=11,time=02:00
        set TimeSettings daylightSavingTimeOffset 1:00
    else if $nr_of_mos != 0 && $sleepEnabled_var1 !~ 0 && $TimeZ = US/Eastern
        set TimeSettings timeOffset -05:00
        set TimeSettings daylightSavingTimeStartDate dayRule=Sun>=8,month=3,time=02:00
        set TimeSettings daylightSavingTimeEndDate dayRule=Sun>=1,month=11,time=02:00
        set TimeSettings daylightSavingTimeOffset 1:00
    fi
                            """]
        # 25Q1 Updates
        if self.usid.client.software.swname[:9] > 'TMO_24_Q4':
            lines += [F"""
####:----------------> LTE Parameter Setting for 25Q1 SW <----------------:####
set PowerSaving ranCompDeepSleepEnabled true
"""]
            if (0 < self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.startswith(('K', 'J', 'I')))].shape[0] ==
                    self.df_gnb_cell.loc[self.df_gnb_cell.postcell.str.startswith(('K', 'J', 'I'))].shape[0]):
                lines += ["""
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
set GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=6          drbRef GNBCUUPFunction=1,UeCC=1,Drb=5QI6_L4S

################################################################
#### GEN3 BB and Above Features - BB6630 and BB5216 Excluded 
#### 2L UL SU-MIMO FDD - Gen3 and above
#### Energy-optimized Slot Allocation - Gen3 and above
#### Priority Paging - Gen3 and above
#### MPS priority indication in RRC connection release - Gen3 and above
#### Uplink RAN-Assisted Rate Adaptation with L4S - Gen3 and above
#### Dynamic A-CSI Periodicity - Gen 3 AND ABOVE 
#### UL Config Grant
################################################################

func GEN3BB

####################
## 2L UL SU-MIMO 
####################

#### create OneTxPort
 
crn GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=OneTxPort
ulWfSwitchFr1Mode 1
ulPortSwitchQualThresh 10000
ulLayerSwitchQualThresh 10000
ulPortSwitchFr1Mode 1
ulPortSwitchTimeToTrigger 200

end

set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR ulWfPortSwitchUeCfgRef GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=OneTxPort

set CXC4012493 featureState 1

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

###############################################
## UL RAN-Assisted Rate Adaptation with L4S
###############################################

set SystemFunctions=1,Lm=1,FeatureState=CXC4012749  featureState 1
cr GNBDUFunction=1,UeCC=1,L4sCfg=1
set GNBDUFunction=1,UeCC=1,L4sCfg=1 ulL4sHighThresh 40
set GNBDUFunction=1,UeCC=1,L4sCfg=1 ulL4slowThresh 20
set GNBDUFunction=1,UeCC=1,L4sCfg=1 ulL4sMode 1     
set DU5qiTable=1,DU5qi=6               l4sCfgRef GNBDUFunction=1,UeCC=1,L4sCfg=1

###############################################
#### Dynamic A-CSI Periodicity - Gen 3 AND ABOVE 
###############################################

cr GNBDUFunction=1,UeCC=1,CsiProfile=1,CsiProfileUeCfg=VoNR
set GNBDUFunction=1,UeCC=1,CsiProfile=1,CsiProfileUeCfg=VoNR csiBufferThresh 0
set GNBDUFunction=1,UeCC=1,CsiProfile=1,CsiProfileUeCfg=VoNR csiRptPeriodAdd 0
set GNBDUFunction=1,UeCC=1,CsiProfile=1,CsiProfileUeCfg=VoNR csiPollRetransmitEnabled false
set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR csiProfileUeCfgRef GNBDUFunction=1,UeCC=1,CsiProfile=1,CsiProfileUeCfg=VoNR

set FeatureState=CXC4012762 featureState 1

set GNBDUFunction=1,UeCC=1,CsiProfile=1,CsiProfileUeCfg=Base csiBufferThresh 3
set GNBDUFunction=1,UeCC=1,CsiProfile=1,CsiProfileUeCfg=Base csiRptPeriodAdd 2
set GNBDUFunction=1,UeCC=1,CsiProfile=1,CsiProfileUeCfg=Base csiPollRetransmitEnabled true

##############################################
## Uplink Configured Grant 
##############################################

set CXC4012596 FeatureState 1
## Activate NR Service-Adaptive Prescheduling feature
set SystemFunctions=1,Lm=1,FeatureState=CXC4012547 featureState 1
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

//set GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=SD_6001 ueGroupPriority 98


## Create UeBbProfile for SD_6001
ldc GNBCUCPFunction=1,UeGroupSelection=1
pr GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=SD_6001
if $nr_of_mos = 0
crn GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=SD_6001
ueGroupList 6
end
fi

//set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=SD_6001 ueGroupList 6

ldc GNBCUCPFunction=1,UeGroupSelection=1
pr GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR
if $nr_of_mos = 0
crn GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR
ueGroupList 1
end
fi

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

set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=SD_6001 configuredGrantUeCfgRef GNBDUFunction=1,UeCC=1,ConfiguredGrant=1,ConfiguredGrantUeCfg=SD_6001

## Create Pre Scheduling for SD_6001 and SD_6000

pr GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=SD_6001
if $nr_of_mos = 0
crn GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=SD_6001
preschedulingUeMode 0
end
fi

## Align prescheduling for SD_6001
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

endfunc

########################################
## Check for GEN2 and exit if found
########################################

pr upgradepackage=.*/2
if $nr_of_mos != 0 
	$GEN3BB = yes
else
	$GEN3BB = no
fi

if $GEN3BB = no
l echo $date1 "Not Gen3 BB"
break
else
GEN3BB
fi

########################################################################################
####DL Smart Scheduling for Space-X     (Requires Cell block/deblock for implementation)                   
########################################################################################

##Feature Activation for N1900  10/15/20/25/30 MHz includes G block                   
mr N19_Sector_Carr
ma N19_Sector_Carr NRCellDU=J nRSectorCarrierRef
get N19_Sector_Carr arfcnDL 398000|397500|397000|396500|396000
if $nr_of_mos != 0  
set FeatureState=CXC4012810 featureState 1
fi

for $mo in N19_Sector_Carr
mr REF_CELL_DU
get $mo nRSectorCarrierId > $N19_scID
get $mo arfcnDL > $N19_arfcnDL[$N19_scID]
get $mo bSChannelBwDL > $BW[$N19_scID]
ma REF_CELL_DU $mo reservedBy 
if $N19_arfcnDL[$N19_scID] = 398000 && $BW[$N19_scID] = 10

set REF_CELL_DU pdschStartPrbStrategy 3
set REF_CELL_DU prioBoundaryCrb 27
set REF_CELL_DU intMitigationDlSched 2

else if $N19_arfcnDL[$N19_scID] = 397500 && $BW[$N19_scID] = 15

set REF_CELL_DU pdschStartPrbStrategy 3
set REF_CELL_DU prioBoundaryCrb 54
set REF_CELL_DU intMitigationDlSched 2

else if $N19_arfcnDL[$N19_scID] = 397000 && $BW[$N19_scID] = 20

set REF_CELL_DU pdschStartPrbStrategy 3
set REF_CELL_DU prioBoundaryCrb 81
set REF_CELL_DU intMitigationDlSched 2

else if $N19_arfcnDL[$N19_scID] = 396500 && $BW[$N19_scID] = 25

set REF_CELL_DU pdschStartPrbStrategy 3
set REF_CELL_DU prioBoundaryCrb 108
set REF_CELL_DU intMitigationDlSched 2

else if $N19_arfcnDL[$N19_scID] = 396000 && $BW[$N19_scID] = 30

set REF_CELL_DU pdschStartPrbStrategy 3
set REF_CELL_DU prioBoundaryCrb 135
set REF_CELL_DU intMitigationDlSched 2

fi
done

set GNBDUFunction=1,Paging=1 defaultPagingCycle 128

"""]
            if (0 < self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.startswith('A'))].shape[0] ==
                    self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.startswith('A'))].shape[0]):
                lines += [""""
//v5 Part of the break-fix issue STA-00295632, addressing SA KPI degradation with increased RRC Connected Users
scw RP2624:3,RP2625:1

//#v3 - SRS Functionality reintroduced with MTR24.03 but with new SC RP2572:0 (former RP1860:0)
scw RP2572:0

// 22.Q2 Rev4 - TMO Adv DL SU MIMO feature SC addition
get FeatureState=CXC4012510$ featureState$ > $AdvDlmimo
if $AdvDlmimo ~ 1
 scw RP970:30,RP1022:0
fi

// 23.Q2 PMI Based PDCCH BF - Only for N41
set CXC4012589 featurestate 1
set NRCellDU pdcchLaBfGainFraction 75
scw RP1988:7
scw RP1810:2

// 23.Q2 MU-MIMO 16 layers - Only for N41.
scw RP146:4,RP1459:4,RP1545:4

//## v3 IA62622 to revert IRAT to legacy behavior
scw RC554:200,RC555:480


//##################################################################################################################
//# NR-MB Parameters
//##################################################################################################################

//# Insert NR MB Parameters Here

//24.Q4-v2 SRS Port Validation feature activation
get FieldReplaceableUnit productData AIR.*64...*B41
if $nr_of_mos != 0
 //SRS Port Validation activation
 mr adsumimo
 ma adsumimo NRCellDU=A.* advancedDlSuMimoEnabled true
 set adsumimo advDlBfWhenAllSrsPortsUsable true
 set adsumimo pairwiseSrsCorrelationThresh 850,990
 
 //2 symbol PDCCH activation
 scw RP2508:1
fi

//25.Q1-v3 - enable radiorestart and radio interface alerts to be sent to enm 
set FmAlarmType=Radio.*Alert.* isNotified 0

//25.Q1-v3 - CB MU MIMO prototype enhancement feature into the 24.Q2 Post upgrade scripts
get FieldReplaceableUnit productData AIR.*64...*B41
if $nr_of_mos != 0
set CXC4012406  featurestate 1
set NRCellDU=A.* dlMaxMuMimoLayers 8

//##MTR25.03 below SCs are now default
#scw RP2519:2343642,RP2357:66389,RP588:405416456,RP558:51811722,RP2648:2
#scd RP268

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
set GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=6          drbRef GNBCUUPFunction=1,UeCC=1,Drb=5QI6_L4S
set GNBCUUPFunction=1,CUUP5qiTable=2,CUUP5qi=6          drbRef GNBCUUPFunction=1,UeCC=1,Drb=5QI6_L4S

###############################################
## UL L4S
###############################################

set SystemFunctions=1,Lm=1,FeatureState=CXC4012749  featureState 1
cr GNBDUFunction=1,UeCC=1,L4sCfg=1
set GNBDUFunction=1,UeCC=1,L4sCfg=1 ulL4sHighThresh 40
set GNBDUFunction=1,UeCC=1,L4sCfg=1 ulL4slowThresh 20
set GNBDUFunction=1,UeCC=1,L4sCfg=1 ulL4sMode 1     
set DU5qiTable=1,DU5qi=6               l4sCfgRef GNBDUFunction=1,UeCC=1,L4sCfg=1
set DU5qiTable=2,DU5qi=6               l4sCfgRef GNBDUFunction=1,UeCC=1,L4sCfg=1

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

### default paging cycle 
set GNBDUFunction=1,Paging=1 defaultPagingCycle 128

func BOCS_RA1
### BoCS 1.5 AAS radio check

get SysM=1,TimeM=1,DateAndTime=1 timeZone > $TimeZ
l echo "TimeZone current setting value are" $TimeZ

if $TimeZ =
l echo "No TimeZone is currently set on the node EXIT"
set GNBCUCPFunction=1,NRCellCU epBoCSMode 0
fi

cr ManagedElement=1,GNBCUCPFunction=1,EnergyPerformance=1,EPBoCS=1,EPBoosterAdvCfg=1
cr ManagedElement=1,GNBCUCPFunction=1,EnergyPerformance=1,EPBoCS=1,EPBoosterCellProfile=1
 
cr ManagedElement=1,GNBCUCPFunction=1,TimeSchedulingGroup=1
cr ManagedElement=1,GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1

set TimeSchedulingGroup=1,TimeSchedulingWindow=1 epBoosterCellProfileRef EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1
set GNBCUCPFunction=1,EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 epBoosterAdvCfgRef EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1  
 
set GNBCUCPFunction=1,NRCellCU=A epBoCSTimeSchedulingGroupRef ManagedElement=1,GNBCUCPFunction=1,TimeSchedulingGroup=1

#### start time and stop time below are in UTC time based on TimeZone on the Node ####
 
//Set TimeSchedulingWindow(UTC)
if $TimeZ = US/Eastern
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  09:45
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 04:00
fi
if $TimeZ = US/Central
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  10:45
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 05:00
fi
if $TimeZ = US/Mountain
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  11:45
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 06:00
fi
if $TimeZ = US/Pacific
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  12:45
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 07:00
fi
if $TimeZ = US/Hawaii
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 stopTime  14:45
set GNBCUCPFunction=1,TimeSchedulingGroup=1,TimeSchedulingWindow=1 startTime 09:00
fi

get NRCellCU=A.*,DESManagementFunction=1 desSwitch > $DEAS
if $DEAS = true
set NRCellCU=A.*,DESManagementFunction=1 desSwitch false
set GNBCUCPFunction=1,NRCellCU=A.* epBoCSMode 1
fi

set GNBCUCPFunction=1,EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 wakeupRequiredTime 600
set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1  wakeupPeriodicEsDuration 120

set EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1     sleepUcfThreshBooster 1500
set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1          sleepFilterTimePercentage 90
set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1          sleepRelBoosterFilterTimePerc 90
set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1          sleepEvaluateTimeWindow 360

set EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=1 wakeupUcfThresh   2500
set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 sleepUcfWakeupThreshFactor 40
set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 wakeupFilterTimePercentage  80
set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1 wakeupEvaluateTimeWindow   600

set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=1  wakeupMissingSampleTime    300

//set GNBCUCPFunction=1 altDepHBoCSEnabled true (in pre script) 

#### NR Flexible DL Resource Allocation Type - AAS Radio check
set CXC4012772 featurestate 1
set GNBDUFunction=1,UeCC=1,ResourceAllocTypeDl=Default,ResourceAllocTypeDlUeCfg=Base prefUeResourceAllocDlTypeFr1 2

endfunc

##  MUST BE AAS Radio 6449/6419 
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

### BoCS 1.5  continuation 
### configure energy performance-related cells , co-sector , inter-frequency , inter-Radio
//NRRelations
// epLoadMonitoringEnabled

func Validate_intra_Inter
get ENEPER_Cell nRCellRef ^NRCellCU=
if $nr_of_mos > 0
set GNBCUCPFunction=1    resourceStatusReportF1Enabled true
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
                
"""]
                if self.air_6648_6649:
                    lines += ['', 'BOCS_RA1', '',]

        # 25Q2 Updates
        if self.usid.client.software.swname[:9] > 'TMO_25_Q1':
            lines += [F"""
####:----------------> LTE Parameter Setting for 25Q1 SW <----------------:####
pr upgradepackage=.*/2
if $nr_of_mos != 0 
    set GNBDUFunction=1 configuredGrantConfMode 1
    set GNBDUFunction=1 measGapLengthMode 0
    
    #### 5CC/6CC - 3F+2T, 4F+1T, 4F +2T, 3F+3T (Gen2 - SCell(s))
    set FeatureState=CXC4012682 featureState 1
    set FeatureState=CXC4012761 featureState 1
    set NRCellDU= additionalPucchForCaEnabled true
    
    #### NR Advanced Cell Supervision
    set FeatureState=CXC4012821 featureState 1
    
    #### NR Flexible DL Resource Allocation Type FDD & 23Q4/24Q4 CSR Fix
    set FeatureState=CXC4012772 featureState 1
    set GNBDUFunction=1,UeCC=1,ResourceAllocTypeDl=Default,ResourceAllocTypeDlUeCfg=Base prefUeResourceAllocDlTypeFr1 2

fi

#### NR Cell Soft Lock Profiles - Cell Offload Priorty Profile Configuration

get SystemFunctions=1,SwInventory=1,SwVersion= swVersionId > $OLDUP
$OLDUP = $OLDUP -s -.*

if $OLDUP ~ ^CXP2010174/2
$NRSoftLockProfiles_GenCheck = Gen3
else if $OLDUP ~ ^CXP9024418/16
$NRSoftLockProfiles_GenCheck = Gen2
else if $OLDUP ~ ^CXP9024418/22
$NRSoftLockProfiles_GenCheck = Gen2
fi

#### Pre Script
set GNBCUCPFunction=1,TrafficOffload=1,OffloadCellProfile=Default ueConfGroupType 2 
set GNBCUCPFunction=1,TrafficOffload=1,OffloadEUtranFreqRelProfile=Default ueConfGroupType 2
set GNBCUCPFunction=1,TrafficOffload=1,OffloadNrFreqRelProfile=Default ueConfGroupType 2 

pr GNBCUCPFunction=1,TrafficOffload=1,OffloadCellProfile=Default,OffloadCellProfileUeCfg=VoNR
if $nr_of_mos = 0 && $NRSoftLockProfiles_GenCheck ~ Gen3
crn GNBCUCPFunction=1,TrafficOffload=1,OffloadCellProfile=Default,OffloadCellProfileUeCfg=VoNR
cellOffloadPriority 7
maxReportCells 4
checkForOffloadEnd false
offloadISHoEnabled false
pCellCandidateTriggerQuantity 0
prefUeGroupList
rimOffloadIncHoRsrpThresh
rsrpPCellCandAddTargEval 0
rsrpPCellCandB1AddTargEval 0
rsrpPCellCandidate hysteresis=10,threshold2=-116,timeToTrigger=320
rsrpPCellCandidateB1 hysteresis=10,threshold=-140,timeToTrigger=640
rsrqPCellCandAddTargEval 0
rsrqPCellCandB1AddTargEval 0
rsrqPCellCandidate hysteresis=10,threshold2=-435,timeToTrigger=640
rsrqPCellCandidateB1 hysteresis=10,threshold=-195,timeToTrigger=40
sinrPCellCandAddTargEval 0
sinrPCellCandB1AddTargEval 0
sinrPCellCandidate hysteresis=10,threshold2=-230,timeToTrigger=640
sinrPCellCandidateB1 hysteresis=10,threshold=-230,timeToTrigger=40
ueConfGroupList
ueGroupList 1
ueOffloadISHoRatio 1000
end
fi

pr GNBCUCPFunction=1,TrafficOffload=1,OffloadCellProfile=Default,OffloadCellProfileUeCfg=WPS_User
if $nr_of_mos = 0 && $NRSoftLockProfiles_GenCheck ~ Gen3
crn GNBCUCPFunction=1,TrafficOffload=1,OffloadCellProfile=Default,OffloadCellProfileUeCfg=WPS_User
cellOffloadPriority 5
maxReportCells 4
checkForOffloadEnd false
offloadISHoEnabled false
pCellCandidateTriggerQuantity 0
prefUeGroupList
rimOffloadIncHoRsrpThresh
rsrpPCellCandAddTargEval 0
rsrpPCellCandB1AddTargEval 0
rsrpPCellCandidate hysteresis=10,threshold2=-116,timeToTrigger=320
rsrpPCellCandidateB1 hysteresis=10,threshold=-140,timeToTrigger=640
rsrqPCellCandAddTargEval 0
rsrqPCellCandB1AddTargEval 0
rsrqPCellCandidate hysteresis=10,threshold2=-435,timeToTrigger=640
rsrqPCellCandidateB1 hysteresis=10,threshold=-195,timeToTrigger=40
sinrPCellCandAddTargEval 0
sinrPCellCandB1AddTargEval 0
sinrPCellCandidate hysteresis=10,threshold2=-230,timeToTrigger=640
sinrPCellCandidateB1 hysteresis=10,threshold=-230,timeToTrigger=40
ueConfGroupList 1
ueGroupList 
ueOffloadISHoRatio 1000
end
fi

pr GNBCUCPFunction=1,TrafficOffload=1,OffloadCellProfile=Default,OffloadCellProfileUeCfg=VoNR
if $nr_of_mos = 0 && $NRSoftLockProfiles_GenCheck ~ Gen2
crn GNBCUCPFunction=1,TrafficOffload=1,OffloadCellProfile=Default,OffloadCellProfileUeCfg=VoNR
cellOffloadPriority 7
checkForOffloadEnd false
offloadISHoEnabled false
prefUeGroupList
rimOffloadIncHoRsrpThresh
rsrpPCellCandidate hysteresis=10,threshold2=-116,timeToTrigger=320
rsrpPCellCandidateB1 hysteresis=10,threshold=-140,timeToTrigger=640
ueConfGroupList
ueGroupList 1
ueOffloadISHoRatio 1000
end
fi

pr GNBCUCPFunction=1,TrafficOffload=1,OffloadCellProfile=Default,OffloadCellProfileUeCfg=WPS_User
if $nr_of_mos = 0 && $NRSoftLockProfiles_GenCheck ~ Gen2
crn GNBCUCPFunction=1,TrafficOffload=1,OffloadCellProfile=Default,OffloadCellProfileUeCfg=WPS_User
cellOffloadPriority 5
checkForOffloadEnd false
offloadISHoEnabled false
prefUeGroupList
rimOffloadIncHoRsrpThresh
rsrpPCellCandidate hysteresis=10,threshold2=-116,timeToTrigger=320
rsrpPCellCandidateB1 hysteresis=10,threshold=-140,timeToTrigger=640
ueConfGroupList 1
ueGroupList 
ueOffloadISHoRatio 1000
end
fi

#### BandlistManual
st ^nrcelldu=K
if $nr_of_mos != 0
set nrcelldu=K.* BandlistManual 71
fi

st ^nrcelldu=J.*
if $nr_of_mos != 0
set nrcelldu=J.* BandlistManual 25
fi

st ^nrcelldu=I
if $nr_of_mos != 0
set nrcelldu=I.* BandlistManual 66
fi

st ^nrcelldu=A
if $nr_of_mos != 0
set nrcelldu=A.* BandlistManual 41
fi

st ^nrcelldu=Q
if $nr_of_mos != 0
set nrcelldu=Q.* BandlistManual 77
fi

st ^nrcelldu=S
if $nr_of_mos != 0
set nrcelldu=S.* BandlistManual 77
fi

st ^nrcelldu=M
if $nr_of_mos != 0
set nrcelldu=M.* BandlistManual 261
fi

st ^nrcelldu=N
if $nr_of_mos != 0
set nrcelldu=N.* BandlistManual 260
fi

st ^nrcelldu=O
if $nr_of_mos != 0
set nrcelldu=O.* BandlistManual 258
fi

#### PDCCH Capacity Boost* (rollover from 25Q1)

mr nrcellgr
mr cellgrToSet
ma nrcellgr NRCellDU=[AQS]
for $mo in nrcellgr
get $mo nRSectorCarrierRef > $nrseccarrRef
$secCarrRefval = split($nrseccarrRef)
get $secCarrRefval[6] sectorEquipmentFunctionRef > $secEquFuncRef

get $secEquFuncRef$ rfBranchRef > $rfbranchval
$branchVal = split($rfbranchval)
$branch1 = $branchVal[6]

if $branch1 ~ .*AntennaUnitGroup=.* && $branch1 !~ .*MulticastAntennaBranch=.*
get $branch1 rfPortRef > $branch2
$fieldRepUnit = $branch2 -s ,RfPort=.* -g
else if $branch1 ~ .*FieldReplaceableUnit=.* && $branch1 !~ .*MulticastAntennaBranch=.*
$fieldRepUnit = $branch1 -s ,Transceiver=.* -g
else if $branch1 ~ .*AntennaUnitGroup=.* && $branch1 ~ .*MulticastAntennaBranch=.*
get $branch1 transceiverRef > $branch3
$transceiverRefVal = $branch3 -s ,Transceiver=.* -g
$firsttransceiverRefVal = split($transceiverRefVal)
$fieldRepUnit = $firsttransceiverRefVal[6]
fi

get $fieldRepUnit$ productData > $varproductData
$prodName = $varproductData[productName]

$AirRadio = 0
if $prodName ~ AIR.*64...*B??.*
$AirRadio = 1
fi

if $AirRadio = 1
lma cellgrToSet $mo
fi
done

pr cellgrToSet
if $nr_of_mos > 0
set cellgrToSet pdcchCapacityBoostEnabled true
set FeatureState=CXC4012817 featureState 1
fi

#### FDD PC2 support

set ,NRFreqRelation=1 pmax 27
set ,NRFreqRelation=1 qrxlevmin -120
set ,NRFreqRelation=3 pmax 27
set ,NRFreqRelation=3 qrxlevmin -124
set ,NRFreqRelation=4 pmax 27
set ,NRFreqRelation=4 qrxlevmin -124

set ,GUtranFreqRelation=1 pmaxnr 27
set ,GUtranFreqRelation=1 qrxlevmin -120
set ,GUtranFreqRelation=3 pmaxnr 27
set ,GUtranFreqRelation=3 qrxlevmin -124
set ,GUtranFreqRelation=4 pmaxnr 27
set ,GUtranFreqRelation=4 qrxlevmin -124

pr GNBDUFunction=1,NRCellDU=I
if $nr_of_mos > 0
    set GNBDUFunction=1,NRCellDU=I pmax 27
    set GNBDUFunction=1,NRCellDU=I qrxlevmin -124
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=I.*,McpcPCellProfileUeCfg=Base rsrpCriticalPcOffset powerClass=PC_2,thresholdOffset=-3
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=I.*,McpcPCellProfileUeCfg=Base rsrpSearchZonePcOffset powerClass=PC_2,thresholdOffset=-3
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=I.*,McpcPCellProfileUeCfg=Base rsrpCandidateA5PcOffset powerClass=PC_2,threshold1Offset=-3,threshold2Offset=0
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=I.*,McpcPCellProfileUeCfg=Base rsrpCandidateB2PcOffset powerClass=PC_2,threshold1Offset=0
fi

pr GNBDUFunction=1,NRCellDU=J
if $nr_of_mos > 0
    set GNBDUFunction=1,NRCellDU=J pmax 27
    set GNBDUFunction=1,NRCellDU=J qrxlevmin -124
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=J.*,McpcPCellProfileUeCfg=Base rsrpCriticalPcOffset powerClass=PC_2,thresholdOffset=-3
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=J.*,McpcPCellProfileUeCfg=Base rsrpSearchZonePcOffset powerClass=PC_2,thresholdOffset=-3
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=J.*,McpcPCellProfileUeCfg=Base rsrpCandidateA5PcOffset powerClass=PC_2,threshold1Offset=-3,threshold2Offset=0
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=J.*,McpcPCellProfileUeCfg=Base rsrpCandidateB2PcOffset powerClass=PC_2,threshold1Offset=0
fi

pr GNBDUFunction=1,NRCellDU=K
if $nr_of_mos > 0
    set GNBDUFunction=1,NRCellDU=K pmax 27
    set GNBDUFunction=1,NRCellDU=K qrxlevmin -120
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=K.*,McpcPCellProfileUeCfg=Base rsrpCriticalPcOffset powerClass=PC_2,thresholdOffset=-3
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=K.*,McpcPCellProfileUeCfg=Base rsrpSearchZonePcOffset powerClass=PC_2,thresholdOffset=-3
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=K.*,McpcPCellProfileUeCfg=Base rsrpCandidateA5PcOffset powerClass=PC_2,threshold1Offset=-3,threshold2Offset=0
    set GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=K.*,McpcPCellProfileUeCfg=Base rsrpCandidateB2PcOffset powerClass=PC_2,threshold1Offset=0
fi

#### NR Switched Uplink for Throughput Boost (MLC interactions with UL Tx switching)
get FeatureState=CXC4012493 featureState$ > $NRSwitch_PreReq1
get FeatureState=CXC4012690 featureState$ > $NRSwitch_PreReq2
pr upgradepackage=.*/2
if $nr_of_mos != 0
    $NRULTptBoost_Gen3 = Yes
fi
if $NRSwitch_PreReq1 ~ 1 && $NRSwitch_PreReq2 ~ 1 && $NRULTptBoost_Gen3 ~ Yes
    set FeatureState=CXC4012786 featureState 1
    set NRCellDU= ulTxSwitchingEnabled true
    set CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=Base ulTxSwitchingAllowed false
    set GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default ueConfGroupType 1
fi

"""]
            if self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.startswith('A'))].shape[0] > 0:
                lines += [F"""
#### RCDS activation
pr upgradepackage=.*/2
if $nr_of_mos != 0
$RCDS_Gen3 = 1
fi
get PowerSaving ranCompDeepSleepEnabled$ > $RCDS_Var1
if $RCDS_Var1 ~ false && $RCDS_Gen3 = 1
set PowerSaving ranCompDeepSleepEnabled true
fi

#### NR FR1 DL SCell Mitigation for SRS Antenna Switching in SpCell
set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base srsImpactHandling 1

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

"""]
            if (0 < self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.startswith(('K', 'J', 'I')))].shape[0] ==
                    self.df_gnb_cell.loc[self.df_gnb_cell.postcell.str.startswith(('K', 'J', 'I'))].shape[0]):
                lines += ["""
#### UL CA F+F

func ULCA_FplusFAct_FplusTDeAct
    # Disabling UL F+T due to rollover to 25.Q3
    mr IJ_SCell1
    ma IJ_SCell1 NRCellCU=[JI].*NRCellRelation= ^sCellCandidate 1
    ma IJ_SCell1_NRFreqRelation5 IJ_SCell1 nRFreqRelationRef NRFreqRelation=5.*
    set IJ_SCell1_NRFreqRelation5 sCellCandidate 2

    set FeatureState=CXC4012663 featureState 1

    //#Gen4 (RP6672) Verification
    get FieldReplaceableUnit productData RAN.*Processor.*6672
    if $nr_of_mos != 0
        $ULFplusFVar2 = Default_FDD
    else
        $ULFplusFVar2 = Default
    fi

    pr CaCellProfile=$ULFplusFVar2$
    if $nr_of_mos > 0
        u+s
        ldel CaCellProfile=$ULFplusFVar2$
        u-
    else
        $ULFplusFVar2 = Default
        u+s
        ldel CaCellProfile=$ULFplusFVar2$
        u-
    fi

    mr NRCELLCU_Var1
    ma NRCELLCU_Var1 GNBCUCPFunction=1,NRCellCU=
    pr NRCELLCU_Var1
    $countIJ = 1
    $countK = 1

    for $mo in NRCELLCU_Var1
        $CellID = rdn($mo)
        $CellID = $CellID -s NRCellCU=
        $CellID = $CellID -s I.* -r I
        $CellID = $CellID -s K.* -r K
        $CellID = $CellID -s J.* -r J
        print $CellID
        if $CellID = I && $countIJ = 1
            l sed 's/CaCellProfile=\$ULFplusFVar2/CaCellProfile=midBandFDD/g' $undocommandfile  > $nodename_commandfile_IJ.mos
            run $nodename_commandfile_IJ.mos
            l rm $nodename_commandfile_IJ.mos
            $countIJ = $countIJ + 1
        else if $CellID = J && $countIJ = 1
            l sed 's/CaCellProfile=\$ULFplusFVar2/CaCellProfile=midBandFDD/g' $undocommandfile > $nodename_commandfile_IJ.mos
            run $nodename_commandfile_IJ.mos
            l rm $nodename_commandfile_IJ.mos
            $countIJ = $countIJ + 1
        else if $CellID = K && $countK = 1
            l sed 's/CaCellProfile=\$ULFplusFVar2/CaCellProfile=N600_Config/g' $undocommandfile > $nodename_commandfile_K.mos
            run $nodename_commandfile_K.mos
            l rm $nodename_commandfile_K.mos
            $countK = $countK + 1
        fi
    done

    l rm $undodelcommandfile $undocommandfile $undologfile

    lt CaCellProfile
    set nrcellcu=[I|J].* caCellProfileRef GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=midBandFDD
    set nrcellcu=K.* caCellProfileRef GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=N600_Config
    pr GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=midBandFDD,CaCellProfileUeCfg=Base
    if $nr_of_mos != 0
        set GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=midBandFDD,CaCellProfileUeCfg=Base maxUlCcAllowed 32
    fi
    pr GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=N600_Config,CaCellProfileUeCfg=Base
    if $nr_of_mos != 0
        set GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=N600_Config,CaCellProfileUeCfg=Base maxUlCcAllowed 32
    fi

    set FeatureState=CXC4012690 featureState 1
    set NRCellDU=[IJK] caPerCcFairnessWeightUlEnabled true
endfunc

pr CaCellProfile=Default
if $nr_of_mos != 0
    ULCA_FplusFAct_FplusTDeAct
fi


#### UE grouping for 2L SU MIMO for Moto RAZR
func UEGrp_MotoRzr
    pr GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=OneTxPort
    if $nr_of_mos = 0
        crn GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=OneTxPort
        ulWfSwitchFr1Mode 1
        ulPortSwitchQualThresh 10000
        ulLayerSwitchQualThresh 10000
        ulPortSwitchFr1Mode 1
        ulPortSwitchTimeToTrigger 200
        end
    fi
    
    lt UlWfPortSwitch
    
    pr GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=MotoRazr25
    if $nr_of_mos = 0
        crn GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=MotoRazr25
        selectionCriteria (imeitac=={35008657,35665599,35029189,35661177})
        ueServiceGroupId 1
        ueServiceGroupPriority 103
        userLabel MotoRazr25
        end
    fi
    
    lt UeGroupSelection
    pr GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=MotoRazr25
    if $nr_of_mos = 0
        crn GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=MotoRazr25
        ueConfGroupList 1
        ulWfPortSwitchUeCfgRef GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=OneTxPort
        end
    fi
    
    lt UeBbProfile
    set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=MotoRazr25 ulWfPortSwitchUeCfgRef GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=OneTxPort
endfunc

get FeatureState=CXC4012493 licenseState$ > $MotoRzr_PreReq1
get FeatureState=CXC4012493 featureState$ > $MotoRzr_PreReq2

pr upgradepackage=.*/2
if $nr_of_mos != 0
    $MotoRzr_Gen3 = Yes
fi

if MotoRzr_PreReq1 ~ 1 && $MotoRzr_PreReq2 ~ 1 && $MotoRzr_Gen3 ~ Yes
    UEGrp_MotoRzr
fi


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

from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base
from .tmo_data import global_amos_logic
import re


class nr_09a_BaseLine(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.addcell].index) == 0: return
        self.air_6648_6649 = len([True for _ in self.df_gnb_cell.frutypecix if
                                  len([radio for radio in _ if re.match('AIR.*64.*', radio)]) > 0]) > 0
        self.script_list += self.bl_start()
        self.script_list += global_amos_logic()
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
####:----------------> Pre Check <----------------:####
pr GNBDUFunction=1,NRCellDU=
if $nr_of_mos = 0
    print  ERROR: No NR cell defined !!!
    l-
    return
fi
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
        lines = ["""####:----------------> Parameter Setting <----------------:####"""]
        lines.extend(self.get_vswr_script())
        if 0 < self.df_gnb_cell.loc[self.df_gnb_cell.addcell].shape[0] == self.df_gnb_cell.shape[0]:
            lines.extend(self.get_node_certificate())
        lines.extend([F"""
####:----------------> Default Parameter Setting <----------------:####
set PowerSaving ranCompDeepSleepEnabled true

#### NR FR1 DL SCell Mitigation for SRS Antenna Switching in SpCell
set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base srsImpactHandling 1
st ^nrcelldu=O
if $nr_of_mos != 0
    set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base srsImpactHandling 0
fi

set BrM=1,BrmBackupManager=1,BrmBackupHousekeeping=1$ maxStoredManualBackups 20
set Fm=1$ heartbeatInterval 100
set GNBDUFunction=1,TermPointToGNBCUCP=1$ administrativeState 1
set GNBDUFunction=1,UeCC=1,Prescheduling=1,PreschedulingUeCfg=Base preschedulingUeMode 0

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
if $K_Cell_Present = 1
    set NRCellDU=[J|I|K] nrLteCoexistence false
    ## set GNBDUFunction=1,NRCellDU=K qRxLevMin -116
    set GNBDUFunction=1,Rrc=1$ n310 20
    set GNBCUCPFunction=1,QciProfileEndcConfigExt=1$ initialUplinkConf 0
    set GNBCUCPFunction=1$ nasInactivityTime 5
    set GNBCUUPFunction=1$ dcDlAggActTime 10
    set GNBCUCPFunction=1,AnrFunction=1,AnrFunctionNR=1,AnrFunctionNRUeCfg=Base anrRsrpThreshold -114
fi

####:----------------> N2 (N1900) <----------------:####
if $J_Cell_Present = 1
    set NRCellDU=[J|I|K] nrLteCoexistence false
    ## set GNBDUFunction=1,NRCellDU=J qRxLevMin -120
    set GNBDUFunction=1,NRCellDU=J pdcchLaBfGainFraction 0
    set GNBDUFunction=1,Rrc=1$ n310 20
    set GNBCUCPFunction=1,QciProfileEndcConfigExt=1$ initialUplinkConf 0
    set GNBCUCPFunction=1$ nasInactivityTime 10
    set GNBCUUPFunction=1$ dcDlAggActTime 1
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
if $J_Cell_Present = 1
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
        return lines

    def software_update(self):
        lines = []
        lines += ["""
####:----------------> Parameter Setting for 24Q2 SW <----------------:####
set GNBCUUPFunction=1,UeCC=1,UserPlaneProfile=Default,UserPlaneProfileUeCfg=Base dcDlAggCgPrio 1 
set GNBCUUPFunction=1,UeCC=1,UserPlaneProfile=Default,UserPlaneProfileUeCfg=Base dcDlAggAgeDiffPreferredCg 2 
set GNBCUUPFunction=1,UeCC=1,UserPlaneProfile=Default,UserPlaneProfileUeCfg=Base dlPdcpPreferredCg  1 
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_other aqmMode 1       
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_conversational_media aqmMode 2 
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_application_signaling aqmMode 0
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_other tDiscardDl 280       
set GNBCUUPFunction=1,UeCC=1,AqmCfg=Default_conversational_media tDiscardDl 80 
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
set GNBCUUPFunction=1,UeCC=1,Drb=Conversational_Video,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=Conversational_Video
set GNBCUUPFunction=1,UeCC=1,Drb=Real_Time_Gaming,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=Real_Time_Gaming
set GNBCUUPFunction=1,UeCC=1,Drb=Non-Conversational_Video,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=Non-Conversational_Video
set GNBCUUPFunction=1,UeCC=1,Drb=SD_2000,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_2000
set GNBCUUPFunction=1,UeCC=1,Drb=SD_3001,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_3001
set GNBCUUPFunction=1,UeCC=1,Drb=SD_3002,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_3002
set GNBCUUPFunction=1,UeCC=1,Drb=SD_6000,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_6000
set GNBCUUPFunction=1,UeCC=1,Drb=SD_6001,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=SD_6001
set GNBCUUPFunction=1,UeCC=1,Drb=Conversational_Video,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=default
set GNBCUUPFunction=1,UeCC=1,Drb=Real_Time_Gaming,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=default  
set GNBCUUPFunction=1,UeCC=1,Drb=Non-Conversational_Video,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_2000,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_3001,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_6000,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_6001,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set GNBCUUPFunction=1,UeCC=1,Drb=SD_3002,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default

set ,CUUP5qi=2 drbRef GNBCUUPFunction=1,UeCC=1,Drb=Conversational_Video
set ,CUUP5qi=3 drbRef GNBCUUPFunction=1,UeCC=1,Drb=Real_Time_Gaming
set ,CUUP5qi=4 drbRef GNBCUUPFunction=1,UeCC=1,Drb=Non-Conversational_Video
set CUUP5qiTable=SD_2000,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=SD_2000
set CUUP5qiTable=SD_3001,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=SD_3001
set CUUP5qiTable=SD_6000,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=SD_6000
set CUUP5qiTable=SD_6001,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=SD_6001
set CUUP5qiTable=SD_3002,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=SD_3002

set GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default dcDlAggAllowed true
set GNBCUUPFunction=1 altDepHServAdapUPProfEnabled true 

set GNBDUFunction=1,UeCC=1,AqmCfg=Default_other aqmMode 1       
set GNBDUFunction=1,UeCC=1,AqmCfg=Default_conversational_media aqmMode 2 
set GNBDUFunction=1,UeCC=1,AqmCfg=Default_application_signaling aqmMode 0
set GNBDUFunction=1,UeCC=1,AqmCfg=Default_other tDiscardDl 280       
set GNBDUFunction=1,UeCC=1,AqmCfg=Default_conversational_media tDiscardDl 80 
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
set  GNBDUFunction=1,UeCC=1,DrbUp=Conversational_Video,DrbUpUeCfg=Base aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=Conversational_Video
set  GNBDUFunction=1,UeCC=1,DrbUp=Real_Time_Gaming,DrbUpUeCfg=Base aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=Real_Time_Gaming
set  GNBDUFunction=1,UeCC=1,DrbUp=Non-Conversational_Video,DrbUpUeCfg=Base aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=Non-Conversational_Video
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_2000,DrbUpUeCfg=Base aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_2000
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_3001,DrbUpUeCfg=Base aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_3001
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_6000,DrbUpUeCfg=Base aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_6000
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_6001,DrbUpUeCfg=Base aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_6001
set  GNBDUFunction=1,UeCC=1,DrbUp=SD_3002,DrbUpUeCfg=Base aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=SD_3002
set ,DU5qi=2 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=Conversational_Video
set ,DU5qi=3 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=Real_Time_Gaming
set ,DU5qi=4 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=Non-Conversational_Video
set DU5qiTable=SD_2000,DU5qi=6 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=SD_2000
set DU5qiTable=SD_3001,DU5qi=6 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=SD_3001
set DU5qiTable=SD_6000,DU5qi=6 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=SD_6000
set DU5qiTable=SD_6001,DU5qi=6 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=SD_6001
set DU5qiTable=SD_3002,DU5qi=6 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=SD_3002

set GNBDUFunction=1 altDepHServAdapUPProfEnabled true

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

u-
l rm $undodelcommandfile $undocommandfile $undologfile

u+s
ldel DU5qiTable=$TID,DU5qi=9$
ldel CUUP5qiTable=$TID,CUUP5qi=9$
ldel CUCP5qiTable=$TID,CUCP5qi=9$
u-
l sed -i 's/5qi=9/5qi=129/g' $undocommandfile
l sed -i 's/profile5qi 9/profile5qi 129/g' $undocommandfile
l sed -i 's/schedulingProfileRef.*/schedulingProfileRef /g' $undocommandfile 
run $undocommandfile
l rm $undodelcommandfile $undocommandfile $undologfile

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

####:----------------> Parameter Setting for 24Q4 SW <----------------:####

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


####:----------------> Parameter Setting for 25Q2 SW <----------------:####
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
        # SW TMO_25_Q4
        if self.usid.client.software.swname[:9] > 'TMO_25_Q3':
            lines += [F"""
####:----------------> Parameter Setting for 25Q4 SW <----------------:####
################ Disabling NR PCI Conflict Reporting (STA-00628371) ################
if $GenCheck = Gen2
	set PciHandling=1 pciConflictHandlingEnabled false
fi

################ Advanced Unified Access Control (T-Priority) ################
################ Advanced Priority Based Access Control (T-Priority) ################
###### TDD Profile creation
func Create_TDD_CchLdProfile
	pr GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_TDD
	if $nr_of_mos = 0
		crn GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_TDD
		pdcchBlockingPuschLimit 65
		pdcchBlockingPdschLimit 50
		end
	else
		set GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_TDD pdcchBlockingPuschLimit 65
		set GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_TDD pdcchBlockingPdschLimit 50
	fi
	set NRCellDU=A cchLoadProfileRef GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_TDD
	$AUAC_APBAC_CcLdProfile_FuncExecuted = $AUAC_APBAC_CcLdProfile_FuncExecuted + $nr_of_mos_ok
endfunc

###### FDD Profile creation
func Create_FDD_CchLdProfile
	pr GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_FDD
	if $nr_of_mos = 0
		crn GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_FDD
		pdcchBlockingPuschLimit 65
		pdcchBlockingPdschLimit 50
		end
	else
		set GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_FDD pdcchBlockingPuschLimit 65
		set GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_FDD pdcchBlockingPdschLimit 50
	fi
	set NRCellDU=[IJK] cchLoadProfileRef GNBDUFunction=1,AdmissionControl=1,CchLoadProfile=Default_FDD
	$AUAC_APBAC_CcLdProfile_FuncExecuted = $AUAC_APBAC_CcLdProfile_FuncExecuted + $nr_of_mos_ok
endfunc

func AUAC_APBAC_Config
	##Advanced unified access control
	set FeatureState=CXC4012865 featureState 1
	##Advanced Priority-Based Admission Control
	set FeatureState=CXC4012872 featureState 1
	##Set the values as per T-Mobile PBL
	set1x GNBCUCPFunction=1,AdmissionControl=1,Uac=1,UacProfile=TMO_WPS,BarringGroup=WPS ccLoadBarringStart 55
	set1x GNBCUCPFunction=1,AdmissionControl=1,Uac=1,UacProfile=TMO_WPS,BarringGroup=WPS ccLoadBarringMax 95
	commit
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=Default ccLoadThreshold 98
endfunc

$AUAC_APBAC_CcLdProfile_FuncExecuted = 0
get FeatureState=CXC4012705 featureState$ > $CXC4012705_state
get FeatureState=CXC4012593 featureState$ > $CXC4012593_state
if $A_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $CXC4012705_state ~ 1 && $CXC4012593_state ~ 1
	Create_TDD_CchLdProfile
fi
if $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $CXC4012705_state ~ 1 && $CXC4012593_state ~ 1
    Create_FDD_CchLdProfile
fi
if $AUAC_APBAC_CcLdProfile_FuncExecuted > 0
    AUAC_APBAC_Config
fi

################ DCI Based RA Type 1 (Pcell and Internal Scell) * x80 ################
if $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
set FeatureState=CXC4012863 featureState 1
set GNBDUFunction=1,UeCC=1,ResourceAllocTypeDl=Default,ResourceAllocTypeDlUeCfg=Base prefUeResourceAllocDlTypeFr1 3
fi

################ RACH backoff (G3+ FDD and TDD) ################
get FieldReplaceableUnit productData RAN.*Processor.*6672
if $nr_of_mos != 0
$RP6672_Present_RACHbackoff = 1
else
$RP6672_Present_RACHbackoff = 0
fi

if $GenCheck = Gen3or4
scw RP3141:90,RP3142:5,RP2701:20,RP2702:0,RP2703:50,RP2861:12
fi

if $A_Cell_Present = 1 && $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $RP6672_Present_RACHbackoff = 1 && $QSH_Cell_Present = 0
	### TDD setting
	scw RP3155:11 NR-FR1-C2-TDD
	### FDD setting
	scw RP3155:7 NR-FR1-FDD
else if $A_Cell_Present = 1 && $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $RP6672_Present_RACHbackoff = 0 && $QSH_Cell_Present = 0
	### TDD setting
	scw RP3155:11 NR-FR1-C1-TDD
	### FDD setting
	scw RP3155:7 NR-FR1-C1-FDD
else if $A_Cell_Present = 1 && $IJK_Cell_Present = 0 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
	### TDD setting
	scw RP3155:11
else if $A_Cell_Present = 0 && $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
	### FDD setting
	scw RP3155:7
fi

################ defaultPagingCycle to 64 ################
set GNBDUFunction=1,Paging=1 defaultPagingCycle 64
################ BWP activation on FDD ################
set FeatureState=CXC4012606 featureState 1

################ Service Adaptive Massive MIMO* ################
func ServAdpMasMIMO_NR_FDD
	//Create new MOs for VoNR Devices
	cr GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=OneTxPort
	// Set non-default in new MOs
	set GNBDUFunction=1,UeCC=1,ulMimo=1,ulMimoUeCfg=OneTxPort ulLayerSwitchQualThresh 10000
	ServAdpMasMIMO_NR_FDD_MotoRazr25_VoNR
	// Migration setting
	set GNBDUFunction=1 altDepHMassiveMimoEnabled true
	set FeatureState=CXC4012851 featureState 1
endfunc

func ServAdpMasMIMO_NR_FDD_MotoRazr25_VoNR
	if $A_Cell_Present = 1 && $IJK_Cell_Present = 1
		// Assign UEBbProfiles to new MO structure
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default_FDD,UeBbProfileUeCfg=MotoRazr25 ulMimoUeCfgRef GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=OneTxPort
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default_FDD,UeBbProfileUeCfg=VoNR ulMimoUeCfgRef GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=OneTxPort
	else
		// Assign UEBbProfiles to new MO structure
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=MotoRazr25 ulMimoUeCfgRef GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=OneTxPort
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR ulMimoUeCfgRef GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=OneTxPort
	fi
endfunc

func ServAdpMasMIMO_NR_TDD
	// Create new MOs for VoNR and Hint Devices
	cr GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=VoNR
	cr GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=VoNR
	cr GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=VoNR
	cr GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=HSI
	cr GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=HSI
	cr GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=HSI
	// Set non-default in new MOs
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base speedAdvMuThresh 20
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base speedAdvSuThresh 30
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base advDlBfWhenAllSrsPortsUsable true
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base maxAllowedUeDlRatMuLayers 4
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=Base srsUeMode 2
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=VoNR speedAdvMuThresh 20
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=VoNR speedAdvSuThresh 30
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=VoNR advDlBfWhenAllSrsPortsUsable true
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=VoNR maxAllowedUeDlRatMuLayers 4
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=VoNR srsUeMode 2
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=VoNR srsImpactHandling 1
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=HSI speedAdvMuThresh 20
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=HSI speedAdvSuThresh 30
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=HSI advDlBfWhenAllSrsPortsUsable true
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=HSI maxAllowedUeDlRatMuLayers 4
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=HSI srsUeMode 2
	set GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=HSI srsImpactHandling 1
	ServAdpMasMIMO_NR_TDD_VoNR_HSI
	// Migration setting
	set GNBDUFunction=1 altDepHMassiveMimoEnabled true
	set FeatureState=CXC4012851 featureState 1
endfunc

func ServAdpMasMIMO_NR_TDD_VoNR_HSI
	if $A_Cell_Present = 1 && $IJK_Cell_Present = 1
		// Assign UEBbProfiles to new MO structure
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default_TDD,UeBbProfileUeCfg=VoNR dlMimoUeCfgRef GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=VoNR
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default_TDD,UeBbProfileUeCfg=VoNR ulMimoUeCfgRef GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=VoNR
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default_TDD,UeBbProfileUeCfg=VoNR ulWfPortSwitchUeCfgRef GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=VoNR
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default_TDD,UeBbProfileUeCfg=HSI dlMimoUeCfgRef GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=HSI
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default_TDD,UeBbProfileUeCfg=HSI ulMimoUeCfgRef GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=HSI
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default_TDD,UeBbProfileUeCfg=HSI ulWfPortSwitchUeCfgRef GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=HSI
	else
		// Assign UEBbProfiles to new MO structure
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR dlMimoUeCfgRef GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=VoNR
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR ulMimoUeCfgRef GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=VoNR
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR ulWfPortSwitchUeCfgRef GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=VoNR
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=HSI dlMimoUeCfgRef GNBDUFunction=1,UeCC=1,DlMimo=1,DlMimoUeCfg=HSI
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=HSI ulMimoUeCfgRef GNBDUFunction=1,UeCC=1,UlMimo=1,UlMimoUeCfg=HSI
		set GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=HSI ulWfPortSwitchUeCfgRef GNBDUFunction=1,UeCC=1,UlWfPortSwitch=1,UlWfPortSwitchUeCfg=HSI
	fi
endfunc

if $GenCheck = Gen3or4 && $IJK_Cell_Present = 1
	ServAdpMasMIMO_NR_FDD
fi

if $GenCheck = Gen3or4 && $A_Cell_Present = 1
	ServAdpMasMIMO_NR_TDD
fi

###################################################################################################################################################
###################################################################################################################################################

"""]
        # SW TMO_25_Q1
        if self.usid.client.software.swname[:9] > 'TMO_25_Q4':
            lines += ["""
#### 26.Q1
#### NR_LB & NR_MB
#### Adaptive SRB priority
func AdapSRBPriority_Config
	pr GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=WPS
	if $nr_of_mos = 0
		crn GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=WPS
		prefUeGroupList
		srbPriority 12
		ueConfGroupList 1
		ueGroupList
		end
	else
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=WPS prefUeGroupList
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=WPS srbPriority 12
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=WPS ueConfGroupList 1
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=WPS ueGroupList
	fi
	pr GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=E911_Users
	if $nr_of_mos = 0
		crn GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=E911_Users
		prefUeGroupList
		srbPriority 10
		ueConfGroupList 2
		ueGroupList
		end
	else
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=E911_Users prefUeGroupList
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=E911_Users srbPriority 10
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=E911_Users ueConfGroupList 2
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=E911_Users ueGroupList
	fi
	pr GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=VoNR
	if $nr_of_mos = 0
		crn GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=VoNR
		prefUeGroupList
		srbPriority 8
		ueConfGroupList 3
		ueGroupList
		end
	else
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=VoNR prefUeGroupList
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=VoNR srbPriority 8
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=VoNR ueConfGroupList 3
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=VoNR ueGroupList
	fi
	pr GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=Slicing_Users
	if $nr_of_mos = 0
		crn GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=Slicing_Users
		prefUeGroupList
		srbPriority 6
		ueConfGroupList 5
		ueGroupList
		end
	else
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=Slicing_Users prefUeGroupList
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=Slicing_Users srbPriority 6
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=Slicing_Users ueConfGroupList 5
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=Slicing_Users ueGroupList
	fi
	pr GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=SA_Traffic
	if $nr_of_mos = 0
		crn GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=SA_Traffic
		prefUeGroupList
		srbPriority 4
		ueConfGroupList 4
		ueGroupList
		end
	else
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=SA_Traffic prefUeGroupList
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=SA_Traffic srbPriority 4
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=SA_Traffic ueConfGroupList 4
		set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=SA_Traffic ueGroupList
	fi
endfunc

if $GenCheck = Gen2
   $E911_selCrit = rrcEstResCause==emergency || arp==6
else if $GenCheck = Gen3or4
   $E911_selCrit = rrcEstResCause==emergency || arp==6 || pagingPrio==6
fi

if $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
	set FeatureState=CXC4012780 featureState 1
	set GNBDUFunction=1,UeCC=1,SrbPriority=Default ueConfGroupType 2
	set GNBDUFunction=1,UeCC=1,SrbPriority=Default,SrbPriorityUeCfg=Base srbPriority 2
	AdapSRBPriority_Config
fi

pr GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=SA_Traffic
if $nr_of_mos = 0
	crn GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=SA_Traffic
	chipsetRef
	imeiSvRef
	selectionCriteria 5qi>=5
	ueAdmissionGroupId 4
	ueAdmissionGroupPriority 60
	userLabel SA_Traffic
	end
else
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=SA_Traffic chipsetRef
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=SA_Traffic imeiSvRef
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=SA_Traffic selectionCriteria 5qi>=5
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=SA_Traffic ueAdmissionGroupId 4
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=SA_Traffic ueAdmissionGroupPriority 60
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=SA_Traffic userLabel SA_Traffic
fi

pr GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=VoNR
if $nr_of_mos = 0
	crn GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=VoNR
	chipsetRef
	imeiSvRef
	selectionCriteria 5qi==1 || rrcEstResCause==mo-VoiceCall
	ueAdmissionGroupId 3
	ueAdmissionGroupPriority 90
	userLabel VoNR
	end
else
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=VoNR chipsetRef
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=VoNR imeiSvRef
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=VoNR selectionCriteria 5qi==1 || rrcEstResCause==mo-VoiceCall
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=VoNR ueAdmissionGroupId 3
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=VoNR ueAdmissionGroupPriority 90
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=VoNR userLabel VoNR
fi

pr GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=Slicing_Users
if $nr_of_mos = 0
	crn GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=Slicing_Users
	chipsetRef
	imeiSvRef
	selectionCriteria snssai==0x010007D0 || snssai==0x010007D1 || snssai==0x01000BB8 || snssai==0x01000BB9 || snssai==0x01000BBA || snssai==0x01000FA0 || snssai==0x01001388 || snssai==0x01001389 || snssai==0x0100138A || snssai==0x01001770 || snssai==0x01001771 || snssai==0x01001F40 || snssai==0x01001F41 || snssai==0x01002328 || snssai==0x01002329 || snssai==0x0100232A || snssai==0x01002710 || snssai==0x01002711
	ueAdmissionGroupId 5
	ueAdmissionGroupPriority 80
	userLabel Slicing_Users
	end
else
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=Slicing_Users chipsetRef
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=Slicing_Users imeiSvRef
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=Slicing_Users selectionCriteria snssai==0x010007D0 || snssai==0x010007D1 || snssai==0x01000BB8 || snssai==0x01000BB9 || snssai==0x01000BBA || snssai==0x01000FA0 || snssai==0x01001388 || snssai==0x01001389 || snssai==0x0100138A || snssai==0x01001770 || snssai==0x01001771 || snssai==0x01001F40 || snssai==0x01001F41 || snssai==0x01002328 || snssai==0x01002329 || snssai==0x0100232A || snssai==0x01002710 || snssai==0x01002711
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=Slicing_Users ueAdmissionGroupId 5
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=Slicing_Users ueAdmissionGroupPriority 80
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=Slicing_Users userLabel Slicing_Users
fi

pr GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users
if $nr_of_mos = 0
	crn GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users
	chipsetRef
	imeiSvRef
	selectionCriteria $E911_selCrit
	ueAdmissionGroupId 2
	ueAdmissionGroupPriority 95
	userLabel E911_Users
	end
else
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users chipsetRef
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users imeiSvRef
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users selectionCriteria $E911_selCrit
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users ueAdmissionGroupId 2
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users ueAdmissionGroupPriority 95
	set GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users userLabel E911_Users
fi

pr GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=E911_Users
if $nr_of_mos = 0
	crn GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=E911_Users
	prefUeGroupList
	ueConfGroupList 2
	ueGroupList
	uePriority 101
	end
else
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=E911_Users prefUeGroupList
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=E911_Users ueConfGroupList 2
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=E911_Users ueGroupList
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=E911_Users uePriority 101
fi

pr GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=VoNR
if $nr_of_mos = 0
	crn GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=VoNR
	prefUeGroupList
	ueConfGroupList 3
	ueGroupList
	uePriority 110
	end
else
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=VoNR prefUeGroupList
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=VoNR ueConfGroupList 3
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=VoNR ueGroupList
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=VoNR uePriority 110
fi

pr GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=SA_Traffic
if $nr_of_mos = 0
	crn GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=SA_Traffic
	prefUeGroupList
	ueConfGroupList 4
	ueGroupList
	uePriority 200
	end
else
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=SA_Traffic prefUeGroupList
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=SA_Traffic ueConfGroupList 4
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=SA_Traffic ueGroupList
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=SA_Traffic uePriority 200
fi

pr GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=Slicing_Users
if $nr_of_mos = 0
	crn GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=Slicing_Users
	prefUeGroupList
	ueConfGroupList 5
	ueGroupList
	uePriority 120
	end
else
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=Slicing_Users prefUeGroupList
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=Slicing_Users ueConfGroupList 5
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=Slicing_Users ueGroupList
	set GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=Slicing_Users uePriority 120
fi



#### NR_LB
#### NR Data Aware Mobility
mr bwTrigISHoEnabled_TrStSaCellProfileUeCfg
ma bwTrigISHoEnabled_TrStSaCellProfileUeCfg TrStSaCellProfile=K.*,TrStSaCellProfileUeCfg=Base bwTrigISHoEnabled true
if $nr_of_mos > 0
	$bwTrigISHoEnabled_true = yes
fi
if $GenCheck = Gen3or4 && $bwTrigISHoEnabled_true = yes && $QSH_Cell_Present = 0
	set FeatureState=CXC4012736 featureState 1
	set bwTrigISHoEnabled_TrStSaCellProfileUeCfg dataAwareMobLowDlThpThr 3000
	set bwTrigISHoEnabled_TrStSaCellProfileUeCfg dataAwareMobLowUlThpThr 500
	set bwTrigISHoEnabled_TrStSaCellProfileUeCfg deprioritisationModeAtRwr 1
	set bwTrigISHoEnabled_TrStSaCellProfileUeCfg deprioritisationTimer 5
else if $GenCheck = Gen2 && $bwTrigISHoEnabled_true = yes && $QSH_Cell_Present = 0
	set FeatureState=CXC4012736 featureState 1
	set bwTrigISHoEnabled_TrStSaCellProfileUeCfg dataAwareMobLowDlThpThr 3000
	set bwTrigISHoEnabled_TrStSaCellProfileUeCfg dataAwareMobLowUlThpThr 500
fi


#### NR_MB
#### handling for Custom Channel Bandwidth related to IB64523 - Part 1 of 3
get NRSectorCarrier=25 customChannelBw$  [495|555|380|880]
if $nr_of_mos > 0
	mr TrsConfigMode_Group
	mr TrsConfigMode_Group_Unlocked
	ma TrsConfigMode_Group NRCellDU=A TrsConfigMode 3
	ma TrsConfigMode_Group_Unlocked TrsConfigMode_Group administrativeState 1
	set1x TrsConfigMode_Group TrsConfigMode 0
	set1x TrsConfigMode_Group_Unlocked administrativeState 0
	commit
fi

#### handling for Custom Channel Bandwidth related to IB64523 - Part 2 of 3
get NRSectorCarrier=25 customChannelBw$  [495|555|380|880]
if $nr_of_mos > 0
	ma NRSectorCarrier25_unlock NRSectorCarrier=25 administrativeState 1
	bl NRSectorCarrier25_unlock
	ma NRSectorBw_495 NRSectorCarrier=25 customChannelBw$ 495
	ma NRSectorBw_555 NRSectorCarrier=25 customChannelBw$ 555
	ma NRSectorBw_380 NRSectorCarrier=25 customChannelBw$ 380
	ma NRSectorBw_880 NRSectorCarrier=25 customChannelBw$ 880
	set NRSectorBw_495 customChannelBw
	set NRSectorBw_555 customChannelBw
	set NRSectorBw_380 customChannelBw
	set NRSectorBw_880 customChannelBw
	set NRSectorBw_495 customChannelBw 495
	set NRSectorBw_555 customChannelBw 555
	set NRSectorBw_380 customChannelBw 380
	set NRSectorBw_880 customChannelBw 880
	deb NRSectorCarrier25_unlock
fi

#### handling for Custom Channel Bandwidth related to IB64523 - Part 3 of 3
get NRSectorCarrier=25 customChannelBw$  [495|555|380|880]
if $nr_of_mos > 0
	set TrsConfigMode_Group TrsConfigMode 3
	set TrsConfigMode_Group_Unlocked administrativeState 1
fi

#### NR UL Coordinated Multi-Point Reception (Intra-site TDD)*
func ULComp
	mr ULComp_NRCellDU_A
	mr ULComp_NRCellCU_A_Air
	ma ULComp_NRCellDU_A GNBDUFunction=1,NRCellDU=A
	for $mo in ULComp_NRCellDU_A
		lk $mo
		$rdn = rdn($mo)
		get lk_group ^MulticastAntennaBranchid$
		if $nr_of_mos > 0
			return
		fi
		get lk_group ^transceiverid$
		if $nr_of_mos > 0
			mr hget_group
			get $rdn nRCellDUId > $nRCell_Id
			hget GNBCUCPFunction=1,NRCellCU nRCellCUId $nRCell_Id
			ma ULComp_NRCellCU_A_Air hget_group
		fi
	done
	mr ULComp_NRCellCU_A_hget_group
	for $mo in ULComp_NRCellCU_A_Air
		$ULComp_NRCellCU_A_RDN = rdn($mo)
		$ULComp_NRCellCU_A1 = `$gawk -v s="$ULComp_NRCellCU_A_RDN" 'BEGIN{ print substr(s,1,length(s)-2) "." substr(s,length(s),1) }'`
		mr hget_group
		hget $ULComp_NRCellCU_A_RDN,NRCellRelation= nRCellRef $ULComp_NRCellCU_A1
		if $nr_of_mos > 0
			ma ULComp_NRCellCU_A_hget_group hget_group
		fi
	done
	pr ULComp_NRCellCU_A_hget_group
	if $nr_of_mos > 0
		set FeatureState=CXC4012816 featureState 1
		set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base uplinkCompUserSelSinrHyst 30
		set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base uplinkCompUserSelSinrThresh 250
		set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base uplinkCompUeEnabled true
		set ULComp_NRCellCU_A_hget_group ulCompCellCandidate 1
	fi
endfunc

if $A_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
	ULComp
fi

            """]
        # SW TMO_25_Q2
        if self.usid.client.software.swname[:9] > 'TMO_26_Q1':
            lines += ["""
//=============================================================================
// NR Pre-emptive Mobility Management - Barred 2nd Carrier SCell Enablement
//=============================================================================

// Enable manualBarringReportEnabled at node level on TDD only
pr NRCelldu=A
if $GenCheck = Gen3or4 && $nr_of_mos > 0
  set GNBCUCPFunction=1 manualBarringReportEnabled true
fi
  
if $GenCheck = Gen3or4
  // Group 2nd carrier barred cells
  ma 2ndC_barred_cells NRCellDU=[AIJK].*2$ cellBarred$ 0
  
  // Step 3: function call
  PreempMob
  
  // Verify
  hget UeMC=1,UeMCCellProfile= connModeUeAllowedToBarredCellType
  mr 2ndC_barred_cells
fi

##################################################################################################################

//##NEXT_CHANGE##

//##################################################################################################################
//# NR BSW Configuration that DOES NOT require cells to be in LOCKED state
//##################################################################################################################

####################################################################################################################################################
## NR Robust PDCCH Link Adaptation
####################################################################################################################################################

##################################################
## Creating LinkAdaptationUeCfg VoNR if missing
##################################################
func Create_VoNR

pr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR$
if $nr_of_mos = 0
   cr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
   ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,DlLinkAdaptation=1
   ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,UlLinkAdaptation=1
   ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,PdcchLinkAdaptation=1
   set UeBbProfile=Default,UeBbProfileUeCfg=VoNR LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
   set UeBbProfile=Default,UeBbProfileUeCfg=Base LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base
fi

if $GenCheck = Gen3or4
   ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=VoNR
   ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=VoNR,UlService=1
else if $GenCheck = Gen2
   cr GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=VoNR
fi

endfunc

func check_LinkAdaptationUeCfg

ma LinkAdaptationUeCfg_inuse LinkAdaptationUeCfg=
mr LinkAdaptationUeCfg_inuse LinkAdaptationUeCfg=Base
mr LinkAdaptationUeCfg_inuse LinkAdaptationUeCfg=VoNR

$min_lim = 0
if $PDCCHOLA_UeBBProfile_Var_FDD = UeBbProfile=Default_FDD
   $min_lim = 5
else if $PDCCHOLA_UeBBProfile_Var_FDD = UeBbProfile=Default
   $min_lim = 2
fi

pr LinkAdaptationUeCfg_inuse
$nr_for_BV = 8 - $nr_of_mos

if $nr_for_BV < $min_lim
   $Max_LinkAdaptationUeCfg = yes
   return
fi

pr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
if $nr_of_mos = 0
   Create_VoNR
else
   set UeBbProfile=Default,UeBbProfileUeCfg=VoNR LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
   set UeBbProfile=Default,UeBbProfileUeCfg=Base LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base
fi

endfunc

func LinkAdaptationUeCfg_parm_default

$LinkAdaptationUeCfg_parm = $1$
$LinkAdaptationUeCfg_parm2 = $1

set $LinkAdaptationUeCfg_parm                          dlMaxBitrate                           -1
set $LinkAdaptationUeCfg_parm                          dlMcsTable                             1
set $LinkAdaptationUeCfg_parm                          linkAdaptationUeMode                   0
set $LinkAdaptationUeCfg_parm                          ulMcsTable                             1

set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlBlerTarget                           1000
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlBlerTargetExtended                   -1
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlDownStep                             0
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlMaxMcsIndex                          27
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlMaxTbs                               0
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlSinrBackoff                          0

set $LinkAdaptationUeCfg_parm2,PdcchLinkAdaptation=1    pdcchLaSinrUeOffset                    0
set $LinkAdaptationUeCfg_parm2,PdcchLinkAdaptation=1    pdcchRobustLaDtxTarget                 10
set $LinkAdaptationUeCfg_parm2,PdcchLinkAdaptation=1    pdcchRobustLaEnabled                   false

set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulBlerTarget                           1000
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulBlerTargetExtended                   -1
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulDownStep                             0
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulMaxMcsIndex                          27
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulMinTbs                               96
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulSinrBackoff                          0

endfunc

###############################################################
## Profile LinkAdaptationUeCfg VoNR deletion for Trimode Nodes
###############################################################
func del_VoNR

pr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR$

if $nr_of_mos != 0
   ma UeBbProfileUeCfg_VoNR UeBbProfileUeCfg= LinkAdaptationUeCfgRef LinkAdaptationUeCfg=VoNR$
   set UeBbProfileUeCfg_VoNR LinkAdaptationUeCfgRef
   ldel LinkAdaptationUeCfg=VoNR$
   lt all
fi

endfunc

func FIX_LinkAdaptationUeCfg

if $Max_LinkAdaptationUeCfg = yes
   return
fi

pr LinkAdaptationUeCfg=Base_TDD
if $nr_of_mos = 0
   $LinkAdaptationUeCfg_Base_TDD = no
else
   $LinkAdaptationUeCfg_Base_TDD = yes
fi

pr LinkAdaptationUeCfg=Base_FDD
if $nr_of_mos = 0
   $LinkAdaptationUeCfg_Base_FDD = no
else
   $LinkAdaptationUeCfg_Base_FDD = yes
fi

pr LinkAdaptationUeCfg=VoNR_TDD
if $nr_of_mos = 0
   $LinkAdaptationUeCfg_VoNR_TDD = no
else
   $LinkAdaptationUeCfg_VoNR_TDD = yes
fi

pr LinkAdaptationUeCfg=VoNR_FDD
if $nr_of_mos = 0
   $LinkAdaptationUeCfg_VoNR_FDD = no
else
   $LinkAdaptationUeCfg_VoNR_FDD = yes
fi

### Create LinkAdaptationUeCfg_VoNR_TDD
    if $A_Cell_Present = 1 && $LinkAdaptationUeCfg_VoNR_TDD = no
      u+s $nodename_LinkAdaptationUeCfg
      LinkAdaptationUeCfg_parm_default LinkAdaptationUeCfg=VoNR
      u-
      l sed 's/LinkAdaptationUeCfg=VoNR/LinkAdaptationUeCfg=VoNR_TDD/g' $undocommandfile > $nodename_LinkAdaptationUeCfg_TDD.mos
      cr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_TDD

      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_TDD,DlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_TDD,UlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_TDD,PdcchLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=VoNR_TDD
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=VoNR_TDD,UlService=1

      run $nodename_LinkAdaptationUeCfg_TDD.mos
      l rm $nodename_LinkAdaptationUeCfg_TDD.mos $undodelcommandfile $undologfile $undocommandfile
      set $PDCCHOLA_UeBBProfile_Var_TDD,UeBbProfileUeCfg=VoNR LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_TDD
    else if $A_Cell_Present = 1 && $LinkAdaptationUeCfg_VoNR_TDD = yes
      set $PDCCHOLA_UeBBProfile_Var_TDD,UeBbProfileUeCfg=VoNR LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_TDD
    fi

### Create LinkAdaptationUeCfg_VoNR_FDD
    if $IJK_Cell_Present = 1 && $LinkAdaptationUeCfg_VoNR_FDD = no
      u+s $nodename_LinkAdaptationUeCfg
      LinkAdaptationUeCfg_parm_default LinkAdaptationUeCfg=VoNR
      u-
      l sed 's/LinkAdaptationUeCfg=VoNR/LinkAdaptationUeCfg=VoNR_FDD/g' $undocommandfile > $nodename_LinkAdaptationUeCfg_FDD.mos
      del_VoNR
      cr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_FDD

      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_FDD,DlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_FDD,UlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_FDD,PdcchLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=VoNR_FDD
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=VoNR_FDD,UlService=1

      run $nodename_LinkAdaptationUeCfg_FDD.mos
      l rm $nodename_LinkAdaptationUeCfg_FDD.mos $undodelcommandfile $undologfile $undocommandfile
      set $PDCCHOLA_UeBBProfile_Var_FDD,UeBbProfileUeCfg=VoNR LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_FDD
    else if $IJK_Cell_Present = 1 && $LinkAdaptationUeCfg_VoNR_FDD = yes
      del_VoNR
      set $PDCCHOLA_UeBBProfile_Var_FDD,UeBbProfileUeCfg=VoNR LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR_FDD
    fi

### Create LinkAdaptationUeCfg_Base_TDD
    if $A_Cell_Present = 1 && $LinkAdaptationUeCfg_Base_TDD = no
      u+s $nodename_LinkAdaptationUeCfg
      LinkAdaptationUeCfg_parm_default LinkAdaptationUeCfg=Base
      u-
      l sed 's/LinkAdaptationUeCfg=Base/LinkAdaptationUeCfg=Base_TDD/g' $undocommandfile > $nodename_LinkAdaptationUeCfg_TDD.mos
      cr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD

      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD,DlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD,UlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD,PdcchLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=Base_TDD
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=Base_TDD,UlService=1

      run $nodename_LinkAdaptationUeCfg_TDD.mos
      l rm $nodename_LinkAdaptationUeCfg_TDD.mos $undodelcommandfile $undologfile $undocommandfile
      set $PDCCHOLA_UeBBProfile_Var_TDD,UeBbProfileUeCfg=Base LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD
    else if $A_Cell_Present = 1 && $LinkAdaptationUeCfg_Base_TDD = yes
      set $PDCCHOLA_UeBBProfile_Var_TDD,UeBbProfileUeCfg=Base LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD
    fi

### Create LinkAdaptationUeCfg_Base_FDD
    if $IJK_Cell_Present = 1 && $LinkAdaptationUeCfg_Base_FDD = no
      u+s $nodename_LinkAdaptationUeCfg
      LinkAdaptationUeCfg_parm_default LinkAdaptationUeCfg=Base
      u-
      l sed 's/LinkAdaptationUeCfg=Base/LinkAdaptationUeCfg=Base_FDD/g' $undocommandfile > $nodename_LinkAdaptationUeCfg_FDD.mos
      cr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_FDD

      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_FDD,DlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_FDD,UlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_FDD,PdcchLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=Base_FDD
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=Base_FDD,UlService=1

      run $nodename_LinkAdaptationUeCfg_FDD.mos
      l rm $nodename_LinkAdaptationUeCfg_FDD.mos $undodelcommandfile $undologfile $undocommandfile
      set $PDCCHOLA_UeBBProfile_Var_FDD,UeBbProfileUeCfg=Base LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_FDD
    else if $IJK_Cell_Present = 1 && $LinkAdaptationUeCfg_Base_FDD = yes
      set $PDCCHOLA_UeBBProfile_Var_FDD,UeBbProfileUeCfg=Base LinkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_FDD
    fi

endfunc

func PDCCHOLA_TriMode_Precheck

$PDCCHOLA_Precheck_Pass = yes

pr UeBbProfile=Default_FDD
if $nr_of_mos = 0
   $PDCCHOLA_Precheck_Pass = no
   return
fi

pr UeBbProfile=Default_TDD
if $nr_of_mos = 0
   $PDCCHOLA_Precheck_Pass = no
   return
fi

pr UeBbProfile=Default_FDD,UeBbProfileUeCfg=VoNR
if $nr_of_mos = 0
   $PDCCHOLA_Precheck_Pass = no
   return
fi

pr UeBbProfile=Default_TDD,UeBbProfileUeCfg=VoNR
if $nr_of_mos = 0
   $PDCCHOLA_Precheck_Pass = no
   return
fi

pr UeBbProfile=Default_FDD,UeBbProfileUeCfg=Base
if $nr_of_mos = 0
   $PDCCHOLA_Precheck_Pass = no
   return
fi

pr UeBbProfile=Default_TDD,UeBbProfileUeCfg=Base
if $nr_of_mos = 0
   $PDCCHOLA_Precheck_Pass = no
   return
fi

endfunc

func PDCCHOLA_Single_Precheck

$PDCCHOLA_Precheck_Pass = yes

pr UeBbProfile=Default,UeBbProfileUeCfg=Base$
if $nr_of_mos = 0
   $PDCCHOLA_Precheck_Pass = no
   return
fi

pr UeBbProfile=Default,UeBbProfileUeCfg=VoNR$
if $nr_of_mos = 0
   $PDCCHOLA_Precheck_Pass = no
   return
fi

endfunc

func PDCCHOLA_TriMode_Config

$PDCCHOLA_UeBBProfile_Var_FDD = UeBbProfile=Default_FDD
$PDCCHOLA_UeBBProfile_Var_TDD = UeBbProfile=Default_TDD
check_LinkAdaptationUeCfg
FIX_LinkAdaptationUeCfg

endfunc

func PDCCHOLA_SingleMode_Config

$PDCCHOLA_UeBBProfile_Var_FDD = UeBbProfile=Default
$PDCCHOLA_UeBBProfile_Var_TDD = UeBbProfile=Default
check_LinkAdaptationUeCfg

endfunc

func PDCCHOLA_Activate

#Disable Prototype version
set SystemFunctions=1,Lm=1,FeatureState=CXC4012679 featureState 0

ma UeBbProfileUeCfg_PrototypeConfigUeCfg_base UeBbProfileUeCfg
mr UeBbProfileUeCfg_PrototypeConfigUeCfg_base UeBbProfileUeCfg= prototypeConfigUeCfgRef base

pr UeBbProfileUeCfg_PrototypeConfigUeCfg_base
if $nr_of_mos > 0
  for $mo in UeBbProfileUeCfg_PrototypeConfigUeCfg_base
     get $mo prototypeConfigUeCfgRef > $prototypeConfigUeCfg_to_del
     set $mo prototypeConfigUeCfgRef GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=Base
     rdel $prototypeConfigUeCfg_to_del
  done
fi

### Activate Commercial version
set SystemFunctions=1,Lm=1,FeatureState=CXC4012873 featureState 1
lset GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base pdcchRobustLaEnabled true
lset GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR pdcchRobustLaEnabled true

### FDD Configuration
if $IJK_Cell_Present = 1
#FDD eMBB
   get $PDCCHOLA_UeBBProfile_Var_FDD,UeBbProfileUeCfg=Base LinkAdaptationUeCfgref > $LinkAdaptationUeCfg_FDD_Base
   set $LinkAdaptationUeCfg_FDD_Base,PdcchLinkAdaptation=1 pdcchRobustLaDtxTarget 10
#FDD VoNR
   get $PDCCHOLA_UeBBProfile_Var_FDD,UeBbProfileUeCfg=VoNR LinkAdaptationUeCfgref > $LinkAdaptationUeCfg_FDD_VoNR
   set $LinkAdaptationUeCfg_FDD_VoNR,PdcchLinkAdaptation=1 pdcchRobustLaDtxTarget 9
fi

### TDD Configuration
if $A_Cell_Present = 1
#TDD eMBB
   get $PDCCHOLA_UeBBProfile_Var_TDD,UeBbProfileUeCfg=Base LinkAdaptationUeCfgref > $LinkAdaptationUeCfg_TDD_Base
   set $LinkAdaptationUeCfg_TDD_Base,PdcchLinkAdaptation=1 pdcchRobustLaDtxTarget 20
#TDD VoNR
   get $PDCCHOLA_UeBBProfile_Var_TDD,UeBbProfileUeCfg=VoNR LinkAdaptationUeCfgref > $LinkAdaptationUeCfg_TDD_VoNR
   set $LinkAdaptationUeCfg_TDD_VoNR,PdcchLinkAdaptation=1 pdcchRobustLaDtxTarget 10
fi

#Configuration of SDs if exist
pr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=SD.*
if $nr_of_mos > 0
   set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=SD.*,PdcchLinkAdaptation=1 pdcchRobustLaEnabled true 
   set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=SD.*,PdcchLinkAdaptation=1 pdcchRobustLaDtxTarget 10 
fi

endfunc

####################################################################################################################################################
## Execution
####################################################################################################################################################

$NrServAdaptiveLinkAdaptation_CXC = 0
get FeatureState=CXC4012637 featureState$ 1
if $nr_of_mos > 0
   $NrServAdaptiveLinkAdaptation_CXC = 1
fi

$Max_LinkAdaptationUeCfg = no

if $NrServAdaptiveLinkAdaptation_CXC = 1 && $QSH_Cell_Present = 0 && $A_Cell_Present = 1 && $IJK_Cell_Present = 1
   PDCCHOLA_TriMode_Precheck
else if $NrServAdaptiveLinkAdaptation_CXC = 1 && $QSH_Cell_Present = 0
   PDCCHOLA_Single_Precheck
fi

if $NrServAdaptiveLinkAdaptation_CXC = 1 && $QSH_Cell_Present = 0 && $A_Cell_Present = 1 && $IJK_Cell_Present = 1 && $PDCCHOLA_Precheck_Pass = yes
   PDCCHOLA_TriMode_Config
else if $NrServAdaptiveLinkAdaptation_CXC = 1 && $QSH_Cell_Present = 0 && $PDCCHOLA_Precheck_Pass = yes
   PDCCHOLA_SingleMode_Config
fi

if $Max_LinkAdaptationUeCfg = no && $PDCCHOLA_Precheck_Pass = yes && $NrServAdaptiveLinkAdaptation_CXC = 1 && $QSH_Cell_Present = 0
   PDCCHOLA_Activate
fi

####################################################################################################################################################
## QoS-controlled SR scheduling operation with RRP
####################################################################################################################################################

func SrRrpFeatureCheck

$SrRrp_CXC4012559_Active = 0
get FeatureState=CXC4012559 featureState$ 1
if $nr_of_mos > 0
$SrRrp_CXC4012559_Active = 1
fi

$SrRrp_CXC4012475_Active = 0
get FeatureState=CXC4012475 featureState$ 1
if $nr_of_mos > 0
$SrRrp_CXC4012475_Active = 1
fi

$SrRrp_srHandlingMode_OK = 0
get GNBDUFunction=1,UeCC=1,SrHandling=.*,SrHandlingUeCfg=Base srHandlingMode$ 1
if $nr_of_mos > 0
$SrRrp_srHandlingMode_OK = 1
fi

endfunc

SrRrpFeatureCheck

# Configure only cells where nrRrpEnabled=true, if all conditions met
if $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $SrRrp_CXC4012559_Active = 1 && $SrRrp_CXC4012475_Active = 1 && $SrRrp_srHandlingMode_OK = 1
   mr SrRrp_nrRrpCells
   ma SrRrp_nrRrpCells GNBDUFunction=1,NRCellDU=
   mr SrRrp_nrRrpCells GNBDUFunction=1,NRCellDU= nrRrpEnabled false
   set SrRrp_nrRrpCells srRrpPriorityAlignment 1
fi

####################################################################################################################################################
## Alternate UE specific and Cell common Scrambling Id during RRC Resume and RRE procedures (IB44714 TR solution - RRC Inactive E/// side mitigation)
####################################################################################################################################################

if $GenCheck = Gen3or4
   scw RP3535:1
fi

####################################################################################################################################################
## Reduced SCell Activation Time (CA Activation Latency improvement)
####################################################################################################################################################

if $GenCheck = Gen3or4
   set featureState=CXC4012864 FeatureState 1
fi

####################################################################################################################################################
## NR Advance UE location support & UL angle of arrival for Macro positioning & High-Resolution Timing Advance for Macro Positioning
####################################################################################################################################################

if $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
	### Activate Pre-Requisite feature NR Advance UE Location Support
	set SystemFunctions=1,Lm=1,FeatureState=CXC4012681 featureState 1

	### Activate UL Angle of Arrival
	set SystemFunctions=1,Lm=1,FeatureState=CXC4012770 featureState 1

	### Activate High-Resolution TA
	set SystemFunctions=1,Lm=1,FeatureState=CXC4012769 featureState 1

	#### advUePosMode is set to 1[All] to mesure RSRP, TA andd UL AoA ####
	set NRCellCU=[AIJK] advUePosMode 1

else if $GenCheck = Gen2 && $QSH_Cell_Present = 0

	### Activate Pre-Requisite feature NR Advance UE Location Support
	set SystemFunctions=1,Lm=1,FeatureState=CXC4012681 featureState 1

	#### advUePosMode is set to 1[All] to mesure RSRP, TA andd UL AoA ####
	set NRCellCU=[AIJK] advUePosMode 1
fi

####################################################################################################################################################
## RRC Inactive
####################################################################################################################################################

set FeatureState=CXC4012550 featurestate 1
set RrcInactiveProfileUeCfg=Base rrcInactiveStateSupport true
set RrcInactiveProfileUeCfg=Base periodicRnaUpdateCount 1
set RrcInactiveProfileUeCfg=Base periodicRnaUpdateTimer 60

mr inactiveMO
ma inactiveMO UeServiceGroupDefinition ueServiceGroupId 6
del inactiveMO

crn GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=RRCinactive_ProblemDevice 
selectionCriteria imeitac=={35615888,35686219,35885367,01651900,35557411,35557511,35557311,35150588,35557211,86031607,86935007,86250307,86355007,35477322}
ueServiceGroupId 6
ueServiceGroupPriority 125
userLabel RRCinactiveBlocklist
end

mr blocklistMO
ma blocklistMO RrcInactiveProfileUeCfg rrcInactiveProfileUeCfgId !Base
del blocklistMO

crn GNBCUCPFunction=1,UeCC=1,RrcInactiveProfile=Default,RrcInactiveProfileUeCfg=blocklist
rrcInactiveStateSupport false
ueConfGroupList 6
end

####################################################################################################################################################
## NR PUCCH Closed-Loop Power Control Low/Mid-band
####################################################################################################################################################

$CLPC_FDD_PCUeCfg_Name = Base_FDD
$CLPC_PZERO_N41 = -110

func CLPC_Precheck
$CLPC_PCUeCfg_Present = no
$CLPC_Precheck_Pass   = no
pr GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=1
if $nr_of_mos = 0
  return
fi
$CLPC_PCUeCfg_Present = yes
pr UeBbProfile=Default_FDD
if $nr_of_mos = 0
  return
fi
pr UeBbProfile=Default_TDD
if $nr_of_mos = 0
  return
fi
$CLPC_Precheck_Pass = yes
endfunc

func CLPC_PZERONOMPUCCH_N41_SET
mr CLPC_NR41Cells
ma CLPC_NR41Cells GNBDUFunction=1,NRCellDU=A
pr CLPC_NR41Cells
if $nr_of_mos != 0
  set CLPC_NR41Cells pZeroNomPucch $CLPC_PZERO_N41
fi
endfunc

func CLPC_SPLIT_PCUECFG
cr GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=$CLPC_FDD_PCUeCfg_Name
set GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=$CLPC_FDD_PCUeCfg_Name pZeroNomPucchOffset 0
set GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=$CLPC_FDD_PCUeCfg_Name pZeroNomPuschOffset 0
set GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=$CLPC_FDD_PCUeCfg_Name puschPowerControlModeFr1 1
set GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=$CLPC_FDD_PCUeCfg_Name puschPowerControlModeFr2 1
set GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=$CLPC_FDD_PCUeCfg_Name pucchPowerControlModeFr1 0
# Remap only Default_FDD entries on =1, leave =Base untouched
mr CLPC_FDD_Remap
ma CLPC_FDD_Remap GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default_FDD,UeBbProfileUeCfg=
mr CLPC_FDD_Remap UeBbProfileUeCfg= powerControlUeCfgRef PowerControlUeCfg=Base
pr CLPC_FDD_Remap
if $nr_of_mos != 0
  set CLPC_FDD_Remap powerControlUeCfgRef GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=$CLPC_FDD_PCUeCfg_Name
fi
endfunc

CLPC_Precheck

# Mixed node (A + IJK)
if $GenCheck = Gen3or4 && $CLPC_Precheck_Pass = yes && $A_Cell_Present = 1 && $IJK_Cell_Present = 1
  set SystemFunctions=1,Lm=1,FeatureState=CXC4012883 featureState 1
  CLPC_SPLIT_PCUECFG
  set GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=1 pucchPowerControlModeFr1 1
  CLPC_PZERONOMPUCCH_N41_SET

# TDD-only node (A only)
else if $GenCheck = Gen3or4 && $CLPC_PCUeCfg_Present = yes && $A_Cell_Present = 1 && $IJK_Cell_Present = 0
  set SystemFunctions=1,Lm=1,FeatureState=CXC4012883 featureState 1
  set GNBDUFunction=1,UeCC=1,PowerControl=1,PowerControlUeCfg=1 pucchPowerControlModeFr1 1
  CLPC_PZERONOMPUCCH_N41_SET

# FDD-only node (IJK only) - skip
fi

####################################################################################################################################################
## Switched Uplink with FDD and TDD Uplink MIMO - Rel 17
####################################################################################################################################################

### NR Switched Uplink for Throughput Boost (1 (ACTIVATED))
get CXC4012786 featureState$ 1
if $nr_of_mos != 0
   $feat_NRSwitUlBoost = 1
else
   $feat_NRSwitUlBoost = 0
fi

### NR UL Carrier Aggregation (1 (ACTIVATED))
get CXC4012690 featureState$ 1
if $nr_of_mos != 0
   $feat_NRUlCA = 1
else
   $feat_NRUlCA = 0
fi

### Uplink Single-User MIMO (1 (ACTIVATED))
get CXC4012493 featureState$ 1
if $nr_of_mos != 0
   $feat_ULSUMIMO = 1
else
   $feat_ULSUMIMO = 0
fi

### ulTxSwitchingEnabled needs to be true

get NRCellDU=[AIJK] ulTxSwitchingEnabled true
if $nr_of_mos = 0
   $UlTx_check_All = 0
else
   $UlTx_check_All = 1
fi

get NRCellDU=A ulTxSwitchingEnabled true
if $nr_of_mos = 0
   $UlTx_check_TDD = 0
else
   $UlTx_check_TDD = 1
fi

if $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $feat_NRSwitUlBoost = 1 && $feat_NRUlCA = 1 && $feat_ULSUMIMO = 1 && $UlTx_check_All = 1
   set FeatureState=CXC4012874 featureState 1
fi

if $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $A_Cell_Present = 1 && $feat_NRSwitUlBoost = 1 && $feat_NRUlCA = 1 && $feat_ULSUMIMO = 1 && $UlTx_check_TDD = 1
   set CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=Base UlTxSwitching2T2T true
   set GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default_TDD,CaCellProfileUeCfg=Base UlTxSwitching2T2T true
   set GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=N250.*,CaCellProfileUeCfg=Base UlTxSwitching2T2T true
fi

####################################################################################################################################################
## NR Paging Coverage Enhancement - Prototype
####################################################################################################################################################

if $GenCheck = Gen3or4
 scw RP3566:2
 scw RP3567:2
 scw RP3568:1
fi
        """]
            if self.df_gnb_cell.loc[self.df_gnb_cell.postcell.str.startswith(('K', 'J', 'I'))].shape[0] > 0:
                lines += ["""
####################################################################################################################################################
## NR UL CoMP - FDD
####################################################################################################################################################

####################################################################################################################################################
## TriMode Precheck Phase 1: UeBbProfile structure
####################################################################################################################################################

func ULComp_TriMode_Precheck_Profiles
$ULComp_Precheck_Pass = yes

pr UeBbProfile=Default_FDD
if $nr_of_mos = 0
$ULComp_Precheck_Pass = no
return
fi

pr UeBbProfile=Default_TDD
if $nr_of_mos = 0
$ULComp_Precheck_Pass = no
return
fi

endfunc

####################################################################################################################################################
## TriMode Precheck Phase 2: RRU verification on [IJK] cells
####################################################################################################################################################

func ULComp_check_RU_precheck
$ULComp_fieldRepUnit = $ULComp_RF_port -s ,RfPort=.* -g
get $ULComp_fieldRepUnit productData > $ULComp_prodctData
if $ULComp_prodctData[productName] ~ Radio
$ULComp_RRU_Found = yes
get $ULComp_rdn cellLocalId > $ULComp_cellLocal_Id
hget GNBCUCPFunction=1,NRCellCU cellLocalId ^$ULComp_cellLocal_Id$
ma ULComp_NRCellCU_FDD_RU hget_group
pr ULComp_NRCellCU_FDD_RU
fi
endfunc

func ULComp_TriMode_Precheck_RRU
$ULComp_RRU_Found = no
mr ULComp_NRCellDU_FDD
mr ULComp_NRCellCU_FDD_RU

ma ULComp_NRCellDU_FDD GNBDUFunction=1,NRCellDU=[IJK]

for $mo in ULComp_NRCellDU_FDD
lk $mo
$ULComp_rdn = rdn($mo)
get lk_group rfportref > $ULComp_RF_port
if $nr_of_mos > 0
ULComp_check_RU_precheck
return
fi
get lk_group ^MulticastAntennaBranchid$
if $nr_of_mos > 0
$ULComp_RRU_Found = yes
get $ULComp_rdn cellLocalId > $ULComp_cellLocal_Id
hget GNBCUCPFunction=1,NRCellCU cellLocalId ^$ULComp_cellLocal_Id$
ma ULComp_NRCellCU_FDD_RU hget_group
return
fi
get lk_group ^transceiverid$
if $nr_of_mos > 0
return
fi
done

if $ULComp_RRU_Found = no
$ULComp_Precheck_Pass = no
fi
endfunc

####################################################################################################################################################
## TriMode Precheck Phase 3: FDD Candidate detection
####################################################################################################################################################

func ULComp_TriMode_Precheck_Candidates
$ULComp_Candidates_Found = no

mr ULComp_NRFreqRel_FDD_hget_group
mr ULComp_NRCellCU_FDD_hget_group

for $mo in ULComp_NRCellCU_FDD_RU
$ULComp_NRCellCU_FDD_RDN = rdn($mo)
get $ULComp_NRCellCU_FDD_RDN nRFrequencyRef > $ULComp_nRFrequency
lhget $ULComp_NRCellCU_FDD_RDN nRFrequencyRef $ULComp_nRFrequency
if $nr_of_mos > 0
ma ULComp_NRFreqRel_FDD_hget_group hget_group
fi
done

ma ULComp_NRCellCU_FDD_hget_group ULComp_NRFreqRel_FDD_hget_group reservedBy

########################################################
# Remove any neighbor cell relations (ExternalNRCellCU)
########################################################
mr ULComp_NRCellCU_FDD_hget_group NRCellRelation= nRCellRef ExternalNRCellCU

########################################################
# Verify we have valid candidates
########################################################
get ULComp_NRCellCU_FDD_hget_group nRCellRef

if $nr_of_mos > 0
$ULComp_Candidates_Found = yes
fi
endfunc

####################################################################################################################################################
## TriMode Configuration: All-or-nothing
####################################################################################################################################################

func ULComp_TriMode_Config

# Check if UplinkCompUeCfg=Base_TDD already exists
pr GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_TDD$
if $nr_of_mos = 0
$ULComp_Base_TDD = no
else
$ULComp_Base_TDD = yes
fi

# Check if UplinkCompUeCfg=Base_FDD already exists
pr GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_FDD$
if $nr_of_mos = 0
$ULComp_Base_FDD = no
else
$ULComp_Base_FDD = yes
fi

### Create UplinkCompUeCfg=Base_TDD if missing
if $ULComp_Base_TDD = no
cr GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_TDD
fi

# Set TDD values (always, in case of partial prior run)
set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_TDD uplinkCompUserSelSinrHyst 30
set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_TDD uplinkCompUserSelSinrThresh 250
set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_TDD uplinkCompUeEnabled true

### Create UplinkCompUeCfg=Base_FDD if missing
if $ULComp_Base_FDD = no
cr GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_FDD
fi

# Set FDD values (always, in case of partial prior run)
set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_FDD uplinkCompUserSelSinrHyst 30
set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_FDD uplinkCompUserSelSinrThresh 400
set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_FDD uplinkCompUeEnabled true

### Remap Default_TDD UeBbProfileUeCfg references to Base_TDD
set UeBbProfile=Default_TDD,UeBbProfileUeCfg= uplinkCompUeCfgRef GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_TDD

### Remap Default_FDD UeBbProfileUeCfg references to Base_FDD
set UeBbProfile=Default_FDD,UeBbProfileUeCfg= uplinkCompUeCfgRef GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base_FDD

### Set cell candidates and activate feature
set ULComp_NRCellCU_FDD_hget_group ulCompCellCandidate 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012816 featureState 1

endfunc

####################################################################################################################################################
## Single-Mode FDD (v1 approach)
####################################################################################################################################################

func ULComp_check_RU
$ULComp_fieldRepUnit = $ULComp_RF_port -s ,RfPort=.* -g
$ULComp_Eqm[$ULComp_rdn] = $ULComp_fieldRepUnit
get $ULComp_fieldRepUnit productData > $ULComp_prodctData
if $ULComp_prodctData[productName] ~ Radio
get $ULComp_rdn cellLocalId > $ULComp_cellLocal_Id
hget GNBCUCPFunction=1,NRCellCU cellLocalId ^$ULComp_cellLocal_Id$
ma ULComp_NRCellCU_FDD_RU hget_group
pr ULComp_NRCellCU_FDD_RU
fi
endfunc

func ULComp_FDD
mr ULComp_NRCellDU_FDD
mr ULComp_NRCellCU_FDD_RU
mr ULComp_NRFreqRel_FDD_hget_group
mr ULComp_NRCellCU_FDD_hget_group

ma ULComp_NRCellDU_FDD GNBDUFunction=1,NRCellDU=[IJK]

for $mo in ULComp_NRCellDU_FDD
lk $mo
$ULComp_rdn = rdn($mo)
get lk_group rfportref > $ULComp_RF_port
if $nr_of_mos > 0
ULComp_check_RU
return
fi
get lk_group ^MulticastAntennaBranchid$
if $nr_of_mos > 0
get $ULComp_rdn cellLocalId > $ULComp_cellLocal_Id
hget GNBCUCPFunction=1,NRCellCU cellLocalId ^$ULComp_cellLocal_Id$
ma ULComp_NRCellCU_FDD_RU hget_group
return
fi
get lk_group ^transceiverid$
if $nr_of_mos > 0
return
fi
done

mr ULComp_NRCellCU_FDD_hget_group
for $mo in ULComp_NRCellCU_FDD_RU
$ULComp_NRCellCU_FDD_RDN = rdn($mo)
get $ULComp_NRCellCU_FDD_RDN nRFrequencyRef > $ULComp_nRFrequency
lhget $ULComp_NRCellCU_FDD_RDN nRFrequencyRef $ULComp_nRFrequency
if $nr_of_mos > 0
ma ULComp_NRFreqRel_FDD_hget_group hget_group
fi
done

ma ULComp_NRCellCU_FDD_hget_group ULComp_NRFreqRel_FDD_hget_group reservedBy


########################################################
# Remove any neighbor cell relations (ExternalNRCellCU)
########################################################
mr ULComp_NRCellCU_FDD_hget_group NRCellRelation= nRCellRef ExternalNRCellCU

########################################################
# Verify we have valid candidates - all or none
########################################################
get ULComp_NRCellCU_FDD_hget_group nRCellRef

if $nr_of_mos > 0
set ULComp_NRCellCU_FDD_hget_group ulCompCellCandidate 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012816 featureState 1
set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base uplinkCompUserSelSinrHyst 30
set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base uplinkCompUserSelSinrThresh 400
set GNBDUFunction=1,UeCC=1,UplinkComp=1,UplinkCompUeCfg=Base uplinkCompUeEnabled 1
fi
endfunc

####################################################################################################################################################
## Execution
####################################################################################################################################################

$ULComp_Precheck_Pass = no
$ULComp_Candidates_Found = no

if $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $A_Cell_Present = 1
# TriMode: run all prechecks
ULComp_TriMode_Precheck_Profiles
else if $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0
# Single-Mode: run v1 approach directly
ULComp_FDD
fi

if $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $A_Cell_Present = 1 && $ULComp_Precheck_Pass = yes
# TriMode: precheck phase 2 - verify RRU on [IJK] cells
ULComp_TriMode_Precheck_RRU
fi

if $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $A_Cell_Present = 1 && $ULComp_Precheck_Pass = yes && $ULComp_RRU_Found = yes
# TriMode: precheck phase 3 - verify candidates exist
ULComp_TriMode_Precheck_Candidates
fi

if $IJK_Cell_Present = 1 && $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $A_Cell_Present = 1 && $ULComp_Precheck_Pass = yes && $ULComp_Candidates_Found = yes
# TriMode: all prechecks passed - execute all-or-nothing configuration
ULComp_TriMode_Config
fi

####################################################################################################################################################
## SSB Power Boost Prototype Workaround
####################################################################################################################################################

# Check feature active
$SsbBoost_FeatureActive = 0
get FeatureState=CXC4012500 featureState$ 1
if $nr_of_mos > 0
$SsbBoost_FeatureActive = 1
fi

# Check if any JK cell has ssbPowerBoost != 0
mr SsbBoost_JKCells
ma SsbBoost_JKCells GNBDUFunction=1,NRCellDU=[JK]
mr SsbBoost_JKCells GNBDUFunction=1,NRCellDU=[JK] ^ssbPowerBoost$ 0
pr SsbBoost_JKCells
$SsbBoost_JK_Qualifying = $nr_of_mos

if $SsbBoost_FeatureActive = 1 && $SsbBoost_JK_Qualifying > 0
  mr SSB_UnlockedNRSectorCarrier
  ma SSB_UnlockedNRSectorCarrier NRSectorCarrier= administrativeState 1
  bl SSB_UnlockedNRSectorCarrier
  wait 10
  scw RP3046:1
  deb SSB_UnlockedNRSectorCarrier
  mr SSB_UnlockedNRSectorCarrier
fi

                """]
            if self.df_gnb_cell.loc[self.df_gnb_cell.postcell.str.startswith('A')].shape[0] > 0:
                lines += ["""
####################################################################################################################################################
## AI-Native Scheduler for Link Adaptation for TDD
####################################################################################################################################################

func AINPreCheck_AIML_TDD

## UeBbProfileUeCfg=Base must exist
pr $AINative_TDD_UeBBProfile_Var_TDD,UeBbProfileUeCfg=Base
if $nr_of_mos = 0
   $TDD_ProfilesCfg_Ready = no
   return
fi

## UeBbProfileUeCfg=HSI must exist
pr $AINative_TDD_UeBBProfile_Var_TDD,UeBbProfileUeCfg=HSI
if $nr_of_mos = 0
   $TDD_ProfilesCfg_Ready = no
   return
fi

$TDD_ProfilesCfg_Ready = yes

## Slot availability (max 8 LinkAdaptationUeCfg)
mr AIN_LACfg_inuse
ma AIN_LACfg_inuse LinkAdaptationUeCfg=
mr AIN_LACfg_inuse LinkAdaptationUeCfg=Base$
mr AIN_LACfg_inuse LinkAdaptationUeCfg=Base_TDD
mr AIN_LACfg_inuse LinkAdaptationUeCfg=AIML$

$min_lim = 0
if $AINative_TDD_UeBBProfile_Var_TDD = UeBbProfile=Default_TDD
   $min_lim = 2
else if $AINative_TDD_UeBBProfile_Var_TDD = UeBbProfile=Default
   $min_lim = 1
fi

pr AIN_LACfg_inuse
$free_spot_AIN = 8 - $nr_of_mos

if $free_spot_AIN < $min_lim
   $Max_LACfg = yes
   return
fi

## Legacy AIML naming alignment (clear refs before delete)
pr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=AIML$
if $nr_of_mos != 0
   set $AINative_TDD_UeBBProfile_Var_TDD,UeBbProfileUeCfg=Base linkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base
   set $AINative_TDD_UeBBProfile_Var_TDD,UeBbProfileUeCfg=HSI linkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base
   del GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=AIML$
fi

endfunc

func LinkAdaptationUeCfg_parm_default

$LinkAdaptationUeCfg_parm = $1$
$LinkAdaptationUeCfg_parm2 = $1

set $LinkAdaptationUeCfg_parm                          dlMaxBitrate                           -1
set $LinkAdaptationUeCfg_parm                          dlMcsTable                             1
set $LinkAdaptationUeCfg_parm                          linkAdaptationUeMode                   0
set $LinkAdaptationUeCfg_parm                          ulMcsTable                             1

set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlBlerTarget                           1000
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlBlerTargetExtended                   -1
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlDownStep                             0
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlMaxMcsIndex                          27
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlMaxTbs                               0
set $LinkAdaptationUeCfg_parm2,DlLinkAdaptation=1       dlSinrBackoff                          0

set $LinkAdaptationUeCfg_parm2,PdcchLinkAdaptation=1    pdcchLaSinrUeOffset                    0
set $LinkAdaptationUeCfg_parm2,PdcchLinkAdaptation=1    pdcchRobustLaDtxTarget                 10
set $LinkAdaptationUeCfg_parm2,PdcchLinkAdaptation=1    pdcchRobustLaEnabled                   false

set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulBlerTarget                           1000
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulBlerTargetExtended                   -1
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulDownStep                             0
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulMaxMcsIndex                          27
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulMinTbs                               96
set $LinkAdaptationUeCfg_parm2,UlLinkAdaptation=1       ulSinrBackoff                          0

endfunc

func AINative_Config

set FeatureState=CXC4012888 featureState 1
set FeatureState=CXC4012884 featureState 1

pr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=$LinkAdaptUeCfg_profile$
if $nr_of_mos = 0
   $LinkAdaptUeCfg_Base_TDD = no
else
   $LinkAdaptUeCfg_Base_TDD = yes
fi

### Create LinkAdaptationUeCfg_Base_TDD if does not exist
if $A_Cell_Present = 1 && $IJK_Cell_Present = 1 && $LinkAdaptUeCfg_Base_TDD = no
      u+s $nodename_LinkAdaptationUeCfg
      LinkAdaptationUeCfg_parm_default LinkAdaptationUeCfg=Base
      u-
      l sed 's/LinkAdaptationUeCfg=Base/LinkAdaptationUeCfg=Base_TDD/g' $undocommandfile > $nodename_LinkAdaptationUeCfg_TDD.mos
      cr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD

      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD,DlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD,UlLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base_TDD,PdcchLinkAdaptation=1
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=Base_TDD
      ld GNBDUFunction=1,UeCC=1,UlServiceDefinition=1,UlServiceDefinitionUeCfg=Base_TDD,UlService=1

      run $nodename_LinkAdaptationUeCfg_TDD.mos
      l rm $nodename_LinkAdaptationUeCfg_TDD.mos $undodelcommandfile $undologfile $undocommandfile
fi

set $AINative_TDD_UeBBProfile_Var_TDD,UeBbProfileUeCfg=Base linkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=$LinkAdaptUeCfg_profile
set $AINative_TDD_UeBBProfile_Var_TDD,UeBbProfileUeCfg=HSI linkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=$LinkAdaptUeCfg_profile

mr All_LACfg
ma All_LACfg LinkAdaptationUeCfg=SD.*
ma All_LACfg LinkAdaptationUeCfg=Base$
ma All_LACfg LinkAdaptationUeCfg=Base_TDD
mr All_LACfg LinkAdaptationUeCfg=SD_6001
mr All_LACfg LinkAdaptationUeCfg=Base_FDD
mr All_LACfg LinkAdaptationUeCfg=VoNR.*

for $mo in All_LACfg

   $Link_Adap_prof_rdn = rdn($mo)
   set $Link_Adap_prof_rdn$ linkAdaptationUeMode 3
   set $Link_Adap_prof_rdn,DlLinkAdaptation=1 dlAiLinkAdaptationUeMode 1

done

endfunc

$Max_LACfg = no
$TDD_ProfilesCfg_Ready = no

get FieldReplaceableUnit productData AIR.*64...*B41
   $AI_Native_AIR64_Present = 0
if $nr_of_mos != 0
   $AI_Native_AIR64_Present = 1
fi

get FieldReplaceableUnit productData Radio.*8863.*B41
   $AI_Native_Radio8863_Present = 0
if $nr_of_mos != 0
   $AI_Native_Radio8863_Present = 1
fi

if $A_Cell_Present = 1 && $IJK_Cell_Present = 1
   $AINative_TDD_UeBBProfile_Var_TDD = UeBbProfile=Default_TDD
   $LinkAdaptUeCfg_profile = Base_TDD
else
   $AINative_TDD_UeBBProfile_Var_TDD = UeBbProfile=Default
   $LinkAdaptUeCfg_profile = Base
fi

AINPreCheck_AIML_TDD

if $GenCheck = Gen3or4 && $QSH_Cell_Present = 0 && $Max_LACfg = no && $TDD_ProfilesCfg_Ready = yes && $AI_Native_AIR64_Present = 1 && $AI_Native_Radio8863_Present = 0
   AINative_Config
fi

####################################################################################################################################################
## Energy Optimized Symbol Allocation
####################################################################################################################################################

func EoSA_MIDBAND_SET

mr EoSA_NRCells_A
ma EoSA_NRCells_A GNBDUFunction=1,NRCellDU=[A]

  for $mo in EoSA_NRCells_A
    $EoSA_NRCellDU_A = rdn($mo)
    mr EoSA_NRSectorCarrier_A
    ma EoSA_NRSectorCarrier_A nrsector reserv $EoSA_NRCellDU_A
    get EoSA_NRSectorCarrier_A bSChannelBwDL > $EoSA_BWD_A
    if $EoSA_BWD_A != 10 && $EoSA_BWD_A != 15 && $EoSA_BWD_A != 20
      set $EoSA_NRCellDU_A energyOptSymAllocRef EnergyEfficiency=1,EnergyOptSymAlloc=EOSyA
      $EoSA_VALID_CELL_FOUND = $EoSA_VALID_CELL_FOUND + $nr_of_mos
    else if $EoSA_BWD_A = 20
      mr EoSA_NRCellDU_A-20
      ma EoSA_NRCellDU_A-20 $EoSA_NRCellDU_A
      mr EoSA_NRCellDU_A-20 $EoSA_NRCellDU_A dlAvailableCrbs [1-9]
      mr EoSA_NRCellDU_A-20 $EoSA_NRCellDU_A ulAvailableCrbs [1-9]
      set EoSA_NRCellDU_A-20 energyOptSymAllocRef EnergyEfficiency=1,EnergyOptSymAlloc=EOSyA
      $EoSA_VALID_CELL_FOUND = $EoSA_VALID_CELL_FOUND + $nr_of_mos
    fi
  done

endfunc

$EoSA_VALID_CELL_FOUND = 0

get FieldReplaceableUnit=BB-01|FieldReplaceableUnit=1 productData > $BoardType
pr EnergyOptSymAlloc=EOSyA

   if $BoardType[productName] ~ "|6641|6648|6337|6347|6621|6631|6339|6353|6507|6647|6651|6672|6655|6372|6355|" && $nr_of_mos != 0
      EoSA_MIDBAND_SET
   else if $BoardType[productName] ~ "|6641|6648|6337|6347|6621|6631|6339|6353|6507|6647|6651|6672|6655|6372|6355|" && $nr_of_mos = 0

   crn GNBDUFunction=1,EnergyEfficiency=1,EnergyOptSymAlloc=EOSyA
   energyOptSymAllocMode 0
   end

      EoSA_MIDBAND_SET

   fi

if $EoSA_VALID_CELL_FOUND > 0
  set FeatureState=CXC4012850 featureState 1
  set GNBDUFunction=1,EnergyEfficiency=1,EnergyOptSymAlloc=EOSyA energyOptSymAllocMode 1
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

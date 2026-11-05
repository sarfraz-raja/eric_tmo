from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base
from .tmo_data import global_amos_logic
import re


class nr_09b_NRLB_Para(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.addcell].index) == 0: return
        if self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.contains('^K'))].shape[0] == 0 and \
                self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.contains('^J'))].shape[0] == 0 and \
                self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.contains('^I'))].shape[0] == 0:
            return
        self.script_list += self.bl_start()
        self.script_list += global_amos_logic()
        self.script_list += self.get_lock_cells()
        self.script_list += self.parameter_settings()
        self.script_list += self.software_update()
        self.script_list += self.get_unlock_cells()
        if len(self.script_list) > 0:
            self.script_list = self.activity_check('Pre') + self.script_list + self.activity_check('Post')

    def bl_start(self):
        return [
            F"""
####:----------------> Pre Check <----------------:####
pr NRCellDU=[IJK]
if $nr_of_mos = 0
    print  ERROR: No NR LB cell defined !!!
    l-
    return
fi

####:----------------> Logic <----------------:####
pv $mibprefix

$excalibur = 0
if {" || ".join(["$mibprefix ~ " + _ for _ in self.market_dict.get("excalibur")])}
   $excalibur = 1
fi
"""]


    def parameter_settings(self):
        lines = ["""
####:----------------> Parameter Setting <----------------:####

###########################################
####  REDCAP Activation NR N25/N71 FDD ONLY
###########################################
set FeatureState=CXC4012800 featureState 1
set NRCellDU=[K|J] redCap1RxEnabled true
set NRCellDU=[K|J] redCap2RxEnabled true

set NRCellDU=[K|J|I] PuschModeOnFddSCell 1

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

####:----------------> Parameter Setting for 24Q4 SW <----------------:####

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

####:----------------> Parameter Setting for 25Q2 SW <----------------:####

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

if $MotoRzr_PreReq1 ~ 1 && $MotoRzr_PreReq2 ~ 1 && $MotoRzr_Gen3 ~ Yes
    UEGrp_MotoRzr
fi

"""]
        return lines

    def software_update(self):
        lines = []
        if self.usid.client.software.swname[:9] > 'TMO_25_Q3':
            lines += [F"""
####:----------------> Parameter Setting for 25Q4 SW <----------------:####
################ PDCCH OLA based on DTX (G3+ FDD) ################
func PDCCHOLA_Config
	# Activate NR DL Beam Optimizer feature with "SLOW" settings(OFF for FDD in normal scenario)
	set SystemFunctions=1,Lm=1,FeatureState=CXC4012832 featureState 1
	set GNBDUFunction=1,UeCC=1,DlBeamOptProfile=1,DlBeamOptProfileUeCfg=Base pdcchBeamOptMode 1

	# Deactivate PDSCH based PDCCH OLA(only for N71)
	set NRCellDU=K pdcchOlaSelection 0

	# Activate PDCCH OLA based on DTX prototype
	set SystemFunctions=1,Lm=1,FeatureState=CXC4012679 featureState 1

	# FDD band: eMBB
	cr GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=1
	cr GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=1,PrototypeEntry=1
	set GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=1,PrototypeEntry=1 paramId 1
	set GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=1,PrototypeEntry=1 paramvalue 365731945
	set GNBDUFunction=1,UeCC=1,UeBb=1,$PDCCHOLA_UeBBProfile_Var,UeBbProfileUeCfg=Base prototypeConfigUeCfgRef GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=1

	# FDD band: VoNR
	cr GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=2
	cr GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=2,PrototypeEntry=1
	set GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=2,PrototypeEntry=1 paramId 1
	set GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=2,PrototypeEntry=1 paramvalue 359047869
	set GNBDUFunction=1,UeCC=1,UeBb=1,$PDCCHOLA_UeBBProfile_Var,UeBbProfileUeCfg=VoNR prototypeConfigUeCfgRef GNBDUFunction=1,UeCC=1,PrototypeConfig=1,PrototypeConfigUeCfg=2
endfunc

if $A_Cell_Present = 1 && $IJK_Cell_Present = 1
	$PDCCHOLA_UeBBProfile_Var = UeBbProfile=Default_FDD
else
	$PDCCHOLA_UeBBProfile_Var = UeBbProfile=Default
fi

if $GenCheck = Gen3or4 && $IJK_Cell_Present = 1
	PDCCHOLA_Config
fi

################ BoCS - Multi-Layer Traffic Awareness (RRH/FDD)* ################
func BoCS_FDD_Configure
	//Auto DST
	set TimeSettings daylightSavingTimeStartDate dayRule=Sun>=8,month=3,time=02:00
	set TimeSettings daylightSavingTimeEndDate dayRule=Sun>=1,month=11,time=02:00
	set TimeSettings daylightSavingTimeOffset 1:00

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

	set GNBCUCPFunction=1,EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=2 wakeupRequiredTime 15
	set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=2  wakeupPeriodicEsDuration 0

	//Sleep Conditions
	set EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=2     sleepUcfThreshBooster 2000
	set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=2          sleepFilterTimePercentage 90
	set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=2          sleepRelBoosterFilterTimePerc 90
	set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=2          sleepEvaluateTimeWindow 600

	//Cond2: UCF of at least one of the energy performance related cells < sleepUcfThreshEp
	//Wakeup requeriments
	set EnergyPerformance=1,EpBoCS=1,EpBoosterCellProfile=2 wakeupUcfThresh   2000
	set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=2 sleepUcfWakeupThreshFactor 40
	set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=2 wakeupFilterTimePercentage  80
	set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=2 wakeupEvaluateTimeWindow   360

	//Wake-up cond2 = True, if Cond1=True and either of the following is True:
	set EnergyPerformance=1,EpBoCS=1,EpBoosterAdvCfg=2  wakeupMissingSampleTime    150
endfunc

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
		if $src_Cellid  = 21 && $Ext_Cellid = 1
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 21 && $Ext_Cellid = 11
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 22 && $Ext_Cellid = 2
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 22 && $Ext_Cellid = 12
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 23 && $Ext_Cellid = 3
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 23 && $Ext_Cellid = 13
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 24 && $Ext_Cellid = 4
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 24 && $Ext_Cellid = 14
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 41 && $Ext_Cellid = 1
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 41 && $Ext_Cellid = 11
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 42 && $Ext_Cellid = 2
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 42 && $Ext_Cellid = 12
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 43 && $Ext_Cellid = 3
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 43 && $Ext_Cellid = 13
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 44 && $Ext_Cellid = 4
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 44 && $Ext_Cellid = 14
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 61 && $Ext_Cellid = 1
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 61 && $Ext_Cellid = 11
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 62 && $Ext_Cellid = 2
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 62 && $Ext_Cellid = 12
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 63 && $Ext_Cellid = 3
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 63 && $Ext_Cellid = 13
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 64 && $Ext_Cellid = 4
			set $TAR_REL epLoadMonitoringEnabled true
		else if $src_Cellid  = 64 && $Ext_Cellid = 14
			set $TAR_REL epLoadMonitoringEnabled true
		fi
	done
endfunc

func ENEPER_Cell_Checker
mr ENEPER_Cell
ma ENEPER_Cell NRCellCU=J.*NRCellRelation= coverageIndicator !0
pr ENEPER_Cell
if $nr_of_mos != 0
	$BoCS_FDD_ENEPER_CellCheck = 1
else
	$BoCS_FDD_ENEPER_CellCheck = 0
fi
for $mo in ENEPER_Cell
	$ldn = ldn($mo)
	get $ldn  nRFreqRelationRef > $TestFreq
	if $TestFreq ~ NRFreqRelation=3
		mr ENEPER_Cell $ldn
	fi
done
endfunc

$BoCS_FDD_ENEPER_CellCheck = 0
get GNBCUCPFunction=1 altDepHBoCSEnabled true
if $nr_of_mos != 0
	$BoCS_FDD_PreScript = 1
fi

//check n25 radio type
mr BoCS_FDD_RadioCheck
ma BoCS_FDD_RadioCheck FieldReplaceableUnit productData RADIO.*44...*B25
ma BoCS_FDD_RadioCheck FieldReplaceableUnit productData RADIO.*22...*B25

pr BoCS_FDD_RadioCheck
if $nr_of_mos = 0
	$BoCS_FDD_RadioCheck = 0
else
	$BoCS_FDD_RadioCheck = 1
fi

get SysM=1,TimeM=1,DateAndTime=1 timeZone > $TimeZ
if $TimeZ = US/Hawaii || $TimeZ = US/Pacific || $TimeZ = US/Mountain || $TimeZ = US/Central || $TimeZ = US/Eastern
	$Valid_TimeZ = 1
else
	$Valid_TimeZ = 0
fi

if $GenCheck = Gen3or4 && $BoCS_FDD_RadioCheck = 1 && $Valid_TimeZ = 1 && $BoCS_FDD_PreScript = 1 && $J_Cell_Present = 1 && $K_Cell_Present = 1
	BoCS_FDD_Configure
	ENEPER_Cell_Checker
fi

if $GenCheck = Gen3or4 && $BoCS_FDD_RadioCheck = 1 && $Valid_TimeZ = 1 && $BoCS_FDD_PreScript = 1 && $J_Cell_Present = 1 && $K_Cell_Present = 1 && $BoCS_FDD_ENEPER_CellCheck = 1
	Validate_intra_Inter
	LoadMonitor_Enable
fi


################ Energy Optimized Symbol Allocation ################

func EoSA_LOWBAND_SET
	mr EoSA_NRCells_IJK
	ma EoSA_NRCells_IJK GNBDUFunction=1,NRCellDU=[IJK]
	for $mo in EoSA_NRCells_IJK
		$EoSA_NRCellDU_IJK = rdn($mo)
		mr EoSA_NRSectorCarrier_IJK
		ma EoSA_NRSectorCarrier_IJK nrsector reserv $EoSA_NRCellDU_IJK
		get EoSA_NRSectorCarrier_IJK bSChannelBwDL > $EoSA_BWD_IJK
		if $EoSA_BWD_IJK != 5 && $EoSA_BWD_IJK != 10
			set $EoSA_NRCellDU_IJK energyOptSymAllocRef EnergyEfficiency=1,EnergyOptSymAlloc=EOSyA
			$EoSA_VALID_CELL_FOUND = $EoSA_VALID_CELL_FOUND + $nr_of_mos
		else if $EoSA_BWD_IJK = 10
			mr EoSA_NRCellDU_IJK-10
			ma EoSA_NRCellDU_IJK-10 $EoSA_NRCellDU_IJK
			set EoSA_NRCellDU_IJK-10 energyOptSymAllocRef EnergyEfficiency=1,EnergyOptSymAlloc=Default
			mr EoSA_NRCellDU_IJK-10 $EoSA_NRCellDU_IJK dlAvailableCrbs [1-9]
			mr EoSA_NRCellDU_IJK-10 $EoSA_NRCellDU_IJK ulAvailableCrbs [1-9]
			set EoSA_NRCellDU_IJK-10 energyOptSymAllocRef EnergyEfficiency=1,EnergyOptSymAlloc=EOSyA
			$EoSA_VALID_CELL_FOUND = $EoSA_VALID_CELL_FOUND + $nr_of_mos
		fi
	done
endfunc

$EoSA_VALID_CELL_FOUND = 0
get FieldReplaceableUnit=BB-01|FieldReplaceableUnit=1 productData > $BoardType
pr EnergyOptSymAlloc=EOSyA
if $BoardType[productName] ~ "|6641|6648|6337|6347|6621|6631|6339|6353|6507|6647|6651|6672|6655|6372|6355|" && $nr_of_mos != 0
	EoSA_LOWBAND_SET
else if $BoardType[productName] ~ "|6641|6648|6337|6347|6621|6631|6339|6353|6507|6647|6651|6672|6655|6372|6355|" && $nr_of_mos = 0
	crn GNBDUFunction=1,EnergyEfficiency=1,EnergyOptSymAlloc=EOSyA
	energyOptSymAllocMode 0
	end
	EoSA_LOWBAND_SET
fi

if $EoSA_VALID_CELL_FOUND > 0
  set FeatureState=CXC4012850 featureState 1
  set GNBDUFunction=1,EnergyEfficiency=1,EnergyOptSymAlloc=EOSyA energyOptSymAllocMode 1
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

from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_11_NRFreqProfile_v13(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return

        self.relative_path.insert(-2, 'NR_NR_Relations')
        self.nrnwmo = F'GNBCUCPFunction=1,NRNetwork={self.gnbdata.get("NRNetwork")}'
        self.script_list += self.pre_post_check('Pre') + self.nr_nr_relation_profile_creation() + self.pre_post_check('Post')

    def nr_nr_relation_profile_creation(self):
        lines = [
            """
###################################################################################################################################################
###### SCript handles five Tasks
###### Task1 : copy all exsting profiles and re-labeling to SSB_Sband_SCarrier format. copy also exsting baselines from each profile
###### Task2 : check if any Frequency relation missing peofile and created new profile with parameters inside the script.
###### Task3 : Cleanup all the profiles not reserved to any frequency relation 
###### Task4 : check if the MCPC/UEMC VONR Profiles are missing and corrected but updated the parametr to the baseline
###### Task5 : change McpcPSCellProfile from node level to per cell profile 
###### Ver12:  Profile Naming N1900_2 remains undeleted
###### Ver13:  Modify Baseline Parameter for missing Profiles.
###### Version 13 06/21/2023
###### created by bfisha
######################################################################################################################################################

confbd+
gs+
lt all

####check if VONR UE Group is defined #####

pr GNBCUCPFunction=1,UeGroupSelection=1
if $nr_of_mos = 0
 cr GNBCUCPFunction=1,UeGroupSelection=1
fi

get UeGroupSelectionProfile= ueGroupId ^1$
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=VoNR
    ueGroupId 1
    ueGroupPriority 100
    selectionProbability 100
    selectionCriteria 5qi==1
    end
fi

################################################################################


func RUNPSCELLFIX
$SCARR =
$SCell = 
$split_separator = ,
for $mo in MCPCPSCELL
$ldn = ldn($mo)
$NRFR = $ldn
get $ldn nRFrequencyRef > $NRSSB
get $NRSSB arfcnValueNRDl > $nssb
$S_Cell = split($ldn) 
$SCell = $S_Cell[2]  -s NRCellCU=
$SCARR = `$gawk -v CelName=$SCell 'BEGIN {print  substr(CelName,11,1) }'`
if $SCell ~ ^A
$SBAND = N2500
$SRCNR = N41
else if $SCell ~ ^K
$SBAND = N600
$SRCNR = N71
else if $SCell ~ ^J
$SBAND = N1900
$SRCNR = N19
fi

pr GNBCUCPFunction=1,Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
if $nr_of_mos = 0
crn GNBCUCPFunction=1,Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
ueConfGroupType 0
userLabel 
end
set $mo mcpcPSCellNrFreqRelProfileRef Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
ld Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPSCellNrFreqRelProfileUeCfg=Base
set Mcpc=1,McpcPSCellNrFreqRelProfile=3.*,McpcPSCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate true
else
set $mo mcpcPSCellNrFreqRelProfileRef Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
ld Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPSCellNrFreqRelProfileUeCfg=Base
set Mcpc=1,McpcPSCellNrFreqRelProfile=3.*,McpcPSCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate true
fi

$SCARR =
$SCell = 
done

endfunc



wfo $tempdir/NRFREQOFFSET_FIX_$nodename.mos
func LTEPRF_Baseline

## MCPC for IRAT

if $SRCNR ~  N41 && ( $BAND ~ ^2$  || $BAND ~ ^4$) 
$TRSHLD1_BASE_Base = 5
$TRSHLD2LTE_Base = -10
$CMPcellP_Base = 4
$BRWR = true

$TRSHLD1_vonr = 0
$TRSHLD2LTE_vonr = 0
$CMPcellP_vonr = 4

fi

if $SRCNR ~  N41 && ( $BAND ~ ^71$  || $BAND ~ ^12$) 
$TRSHLD1_BASE_Base = -8
$TRSHLD2LTE_Base = -12
$CMPcellP_Base = 2
$BRWR = false

$TRSHLD1_vonr = 0
$TRSHLD2LTE_vonr = 0
$CMPcellP_vonr = 4

fi

if $SRCNR ~  N71 && ( $BAND ~ ^2$  || $BAND ~ ^4$) 
$TRSHLD1_BASE_Base = 64
$TRSHLD2LTE_Base = -6
$CMPcellP_Base = 4
$BRWR = false

$TRSHLD1_vonr = 0
$TRSHLD2LTE_vonr = 0
$CMPcellP_vonr = 5

fi

if $SRCNR ~  N71 && ( $BAND ~ ^71$  || $BAND ~ ^12$) 
$TRSHLD1_BASE_Base = 0
$TRSHLD2LTE_Base = -12
$CMPcellP_Base = 2

$TRSHLD1_vonr = 0
$TRSHLD2LTE_vonr = 0
$CMPcellP_vonr = 3

fi

if $SRCNR ~  N71 && $BAND ~ ^71$  
$BRWR = true
else if $SRCNR ~  N71  && $BAND ~ ^12$
$BRWR = false
fi


if $SRCNR ~  N25 && ( $BAND ~ ^2$  || $BAND ~ ^4$) 
$TRSHLD1_BASE_Base = 1
$TRSHLD2LTE_Base = -14
$CMPcellP_Base = 4
$BRWR = true

$TRSHLD1_vonr = -2
$TRSHLD2LTE_vonr = 8
$CMPcellP_vonr = 4

fi

if $SRCNR ~  N25 && ( $BAND ~ ^71$  || $BAND ~ ^12$) 
$TRSHLD1_BASE_Base = -8
$TRSHLD2LTE_Base = -12
$CMPcellP_Base = 2
$BRWR = false

$TRSHLD1_vonr = -2
$TRSHLD2LTE_vonr = 8
$CMPcellP_vonr = 3

fi


lset GNBCUCPFunction=1,Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,McpcPCellEUtranFreqRelProfileUeCfg=Base rsrpCandidateB2Offsets threshold1Offset=$TRSHLD1_BASE_Base,threshold2EUtraOffset=$TRSHLD2LTE_Base
lset GNBCUCPFunction=1,Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,McpcPCellEUtranFreqRelProfileUeCfg=VoNR rsrpCandidateB2Offsets threshold1Offset=$TRSHLD1_vonr,threshold2EUtraOffset=$TRSHLD2LTE_vonr 

lset GNBCUCPFunction=1,UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=Base connModePrioPCell $CMPcellP_Base
lset GNBCUCPFunction=1,UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=VoNR connModePrioPCell $CMPcellP_vonr

lset GNBCUCPFunction=1,UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=Base blindRwrAllowed $BRWR

lset GNBCUCPFunction=1,Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,McpcPCellEUtranFreqRelProfileUeCfg= inhibitMeasForCellCandidate false
lset GNBCUCPFunction=1,UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=Base connModeAllowedPCell true 

endfunc

func LTEF_Profile

pr GNBCUCPFunction=1,Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR$
if $nr_of_mos = 0 
crn GNBCUCPFunction=1,Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR
ueConfGroupType 0
end
cr GNBCUCPFunction=1,Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,McpcPCellEUtranFreqRelProfileUeCfg=Base
set $LTEFR mcpcPCellEUtranFreqRelProfileRef Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR
else
set $LTEFR mcpcPCellEUtranFreqRelProfileRef Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR
fi

pr Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,McpcPCellEUtranFreqRelProfileUeCfg=VoNR
if $nr_of_mos = 0 
crn Mcpc=1,McpcPCellEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,McpcPCellEUtranFreqRelProfileUeCfg=VoNR
ueGroupList 1
end 
fi


pr GNBCUCPFunction=1,UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR$
if $nr_of_mos = 0 
crn GNBCUCPFunction=1,UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR
ueConfGroupType 0
end
cr GNBCUCPFunction=1,UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=Base
set $LTEFR ueMCEUtranFreqRelProfileRef UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR
else
set $LTEFR ueMCEUtranFreqRelProfileRef UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR
fi
pr UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=VoNR
if $nr_of_mos = 0 
crn UeMC=1,UeMCEUtranFreqRelProfile=$xarfcn_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=VoNR
ueGroupList 1
end
fi

LTEPRF_Baseline
endfunc



#########################################################################################################
###Device A53 inhibit mobility to N41 (source is N71 or N19)
func GA53_N41_inhibit
pr GNBCUCPFunction=1,UeGroupSelection=1
if $nr_of_mos = 0
 cr GNBCUCPFunction=1,UeGroupSelection=1
fi
pr  UeGroupSelectionProfile=.*A53 
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=GalaxyA53 
    ueGroupId 5
    ueGroupPriority 101
    selectionProbability 100
    selectionCriteria imeitac=={35057957,35098767,35345419,35849772,35424140,35026620,35078262,35102405,35672173}
    end
fi

pr Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53
if $nr_of_mos = 0
    crn Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53
    ueGroupList 5
    end
    set Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53 inhibitMeasForCellCandidate true
else
    set Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53 inhibitMeasForCellCandidate true
fi

endfunc

#########################################################################################################
###Device OnePlus 7T Pro 5G phones failed on N41 BW > 60Mhz , trun off CM NSA 
func ONePlus_N41_inhibit_PSCELL_CH
pr GNBCUCPFunction=1,UeGroupSelection=1
if $nr_of_mos = 0
 cr GNBCUCPFunction=1,UeGroupSelection=1
fi
pr  UeGroupSelectionProfile=OldOnePlus 
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=OldOnePlus
    selectionCriteria "imeitac=={99001382,99001569} && imeisvn==46"
    selectionProbability 100
    ueGroupId 11
    ueGroupPriority 110
    userLabel 
    end
fi

pr Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=OldOnePlus
if $nr_of_mos = 0
    crn UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=OldOnePlus
    ueGroupList 11
    end 
    set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=OldOnePlus connModeAllowedPSCell false
else
    set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=OldOnePlus connModeAllowedPSCell false
fi

endfunc


###NRFREQ Profile Baseline##############################################################################
func NRPRF_Baseline

if $SRCNR ~ N41 && $nssb ~ ^5

# NR41 >> N41 MCPC for IFHO
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=0
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=16  
##UeMC for NR
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModePrioPCell 7
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPCell true
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModePrioPCell 7
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModeAllowedPCell true

fi

if $SRCNR ~ N41 && $nssb ~ ^3

# NR41 >> N19 MCPC for IFHO
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base rsrpCandidateA5Offsets threshold1Offset=7,threshold2Offset=-9
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate false
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=-1
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR inhibitMeasForCellCandidate false
##UeMC for NR
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModePrioPCell 6
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPCell true
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPSCell false
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModePrioPCell 7
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModeAllowedPCell true

fi

if $SRCNR ~ N41 && $nssb ~ ^1

# NR41 >> N71 MCPC for IFHO
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base rsrpCandidateA5Offsets threshold1Offset=5,threshold2Offset=-8
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate false
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=0
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR inhibitMeasForCellCandidate false
##UeMC for NR
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModePrioPCell 3
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPCell true
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModePrioPCell 6
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModeAllowedPCell true
fi 



if $SRCNR ~ N19 && $nssb ~ ^5

# NR19 >> N41 MCPC for IFHO
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base rsrpCandidateA5Offsets threshold1Offset=64,threshold2Offset=-2
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate false
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=10 
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR inhibitMeasForCellCandidate false 

##UeMC for NR
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModePrioPCell 7
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPCell true
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModePrioPCell 6
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModeAllowedPCell true

fi

if $SRCNR ~ N19 && $nssb ~ ^3

# NR19 >> N19 MCPC for IFHO
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base rsrpCandidateA5Offsets threshold1Offset=7,threshold2Offset=-1
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=-1
##UeMC for NR
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModePrioPCell 6
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPCell true
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModePrioPCell 7
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModeAllowedPCell true

fi

if $SRCNR ~ N19 && $nssb ~ ^1

# NR19 >> N71 MCPC for IFHO
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base rsrpCandidateA5Offsets threshold1Offset=1,threshold2Offset=-8
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate false
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=-3 
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR inhibitMeasForCellCandidate false 

##UeMC for NR
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModePrioPCell 3
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPCell true
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModePrioPCell 6
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModeAllowedPCell true
fi 


if $SRCNR ~ N71 && $nssb ~ ^5

# NR71 >> N41 MCPC for IFHO
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base rsrpCandidateA5Offsets threshold1Offset=64,threshold2Offset=-4
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate false
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=16 
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR inhibitMeasForCellCandidate false 
 
##UeMC for NR
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModePrioPCell 7
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPCell true
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModePrioPCell 6
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModeAllowedPCell true

fi

if $SRCNR ~ N71 && $nssb ~ ^3

# NR71 >> N19 MCPC for IFHO
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base rsrpCandidateA5Offsets threshold1Offset=16,threshold2Offset=0
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base inhibitMeasForCellCandidate false
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=-3 
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR inhibitMeasForCellCandidate false 
##UeMC for NR
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModePrioPCell 6
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPCell true
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPSCell false
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModePrioPCell 7
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModeAllowedPCell true

fi

if $SRCNR ~ N71 && $nssb ~ ^1

# NR71 >> N71 MCPC for IFHO
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=0
set GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR rsrpCandidateA5Offsets threshold1Offset=0,threshold2Offset=0

##UeMC for NR
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModePrioPCell 3
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=BASE connModeAllowedPCell true
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModePrioPCell 3
set GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VONR connModeAllowedPCell true
fi

### N41 C2 , inhibit measurement from all layers

if $SCNDSSB > 0
set UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg connModeAllowedPCell false
set UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg connModeAllowedPSCell false
set Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg inhibitMeasForCellCandidate true 
set Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb,McpcPSCellNrFreqRelProfileUeCfg inhibitMeasForCellCandidate true  
fi


endfunc


###NRFREQ Profile #######################################################################################

func NRF_Profile

pr GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR$
if $nr_of_mos = 0 
    crn GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
    ueConfGroupType 0
    end
    set $NRFR mcpcPCellNrFreqRelProfileRef Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
    cr GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=Base
else 
    set $NRFR mcpcPCellNrFreqRelProfileRef Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
fi

pr Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR
if $nr_of_mos = 0 
    crn Mcpc=1,McpcPCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR
    ueGroupList 1
    end 
fi


pr GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR$
if $nr_of_mos = 0 
    crn GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR
    ueConfGroupType 0
    end
    set $NRFR ueMCNrFreqRelProfileRef UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR
    cr GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=Base
    set UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg connModeAllowedPSCell true 
else
    set $NRFR ueMCNrFreqRelProfileRef UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR
fi

pr UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VoNR
if $nr_of_mos = 0 
    crn UeMC=1,UeMCNrFreqRelProfile=$nssb_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VoNR
    ueGroupList 1
    end
fi

pr GNBCUCPFunction=1,Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
if $nr_of_mos = 0 
    crn GNBCUCPFunction=1,Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
    ueConfGroupType 0
    end
    set $NRFR mcpcPSCellNrFreqRelProfileRef Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
    cr GNBCUCPFunction=1,Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR,McpcPSCellNrFreqRelProfileUeCfg=Base
else
    set $NRFR mcpcPSCellNrFreqRelProfileRef Mcpc=1,McpcPSCellNrFreqRelProfile=$nssb_$SBAND_$SCARR
fi
####NR_sCell_Intelligent_Management N71 to N41 ####

if $SRCNR ~ N71 && $nssb ~ ^5
    cr GNBCUCPFunction=1,IntraFreqMC=1,IntraFreqMCFreqRelProfile=$nssb
    set $NRFR intraFreqMCFreqRelProfileRef GNBCUCPFunction=1,IntraFreqMC=1,IntraFreqMCFreqRelProfile=$nssb
    cr GNBCUCPFunction=1,IntraFreqMC=1,IntraFreqMCFreqRelProfile=$nssb,IntraFreqMCFreqRelProfileUeCfg=Base
    set GNBCUCPFunction=1,IntraFreqMC=1,IntraFreqMCFreqRelProfile=$nssb,IntraFreqMCFreqRelProfileUeCfg=Base waitForBetterSCellRep 1000
    GA53_N41_inhibit
    ONePlus_N41_inhibit_PSCELL_CH
fi

if $SRCNR ~ N19 && $nssb ~ ^5
    GA53_N41_inhibit
fi

NRPRF_Baseline
endfunc

func RUNPROFILE
$SCARR =
$SCell = 
$split_separator = ,
for $mo in MCPCMISS
$ldn = ldn($mo)
$NRFR = $ldn
get $ldn nRFrequencyRef > $NRSSB
get $NRSSB arfcnValueNRDl > $nssb
$S_Cell = split($ldn) 
$SCell = $S_Cell[2]  -s NRCellCU=
$SCARR = `$gawk -v CelName=$SCell 'BEGIN {print  substr(CelName,11,1) }'`
if $SCell ~ ^A
$SBAND = N2500
$SRCNR = N41
else if $SCell ~ ^K
$SBAND = N600
$SRCNR = N71
else if $SCell ~ ^J
$SBAND = N1900
$SRCNR = N19
fi
NRF_Profile
$SCARR =
$SCell = 
done

endfunc


func RUNIRATPRO
$SCARR =
$SCell = 
$split_separator = ,
for $z in MCPCIRAT
$ldn = ldn($z)
$LTEFR = $ldn
get $ldn eUtranFrequencyRef > $IRATFREQ
get $IRATFREQ arfcnValueEUtranDl > $xarfcn
$S_Cell = split($ldn) 
$SCell = $S_Cell[2]  -s NRCellCU=
$SCARR = `$gawk -v CelName=$SCell 'BEGIN {print  substr(CelName,11,1) }'`
if $SCell ~ ^A
$SBAND = N2500
$SRCNR = N41
else if $SCell ~ ^K
$SBAND = N600
$SRCNR = N71
else if $SCell ~ ^J
$SBAND = N1900
$SRCNR = N19
fi
if $xarfcn >= 1950 && $xarfcn <=  2399
$BAND = 4
else if $xarfcn >= 68586 && $xarfcn <=  68935  
$BAND = 71
else if $xarfcn >= 600 && $xarfcn <=  1199 
$BAND = 2
else if $xarfcn = 5035
$BAND = 12
fi 

LTEF_Profile
$SCARR =
$SCell = 
done

endfunc

####call NR missing profile ###
RUNPROFILE
####call IRAT missing profile ###
RUNIRATPRO

eof

##### SCript copy all the exsting Profile and re-labeled to SSB_SBAND_SCarrier format ######
func NRMCPC_VONR
crn Mcpc=1,McpcPCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VoNR
ueGroupList 1
end
$NRFIX = yes
endfunc

func LTEMCPC_VONR
crn Mcpc=1,McpcPCellEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR,McpcPCellEUtranFreqRelProfileUeCfg=VoNR
ueGroupList 1
end
$LTEFIX = yes
endfunc

func NRUEMC_VONR
crn UeMC=1,UeMCNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VoNR
ueGroupList 1
end
$NRFIX = yes
endfunc

func LTEUEMC_VONR
crn UeMC=1,UeMCEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=VoNR
ueGroupList 1
end
$LTEFIX = yes
endfunc


func N2NFREQ
$NOProf = no
mr NRFPRrel
ma NRFPRrel GNBCUCPFunction=1,NRCellCU=$SCell,NRFreqRelation=
for $y in NRFPRrel
get $y nRFrequencyRef > $TFREQ_NR
$TFREQ_NR = $TFREQ_NR -s NRNetwork=1,NRFrequency=
$TFREQ_NR = $TFREQ_NR -s -.*

#####MCPC-PCELL######
get $y mcpcPCellNrFreqRelProfileRef > $MCPC_NR
if $MCPC_NR !~ ^Mcpc
$NOProf = yes
fi
pr Mcpc=1,McpcPCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR
if $nr_of_mos = 0 && $NOProf = no
get $MCPC_NR$ mcpcPCellNrFreqRelProfileId > $MCPC_ID
u+s $tempdir/$nodename_MCPC.mos
ldel $MCPC_NR$
y
u-
l sed -i 's/McpcPCellNrFreqRelProfile=$MCPC_ID/McpcPCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR/g' $tempdir/$nodename_MCPC.mos
run1 $tempdir/$nodename_MCPC.mos
set $y mcpcPCellNrFreqRelProfileRef Mcpc=1,McpcPCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR
l rm -f $tempdir/$nodename_MCPC.mos
else if $NOProf = no 
set $y mcpcPCellNrFreqRelProfileRef Mcpc=1,McpcPCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR
fi
ld Mcpc=1,McpcPCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VONR
pr Mcpc=1,McpcPCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR,McpcPCellNrFreqRelProfileUeCfg=VONR
if $nr_of_mos = 0
NRMCPC_VONR
fi

#####MCPC-PSCELL######
$NOProf = no
get $y mcpcPSCellNrFreqRelProfileRef > $MCPCNSA_NR
if $MCPCNSA_NR !~ ^Mcpc
$NOProf = yes
fi
pr Mcpc=1,McpcPSCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR
if $nr_of_mos = 0 && $NOProf = no
get $MCPCNSA_NR$ mcpcPSCellNrFreqRelProfileId > $MCPCNSA_ID
u+s $tempdir/$nodename_MCPC_NSA.mos
ldel $MCPCNSA_NR$
y
u-
l sed -i 's/McpcPSCellNrFreqRelProfile=$MCPCNSA_ID/McpcPSCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR/g' $tempdir/$nodename_MCPC_NSA.mos
run1 $tempdir/$nodename_MCPC_NSA.mos
set $y mcpcPSCellNrFreqRelProfileRef Mcpc=1,McpcPSCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR
l rm -f $tempdir/$nodename_MCPC_NSA.mos
else if $NOProf = no
set $y mcpcPSCellNrFreqRelProfileRef Mcpc=1,McpcPSCellNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR
fi

#####UEMC######
$NOProf = no
get $y ueMCNrFreqRelProfileRef > $UEMC_NR
if $UEMC_NR !~ ^UeMC
$NOProf = yes
fi
pr UeMC=1,UeMCNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR
if $nr_of_mos = 0 && $NOProf = no
get $UEMC_NR$ ueMCNrFreqRelProfileId > $UEMC_ID
u+s $tempdir/$nodename_UEMC.mos
ldel $UEMC_NR$
y
u-
l sed -i 's/UeMCNrFreqRelProfile=$UEMC_ID/UeMCNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR/g' $tempdir/$nodename_UEMC.mos
run1 $tempdir/$nodename_UEMC.mos
set $y ueMCNrFreqRelProfileRef  UeMC=1,UeMCNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR
l rm -f $tempdir/$nodename_UEMC.mos
else if $NOProf = no
set $y ueMCNrFreqRelProfileRef  UeMC=1,UeMCNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR
fi
ld UeMC=1,UeMCNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VoNR
pr UeMC=1,UeMCNrFreqRelProfile=$TFREQ_NR_$SBAND_$SCARR,UeMCNrFreqRelProfileUeCfg=VoNR
if $nr_of_mos = 0
NRUEMC_VONR
fi
$NOProf = no
done

endfunc


func N2LFREQ
$NOProf = no
mr N2LFPRrel
ma N2LFPRrel GNBCUCPFunction=1,NRCellCU=$SCell,EUtranFreqRelation=
for $x in N2LFPRrel
get $x eUtranFrequencyRef > $TFREQ_LTE
$TFREQ_LTE = $TFREQ_LTE -s GNBCUCPFunction=1,EUtraNetwork=1,EUtranFrequency=
$TFREQ_LTE = $TFREQ_LTE -s -.*

#####MCPC_IRAT-PCELL######
get $x mcpcPCellEUtranFreqRelProfileRef > $MCPC_LTE
if $MCPC_LTE !~ Mcpc
$NOProf = yes
fi
pr Mcpc=1,McpcPCellEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR
if $nr_of_mos = 0 && $NOProf = no
get $MCPC_LTE$ mcpcPCellEUtranFreqRelProfileId > $MCPCIRAT_ID
u+s $tempdir/$nodename_MCPC_IRAT.mos
ldel $MCPC_LTE$
y
u-
l sed -i 's/McpcPCellEUtranFreqRelProfile=$MCPCIRAT_ID/McpcPCellEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR/g' $tempdir/$nodename_MCPC_IRAT.mos
run1 $tempdir/$nodename_MCPC_IRAT.mos
set $x mcpcPCellEUtranFreqRelProfileRef Mcpc=1,McpcPCellEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR
l rm -f $tempdir/$nodename_MCPC_IRAT.mos
else if $NOProf = no
set $x mcpcPCellEUtranFreqRelProfileRef Mcpc=1,McpcPCellEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR
fi
ld Mcpc=1,McpcPCellEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR,McpcPCellEUtranFreqRelProfileUeCfg=VoNR
pr Mcpc=1,McpcPCellEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR,McpcPCellEUtranFreqRelProfileUeCfg=VoNR
if $nr_of_mos = 0
LTEMCPC_VONR
fi


#####UEMC_IRAT######
$NOProf = no
get $x ueMCEUtranFreqRelProfileRef > $UEMC_LTE
if $UEMC_LTE !~ UeMC
$NOProf = yes
fi
pr UeMC=1,UeMCEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR
if $nr_of_mos = 0 && $NOProf = no
get $UEMC_LTE$ ueMCEUtranFreqRelProfileId > $UEMC_IRAT_ID
u+s $tempdir/$nodename_UEMC_IRAT.mos
ldel $UEMC_LTE$
y
u-
l sed -i 's/UeMCEUtranFreqRelProfile=$UEMC_IRAT_ID/UeMCEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR/g' $tempdir/$nodename_UEMC_IRAT.mos
run1 $tempdir/$nodename_UEMC_IRAT.mos
set $x ueMCEUtranFreqRelProfileRef  UeMC=1,UeMCEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR
l rm -f $tempdir/$nodename_UEMC_IRAT.mos
else if $NOProf = no
set $x ueMCEUtranFreqRelProfileRef  UeMC=1,UeMCEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR
fi
ld UeMC=1,UeMCEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=VoNR
pr UeMC=1,UeMCEUtranFreqRelProfile=$TFREQ_LTE_$SBAND_$SCARR,UeMCEUtranFreqRelProfileUeCfg=VoNR
if $nr_of_mos = 0
LTEUEMC_VONR
fi
$NOProf = no
done
endfunc



mr NRFPRCell
ma NRFPRCell GNBCUCPFunction=1,NRCellCU nRCellCUId ^[A|K|J|I]
$SCell = 
$SBAND = 
$SCARR =
$NOProf = no
$LTEFIX = no
$NRFIX = no

for $mo in NRFPRCell
$rdn = rdn($mo)
$SCell = $rdn  -s NRCellCU=
$SCARR = `$gawk -v CelName=$SCell 'BEGIN {print  substr(CelName,11,1) }'`
if $SCell ~ ^A
$SBAND = N2500
else if $SCell ~ ^K
$SBAND = N600
else if $SCell ~ ^J
$SBAND = N1900
else if $SCell ~ ^I
$SBAND = N2100
fi
N2NFREQ
N2LFREQ
if $LTEFIX = yes
LTEPRF_Baseline
fi

if $NRFIX = yes
NRPRF_Baseline
fi
$SCell = 
$SBAND = 
$SCARR =
$LTEFIX = no
$NRFIX = no
done


####################################fixing and missing profile########################
mr MCPCMISS 
ma MCPCMISS NRFreqRelation= mcpcPCellNrFreqRelProfileRef !Mcpc

pr mcpcmiss
if $nr_of_mos > 0
run $tempdir/NRFREQOFFSET_FIX_$nodename.mos
fi


mr MCPCIRAT
ma MCPCIRAT EUtranFreqRelation= mcpcPCellEUtranFreqRelProfileRef !Mcpc

pr MCPCIRAT
if $nr_of_mos > 0
run $tempdir/NRFREQOFFSET_FIX_$nodename.mos
fi

mr MCPCPSCELL
ma MCPCPSCELL NRFreqRelation= mcpcPSCellNrFreqRelProfileRef !Mcpc

pr MCPCPSCELL
if $nr_of_mos > 0
RUNPSCELLFIX
fi



#############################################################################
###### change McpcPSCellProfile from per node to per cell and copy exsiting## 

mr CELLPSCELL
ma CELLPSCELL ,NRCellCU=

for $mo in CELLPSCELL
$CPSCELLID = 
$CrDN = rdn($mo)
get $mo nRCellCUId > $cellname
get $mo mcpcPSCellProfileRef > $PSCELLREF
if $PSCELLREF ~ ^Mcpc
get $PSCELLREF mcpcPSCellProfileId > $CPSCELLID
else
$CPSCELLID = NO
fi
if $CPSCELLID != $cellname && $CPSCELLID != NO
u+s $tempdir/$nodename_PSCELL.mos
uv use_crn=0
del $PSCELLREF$
u-
uv use_crn=1
l sed -i 's/McpcPSCellProfile=$CPSCELLID/McpcPSCellProfile=$cellname/g' $tempdir/$nodename_PSCELL.mos
run1 $tempdir/$nodename_PSCELL.mos
set $mo mcpcPSCellProfileRef Mcpc=1,McpcPSCellProfile=$cellname
l rm -f $tempdir/$nodename_PSCELL.mos
fi
if $CPSCELLID = NO
crn GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile=$cellname
ueConfGroupType 0
userLabel 
end
set $CrDN$ mcpcPSCellProfileRef Mcpc=1,McpcPSCellProfile=$cellname

ld GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile=$cellname,McpcPSCellProfileUeCfg=Base$

lset GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile=$cellname,McpcPSCellProfileUeCfg=Base$ lowHighFreqPrioClassification 5
lset GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile=$cellname,McpcPSCellProfileUeCfg=Base$ mcpcQuantityList 0
lset GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile=$cellname,McpcPSCellProfileUeCfg=Base$ rsrpCandidateA5 hysteresis=10,threshold1=-80,threshold2=-112,timeToTrigger=640
lset GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile=$cellname,McpcPSCellProfileUeCfg=Base$ rsrpCritical hysteresis=10,threshold=-116,timeToTrigger=320
lset GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile=$cellname,McpcPSCellProfileUeCfg=Base$ rsrpCriticalEnabled true
lset GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile=$cellname,McpcPSCellProfileUeCfg=Base$ rsrpSearchTimeRestriction -1
lset GNBCUCPFunction=1,Mcpc=1,McpcPSCellProfile=$cellname,McpcPSCellProfileUeCfg=Base$ rsrpSearchZone hysteresis=10,threshold=-80,timeToTrigger=320,timeToTriggerA1=-1
fi
done

##########################################################################


####Cleanup of not used profiles ###############

###MCPC_PCELL#####
mr NORELMCPC_SA
ma NORELMCPC_SA McpcPCellNrFreqRelProfile= reservedBy !NRFreqRelation
mr NORELMCPC_SA McpcPCellNrFreqRelProfile=Default
mr NORELMCPC_SA McpcPCellNrFreqRelProfile=.*N1900_2
pr NORELMCPC_SA
if $nr_of_mos > 0
del norelmcpc_sa
fi


###MCPC_PSCELL#####
mr NORELMCPC_NSA
ma NORELMCPC_NSA McpcPSCellNrFreqRelProfile= reservedBy !NRFreqRelation
mr NORELMCPC_NSA McpcPSCellNrFreqRelProfile=Default
mr NORELMCPC_NSA McpcPSCellNrFreqRelProfile=.*N1900_2
pr NORELMCPC_NSA
if $nr_of_mos > 0
del NORELMCPC_NSA
fi

###MCPC_PSCELL#####
mr NORELUEMC
ma NORELUEMC UeMCNrFreqRelProfile= reservedBy !NRFreqRelation
mr NORELUEMC UeMCNrFreqRelProfile=Default
pr NORELUEMC
if $nr_of_mos > 0
del NORELUEMC
fi


###MCPC_IRAT_PCELL#####
mr NORELIRAT_MC
ma NORELIRAT_MC McpcPCellEUtranFreqRelProfile= reservedBy !EUtranFreqRelation
mr NORELIRAT_MC McpcPCellEUtranFreqRelProfile=Default
pr NORELIRAT_MC
if $nr_of_mos > 0
del NORELIRAT_MC
fi


###MCPC_IRAT_PSCELL#####
mr NORELITAR_UEMC
ma NORELITAR_UEMC UeMCEUtranFreqRelProfile= reservedBy !EUtranFreqRelation
mr NORELITAR_UEMC UeMCEUtranFreqRelProfile=Default
pr NORELITAR_UEMC
if $nr_of_mos > 0
del NORELITAR_UEMC
fi

###MCPC_IRAT_PSCELL#####
mr NOPSCELLREF
ma NOPSCELLREF McpcPSCellProfile= reservedBy !GNBCUCPFunction
mr NOPSCELLREF McpcPSCellProfile=Default
pr NOPSCELLREF
if $nr_of_mos > 0
del NOPSCELLREF
fi

l rm -f $tempdir/NRFREQOFFSET_FIX_$nodename.mos
confb-
gs-

            """
        ]

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

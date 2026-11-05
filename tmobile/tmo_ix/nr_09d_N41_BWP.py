from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base
import re


class nr_09d_N41_BWP(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.addcell].index) == 0: return
        if self.df_gnb_cell.loc[(self.df_gnb_cell.addcell & self.df_gnb_cell.postcell.str.startswith('A'))].shape[0] == 0: return
        if len(self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.startswith('A'))].bschannelbwdl.unique()) < 2: return
        self.script_list += self.bwp_settings()
        if len(self.script_list) > 0:
            self.script_list = self.activity_check('Pre') + self.script_list + self.activity_check('Post')

    def bwp_settings(self):
        lines = ["""
         
####:----------------> BWP Setting <----------------:####
#####################################################################
#### Service level parameter configuration ##########################
#####################################################################
####NDPO & NURBS creation for BW 40 50 60 70 80 90 100 ####
#### BW 100 80 60 40 NDPO only####
#### BW 50 70 90 NURBS built on top of NPDO - Combined ####
#### BW 30 Scenario not considered as per national feedback BW 30 is for NSA ####

pr BWPSetUeCfg=UL_Grant
if $nr_of_mos != 0
    $UL_Grant_Var = Yes
fi

func numberOfRBs_setting_Even
    if $BWD = 100
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 273
      $BWS = 1
    else if $BWD = 90
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 245
      $BWS = 2
    else if $BWD = 80
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 217
      $BWS = 3
    else if $BWD = 70
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 189
      $BWS = 4
    else if $BWD = 60
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 162
      $BWS = 5
    else if $BWD = 50
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 133
      $BWS = 6
    else if $BWD = 40
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 106
      $BWS = 7
    fi
endfunc

func numberOfRBs_setting_Odd
    if $BWD = 100
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 245
      set GNBDUFunction=1,BWP=BW$BWD.*_FBWP$ numberOfRBs 273 
      $BWS = 1
    else if $BWD = 90
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 217
      set GNBDUFunction=1,BWP=BW$BWD.*_FBWP$ numberOfRBs 245
      $BWS = 2
    else if $BWD = 80
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 189
      set GNBDUFunction=1,BWP=BW$BWD.*_FBWP$ numberOfRBs 217
      $BWS = 3
    else if $BWD = 70
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 162
      set GNBDUFunction=1,BWP=BW$BWD.*_FBWP$ numberOfRBs 189
      $BWS = 4
    else if $BWD = 60
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 133
      set GNBDUFunction=1,BWP=BW$BWD.*_FBWP$ numberOfRBs 162
      $BWS = 5
    else if $BWD = 50
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 106
      set GNBDUFunction=1,BWP=BW$BWD.*_FBWP$ numberOfRBs 133
      $BWS = 6
    else if $BWD = 40
      set GNBDUFunction=1,BWP=BW$BWD numberOfRBs 78
      set GNBDUFunction=1,BWP=BW$BWD.*_FBWP$ numberOfRBs 106
      $BWS = 7
    fi
endfunc

func BW_P_40M_OR_HIGHER
    set FeatureState=CXC4012606 featureState 1
    ## Remove Existing References and BWP  configuration ##
    set TDDN41CELL_ALL bWPRef
    set TDDN41CELL_ALL bWPSetRef
    del UeServiceGroupDefinition=
    del GNBDUFunction=1,BWPSet=
    del GNBDUFunction=1,BWP=

    #### DACM - Data aware Carrier Management feature -required for BWP as pre-requisite since BWP not working when SCell is configured ####
    get GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2 selectionCriteria
    if $nr_of_mos = 0
    crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2
    ueGroupId 2
    ueGroupPriority 15
    selectionCriteria 5qi>=5
    end
    fi

    get GNBDUFunction=1,UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg= ueGroupList 1.*2
    if $nr_of_mos = 0
    crn UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA
    sCellActDeactDataThres 100
    sCellActDeactDataThresHyst 20
    sCellDeactDelayTimer 80
    sCellActProhibitTimer 10
    sCellDeactProhibitTimer 250
    ueGroupList 1 2
    prefUeGroupList 
    end
    fi

    set UeGroupSelectionProfile=2 selectionCriteria 5qi>=5
    set CaSCellHandlingUeCfg=SA uegrouplist 1 2 

    #### Reconfigure Service Groups ###
    crn GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=1
    selectionCriteria 5qi==1
    ueServiceGroupId 10
    ueServiceGroupPriority 100
    userLabel R16VoNR
    end

    crn GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=2
    selectionCriteria rfsp==200
    ueServiceGroupId 11
    ueServiceGroupPriority 101
    userLabel Allowlist Data
    end

    crn GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=3
    selectionCriteria 5qi==1 && rfsp==200
    ueServiceGroupId 12
    ueServiceGroupPriority 102
    userLabel Allowlist VoNR
    end

endfunc

func BWPCONF_Odd
    ///////////////////////////////////////////////
    ///  Odd FULL BWP_Activation
    /////////////////////////////////////////////

    ###activate the feature 'NR Dynamic Power Optimizer'
    get Lm=1,FeatureState=CXC4012607 featureState$ > $NRDPO
    if $NRDPO ~ 0
        set FeatureState=CXC4012607 featureState 1
    fi

    #### Enable 23.Q2 UL enhancement ####
    #scw RP2166:1
    set NRCellDU= improvedUlInSparseBwp true

    #### Enable 23.Q2 max sparse users enhancement - DEFAULT VALUE 900 ####
    set NRCellDU= maxNoOfUeInSparseBwp 900

    #### Enable 23.Q2 poor coverage enhancement - DEFAULT VALUES hyst=3 ####
    set NRCellDU=  poorRadioQualDciBwpSwitchThr 18
    set NRCellDU=  qualHystDciBwpSwitch 3

    # creates BWP MOs, Inital, Dense and Sparse#
    # numberOfRbs should correlate to carrier bandwidth #
    cr GNBDUFunction=1,BWP=BW$BWD_Init_DL
    cr GNBDUFunction=1,BWP=BW$BWD_Init_UL
    cr GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_PBWP
    cr GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_PBWP
    cr GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_PBWP
    cr GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_PBWP
    cr GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_FBWP
    cr GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_FBWP
    cr GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_FBWP
    cr GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_FBWP

    numberOfRBs_setting_Odd
     
    set GNBDUFunction=1,BWP=BW$BWD isInitialBwp false
    set GNBDUFunction=1,BWP=BW$BWD_Init_DL isInitialBwp true
    set GNBDUFunction=1,BWP=BW$BWD_Init_UL isInitialBwp true
    set GNBDUFunction=1,BWP=BW$BWD_Init_UL bwpContext 1
    set GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL  bwpContext 1
    set GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL bwpContext 1

    #### create BWPset MO, including BWPSetUeCfg=1, and the children MOs BWPSetCfg=0&1, and DynPowerOpt=1 MO for BWP data threshold ##

    cr1x GNBDUFunction=1,BWPSet=$BWS
    cr1x GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1
    set1x GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1 upDlThreshold 100
    set1x GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1 upUlThreshold 100
    set1x GNBDUFunction=1,BWPSet=$BWS allBWPRegularRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_FBWP GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_PBWP GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_FBWP GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_PBWP GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_FBWP GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_PBWP GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_FBWP GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_PBWP
    set1x GNBDUFunction=1,BWPSet=$BWS startBWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_PBWP
    set1x GNBDUFunction=1,BWPSet=$BWS startBWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_PBWP
    cr1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1 userLabel R16Data
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1,BWPSetCfg=0
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_PBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_PBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1,BWPSetCfg=1
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_PBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_PBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1,BWPSetCfg=2
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_FBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_FBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1,BWPSetCfg=3
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_FBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_FBWP
    end
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1,BWPSetCfg=1 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1,BWPSetCfg=3 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1
    commit

    #### create VoNR BWP Threshold####
    cr GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2
    set GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2 upDlThreshold 30
    set GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2 upUlThreshold 30

    #creates simultaneously  BWPSetUeCfg=2 and children MOs, Allowlist Data####

    cr1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2 userLabel AllowlistData
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2 ueConfGroupList 11 
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2 bwpSwitchingFilterRelaxation true
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2,BWPSetCfg=0
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_PBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_PBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2,BWPSetCfg=1
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_PBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_PBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2,BWPSetCfg=2
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_FBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_FBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2,BWPSetCfg=3
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_FBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_FBWP
    end
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2,BWPSetCfg=1 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2,BWPSetCfg=3 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1
    commit

    #creates simultaneously  BWPSetUeCfg=3 and children MOs ---Allowlist VoNR####
    cr1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3 userLabel 
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3 ueConfGroupList 12
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3 bwpSwitchingFilterRelaxation true
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3,BWPSetCfg=0
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_PBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_PBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3,BWPSetCfg=1
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_PBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_PBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3,BWPSetCfg=2
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_FBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_FBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3,BWPSetCfg=3
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_FBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_FBWP
    end
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3,BWPSetCfg=1 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3,BWPSetCfg=3 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2
    commit

    #### create BWPSetUeCfg=4 MO for R16VoNR##
    cr1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4 userLabel R16VoNR
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4 ueConfGroupList 10 
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4,BWPSetCfg=0
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_PBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_PBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4,BWPSetCfg=1
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_PBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_PBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4,BWPSetCfg=2
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL_FBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL_FBWP
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4,BWPSetCfg=3
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL_FBWP
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL_FBWP
    end
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4,BWPSetCfg=1 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4,BWPSetCfg=3 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2
    commit

    # NR cell points to inital BWPs
    set $NRTCell$ bwpref GNBDUFunction=1,BWP=BW$BWD_Init_DL GNBDUFunction=1,BWP=BW$BWD_Init_UL
    set $NRTCell$ bWPSetRef GNBDUFunction=1,BWPSet=$BWS

endfunc


func BWPCONF_Even
    ///////////////////////////////////////////////
    ///  Even FULL BWP_Activation
    /////////////////////////////////////////////

    ###activate the feature 'NR Dynamic Power Optimizer'
    get Lm=1,FeatureState=CXC4012607 featureState$ > $NRDPO
    if $NRDPO ~ 0
    set FeatureState=CXC4012607 featureState 1
    fi

    #### Enable 23.Q2 UL enhancement ####
    #scw RP2166:1
    #set NRCellDU= improvedUlInSparseBwp true

    #### Enable 23.Q2 max sparse users enhancement - DEFAULT VALUE 900 ####
    #set NRCellDU= maxNoOfUeInSparseBwp 900

    #### Enable 23.Q2 poor coverage enhancement - DEFAULT VALUES thresh=5 hyst=3 ####
    #set NRCellDU=  poorRadioQualDciBwpSwitchThr 18
    #set NRCellDU=  qualHystDciBwpSwitch 3

    # creates BWP MOs, Inital, Dense and Sparse#
    # numberOfRbs should correlate to carrier bandwidth #
    cr GNBDUFunction=1,BWP=BW$BWD_Init_DL
    cr GNBDUFunction=1,BWP=BW$BWD_Init_UL
    cr GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL
    cr GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL
    cr GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL
    cr GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL

    numberOfRBs_setting_Even
     
    set GNBDUFunction=1,BWP=BW$BWD isInitialBwp false
    set GNBDUFunction=1,BWP=BW$BWD_Init_DL isInitialBwp true
    set GNBDUFunction=1,BWP=BW$BWD_Init_UL isInitialBwp true
    set GNBDUFunction=1,BWP=BW$BWD_Init_UL bwpContext 1
    set GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL  bwpContext 1
    set GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL bwpContext 1

    #### create BWPset MO, including BWPSetUeCfg=1, and the children MOs BWPSetCfg=0&1, and DynPowerOpt=1 MO for BWP data threshold ##

    cr1x GNBDUFunction=1,GNBDUFunction=1,BWPSet=$BWS
    cr1x GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1
    set1x GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1 upDlThreshold 100
    set1x GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1 upUlThreshold 100
    set1x GNBDUFunction=1,BWPSet=$BWS allBWPRegularRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL
    set1x GNBDUFunction=1,BWPSet=$BWS startBWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL
    set1x GNBDUFunction=1,BWPSet=$BWS startBWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL
    cr1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1 userLabel R16Data
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1,BWPSetCfg=0
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1,BWPSetCfg=1
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL
    end
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=1,BWPSetCfg=1 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1
    commit

    #### create VoNR BWP Threshold####
    cr GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2
    set GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2 upDlThreshold 30
    set GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2 upUlThreshold 30

    #creates simultaneously  BWPSetUeCfg=2 and children MOs, Allowlist Data####

    cr1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2 userLabel AllowlistData
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2 ueConfGroupList 11 
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2 bwpSwitchingFilterRelaxation true
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2,BWPSetCfg=0
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2,BWPSetCfg=1
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL
    end
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=2,BWPSetCfg=1 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=1
    commit

    #creates simultaneously  BWPSetUeCfg=3 and children MOs ---Allowlist VoNR####
    cr1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3 userLabel AllowlistVoNR
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3 ueConfGroupList 12 
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3 bwpSwitchingFilterRelaxation true
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3,BWPSetCfg=0
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3,BWPSetCfg=1
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL
    end
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=3,BWPSetCfg=1 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2
    commit

    #### create BWPSetUeCfg=4 MO for R16VoNR##
    cr1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4 userLabel R16VoNR
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4 ueConfGroupList 10 
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4,BWPSetCfg=0
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_DL
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_DenseSS_UL
    end
    crn1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4,BWPSetCfg=1
    bWPDlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_DL
    bWPUlRef GNBDUFunction=1,BWP=BW$BWD_SparseSS_UL
    end
    set1x GNBDUFunction=1,BWPSet=$BWS,BWPSetUeCfg=4,BWPSetCfg=1 dynPowerOptRef GNBDUFunction=1,BWPSet=$BWS,DynPowerOpt=2
    commit

    # NR cell points to inital BWPs
    set $NRTCell$ bwpref GNBDUFunction=1,BWP=BW$BWD_Init_DL GNBDUFunction=1,BWP=BW$BWD_Init_UL
    set $NRTCell$ bWPSetRef GNBDUFunction=1,BWPSet=$BWS

endfunc

####Group all N41 cells C1/C2 and add BWP & NURBS#####

st NRCellDU=A
if $nr_of_mos = 0
    l echo "BWP is supported only on NR41 nodes but this site has no Cell start with NRCellDU=A"
else
    $40MORHIGH = no
    $Even_BW = 0
    $Odd_BW = 0
fi

mr SEC_CAR
mr SEC_BWP
mr TDDN41CELL_ALL 
ma SEC_CAR GNBDUFunction=1,NRCellDU=A nRSectorCarrierRef
ma SEC_BWP SEC_CAR bSChannelBwDL  40|50|60|70|80|90|100
ma TDDN41CELL_ALL SEC_BWP reservedBy
st TDDN41CELL_ALL
if $nr_of_mos > 0
    $40MORHIGH = yes
    BW_P_40M_OR_HIGHER
else
    l echo "BWP and NURBS are supported only BW >= 40 but site has less BW"
fi

mr SEC_CAR
mr SEC_BWP_Even
mr SEC_BWP_Odd
mr TDDN41CELL_Even
mr TDDN41CELL_Odd
ma SEC_CAR GNBDUFunction=1,NRCellDU=A nRSectorCarrierRef
ma SEC_BWP_Even SEC_CAR bSChannelBwDL  40|50|60|70|80|100
ma SEC_BWP_Odd SEC_CAR bSChannelBwDL   90
ma TDDN41CELL_Even SEC_BWP_Even reservedBy
ma TDDN41CELL_Odd SEC_BWP_Odd reservedBy
st TDDN41CELL_Even
if $nr_of_mos > 0
    $40MORHIGH = yes
    $Even_BW = 1
fi

st TDDN41CELL_Odd
if $nr_of_mos > 0
    $40MORHIGH = yes
    $Odd_BW = 1
fi

func BWPconfig_Even
    for $mo in TDDN41CELL_Even
        $NRTCell = rdn($mo)
        mr SECTR
        ma SECTR $mo nRSectorCarrierRef
        get SECTR bSChannelBwDL > $BWD
        pr GNBDUFunction=1,BWP=BW$BWD_Init_DL
        if $nr_of_mos = 0
            BWPCONF_Even
        else
            numberOfRBs_setting_Even
            set $NRTCell$ bwpref GNBDUFunction=1,BWP=BW$BWD_Init_DL GNBDUFunction=1,BWP=BW$BWD_Init_UL
            set $NRTCell$ bWPSetRef GNBDUFunction=1,BWPSet=$BWS
        fi
        get $NRTCell caSCellHandlingRef > $CHECK_DACM
        if $CHECK_DACM !~ CaSCellHandling
            set $NRTCell$ caSCellHandlingRef UeCA=1,CaSCellHandling=1
        fi
    done
endfunc

func BWPconfig_Odd
    for $mo in TDDN41CELL_Odd
        $NRTCell = rdn($mo)
        mr SECTR
        ma SECTR $mo nRSectorCarrierRef
        get SECTR bSChannelBwDL > $BWD
        pr GNBDUFunction=1,BWP=BW$BWD_Init_DL
        if $nr_of_mos = 0
            BWPCONF_Odd
        else
            numberOfRBs_setting_Odd
            set $NRTCell$ bwpref GNBDUFunction=1,BWP=BW$BWD_Init_DL GNBDUFunction=1,BWP=BW$BWD_Init_UL
            set $NRTCell$ bWPSetRef GNBDUFunction=1,BWPSet=$BWS
        fi
        get $NRTCell caSCellHandlingRef > $CHECK_DACM
        if $CHECK_DACM !~ CaSCellHandling
            set $NRTCell$ caSCellHandlingRef UeCA=1,CaSCellHandling=1
        fi
    done

endfunc

if $40MORHIGH = yes && $Even_BW = 1
    BWPconfig_Even
fi

if $40MORHIGH = yes && $Odd_BW = 1
    BWPconfig_Odd
fi

func UL_Grant_create
    for $mo in BWP_DEF
        $NOMBRE = ldn($mo)
        lpr  $NOMBRE,BWPSetUeCfg=1,BWPSetCfg=
        if $nr_of_mos = 2
            get $NOMBRE,BWPSetUeCfg=1,BWPSetCfg=0 bWPDlRef > $DLBWP
            get $NOMBRE,BWPSetUeCfg=1,BWPSetCfg=0 bWPUlRef > $ULBWP
            cr1x $NOMBRE,BWPSetUeCfg=UL_Grant
            cr1x $NOMBRE,BWPSetUeCfg=UL_Grant,BWPSetCfg=0
            $DLBWP
            $ULBWP
        else if $nr_of_mos = 4
            get $NOMBRE,BWPSetUeCfg=1,BWPSetCfg=0 bWPDlRef > $DLBWP
            get $NOMBRE,BWPSetUeCfg=1,BWPSetCfg=0 bWPUlRef > $ULBWP
            get $NOMBRE,BWPSetUeCfg=1,BWPSetCfg=2 bWPDlRef > $DLBWP_1
            get $NOMBRE,BWPSetUeCfg=1,BWPSetCfg=2 bWPUlRef > $ULBWP_2
            cr1x $NOMBRE,BWPSetUeCfg=UL_Grant
            cr1x $NOMBRE,BWPSetUeCfg=UL_Grant,BWPSetCfg=0
            $DLBWP
            $ULBWP
            cr1x $NOMBRE,BWPSetUeCfg=UL_Grant
            cr1x $NOMBRE,BWPSetUeCfg=UL_Grant,BWPSetCfg=1
            $DLBWP_1
            $ULBWP_2
        fi
        set1x $NOMBRE,BWPSetUeCfg=UL_Grant ueGroupList 6
        commit
    done
endfunc

func UL_Grant_create_1
    mr BWP_DEF
    ma BWP_DEF GNBDUFunction=1,BWPset
    pr BWP_DEF
    if $nr_of_mos > 0
        UL_Grant_create
    fi
endfunc

if $UL_Grant_Var = Yes
    UL_Grant_create_1
fi

// Added - Pre-req to check if the Q1 BWP feature enhancement is set or not for SC RP1869:0.
get BWPSetUeCfg=2 bwpSwitchingFilterRelaxation$ > $BWPact
if $BWPact ~ false
    scw RP1869:0
fi

                 """]

        if self.usid.client.software.swname[:9] > 'TMO_25_Q4':
            lines += ["""
#### 26Q1 Update
#### BWP Nationwide Cleanup <> T-Mobile Copy Cleaned Up<>
func BWP_Modify_DPO
	set GNBDUFunction=1,$TBWP,BWPSetUeCfg=1  bwpSwitchingFilterRelaxation true
	set GNBDUFunction=1,$TBWP,BWPSetUeCfg=3  bwpSwitchingFilterRelaxation true
	set $TBWP,BWPSetUeCfg=2,BWPSetCfg=1 dynPowerOptRef    $TBWP,DynPowerOpt=2
	pr $TBWP,BWPSetUeCfg=2,BWPSetCfg=3
	if $nr_of_mos != 0
		set $TBWP,BWPSetUeCfg=2,BWPSetCfg=3 dynPowerOptRef    $TBWP,DynPowerOpt=2
	fi
	set GNBDUFunction=1,$TBWP,BWPSetUeCfg=2 userLabel R15_R16_VoNR
	set GNBDUFunction=1,$TBWP,BWPSetUeCfg=2 ueGroupList 1 
	set GNBDUFunction=1,$TBWP,BWPSetUeCfg=2 ueConfGroupList 
	set GNBDUFunction=1,$TBWP,BWPSetUeCfg=1 userLabel R15_R16_Data
	ldel GNBDUFunction=1,$TBWP,BWPSetUeCfg=3
	ldel GNBDUFunction=1,$TBWP,BWPSetUeCfg=4
endfunc

func Test_BWP
	if $FirstBWPS !~ $TBWP
		BWP_Modify_DPO
		$FirstBWPS = $TBWP
	fi
endfunc

mr BWPSECTOR
ma BWPSECTOR NRSectorCarrier  bSChannelBwDL 40|45|50|60|70|80|90|100
mr NRBWPREADY_Cell
ma NRBWPREADY_Cell BWPSECTOR reservedBy 
mr NR_BWP_MODIFY
ma NR_BWP_MODIFY NRBWPREADY_Cell bWPSetRef BWPSet

st NR_BWP_MODIFY
if $nr_of_mos != 0
	$FirstBWPS = 0
	for $mo in NR_BWP_MODIFY
		get $mo bWPSetRef > $TBWP
		Test_BWP
	done
fi
            """]
        return lines
    @staticmethod
    def activity_check(activity):
        return [F"""
####:----------------> {activity} Check <----------------:####
alt
scg
lpr GNBDUFunction=1,BWP=
lpr GNBDUFunction=1,BWPSet=
get NRCellDU= bwpref|bWPSetRef
       """]

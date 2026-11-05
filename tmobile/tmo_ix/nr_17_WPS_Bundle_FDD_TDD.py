import os
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_17_WPS_Bundle_FDD_TDD(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        # No Scripts for East Market
        if self.usid.client.mname in ['Salina', 'Bloomfield', 'EastProvidence', 'Norton']: return
        if self.df_gnb_cell.loc[self.df_gnb_cell.addcell].shape[0] == 0: return
        self.script_list += ["""
##############################
#### WPS 5Qi128 Bundle #######
##############################
confbl+
lt all
gs+

$date1 = `date +%y%m%d`
$jobname = 24Q2_WPS_Bundle_$date1
$log_dir = ~/$jobname
l if [ ! -d $log_dir ] ; then mkdir -p $log_dir; fi
$Error_log = $log_dir/$jobname_Error_$date1.log
$date = `date +%Y%m%d_%H%M%S` 


#####  CHECK FOR 24Q2 SW or higher and Exit Activation if not ######
get 0 swVersion > $SWV
$SWRel = $SWV -s .Q
if $SWRel < 242
    l echo $date1: $nodename -- SW version is earlier than 24Q2 >> $Error_log
    exit
fi

#########################################################
#### Remove SchedulingProfile 5qi7-9 except FWA SD_1000
####  Scheduling profiles on 5QI6 ONLY except FWA
#########################################################

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_2000_SST_1_5QI7
if $nr_of_mos = 1
    lset DU5qiTable=SD_2000,DU5qi=(7|8|9)   schedulingProfileRef
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_2000_SST_1_5QI7
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_2000_SST_1_5QI8
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_2000_SST_1_5QI9
fi
pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_4000_SST_1_5QI7
if $nr_of_mos = 1
    lset DU5qiTable=SD_4000,DU5qi=(7|8|9)   schedulingProfileRef
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_4000_SST_1_5QI7
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_4000_SST_1_5QI8
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_4000_SST_1_5QI9
fi
pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_6000_SST_1_5QI7
if $nr_of_mos = 1
    lset DU5qiTable=SD_6000,DU5qi=(7|8|9)   schedulingProfileRef
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_6000_SST_1_5QI7
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_6000_SST_1_5QI8
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_6000_SST_1_5QI9
fi
pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_7000_SST_1_5QI6
if $nr_of_mos = 1
    lset DU5qiTable=SD_7000,DU5qi=(6|7|8|9|128)   schedulingProfileRef
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_7000_SST_1_5QI6
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_7000_SST_1_5QI7
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_7000_SST_1_5QI8
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_7000_SST_1_5QI9
fi
pr GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_8000_SST_1_5QI7
if $nr_of_mos = 1
    lset DU5qiTable=SD_8000,DU5qi=(7|8|9)   schedulingProfileRef
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_8000_SST_1_5QI7
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_8000_SST_1_5QI8
    del GNBDUFunction=1,UeCC=1,SchedulingProfile=SD_8000_SST_1_5QI9
fi

#####################################
### Check for SD_7000 RRP and Remove
#####################################
pr GNBCUCPFunction=1,ResourcePartitions=1,ResourcePartition=SD_7000
if $nr_of_mos != 0
    ldel GNBCUCPFunction=1,ResourcePartitions=1,ResourcePartition=SD_7000,ResourcePartitionMember=1$
    ldel GNBCUCPFunction=1,ResourcePartitions=1,ResourcePartition=SD_7000$
fi

pr GNBDUFunction=1,ResourceAllocationPolicies=1,CellResourceMapping=1,PartitionMapping=SD_7000
if $nr_of_mos != 0
    ldel GNBDUFunction=1,ResourceAllocationPolicies=1,CellResourceMapping=1,PartitionMapping=SD_7000$
fi

lt all
################################################################
#### Check for Slicing 5Qi128 Table and create if missing 
################################################################
#################################
##### Check 5QITables are built
###################################
func 5qi128_TDD
    pr GNBDUFunction=1,DU5qiTable=$ID,DU5qi=128
    if $nr_of_mos = 0
        crn GNBDUFunction=1,DU5qiTable=$ID,DU5qi=128
        aqmMode 1
        drbRlcInDu5qiEnabled false
        drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
        drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=Default_other
        dscp 12
        estimatedE2ERTT 50
        l4sCfgRef
        logicalChannelGroupId 5
        logicalChannelRef GNBDUFunction=1,UeCC=1,LogicalChannel=Default
        packetDelayBudget 280
        packetDelayBudgetOffset 0
        pref5qiSrPeriodicityPool 1
        priorityLevel 45
        profile5qi 128
        puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
        schedulingProfileRef 
        srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
        userLabel
        end
    fi
    
    pr GNBCUUPFunction=1,CUUP5qiTable=$ID,CUUP5qi=128
    if $nr_of_mos = 0
        crn GNBCUUPFunction=1,CUUP5qiTable=$ID,CUUP5qi=128
        aqmMode 1
        counterActiveMode false
        dcDlPdcpAggrPrioCg 2
        dcDlPdcpAggrTimeDiffCg 2
        dcDlPdcpAggrTimeDiffProhibit 200
        dcDlPdcpAggrTimeDiffThresh 150
        drbRef GNBCUUPFunction=1,UeCC=1,Drb=Default_other
        dscp 12
        estimatedE2ERTT 50
        l4sCfgRef
        packetDelayBudget 280
        packetDelayBudgetOffset 0
        profile5qi 128
        tOooUlDelivery 150
        userLabel
        end
    fi
    
    pr GNBCUCPFunction=1,CUCP5qiTable=$ID,CUCP5qi=128
    if $nr_of_mos = 0
        crn GNBCUCPFunction=1,CUCP5qiTable=$ID,CUCP5qi=128
        nrdcSnTerminationRef
        pdcpSnSize 18
        profile5qi 128
        rlcMode 0
        tPdcpDiscard 750
        tReorderingDl 200
        tReorderingUl 200
        userLabel
        end
    fi
endfunc

get DU5qiTable=1$
if $nr_of_mos != 0
    $ID = 1
    5qi128_TDD
fi

get DU5qiTable=2$
if $nr_of_mos != 0
    $ID = 2
    5qi128_TDD
fi


lt DU5qi
pr GNBDUFunction=1,DU5qiTable=SD_7000
if $nr_of_mos = 0
    cr1x GNBDUFunction=1,DU5qiTable=SD_7000
    cr1x GNBDUFunction=1,DU5qiTable=SD_7000,DU5qi=6
    6
    set1x DU5qiTable=SD_7000,DU5qi=6 profile5qi 6
    set1x DU5qiTable=SD_7000,DU5qi=6 aqmMode 1
    set1x DU5qiTable=SD_7000,DU5qi=6 drbRlcInDu5qiEnabled false
    set1x DU5qiTable=SD_7000,DU5qi=6 drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
    set1x DU5qiTable=SD_7000,DU5qi=6 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=Default_other
    set1x DU5qiTable=SD_7000,DU5qi=6 dscp 12
    set1x DU5qiTable=SD_7000,DU5qi=6 estimatedE2ERTT 50
    set1x DU5qiTable=SD_7000,DU5qi=6 logicalChannelGroupId 5
    set1x DU5qiTable=SD_7000,DU5qi=6 logicalChannelRef GNBDUFunction=1,UeCC=1,LogicalChannel=Default
    set1x DU5qiTable=SD_7000,DU5qi=6 packetDelayBudget 280
    set1x DU5qiTable=SD_7000,DU5qi=6 packetDelayBudgetOffset 0
    set1x DU5qiTable=SD_7000,DU5qi=6 pref5qiSrPeriodicityPool 1
    set1x DU5qiTable=SD_7000,DU5qi=6 priorityLevel 55
    set1x DU5qiTable=SD_7000,DU5qi=6 puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default 
    set1x DU5qiTable=SD_7000,DU5qi=6 srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
    commit
fi

lt DU5qi
pr GNBDUFunction=1,DU5qiTable=SD_7001
if $nr_of_mos = 0
    cr1x GNBDUFunction=1,DU5qiTable=SD_7001
    cr1x GNBDUFunction=1,DU5qiTable=SD_7001,DU5qi=6
    6
    set1x DU5qiTable=SD_7001,DU5qi=6 profile5qi 6
    set1x DU5qiTable=SD_7001,DU5qi=6 aqmMode 1
    set1x DU5qiTable=SD_7001,DU5qi=6 drbRlcInDu5qiEnabled false
    set1x DU5qiTable=SD_7001,DU5qi=6 drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
    set1x DU5qiTable=SD_7001,DU5qi=6 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=Default_other
    set1x DU5qiTable=SD_7001,DU5qi=6 dscp 12
    set1x DU5qiTable=SD_7001,DU5qi=6 estimatedE2ERTT 50
    set1x DU5qiTable=SD_7001,DU5qi=6 logicalChannelGroupId 5
    set1x DU5qiTable=SD_7001,DU5qi=6 logicalChannelRef GNBDUFunction=1,UeCC=1,LogicalChannel=Default
    set1x DU5qiTable=SD_7001,DU5qi=6 packetDelayBudget 280
    set1x DU5qiTable=SD_7001,DU5qi=6 packetDelayBudgetOffset 0
    set1x DU5qiTable=SD_7001,DU5qi=6 pref5qiSrPeriodicityPool 1
    set1x DU5qiTable=SD_7001,DU5qi=6 priorityLevel 55
    set1x DU5qiTable=SD_7001,DU5qi=6 puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default 
    set1x DU5qiTable=SD_7001,DU5qi=6 srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
    commit
fi

lt DU5qi
lt CUUP5qi
pr GNBCUUPFunction=1,CUUP5qiTable=SD_7000
if $nr_of_mos = 0 
    cr1x GNBCUUPFunction=1,CUUP5qiTable=SD_7000
    cr1x CUUP5qiTable=SD_7000,CUUP5qi=6
    6
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 profile5qi 6
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 aqmMode 1
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 counterActiveMode false
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 dcDlPdcpAggrPrioCg 2
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 dcDlPdcpAggrTimeDiffCg 2
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 dcDlPdcpAggrTimeDiffProhibit 200
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 dcDlPdcpAggrTimeDiffThresh 150
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=Default_other
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 dscp 12
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 estimatedE2ERTT 50
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 packetDelayBudget 280
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 packetDelayBudgetOffset 0
    set1x CUUP5qiTable=SD_7000,CUUP5qi=6 tOooUlDelivery 150
    commit
fi

lt CUUP5qi
pr GNBCUUPFunction=1,CUUP5qiTable=SD_7001
if $nr_of_mos = 0 
    cr1x GNBCUUPFunction=1,CUUP5qiTable=SD_7001
    cr1x CUUP5qiTable=SD_7001,CUUP5qi=6
    6
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 profile5qi 6
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 aqmMode 1
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 counterActiveMode false
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 dcDlPdcpAggrPrioCg 2
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 dcDlPdcpAggrTimeDiffCg 2
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 dcDlPdcpAggrTimeDiffProhibit 200
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 dcDlPdcpAggrTimeDiffThresh 150
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=Default_other
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 dscp 12
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 estimatedE2ERTT 50
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 packetDelayBudget 280
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 packetDelayBudgetOffset 0
    set1x CUUP5qiTable=SD_7001,CUUP5qi=6 tOooUlDelivery 150
    commit
fi

lt CUUP5qi
pr GNBCUCPFunction=1,CUCP5qiTable=SD_7000
if $nr_of_mos = 0
    cr1x GNBCUCPFunction=1,CUCP5qiTable=SD_7000
    cr1x GNBCUCPFunction=1,CUCP5qiTable=SD_7000,CUCP5qi=6
    6
    set1x CUCP5qiTable=SD_7000,CUCP5qi=6 profile5qi 6
    set1x CUCP5qiTable=SD_7000,CUCP5qi=6 pdcpSnSize 18
    set1x CUCP5qiTable=SD_7000,CUCP5qi=6 rlcMode 0
    set1x CUCP5qiTable=SD_7000,CUCP5qi=6 tPdcpDiscard 750
    set1x CUCP5qiTable=SD_7000,CUCP5qi=6 tReorderingDl 200
    set1x CUCP5qiTable=SD_7000,CUCP5qi=6 tReorderingUl 200
    commit
fi

lt CUCP5qi
pr GNBCUCPFunction=1,CUCP5qiTable=SD_7001
if $nr_of_mos = 0
    cr1x GNBCUCPFunction=1,CUCP5qiTable=SD_7001
    cr1x GNBCUCPFunction=1,CUCP5qiTable=SD_7001,CUCP5qi=6
    6
    set1x CUCP5qiTable=SD_7001,CUCP5qi=6 profile5qi 6
    set1x CUCP5qiTable=SD_7001,CUCP5qi=6 pdcpSnSize 18
    set1x CUCP5qiTable=SD_7001,CUCP5qi=6 rlcMode 0
    set1x CUCP5qiTable=SD_7001,CUCP5qi=6 tPdcpDiscard 750
    set1x CUCP5qiTable=SD_7001,CUCP5qi=6 tReorderingDl 200
    set1x CUCP5qiTable=SD_7001,CUCP5qi=6 tReorderingUl 200
    commit
fi

lt CUCP5qi
pr GNBDUFunction=1,DU5qiTable=SD_7000,DU5qi=128
if $nr_of_mos = 0
    crn GNBDUFunction=1,DU5qiTable=SD_7000,DU5qi=128
    aqmMode 1
    drbRlcInDu5qiEnabled false
    drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
    drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=Default_other
    dscp 12
    estimatedE2ERTT 50
    l4sCfgRef
    logicalChannelGroupId 5
    logicalChannelRef GNBDUFunction=1,UeCC=1,LogicalChannel=Default
    packetDelayBudget 280
    packetDelayBudgetOffset 0
    pref5qiSrPeriodicityPool 1
    priorityLevel 45
    profile5qi 128
    puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
    schedulingProfileRef 
    srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
    userLabel
    end
fi

pr GNBCUUPFunction=1,CUUP5qiTable=SD_7000,CUUP5qi=128
if $nr_of_mos = 0
    crn GNBCUUPFunction=1,CUUP5qiTable=SD_7000,CUUP5qi=128
    aqmMode 1
    counterActiveMode false
    dcDlPdcpAggrPrioCg 2
    dcDlPdcpAggrTimeDiffCg 2
    dcDlPdcpAggrTimeDiffProhibit 200
    dcDlPdcpAggrTimeDiffThresh 150
    drbRef GNBCUUPFunction=1,UeCC=1,Drb=Default_other
    dscp 12
    estimatedE2ERTT 50
    l4sCfgRef
    packetDelayBudget 280
    packetDelayBudgetOffset 0
    profile5qi 128
    tOooUlDelivery 150
    userLabel
    end
fi

pr GNBCUCPFunction=1,CUCP5qiTable=SD_7000,CUCP5qi=128
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,CUCP5qiTable=SD_7000,CUCP5qi=128
    nrdcSnTerminationRef
    pdcpSnSize 18
    profile5qi 128
    rlcMode 0
    tPdcpDiscard 750
    tReorderingDl 200
    tReorderingUl 200
    userLabel
    end
fi

pr GNBDUFunction=1,DU5qiTable=SD_7001,DU5qi=128
if $nr_of_mos = 0
    crn GNBDUFunction=1,DU5qiTable=SD_7001,DU5qi=128
    aqmMode 1
    drbRlcInDu5qiEnabled false
    drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
    drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=Default_other
    dscp 12
    estimatedE2ERTT 50
    l4sCfgRef
    logicalChannelGroupId 5
    logicalChannelRef GNBDUFunction=1,UeCC=1,LogicalChannel=Default
    packetDelayBudget 280
    packetDelayBudgetOffset 0
    pref5qiSrPeriodicityPool 1
    priorityLevel 45
    profile5qi 128
    puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
    schedulingProfileRef 
    srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
    userLabel
    end
fi

pr GNBCUUPFunction=1,CUUP5qiTable=SD_7001,CUUP5qi=128
if $nr_of_mos = 0
    crn GNBCUUPFunction=1,CUUP5qiTable=SD_7001,CUUP5qi=128
    aqmMode 1
    counterActiveMode false
    dcDlPdcpAggrPrioCg 2
    dcDlPdcpAggrTimeDiffCg 2
    dcDlPdcpAggrTimeDiffProhibit 200
    dcDlPdcpAggrTimeDiffThresh 150
    drbRef GNBCUUPFunction=1,UeCC=1,Drb=Default_other
    dscp 12
    estimatedE2ERTT 50
    l4sCfgRef
    packetDelayBudget 280
    packetDelayBudgetOffset 0
    profile5qi 128
    tOooUlDelivery 150
    userLabel
    end
fi

pr GNBCUCPFunction=1,CUCP5qiTable=SD_7001,CUCP5qi=128
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,CUCP5qiTable=SD_7001,CUCP5qi=128
    nrdcSnTerminationRef
    pdcpSnSize 18
    profile5qi 128
    rlcMode 0
    tPdcpDiscard 750
    tReorderingDl 200
    tReorderingUl 200
    userLabel
    end
fi

lt all
#######################################
#### Create AqmCfg for SD7000 and 7001
#######################################
cr GNBCUUPFunction=1,UeCC=1,Drb=WPS_User
crn GNBCUUPFunction=1,UeCC=1,AqmCfg=WPS_User
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  56
tOooUlDelivery 150 
end

lt all
set GNBCUUPFunction=1,UeCC=1,Drb=WPS_User,DrbUeCfg=Base aqmCfgRef GNBCUUPFunction=1,UeCC=1,AqmCfg=WPS_User
set GNBCUUPFunction=1,UeCC=1,Drb=WPS_User,DrbUeCfg=Base dcDlCfgRef GNBCUUPFunction=1,UeCC=1,DcDlCfg=Default
set CUUP5qiTable=SD_7000,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=WPS_User
set CUUP5qiTable=SD_7001,CUUP5qi=6 drbRef GNBCUUPFunction=1,UeCC=1,Drb=WPS_User
set CUUP5qiTable=SD_7000,CUUP5qi=128 drbRef GNBCUUPFunction=1,UeCC=1,Drb=WPS_User
set CUUP5qiTable=SD_7001,CUUP5qi=128 drbRef GNBCUUPFunction=1,UeCC=1,Drb=WPS_User

cr GNBDUFunction=1,UeCC=1,DrbUp=WPS_User
crn GNBDUFunction=1,UeCC=1,AqmCfg=WPS_User
aqmMode 1
estimatedE2ERTT 50
tDiscardDl  56
end

lt all
set  GNBDUFunction=1,UeCC=1,DrbUp=WPS_User,DrbUpUeCfg=Base aqmCfgRef GNBDUFunction=1,UeCC=1,AqmCfg=WPS_User
set DU5qiTable=SD_7000,DU5qi=6 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=WPS_User
set DU5qiTable=SD_7001,DU5qi=6 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=WPS_User
set DU5qiTable=SD_7000,DU5qi=128 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=WPS_User
set DU5qiTable=SD_7001,DU5qi=128 drbUpRef GNBDUFunction=1,UeCC=1,DrbUp=WPS_User

#################################################################
### Check for SD_7000 and 7001 Scheduling Profiles and set 5x RPS
#################################################################
pr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128
    dlCaSchedulingMode 0
    essResourceAllocationMode 0
    relativePriority 128
    relativePriorityMode 0
    schedulingAlgorithm 1
    ulSchedulingAlgorithm
    userLabel WPS_Non_Slice_5QI128
    end
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128
    dlCaSchedulingMode 0
    essResourceAllocationMode 0
    relativePriority 128
    relativePriorityMode 2
    schedulingAlgorithm 1
    ulSchedulingAlgorithm
    userLabel WPS_First_Responder_5QI128
    end
fi


pr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI6
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI6
    dlCaSchedulingMode 0
    essResourceAllocationMode 0
    relativePriority 128
    relativePriorityMode 2
    schedulingAlgorithm 0
    ulSchedulingAlgorithm
    userLabel WPS_First_Responder_5QI6
    end
fi

lt all
set DU5qiTable=SD_7000,DU5qi=6 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI6
set DU5qiTable=SD_7001,DU5qi=6 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI6
set DU5qiTable=SD_7000,DU5qi=128 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128
set DU5qiTable=SD_7001,DU5qi=128 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI6 relativePriority 128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128 relativePriority 128
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI6 relativePriorityMode 2
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128 relativePriorityMode 2
set DU5qiTable=SD_7000,DU5qi=6 packetDelayBudget 56
set DU5qiTable=SD_7000,DU5qi=128 packetDelayBudget 56
set DU5qiTable=SD_7001,DU5qi=6 packetDelayBudget 56
set DU5qiTable=SD_7001,DU5qi=128 packetDelayBudget 56

##################################################################################
#####  Set Target Bit Rate SD_7000 SD_7001 and Regular 5Qi128 User for WPS
##################################################################################
##Pre checks (Enable the licenses CXC4012531 (Relative priority) and CXC4012475 (Absolute priority))
get CXC4012531
get CXC4012475
set CXC4012531 FeatureState 1 
set CXC4012475 FeatureState 1
get CXC4012659 FeatureState 
set CXC4012659 FeatureState 1


##Create the MO for NR Rate-controlled scheduling
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128,DlRateBasedPriority=1
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128,DlRateBasedPriority=1
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128,UlRateBasedPriority=1
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128,UlRateBasedPriority=1

lt all
## set bit rate as per the slice requirement
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128,DlRateBasedPriority=1 dlPrioritizedRate 600
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128,UlRateBasedPriority=1 ulPrioritizedRate 600
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128,DlRateBasedPriority=1 dlPrioritizedRate 1000
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128,UlRateBasedPriority=1 ulPrioritizedRate 600

##Check Dl/UlResourceBasedPriority Mo if not available then create it
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128,DlResourceBasedPriority=1
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128,DlResourceBasedPriority=1
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128,UlResourceBasedPriority=1
cr GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128,UlResourceBasedPriority=1

### schedulingAlgorithm set to PRIORITIZED_RATE
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128 schedulingAlgorithm 1
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128 schedulingAlgorithm 1
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI6 schedulingAlgorithm 0

### UL schedulingAlgorithm set to PRIORITIZED_RATE
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128 ulschedulingAlgorithm 1
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128 ulschedulingAlgorithm 1
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI6 ulschedulingAlgorithm 0

### set dlDemotedRelativePriority to true
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128,DlRateBasedPriority=1 dlDemotedRelativePriority true
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128,DlRateBasedPriority=1 dlDemotedRelativePriority true

### set ulDemotedRelativePriority to true
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128,UlRateBasedPriority=1 ulDemotedRelativePriority true
set GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_Slice_User_5QI128,UlRateBasedPriority=1 ulDemotedRelativePriority true

###################################################################
#### PrioirtyDomainMapping Check for Priority Controlled Scheduling
###################################################################
pr GNBDUFunction=1,QosPriorityMapping=1
if $nr_of_mos = 0
    crn GNBDUFunction=1,QosPriorityMapping=1
    end
fi

lt QosPriorityMapping
pr GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI1
if $nr_of_mos = 0
    crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI1
    priorityDomain 16
    priorityLevelsList 20
    end
fi

pr GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI2
if $nr_of_mos = 0
    crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI2
    priorityDomain 18
    priorityLevelsList 40
    end
fi

pr GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI5
if $nr_of_mos = 0
    crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI5
    priorityDomain 4
    priorityLevelsList 10
    end
fi

pr GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI6_7_8_9
if $nr_of_mos = 0 
    crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI6_7_8_9
    priorityDomain 48
    priorityLevelsList 60,70,80,90
    end
fi

lt priorityDomainMapping
##############################
#### Relative Priority Check
##############################
pr GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI6
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI6
    dlCaSchedulingMode 0
    essResourceAllocationMode 0
    relativePriority 128
    relativePriorityMode 0
    schedulingAlgorithm 0
    ulRelativePriority
    ulSchedulingAlgorithm
    userLabel NRSA_5QI6
    end
else 
    set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI6 relativePriority 128
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI7
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI7
    dlCaSchedulingMode 0
    essResourceAllocationMode 0
    relativePriority 32
    relativePriorityMode 0
    schedulingAlgorithm 0
    ulRelativePriority
    ulSchedulingAlgorithm
    userLabel NRSA_5QI7
    end
else 
    set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI7 relativePriority 32
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI8
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI8
    dlCaSchedulingMode 0
    essResourceAllocationMode 0
    relativePriority 16
    relativePriorityMode 0
    schedulingAlgorithm 0
    ulRelativePriority
    ulSchedulingAlgorithm
    userLabel NRSA_5QI8
    end
else 
    set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI8 relativePriority 16
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI9
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI9
    dlCaSchedulingMode 0
    essResourceAllocationMode 0
    relativePriority 8
    relativePriorityMode 0
    schedulingAlgorithm 0
    ulRelativePriority
    ulSchedulingAlgorithm
    userLabel NRSA_5QI9
    end
else 
    set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI9 relativePriority 8
fi

##Create new profile for  PriorityDomainMapping and give prioritydomain XX and set the priorityLevelsList to XX																											   
crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI_128_WPS_User
priorityDomain 30
priorityLevelsList 45
end

lt PriorityDomainMapping
set QosPriorityMapping=1,PriorityDomainMapping=5QI6_7_8_9 priorityLevelsList 55 60 70 80 90

##Map the priority level of the slice to the above created priority level 
set GNBDUFunction=1,DU5qiTable=SD_700.*,DU5qi=6 priorityLevel 55
set GNBDUFunction=1,DU5qiTable=SD_700.*,DU5qi=128 priorityLevel 45
lpr GNBDUFunction=1,DU5qiTable=[1|2],DU5qi=128
if $nr_of_mos != 0 
    lset GNBDUFunction=1,DU5qiTable=[1|2],DU5qi=128 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=WPS_User_5QI128
fi

lset GNBDUFunction=1,DU5qiTable=[1|2],DU5qi=128 prioritylevel 45

#######################################
#### Set SD_7001 to NRCELLDU and CUUP
#######################################
set1 NRCellDU sNSSAIList sd=16777215,sst=1; sd=1000,sst=1; sd=1001,sst=1; sd=2000,sst=1; sd=3000,sst=1; sd=3001,sst=1; sd=3002,sst=1; sd=4000,sst=1; sd=5000,sst=1; sd=5001,sst=1;sd=5002,sst=1; sd=6000,sst=1; sd=6001,sst=1; sd=7000,sst=1; sd=7001,sst=1; sd=8000,sst=1; sd=8001,sst=1; sd=9000,sst=1; sd=9001,sst=1; sd=9002,sst=1; sd=10000,sst=1
set1 GNBCUUPFunction=1 sNSSAIList sd=16777215,sst=1; sd=1000,sst=1; sd=1001,sst=1; sd=2000,sst=1; sd=3000,sst=1; sd=3001,sst=1; sd=3002,sst=1; sd=4000,sst=1; sd=5000,sst=1; sd=5001,sst=1;sd=5002,sst=1; sd=6000,sst=1; sd=6001,sst=1; sd=7000,sst=1; sd=7001,sst=1; sd=8000,sst=1; sd=8001,sst=1; sd=9000,sst=1; sd=9001,sst=1; sd=9002,sst=1; sd=10000,sst=1

lt all
##################################
### UeGrouping for WPS 5QI128  ###
##################################
pr GNBCUCPFunction=1,UeGroupSelection=1
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,UeGroupSelection=1
    validityTimeEmergencyCause 6
    validityTimeHighPrioAccCause 6
    validityTimeMcsPrioAccCause 6
    validityTimeMoDataCause 6
    validityTimeMoSignallingCause 6
    validityTimeMoSmsCause 6
    validityTimeMoVideoCallCause 6
    validityTimeMoVoiceCallCause 6
    validityTimeMpsPrioAccCause 6
    validityTimeMtAccessCause 6
    end
fi

pr UeGroupSelection=1,UeAdmissionGroupDefinition=WPS_Users
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=WPS_Users
    chipsetRef
    imeiSvRef
    selectionCriteria 5qi==128 || qci==128 || rrcEstResCause==mps-PriorityAccess || arp<6
    ueAdmissionGroupId 1
    ueAdmissionGroupPriority 100
    userLabel WPS_Users
    end
fi

####################################################################################
####  Admission Control WPS  
####################################################################################
set CXC4012593 FeatureState 1
set CXC4012705 FeatureState 1
set GNBDUFunction=1,AdmissionControl=1 rrcMpsPriorityAccessPrio 1

lt AdmissionLimit
############################################################################
##########  MAXCONNECTEDUE VALUE for production
############################################################################

func MaxUE_FDD
    mr WPSbb
    ma WPSbb fieldreplaceableunit productdata Baseband*
    if $nr_of_mos = 0
        ma WPSbb fieldreplaceableunit productdata RAN Processor*
    fi
    for $mo in WPSbb
        get $mo productdata > $BasebandX
        $chkBaseband = $BasebandX[productName] -s RAN Processor 
        if $BasebandX[productName] ~ Baseband 5216* 
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=default maxConnectedUe 500
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=Default preemptionRate 100
        else if $BasebandX[productName] ~ Baseband 6630* 
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=default maxConnectedUe 500
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=Default preemptionRate 100
        else if $BasebandX[productName] ~ Baseband 6648* 
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=default maxConnectedUe 500
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=Default preemptionRate 100
        else if $BasebandX[productName] ~ RAN 
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=default maxConnectedUe 500
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=Default preemptionRate 100
        fi
    done
endfunc

func MaxUE_TDD
    mr WPSbb
        ma WPSbb fieldreplaceableunit productdata Baseband*
    if $nr_of_mos = 0
        ma WPSbb fieldreplaceableunit productdata RAN Processor*
    fi
    for $mo in WPSbb
        get $mo productdata > $BasebandX
        $chkBaseband = $BasebandX[productName] -s RAN Processor 
        if $BasebandX[productName] ~ Baseband 5216* 
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=default maxConnectedUe 1000
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=Default preemptionRate 100
        else if $BasebandX[productName] ~ Baseband 6630* 
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=default maxConnectedUe 1000
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=Default preemptionRate 100
        else if $BasebandX[productName] ~ Baseband 6648* 
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=default maxConnectedUe 1000
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=Default preemptionRate 100
        else if $BasebandX[productName] ~ RAN 
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=default maxConnectedUe 1000
            set GNBCUCPFunction=1,AdmissionControl=1,AdmissionLimit=Default preemptionRate 100
        fi
    done
endfunc

lst NRCellDU=A.* 
if $nr_of_mos != 0
    MaxUE_TDD
fi

lst NRCellDU=[K|J|I]
if $nr_of_mos != 0
    MaxUE_FDD
fi

crn GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS 
ueConfGroupType 2
end

lt AdmissionPriority
set NRCellCU= admissionPriorityRef GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS
crn GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=WPS
prefUeGroupList
ueConfGroupList 1
ueGroupList 
uePriority 100
end

##################################
### UeGrouping for Emergency Calls###
##################################
pr UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users
if $nr_of_mos = 0
crn GNBCUCPFunction=1,UeGroupSelection=1,UeAdmissionGroupDefinition=E911_Users
chipsetRef
imeiSvRef
selectionCriteria rrcEstResCause==emergency || arp==6
ueAdmissionGroupId 2
ueAdmissionGroupPriority 101
userLabel E911_Users
end
fi
 
crn GNBCUCPFunction=1,AdmissionControl=1,AdmissionPriority=TMO_WPS,AdmissionPriorityUeCfg=E911_Users
prefUeGroupList
ueConfGroupList 2
ueGroupList 
uePriority 101
end

crn GNBCUCPFunction=1,AdmissionControl=1,Uac=1,UacProfile=TMO_WPS
barringEnabled true
end

lt UacProfile
set nrcellcu= uacProfileRef GNBCUCPFunction=1,AdmissionControl=1,Uac=1,UacProfile=TMO_WPS 

#############################################################
########  BARRINGGROUP SETTINGS for Production
#############################################################
crn GNBCUCPFunction=1,AdmissionControl=1,Uac=1,UacProfile=TMO_WPS,BarringGroup=WPS
accessCategoryList 1 3 4 5 6 7 8 9 10
barringTime 16
cellUsageBarringMax 95
cellUsageBarringStart 93
maxBarringProbability 95
pLMNIdList
rejRatioBarringMax 95
rejRatioBarringStart 93
startBarringAi1 100
startBarringAi11 100
startBarringAi12 100
startBarringAi13 100
startBarringAi14 100
startBarringAi15 100
startBarringAi2 100
end

##############################################
## Setting Parameter Compliance if Preexisting
##############################################
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  aqmMode 1
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  counterActiveMode false
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  dcDlPdcpAggrPrioCg 2
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  dcDlPdcpAggrTimeDiffCg 2
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  dcDlPdcpAggrTimeDiffProhibit 200
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  dcDlPdcpAggrTimeDiffThresh 150
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  estimatedE2ERTT 50
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  packetDelayBudget 280
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  packetDelayBudgetOffset 0
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  tOooUlDelivery 150
lset CUUP5qiTable=SD_700.*,CUUP5qi=(6|128)  dscp 12 

lset DU5qiTable=SD_700.*,DU5qi=(6|128) aqmMode 1
lset DU5qiTable=SD_700.*,DU5qi=(6|128) drbRlcInDu5qiEnabled false
lset DU5qiTable=SD_700.*,DU5qi=(6|128) dscp 12
lset DU5qiTable=SD_700.*,DU5qi=(6|128) estimatedE2ERTT 50
lset DU5qiTable=SD_700.*,DU5qi=(6|128) logicalChannelGroupId 5	
lset DU5qiTable=SD_700.*,DU5qi=(6|128) packetDelayBudgetOffset 0
lset DU5qiTable=SD_700.*,DU5qi=(6|128) pref5qiSrPeriodicityPool 1
lset DU5qiTable=SD_700.*,DU5qi=(6|128) drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
lset DU5qiTable=SD_700.*,DU5qi=(6|128) puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
lset DU5qiTable=SD_700.*,DU5qi=(6|128) srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default

lset CUCP5qiTable=SD_700.*,CUCP5qi=(6|128) pdcpSnSize 18
lset CUCP5qiTable=SD_700.*,CUCP5qi=(6|128) rlcMode 0
lset CUCP5qiTable=SD_700.*,CUCP5qi=(6|128) tPdcpDiscard 750
lset CUCP5qiTable=SD_700.*,CUCP5qi=(6|128) tReorderingDl 200
lset CUCP5qiTable=SD_700.*,CUCP5qi=(6|128) tReorderingUl 200

lset CUUP5qiTable=[1|2],CUUP5qi=128  aqmMode 1
lset CUUP5qiTable=[1|2],CUUP5qi=128  counterActiveMode false
lset CUUP5qiTable=[1|2],CUUP5qi=128  dcDlPdcpAggrPrioCg 2
lset CUUP5qiTable=[1|2],CUUP5qi=128  dcDlPdcpAggrTimeDiffCg 2
lset CUUP5qiTable=[1|2],CUUP5qi=128  dcDlPdcpAggrTimeDiffProhibit 200
lset CUUP5qiTable=[1|2],CUUP5qi=128  dcDlPdcpAggrTimeDiffThresh 150 
lset CUUP5qiTable=[1|2],CUUP5qi=128  estimatedE2ERTT 50
lset CUUP5qiTable=[1|2],CUUP5qi=128  packetDelayBudget 280
lset CUUP5qiTable=[1|2],CUUP5qi=128  packetDelayBudgetOffset 0
lset CUUP5qiTable=[1|2],CUUP5qi=128  tOooUlDelivery 150
lset CUUP5qiTable=[1|2],CUUP5qi=128  dscp 12 

lset DU5qiTable=[1|2],DU5qi=128  aqmMode 1
lset DU5qiTable=[1|2],DU5qi=128  drbRlcInDu5qiEnabled false
lset DU5qiTable=[1|2],DU5qi=128  dscp 12
lset DU5qiTable=[1|2],DU5qi=128  estimatedE2ERTT 50
lset DU5qiTable=[1|2],DU5qi=128  logicalChannelGroupId 5
lset DU5qiTable=[1|2],DU5qi=128  packetDelayBudget 280	
lset DU5qiTable=[1|2],DU5qi=128  packetDelayBudgetOffset 0
lset DU5qiTable=[1|2],DU5qi=128  pref5qiSrPeriodicityPool 1
lset DU5qiTable=[1|2],DU5qi=128  drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
lset DU5qiTable=[1|2],DU5qi=128  puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
lset DU5qiTable=[1|2],DU5qi=128  srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default

lset CUCP5qiTable=[1|2],CUCP5qi=128 pdcpSnSize 18
lset CUCP5qiTable=[1|2],CUCP5qi=128 rlcMode 0
lset CUCP5qiTable=[1|2],CUCP5qi=128 tPdcpDiscard 750
lset CUCP5qiTable=[1|2],CUCP5qi=128 tReorderingDl 200
lset CUCP5qiTable=[1|2],CUCP5qi=128 tReorderingUl 200														  

confbl-
gs-
lt all 
hget NRCellDU sNSSAIList
hget GNBCUUPFunction=1 sNSSAIList
hget 5qi=6$
hget 5qi=128$
hget . schedulingprofileref
hget . related5qiTableRef
hget SchedulingProfile= relativePriority|relativePriorityMode|schedulingAlgorithm
hget ,AdmissionPriorityUeCfg
hget ,BarringGroup
hget ,UeAdmissionGroupDefinition

"""]

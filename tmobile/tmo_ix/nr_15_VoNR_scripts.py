import os
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_15_VoNR_scripts(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return

    def cr_file_path(self): pass
    def write_script_file(self): pass

    def writemos_script_file(self):
        """ :rtype: None """
        if len(self.s_dict) == 0: return
        mos_file = os.path.join(self.usid.base_dir, *self.relative_path)
        if not os.path.exists(os.path.dirname(mos_file)):
            os.makedirs(os.path.dirname(mos_file))
        with open(mos_file, 'w') as f:
            f.write(F"""lt all
unset all
pv $nodename
if $nodename != {self.node}
    print ERROR: Node Name Mismatch. Wrong Node. ABORT !!!
    return
fi
$date = `date +%Y%m%d_%H%M%S`
l+ LogFile_{self.relative_path[-1].split('.')[0]}_$date.log
confbl+
gs+

""")
            f.write('\n'.join(self.s_dict))
            f.write("""

confbl-
gs
l-
unset all            
""")
        self.s_dict = []

    def special_formate_scripts(self):
        if len(self.gnbdata) == 0: return
        if str(self.usid.client.mname) not in ['Syosset', 'Norfolk', 'Philadelphia', 'Bloomfield', 'Salina']: return
        band = 'N41' if len(self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.contains('^A'))].index) > 0 else 'N71_N25'
        # Notes
        self.relative_path[-2] = 'VoNR_Scripts'
        self.relative_path[-1] = 'VoNR_Process_Documents_details.txt'
        mos_file = os.path.join(self.usid.base_dir, *self.relative_path)
        if not os.path.exists(os.path.dirname(mos_file)): os.makedirs(os.path.dirname(mos_file))
        with open(mos_file, 'w') as f:
            f.write(F"""
return
#######################################################################################################
Team- please see below update & clarification from Bob. Share with anyone I missed who supports integrations. 911 VoNR Call Test process also attached. Thanks!
-	If any questions reach out to RF, Bob or me. 
All,
Need to make sure going forward that all NSD and Anchor/Overlay projects in these 3 NRTACs are integrated/setup and call tested for VONR as well. I have attached the DACM, NSI and SI pre-req scripts, and the activation script (NSI) as well. It is imperative that a PCI retune be completed for MOD 6 compliance is completed before the new VONR layers are released to the network.
-	NRTAC 5766144|5765888|5766656 VONR Activation
If there is any doubt if a site you are working on is in these areas can refer to the CIQ for the NRTAC assignment. Can also then  determine if any N41 is below the >= 80MBW SA activation threshold, in which case means no VONR on that node.
Steps to run in this order.
1)	VONR only gets activated on NR nodes in SA mode. NSA only nodes (low BW N41 nodes typically) shall not have VoNR activated.
2)	Unlock NR cells for a minute or 2 well before the call test phase to generate the SSB. This is needed for SON to be able to identify a new cell to be added to SON Topology.
3)	Band specific scripts for, script_DACM_XXXX
4)	Band Specific scripts for, VoNR_Preq_up_to_23Q1_XXXX
5)	VONR_Prereq_SI.txt
6)	MOD 6 PCI Retune- If no access to SON, request this to be done by the market RF team. All new LTE and NR cells must be retuned prior to release anyway.
7)	VoNR_activation_script_NSI_0908.txt

***If VONR was accidentally activated on an NSA only node, you can run the NSI VONR Deactivation Script***
**** New Update SA need to be implemented on all UPNY Nodes ****
**** FW: NRTAC 5766144|5765888|5766656 VONR Activation- Site Integrations. Update & Clarification + 911 Call Test Process ****
#######################################################################################################
            """)

            # VoNR_Deactivation_script_NSI_0908
            self.relative_path[-1] = F'nr_VoNR_Deactivation.mos'
            mos_file = os.path.join(self.usid.base_dir, *self.relative_path)
            if not os.path.exists(os.path.dirname(mos_file)): os.makedirs(os.path.dirname(mos_file))
            with open(mos_file, 'w') as f:
                f.write(F"""
lt all
unset all
$date = `date +%Y%m%d_%H%M%S`
l+ LogFile_nr_01_VoNR_Deactivation_N71_N25_$date.log
confbl+
gs+
cvms Pre_VoNR_Deactivation_$date
set Mcfb=1,McfbCellProfile=[KJA].*,McfbCellProfileUeCfg=Base epsFallbackOperation 5
set Mcfb=1,McfbCellProfile=[KJA].*,McfbCellProfileUeCfg=Base epsFallbackOperationEm 1
cvms Post_VoNR_Deactivation_$date
confbl-
gs
l-
unset all

                """)


        # script_DACM_N41_vonraware_updated_rev3    script_DACM_N41_vonraware_updated_rev3
        self.relative_path.insert(-1, self.node)
        self.relative_path[-1] = F'nr_01_script_DACM_{band}_vonraware_updated_rev3_{self.node}.mos'
        self.s_dict = [F"""
cvms Pre_DACM_VoNR_config_$date

pr GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2$
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2
    ueGroupId 2
    ueGroupPriority 15
    selectionCriteria {"5qi>=5" if band == "N41" else "5qi==5"}
    end
fi
set GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=2 selectionCriteria {"5qi>=5" if band == "N41" else "5qi==5"}

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
    crn UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA
    sCellActDeactDataThres 100
    sCellActDeactDataThresHyst 20
    sCellDeactDelayTimer 80
    sCellActProhibitTimer 10
    sCellDeactProhibitTimer 250
    ueGroupList 1 2
    prefUeGroupList 
    end
else
    set UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA sCellActDeactDataThresHyst 20
    set UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA sCellDeactDelayTimer 80
    set UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA sCellDeactProhibitTimer 250
    set UeCA=1,CaSCellHandling=1,CaSCellHandlingUeCfg=SA ueGroupList 1 2
fi
set NRCellDU= caSCellHandlingRef UeCA=1,CaSCellHandling=1

cvms Post_DACM_VoNR_config_$date
"""]
        self.writemos_script_file()

        # VoNR_Preq_up_to_23Q1_FDD_only_622_v4,     VoNR_Preq_up_to_23Q1_TDD_only_622_v4
        self.relative_path[-1] = F'nr_02_VoNR_Preq_up_to_23Q1_{band}_{"TDD" if band == "N41" else "FDD" }_only_622_v4_{self.node}.mos'
        self.s_dict = [F"""
cvms Pre_VoNR_prequsite_$date

##DU 5QI ####

func DU5qi
wfat $tempdir/DU5qi.mos
ldel GNBDUFunction=1,DU5qiTable=1,DU5qi=auto
crn GNBDUFunction=1,DU5qiTable=1
default5qiTable true
end

crn GNBDUFunction=1,DU5qiTable=1,DU5qi=9
aqmMode 1
drbRlcInDu5qiEnabled true
drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
dscp 10
estimatedE2ERTT 50
logicalChannelGroupId 4
packetDelayBudget 280
packetDelayBudgetOffset 0
priorityLevel 90
profile5qi 9
puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI9
srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
userLabel 
end

crn GNBDUFunction=1,DU5qiTable=1,DU5qi=8
aqmMode 1
drbRlcInDu5qiEnabled true
drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
dscp 14
estimatedE2ERTT 50
logicalChannelGroupId 4
packetDelayBudget 280
packetDelayBudgetOffset 0
priorityLevel 80
profile5qi 8
puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI8
srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
userLabel 
end

crn GNBDUFunction=1,DU5qiTable=1,DU5qi=7
aqmMode 1
drbRlcInDu5qiEnabled true
drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
dscp 14
estimatedE2ERTT 50
logicalChannelGroupId 4
packetDelayBudget 280
packetDelayBudgetOffset 0
priorityLevel 70
profile5qi 7
puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI7
srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
userLabel 
end

crn GNBDUFunction=1,DU5qiTable=1,DU5qi=6
aqmMode 1
drbRlcInDu5qiEnabled true
drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
dscp 12
estimatedE2ERTT 50
logicalChannelGroupId 4
packetDelayBudget 280
packetDelayBudgetOffset 0
priorityLevel 60
profile5qi 6
puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI6
srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
userLabel 
end

crn GNBDUFunction=1,DU5qiTable=1,DU5qi=5
aqmMode 0
drbRlcInDu5qiEnabled true
drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
dscp 26
estimatedE2ERTT 50
logicalChannelGroupId 1
packetDelayBudget 80
packetDelayBudgetOffset 0
priorityLevel 10
profile5qi 5
puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
schedulingProfileRef 
srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
userLabel 
end

crn GNBDUFunction=1,DU5qiTable=1,DU5qi=4
aqmMode 2
drbRlcInDu5qiEnabled true
drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
dscp 38
estimatedE2ERTT 50
logicalChannelGroupId 5
packetDelayBudget 280
packetDelayBudgetOffset 0
priorityLevel 50
profile5qi 4
puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
schedulingProfileRef 
srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
userLabel 
end

crn GNBDUFunction=1,DU5qiTable=1,DU5qi=3
aqmMode 2
drbRlcInDu5qiEnabled true
drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
dscp 36
estimatedE2ERTT 50
logicalChannelGroupId 5
packetDelayBudget 30
packetDelayBudgetOffset 0
priorityLevel 30
profile5qi 3
puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
schedulingProfileRef 
srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
-

crn GNBDUFunction=1,DU5qiTable=1,DU5qi=1
aqmMode 2
drbRlcInDu5qiEnabled true
drbRlcRef GNBDUFunction=1,UeCC=1,RadioLinkControl=1,DrbRlc=Default
dscp 40
estimatedE2ERTT 50
logicalChannelGroupId 2
packetDelayBudget 80
packetDelayBudgetOffset 50
priorityLevel 20
profile5qi 1
puschRepRef GNBDUFunction=1,UeCC=1,PuschRep=Default
schedulingProfileRef 
srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=Default
userLabel 
end
eof
run1 $tempdir/DU5qi.mos
endfunc

pr GNBDUFunction=1,DU5qiTable=1,
if $nr_of_mos  < 9
ldel GNBDUFunction=1,DU5qiTable=1
DU5qi
fi

lset GNBDUFunction=1,DU5qiTable=1$ default5qiTable true
cr GNBDUFunction=1,DU5qiTable=1,DU5qi=5 LogicalChannelGroup=1


##CUUP 5QI ####
func CUUP5qi
wfat $tempdir/CUUP5qi.mos
crn GNBCUUPFunction=1,CUUP5qiTable=1
default5qiTable true
end

crn GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=1
aqmMode 2
counterActiveMode false
dscp 40
estimatedE2ERTT 0
packetDelayBudget 80
packetDelayBudgetOffset 50
profile5qi 1
tOooUlDelivery 150
userLabel 
end

crn GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=2
aqmMode 2
counterActiveMode false
dscp 32
estimatedE2ERTT 0
packetDelayBudget 130
packetDelayBudgetOffset 0
profile5qi 2
tOooUlDelivery 150
userLabel 
end

crn GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=3
aqmMode 2
counterActiveMode false
dscp 36
estimatedE2ERTT 0
packetDelayBudget 30
packetDelayBudgetOffset 0
profile5qi 3
tOooUlDelivery 150
userLabel 
end

crn GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=4
aqmMode 2
counterActiveMode false
dscp 38
estimatedE2ERTT 0
packetDelayBudget 280
packetDelayBudgetOffset 0
profile5qi 4
tOooUlDelivery 150
userLabel 
end

crn GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=5
aqmMode 0
counterActiveMode false
dscp 26
estimatedE2ERTT 0
packetDelayBudget 80
packetDelayBudgetOffset 0
profile5qi 5
tOooUlDelivery 150
userLabel 
end

crn GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=6
aqmMode 1
counterActiveMode false
dscp 12
estimatedE2ERTT 50
packetDelayBudget 280
packetDelayBudgetOffset 0
profile5qi 6
tOooUlDelivery 150
userLabel 
end

crn GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=7
aqmMode 1
counterActiveMode false
dscp 14
estimatedE2ERTT 50
packetDelayBudget 80
packetDelayBudgetOffset 0
profile5qi 7
tOooUlDelivery 150
userLabel 
end

crn GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=8
aqmMode 1
counterActiveMode false
dscp 14
estimatedE2ERTT 50
packetDelayBudget 280
packetDelayBudgetOffset 0
profile5qi 8
tOooUlDelivery 150
userLabel 
end

crn GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi=9
aqmMode 1
counterActiveMode false
dscp 10
estimatedE2ERTT 50
packetDelayBudget 280
packetDelayBudgetOffset 0
profile5qi 9
tOooUlDelivery 150
userLabel 
end
eof
run1 $tempdir/CUUP5qi.mos
endfunc

pr GNBCUUPFunction=1,CUUP5qiTable=1,CUUP5qi
if $nr_of_mos  < 9
    CUUP5qi
fi

lset GNBCUUPFunction=1,CUUP5qiTable=1$ default5qiTable true


##CUCP 5QI ####
func CUCP5qi
wfat $tempdir/CUCP5qi.mos
crn GNBCUCPFunction=1,CUCP5qiTable=1
default5qiTable true
end

crn GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=1
pdcpSnSize 18
profile5qi 1
rlcMode 1
tPdcpDiscard 150
tReorderingDl 200
tReorderingUl 200
userLabel 
end

crn GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=2
pdcpSnSize 18
profile5qi 2
rlcMode 1
tPdcpDiscard 750
tReorderingDl 200
tReorderingUl 200
userLabel 
end

crn GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=3
pdcpSnSize 18
profile5qi 3
rlcMode 1
tPdcpDiscard 750
tReorderingDl 200
tReorderingUl 200
userLabel 
end

crn GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=4
pdcpSnSize 18
profile5qi 4
rlcMode 1
tPdcpDiscard 750
tReorderingDl 200
tReorderingUl 200
userLabel 
end

crn GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=5
pdcpSnSize 18
profile5qi 5
rlcMode 0
tPdcpDiscard 750
tReorderingDl 200
tReorderingUl 200
userLabel 
end

crn GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=6
pdcpSnSize 18
profile5qi 6
rlcMode 0
tPdcpDiscard 750
tReorderingDl 200
tReorderingUl 200
userLabel 
end

crn GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=7
pdcpSnSize 18
profile5qi 7
rlcMode 0
tPdcpDiscard 750
tReorderingDl 200
tReorderingUl 200
userLabel 
end

crn GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=8
pdcpSnSize 18
profile5qi 8
rlcMode 0
tPdcpDiscard 750
tReorderingDl 200
tReorderingUl 200
userLabel 
end

crn GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=9
pdcpSnSize 18
profile5qi 9
rlcMode 0
tPdcpDiscard 750
tReorderingDl 200
tReorderingUl 200
userLabel 
end

eof
run1 $tempdir/CUCP5qi.mos
endfunc

pr GNBCUCPFunction=1,CUCP5qiTable=1,
if $nr_of_mos  < 9
 ldel GNBCUCPFunction=1,CUCP5qiTable=1
 CUCP5qi
fi

lset GNBCUCPFunction=1,CUCP5qiTable=1$ default5qiTable true

### 21.Q2 ####

##### PCS Feature Activation
pr GNBDUFunction=1,QosPriorityMapping=1
if $nr_of_mos = 0
 crn GNBDUFunction=1,QosPriorityMapping=1
 end
fi

# 5QI-1
pr GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI1
if $nr_of_mos = 0
 crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI1
 priorityDomain 8
 priorityLevelsList 20
 end
else
 set GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI1 priorityDomain 8
 set GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI1 priorityLevelsList 20
fi

# 5QI-2
pr GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI2
if $nr_of_mos = 0
 crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI2
 priorityDomain 12
 priorityLevelsList 40
 end
else
 set GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI2 priorityDomain 12
 set GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI2 priorityLevelsList 40
fi

# 5QI-5
pr GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI5
if $nr_of_mos = 0
 crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI5
 priorityDomain 4
 priorityLevelsList 10
 end
else
 set GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI5 priorityDomain 4
 set GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI5 priorityLevelsList 10
fi

# 5QI-6-7-8-9
pr GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI6_7_8_9
if $nr_of_mos = 0
 crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI6_7_8_9
 priorityDomain 32
 priorityLevelsList 60,70,80,90
 end
else
 set GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI6_7_8_9 priorityDomain 32
 set GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI6_7_8_9 priorityLevelsList 60,70,80,90
fi

##### RPS Feature Activation
pr GNBDUFunction=1,UeCC=1
if $nr_of_mos = 0
 cr GNBDUFunction=1,UeCC=1
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI6
if $nr_of_mos = 0
 crn GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI6
 relativePriority 64
 userLabel NRSA_5QI6
 end
else
 set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI6 relativePriority 64
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI7
if $nr_of_mos = 0
 crn GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI7
 relativePriority 16
 userLabel NRSA_5QI7
 end
else
 set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI7 relativePriority 16
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI8
if $nr_of_mos = 0
 crn GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI8
 relativePriority 8
 userLabel NRSA_5QI8 
 end
else
 set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI8 relativePriority 8
fi

pr GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI9
if $nr_of_mos = 0
 crn GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI9
 relativePriority 4
 userLabel NRSA_5QI9
 end
else
 set GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI9 relativePriority 4
fi

set DU5qiTable=1,DU5qi=6 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI6
set DU5qiTable=1,DU5qi=7 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI7
set DU5qiTable=1,DU5qi=8 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI8
set DU5qiTable=1,DU5qi=9 schedulingProfileRef GNBDUFunction=1,UeCC=1,SchedulingProfile=5QI9

##Differentiated UE handlinig
pr GNBCUCPFunction=1,UeGroupSelection=1
if $nr_of_mos = 0
 crn GNBCUCPFunction=1,UeGroupSelection=1
 end
fi

pr GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=1
if $nr_of_mos = 0
 crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=1
 selectionCriteria 5qi==1
 selectionProbability 100
 ueGroupId 1
 ueGroupPriority 100
 userLabel
 end
fi

pr GNBCUCPFunction=1,UeCC=1,InactivityProfile=Default,InactivityProfileUeCfg=1
if $nr_of_mos = 0
 crn GNBCUCPFunction=1,UeCC=1,InactivityProfile=Default,InactivityProfileUeCfg=1
 prefUeGroupList
 tInactivityTimer 45
 tInactivityTimerEndcSn 10
 tInactivityTimerNrdcSn 10
 ueGroupList 1
 userLabel
 end
fi


#### 5QI Table update for 21.Q3
#CUCP5qiTable
set  CUCP5qiTable=1,CUCP5qi=1$  pdcpSnSize  12
set  CUCP5qiTable=1,CUCP5qi=2$  pdcpSnSize  12
set  CUCP5qiTable=1,CUCP5qi=3$  pdcpSnSize  12
set  CUCP5qiTable=1,CUCP5qi=4$  pdcpSnSize  12
set  CUCP5qiTable=1,CUCP5qi=5$  pdcpSnSize  12
set  CUCP5qiTable=1,CUCP5qi=6$  pdcpSnSize  18
set  CUCP5qiTable=1,CUCP5qi=7$  pdcpSnSize  18
set  CUCP5qiTable=1,CUCP5qi=8$  pdcpSnSize  18
set  CUCP5qiTable=1,CUCP5qi=9$  pdcpSnSize  18

set  CUCP5qiTable=1,CUCP5qi=1$  rlcMode  1
set  CUCP5qiTable=1,CUCP5qi=2$  rlcMode  1
set  CUCP5qiTable=1,CUCP5qi=3$  rlcMode  1
set  CUCP5qiTable=1,CUCP5qi=4$  rlcMode  1
set  CUCP5qiTable=1,CUCP5qi=5$  rlcMode  0
set  CUCP5qiTable=1,CUCP5qi=6$  rlcMode  0
set  CUCP5qiTable=1,CUCP5qi=7$  rlcMode  0
set  CUCP5qiTable=1,CUCP5qi=8$  rlcMode  0
set  CUCP5qiTable=1,CUCP5qi=9$  rlcMode  0

set  CUCP5qiTable=1,CUCP5qi=1$  tPdcpDiscard  150
set  CUCP5qiTable=1,CUCP5qi=2$  tPdcpDiscard  750
set  CUCP5qiTable=1,CUCP5qi=3$  tPdcpDiscard  750
set  CUCP5qiTable=1,CUCP5qi=4$  tPdcpDiscard  750
set  CUCP5qiTable=1,CUCP5qi=5$  tPdcpDiscard  750
set  CUCP5qiTable=1,CUCP5qi=6$  tPdcpDiscard  750
set  CUCP5qiTable=1,CUCP5qi=7$  tPdcpDiscard  750
set  CUCP5qiTable=1,CUCP5qi=8$  tPdcpDiscard  750
set  CUCP5qiTable=1,CUCP5qi=9$  tPdcpDiscard  750

set  CUCP5qiTable=1,CUCP5qi=1$  tReorderingDl  200
set  CUCP5qiTable=1,CUCP5qi=2$  tReorderingDl  200
set  CUCP5qiTable=1,CUCP5qi=3$  tReorderingDl  200
set  CUCP5qiTable=1,CUCP5qi=4$  tReorderingDl  200
set  CUCP5qiTable=1,CUCP5qi=5$  tReorderingDl  200
set  CUCP5qiTable=1,CUCP5qi=6$  tReorderingDl  200
set  CUCP5qiTable=1,CUCP5qi=7$  tReorderingDl  200
set  CUCP5qiTable=1,CUCP5qi=8$  tReorderingDl  200
set  CUCP5qiTable=1,CUCP5qi=9$  tReorderingDl  200

set  CUCP5qiTable=1,CUCP5qi=1$  tReorderingUl  200
set  CUCP5qiTable=1,CUCP5qi=2$  tReorderingUl  200
set  CUCP5qiTable=1,CUCP5qi=3$  tReorderingUl  200
set  CUCP5qiTable=1,CUCP5qi=4$  tReorderingUl  200
set  CUCP5qiTable=1,CUCP5qi=5$  tReorderingUl  200
set  CUCP5qiTable=1,CUCP5qi=6$  tReorderingUl  200
set  CUCP5qiTable=1,CUCP5qi=7$  tReorderingUl  200
set  CUCP5qiTable=1,CUCP5qi=8$  tReorderingUl  200
set  CUCP5qiTable=1,CUCP5qi=9$  tReorderingUl  200

#CUUP5qi
set  CUUP5qiTable=1,CUUP5qi=9$  aqmMode  1
set  CUUP5qiTable=1,CUUP5qi=1$  aqmMode  2
set  CUUP5qiTable=1,CUUP5qi=2$  aqmMode  2
set  CUUP5qiTable=1,CUUP5qi=3$  aqmMode  2
set  CUUP5qiTable=1,CUUP5qi=4$  aqmMode  2
set  CUUP5qiTable=1,CUUP5qi=5$  aqmMode  0
set  CUUP5qiTable=1,CUUP5qi=6$  aqmMode  1
set  CUUP5qiTable=1,CUUP5qi=7$  aqmMode  1
set  CUUP5qiTable=1,CUUP5qi=8$  aqmMode  1

set  CUUP5qiTable=1,CUUP5qi=1$  dcDlPdcpAggrPrioCg  2
set  CUUP5qiTable=1,CUUP5qi=2$  dcDlPdcpAggrPrioCg  2
set  CUUP5qiTable=1,CUUP5qi=3$  dcDlPdcpAggrPrioCg  2
set  CUUP5qiTable=1,CUUP5qi=4$  dcDlPdcpAggrPrioCg  2
set  CUUP5qiTable=1,CUUP5qi=5$  dcDlPdcpAggrPrioCg  2
set  CUUP5qiTable=1,CUUP5qi=6$  dcDlPdcpAggrPrioCg  2
set  CUUP5qiTable=1,CUUP5qi=7$  dcDlPdcpAggrPrioCg  2
set  CUUP5qiTable=1,CUUP5qi=8$  dcDlPdcpAggrPrioCg  2
set  CUUP5qiTable=1,CUUP5qi=9$  dcDlPdcpAggrPrioCg  2

set  CUUP5qiTable=1,CUUP5qi=1$  dcDlPdcpAggrTimeDiffCg  2
set  CUUP5qiTable=1,CUUP5qi=2$  dcDlPdcpAggrTimeDiffCg  2
set  CUUP5qiTable=1,CUUP5qi=3$  dcDlPdcpAggrTimeDiffCg  2
set  CUUP5qiTable=1,CUUP5qi=4$  dcDlPdcpAggrTimeDiffCg  2
set  CUUP5qiTable=1,CUUP5qi=5$  dcDlPdcpAggrTimeDiffCg  2
set  CUUP5qiTable=1,CUUP5qi=6$  dcDlPdcpAggrTimeDiffCg  2
set  CUUP5qiTable=1,CUUP5qi=7$  dcDlPdcpAggrTimeDiffCg  2
set  CUUP5qiTable=1,CUUP5qi=8$  dcDlPdcpAggrTimeDiffCg  2
set  CUUP5qiTable=1,CUUP5qi=9$  dcDlPdcpAggrTimeDiffCg  2

set  CUUP5qiTable=1,CUUP5qi=1$  dcDlPdcpAggrTimeDiffProhibit  400
set  CUUP5qiTable=1,CUUP5qi=2$  dcDlPdcpAggrTimeDiffProhibit  400
set  CUUP5qiTable=1,CUUP5qi=3$  dcDlPdcpAggrTimeDiffProhibit  400
set  CUUP5qiTable=1,CUUP5qi=4$  dcDlPdcpAggrTimeDiffProhibit  400
set  CUUP5qiTable=1,CUUP5qi=5$  dcDlPdcpAggrTimeDiffProhibit  400
set  CUUP5qiTable=1,CUUP5qi=6$  dcDlPdcpAggrTimeDiffProhibit  400
set  CUUP5qiTable=1,CUUP5qi=7$  dcDlPdcpAggrTimeDiffProhibit  400
set  CUUP5qiTable=1,CUUP5qi=8$  dcDlPdcpAggrTimeDiffProhibit  400
set  CUUP5qiTable=1,CUUP5qi=9$  dcDlPdcpAggrTimeDiffProhibit  400

set  CUUP5qiTable=1,CUUP5qi=1$  dcDlPdcpAggrTimeDiffThresh  100
set  CUUP5qiTable=1,CUUP5qi=2$  dcDlPdcpAggrTimeDiffThresh  100
set  CUUP5qiTable=1,CUUP5qi=3$  dcDlPdcpAggrTimeDiffThresh  100
set  CUUP5qiTable=1,CUUP5qi=4$  dcDlPdcpAggrTimeDiffThresh  100
set  CUUP5qiTable=1,CUUP5qi=5$  dcDlPdcpAggrTimeDiffThresh  100
set  CUUP5qiTable=1,CUUP5qi=6$  dcDlPdcpAggrTimeDiffThresh  100
set  CUUP5qiTable=1,CUUP5qi=7$  dcDlPdcpAggrTimeDiffThresh  100
set  CUUP5qiTable=1,CUUP5qi=8$  dcDlPdcpAggrTimeDiffThresh  100
set  CUUP5qiTable=1,CUUP5qi=9$  dcDlPdcpAggrTimeDiffThresh  100

set  CUUP5qiTable=1,CUUP5qi=1$  dscp  40
set  CUUP5qiTable=1,CUUP5qi=2$  dscp  32
set  CUUP5qiTable=1,CUUP5qi=3$  dscp  36
set  CUUP5qiTable=1,CUUP5qi=4$  dscp  38
set  CUUP5qiTable=1,CUUP5qi=5$  dscp  26
set  CUUP5qiTable=1,CUUP5qi=6$  dscp  12
set  CUUP5qiTable=1,CUUP5qi=7$  dscp  14
set  CUUP5qiTable=1,CUUP5qi=8$  dscp  14
set  CUUP5qiTable=1,CUUP5qi=9$  dscp  10

Set CUUP5qi=1 estimatedE2ERTT 0
Set CUUP5qi=2 estimatedE2ERTT 0
Set CUUP5qi=3 estimatedE2ERTT 0
Set CUUP5qi=4 estimatedE2ERTT 0
Set CUUP5qi=5 estimatedE2ERTT 0
Set CUUP5qi=6 estimatedE2ERTT 100
Set CUUP5qi=7 estimatedE2ERTT 100
Set CUUP5qi=8 estimatedE2ERTT 100
Set CUUP5qi=9 estimatedE2ERTT 100
set CUUP5qi dcDlPdcpAggrPrioCg 2

set  CUUP5qiTable=1,CUUP5qi=1$  tOooUlDelivery  150
set  CUUP5qiTable=1,CUUP5qi=2$  tOooUlDelivery  150
set  CUUP5qiTable=1,CUUP5qi=3$  tOooUlDelivery  150
set  CUUP5qiTable=1,CUUP5qi=4$  tOooUlDelivery  150
set  CUUP5qiTable=1,CUUP5qi=5$  tOooUlDelivery  150
set  CUUP5qiTable=1,CUUP5qi=6$  tOooUlDelivery  150
set  CUUP5qiTable=1,CUUP5qi=7$  tOooUlDelivery  150
set  CUUP5qiTable=1,CUUP5qi=8$  tOooUlDelivery  150
set  CUUP5qiTable=1,CUUP5qi=9$  tOooUlDelivery  150

set CUUP5qiTable=1,CUUP5qi=1 packetDelayBudget 80
set CUUP5qiTable=1,CUUP5qi=2 packetDelayBudget 130
set CUUP5qiTable=1,CUUP5qi=3 packetDelayBudget 30
set CUUP5qiTable=1,CUUP5qi=4 packetDelayBudget 280
set CUUP5qiTable=1,CUUP5qi=5 packetDelayBudget 80
set CUUP5qiTable=1,CUUP5qi=6 packetDelayBudget 280
set CUUP5qiTable=1,CUUP5qi=7 packetDelayBudget 280
set CUUP5qiTable=1,CUUP5qi=8 packetDelayBudget 280
set CUUP5qiTable=1,CUUP5qi=9 packetDelayBudget 280

set CUUP5qiTable=1,CUUP5qi=1 packetDelayBudgetOffset 50
set CUUP5qiTable=1,CUUP5qi=2 packetDelayBudgetOffset 0
set CUUP5qiTable=1,CUUP5qi=3 packetDelayBudgetOffset 0
set CUUP5qiTable=1,CUUP5qi=4 packetDelayBudgetOffset 0
set CUUP5qiTable=1,CUUP5qi=5 packetDelayBudgetOffset 0
set CUUP5qiTable=1,CUUP5qi=6 packetDelayBudgetOffset 0
set CUUP5qiTable=1,CUUP5qi=7 packetDelayBudgetOffset 0
set CUUP5qiTable=1,CUUP5qi=8 packetDelayBudgetOffset 0
set CUUP5qiTable=1,CUUP5qi=9 packetDelayBudgetOffset 0

#DU5qiTable

set DU5qiTable=1,DU5qi=1 aqmMode 2
set DU5qiTable=1,DU5qi=2 aqmMode 2
set DU5qiTable=1,DU5qi=3 aqmMode 2
set DU5qiTable=1,DU5qi=4 aqmMode 2
set DU5qiTable=1,DU5qi=5 aqmMode 0
set DU5qiTable=1,DU5qi=6 aqmMode 1
set DU5qiTable=1,DU5qi=7 aqmMode 1
set DU5qiTable=1,DU5qi=8 aqmMode 1
set DU5qiTable=1,DU5qi=9 aqmMode 1

set DU5qiTable=1,DU5qi=1 logicalChannelGroupId 2
set DU5qiTable=1,DU5qi=2 logicalChannelGroupId 3
set DU5qiTable=1,DU5qi=3 logicalChannelGroupId 5
set DU5qiTable=1,DU5qi=4 logicalChannelGroupId 5
set DU5qiTable=1,DU5qi=5 logicalChannelGroupId 1
set DU5qiTable=1,DU5qi=6 logicalChannelGroupId 4
set DU5qiTable=1,DU5qi=7 logicalChannelGroupId 4
set DU5qiTable=1,DU5qi=8 logicalChannelGroupId 4
set DU5qiTable=1,DU5qi=9 logicalChannelGroupId 4

set  DU5qiTable=1,DU5qi=1$  dscp  40
set  DU5qiTable=1,DU5qi=2$  dscp  32
set  DU5qiTable=1,DU5qi=3$  dscp  36
set  DU5qiTable=1,DU5qi=4$  dscp  38
set  DU5qiTable=1,DU5qi=5$  dscp  26
set  DU5qiTable=1,DU5qi=6$  dscp  12
set  DU5qiTable=1,DU5qi=7$  dscp  14
set  DU5qiTable=1,DU5qi=8$  dscp  14
set  DU5qiTable=1,DU5qi=9$  dscp  10

set DU5qiTable=1,DU5qi=1 packetDelayBudgetOffset 50
set DU5qiTable=1,DU5qi=2 packetDelayBudgetOffset 0
set DU5qiTable=1,DU5qi=3 packetDelayBudgetOffset 0
set DU5qiTable=1,DU5qi=4 packetDelayBudgetOffset 0
set DU5qiTable=1,DU5qi=5 packetDelayBudgetOffset 0
set DU5qiTable=1,DU5qi=6 packetDelayBudgetOffset 0
set DU5qiTable=1,DU5qi=7 packetDelayBudgetOffset 0
set DU5qiTable=1,DU5qi=8 packetDelayBudgetOffset 0
set DU5qiTable=1,DU5qi=9 packetDelayBudgetOffset 0

set DU5qiTable=1,DU5qi=1 priorityLevel 20
set DU5qiTable=1,DU5qi=2 priorityLevel 40
set DU5qiTable=1,DU5qi=3 priorityLevel 30
set DU5qiTable=1,DU5qi=4 priorityLevel 50
set DU5qiTable=1,DU5qi=5 priorityLevel 10
set DU5qiTable=1,DU5qi=6 priorityLevel 60
set DU5qiTable=1,DU5qi=7 priorityLevel 70
set DU5qiTable=1,DU5qi=8 priorityLevel 80
set DU5qiTable=1,DU5qi=9 priorityLevel 90

set  DU5qiTable=1,DU5qi=1$  packetDelayBudget  80
set  DU5qiTable=1,DU5qi=2$  packetDelayBudget  130
set  DU5qiTable=1,DU5qi=3$  packetDelayBudget  30
set  DU5qiTable=1,DU5qi=4$  packetDelayBudget  280
set  DU5qiTable=1,DU5qi=5$  packetDelayBudget  80
set  DU5qiTable=1,DU5qi=6$  packetDelayBudget  280
set  DU5qiTable=1,DU5qi=7$  packetDelayBudget  280
set  DU5qiTable=1,DU5qi=8$  packetDelayBudget  280
set  DU5qiTable=1,DU5qi=9$  packetDelayBudget  280

set DU5qiTable=1,DU5qi=1 rlcSnLength 12
set DU5qiTable=1,DU5qi=2 rlcSnLength 12
set DU5qiTable=1,DU5qi=3 rlcSnLength 12
set DU5qiTable=1,DU5qi=4 rlcSnLength 12
set DU5qiTable=1,DU5qi=5 rlcSnLength 12
set DU5qiTable=1,DU5qi=6 rlcSnLength 18
set DU5qiTable=1,DU5qi=7 rlcSnLength 18
set DU5qiTable=1,DU5qi=8 rlcSnLength 18
set DU5qiTable=1,DU5qi=9 rlcSnLength 18

set DU5qiTable=1,DU5qi=1 tReassemblyUl 35
set DU5qiTable=1,DU5qi=2 tReassemblyUl 35
set DU5qiTable=1,DU5qi=3 tReassemblyUl 25
set DU5qiTable=1,DU5qi=4 tReassemblyUl 25
set DU5qiTable=1,DU5qi=5 tReassemblyUl 25
set DU5qiTable=1,DU5qi=6 tReassemblyUl 25
set DU5qiTable=1,DU5qi=7 tReassemblyUl 25
set DU5qiTable=1,DU5qi=8 tReassemblyUl 25
set DU5qiTable=1,DU5qi=9 tReassemblyUl 25

set DU5qiTable=1,DU5qi=1 tReassemblyDl 35
set DU5qiTable=1,DU5qi=2 tReassemblyDl 35
set DU5qiTable=1,DU5qi=3 tReassemblyDl 25
set DU5qiTable=1,DU5qi=4 tReassemblyDl 25
set DU5qiTable=1,DU5qi=5 tReassemblyDl 25
set DU5qiTable=1,DU5qi=6 tReassemblyDl 25
set DU5qiTable=1,DU5qi=7 tReassemblyDl 25
set DU5qiTable=1,DU5qi=8 tReassemblyDl 25
set DU5qiTable=1,DU5qi=9 tReassemblyDl 25

get McfbCellProfile epsFallbackOperation$ > $VONR

if $VONR !~ 2
/Enable VoNR LA
set QosPriorityMapping=1,PriorityDomainMapping=5QI1 priorityDomain 16
set QosPriorityMapping=1,PriorityDomainMapping=5QI2 priorityDomain 18

//Parameter for VoNR Quality per PDU feedback
set CUCP5qiTable=1,CUCP5qi=1 tReorderingUl 60
set CUCP5qiTable=1,CUCP5qi=2 tReorderingUl 20
set CUCP5qiTable=1,CUCP5qi=5 tReorderingUl 20
set DU5qiTable=1,DU5qi=1 tReassemblyUl 65
set CUCP5qiTable=1,CUCP5qi=2 tPdcpDiscard 200
set CUCP5qiTable=1,CUCP5qi=5 tPdcpDiscard 2147483646
fi
del GNBCUCPFunction=1,CUCP5qiTable=1,CUCP5qi=auto
del GNBDUFunction=1,DU5qiTable=1,DU5qi=auto5qi

### *************************************************************************************
### **Create QoS Priority domain mapping
#### ************************************************************************************************
crn GNBDUFunction=1,QosPriorityMapping=1
end

# 5QI-1
crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI1
priorityDomain 8
priorityLevelsList 20
end

# 5QI-2
crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI2
priorityDomain 12
priorityLevelsList 40
end

# 5QI-5
crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI5
priorityDomain 4
priorityLevelsList 10
end

# 5QI-6-7-8-9
crn GNBDUFunction=1,QosPriorityMapping=1,PriorityDomainMapping=5QI6_7_8_9
priorityDomain 32
priorityLevelsList 60,70,80,90
end

# logicalChannelGroupId
set DU5qiTable=1,DU5qi=1 logicalChannelGroupId 2
set DU5qiTable=1,DU5qi=2 logicalChannelGroupId 3
set DU5qiTable=1,DU5qi=3 logicalChannelGroupId 5
set DU5qiTable=1,DU5qi=4 logicalChannelGroupId 5
set DU5qiTable=1,DU5qi=5 logicalChannelGroupId 1
set DU5qiTable=1,DU5qi=6 logicalChannelGroupId 4
set DU5qiTable=1,DU5qi=7 logicalChannelGroupId 4
set DU5qiTable=1,DU5qi=8 logicalChannelGroupId 4
set DU5qiTable=1,DU5qi=9 logicalChannelGroupId 4

# priorityLevel
set DU5qiTable=1,DU5qi=1 priorityLevel 20
set DU5qiTable=1,DU5qi=2 priorityLevel 40
set DU5qiTable=1,DU5qi=3 priorityLevel 30
set DU5qiTable=1,DU5qi=4 priorityLevel 50
set DU5qiTable=1,DU5qi=5 priorityLevel 10
set DU5qiTable=1,DU5qi=6 priorityLevel 60
set DU5qiTable=1,DU5qi=7 priorityLevel 70
set DU5qiTable=1,DU5qi=8 priorityLevel 80
set DU5qiTable=1,DU5qi=9 priorityLevel 90

################################################################################################
### VoNR pre requist features activation
###############################################################################################
# Enable NR Service-Adaptive Link Adaptation Feature 
set CXC4012637 FeatureState 1

#Create UeBBProfile for UEs with voice data bearer
pr GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
if $nr_of_mos = 0
 crn GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
 dlMaxBitrate -1
 dlMcsTable 0
 linkAdaptationUeMode 3
 ulMcsTable 0
 userLabel 
 end
fi
            
pr GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR
if $nr_of_mos = 0
 crn GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR
 dlHarqMode 1
 ulHarqMode 1
 end
fi         

# Update the Base profile to have Harq Robust settings  
set GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=Base dlHarqMode 2	

# Update the Base profile to have linkAdaptationUeMode set to CUSTOM
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=Base linkAdaptationUeMode 3

pr GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR
if $nr_of_mos = 0
 crn GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR
 reTxBsrTimer 80
 srGrantSize 840
 end
fi

lt all

#Setting Harq for VoNR profile 
set GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR ulHarqMode 1
set GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR dlHarqMode 1
set GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR reTxBsrTimer 80
set GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR srGrantSize 840

#Setting DlLinkAdaptation for VoNR profile 
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,DlLinkAdaptation=1 dlBlerTarget 500
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,DlLinkAdaptation=1 dlMaxMcsIndex 16
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR dlMcsTable 0

#Setting PdcchLinkAdaptation for VoNR profile 
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,PdcchLinkAdaptation=1 pdcchLaSinrUeOffset -5        

#Setting UlLinkAdaptationfor VoNR profile 
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,UlLinkAdaptation=1 ulBlerTarget 500
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,UlLinkAdaptation=1 ulMaxMcsIndex 16
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,UlLinkAdaptation=1 ulMinTbs -1
set GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR ulMcsTable 0

lt all
set1x GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,UlLinkAdaptation=1 ulServicePacketInterval 20
set1x GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR,UlLinkAdaptation=1 ulServicePacketSize 70
commit

pr GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default
if $nr_of_mos = 0
 crn GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default
 ueConfGroupType 1
 userLabel 
 end
fi

pr GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR
if $nr_of_mos = 0
 crn GNBDUFunction=1,UeCC=1,UeBb=1,UeBbProfile=Default,UeBbProfileUeCfg=VoNR
 adaptTPollRetxDlRetxCount 0
 bsrUeCfgRef GNBDUFunction=1,UeCC=1,Bsr=1,BsrUeCfg=VoNR
 configuredGrantUeCfgRef 
 harqUeCfgRef GNBDUFunction=1,UeCC=1,Harq=1,HarqUeCfg=VoNR
 linkAdaptationUeCfgRef GNBDUFunction=1,UeCC=1,LinkAdaptation=1,LinkAdaptationUeCfg=VoNR
 prefUeGroupList  
 preschedulingUeCfgRef 
 ueConfGroupList 
 ueGroupList 1
 userLabel 
 end
fi
        """]
        if band == 'N41':
            self.s_dict += [F"""
###############################################################
#   CLPC actaivation SCs are replace by MO in 23Q3 BSW
###############################################################
scd RP1469,RP1470,RP1533,RP1600,RP1601,RP1602,RP1765,RP1766,RP86,RP87,RP88
wait 3s
scw RP1469:1,RP1470:10,RP1533:13,RP1600:8,RP1601:0,RP1602:1,RP86:50,RP87:10,RP88:1
wait 10s
set NRCellDU=A.*1$  pZeroNomPuschGrant -98
set NRCellDU=A.*1$ pZeroUePuschOffset256Qam 0
wait 15s
            """]
        else:
            self.s_dict += [F"""
###############################################################
#   CLPC actaivation . SC are replace with MOs in 23Q3 BSW
###############################################################
//scd RP1469,RP1470,RP1533,RP1600,RP1601,RP1602,RP1765,RP1766,RP86,RP87,RP88
//wait 3s
///scw RP1469:1,RP1470:10,RP1533:11,RP1600:6,RP1601:0,RP1602:1,RP1765:1,RP1766:150,RP86:50,RP87:10,RP88:1
//wait 30s
            """]
        self.s_dict += [F"""
################### RPS --- Activate Priority Controlled Scheduling-PCS --- Activate NR Relative Priority Scheduling -RPS ---
set SystemFunctions=1,Lm=1,FeatureState=CXC4012475 featureState 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012531 featurestate 1

################### if the AnrFunctionNR MO is missing, it will create but keep the default(deactivated) 
pr GNBCUCPFunction=1,AnrFunction=1
if $nr_of_mos = 0
    cr GNBCUCPFunction=1,AnrFunction=1
fi

pr GNBCUCPFunction=1,AnrFunction=1,AnrFunctionNR=1
if $nr_of_mos = 0
    cr GNBCUCPFunction=1,AnrFunction=1,AnrFunctionNR=1
fi

#### ANR Intra-freq --> being done by the Regional Performance team --- ENABLE SA-ANR Intra Freq --- ENABLE SA-ANR Inter Freq
set GNBCUCPFunction=1,AnrFunction=1,AnrFunctionNR=1 anrCgiMeasIntraFreqEnabled true
set GNBCUCPFunction=1,AnrFunction=1,AnrFunctionNR=1 anrCgiMeasInterFreqMode 1

###################10)	5QI Tables - Short PDCP and SN length
###Updating 5QI-1/5QI-2 table. Will not affect Data only user
set CUCP5qiTable=1,CUCP5qi=1 tReorderingUl 60
set CUCP5qiTable=1,CUCP5qi=2 tReorderingUl 20
set CUCP5qiTable=1,CUCP5qi=5 tReorderingUl 20
set DU5qiTable=1,DU5qi=1 tReassemblyUl 65
set DU5qiTable=1,DU5qi=1 tReassemblyDl 65
set CUCP5qiTable=1,CUCP5qi=2 tPdcpDiscard 200
set CUCP5qiTable=1,CUCP5qi=5 tPdcpDiscard 2147483646

###################11)	VoNR to Non-VoNR handling  SKIP But MOP is available if needed (tool box)
#//To reject  incoming Voice handvoer need to set McfbCellProfile::rejectVoiceIncHoAtEpsFb as TRUE
#// The parameter default is false, we don't reject --> it should be FALSE
#//FALSE allows EPSFB calls (LTE) to be accepted as VoNR
set Mcfb=1,McfbCellProfile=Default,McfbCellProfileUeCfg=Base rejectVoiceIncHoAtEpsFb false

///////////////////////////////////////////////////////////////////////////////////////////
//Voice centric Features
//////////////////////////////////////////////////////////////////////////////////////////
###################1)	Basic VoNR activation flag 
#//Makign sure other VoNR related paramter are set corretly
#//McfbCellProfile::epsFallbackOperation 2:INACTIVE (EPS-FB FORCED) 1 or 3:ACTIVE (VoNR Supported)

set GNBCUCPFunction=1,Mcfb=1 voiceEpsFbPossible true

#//set Mcfb=1,McfbCellProfile=.*,McfbCellProfileUeCfg=Base epsFallbackOperation 2

###################4)	VoNR Parameter - SRB DL and UL Retx
set GNBDUFunction=1,RadioBearerTable=1,SignalingRadioBearer=1 dlMaxRetxThreshold 16
set GNBDUFunction=1,RadioBearerTable=1,SignalingRadioBearer=1 tPollRetransmitDl 160
set GNBDUFunction=1,RadioBearerTable=1,SignalingRadioBearer=1 tPollRetransmitUl 80
set GNBDUFunction=1,RadioBearerTable=1,SignalingRadioBearer=1 ulMaxRetxThreshold 32

###################5)	911 over NR 
#//Makign sure 911 over NR is FORCED (0:911 over NR is ACTIVE, 1:FORCED)
#//Makign sure 911 over NR is FORCED (0:911 over VoNR is ACTIVE ,  1: RWR EPS is in effect, FORCED)
#//set Mcfb=1,McfbCellProfile=.*,McfbCellProfileUeCfg=Base epsFallbackOperationEm 1

###################6)	911 simless set to TRUE but won't impact since 911 over NR is FORCED 
##############NR Emergency Procedures (NR Low/Mid)
//set FeatureState=CXC4012534 featurestate 1

#############NR Limited Service Mode Emergency Call Support (NR Low/Mid)
#//NR Limited Service Mode Emergency Call Support (NR Low/Mid)
//set FeatureState=CXC4012538 featurestate 1

#//Enable for simless support but this will not active untill EoNR is activated
### Per Region request this is set to true, no impact if VoNR is not activatged. 
set NRCellDU= imsEmSupportEnabled true

###################7)	UE grouping + 5QI inactivity timer
set FeatureState=CXC4012549 featureState 1

###################8)	Meas- based EPSFB * dependency with Performance team CSR ### Moved to NR41 to activate MEAS_RWR
#//Need to set McfbCellProfile::epsFallbackOperation 3:ACTIVE_MEAS_RWR
#//set McfbCellProfileUeCfg=Base epsFallbackOperation 3

###################9)	Enable VoNR LA
set QosPriorityMapping=1,PriorityDomainMapping=5QI1 priorityDomain 16
set QosPriorityMapping=1,PriorityDomainMapping=5QI2 priorityDomain 18
Set QosPriorityMapping=1,PriorityDomainMapping=5QI6_7_8_9 priorityDomain 48	

################### 1.) Xn ANR (online change)
set GNBCUCPFunction=1,AnrFunction=1,AnrFunctionNR=1 anrCgiMeasInterFreqMode 1
set GNBCUCPFunction=1,AnrFunction=1,AnrFunctionNR=1 anrCgiMeasIntraFreqEnabled true

#//enable Xn IP lookup over Ng
set GNBCUCPFunction=1 xnIpAddrViaNgActive True


################### 2.) Xn Mobility  (online change)
#// Ensure RC656 is set to default, 1 - NG based HO (lock term points towards your neighbor), 0 - allows NG and Xn
###RC656 is replaced by MOM MO parameter "prefInterGnbHo = 0 Xn_HO" set by default in the BSW
#//scd RC656

################### 3.) Service Specific DRX  (online change)

get CXC4012548  licensestate > $licstate
set CXC4012548 featurestate 1

#//cr GNBCUCPFunction=1,UeGroupSelection=1
#//
#//crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=1
#//ueGroupId 1
#//ueGroupPriority 100
#//selectionCriteria 5qi==1
#//selectionProbability 100
#//end

set DrxProfile=Default,DrxProfileUeCfg=Base drxLongCycle 10
set DrxProfile=Default,DrxProfileUeCfg=Base drxOnDurationTimer 39
set DrxProfile=Default,DrxProfileUeCfg=Base drxInactivityTimer 15

pr GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VONR
if $nr_of_mos = 0
    crn GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VONR
    drxEnabled True
    drxInactivityTimer 8
    drxLongCycle 4
    drxOnDurationTimer 39
    ueGroupList 1
    prefUeGroupList
    end
else
    set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VONR drxEnabled True
    set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VONR drxInactivityTimer 8
    set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VONR drxLongCycle 4
    set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VONR drxOnDurationTimer 39
    set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VONR ueGroupList 1
    set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VONR prefUeGroupList
fi

set NRCellDU= drxProfileRef GNBDUFunction=1,UeCC=1,DrxProfile=Default
set NRCellDU= drxProfileenabled true

################### 4.)   tReorderingDl (online change)

set CUCP5qiTable=1,CUCP5qi=1 tReorderingDl 60
set CUCP5qiTable=1,CUCP5qi=2 tReorderingDl 60
set CUCP5qiTable=1,CUCP5qi=5 tReorderingDl 60

#################RRC-Multi-Target
set GNBCUCPFunction=1 rrcReestSupportType 2


## set CXC4012592 featurestate 1
## #####################USSM
## set CXC4012591 featurestate 1



######################## 11.) Automatic Xn Setup improvements (online change)
set GNBCUCPFunction=1 xnIpAddrViaNgActive True



######################## 12.)DRX Retransmission Timer -(online change)
// set CXC4012548 featurestate 1  --- Service Adaptive DRX (Voice & Data) - we already have this deployed
// scw RP1617:1 --- in 22.Q2 this is enabled by default

set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=Base drxRetransmissionTimerDl 8
set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VoNR drxRetransmissionTimerDl 8
set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=Base drxRetransmissionTimerUl 8
set GNBDUFunction=1,UeCC=1,DrxProfile=Default,DrxProfileUeCfg=VoNR drxRetransmissionTimerUl 8
###endfunc

//QoS Controlled scheduling
######################################

##Create new SrHandling Profile

crn GNBDUFunction=1,UeCC=1,SrHandling=5QI_5
ueConfGroupType 1
userLabel 
end

##load newly created child mo
lt SrHandling

##Turn on QoS Controlled SR Handling Base and Default Profiles
set GNBDUFunction=1,UeCC=1,SrHandling=5QI_5,SrHandlingUeCfg=Base$ srHandlingMode 1
set GNBDUFunction=1,UeCC=1,SrHandling=default,SrHandlingUeCfg=Base$ srHandlingMode 1


##Configure SR handling conditional on 5QI 1
set GNBDUFunction=1,UeCC=1,SrHandling=5QI_5,SrHandlingUeCfg=Base$ conditional5qi 1

##Point 5QI5 to the newly created SrHandling profile
set GNBDUFunction=1,DU5qiTable=1,DU5qi=5$ srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=5QI_5
        """]
        if band == 'N41':
            self.s_dict += [F'set GNBDUFunction=1,DU5qiTable=2,DU5qi=5$ srHandlingRef GNBDUFunction=1,UeCC=1,SrHandling=5QI_5']
        self.s_dict += [F"""
###### MCS Reduction activation#############
scw RP1761:1

##*****************************SA NR ANR for IRAT B2 based**************************************
##*****************ANR For IRAT B2*******************************
pr GNBCUCPFunction=1,AnrFunction=1
if $nr_of_mos = 0
    cr GNBCUCPFunction=1,AnrFunction=1
fi
set GNBCUCPFunction=1,AnrFunction=1 removeEnbTime 7
set GNBCUCPFunction=1,AnrFunction=1 removeFreqRelTime 15                  
set GNBCUCPFunction=1,AnrFunction=1 removeGnbTime 7                      
set GNBCUCPFunction=1,AnrFunction=1 removeNrelTime 7                 
pr GNBCUCPFunction=1,AnrFunction=1,AnrFunctionEUtran=1
if $nr_of_mos = 0
    cr GNBCUCPFunction=1,AnrFunction=1,AnrFunctionEUtran=1 
fi
set GNBCUCPFunction=1,AnrFunction=1,AnrFunctionEUtran=1 anrCgiMeasEUtranEnabled true
set NRCellCU=.*,EUtranFreqRelation= anrMeasOn true
set NRCellCU=.*,EUtranFreqRelation=2.* anrMeasOn false

cvms Post_VoNR_prequsite_$date
"""]
        self.writemos_script_file()

        # VONR_Prereq_SI
        self.relative_path[-1] = F'nr_03_VONR_Prereq_SI_{band}_{self.node}.mos'
        self.s_dict = [F"""
cvms Pre_VoNR_Prereq_SI_$date

//////////////////////////////////////////////////////////////////////
///  DFTS OFDM Wave Form support (N41,N71, N25) Feature number: FAJ 121 5089
///  2/1/2022 - Rev1 
///  	Initial setting Config for 21.Q4
//////////////////////////////////////////////////////////////////////
#### checks
get FeatureState=CXC4012373
get NRCellDU dftSOfdmMsg3Enabled
get NRCellDU dftSOfdmPuschEnabled

#### Activate feature
mr NRCellDU_unlock
ma NRCellDU_unlock NRCellDU= administrativeState 1
bl NRCellDU_unlock

st NRCellDU
wait 2

set SystemFunctions=1,Lm=1,FeatureState=CXC4012373 featurestate 1
set NRCellDU dftSOfdmMsg3Enabled true
set NRCellDU dftSOfdmPuschEnabled true

#### checks
get FeatureState=CXC4012373
get NRCellDU dftSOfdmMsg3Enabled
get NRCellDU dftSOfdmPuschEnabled

#### ---- NR Emergency Procedures (NR Low/Mid) ---- NR Limited Service Mode Emergency Call Support (NR Low/Mid)
set SystemFunctions=1,Lm=1,FeatureState=CXC4012534 featurestate 1
set SystemFunctions=1,Lm=1,FeatureState=CXC4012538 featurestate 1
deb NRCellDU_unlock
wait 2
st NRCellDU
wait 40s

cvms Post_VoNR_Prereq_SI_$date
"""]
        self.writemos_script_file()

        # VoNR_activation_script_NSI_0908
        self.relative_path[-1] = F'nr_04_VoNR_activation_script_NSI_0908_{band}_{self.node}.mos'
        self.s_dict = [F"""
cvms Pre_VoNR_activation_$date

mr cellcu
ma cellcu ,NRCellCU=
for $mo in cellcu
    $sourceCell = ldn($mo)
    get $mo nRCellCUId > $cellname   
    pr GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=$cellname$
    if $nr_of_mos = 0
        cr GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=$cellname
    fi
    set $sourceCell mcfbCellProfileRef GNBCUCPFunction=1,Mcfb=1,McfbCellProfile=$cellname
done
mr cellcu
lt McfbCellProfileUeCfg
lset Mcfb=1,McfbCellProfile=[KJA].*,McfbCellProfileUeCfg=Base rsrpCellCandidate hysteresis=10,threshold=-124,timeToTrigger=40
lset Mcfb=1,McfbCellProfile=[KJA].*,McfbCellProfileUeCfg=Base triggerQuantity 0
lset Mcfb=1,McfbCellProfile=[KJ].*,McfbCellProfileUeCfg=Base epsFallbackOperation 3
lset Mcfb=1,McfbCellProfile=[KJ].*,McfbCellProfileUeCfg=Base epsFallbackOperationEm 0
lset Mcfb=1,McfbCellProfile=A.*1,McfbCellProfileUeCfg=Base epsFallbackOperation 3
lset Mcfb=1,McfbCellProfile=A.*1,McfbCellProfileUeCfg=Base epsFallbackOperationEm 0

cvms Post_VoNR_activation_$date
"""]
        self.writemos_script_file()


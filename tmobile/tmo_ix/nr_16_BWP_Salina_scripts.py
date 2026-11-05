import os
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_16_BWP_Salina_scripts(tmo_xml_base):
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
            f.write('\n'.join(['confbl-', 'gs', 'l-', 'unset all', '']))

    def special_formate_scripts(self):
        if len(self.gnbdata) == 0: return
        self.relative_path[-1] = F'nr_12_MotoEdge_Austin_v3_{self.node}.mos'
        if str(self.usid.client.mname) not in ['Salina']: return
        if len(self.df_gnb_cell.loc[(self.df_gnb_cell.postcell.str.contains('^A'))].index) > 0:
            # band = 'N41'
            self.s_dict = [F"""
cvms Pre_USCA_MotoEdge_Austin_Wingtech_$date

pr GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=MotoEdge
if $nr_of_mos = 1
del GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=MotoEdge
else
l echo "Motoedge profile not present"
fi

pr GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=MotoEdge
if $nr_of_mos = 1
del GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=MotoEdge
else
l echo "Motoedge UEgroup profile not present"
fi

pr GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=Austin_Wingtech
if $nr_of_mos = 1
del GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=Austin_Wingtech
else
l echo "Austin_Wingtech profile not present"
fi

pr GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=Austin_Wingtech
if $nr_of_mos = 1
del GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=Austin_Wingtech
else
l echo "Austin_Wingtech UEgroup profile not present"
fi

set FeatureState=CXC4012663 featurestate 1  

crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=MotoEdge
selectionCriteria imeitac=={{35046480,35118823,35548633,35601739,35643969,35888262,35982551}} 
selectionProbability 100
ueGroupId 13
ueGroupPriority 95
userLabel 
end

crn GNBCUCPFunction=1,UeGroupSelection=1,UeServiceGroupDefinition=Austin_Wingtech
selectionCriteria imeitac=={{86169006,86958906}} && imeisvn<09 || imeitac=={{35946390,35657463,35771112,35769070,35603762}} && imeisvn<62 
ueServiceGroupId 9
ueServiceGroupPriority 98
userLabel
end

crn GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=MotoEdge
maxDlCcAllowed 2 
maxUlCcAllowed 1 
ueGroupList 13 
end 

crn GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=Austin_Wingtech
maxDlCcAllowed 1 
maxUlCcAllowed 1 
ueConfGroupList 9
end 

set NRCellCU= caCellProfileRef CarrierAggregation=1,CaCellProfile=Default 
set GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default ueConfGroupType 1

cvms Post_USCA_MotoEdge_Austin_Wingtech_$date
"""]
        elif len(self.df_gnb_cell.loc[((self.df_gnb_cell.postcell.str.contains('^K')) |
                                       (self.df_gnb_cell.postcell.str.contains('^J')) |
                                       (self.df_gnb_cell.postcell.str.contains('^I')))].index) > 0:
            self.s_dict = [F"""
cvms Pre_USCA_MotoEdge_$date
pr GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=MotoEdge
if $nr_of_mos = 1
del GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=MotoEdge
else
l echo "Motoedge profile not present"
fi

pr GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=MotoEdge
if $nr_of_mos = 1
del GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=MotoEdge
else
l echo "Motoedge UEgroup profile not present"
fi

set FeatureState=CXC4012663 featurestate 1  

crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=MotoEdge_Austin_Wingtech
selectionCriteria imeitac=={{35046480,35118823,35548633,35601739,35643969,35888262,35982551}} || imeitac=={{86169006,86958906}} && imeisvn<09 || imeitac=={{35946390,35657463,35771112,35769070,35603762}} && imeisvn<62 
selectionProbability 100
ueGroupId 13
ueGroupPriority 99
userLabel 
end

crn GNBCUCPFunction=1,CarrierAggregation=1,CaCellProfile=Default,CaCellProfileUeCfg=MotoEdge_Austin_Wingtech
blockedSCellFreqList 501390,502110,502590,504750,517710,521310,522030
ueGroupList 13 
end 

set NRCellCU= caCellProfileRef CarrierAggregation=1,CaCellProfile=Default 

cvms Post_USCA_MotoEdge_$date
"""]

        self.writemos_script_file()

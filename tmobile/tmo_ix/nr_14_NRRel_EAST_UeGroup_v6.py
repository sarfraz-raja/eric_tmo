from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_14_NRRel_EAST_UeGroup_v6(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if self.usid.client.mname not in ['Bloomfield', 'Norfolk', 'Philadelphia', 'Salina']: return
        if len(self.df_gnb_cell.loc[self.df_gnb_cell.postcell.str.startswith('K', na=False)].index) == 0: return

        self.relative_path.insert(-2, 'NR_NR_Relations')
        if len(self.usid.df_gnb_cell.postsite.unique()) > 1:
            self.script_list.extend(self.pre_post_check('Pre'))
            self.script_list.extend(self.nr_relation_creation())
            self.script_list.extend(self.pre_post_check('Post'))

    def nr_relation_creation(self):
        lines = [
            """
//Script to create service/User Specific Mobility for Samsung galaxy A53 drop issue
cvmk Pre_InhibitN41_SA_GalaxyA53_Act_$date

pr GNBCUCPFunction=1,UeGroupSelection=1
if $nr_of_mos = 0
    cr GNBCUCPFunction=1,UeGroupSelection=1
fi

get UeGroupSelectionProfile= selectionCriteria imeitac
if $nr_of_mos = 0
    crn GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=GalaxyA53 
    ueGroupId 5
    ueGroupPriority 101
    selectionProbability 100
    selectionCriteria imeitac=={35057957,35098767,35345419,35849772,35424140,35026620,35078262,35102405,35672173}
    end
fi

///////////////////////////////////////////////////////////////////////////////
//Verify all  UEMC profiles are created and reserved on each relation and if any missing created.

func CheckMCPCPcell
    if $MCPCNRF !~ $NRFRQ
        crn GNBCUCPFunction=1,Mcpc=1,McpcPCellNrFreqRelProfile=$NRFRQ
        ueConfGroupType 0
        end
        set $NRFR mcpcPCellNrFreqRelProfileRef Mcpc=1,McpcPCellNrFreqRelProfile=$NRFRQ
        lt McpcPCellNrFreqRelProfileUeCfg
    fi
endfunc

func CheckUEMCNR
    if $UEMCFRQ !~ $NRFRQ
        crn GNBCUCPFunction=1,UeMC=1,UeMCNrFreqRelProfile=$NRFRQ
        ueConfGroupType 0
        end
        set $NRFR ueMCNrFreqRelProfileRef UeMC=1,UeMCNrFreqRelProfile=$NRFRQ
        lt UeMCNrFreqRelProfileUeCfg
        set UeMC=1,UeMCNrFreqRelProfile=$NRFRQ,UeMCNrFreqRelProfileUeCfg connModeAllowedPSCell true 
    fi
endfunc

mr NRFRQREL 
ma NRFRQREL ^NRFreqRelation= nRFrequencyRef NRFrequency=5
for $mo in NRFRQREL
    $NRFR = ldn($mo)
    get $mo nRFrequencyRef > $NRFRQ
    get $NRFRQ arfcnValueNRDl >  $NRFRQ
    get $mo mcpcPCellNrFreqRelProfileRef > $MCPCNRF
    CheckMCPCPcell
    get $mo ueMCNrFreqRelProfileRef > $UEMCFRQ
    CheckUEMCNR
done

///////////////////////////////////////////////////////////////////////////////
// create MCPC NR Freq-Relation Profiles for VoNR  ////////////////////////////
///////////////////////////////////////////////////////////////////////////////

mr PCELLMCPC
ma PCELLMCPC McpcPCellNrFreqRelProfile=5
for $f in PCELLMCPC
    get $f mcpcPCellNrFreqRelProfileId > $MCPCID
    get Mcpc=1,McpcPCellNrFreqRelProfile=$MCPCID,McpcPCellNrFreqRelProfileUeCfg= ueGroupList =.*5
    if $nr_of_mos = 0
        crn Mcpc=1,McpcPCellNrFreqRelProfile=$MCPCID,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53
        ueGroupList 5
        end
    else
        mr PrefUEGL
        ma PrefUEGL Mcpc=1,McpcPCellNrFreqRelProfile=$MCPCID,McpcPCellNrFreqRelProfileUeCfg= ueGroupList =.*5
        del PrefUEGL
        crn Mcpc=1,McpcPCellNrFreqRelProfile=$MCPCID,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53
        ueGroupList 5
        end
    fi
done

mr N19MCPC
ma N19MCPC McpcPCellNrFreqRelProfile=3
for $f in N19MCPC
get $f mcpcPCellNrFreqRelProfileId > $MCPCID
get Mcpc=1,McpcPCellNrFreqRelProfile=$MCPCID,McpcPCellNrFreqRelProfileUeCfg= ueGroupList =.*5
if $nr_of_mos = 0
    crn Mcpc=1,McpcPCellNrFreqRelProfile=$MCPCID,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53
    ueGroupList 5
    end
else
    mr PrefUEGL
    ma PrefUEGL Mcpc=1,McpcPCellNrFreqRelProfile=$MCPCID,McpcPCellNrFreqRelProfileUeCfg= ueGroupList =.*5
    del PrefUEGL
    crn Mcpc=1,McpcPCellNrFreqRelProfile=$MCPCID,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53
    ueGroupList 5
    end
fi
done

#############################################################################
### inhibit SA connected mode mobility to N41 and N19 for Galaxy A53 devices but NSA is still active

set Mcpc=1,McpcPCellNrFreqRelProfile=5.*,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53 inhibitMeasForCellCandidate true
set Mcpc=1,McpcPCellNrFreqRelProfile=3.*,McpcPCellNrFreqRelProfileUeCfg=GalaxyA53 inhibitMeasForCellCandidate true

cvmk Post_InhibitN41_SA_GalaxyA53_Act_$date

"""
        ]
        return lines
    
    def pre_post_check(self, activity):
        return [
            F'#################################################################################################',
            F'##############################################################',
            F'####:----------------> {activity} Check <----------------:####',
            F'get GNBCUCPFunction=1,UeGroupSelection=',
            F'get GNBCUCPFunction=1,UeGroupSelection=1,UeGroupSelectionProfile=',
            F'hget ^NRFrequency=.* arfcnValueNRDl|^band(List|ListManual)|gscn$|^smtc(Duration|Offset|Periodicity|Scs)$',
            F'hget ^NRFreqRelation=.* mcpcPCellNrFreqRelProfileRef|nRFrequencyRef',
            F'hget ^McpcPCellNrFreqRelProfile=',
            F'hget ^McpcPCellNrFreqRelProfileUeCfg=',
            F'',
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

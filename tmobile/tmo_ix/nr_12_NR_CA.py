from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class nr_12_NR_CA(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        if self.gnbdata.get('IDLE') is None or len(self.usid.gnodeb.keys()) == 0: return

        self.relative_path.insert(-2, 'NR_NR_Relations')
        if self.gnbdata.get('IDLE') and len(self.usid.gnodeb.keys()) > 0:
            self.script_list.extend(self.get_nsa_nr_ca_para())
            if len(self.script_list) > 0:
                self.script_list += self.activity_check('Pre') + self.idle_activation() + self.script_list + self.activity_check('Post')
    
    def idle_activation(self):
        lines = [F"""
####:----------------> NSA NR CA Enablement, IDL Port {self.gnbdata.get("IDLE")} <----------------:####
get Equipment=1,FieldReplaceableUnit={self.gnbdata.get("BBId")},TnPort={self.gnbdata["IDLE"]}$
get Transport=1,EthernetPort=ERAN$
get Transport=1,VlanPort=ERAN_NR$
get Transport=1,VlanPort=ERAN_NR$ vlanId 4060

pr ^GNBDUFunction=1$
if $nr_of_mos > 0
    set GNBDUFunction=1$ caVlanPortRef Transport=1,VlanPort=ERAN_NR
    set GNBDUFunction=1,NRCellDU= additionalPucchForCaEnabled true
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012477$ featureState 1
    set SystemFunctions=1,Lm=1,FeatureState=CXC4012478$ featureState 1
fi
"""]
        for gnb in self.usid.gnodeb.keys():
            if gnb == self.node: continue
            if self.usid.gnodeb.get(gnb, {}).get('IDLE', False):
                lines.extend([F"""
pr GNBDUFunction=1,ExtGNBDUPartnerFunction={self.usid.gnodeb[gnb]["nodeid"]}$
if $nr_of_mos = 0
    crn GNBDUFunction=1,ExtGNBDUPartnerFunction={self.usid.gnodeb[gnb]["nodeid"]}
    caVlanPortRef Transport=1,VlanPort=ERAN_NR
    gNBDUId 1
    gNBId {self.usid.gnodeb[gnb]["nodeid"]}
    gNBIdLength {self.usid.gnodeb[gnb]["gNBIdLength"]}
    end
fi
"""])
        return lines
    
    def get_nsa_nr_ca_para(self):
        lines = []
        nsa_nr_ca_flag = False
        for _, row in self.df_gnb_cell.iterrows():
            for _, t_row in self.usid.df_gnb_cell.loc[self.usid.df_gnb_cell.postsite != self.node].iterrows():
                if not self.usid.gnodeb.get(t_row.postsite).get('IDLE'): continue
                if row.postcell[-2] == t_row.postcell[-2]:
                    nsa_nr_ca_flag = True
                    t_nci = int(self.usid.gnodeb.get(t_row.postsite).get("nodeid")) * \
                            (2 ** (36 - int(self.usid.gnodeb.get(t_row.postsite).get("gNBIdLength")))) + int(t_row.cellid)
                    lines.extend([
                        F'pr GNBCUCPFunction=1,NRCellCU={row.postcell},NRCellRelation=auto{t_nci}$',
                        F'if $nr_of_mos > 0',
                        F'  set GNBCUCPFunction=1,NRCellCU={row.postcell},NRCellRelation=auto{t_nci}$ coverageIndicator 3',
                        F'  set GNBCUCPFunction=1,NRCellCU={row.postcell},NRCellRelation=auto{t_nci}$ sCellCandidate 1',
                        F'fi',
                        F'pr GNBCUCPFunction=1,NRCellCU={row.postcell},NRCellRelation={t_row.postcell}$',
                        F'if $nr_of_mos > 0',
                        F'  set GNBCUCPFunction=1,NRCellCU={row.postcell},NRCellRelation={t_row.postcell}$ coverageIndicator 3',
                        F'  set GNBCUCPFunction=1,NRCellCU={row.postcell},NRCellRelation={t_row.postcell}$ sCellCandidate 1',
                        F'fi',
                    ])
        if nsa_nr_ca_flag:
            lines = [F'####:----------------> N41 NSA NR CA Enablement <----------------:####'] + lines + ['', '']
        return lines
    
    @staticmethod
    def activity_check(activity=''):
        return [
            '',
            F'####:----------------> {activity} Check <----------------:####',
            F'pr TnPort=',
            F'hget Transport=1,VlanPort= encapsulation|vlanId|isTagged|lowLatencySwitching|reservedBy',
            F'hget Transport=1,EthernetPort= admOperatingMode|encapsulation|autoNegEnable|reservedBy',
            F'get (ENodeB|GNBDU)Function=1|ExtGNBDUPartnerFunction=.* ^eranVlanPortRef$|^eNBId$|^caVlanPortRef$|^gNBId$|^gNBIdLength$|^gNBDUName$',
            F'st InterMeLink|EthernetPort|BbLink',
            F'hget ^FeatureState=(CXC4012478|CXC4012477)$ ^FeatureState$|^description$|^serviceState$|^licenseState$',
            F'get ^NRCellRelation= sCellCandidate 1',
            F'get ^NRCellRelation= coverageIndicator 3',
            F'get ^NRCellRelation= caStatusActive true',
            '',
            '',
        ]
    
    def cr_file_path(self):
        if len(self.script_list) == 0: return
        import os
        self.script_file = os.path.join(self.usid.base_dir, *self.relative_path)
        out_dir = os.path.dirname(self.script_file)
        if not os.path.exists(out_dir): os.makedirs(out_dir)


#### pr Equipment=1,FieldReplaceableUnit={self.gnbdata.get("BBId")},TnPort={self.gnbdata["IDLE"]}$
#### if $nr_of_mos = 0
####     cr Equipment=1,FieldReplaceableUnit={self.gnbdata.get("BBId")},TnPort={self.gnbdata["IDLE"]}
#### fi
####
#### pr Transport=1,EthernetPort=ERAN$
#### if $nr_of_mos = 0
####     crn Transport=1,EthernetPort=ERAN
####     administrativeState 1
####     autoNegEnable false
####     admOperatingMode 9
####     encapsulation Equipment=1,FieldReplaceableUnit={self.gnbdata.get("BBId")},TnPort={self.gnbdata.get("IDLE")}
####     userLabel {self.gnbdata.get("IDLE")}
####     end
#### fi
####
#### pr Transport=1,VlanPort=ERAN_NR$
#### if $nr_of_mos = 0
####     crn Transport=1,VlanPort=ERAN_NR
####     vlanId 4060
####     userLabel ERAN_NR
####     encapsulation Transport=1,EthernetPort=ERAN
####     end
#### else
####     set Transport=1,VlanPort=ERAN_NR$ vlanId 4060
#### fi
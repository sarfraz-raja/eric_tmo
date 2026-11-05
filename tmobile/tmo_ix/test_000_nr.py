from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class test_000_nr(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.gnbdata) == 0: return
        self.motype = 'GNBDU'
        self.relative_path.insert(-1, 'BACKUP_SCRIPT')
        self.script_list += self.test_script()

    def transport_site(self):
        tn_mo = ['return', 'return', 'return', 'return']
        tn_mo.extend(['', '#############:- Transport MOs-:#############', ''])

        tn_mo.extend(self.create_mos_script_from_dict({'qosProfilesId': '1'}, 'QosProfiles', F'Transport=1,QosProfiles=1'))
        tmp_dict, _ = self.get_mo_dict_for_id_tag('DscpPcpMap', '1')
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'DscpPcpMap', F'Transport=1,QosProfiles=1,DscpPcpMap=1'))
        tn_mo.extend(['', F'set Transport=1,Router=vr_OAM,InterfaceIPv4=1$ egressQosMarking Transport=1,QosProfiles=1,DscpPcpMap=1',
                      F'set Transport=1,Router=vr_TRAFFIC,InterfaceIPv4=1$ egressQosMarking Transport=1,QosProfiles=1,DscpPcpMap=1', ''])
        int_rout = 'Transport=1,Router=Node_Internal_F1'
        tn_mo.extend(self.create_mos_script_from_dict({'routerId': 'Node_Internal_F1'}, 'Router', int_rout))
        tn_mo.extend(self.create_mos_script_from_dict({'interfaceIPv4Id': 'NRCUCP', 'loopback': 'true'}, 'InterfaceIPv4', F'{int_rout},InterfaceIPv4=NRCUCP'))
        tn_mo.extend(self.create_mos_script_from_dict({'addressIPv4Id': 1, 'address': '169.254.42.42/32'}, 'AddressIPv4', F'{int_rout},InterfaceIPv4=NRCUCP,AddressIPv4=1'))
        tn_mo.extend(self.create_mos_script_from_dict({'interfaceIPv4Id': 'NRDU', 'loopback': 'true'}, 'InterfaceIPv4',  F'{int_rout},InterfaceIPv4=NRDU'))
        tn_mo.extend(self.create_mos_script_from_dict({'addressIPv4Id': 1, 'address': '169.254.42.42/32'}, 'AddressIPv4', F'{int_rout},InterfaceIPv4=NRDU,AddressIPv4=1'))

        tmp_dict, _ = self.get_mo_dict_for_id_tag('SctpProfile', '1')
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'SctpProfile', 'Transport=1,SctpProfile=1'))
        tmp_dict.update({'sctpProfileId': 'Node_Internal_F1'})
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'SctpProfile', 'Transport=1,SctpProfile=Node_Internal_F1'))
        tmp_dict = {'sctpEndpointId': 'NR_X2', 'portNumber': '36422', 'sctpProfile': 'Transport=1,SctpProfile=1',
                     'localIpAddress': F'Transport=1,Router={self.gnbdata["lte"]},InterfaceIPv4=1,AddressIPv4=1'}
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'SctpEndpoint', 'Transport=1,SctpEndpoint=NR_X2'))
        tmp_dict.update({'sctpEndpointId': 'NR_N2', 'portNumber': '38412'})
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'SctpEndpoint', 'Transport=1,SctpEndpoint=NR_N2'))
        tmp_dict.update({'sctpEndpointId': 'NR_Xn', 'portNumber': '38422'})
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'SctpEndpoint', 'Transport=1,SctpEndpoint=NR_Xn'))
        tmp_dict.update({'sctpEndpointId': 'F1_NRCUCP', 'portNumber': '38472', 'sctpProfile': 'Transport=1,SctpProfile=Node_Internal_F1',
                         'localIpAddress': F'Transport=1,Router=Node_Internal_F1,InterfaceIPv4=NRDU,AddressIPv4=1'})
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'SctpEndpoint', 'Transport=1,SctpEndpoint=F1_NRCUCP'))
        tmp_dict.update({'sctpEndpointId': 'F1_NRDU'})
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'SctpEndpoint', 'Transport=1,SctpEndpoint=F1_NRDU'))

        tmp_dict, _ = self.get_mo_dict_for_id_tag('RadioEquipmentClock', '1')
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'RadioEquipmentClock', 'Transport=1,Synchronization=1,RadioEquipmentClock=1'))
        tmp_dict, _ = self.get_mo_dict_for_id_tag('RadioEquipmentClockReference', '1')
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'RadioEquipmentClockReference',
                                                      'Transport=1,Synchronization=1,RadioEquipmentClock=1,RadioEquipmentClockReference=1'))
        tmp_dict, _ = self.get_mo_dict_for_id_tag('TimeSyncIO', '1')
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'TimeSyncIO', 'Transport=1,Synchronization=1,TimeSyncIO=1'))
        tmp_dict, _ = self.get_mo_dict_for_id_tag('GnssInfo', '1')
        tn_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'GnssInfo', 'Transport=1,Synchronization=1,TimeSyncIO=1,GnssInfo=1'))
        tn_mo.extend([
            F'',
            F'crn Transport=1,SctpEndpoint=NR_X2',
            F'localIpAddress Transport=1,Router=vr_TRAFFIC,InterfaceIPv4=1,AddressIPv4=1',
            F'portNumber 36422',
            F'sctpProfile SctpProfile=1',
            F'userLabel',
            F'end',
            F'',
            F'crn Transport=1,SctpEndpoint=NR_N2',
            F'localIpAddress Transport=1,Router=vr_TRAFFIC,InterfaceIPv4=1,AddressIPv4=1',
            F'portNumber 38412',
            F'sctpProfile SctpProfile=1',
            F'userLabel',
            F'end',
            F'',
            F'crn Transport=1,SctpEndpoint=NR_Xn',
            F'localIpAddress Transport=1,Router=vr_TRAFFIC,InterfaceIPv4=1,AddressIPv4=1',
            F'portNumber 38422',
            F'sctpProfile SctpProfile=1',
            F'userLabel',
            F'end',
            F'',
            F'crn Transport=1,SctpEndpoint=F1_NRDU',
            F'localIpAddress Transport=1,Router=Node_Internal_F1,InterfaceIPv4=NRDU,AddressIPv4=1',
            F'portNumber 38472',
            F'sctpProfile SctpProfile=Node_Internal_F1',
            F'userLabel',
            F'end',
            F'',
            F'crn Transport=1,SctpEndpoint=F1_NRCUCP',
            F'localIpAddress Transport=1,Router=Node_Internal_F1,InterfaceIPv4=NRCUCP,AddressIPv4=1',
            F'portNumber 38472',
            F'sctpProfile SctpProfile=Node_Internal_F1',
            F'userLabel',
            F'end',
            F'',
            F'crn GNBDUFunction=1,EndpointResource=1,LocalSctpEndpoint=1',
            F'interfaceUsed 3',
            F'sctpEndpointRef SctpEndpoint=F1_NRDU',
            F'end',
            F'',
            F'crn GNBCUCPFunction=1,EndpointResource=1,LocalSctpEndpoint=4',
            F'interfaceUsed 3',
            F'sctpEndpointRef SctpEndpoint=F1_NRCUCP',
            F'end',
            F'',
            F'crn GNBCUCPFunction=1,EndpointResource=1,LocalSctpEndpoint=3',
            F'interfaceUsed 6',
            F'sctpEndpointRef SctpEndpoint=NR_Xn',
            F'end',
            F'',
            F'crn GNBCUCPFunction=1,EndpointResource=1,LocalSctpEndpoint=2',
            F'interfaceUsed 7',
            F'sctpEndpointRef SctpEndpoint=NR_X2',
            F'end',
            F'',
            F'crn GNBCUCPFunction=1,EndpointResource=1,LocalSctpEndpoint=1',
            F'interfaceUsed 4',
            F'sctpEndpointRef SctpEndpoint=NR_N2',
            F'end',
            F'',
            F'',
        ])
        return tn_mo

    def gnb_function(self):
        gnb_mo = []
        gnb_mo.extend(['', '#############:- GNBCUUPFunction MO-:#############'])
        tmp_dict = {
                'gNBCUUPFunctionId': 1,
                'gNBId': self.gnbdata["nodeid"],
                'gNBIdLength': self.gnbdata['gNBIdLength'],
                'pLMNIdList': self.gnbdata['plmnlist'],
                'intraRanIpAddressRef': F'Transport=1,Router={self.gnbdata["lte"]},InterfaceIPv4=1,AddressIPv4=1',
                'upIpAddressRef': F'Transport=1,Router={self.gnbdata["lte"]},InterfaceIPv4=1,AddressIPv4=1',
                'xnUpIpAddressRef': F'Transport=1,Router={self.gnbdata["lte"]},InterfaceIPv4=1,AddressIPv4=1'
            }
        gnb_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'GNBCUUPFunction', 'GNBCUUPFunction=1'))

        gnb_mo.extend(['', '#############:- GNBDUFunction MO-:#############', ''])
        tmp_dict = {
            'gNBDUFunctionId': 1,
            'gNBDUId': 1,
            'gNBId': self.gnbdata["nodeid"],
            'gNBIdLength': self.gnbdata['gNBIdLength'],
            'f1SctpEndPointRef': 'Transport=1,SctpEndpoint=F1_NRDU',
        }
        gnb_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'GNBDUFunction', 'GNBDUFunction=1'))
        tmp_dict = {'termPointToGNBCUCPId': 1, 'administrativeState': 'UNLOCKED', 'ipv4Address': '169.254.42.42'}
        gnb_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'TermPointToGNBCUCP', 'GNBDUFunction=1,TermPointToGNBCUCP=1'))

        gnb_mo.extend(['', '#############:- GNBCUCPFunction MO-:#############', ''])
        tmp_dict = {
            'gNBCUCPFunctionId': 1,
            'gNBCUName': 1,
            'gNBId': self.gnbdata["nodeid"],
            'gNBIdLength': self.gnbdata['gNBIdLength'],
            'pLMNId': {'mcc': self.gnbdata['plmnlist'].get('mcc'), 'mnc': self.gnbdata['plmnlist'].get('mnc')},
            'f1SctpEndPointRef': 'Transport=1,SctpEndpoint=F1_NRCUCP',
            'ngcSctpEndPointRef': 'Transport=1,SctpEndpoint=NR_N2',
            'x2SctpEndPointRef': 'Transport=1,SctpEndpoint=NR_X2',
            'xnSctpEndPointRef': 'Transport=1,SctpEndpoint=NR_Xn',
        }
        gnb_mo.extend(self.create_mos_script_from_dict(tmp_dict, 'GNBCUCPFunction', 'GNBCUCPFunction=1'))
        gnb_mo.extend(self.create_mos_script_from_dict({'eUtraNetworkId': 1}, 'EUtraNetwork', 'GNBCUCPFunction=1,EUtraNetwork=1'))

        return gnb_mo

    def test_script(self):
        ngs = [
            F'',
            F'cvms Parameters_BKP_$date',
            F'',
            F'#############:-NodeGroupSyncMember-:#############',
            F'lset SystemFunctions=1,Lm=1,FeatureState=CXC4011018$ featureState 1',
            F'',
            F'crn Transport=1,Synchronization=1,RadioEquipmentClock=1,NodeGroupSyncMember=1',
            F'administrativeState 1',
            F'selectionMode 1',
            F'syncNodePriority 1',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=A',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=B',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=C',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=D',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=E',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=F',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=G',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=H',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=J',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=K',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=L',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=M',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=N',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=P',
            F'syncRiPortCandidate Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},RiPort=Q',
            F'end',
            F'',
            F'',
            F'',
        ]
        return ngs

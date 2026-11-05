import copy
from xml.dom.minidom import Document
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C07_01a_Transport(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        node_data = self.gnbdata if len(self.enbdata) == 0 or (self.enbdata.get('MMBB') and self.gnbdata['lte_plength'] != '32') else self.enbdata
        if node_data.get('BBChange') is False: return
        self.reconfig_ap_file_path_to_remote()
        self.script_list = [self.ap_rcp_msg_cap(), self.create_rpc_msg(node_data=node_data), self.rcp_msg_close()]

    def create_rpc_msg(self, *, node_data: dict) -> Document:
        tmp_dict = {
            'managedElementId': self.node, 'userLabel': self.node,
            'Transport': {
                'transportId': '1',
                'QosProfiles': {'qosProfilesId': '1',
                                'DscpPcpMap': self.get_mo_dict_from_site_or_db(moc='DscpPcpMap', mo_id='1')},
                'Router': [],
                # 'Ptp': {},
                'Synchronization': self.get_mo_dict_from_site_or_db(moc='Synchronization', mo_id='1'),
                'SctpProfile': [self.get_mo_dict_from_site_or_db(moc='SctpProfile', mo_id='1')],
                'SctpEndpoint': [],
            },
            'NodeSupport': {'nodeSupportId': '1'}
        }
        # Timings and Synchronization (GPS and Ptp)
        # RadioEquipmentClockReference priority based on if PTP is configured or not
        # 1 - Ptp, 2 - GPS, 3 - Frequency Sync, 4 - Secondary Frequency Sync
        tmp_dict['Transport']['Synchronization']['RadioEquipmentClock'] = self.get_mo_dict_from_site_or_db(moc='RadioEquipmentClock', mo_id='1')
        tmp_dict['Transport']['Synchronization']['RadioEquipmentClock']['RadioEquipmentClockReference'] = []
        # GPS Timings
        tmp_dict['Transport']['Synchronization']['TimeSyncIO'] = self.get_mo_dict_from_site_or_db(moc='TimeSyncIO', mo_id='1')
        tmp_dict['Transport']['Synchronization']['TimeSyncIO'] |= {
            'encapsulation': F'Equipment=1,FieldReplaceableUnit={node_data["BBId"]},SyncPort=1',
            'GnssInfo': self.get_mo_dict_from_site_or_db(moc='GnssInfo', mo_id='1')
        }
        clock_ref = self.get_mo_dict_from_site_or_db(moc='RadioEquipmentClockReference', mo_id='1')
        clock_ref |= {'encapsulation': F'Transport=1,Synchronization=1,TimeSyncIO=1'}
        tmp_dict['Transport']['Synchronization']['RadioEquipmentClock']['RadioEquipmentClockReference'].append(copy.deepcopy(clock_ref))
        # PTP Timings
        if node_data['lte_plength'] == '27' or (str(node_data['csr_type']).upper() in ['IXR-E', 'IXR-R6']):
            # Set priority for GPS to 2 when Ptp is configured
            tmp_dict['Transport']['Synchronization']['RadioEquipmentClock']['RadioEquipmentClockReference'][0]['priority'] = '2'
            tmp_dict['Transport']['Ptp'] = self.get_mo_dict_from_site_or_db(moc='Ptp', mo_id='1')
            tmp_dict['Transport']['Ptp']['BoundaryOrdinaryClock'] = self.get_mo_dict_from_site_or_db(moc='BoundaryOrdinaryClock', mo_id='1')
            tmp_dict['Transport']['Ptp']['BoundaryOrdinaryClock']['PtpBcOcPort'] = self.get_mo_dict_from_site_or_db(moc='PtpBcOcPort', mo_id='0')
            tmp_dict['Transport']['Ptp']['BoundaryOrdinaryClock']['PtpBcOcPort'] |= {
                'transportInterface': F'Transport=1,EthernetPort={node_data["TnPort"]}'
            }
            clock_ref = self.get_mo_dict_from_site_or_db(moc='RadioEquipmentClockReference', mo_id='4')
            clock_ref |= {'encapsulation': F'Transport=1,Ptp=1,BoundaryOrdinaryClock=1', 'priority': '1'}
            tmp_dict['Transport']['Synchronization']['RadioEquipmentClock']['RadioEquipmentClockReference'].append(copy.deepcopy(clock_ref))
        # Router and SctpEndpoint Configurations
        tmp_dict['Transport']['Router'].append({'routerId': node_data['oam'], 'InterfaceIPv4': {
            'interfaceIPv4Id': '1', 'egressQosMarking': 'Transport=1,QosProfiles=1,DscpPcpMap=1'}})
        tmp_dict['Transport']['Router'].append({'routerId': node_data['lte'], 'InterfaceIPv4': {
            'interfaceIPv4Id': node_data['lte_interface'], 'egressQosMarking': 'Transport=1,QosProfiles=1,DscpPcpMap=1'}})
        # NR Internal Router and sctp mos
        if len(self.gnbdata) > 0:
            tmp_str = F'Transport=1,Router={self.gnbdata["lte"]},InterfaceIPv4={self.gnbdata["lte_interface"]},AddressIPv4=1'
            tmp_dict['Transport']['SctpProfile'].append(self.get_mo_dict_from_site_or_db(moc='SctpProfile', mo_id='Node_Internal_F1'))
            tmp_dict['Transport']['Router'].append({
                'routerId': 'Node_Internal_F1',
                'InterfaceIPv4': [
                    {'interfaceIPv4Id': 'NRCUCP', 'loopback': 'true', 'AddressIPv4': {'addressIPv4Id': '1', 'address': '169.254.42.42/32'}},
                    {'interfaceIPv4Id': 'NRDU', 'loopback': 'true', 'AddressIPv4': {'addressIPv4Id': '1', 'address': '169.254.42.43/32'}},]
            })
            tmp_dict['Transport']['SctpEndpoint'].extend([
                self.get_mo_dict_from_site_or_db(moc='SctpEndpoint', mo_id='F1_NRCUCP'),  # F1_NRCUCP
                self.get_mo_dict_from_site_or_db(moc='SctpEndpoint', mo_id='F1_NRDU'),     # F1_NRDU
                # {'sctpEndpointId': 'F1_NRCUCP', 'portNumber': '38472', 'sctpProfile': 'Transport=1,SctpProfile=Node_Internal_F1',
                #  'localIpAddress': F'Transport=1,Router=Node_Internal_F1,InterfaceIPv4=NRCUCP,AddressIPv4=1'},  # F1_NRCUCP
                # {'sctpEndpointId': 'F1_NRDU', 'portNumber': '38472', 'sctpProfile': 'Transport=1,SctpProfile=Node_Internal_F1',
                #  'localIpAddress': F'Transport=1,Router=Node_Internal_F1,InterfaceIPv4=NRDU,AddressIPv4=1'},  # F1_NRDU
                {'sctpEndpointId': 'NR_N2', 'portNumber': '38412', 'sctpProfile': 'Transport=1,SctpProfile=1', 'localIpAddress': tmp_str},  # NR_N2
                {'sctpEndpointId': 'NR_X2', 'portNumber': '36422', 'sctpProfile': 'Transport=1,SctpProfile=1', 'localIpAddress': tmp_str}, # NR_X2
                {'sctpEndpointId': 'NR_Xn', 'portNumber': '38422', 'sctpProfile': 'Transport=1,SctpProfile=1', 'localIpAddress': tmp_str},  # NR_Xn
            ])
        if len(self.enbdata) > 0:
            # tmp_dict['Transport']['SctpEndpoint'].extend([self.get_mo_dict_from_site_or_db(moc='SctpEndpoint', mo_id='LTE')])
            tmp_str = F'Transport=1,Router={self.enbdata["lte"]},InterfaceIPv4={self.enbdata["lte_interface"]},AddressIPv4=1'
            lte_sctp_end = self.get_mo_dict_from_site_or_db(moc='SctpEndpoint', mo_id='LTE')
            lte_sctp_end |= {'localIpAddress': tmp_str, 'sctpProfile': 'Transport=1,SctpProfile=1'}
            tmp_dict['Transport']['SctpEndpoint'].append(copy.deepcopy(lte_sctp_end))
        if node_data.get('MMBB'):
            if self.enbdata['lte_plength'] != '32' and self.gnbdata['lte_plength'] != '32':
                # LTE on Bridge Configuration
                tmp_dict['Transport']['Router'].append({
                    'routerId': self.enbdata['lte'],
                    'InterfaceIPv4': {
                        'interfaceIPv4Id': self.enbdata['lte_interface'], 'routesHoldDownTimer': '180',
                        'encapsulation': F'ManagedElement=1,Transport=1,Bridge=1', 'egressQosMarking': 'Transport=1,QosProfiles=1,DscpPcpMap=1',
                        'AddressIPv4': {'addressIPv4Id': '1', 'address': F'{self.enbdata["lte_ip"]}/{self.enbdata["lte_plength"]}'}
                    },
                    'RouteTableIPv4Static': {'routeTableIPv4StaticId': '1', 'Dst': {
                        'dstId': '1', 'dst': '0.0.0.0/0', 'NextHop': {
                            'nextHopId': '1', 'adminDistance': '10', 'address': self.enbdata['lte_gway']}}}
                })
            elif self.enbdata['lte_plength'] != '32' and self.gnbdata['lte_plength'] == '32':
                # NR on same vlan and loopback Configuration
                tmp_dict['Transport']['Router'].append({
                    'routerId': self.gnbdata['lte'],
                    'InterfaceIPv4': {
                        'interfaceIPv4Id': self.gnbdata['lte_interface'], 'loopback': 'true',
                        'egressQosMarking': 'Transport=1,QosProfiles=1,DscpPcpMap=1',
                        'AddressIPv4': {'addressIPv4Id': '1',
                                        'address': F'{self.gnbdata["lte_ip"]}/{self.gnbdata["lte_plength"]}'}
                    }
                })
            elif self.enbdata['lte_plength'] == '32' and self.gnbdata['lte_plength'] != '32':
                # LTE on same vlan and loopback Configuration
                tmp_dict['Transport']['Router'].append({
                    'routerId': self.enbdata['lte'],
                    'InterfaceIPv4': {
                        'interfaceIPv4Id': self.enbdata['lte_interface'], 'loopback': 'true',
                        'egressQosMarking': 'Transport=1,QosProfiles=1,DscpPcpMap=1',
                        'AddressIPv4': {'addressIPv4Id': '1',
                                        'address': F'{self.enbdata["lte_ip"]}/{self.enbdata["lte_plength"]}'}
                    }
                })
        doc, config = self.main_rcp_msg_start(msg_id='transport')
        config.appendChild(self.mo_add_form_dict_xml(tmp_dict, 'ManagedElement'))
        for aa in doc.getElementsByTagName('loopback'): aa.firstChild.nodeValue = ''
        return doc

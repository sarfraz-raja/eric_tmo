from xml.dom.minidom import Document
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C02_SiteBasic(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        if self.enbdata.get('BBChange') is False or self.gnbdata.get('BBChange') is False: return
        node_data = self.gnbdata if (self.enbdata.get('MMBB') and self.gnbdata['lte_plength'] != '32') or len(self.enbdata) == 0 else self.enbdata
        self.usid.script_dict["SB"] = F'SiteBasic_{self.node}.xml'
        self.relative_path = ['01_AP', self.node, self.node, self.usid.script_dict["SB"]]
        self.script_list = [self.site_basic_msg1(node_data=node_data), self.site_basic_msg2(node_data=node_data),
                                self.site_basic_msg3(node_data=node_data), self.site_basic_msg4(node_data=node_data)]

    def site_basic_msg1(self, *, node_data: dict) -> Document:
        doc, config = self.main_rcp_msg_start(msg_id='1')
        config.appendChild(self.mo_add_form_dict_xml(para_dict={
            'managedElementId': '1', 'dnPrefix': node_data.get('dnPrefix'), 'SystemFunctions': {
                'systemFunctionsId': '1', 'Lm': {'lmId': '1', 'fingerprint': node_data.get("fingerprint")}}},
            moname='ManagedElement', change_me=False))
        return doc

    def site_basic_msg2(self, *, node_data: dict) -> Document:
        tmp_dict = {'managedElementId': '1', 'SystemFunctions': {'systemFunctionsId': '1', 'Lm': {'lmId': '1', 'FeatureState': []}}}
        if len([_ for _ in ['5216', '6630'] if _ in node_data['BBType']]) > 0:
            tmp_dict['SystemFunctions']['Lm']['FeatureState'].extend([
                # {'featureStateId': 'CXC4011823', 'featureState': '1 (ACTIVATED)'}, Moved to BL
                {'featureStateId': 'CXC4011838', 'featureState': '1 (ACTIVATED)'},
            ])
        else: del tmp_dict['SystemFunctions']['Lm']['FeatureState']
        doc, config = self.main_rcp_msg_start(msg_id='2')
        config.appendChild(self.mo_add_form_dict_xml(para_dict=tmp_dict, moname='ManagedElement', change_me=False))
        return doc

    def site_basic_msg3(self, node_data: dict) -> Document:
        tmp_dict = {
            'managedElementId': '1',
            'SystemFunctions': {
                'systemFunctionsId': '1',
                'SecM': {
                    'secMId': '1',
                    'UserManagement': {
                        'userManagementId': '1',
                        'UserIdentity': {
                            'userIdentityId': '1',
                            'MaintenanceUser': {
                                'maintenanceUserId': '1',
                                'userName': node_data['username'],
                                'password': {'cleartext': 'true', 'password': node_data['password']}
                            }
                        }
                    }
                },
                'SysM': {
                    'sysMId': '1',
                    'CliTls': {'cliTlsId': '1', 'administrativeState': '1 (UNLOCKED)',
                               'trustCategory': 'ManagedElement=1,SystemFunctions=1,SecM=1,CertM=1,TrustCategory=oamTrustCategory',
                               'nodeCredential': 'ManagedElement=1,SystemFunctions=1,SecM=1,CertM=1,NodeCredential=oamNodeCredential'},
                    'HttpM': {'httpMId': '1',
                              'Https': {'httpsId': '1',
                                        'nodeCredential': 'ManagedElement=1,SystemFunctions=1,SecM=1,CertM=1,NodeCredential=oamNodeCredential',
                                        'trustCategory': 'ManagedElement=1,SystemFunctions=1,SecM=1,CertM=1,TrustCategory=oamTrustCategory'}},
                    'OamAccessPoint': {
                        'oamAccessPointId': '1',
                        'accessPoint': F'ManagedElement=1,Transport=1,Router={node_data["oam"]},InterfaceIPv4=1,AddressIPv4=1'},
                    'OamTrafficClass': {'oamTrafficClassId': '1', 'dscp': '8'},
                    'TimeM': {'timeMId': '1',
                              'DateAndTime': {'dateAndTimeId': '1', 'timeZone': node_data["timeZone"]},
                              'Ntp': {'ntpId': '1', 'NtpServer': []}},
                }
            },
            'Equipment': {
                'equipmentId': '1',
                'FieldReplaceableUnit': {'fieldReplaceableUnitId': node_data['BBId'], 'TnPort': {'tnPortId': node_data['TnPort']}}
            },
            'Transport': {
                'transportId': '1',
                'EthernetPort': {
                    'ethernetPortId': node_data['TnPort'],
                    'administrativeState': '1 (UNLOCKED)',
                    'admOperatingMode': node_data['admOperatingMode'],
                    'autoNegEnable': 'false',
                    'encapsulation': F'ManagedElement=1,Equipment=1,FieldReplaceableUnit={node_data["BBId"]},TnPort={node_data["TnPort"]}',
                    'userLabel': node_data['TnPort']
                },
                'VlanPort': [
                    {'vlanPortId': node_data['oam_van'], 'vlanId': node_data['oam_van'],
                     'encapsulation': F'ManagedElement=1,Transport=1,EthernetPort={node_data["TnPort"]}'},
                    {'vlanPortId': node_data['lte_vlan'], 'vlanId': node_data['lte_vlan'],
                     'encapsulation': F'ManagedElement=1,Transport=1,EthernetPort={node_data["TnPort"]}'}
                ],
                'Router': [
                    {
                        'routerId': node_data['oam'],
                        'InterfaceIPv4': {
                            'interfaceIPv4Id': '1', 'routesHoldDownTimer': '180',
                            'encapsulation': F'ManagedElement=1,Transport=1,VlanPort={node_data["oam_van"]}',
                            'AddressIPv4': {'addressIPv4Id': '1', 'address': F'{node_data["oam_ip"]}/{node_data["oam_plength"]}'}},
                        'RouteTableIPv4Static': {
                            'routeTableIPv4StaticId': '1',
                            'Dst': {'dstId': '1', 'dst': '0.0.0.0/0',
                                    'NextHop': {'nextHopId': '1', 'adminDistance': '10', 'address': node_data["oam_gway"]}}
                        }
                    },
                    {
                        'routerId': node_data['lte'],
                        'InterfaceIPv4': {
                            'interfaceIPv4Id': node_data['lte_interface'], 'routesHoldDownTimer': '180',
                            'encapsulation': F'ManagedElement=1,Transport=1,VlanPort={node_data["lte_vlan"]}',
                            'AddressIPv4': {'addressIPv4Id': '1', 'address': F'{node_data.get("lte_ip", "")}/{node_data["lte_plength"]}'}},
                        'RouteTableIPv4Static': {
                            'routeTableIPv4StaticId': '1',
                            'Dst': {'dstId': '1', 'dst': '0.0.0.0/0',
                                    'NextHop': {'nextHopId': '1', 'adminDistance': '10', 'address': node_data['lte_gway']}}
                        }
                    }
                ],
            }
        }
        # Special Configurations for NtpServer for 'TOSB' Sites
        if node_data.get(F'transaction', '').upper() == 'TOSB':
            for i in [1, 2]:
                if node_data.get(F'freqsync{i}', '') == '': continue
                tmp_dict['SystemFunctions']['SysM']['TimeM']['Ntp']['NtpServer'].append(
                    {'userLabel': F"NTP{i}", 'ntpServerId': F"{i}",
                     'serverAddress': node_data.get(F"freqsync{i}", ""), 'administrativeState': '1 (UNLOCKED)'})
        else:
            for i in [1, 2, 3, 4]:
                if node_data.get(F'ntpip{i}', '') == '': continue
                tmp_dict['SystemFunctions']['SysM']['TimeM']['Ntp']['NtpServer'].append(
                    {'userLabel': F"NTP{i}", 'ntpServerId': F"{i}",
                     'serverAddress': node_data.get(F"ntpip{i}", ""), 'administrativeState': '1 (UNLOCKED)'})
        # VLAN and Router Configurations for MMBB with Bridge
        if node_data['MMBB'] and self.enbdata.get('lte_plength', "") != '32' and self.gnbdata.get('lte_plength', "") != '32':
            # Adding LTE VLAN and Bridge MOs for LTE; Router Configurations will be added in TN Scripts
            tmp_dict['Transport']['VlanPort'].append({
                'vlanPortId': self.enbdata['lte_vlan'], 'vlanId': self.enbdata['lte_vlan'],
                'encapsulation': F'ManagedElement=1,Transport=1,EthernetPort={self.enbdata["TnPort"]}'})
            tmp_dict['Transport']['Bridge'] = {'bridgeId': '1', 'port': F'ManagedElement=1,Transport=1,VlanPort={self.enbdata["lte_vlan"]}'}

        doc, config = self.main_rcp_msg_start(msg_id='3')
        config.appendChild(self.mo_add_form_dict_xml(tmp_dict, 'ManagedElement', change_me=False))
        for aa in doc.getElementsByTagName("cleartext"): aa.firstChild.nodeValue = ''
        for aa in doc.getElementsByTagName("loopback"): aa.firstChild.nodeValue = ''
        return doc

    def site_basic_msg4(self, *, node_data: dict) -> Document:
        doc, config = self.main_rcp_msg_start(msg_id='4')
        config.appendChild(self.mo_add_form_dict_xml(para_dict={'managedElementId': 1, 'networkManagedElementId': node_data.get("postsite")},
                                                     moname='ManagedElement', change_me=False))
        return doc

    def write_script_file(self):
        if len(self.script_list) > 0:
            self.cr_file_path()
            with open(self.script_file, 'w') as f:
                for index, elem in enumerate(self.script_list):
                    f.write(
                        self.ap_rcp_msg_cap().toprettyxml(encoding='UTF-8', indent='  ').decode('utf-8').strip() + '\n]]>]]>\n' +
                        elem.toprettyxml(encoding='UTF-8', indent='  ').decode('utf-8').replace(
                            '<?xml version="1.0" encoding="UTF-8"?>', '').strip() + '\n]]>]]>\n' +
                        self.rcp_msg_close().toprettyxml(encoding='UTF-8', indent='  ').decode('utf-8').replace(
                            '<?xml version="1.0" encoding="UTF-8"?>', '').strip() + '\n]]>]]>\n'
                    )

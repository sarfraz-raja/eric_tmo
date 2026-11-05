from xml.dom.minidom import Document
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C03_SiteEquipment(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        if self.enbdata.get('BBChange') is False or self.gnbdata.get('BBChange') is False: return
        node_data = self.gnbdata if (self.enbdata.get('MMBB') and self.gnbdata['lte_plength'] != '32') or len(self.enbdata) == 0 else self.enbdata
        self.usid.script_dict["SE"] = F'SiteEquipment_{self.node}.xml'
        self.relative_path = ['01_AP', self.node, self.node, self.usid.script_dict["SE"]]
        self.script_list = [self.ap_rcp_msg_cap(), self.create_rpc_msg(node_data=node_data), self.rcp_msg_close()]

    def create_rpc_msg(self, *, node_data: dict) -> Document:
        doc, config = self.main_rcp_msg_start(msg_id='1')
        tmp_dict = {
            'managedElementId': '1',
            'userLabel': self.node,
            'Equipment': {
                'equipmentId': '1',
                'Cabinet': {'cabinetId': '1', 'smokeDetector': 'false', 'climateSystem': 'STANDARD'},
                'EcBus': {'ecBusId': '1', 'ecBusConnectorRef': F'ManagedElement=1,Equipment=1,FieldReplaceableUnit={node_data["BBId"]}',
                          'equipmentSupportFunctionRef': 'ManagedElement=1,EquipmentSupportFunction=1'},
                'FieldReplaceableUnit': {
                    'fieldReplaceableUnitId': node_data['BBId'], 'administrativeState': 'UNLOCKED',
                    'SyncPort': {'syncPortId': '1'},
                    'EcPort': {'ecPortId': '1', 'ecBusRef': 'ManagedElement=1,Equipment=1,EcBus=1', 'hubPosition': 'A'},
                    'RiPort': [{'riPortId': _, 'administrativeState': 'UNLOCKED'} for _ in node_data['RiPort']],
                    'AlarmPort': []
                },
            },
            'EquipmentSupportFunction': {
                'equipmentSupportFunctionId': '1', 'supportSystemControl': 'true',
                'BatteryBackup': {'batteryBackupId': '1', 'controlDomainRef': F'ManagedElement=1,Equipment=1,Cabinet=1'},
                'Climate': {'climateId': '1', 'climateControlMode': 'NORMAL', 'controlDomainRef': F'ManagedElement=1,Equipment=1,Cabinet=1'},
                'PowerDistribution': {'powerDistributionId': '1', 'controlDomainRef': F'ManagedElement=1,Equipment=1,Cabinet=1'},
                'PowerSupply': {'powerSupplyId': '1', 'controlDomainRef': F'ManagedElement=1,Equipment=1,Cabinet=1'},
            },
            'NodeSupport': {
                'nodeSupportId': '1',
                'MpClusterHandling': {'mpClusterHandlingId': '1',
                                      'primaryCoreRef': F'ManagedElement=1,Equipment=1,FieldReplaceableUnit={node_data["BBId"]}'},
                'CpriLinkSupervision': {'cpriLinkSupervisionId': '1', 'cpriLinkFilterTime': '400'},
                'TimeSettings': {
                    'timeSettingsId': '1', 'timeOffset': node_data['timeOffset'], 'daylightSavingTimeOffset': '1:00',
                    'daylightSavingTimeEndDate': {'dayRule': 'Sun>=1', 'month': '11 (NOVEMBER)', 'time': '02:00'},
                    'daylightSavingTimeStartDate': {'dayRule': 'Sun>=8', 'month': '3 (MARCH)', 'time': '02:00'},
                },
                # 'EquipmentDiscovery': {'equipmentDiscoveryId': '1', 'antennaDeviceScanInBackground': 'false',
                #                        'portVoltage': 'DC_12V', 'portConfiguration': 'SCAN_ALL_PORTS_WITH_CHOSEN_VOLTAGE'},
            }
        }
        if str(node_data['BBType']) in ['6648', '6651']:
            del tmp_dict['Equipment']['FieldReplaceableUnit']['EcPort']
        me_mo = self.mo_add_form_dict_xml(tmp_dict, 'ManagedElement', change_me=False)
        config.appendChild(me_mo)
        # SUP - Start
        if str(node_data['BBType']) in '5216':
            tmp_dict = {'fieldReplaceableUnitId': 'SUP-1', 'administrativeState': 'UNLOCKED',
                        'positionRef': F'ManagedElement=1,Equipment=1,Cabinet=1',
                        'AlarmPort': [{'alarmPortId': str(i), 'administrativeState': 'UNLOCKED'} for i in range(1, 17)],
                        'EcPort': {'ecPortId': '1', 'ecBusRef': F'ManagedElement=1,Equipment=1,EcBus=1', 'hubPosition': 'NA'}}
            sup_mo = self.mo_add_form_dict_xml(tmp_dict, 'FieldReplaceableUnit', change_me=False)
            mc = doc.getElementsByTagName("Equipment")[0]
            mc.appendChild(sup_mo)
        #  SAU - Start
        tmp_dict = {'fieldReplaceableUnitId': self.site.get_sau_id() if self.site else 'SAU-1', 'administrativeState': 'UNLOCKED',
                    'positionRef': F'ManagedElement=1,Equipment=1,Cabinet=1',
                    'EcPort': {'ecPortId': '1', 'ecBusRef': F'ManagedElement=1,Equipment=1,EcBus=1', 'hubPosition': 'SAU'}}
        if self.site:
            site = self.usid.sites.get(F'site_{self.node}')
            mo = site.find_mo_ending_with_id('FieldReplaceableUnit', self.site.get_sau_id())
            if len(mo) > 0:
                sau_mo = self.mo_add_form_dict_xml(tmp_dict, 'FieldReplaceableUnit', change_me=False)
                self.append_equipment_elems(site, sau_mo, mo[0], moc='AlarmPort')
                mc = doc.getElementsByTagName("Equipment")[0]
                mc.appendChild(sau_mo)
        return doc

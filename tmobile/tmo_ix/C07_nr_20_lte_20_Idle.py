from xml.dom.minidom import Document
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C07_nr_20_lte_20_Idle(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        if (not self.enbdata.get('IDLE')) and (not self.gnbdata.get('IDLE')): return
        self.reconfig_ap_file_path_to_remote()
        idle_msg = self.create_rpc_msg()
        if idle_msg is not None: self.script_list = [self.ap_rcp_msg_cap(), idle_msg, self.rcp_msg_close()]

    def create_rpc_msg(self) -> Document or None:
        lte_eran, lte_vlan, lte_vlanid = 'Transport=1,EthernetPort=ERAN', 'Transport=1,VlanPort=ERAN', '4050'
        nr_eran, nr_vlan, nr_vlanid = 'Transport=1,EthernetPort=ERAN', 'Transport=1,VlanPort=ERAN_NR', '4060'
        tmp_dict = {
            'managedElementId': self.node,
            'Equipment': {'equipmentId': '1', 'FieldReplaceableUnit': {
                'fieldReplaceableUnitId': self.enbdata.get('BBId', self.gnbdata.get('BBId')), 'TnPort': []}},
            'Transport': {'transportId': '1', 'EthernetPort': [], 'VlanPort': []},
            'ENodeBFunction': {'eNodeBFunctionId': '1'},
            'GNBDUFunction': {'gNBDUFunctionId': '1'},
            'SystemFunctions': {'systemFunctionsId': '1', 'Lm': {'lmId': '1', 'FeatureState': []}}
        }
        # LTE {'featureStateId': 'CXC4012034', 'featureState': '1 (ACTIVATED)'}
        # NR [{'featureStateId': 'CXC4012477', 'featureState': '1 (ACTIVATED)'}, {'featureStateId': 'CXC4012478', 'featureState': '1 (ACTIVATED)'}]
        doc = ''
        if self.enbdata.get('BBChange') or self.gnbdata.get('BBChange'):
            # tmp_dict['Equipment'] = {'equipmentId': '1', 'FieldReplaceableUnit': {
            #     'fieldReplaceableUnitId': self.enbdata.get('BBId', self.gnbdata.get('BBId')), 'TnPort': []}}
            # tmp_dict['Transport'] = {'transportId': '1', 'EthernetPort': [], 'VlanPort': []}
            # tmp_dict['SystemFunctions'] = {'systemFunctionsId': '1', 'Lm': {'lmId': '1', 'FeatureState': []}}
            # LTE ERAN
            if self.enbdata.get('IDLE'):
                encapsulation = F'ManagedElement=1,Equipment=1,FieldReplaceableUnit={self.enbdata["BBId"]},TnPort={self.enbdata["IDLE"]}'
                tmp_dict['Equipment']['FieldReplaceableUnit']['TnPort'].append(self.get_mo_dict_from_site_or_db(moc='TnPort', mo_id=self.enbdata['IDLE']))
                tmp_dict['Transport']['EthernetPort'].append(self.get_eth_port_dict(mo_id=lte_eran.split('=')[-1], encapsulation=encapsulation))
                tmp_dict['Transport']['VlanPort'].append({'vlanPortId': lte_vlan.split('=')[-1], 'vlanId': lte_vlanid, 'encapsulation': lte_eran})
                tmp_dict['ENodeBFunction'] = {'eNodeBFunctionId': '1', 'eranVlanPortRef': lte_vlan}
                tmp_dict['SystemFunctions']['Lm']['FeatureState'].append({'featureStateId': 'CXC4012034', 'featureState': '1 (ACTIVATED)'})
            # NR ERAN
            if self.gnbdata.get('IDLE') and self.gnbdata.get('IDLE') != self.enbdata.get('IDLE'):
                encapsulation = F'ManagedElement=1,Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},TnPort={self.gnbdata["IDLE"]}'
                tmp_dict['Equipment']['FieldReplaceableUnit']['TnPort'].append(
                    self.get_mo_dict_from_site_or_db(moc='TnPort', mo_id=self.gnbdata['IDLE']))
                if self.enbdata.get('IDLE'):
                    nr_eran = 'Transport=1,EthernetPort=ERAN_NR'
                tmp_dict['Transport']['EthernetPort'].append(self.get_eth_port_dict(mo_id=nr_eran.split('=')[-1], encapsulation=encapsulation))
                tmp_dict['Transport']['VlanPort'].append({'vlanPortId': nr_vlan.split('=')[-1], 'vlanId': nr_vlanid, 'encapsulation': nr_eran})
            elif self.gnbdata.get('IDLE'):
                tmp_dict['Transport']['VlanPort'].append({'vlanPortId': nr_vlan.split('=')[-1], 'vlanId': nr_vlanid, 'encapsulation': nr_eran})
            if self.gnbdata.get('IDLE'):
                tmp_dict['GNBDUFunction'] |= {'gNBDUFunctionId': '1', 'caVlanPortRef': nr_vlan, 'ExtGNBDUPartnerFunction': []}
                for gnb in self.usid.gnodeb.keys():
                    if gnb == self.node: continue
                    tmp_dict['GNBDUFunction']['ExtGNBDUPartnerFunction'].append({
                        'extGNBDUPartnerFunctionId': self.usid.gnodeb[gnb]['nodeid'], 'caVlanPortRef': nr_vlan,
                        'gNBDUId': '1', 'gNBId': self.usid.gnodeb[gnb]['nodeid'], 'gNBIdLength': self.usid.gnodeb[gnb]['gNBIdLength'],
                    })
                # NR CA Features
                tmp_dict['SystemFunctions']['Lm']['FeatureState'].extend([{'featureStateId': 'CXC4012477', 'featureState': '1 (ACTIVATED)'},
                                                                          {'featureStateId': 'CXC4012478', 'featureState': '1 (ACTIVATED)'}])
        else:
            lte_vlan_mo, nr_vlan_mo = None, None
            for mo in self.site.find_mos_with_end_moc(moc='TnPort'):
                if self.site.get_para_value_for_mo(mo=mo, para='vlanId') == lte_vlanid:
                    lte_vlan_mo = ','.join(mo.split(',')[:-2])
                elif self.site.get_para_value_for_mo(mo=mo, para='vlanId') == nr_vlanid:
                    nr_vlan_mo = ','.join(mo.split(',')[:-2])
            if self.enbdata.get('IDLE'):
                encapsulation = F'ManagedElement=1,Equipment=1,FieldReplaceableUnit={self.enbdata["BBId"]},TnPort={self.enbdata["IDLE"]}'
                if lte_vlan_mo is None:
                    lte_vlan_mo = lte_vlan
                    if self.enbdata.get('IDLE') not in [_.split('=')[-1] for _ in self.site.find_mos_with_end_moc(moc='TnPort')]:
                        tmp_dict['Equipment']['FieldReplaceableUnit']['TnPort'].append(
                            self.get_mo_dict_from_site_or_db(moc='TnPort', mo_id=self.enbdata['IDLE']))
                    if lte_eran.split('=')[-1] not in [_.split('=')[-1] for _ in self.site.find_mos_with_end_moc(moc='EthernetPort')]:
                        tmp_dict['Transport']['EthernetPort'].append(
                            self.get_eth_port_dict(mo_id=lte_eran.split('=')[-1], encapsulation=encapsulation))
                    tmp_dict['Transport']['VlanPort'].append({'vlanPortId': lte_vlan_mo.split('=')[-1], 'vlanId': lte_vlanid, 'encapsulation': lte_eran})
                elif (len(self.site.find_mos_with_end_str(end_str=',ENodeBFunction=1')) == 0 or
                        (len(self.site.find_mos_with_end_str(end_str=',ENodeBFunction=1')) > 0 and lte_vlan_mo not in
                         self.site.get_para_value_for_mo(mo=self.site.find_mos_with_end_str(end_str=',ENodeBFunction=1')[0],
                                                         para='eranVlanPortRef'))):
                    tmp_dict['ENodeBFunction'] = {'eNodeBFunctionId': '1', 'eranVlanPortRef': lte_vlan_mo}
                if self.site.get_para_value_for_mo(mo=self.site.find_mos_with_end_str(
                        end_str=',Lm=1,FeatureState=CXC4012034')[0], para='featureState') != '1 (ACTIVATED)':
                    tmp_dict['SystemFunctions']['Lm']['FeatureState'].append({'featureStateId': 'CXC4012034', 'featureState': '1 (ACTIVATED)'})

            if self.gnbdata.get('IDLE') and self.gnbdata.get('IDLE') != self.enbdata.get('IDLE'):
                if nr_vlan_mo is None:
                    nr_vlan_mo = nr_vlan
                    if self.gnbdata.get('IDLE') not in [_.split('=')[-1] for _ in self.site.find_mos_with_end_moc(moc='TnPort')]:
                        tmp_dict['Equipment']['FieldReplaceableUnit']['TnPort'].append(
                            self.get_mo_dict_from_site_or_db(moc='TnPort', mo_id=self.gnbdata['IDLE']))
                    if self.enbdata.get('IDLE'): nr_eran = 'Transport=1,EthernetPort=ERAN_NR'
                    encapsulation = F'ManagedElement=1,Equipment=1,FieldReplaceableUnit={self.gnbdata["BBId"]},TnPort={self.gnbdata["IDLE"]}'
                    if nr_eran.split('=')[-1] not in [_.split('=')[-1] for _ in self.site.find_mos_with_end_moc(moc='EthernetPort')]:
                        tmp_dict['Transport']['EthernetPort'].append(self.get_eth_port_dict(mo_id=nr_eran.split('=')[-1], encapsulation=encapsulation))
                    tmp_dict['Transport']['VlanPort'].append({'vlanPortId': nr_vlan_mo.split('=')[-1], 'vlanId': nr_vlanid, 'encapsulation': nr_eran})
            elif self.gnbdata.get('IDLE') and nr_vlan_mo is None:
                nr_vlan_mo = nr_vlan
                tmp_dict['Transport']['VlanPort'].append({'vlanPortId': nr_vlan_mo.split('=')[-1], 'vlanId': nr_vlanid, 'encapsulation': nr_eran})
            if self.gnbdata.get('IDLE'):
                tmp_dict['GNBDUFunction'] = {'gNBDUFunctionId': '1', 'ExtGNBDUPartnerFunction': []}
                if (len(self.site.find_mos_with_end_str(end_str=',GNBDUFunction=1')) == 0 or
                        (len(self.site.find_mos_with_end_str(end_str=',GNBDUFunction=1')) > 0 or nr_vlan_mo not in
                         self.site.get_para_value_for_mo(mo=self.site.find_mos_with_end_str(end_str=',GNBDUFunction=1')[0], para='caVlanPortRef'))):
                    tmp_dict['GNBDUFunction'] |= {'caVlanPortRef': nr_vlan_mo}
                for gnb in self.usid.gnodeb.keys():
                    if gnb == self.node: continue
                    add_flag = True
                    if len(self.site.find_mos_with_end_moc(moc='ExtGNBDUPartnerFunction')) > 0:
                        for mo in self.site.find_mos_with_end_moc(moc='ExtGNBDUPartnerFunction'):
                            if self.site.get_para_value_for_mo(mo=mo, para='gNBId') == self.usid.gnodeb[gnb]['nodeid']: add_flag = False
                    if add_flag:
                        tmp_dict['GNBDUFunction']['ExtGNBDUPartnerFunction'].append({
                            'extGNBDUPartnerFunctionId': self.usid.gnodeb[gnb]['nodeid'], 'caVlanPortRef': nr_vlan_mo,
                            'gNBDUId': '1', 'gNBId': self.usid.gnodeb[gnb]['nodeid'], 'gNBIdLength': self.usid.gnodeb[gnb]['gNBIdLength'],
                        })
                if self.site.get_para_value_for_mo(mo=self.site.find_mos_with_end_str(end_str=',Lm=1,FeatureState=CXC4012477')[0],
                                                   para='featureState') != '1 (ACTIVATED)':
                    tmp_dict['SystemFunctions']['Lm']['FeatureState'].append({'featureStateId': 'CXC4012477', 'featureState': '1 (ACTIVATED)'})
                if self.site.get_para_value_for_mo(mo=self.site.find_mos_with_end_str(end_str=',Lm=1,FeatureState=CXC4012478')[0],
                                                   para='featureState') != '1 (ACTIVATED)':
                    tmp_dict['SystemFunctions']['Lm']['FeatureState'].append({'featureStateId': 'CXC4012478', 'featureState': '1 (ACTIVATED)'})

        # Remove unused MOCs
        if len(tmp_dict['SystemFunctions']['Lm']['FeatureState']) == 0: del tmp_dict['SystemFunctions']['Lm']['FeatureState']
        if len(tmp_dict['Equipment']['FieldReplaceableUnit']['TnPort']) == 0: del tmp_dict['Equipment']
        if len(tmp_dict['Transport']['EthernetPort']) == 0: del tmp_dict['Transport']['EthernetPort']
        if len(tmp_dict['Transport']['VlanPort']) == 0: del tmp_dict['Transport']['VlanPort']
        if len(tmp_dict['Transport']) == 1: del tmp_dict['Transport']
        if len(tmp_dict['ENodeBFunction']) == 1: del tmp_dict['ENodeBFunction']
        if 'ExtGNBDUPartnerFunction' in tmp_dict['GNBDUFunction'].keys() and len(tmp_dict['GNBDUFunction']['ExtGNBDUPartnerFunction']) == 0:
            del tmp_dict['GNBDUFunction']['ExtGNBDUPartnerFunction']
        if len(tmp_dict['GNBDUFunction']) == 1: del tmp_dict['GNBDUFunction']

        doc = None
        if len(tmp_dict) > 1:
            doc, config = self.main_rcp_msg_start(msg_id='1')
            me_mo = self.mo_add_form_dict_xml(tmp_dict, 'ManagedElement', change_me=False)
            config.appendChild(me_mo)
        return doc

    @staticmethod
    def get_eth_port_dict(*, mo_id: str, encapsulation: str) -> dict:
        return {'ethernetPortId': mo_id, 'administrativeState': '1 (UNLOCKED)', 'admOperatingMode': '9 (10G_FULL)',
                'autoNegEnable': 'false', 'encapsulation': encapsulation, 'userLabel': F'{encapsulation.split("=")[-1]}_port'}

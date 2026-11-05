from .BaseScript import BaseScript
import copy

enb_dict = {
    'ENB': {
        'fieldnames': {
            'NE ID': None, 'NE Type': None, 'NE Version': None, 'Release Version': None, 'Network': None,
            'NE Name': None, 'Local Time Offset': None, 'EAIU': None, 'FW Auto Fusing': None, 'Site ID': None
        }
    },
    'SERVER_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'CFM': None, 'PSM': None,
        }
    },
    'PLMN_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'PLMN Index': None, 'MCC': None, 'MNC': None,
        }
    },
    'SON_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Initial PCI': 'off', 'Initial RSI': 'off', 'Initial Intra-LTE NRT': 'off', 'Initial Inter-RAT NRT NR': 'off',
        }
    },
    'SYSTEM_SHARING_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'RU Sharing Flag': 'on', 'RU Primary Flag': 'on', 'DU Primary Flag': 'off',
        }
    },
    'INTER_CONNECTION_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Inter Connection Group ID': None, 'Inter Connection Switch': 'inter-connection-off', 'Inter Connection Node ID': '2',
        }
    },
    'INTER_ENB_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Inter Node ID': None, 'Admin State': None, 'Clock Share Flag': None,
        }
    },
    'MAIN_BOARD_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Unit Type': 'ump', 'Unit ID': '0', 'Board Type': None,
        }
    },
    'MAIN_BOARD_HSI_ETHERNET_PORT_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Unit Type': 'ump', 'Unit ID': '0', 'Module ID': '0',
        }
    },
    'CLOCK_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Clock Source ID': None, 'Clock Source': None, 'Priority Level': None, 'Quality Level': 'prc',
        }
    },
    'PTP_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'IP Version': None, 'First Master IP': None, 'Second Master IP': None, 'Clock Profile': None, 'PTP Domain': None
        }
    },
    'EXTERNAL_LINK_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Unit Type': None, 'Unit ID': None, 'Port ID': None, 'VR ID': None, 'Admin State': 'unlocked',
            'Connect Type': 'backhaul', 'UDE Type': 'ude-none', 'Speed Duplex': 's10g-full', 'Fec Mode': 'off', 'MTU': '1500',
        }
    },
    'SYSTEM_LOCATION_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'User Defined Mode': None, 'Latitude': None, 'Longitude': None, 'Height': None,
        }
    },
    'MME_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Index': None, 'IP Type': None, 'IP': None, 'Service Purpose': None, 'Attach Without PDN Connectivity': None,
            'CP Optimization': None, 'UP Optimization': None, 'MCC': None, 'MNC': None,
        }
    },
    'EXTERNAL_INTERFACE_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'IF Name': None, 'IP': None, 'Prefix Length': None, 'IP Get Type': None, 'Management': None,
            'Signal S1': None, 'Signal X2': None, 'Bearer S1': None, 'Bearer X2': None, 'IEEE1588': None, 'Smart scheduler': None,
        }
    },
    'STATIC_ROUTE_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'VR ID': None, 'IP Type': None, 'IP Prefix': None, 'IP GW': None, 'Route Interface Name': None
        }
    },
    'VIRTUAL_ROUTING_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'VR ID': None,
        }
    },
    'VLAN_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'VLAN ID': None, 'VR ID': None, 'VLAN Interface Name': None,
        }
    },
    'LAG_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'LAG ID': None, 'VR ID': None, 'LAG Interface Name': None,
        }
    },
    'LOOPBACK_IP_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Interface ID': None, 'VR ID': None, 'IP Address': None, 'Signal S1': None,
            'Signal X2': None,  'Bearer S1': None, 'Bearer ' 'X2': None,
        }
    },
}


class A_02_ENB_NE_Grow(BaseScript):
    def create_msg(self):
        if self.site_dict['enbid']:
            enbid = self.site_dict['enbid']
            csv = copy.deepcopy(enb_dict)

            # ENB
            para = 'ENB'
            csv[para][F'{enbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}'] |= {
                'NE ID': enbid, 'NE Type': self.site_dict['site_type'],
                'NE Version': self.usid.sw.ne_version, 'Release Version': self.usid.sw.release_version, 'Network': 'VZ',
                'NE Name': self.site_dict['node'], 'Local Time Offset': '0', 'EAIU': 'not-equip', 'FW Auto Fusing': 'off', 'Site ID': ''
            }

            # SERVER_INFORMATION
            # para = 'SERVER_INFORMATION'
            # csv[para][F'{enbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            # csv[para][F'{enbid}'] |= {'NE ID': None, 'CFM': None, 'PSM': None}

            # PLMN_INFORMATION ---> Constant Value for VZ
            para = 'PLMN_INFORMATION'
            csv[para][F'{enbid}_0'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_0'] |= {'NE ID': enbid, 'PLMN Index': '0', 'MCC': self.site_dict['plmn']['mcc'],
                                        'MNC': self.site_dict['plmn']['mnc']}

            # SON_INFORMATION
            para = 'SON_INFORMATION'
            csv[para][F'{enbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}'] |= {'NE ID': enbid, 'Inter Connection Node ID': self.site_dict['inter_connection_node_id']}

            for para in ['SON_INFORMATION', 'SYSTEM_SHARING_INFORMATION', 'MAIN_BOARD_HSI_ETHERNET_PORT_INFORMATION']:
                if {'NE ID'}.issubset(set(csv[para]['fieldnames'].keys())):
                    csv[para][F'{enbid}'] = copy.deepcopy(csv[para]['fieldnames'])
                    csv[para][F'{enbid}'] |= {'NE ID': enbid}
                else:
                    self.usid.log(F'{self.node} ---> {para} ---> Intput Error!!!')




            # INTER_CONNECTION_INFORMATION
            para = 'INTER_CONNECTION_INFORMATION'
            csv[para][F'{enbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}'] |= {'NE ID': enbid, 'Inter Connection Node ID': self.site_dict['inter_connection_node_id']}

            # MAIN_BOARD_INFORMATION
            para = 'MAIN_BOARD_INFORMATION'
            csv[para][F'{enbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}'] |= {'NE ID': enbid, 'Board Type': self.site_dict['controller_type']}

            # CLOCK_INFORMATION ---> Constant Value for VZ
            para = 'CLOCK_INFORMATION'
            csv[para][F'{enbid}_0'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_0'] |= {'NE ID': enbid, 'Clock Source ID': '0', 'Clock Source': 'gps-type', 'Priority Level': '1'}

            # PTP_INFORMATION
            if self.site_dict['ptp_1']:
                para = 'CLOCK_INFORMATION'
                csv[para][F'{enbid}_1'] = copy.deepcopy(csv[para]['fieldnames'])
                csv[para][F'{enbid}_1'] |= {'NE ID': enbid, 'Clock Source ID': '1', 'Clock Source': 'ieee1588-phasetype', 'Priority Level': '2'}
                para = 'PTP_INFORMATION'
                csv[para][F'{enbid}_0'] = copy.deepcopy(csv[para]['fieldnames'])
                csv[para][F'{enbid}_0'] |= {'NE ID': enbid, 'IP Version': self.site_dict['ptp_ver'], 'First Master IP': self.site_dict['ptp_1'],
                                            'Second Master IP': self.site_dict['ptp_2'], 'Clock Profile': 'telecom-2008', 'PTP Domain': '0'}

            # EXTERNAL_LINK_INFORMATION
            para = 'EXTERNAL_LINK_INFORMATION'
            csv[para][F'{enbid}_0_0_0'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_0_0_0'] |= {'NE ID': enbid, 'Unit Type': 'ump', 'Unit ID': '0', 'Port ID': '0', 'VR ID': '0'}
            csv[para][F'{enbid}_0_1_0'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_0_1_0'] |= {'NE ID': enbid, 'Unit Type': 'ump', 'Unit ID': '0', 'Port ID': '1', 'VR ID': '0'}

            # SYSTEM_LOCATION_INFORMATION
            para = 'SYSTEM_LOCATION_INFORMATION'
            csv[para][F'{enbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}'] |= {'NE ID': enbid, 'User Defined Mode': 'false', 'Latitude': self.site_dict['latitude'],
                                      'Longitude': self.site_dict['longitude'], 'Height': self.site_dict['height']}

            # MME_INFORMATION
            para = 'MME_INFORMATION'
            csv[para][F'{enbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}'] |= {'NE ID': enbid, 'Index': None, 'IP Type': None, 'IP': None, 'Service Purpose': 'lte-emtc-nbiot',
                                      'Attach Without PDN Connectivity': 'true', 'CP Optimization': 'true', 'UP Optimization': 'true',
                                      'MCC': self.site_dict['plmn']['mcc'], 'MNC': self.site_dict['plmn']['mcc']}

            # EXTERNAL_INTERFACE_INFORMATION
            para = 'EXTERNAL_INTERFACE_INFORMATION'
            csv[para][F'{enbid}_oam'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_oam'] |= {'NE ID': enbid, 'IF Name': F'xe_0_0_0.{self.site_dict["oam_vlan"]}',
                                          'IP': self.site_dict["oam_ip"], 'Prefix Length': self.site_dict["oam_prefix"],
                                          'IP Get Type': 'static', 'Management': 'true', 'Signal S1': 'false', 'Signal X2': 'false',
                                          'Bearer S1': 'false', 'Bearer X2': 'false', 'IEEE1588': 'false', 'Smart scheduler': 'DISABLE'}
            csv[para][F'{enbid}_ber'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_ber'] |= {'NE ID': enbid, 'IF Name': F'xe_0_0_0.{self.site_dict["ran_vlan"]}',
                                          'IP': self.site_dict["ran_ip"], 'Prefix Length': self.site_dict["ran_prefix"],
                                          'IP Get Type': 'static', 'Management': 'false', 'Signal S1': 'true', 'Signal X2': 'true',
                                          'Bearer S1': 'true', 'Bearer X2': 'true', 'IEEE1588': 'false', 'Smart scheduler': 'DISABLE'}
            # csv[para][F'{enbid}_sig'] = copy.deepcopy(csv[para]['fieldnames'])
            # csv[para][F'{enbid}_sig'] |= {'NE ID': enbid, 'IF Name': F'xe_0_0_0.{self.site_dict["oam_vlan"]}',
            #                               'IP': self.site_dict["oam_ip"], 'Prefix Length': self.site_dict["oam_prefix"],
            #                               'IP Get Type': 'static', 'Management': 'false', 'Signal S1': 'true', 'Signal X2': 'true',
            #                               'Bearer S1': 'false', 'Bearer X2': 'false',
            #                               'IEEE1588': 'true' if self.site_dict['ptp_1'] else'false',
            #                               'Smart scheduler': 'DISABLE'}

            # STATIC_ROUTE_INFORMATION
            para = 'STATIC_ROUTE_INFORMATION'
            csv[para][F'{enbid}_oam'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_oam'] |= {'NE ID': enbid, 'VR ID': '0', 'IP Type': self.site_dict["oam_ver"],
                                          'IP Prefix': '::/0' if self.site_dict["oam_ver"] == 'ipv6' else '0.0.0.0/0',
                                          'IP GW': self.site_dict["oam_gw"], 'Route Interface Name': '-'}
            csv[para][F'{enbid}_ber'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_ber'] |= {'NE ID': enbid, 'VR ID': '0', 'IP Type': self.site_dict["ran_vlan"],
                                          'IP Prefix': '::/0' if self.site_dict["ran_ver"] == 'ipv6' else '0.0.0.0/0',
                                          'IP GW': self.site_dict["ran_gw"], 'Route Interface Name': '-'}
            # csv[para][F'{enbid}_sig'] = copy.deepcopy(csv[para]['fieldnames'])
            # csv[para][F'{enbid}_sig'] |= {'NE ID': enbid, 'VR ID': '0', 'IP Type': self.site_dict["ran_ver"],
            #                               'IP Prefix': '::/0' if self.site_dict["ran_ver"] == 'ipv6' else '0.0.0.0/0',
            #                               'IP GW': self.site_dict["ran_gw"], 'Route Interface Name': '-'}

            # VIRTUAL_ROUTING_INFORMATION
            para = 'VIRTUAL_ROUTING_INFORMATION'
            csv[para][F'{enbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}'] |= {'NE ID': enbid, 'VR ID': '0'}

            # VLAN_INFORMATION
            para = 'VLAN_INFORMATION'
            csv[para][F'{enbid}_oam'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_oam'] |= {'NE ID': enbid, 'VLAN ID': self.site_dict["oam_vlan"], 'VR ID': '0', 'VLAN Interface Name': 'xe_0_0_0'}
            csv[para][F'{enbid}_ber'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{enbid}_ber'] |= {'NE ID': enbid, 'VLAN ID': self.site_dict["ran_vlan"], 'VR ID': '0', 'VLAN Interface Name': 'xe_0_0_0'}
            # csv[para][F'{enbid}_sig'] = copy.deepcopy(csv[para]['fieldnames'])
            # csv[para][F'{enbid}_sig'] |= {'NE ID': enbid, 'VLAN ID': self.site_dict["ran_vlan"], 'VR ID': '0', 'VLAN Interface Name': 'xe_0_0_0'}

            self.script['csv'] = copy.deepcopy(csv)

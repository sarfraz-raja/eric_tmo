from .BaseScript import BaseScript
import copy

gnb_dict = {
    'DU': {
        'fieldnames': {
            'NE ID': None, 'NE Type': None, 'NE Version': None, 'Release Version': None, 'Network': None,
            'NE Name': None, 'AdministrativeState': None, 'gNB ID': None, 'gNB ID Length': None,
            'gNB DU ID': None, 'gNB DU Name': None, 'Endpoint CU IP address': None, 'Local Time Offset': None,
            'NE Serial Number': None, 'FW Auto Fusing': None, 'EAIU': None, 'Site ID': None,
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
    'SYSTEM_SHARING_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'DU Primary Flag': None,
        }
    },
    'MAIN_BOARD_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Unit Type': None, 'Unit ID': None, 'Board Type': None,
        }
    },
    'INTER_CONNECTION_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Inter Connection Switch': None, 'Inter Connection Group ID': None, 'Inter Connection Node ID': None,
        }
    },
    'INTER_NODE_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Inter Node ID': None, 'Clock Share Flag': None,
        }
    },
    'CLOCK_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Clock Source ID': None, 'Clock Source': None, 'Priority Level': None, 'Quality Level': 'prc',
        }
    },
    'PTP_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'IP Version': None, 'First Master IP': None, 'Second Master IP': None,
            'Clock Profile': 'telecom-2008', 'PTP Domain': '0',
        }
    },
    'PORT_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'Unit Type': None, 'Unit ID': None, 'Port ID': None, 'VR ID': None, 'Port AdministrativeState': 'unlocked',
            'Connect Type': 'backhaul', 'UDE Type': 'ude-none', 'MTU': '1500', 'Speed Duplex': 's10g-full', 'Fec Mode': 'off',
        }
    },
    'VIRTUAL_ROUTING_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'VR ID': None,
        }
    },
    'IP_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'CPU ID': None, 'External Interface Name': None, 'IP Address': None, 'IP Prefix Length': None,
            'IP Get Type': 'static', 'Management': 'false', 'Control': 'false', 'Bearer': 'false', 'IEEE1588': 'false',
            'Smart scheduler': 'DISABLE',
        }
    },
    'VLAN_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'CPU ID': None, 'VLAN Interface Name': None, 'VLAN ID': None, 'VR ID': '0',
        }
    },
    'LAG_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'CPU ID': None, 'LAG ID': None, 'VR ID': None, 'LAG Interface Name': None,
        }
    },
    'ROUTE_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'CPU ID': None, 'VR ID': None, 'IP Prefix': None, 'IP Prefix Length': None,
            'IP Gateway': None, 'Route Interface Name': None,
        }
    },
    'LOOPBACK_IP_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'CPU ID': None, 'Interface ID': None, 'VR ID': None, 'IP Address': None, 'Control': None, 'Bearer': None,
        }
    },
    'SYSTEM_LOCATION_INFORMATION': {
        'fieldnames': {
            'NE ID': None, 'User Defined Mode': None, 'Latitude': None, 'Longitude': None, 'Height': None,
        }
    },
}


class A_03_GNB_NE_Grow(BaseScript):
    def create_msg(self):
        if self.site_dict['gnbid']:
            gnbid = self.site_dict['gnbid']
            csv = copy.deepcopy(gnb_dict)

            # DU
            para = 'DU'
            csv[para][F'{gnbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}'] |= {
                'NE ID': gnbid, 'NE Type': 'gnb_du',
                'NE Version': self.usid.sw.ne_version, 'Release Version': self.usid.sw.release_version, 'Network': '5G_NR',
                'NE Name': self.site_dict['node'], 'AdministrativeState': 'locked',
                'gNB ID': gnbid, 'gNB ID Length': self.usid.client.gnbidlength,
                'gNB DU ID': self.site_dict['gnb_du_id'], 'gNB DU Name': self.site_dict['gnb_du_name'],
                'Endpoint CU IP address': self.site_dict['end_cu_ip'], 'Local Time Offset': '0', 'NE Serial Number': None,
                'FW Auto Fusing': 'off', 'EAIU': 'not-equip', 'Site ID': None,
            }

            # # SERVER_INFORMATION
            # para = 'SERVER_INFORMATION'
            # csv[para][F'{gnbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            # csv[para][F'{gnbid}'] |= {
            #     'NE ID': None, 'CFM': None, 'PSM': None,
            # }

            para = 'PLMN_INFORMATION'
            csv[para][F'{gnbid}_0'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_0'] |= {
                'NE ID': gnbid, 'PLMN Index': '0', 'MCC': self.site_dict['plmn']['mcc'], 'MNC': self.site_dict['plmn']['mnc']
            }

            para = 'SYSTEM_SHARING_INFORMATION'
            csv[para][F'{gnbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}'] |= {
                'NE ID': gnbid, 'DU Primary Flag': 'off',
            }

            para = 'MAIN_BOARD_INFORMATION'
            csv[para][F'{gnbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}'] |= {
                'NE ID': gnbid, 'Unit Type': 'ump', 'Unit ID': '0', 'Board Type': self.site_dict['controller_type']
            }

            para = 'INTER_CONNECTION_INFORMATION'
            csv[para][F'{gnbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}'] |= {
                'NE ID': gnbid, 'Inter Connection Switch': 'inter-connection-on',
                'Inter Connection Group ID': None, 'Inter Connection Node ID': self.site_dict['inter_connection_node_id'],
            }

            # para = 'INTER_NODE_INFORMATION'
            # csv[para][F'{gnbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            # csv[para][F'{gnbid}'] |= {
            #     'NE ID': None, 'Inter Node ID': None, 'Clock Share Flag': None,
            # }

            # CLOCK_INFORMATION ---> Constant Value for VZ
            para = 'CLOCK_INFORMATION'
            csv[para][F'{gnbid}_0'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_0'] |= {'NE ID': gnbid, 'Clock Source ID': '0', 'Clock Source': 'gps-type', 'Priority Level': '1'}

            # PTP_INFORMATION
            if self.site_dict['ptp_1']:
                para = 'CLOCK_INFORMATION'
                csv[para][F'{gnbid}_1'] = copy.deepcopy(csv[para]['fieldnames'])
                csv[para][F'{gnbid}_1'] |= {'NE ID': gnbid, 'Clock Source ID': '1', 'Clock Source': 'ieee1588-phasetype', 'Priority Level': '2'}
                para = 'PTP_INFORMATION'
                csv[para][F'{gnbid}_0'] = copy.deepcopy(csv[para]['fieldnames'])
                csv[para][F'{gnbid}_0'] |= {'NE ID': gnbid, 'IP Version': self.site_dict['ptp_ver'], 'First Master IP': self.site_dict['ptp_1'],
                                            'Second Master IP': self.site_dict['ptp_2'], 'Clock Profile': 'telecom-2008', 'PTP Domain': '0'}

            para = 'PORT_INFORMATION'
            csv[para][F'{gnbid}_0_0_0'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_0_0_0'] |= {
                'NE ID': gnbid, 'Unit Type': 'ump', 'Unit ID': '0', 'Port ID': '0', 'VR ID': '0', 'Port AdministrativeState': 'unlocked',
                'Connect Type': 'backhaul', 'UDE Type': 'ude-none', 'MTU': '1500', 'Speed Duplex': 's10g-full', 'Fec Mode': 'off',
            }
            csv[para][F'{gnbid}_0_1_0'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_0_1_0'] |= {
                'NE ID': gnbid, 'Unit Type': 'ump', 'Unit ID': '0', 'Port ID': '1', 'VR ID': '0', 'Port AdministrativeState': 'unlocked',
                'Connect Type': 'backhaul', 'UDE Type': 'ude-none', 'MTU': '1500', 'Speed Duplex': 's10g-full', 'Fec Mode': 'off',
            }

            # para = 'VIRTUAL_ROUTING_INFORMATION'
            # csv[para][F'{gnbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            # csv[para][F'{gnbid}'] |= {
            #     'NE ID': None, 'VR ID': None,
            # }

            para = 'IP_INFORMATION'
            csv[para][F'{gnbid}_oam'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_oam'] |= {
                'NE ID': gnbid, 'CPU ID': '0', 'External Interface Name': F'xe_0_0_0.{self.site_dict["oam_vlan"]}',
                'IP Address': self.site_dict["oam_ip"], 'IP Prefix Length': self.site_dict["oam_prefix"],
                'IP Get Type': 'static', 'Management': 'true', 'Control': 'false', 'Bearer': 'false', 'IEEE1588': 'false',
                'Smart scheduler': 'DISABLE'
            }
            csv[para][F'{gnbid}_ber'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_ber'] |= {
                'NE ID': gnbid, 'CPU ID': '0', 'External Interface Name': F'xe_0_0_0.{self.site_dict["ran_vlan"]}',
                'IP Address': self.site_dict["ran_ip"], 'IP Prefix Length': self.site_dict["ran_prefix"],
                'IP Get Type': 'static', 'Management': 'false', 'Control': 'true', 'Bearer': 'true', 'IEEE1588': 'true',
                'Smart scheduler': 'DISABLE'
            }


            para = 'VLAN_INFORMATION'
            csv[para][F'{gnbid}_oam'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_oam'] |= {
                'NE ID': gnbid, 'CPU ID': '0', 'VLAN Interface Name': 'xe_0_0_0', 'VLAN ID': self.site_dict["oam_vlan"], 'VR ID': '0',
            }
            csv[para][F'{gnbid}_ber'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_ber'] |= {
                'NE ID': gnbid, 'CPU ID': '0', 'VLAN Interface Name': 'xe_0_0_0', 'VLAN ID': self.site_dict["ran_vlan"], 'VR ID': '0',
            }

            para = 'ROUTE_INFORMATION'
            csv[para][F'{gnbid}_oam'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_oam'] |= {
                'NE ID': gnbid, 'CPU ID': '0', 'VR ID': '0',
                'IP Prefix': '::/0' if self.site_dict["oam_ver"] == 'ipv6' else '0.0.0.0/0',
                'IP Prefix Length': '0', 'IP Gateway': self.site_dict["oam_gw"], 'Route Interface Name': '-',
            }
            csv[para][F'{gnbid}_ber'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}_ber'] |= {
                'NE ID': gnbid, 'CPU ID': '0', 'VR ID': '0',
                'IP Prefix': '::/0' if self.site_dict["ran_ver"] == 'ipv6' else '0.0.0.0/0',
                'IP Prefix Length': '0', 'IP Gateway': self.site_dict["ran_gw"], 'Route Interface Name': '-',
            }

            para = 'SYSTEM_LOCATION_INFORMATION'
            csv[para][F'{gnbid}'] = copy.deepcopy(csv[para]['fieldnames'])
            csv[para][F'{gnbid}'] |= {'NE ID': gnbid, 'User Defined Mode': 'false', 'Latitude': self.site_dict['latitude'],
                                      'Longitude': self.site_dict['longitude'], 'Height': self.site_dict['height']}

            self.script['csv'] = copy.deepcopy(csv)

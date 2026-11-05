from .BaseCIQ import BaseCIQ
# from .att_dcgk_data import att_dcgk_data
# from common_func.dcgkextract import dcgkextract

import pandas as pd
from pandas import ExcelWriter
import numpy as np

import copy
import os
import datetime
import json
import re


class BaseUSID:
    def __init__(self, client, sw, usm, log, site, base_dir, cqfile, sw_log):
        self.client = client
        self.sw = sw
        self.log = log
        self.sitename = site
        self.base_dir = base_dir
        self.ciq = BaseCIQ(cqfile=cqfile, usm=usm)
        self.sw_log = sw_log
        self.site_dict = dict

        self.gnodeb_enodeb_site_dict()

    def gnodeb_enodeb_site_dict(self):
        site_dict = {}

        column = [
            'SITE_PROJECTS_ID', 'ENODEB_ID', 'ALIAS_NAME', 'CONTROLLER_TYPE', 'GNBID', 'VZ_4G5G_TYPE', 'SERVICE_TYPE',
            'EMS_IP', 'SAMSUNG_OAM_VLAN_ID', 'LATITUDE', 'LONGITUDE', 'PTP_GPS_IP_INFO',
            'SITE_TYPE', 'MCC', 'MNC', 'INTER_CONNECTION_NODE_ID',
            'SAMSUNG_OAM_IP', 'SAMSUNG_OAM_GATEWAY', 'OAM_PREFIX_LENGTH',
            'RAN_VLAN_ID',  'SAMSUNG_TELECOM_IP_ADDRESS_IPV6', 'SAMSUNG_TELECOM_DEFAULT_ROUTER', 'RAN_PREFIX_LENGTH',
            'GNB_DU_ID', 'GNB_DU_NAME', 'CU_OAM_IP_ADDRESS',
        ]

        df_site = self.ciq.df_ciq[column].drop_duplicates()
        for _, r in df_site.iterrows():
            node = getattr(r, 'ALIAS_NAME')
            if node not in site_dict.keys():
                site_dict[node] = {
                    'project_id': getattr(r, 'SITE_PROJECTS_ID'),
                    'node': node,
                    'site_type': getattr(r, 'SITE_TYPE'),
                    'type': None,
                    'enbid': None,
                    'gnbid': None,
                    'plmn': json.loads(self.client.plmn),
                    'bootport': 'PORT_0_0_2',
                    'ipv6_ip': getattr(r, 'SAMSUNG_OAM_IP'),
                    'ipv6_gw': getattr(r, 'SAMSUNG_OAM_GATEWAY'),
                    'ipv6_nm': '126',
                    'ipver': '6',
                    'vlanid': getattr(r, 'SAMSUNG_OAM_VLAN_ID'),
                    'rs_ip': getattr(r, 'EMS_IP'),
                    'ne_type': None,
                    'ne_id': None,
                    'ne_type2': None,
                    'ne_id2': None,
                    'speed': '10000',
                    'flag': None,

                    'ptp_ver': 'ipv6' if (getattr(r, 'PTP_GPS_IP_INFO') is not None and ':' in getattr(r, 'PTP_GPS_IP_INFO')) else 'ipv4',
                    'ptp_1': getattr(r, 'PTP_GPS_IP_INFO'),
                    'ptp_2': None,

                    'latitude': self.decimal_degree_2_dms(value=getattr(r, 'LATITUDE'), latitude_flag=True),
                    'longitude':  self.decimal_degree_2_dms(value=getattr(r, 'LONGITUDE'), latitude_flag=False),
                    'height': f'{0:0.2f}m',

                    'inter_connection_node_id': getattr(r, 'INTER_CONNECTION_NODE_ID'),
                    'controller_type': getattr(r, 'CONTROLLER_TYPE'),

                    'oam_ver': 'ipv4' if (getattr(r, 'SAMSUNG_OAM_VLAN_ID') is not None and ':' not in getattr(r, 'SAMSUNG_OAM_IP')) else 'ipv6',
                    'oam_vlan': getattr(r, 'SAMSUNG_OAM_VLAN_ID'),
                    'oam_ip': getattr(r, 'SAMSUNG_OAM_IP'),
                    'oam_gw': getattr(r, 'SAMSUNG_OAM_GATEWAY'),
                    'oam_prefix': '64' if getattr(r, 'OAM_PREFIX_LENGTH') is None else getattr(r, 'OAM_PREFIX_LENGTH'),

                    'ran_ver': 'ipv4' if (getattr(r, 'SAMSUNG_TELECOM_IP_ADDRESS_IPV6') is not None and
                                          '.' in getattr(r, 'SAMSUNG_TELECOM_IP_ADDRESS_IPV6')) else 'ipv6',
                    'ran_vlan': getattr(r, 'RAN_VLAN_ID'),
                    'ran_ip': getattr(r, 'SAMSUNG_TELECOM_IP_ADDRESS_IPV6'),
                    'ran_gw': getattr(r, 'SAMSUNG_TELECOM_DEFAULT_ROUTER'),
                    'ran_prefix': '64' if getattr(r, 'RAN_PREFIX_LENGTH') is None else getattr(r, 'RAN_PREFIX_LENGTH'),

                    'gnb_du_id': getattr(r, 'GNB_DU_ID'),
                    'gnb_du_name': getattr(r, 'GNB_DU_NAME'),
                    'end_cu_ip': getattr(r, 'CU_OAM_IP_ADDRESS'),
                }

            if len(df_site.loc[(df_site['ALIAS_NAME'] == node), 'ENODEB_ID'].drop_duplicates()) > 1:
                site_dict[node] |= {'type': 'mmbb', 'du_ld_flag': 'LTE_NR'}
                for _, s in df_site.loc[(df_site['ALIAS_NAME'] == node)].iterrows():
                    if str(getattr(s, 'SERVICE_TYPE')).upper().endswith('LTE'):
                        site_dict[node] |= {'ne_type': 'ENB', 'ne_id': getattr(s, 'ENODEB_ID'),
                                            'enbid': getattr(s, 'ENODEB_ID')}
                    elif str(getattr(s, 'SERVICE_TYPE')).upper().endswith('NR'):
                        site_dict[node] |= {'ne_type2': 'DU', 'ne_id2': getattr(s, 'ENODEB_ID'),
                                            'gnbid': getattr(s, 'ENODEB_ID')}
            else:
                if str(getattr(r, 'SERVICE_TYPE')).upper().endswith('LTE'):
                    site_dict[node] |= {'ne_type': 'ENB', 'ne_id': getattr(r, 'ENODEB_ID'),
                                        'enbid': getattr(r, 'ENODEB_ID'), 'du_ld_flag': None, 'type': 'enb'}
                elif str(getattr(r, 'SERVICE_TYPE')).upper().endswith('NR'):
                    site_dict[node] |= {'ne_type': 'DU', 'ne_id': getattr(r, 'ENODEB_ID'),
                                        'gnbid': getattr(r, 'ENODEB_ID'), 'du_ld_flag': None, 'type': 'gnb'}
        self.site_dict = copy.deepcopy(site_dict)

    @staticmethod
    def decimal_degree_2_dms(*, value: float, latitude_flag: bool) -> str:
        """
            Converts a Decimal Degree Value into
            Degrees Minute Seconds Notation.
            S 096:39:39.000
            W 096:39:39.000
        """
        value = float(value)
        news = ''
        if latitude_flag:
            if value < 0: news = 'S'
            elif value > 0: news = 'N'
        else:
            if value < 0: news = 'W'
            elif value > 0: news = 'E'
        value = abs(value)
        deg = int(value)
        submin = (value - deg) * 60
        min = int(submin)
        sec = abs((submin-int(min)) * 60)
        return F'{news} {abs(deg):03d}:{min:02d}:{sec:06.3f}'

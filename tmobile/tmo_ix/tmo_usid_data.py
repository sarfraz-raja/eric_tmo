import os
import json
import copy
from datetime import datetime
import pandas as pd
import numpy as np
from pandas import ExcelWriter
from collections import OrderedDict
from ipaddress import IPv4Interface


from .tmo_data import PlmnId, node_username, node_password, timeOffset_dict, BB_dict, get_sw_nodeidentifier
from .tmo_dcgk_data import tmo_dcgk_data
from .tmo_ciq_data import tmo_ciq_data
from common_func.dcgkextract import dcgkextract


class tmo_usid_data:
    def __init__(self, client, base_dir, log, cix_file, zip_file=None, sites=''):
        self.SiteId = sites
        self.client = client
        self.base_dir = base_dir
        self.log = log

        # Process CIQ Data
        self.cix = tmo_ciq_data(infile=cix_file, sites=None)
        # Extract MO/Parameters for DCGK Files
        self.sites = {}
        dcgk_extract = dcgkextract(inzip=zip_file)
        for node in dcgk_extract.merged_dict.keys():
            self.sites['site_' + str(node)] = tmo_dcgk_data(node, dcgk_extract.merged_dict.get(node, {}))
        self.mom_files, self.mom_cache = dcgk_extract.mom_files, {}
        self.source_files = dcgk_extract.source_files
        self.debug_csv, self.debug_csv_local = False, False
        self.df_ant_near_unit = pd.DataFrame()
        self.ant_system_list = []

        self.gnodeb = {}
        self.df_gnb_cell = pd.DataFrame([], columns=['node', 'celltype', 'presite', 'precell', 'postsite', 'postcell', 'pregnbid', 'precellid',
                                                     'gnbid', 'cellid', 'carrier', 'BBChange', 'addcell', 'nrpci', 'nrtac', 'rachrootsequence',
                                                     'ssbsubcarrierspacing', 'sc', 'arfcndl', 'arfcnul', 'confpow', 'bschannelbwdl', 'bschannelbwul',
                                                     'sef', 'prefru', 'prefrutype'])
        for node in self.cix.gnodeb_list:
            self.gnodeb[node] = self.site_dict_for_eNB_gNB(node=node, node_type='5G')
        if len(self.gnodeb) > 0:
            self.gNodeB_cell_status()
            self.gNodeB_create_cell()
            # Relations

        self.enodeb = {}
        self.df_enb_cell = pd.DataFrame([], columns=[
            'celltype', 'presite', 'precell', 'postsite', 'postcell', 'preenbid', 'precellid', 'enbid', 'cellid',
            'carrier', 'BBChange', 'addcell', 'freqband', 'earfcndl', 'earfcnul', 'dlchannelbandwidth',
            'ulchannelbandwidth', 'physicallayercellid', 'rachrootsequence', 'cellrange', 'tac', 'userlabel',
            'isdlonly', 'latitude', 'longitude', 'altitude', 'eutrancellcoverage', 'sc', 'noofrx', 'nooftx',
            'confpow', 'sef', 'prefru', 'prefrutype', 'nbiotcelltype', 'precellref', 'postcellref',
        ])
        for node in self.cix.enodeb_list:
            self.enodeb[node] = self.site_dict_for_eNB_gNB(node=node, node_type='4G')
        if len(self.enodeb) > 0:
            self.eNodeB_cell_status()
            self.eNodeB_cell_create()
            self.eNodeB_nbiot_create()
            # Relations
            self.eNodeB_EUtraNetwork()
            self.eNodeB_GUtraNetwork()
            self.eNodeB_UtraNetwork()
            self.eNodeB_GeraNetwork()

            self.eNodeB_validate_cix_dcgk_data()

        self.enodeb_gnodeb_antenna_system()
        self.enodeb_gnodeb_antnearunit()
        self.xmu_all_site()
        self.rilink_all_site()
        self.save_different_dataframe()

        del self.cix
        del self.ant_system_list
        self.script_dict = {'AP': False, 'SB': '', 'SE': '', 'SI': '', 'conf': []}

    @staticmethod
    def df_nan_to_none(*, df: pd.DataFrame) -> pd.DataFrame: return df.replace({np.nan: None})

    # Site Dict for eNodeB and gNodeB
    def site_dict_for_eNB_gNB(self, *, node: str, node_type: str) -> dict:
        tmp_dict = {'4G': {'CQ': 'ENodeB', 'IP': 'EDP', 'nodeid': 'enbid', 'lte': 'LTE',
                           'oam_van': 'nmnetaavethernetvlanid', 'oam_ip': 'enodeboamipaddress',
                           'oam_gway': 'nmnetdefaultgateway', 'oam_mask': 'nmnetsubnetmask',
                           'lte_vlan': 'corenetaavethernetvlanids1x2uc', 'lte_ip': 'enodebscontrolplaneipaddresss1x2',
                           'lte_gway': 'corenetdefaultgateways1x2uc', 'lte_mask': 'corenetsubnetmask'},
                    '5G': {'CQ': 'gNodeB', 'IP': 'EDP5G', 'nodeid': 'gnbid', 'lte': 'vr_TRAFFIC',
                           'oam_van': 'nmnetaavethernetvlanid', 'oam_ip': 'gnodeboamipaddress',
                           'oam_gway': 'nmnetdefaultgateway', 'oam_mask': 'nmnetsubnetmask',
                           'lte_vlan': 'corenetaavethernetvlanids1x2uc', 'lte_ip': 'gnodebscontrolplaneipaddresss1x2',
                           'lte_gway': 'corenetdefaultgateways1x2uc', 'lte_mask': 'corenetsubnetmask'}
                    }
        # node = cq_dict.node
        BBType = self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['CQ'], field='BBType')
        assert BBType in BB_dict.keys(), \
            F'!!! Input Error, BBType is not added for site {node} --- {BBType} contact development team!!! '
        node_dict = {
            'node': node,
            'postsite': node,
            'tech': node_type,
            'fingerprint': node,
            'IDLE': None if self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['CQ'], field='idle') not in [
                'IDL_A1', 'IDL_A2', 'IDL_A3', 'TN_IDL_A', 'TN_IDL_B', 'TN_IDL_C', 'TN_IDL_D',
                'TN_IDL_E'] else self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['CQ'], field='IDLE'),
            'MMBB': True if node in self.cix.enodeb_list and node in self.cix.gnodeb_list else False,
            # 'MSMM': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['CQ'], field='msmm'),
            # 'pucchOverdimensioning': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['CQ'],
            #                                                             field='pucchoverdimensioning'),
            # 'compensationDelay': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['CQ'], field='gpscompensationdelay'),
            # 'RBSType': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['CQ'], field='RBSType'),

            'BBChange': True,
            'BBType': BBType,
            'BBId': 'BB-01',
            'TnPort': BB_dict[BBType]['TnPort'],
            'RiPort': BB_dict[BBType]['RiPort'],

            'plmnlist': copy.deepcopy(PlmnId),
            'nodeid': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['CQ'], field=tmp_dict[node_type]['nodeid']),
            'gNBIdLength': '24',

            'sw_version': self.client.software.swname,
            'ENM': self.client.enm,
            'nodeType': 'RadioNode',
            'sw': '',
            'nodeIdentifier': '',
            'username': node_username,
            'password': node_password,
            'ntpip1': self.client.NTPServer1,
            'ntpip2': self.client.NTPServer2,
            'ntpip3': self.client.NTPServer3,
            'ntpip4': self.client.NTPServer4,
            'timeZone': self.client.timeZone,
            'timeOffset': timeOffset_dict.get(self.client.timeZone, '00:00'),
            'dnPrefix': F'SubNetwork=ONRM_ROOT_MO,SubNetwork={self.client.mname},MeContext={node}',

            'gpsdelay': '0',
            'transaction': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field='transaction'),
            'csr_type': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field='csrtype'),
            'admOperatingMode': '6 (1G_FULL)',
            'xmuid': 'XMU03-1-7',
            'oam': 'vr_OAM',
            'lte': 'LTE' if node_type == '4G' else 'vr_TRAFFIC',
            'lte_interface': '1',

            'oam_van': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field=tmp_dict[node_type]['oam_van']),
            'oam_ip': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field=tmp_dict[node_type]['oam_ip']),
            'oam_gway': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field=tmp_dict[node_type]['oam_gway']),
            'oam_mask': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field=tmp_dict[node_type]['oam_mask']),
            'oam_plength': '',

            'lte_vlan': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field=tmp_dict[node_type]['lte_vlan']),
            'lte_ip': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field=tmp_dict[node_type]['lte_ip']),
            'lte_gway': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field=tmp_dict[node_type]['lte_gway']),
            'lte_mask': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field=tmp_dict[node_type]['lte_mask']),
            'lte_plength': '',

            'freqsync1': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field='ntpserverprimaryipaddress'),
            'freqsync2': self.cix.get_site_field_data_upper(node=node, sheet_name=tmp_dict[node_type]['IP'], field='ntpserversecondaryipaddress'),

            'ENodeBFunction': None,
            'GNBDUFunction': None,
            'GNBCUCPFunction': None,
            'GNBCUUPFunction': None,
            'NRNetwork': '1',
            'EUtraNetwork': '1',
            'GUtraNetwork': '1',
            'UtraNetwork': '1',
            'GeraNetwork': '1',
        }
        # admOperatingMode based on prefix length and CSR Type
        node_dict['oam_plength'] = str(IPv4Interface(F'{node_dict["oam_ip"]}/{node_dict["oam_mask"]}').with_prefixlen).split('/')[-1]
        node_dict['lte_plength'] = str(IPv4Interface(F'{node_dict["lte_ip"]}/{node_dict["lte_mask"]}').with_prefixlen).split('/')[-1]
        if (node_dict['lte_plength'] == '27') or (str(node_dict['csr_type']).upper() in ['IXR-E', 'IXR-R6']):
            node_dict['admOperatingMode'] = '9 (10G_FULL)'

        # Manipulating TN Data in Case of MMBB
        if node_type == '4G' and node_dict['MMBB']:
            # self.gnodeb[row.node]['mmbb'] = True
            if node_dict['lte_plength'] == '32' and self.gnodeb[node]['lte_plength'] != '32':
                node_dict.update({'lte': 'vr_TRAFFIC', 'lte_interface': 'LTE', 'admOperatingMode': self.gnodeb[node]['admOperatingMode']})
            elif node_dict['lte_plength'] != '32' and self.gnodeb[node]['lte_plength'] == '32':
                self.gnodeb[node].update({'lte': 'LTE', 'lte_interface': 'NR', 'admOperatingMode': node_dict['admOperatingMode']})
            elif node_dict["lte_plength"] != '32':
                if self.gnodeb[node]['lte_plength'] == '27' or str(self.gnodeb[node]['csr_type']).upper() in ['IXR-E', 'IXR-R6']:
                    node_dict['admOperatingMode'] = '9 (10G_FULL)'

        # SW Package and nodeIdentifier
        # if node_type == '4G':
        #     if node_dict['BBType'] in ['6630', '5216', '6502'] and \
        #             len(self.cix.edx.get('EutranCellFDD').loc[(self.cix.edx.get('EutranCellFDD').node == node) &
        #                                                       (self.cix.edx.get('EutranCellFDD').cell.str.contains('^T'))].index) > 0:
        #         node_dict['sw'] = software_dict[node_dict['sw_version']]['6630_L41_N41']
        #     else: node_dict['sw'] = software_dict[node_dict['sw_version']][node_dict['BBType']]
        #     node_dict['nodeIdentifier'] = nodeIdentifier_dict[node_dict['sw_version']][node_dict['ENM']][node_dict['sw']]
        # else:
        #     if node_dict['BBType'] in ['6630', '5216', '6502'] and \
        #             len(self.cix.edx.get('gUtranCell').loc[(self.cix.edx.get('gUtranCell').node == node) &
        #                                                    (self.cix.edx.get('gUtranCell').cell.str.contains('^A'))].index) > 0:
        #         node_dict['sw'] = software_dict[node_dict['sw_version']]['6630_L41_N41']
        #     else: node_dict['sw'] = software_dict[node_dict['sw_version']][node_dict['BBType']]
        #     node_dict['nodeIdentifier'] = nodeIdentifier_dict[node_dict['sw_version']][node_dict['ENM']][node_dict['sw']]
        # SW Package and nodeIdentifier
        sw_bb_type = node_dict['BBType']
        if (node_dict['BBType'] in ['6630', '5216', '6502'] and
                (len(self.cix.edx.get('EutranCellFDD').loc[(self.cix.edx.get('EutranCellFDD').node == node) &
                                                           (self.cix.edx.get('EutranCellFDD').cell.str.contains('^T'))].index) > 0 or
                 len(self.cix.edx.get('gUtranCell').loc[(self.cix.edx.get('gUtranCell').node == node) &
                                                        (self.cix.edx.get('gUtranCell').cell.str.contains('^A'))].index) > 0)):
            sw_bb_type = '6630_L41_N41'
        sw, nodeIdentifier = get_sw_nodeidentifier(sw=node_dict['sw_version'], bb_type=sw_bb_type, enm=node_dict['ENM'])
        if sw is None or nodeIdentifier is None:
            self.log.info(F'Tool Updated is needed for SW and/or nodeIdentifier {node_dict["node"]} -- '
                          F'{node_dict["sw_version"]} -- {node_dict["ENM"]} -- {sw} -- {nodeIdentifier}')
        node_dict.update({'sw': sw, 'nodeIdentifier': nodeIdentifier})
        # Update Site Data when DCGK exists
        if self.sites.get(F'site_{node}'):
            site = self.sites.get(F'site_{node}')
            node_dict['BBChange'] = site.BBType.upper() != node_dict['BBType']
            if not node_dict['BBChange']:
                node_dict['BBId'] = site.BBId
                node_dict['fingerprint'] = site.fingerprint
            if node_type == '4G' and len(site.find_mos_with_end_moc(moc='ENodeBFunction')) > 0:
                node_dict['ENodeBFunction'] = site.find_mos_with_end_moc(moc='ENodeBFunction')[0]
                for moc in ['EUtraNetwork', 'GUtraNetwork', 'UtraNetwork', 'GeraNetwork']:
                    if len(site.find_mo_ending_with_parent_str(moc=moc, parent=node_dict['ENodeBFunction'])) > 0:
                        node_dict[moc] = site.find_mo_ending_with_parent_str(moc=moc, parent=node_dict['ENodeBFunction'])[0].split('=')[-1]
            if node_type == '5G':
                for moc in ['GNBDUFunction', 'GNBCUCPFunction', 'GNBCUUPFunction']:
                    if len(site.find_mos_with_end_moc(moc=moc)) > 0:
                        node_dict[moc] = site.find_mos_with_end_moc(moc=moc)[0]
                if not node_dict['GNBCUCPFunction']:
                    for moc in ['NRNetwork', 'EUtraNetwork']:
                        if len(site.find_mo_ending_with_parent_str(moc=moc, parent=node_dict['GNBCUCPFunction'])) > 0:
                            node_dict[moc] = site.find_mo_ending_with_parent_str(moc=moc, parent=node_dict['GNBCUCPFunction'])[0].split('=')[-1]
        return node_dict

    # --- NR - 5G ---
    def gNodeB_cell_status(self):
        cell_dict_log = {}
        ecolumns = ['celltype', 'fdn', 'presite', 'precell', 'pregnbid', 'precellid', 'postsite', 'postcell', 'postcellid', 'sefcix',
                    'sccix', 'carrier', 'rrushared', 'frutypecix', 'confpowcix', 'dl_ul_delay_att']
        for site in self.sites:
            for mo in self.sites.get(site).find_mo_ending_with_parent_str('NRCellDU'):
                cellid = self.sites.get(site).site_extract_data(mo).get('cellLocalId')
                p_gid = self.sites.get(site).site_extract_data(','.join(mo.split(',')[2:-1])).get('gNBId')
                cell_dict_log[cellid] = ['5GNR', mo, site.split('_', maxsplit=1)[1], mo.split('=')[-1], p_gid, cellid]
        cell_list_info = []
        for index, row in self.cix.edx.get('gUtranCell').iterrows():
            if cell_dict_log.get(row.cellid):
                cell_list_info.append(cell_dict_log.get(row.cellid) + [row.node, row.gutrancell, row.cellid, row.sefcix, row.sectorid, row.carrier,
                                                                       row.rrushared, row.radiotype, row.configuredmaxtxpower, row.dl_ul_delay_att])
            else:
                cell_list_info.append(['5GNR', None, None, None, '', '', row.node, row.gutrancell, row.cellid, row.sefcix, row.sectorid, row.carrier,
                                       row.rrushared, row.radiotype, row.configuredmaxtxpower, row.dl_ul_delay_att])
        df_gnb_cell = self.df_nan_to_none(df=pd.DataFrame(cell_list_info, columns=ecolumns))
        df_gnb_cell['movement'] = 'yes'
        df_gnb_cell.loc[df_gnb_cell.presite.isnull(), 'movement'] = 'new'
        df_gnb_cell.loc[(df_gnb_cell.precell == df_gnb_cell.postcell) & (df_gnb_cell.presite == df_gnb_cell.postsite), 'movement'] = 'no'
        df_gnb_cell['BBChange'] = df_gnb_cell.postsite.apply(lambda x: self.gnodeb[x]['BBChange'])
        df_gnb_cell['addcell'] = (df_gnb_cell.BBChange | (df_gnb_cell.movement != 'no'))
        df_gnb_cell = self.df_nan_to_none(df=df_gnb_cell)
        self.df_gnb_cell = df_gnb_cell.copy()

    def gNodeB_create_cell(self):
        attrs_cell = ['cellLocalId', 'nRPCI', 'nRTAC', 'nCI', 'rachRootSequence', 'ssbSubCarrierSpacing', 'userLabel']
        attrs_sec = ['arfcnDL', 'arfcnUL', 'configuredMaxTxPower', 'bSChannelBwDL', 'bSChannelBwUL']
        gnb_cell_dict = {}
        for index, row in self.df_gnb_cell.iterrows():
            if row.presite is None: continue
            site = self.sites.get(F'site_{row.presite}')
            tmp = {}
            if row.presite == row.postsite:
                tmp['gnbid'] = site.site_extract_data(site.get_mo_name_ending_str(','.join(row.fdn.split(',')[-4:-1]))).get('gNBId')
            else:
                tmp['gnbid'] = self.cix.get_site_field_data_upper(row.postsite, 'gNodeB', 'gnbid')
            data = site.site_extract_data(row.fdn)
            for attr in attrs_cell:
                tmp[attr] = data.get(attr, '')
            tmp['userLabel'] = tmp['userLabel'].replace(row.precell, row.postcell) if tmp['userLabel'] is not None else row.postcell
            tmp['ssbFrequency'] = data.get('ssbFrequencyAutoSelected', '') if data.get('ssbFrequencyAutoSelected', '') not in [
                'None', None, '', '0'] else data.get('ssbFrequency')
            rf_branches, rfb_list, temp_fru = [], [], []
            sc_mo = data.get('nRSectorCarrierRef', '')
            if len(sc_mo) > 0: sc_mo = site.get_mo_name_ending_str(sc_mo[0])
            tmp['presc'] = sc_mo.split('=')[-1] if len(sc_mo) > 0 else None
            tmp['scfdn'] = sc_mo if len(sc_mo) > 0 else None
            sector_data = site.site_extract_data(sc_mo) if len(sc_mo) > 0 else {}
            for attr in attrs_sec:
                tmp[attr] = None if len(sc_mo) == 0 else sector_data.get(attr, '')
            sef_mo = sector_data.get('sectorEquipmentFunctionRef', '')
            if len(sef_mo) > 0:
                sef_mo = site.get_mo_name_ending_str(sef_mo)
                rfb_list.extend(site.site_extract_data(sef_mo).get('rfBranchRef'))
            tmp['presef'] = sef_mo.split('=')[-1] if len(sef_mo) > 0 else None
            tmp['seffdn'] = sef_mo if len(sef_mo) > 0 else None

            # ---Antenna Systems---
            temp_fru_a = self.antenna_system_cell(site=site, presite=row.presite, precell=row.precell, rfb_list=rfb_list)
            tmp['prefru'] = [_[0] for _ in temp_fru_a]
            tmp['prefrutype'] = [_[1] for _ in temp_fru_a]
            tmp['prefrutype'].sort()
            tmp['prefrusn'] = [_[2] for _ in temp_fru_a]
            gnb_cell_dict[row.postcell] = tmp.copy()

        df_gnb_move = self.df_nan_to_none(df=pd.DataFrame.from_dict(gnb_cell_dict).T)
        if len(gnb_cell_dict) > 0:
            df_gnb_move.rename(columns=lambda x: str(x).lower(), inplace=True)
            df_gnb_move.rename(columns={'celllocalid': 'cellid', }, inplace=True)
        # # ---New Cells---
        df = self.cix.edx.get('gUtranCell').copy()
        df = df[['gutrancell', 'gnbid', 'cellid', 'nrpci', 'nrtac', 'nci', 'rachrootsequence', 'ssbsubcarrierspacing', 'arfcndl', 'arfcnul',
                 'bschannelbwdl', 'bschannelbwul', 'configuredmaxtxpower']]  # , 'ssbfrequency'
        df = df.assign(presef=None, seffdn=None, presc=None, scfdn=None, rfbranches=None, prefru=None, prefrutype=None, prefrusn=None)
        df = df.loc[df.gutrancell.isin(self.df_gnb_cell[self.df_gnb_cell['movement'] == 'new'].postcell)]
        df.set_index('gutrancell', inplace=True)
        df = pd.concat([df_gnb_move, df])
        # df = df_gnb_move.append(df)
        df['sc'] = df.presc
        df['sef'] = df.presef
        self.df_gnb_cell = self.df_gnb_cell.merge(df, left_on='postcell', right_index=True, suffixes=('', '_mv'))
        self.df_gnb_cell.rename(columns={'configuredmaxtxpower': 'confpow', }, inplace=True)
        self.df_gnb_cell['noofrx'] = '0'
        self.df_gnb_cell['nooftx'] = '0'
        # # ---SEF and SectorCarrier for 8843 and RRU_shared---
        self.df_gnb_cell.loc[((self.df_gnb_cell.sef is None) | self.df_gnb_cell.addcell), 'sef'] = self.df_gnb_cell.sefcix
        self.df_gnb_cell.loc[((self.df_gnb_cell.sc is None) | self.df_gnb_cell.addcell), 'sc'] = self.df_gnb_cell.sccix
        self.df_gnb_cell['fruchange'] = ~(self.df_gnb_cell.prefrutype == self.df_gnb_cell.frutypecix)
        self.df_gnb_cell = self.df_gnb_cell.replace({np.nan: None})

    def gNodeB_NRNetwork(self):
        pass

    def gNodeB_EUtraNetwork(self):
        pass

    # --- LTE - 4G ---
    def eNodeB_cell_status(self):
        cell_dict_log = {}
        ecolumns = ['celltype', 'fdn', 'presite', 'precell', 'preenbid', 'precellid', 'postsite', 'postcell', 'postcellid',
                    'sefcix', 'sccix', 'carrier', 'rrushared', 'frutypecix', 'confpowcix', 'dl_ul_delay_att']
        for site in self.sites:
            for mo in self.sites.get(site).find_mo_ending_with_parent_str('EUtranCellFDD'):
                cellid = self.sites.get(site).site_extract_data(mo).get('cellId')
                p_eid = self.sites.get(site).site_extract_data(','.join(mo.split(',')[2:-1])).get('eNBId')
                cell_dict_log[cellid] = ['FDD', mo, site.split('_', maxsplit=1)[1], mo.split('=')[-1], p_eid, cellid]
            for mo in self.sites.get(site).find_mo_ending_with_parent_str('EUtranCellTDD'):
                cellid = self.sites.get(site).site_extract_data(mo).get('cellId')
                p_eid = self.sites.get(site).site_extract_data(','.join(mo.split(',')[2:-1])).get('eNBId')
                cell_dict_log[cellid] = ['TDD', mo, site.split('_', maxsplit=1)[1], mo.split('=')[-1], p_eid, cellid]
        cell_list_info = []
        for index, row in self.cix.edx.get('EutranCellFDD').iterrows():
            if cell_dict_log.get(row.cellid):
                cell_list_info.append(cell_dict_log.get(row.cellid) +
                                      [row.node, row.eutrancellfddid, row.cellid, row.sefcix, row.sectorid, row.carrier, row.rrushared, row.rrutype,
                                       row.confpow, row.dl_ul_delay_att])
            else:
                cell_list_info.append([row.celltype, None, None, None, '', '',
                                       row.node, row.eutrancellfddid, row.cellid, row.sefcix, row.sectorid, row.carrier, row.rrushared, row.rrutype,
                                       row.confpow, row.dl_ul_delay_att])
        df = self.df_nan_to_none(df=pd.DataFrame(cell_list_info, columns=ecolumns))
        df['movement'] = 'yes'
        df.loc[df.presite.isnull(), 'movement'] = 'new'
        df.loc[(df.precell == df.postcell) & (df.presite == df.postsite), 'movement'] = 'no'
        df['BBChange'] = df.postsite.apply(lambda x: self.enodeb[x]['BBChange'])
        df['addcell'] = (df.BBChange | (df.movement != 'no'))
        df = self.df_nan_to_none(df=df)
        self.df_enb_cell = df.copy()

    def eNodeB_cell_create(self):
        cell_val_dict = {}
        attrs = ['freqBand', 'cellId', 'earfcndl', 'earfcnul', 'dlChannelBandwidth', 'ulChannelBandwidth', 'physicalLayerCellId',
                 'rachRootSequence', 'cellRange', 'tac', 'userLabel', 'isDlOnly', 'latitude', 'longitude', 'altitude', 'eutranCellCoverage']
        tdd_attr_dict = {'earfcndl': 'earfcn', 'earfcnul': 'earfcn', 'dlChannelBandwidth': 'channelBandwidth',
                         'ulChannelBandwidth': 'channelBandwidth'}
        for index, row in self.df_enb_cell.iterrows():
            if row.presite is None: continue
            site, tmp = self.sites.get('site_' + row.presite), {}
            if row.presite == row.postsite:
                tmp['enbid'] = site.site_extract_data(site.get_mo_name_ending_str(','.join(row.fdn.split(',')[-4:-1]))).get('eNBId')
            else:
                tmp['enbid'] = self.cix.get_site_field_data_upper(row.postsite, 'ENodeB', 'enbid')
            data = site.site_extract_data(row.fdn)
            for attr in attrs:
                tmp[attr] = data.get(attr, data.get(tdd_attr_dict.get(attr, '')))
            if tmp['userLabel'] is not None:
                tmp['userLabel'] = tmp['userLabel'].replace(row.precell, row.postcell)
            else:
                tmp['userLabel'] = row.postcell
            if tmp['physicalLayerCellId'] is None:
                tmp['physicalLayerCellId'] = int(data.get('physicalLayerCellIdGroup')) * 3 + int(data.get('physicalLayerSubCellId'))
            rfb_list, sector_ref = [], data.get('sectorCarrierRef')
            tmp.update({'scfdn': None, 'presc': None, 'noofrx': None, 'nooftx': None, 'confpow': None, 'sef': None, 'seffdn': None})
            if len(sector_ref) > 0:
                sector_ref = sector_ref[0]
                sector_mo = site.get_mo_name_ending_str(sector_ref)
                sector_data = site.site_extract_data(sector_mo)
                tmp.update({'scfdn': sector_mo, 'presc': sector_ref.split('=')[-1], 'noofrx': sector_data.get('noOfRxAntennas'),
                            'nooftx': sector_data.get('noOfTxAntennas'), 'confpow': sector_data.get('configuredMaxTxPower')})
                rfb_list.extend(sector_data.get('rfBranchTxRef'))
                rfb_list.extend(sector_data.get('rfBranchRxRef'))
                sef_ref = sector_data.get('sectorFunctionRef')
                if sef_ref is not None:
                    sef_mo = site.get_mo_name_ending_str(sef_ref)
                    tmp.update({'presef': sef_ref.split('=')[-1], 'seffdn': sef_mo})
                    rfb_list.extend(site.site_extract_data(sef_mo).get('rfBranchRef'))
            # ---Antenna Systems---
            temp_fru_a = self.antenna_system_cell(site=site, presite=row.presite, precell=row.precell, rfb_list=rfb_list)
            tmp['prefru'] = [_[0] for _ in temp_fru_a]
            tmp['prefrutype'] = [_[1] for _ in temp_fru_a]
            tmp['prefrutype'].sort()
            tmp['prefrusn'] = [_[2] for _ in temp_fru_a]
            # tmp['rfbranches'] = rf_branches
            cell_val_dict[row.postcell] = tmp.copy()

        df = self.df_nan_to_none(df=pd.DataFrame.from_dict(cell_val_dict).T)
        if len(cell_val_dict) > 0:
            df.rename(columns=lambda x: str(x).lower(), inplace=True)
        # ---New Cells---
        df_new = self.cix.edx.get('EutranCellFDD').copy()
        df_new = df_new[['eutrancellfddid', 'enbid', 'freqband', 'cellid', 'earfcndl', 'earfcnul', 'dlchannelbandwidth', 'ulchannelbandwidth',
                         'physicallayercellid', 'rachrootsequence', 'cellrange', 'tac', 'userlabel', 'isdlonly', 'latitude', 'longitude',
                         'nooftx', 'noofrx', 'confpow', 'altitude', 'eutrancellcoverage']]
        df_new['isdlonly'] = df_new.isdlonly.str.upper().replace({'NO': 'false', 'YES': 'true'})
        df_new = df_new.assign(presef=None, seffdn=None, presc=None, scfdn=None, rfbranches=None, prefru=None, prefrutype=None, prefrusn=None)
        df_new = df_new.loc[df_new.eutrancellfddid.isin(self.df_enb_cell[self.df_enb_cell['movement'] == 'new'].postcell)]
        df_new.set_index('eutrancellfddid', inplace=True)
        df = pd.concat([df, df_new])
        # df = df.append(df_new)
        df = df.replace({np.nan: None})
        df['sc'] = df.presc
        df['sef'] = df.presef
        self.df_enb_cell = self.df_enb_cell.merge(df, left_on='postcell', right_index=True, suffixes=('', '_mv'))
        self.df_enb_cell.loc[((self.df_enb_cell.sef is None) | self.df_enb_cell.addcell), 'sef'] = self.df_enb_cell.sefcix
        self.df_enb_cell.loc[((self.df_enb_cell.sc is None) | self.df_enb_cell.addcell), 'sc'] = self.df_enb_cell.sccix
        self.df_enb_cell['fruchange'] = ~(self.df_enb_cell.prefrutype == self.df_enb_cell.frutypecix)
        self.df_enb_cell = self.df_enb_cell.replace({np.nan: None, '': None})

    def eNodeB_nbiot_create(self):
        temp_list = []
        for site in self.sites:
            site = self.sites.get(site)
            node = site.node
            mo = site.find_mo_ending_with_parent_str('ENodeBFunction')
            if len(mo) == 0: continue
            for n_mo in site.find_mo_ending_with_parent_str('NbIotCell', mo[0]):
                nbiot_data = site.site_extract_data(n_mo)
                temp_list.append({
                    'celltype': 'IOT',
                    'presite': node,
                    'precell': n_mo.split('=')[-1],
                    'precellid': nbiot_data.get('cellId'),
                    'nbiotcelltype': nbiot_data.get('nbIotCellType'),
                    'tac': nbiot_data.get('tac'),
                    'earfcndl': nbiot_data.get('earfcndl'),
                    'earfcnul': nbiot_data.get('earfcnul'),
                    'physicallayercellid': nbiot_data.get('physicalLayerCellId'),
                    'precellref': nbiot_data.get('eutranCellRef', '').split('=')[-1] if (nbiot_data.get('eutranCellRef', None) is not None) else '',
                    # 'precellref': nbiot_data.get('eutranCellRef', '').split('=')[-1] if (nbiot_data.get('eutranCellRef', None) is not None) or
                    #                     (nbiot_data.get('eutranCellRef', '').split('=')[-1] != '') else '',
                    'fdn': n_mo
                })
        ecolumns = ['celltype', 'presite', 'precell', 'precellid', 'nbiotcelltype', 'tac', 'earfcndl', 'earfcnul', 'pci', 'precellref', 'fdn']
        df = self.df_nan_to_none(df=pd.DataFrame(temp_list)) if len(temp_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        df['cellid'] = df.precellid
        df['postcell'] = df.precell
        df_cell = self.df_enb_cell[['presite', 'precell', 'postsite', 'postcell', 'sc', 'sef', 'addcell', 'preenbid', 'enbid']].rename(
            columns={'precell': 'precellref', 'postcell': 'postcellref'})
        df = df.merge(df_cell[['presite', 'precellref', 'postsite', 'postcellref', 'addcell', 'preenbid', 'enbid']],
                      on=['presite', 'precellref'], how='left')
        # --- Add New NbIotCell for CIQ ---
        df_n = self.cix.edx.get('NbIotCell')[['nbiotcellname', 'nbiotcelltype', 'nbiottac', 'nbiotcellid', 'earfcndl',
                                              'physicallayercellid', 'enbid', 'node']]
        if df_n.shape[0] > 0:
            df_n = df_n.rename(columns={'nbiotcellname': 'postcell', 'nbiottac': 'tac', 'nbiotcellid': 'cellid', 'node': 'postsite'})
            nb_type = {'1': '1 (NBIOT_INBAND)', '2': '2 (NBIOT_GUARDBAND)', '3': '3 (NBIOT_STANDALONE)', '4': '4 (NBIOT_INBAND_NOT_SAME_PCI)'}
            earfcn_type = {'0': '-1', '': '-1', None: '-1'}
            nb_cell_map = {'Z': 'L', 'Y': 'B', 'X': 'D', 'W': 'E'}
            df_n['nbiotcelltype'] = df_n.nbiotcelltype.map(nb_type)
            df_n['earfcndl'] = df_n.earfcndl.map(earfcn_type)
            df_n[['celltype', 'addcell', 'presite', 'precell', 'precellid', 'precellref', 'fdn', 'earfcnul', 'postcellref']] = \
                df_n.apply(lambda x: pd.Series(['IOT', True, None, None, None, None, None,
                                                '-1' if x.earfcndl in ['-1', None, np.nan] else 18000 + int(float(x.earfcndl)),
                                                F'{nb_cell_map.get(x.postcell[0],"")}{x.postcell[1:]}', ]), axis=1)
            df = pd.concat([df, df_n])
            df = df.drop_duplicates().groupby(['postsite', 'cellid'], sort=False, as_index=False).head(1)
            # df = df.append(df_n).drop_duplicates().groupby(['postsite', 'cellid'], sort=False, as_index=False).head(1)
        df = df.merge(df_cell[['postsite', 'postcellref', 'sc', 'sef']], on=['postsite', 'postcellref'], how='left')
        df.loc[df.addcell.isna(), 'addcell'] = True
        self.df_enb_cell = pd.concat([self.df_enb_cell, df])
        self.df_enb_cell.reset_index(inplace=True, drop=True)
        self.df_enb_cell = self.df_enb_cell.replace({np.nan: None})

    def eNodeB_validate_cix_dcgk_data(self):
        # --- validate eNBId ---
        for index, row in self.cix.edx.get('ENodeB').iterrows():
            if self.sites.get(F'site_{row.node}'):
                mo = self.sites.get(F'site_{row.node}').find_mo_ending_with_parent_str('ENodeBFunction')
                if len(mo) > 0:
                    enbid = self.sites.get(F'site_{row.node}').site_extract_data(mo[0]).get('eNBId')
                    assert enbid == self.cix.get_site_field_data_upper(row.node, 'ENodeB', 'enbid'), \
                        F'!!! Input Error, eNBId for site {row.node} is not matching!!! '
        # --- validate physicalLayerCellId and cellId ---
        for earfcndl in self.df_enb_cell.earfcndl.loc[self.df_enb_cell.celltype.isin(['FDD', 'TDD'])].unique():
            assert self.df_enb_cell.loc[self.df_enb_cell.earfcndl == earfcndl].shape[0] == \
                   len(self.df_enb_cell.loc[self.df_enb_cell.earfcndl == earfcndl].physicallayercellid.unique()), \
                   F'!!! Input Error, physicalLayerCellId for earfcndl "{earfcndl}" is not unique !!!'
            assert self.df_enb_cell.loc[self.df_enb_cell.earfcndl == earfcndl].shape[0] == \
                   len(self.df_enb_cell.loc[self.df_enb_cell.earfcndl == earfcndl].cellid.unique()), \
                   F'!!! Input Error, cellId for earfcndl "{earfcndl}" is not unique !!!'
        # --- validate rrushared ---
        for rrushared in self.df_enb_cell.rrushared.unique():
            if rrushared is not None: assert self.df_enb_cell.loc[self.df_enb_cell.postcell == rrushared].shape[0] != 0, \
                F'!!! Input Error, i.e. RRU_shared, cell {rrushared}'

    def eNodeB_EUtraNetwork(self):
        def get_pre_cell_data(cell, field, df_cell): return df_cell[df_cell.precell == cell][field].iloc[0]
        # ---ExternalENodeBFunction, ExternalEUtranCellFDD, ExternalEUtranCellTDD & EUtranFrequency---
        temp1_list, temp2_list, temp3_list = [], [], []
        for site in self.sites:
            site = self.sites.get(site)
            mo = site.find_mo_ending_with_parent_str('ENodeBFunction')
            if len(mo) == 0: continue
            nwmo = site.find_mo_ending_with_parent_str('EUtraNetwork', mo[0])
            if len(nwmo) == 0: continue
            for xmo in site.find_mo_ending_with_parent_str('ExternalENodeBFunction', nwmo[0]):
                tmp_mo_data = site.site_extract_data(xmo)
                tmp_dict = {
                    'postsite': site.node,
                    'xid': xmo.split("=")[-1],
                    'plmn': tmp_mo_data.get('eNodeBPlmnId'),
                    'enbid': tmp_mo_data.get('eNBId'),
                    'flag': False, 'fdn': xmo,
                    'x2id': None,
                    'ipv4': None,
                    'x2fdn': None
                }
                x2mo = site.find_mo_ending_with_parent_str('TermPointToENB', xmo)
                if len(x2mo):
                    tmp_dict.update({
                        'x2fdn': x2mo[0],
                        'x2id': x2mo[0].split('=')[-1],
                        'ipv4': site.site_extract_data(x2mo[0]).get('ipAddress', '0.0.0.0')
                    })
                temp1_list.append(tmp_dict)
                for celltype in ['FDD', 'TDD']:
                    for xcellmo in site.find_mo_ending_with_parent_str(F'ExternalEUtranCell{celltype}', xmo):
                        tmp_mo_data = site.site_extract_data(xcellmo)
                        tmp_dict = {
                            'postsite': site.node,
                            'celltype': celltype,
                            'xid': xcellmo.split(',')[-2].split('=')[-1],
                            'xcellid': xcellmo.split('=')[-1],
                            'cellid': tmp_mo_data.get('localCellId'),
                            'tac': tmp_mo_data.get('tac'),
                            'pci': tmp_mo_data.get('physicalLayerCellId'),
                            'freqid': tmp_mo_data.get('eutranFrequencyRef', '=').split('=')[-1],
                            'flag': False, 'fdn': xcellmo
                        }
                        temp2_list.append(tmp_dict)
            for frqmo in site.find_mo_ending_with_parent_str('EUtranFrequency', nwmo[0]):
                tmp_dict = {
                    'postsite': site.node,
                    'freqid': frqmo.split("=")[-1],
                    'earfcndl': site.site_extract_data(frqmo).get('arfcnValueEUtranDl'),
                    'flag': False, 'fdn': frqmo
                }
                temp3_list.append(tmp_dict)
        x_col = ['postsite', 'xid', 'plmn', 'enbid', 'flag', 'fdn', 'x2id', 'ipv4', 'x2fdn']
        df_enb_ex = self.df_nan_to_none(df=pd.DataFrame(temp1_list)) if len(temp1_list) > 0 \
            else pd.DataFrame([], columns=x_col)
        xcell_col = ['postsite', 'celltype', 'xid', 'xcellid', 'cellid', 'tac', 'pci', 'freqid', 'flag', 'fdn']
        df_enb_ec = self.df_nan_to_none(df=pd.DataFrame(temp2_list)) if len(temp2_list) > 0 else (
            pd.DataFrame([], columns=xcell_col))
        freq_col = ['postsite', 'freqid', 'earfcndl', 'flag', 'fdn']
        df_enb_ef = self.df_nan_to_none(df=pd.DataFrame(temp3_list)) if len(temp3_list) > 0 else (
            pd.DataFrame([], columns=freq_col))

        # --- EUtranFreqRelation & EUtranCellRelation ---
        temp1_list, temp2_list = [], []
        att_dict = {'creprio': 'cellReselectionPriority', 'cprio': 'connectedModeMobilityPrio', 'vprio': 'voicePrio',
                    'thhigh': 'threshXHigh', 'thlow': 'threshXLow'}
        for _, row in self.df_enb_cell.iterrows():
            if row.fdn is None: continue
            site = self.sites.get(F'site_{row.presite}')
            for rel_mo in site.find_mo_ending_with_parent_str('EUtranFreqRelation', row.fdn):
                rel_data = site.site_extract_data(rel_mo)
                precell = rel_mo.split(',')[-2].split("=")[-1]
                relid = rel_mo.split("=")[-1]
                tmp_dict = {
                    'presite': site.node,
                    'precell': precell,
                    'relid': relid,
                    'freqid': rel_data.get('eutranFrequencyRef', 'EutranFrequencyRef').split('=')[-1],
                    'flag': False, 'fdn': rel_mo
                }
                for att in att_dict.keys(): tmp_dict.update({att: rel_data.get(att_dict.get(att))})
                temp1_list.append(tmp_dict)
                for cellrel_mo in site.find_mo_ending_with_parent_str('EUtranCellRelation', rel_mo):
                    cellrel_data = site.site_extract_data(cellrel_mo)
                    tmp_dict = {
                        'presite': site.node,
                        'precell': precell,
                        'relid': relid,
                        'crelid': cellrel_mo.split("=")[-1],
                        'israllowed': cellrel_data.get('isRemoveAllowed'),
                        'scell': cellrel_data.get('sCellCandidate'),
                        'xid': cellrel_data.get('neighborCellRef').split(",")[-2].split("=")[-1],
                        'xcellid': cellrel_data.get('neighborCellRef').split("=")[-1],
                        'celltype': cellrel_data.get('neighborCellRef').split(',')[-1].split('=')[0][-3:],
                        'flag': False, 'fdn': cellrel_mo
                    }
                    temp2_list.append(tmp_dict)
        rel_col = ['presite', 'precell', 'relid', 'freqid', 'flag', 'fdn', 'rprio', 'cprio', 'vprio', 'thhigh', 'thlow']
        df_enb_er = self.df_nan_to_none(df=pd.DataFrame(temp1_list)) if len(temp1_list) > 0 \
            else pd.DataFrame([], columns=rel_col)
        cellrel_col = ['presite', 'precell', 'relid', 'crelid', 'israllowed', 'scell', 'flag', 'fdn', 'xid', 'xcellid', 'celltype']
        df_enb_ee = self.df_nan_to_none(df=pd.DataFrame(temp2_list)) if len(temp2_list) > 0 \
            else pd.DataFrame([], columns=cellrel_col)

        # --- Update Existing Relations ---
        # if df_enb_ex.shape[0] > 0:
        df_enb_ex['plmn'] = df_enb_ex.plmn.apply(json.dumps)
        df_enb_ec = df_enb_ec.merge(df_enb_ex[['postsite', 'xid', 'enbid', 'plmn']], on=['postsite', 'xid'], how='left')
        df_enb_ec = df_enb_ec.merge(df_enb_ef[['postsite', 'freqid', 'earfcndl']], on=['postsite', 'freqid'], how='left')
        df_enb_er = df_enb_er.merge(self.df_enb_cell[['presite', 'precell', 'postsite', 'postcell']], on=['presite', 'precell'], how='left')
        df_enb_er = df_enb_er.merge(df_enb_ef[['postsite', 'freqid', 'earfcndl']].rename(columns={'postsite': 'presite'}),
                                    on=['presite', 'freqid'], how='left')
        df_enb_ee = df_enb_ee.merge(df_enb_ec[['postsite', 'xid', 'xcellid', 'plmn', 'enbid', 'cellid']].rename(columns={'postsite': 'presite'}),
                                    on=['presite', 'xid', 'xcellid'], how='left')
        df_enb_ee = df_enb_ee.merge(df_enb_er[['presite', 'precell', 'relid', 'postsite', 'postcell', 'earfcndl']],
                                    on=['presite', 'precell', 'relid'], how='left')

        # --- Remove Deleted Cell & there Relations ---
        df_enb_ee = df_enb_ee.loc[(df_enb_ee.xcellid.isin(list(filter(None, self.df_enb_cell['precell'].unique())))) | ~(df_enb_ee.cellid.isnull())]
        df_enb_ee.reset_index(inplace=True, drop=True)
        # --- Update post enbid & cellid of co-site cell relations ---
        df_enb_ee.loc[df_enb_ee.cellid.isna(), 'plmn'] = df_enb_ee.loc[df_enb_ee.cellid.isna()]['xcellid'].map(
            lambda x: json.dumps(copy.deepcopy(PlmnId)))
        df_enb_ee.loc[df_enb_ee.enbid.isna(), 'enbid'] = df_enb_ee.loc[df_enb_ee.enbid.isna()]['xcellid'].map(
            lambda x: get_pre_cell_data(x, 'preenbid', self.df_enb_cell))
        df_enb_ee.loc[df_enb_ee.cellid.isna(), 'cellid'] = df_enb_ee.loc[df_enb_ee.cellid.isna()]['xcellid'].map(
            lambda x: get_pre_cell_data(x, 'precellid', self.df_enb_cell))
        # --- Remove existing External FDD/TDD based on migration ---
        df_enb_ec = df_enb_ec.merge(self.df_enb_cell[['preenbid', 'precellid', 'postsite']].rename(
            columns={'preenbid': 'enbid', 'precellid': 'cellid'}), on=['enbid', 'cellid'], how='left', suffixes=('', '_t'))
        df_enb_ec = df_enb_ec.loc[df_enb_ec.postsite != df_enb_ec.postsite_t].reset_index(inplace=False, drop=True)
        df_enb_ec.drop(['postsite_t'], axis=1, inplace=True)
        # --- Remove ExternalENodeBFunction & External FDD/TDD if node is getting deleted ---
        temp1_list = set(list(self.df_enb_cell.preenbid.unique())) - set(list(self.df_enb_cell.enbid.unique()))
        df_enb_ex = df_enb_ex.loc[~df_enb_ex.enbid.isin(temp1_list)].reset_index(inplace=False, drop=True)
        df_enb_ec = df_enb_ec.loc[~df_enb_ec.enbid.isin(temp1_list)].reset_index(inplace=False, drop=True)
        # --- Update existing Cell Relations, enbid, cellid based on migration ---
        df_enb_ee = df_enb_ee.merge(self.df_enb_cell[['preenbid', 'precellid', 'enbid', 'cellid']].rename(
            columns={'preenbid': 'enbid', 'precellid': 'cellid', 'enbid': 'postenbid', 'cellid': 'postcellid'}),
            on=['enbid', 'cellid'], how='left', suffixes=('', '_t'))
        if df_enb_ee.loc[(~df_enb_ee.postenbid.isna())].shape[0] > 0:
            df_enb_ee.loc[(~df_enb_ee.postenbid.isna()), ['enbid']] = df_enb_ee.loc[
                (~df_enb_ee.postenbid.isna()), ['postenbid']].apply(lambda x: x.postenbid, axis=1)
            df_enb_ee.loc[(~df_enb_ee.postcellid.isna()), ['cellid']] = df_enb_ee.loc[
                (~df_enb_ee.postcellid.isna()), ['postcellid']].apply(lambda x: x.postcellid, axis=1)
        df_enb_ee.drop(['postcellid', 'postenbid'], axis=1, inplace=True)

        # --- Addition of New Relations ---
        df_n = self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD', 'TDD']), [
            'postsite', 'postcell', 'celltype', 'earfcndl', 'enbid', 'cellid', 'tac',
            'physicallayercellid']].rename(columns={'physicallayercellid': 'pci'})
        if df_n.shape[0] > 0:
            df_n[['flag', 'fdn', 'x2fdn', 'plmn', 'xid', 'x2id', 'xcellid', 'ipv4', 'freqid', 'israllowed', 'scell']] = (
                df_n.apply(lambda x: pd.Series([
                    True, None, None, json.dumps(PlmnId), F'{PlmnId["mcc"]}{PlmnId["mnc"]}-{x.enbid}',
                    F'{PlmnId["mcc"]}{PlmnId["mnc"]}-{x.enbid}', F'{PlmnId["mcc"]}{PlmnId["mnc"]}-{x.enbid}-{x.cellid}',
                    F'{self.enodeb[x.postsite].get("lte_ip", "0.0.0.0")}', F'{x.earfcndl}', 'false', '2 (AUTO)']), axis=1)
            )

            # --- Addition of ExternalENodeBFunction & External FDD/TDD ---
            df_t = df_n[['postsite', 'flag']].groupby(['postsite', 'flag'], as_index=False).head(1)
            df_t = df_t.merge(df_n, on='flag', suffixes=('', '_t'))
            df_t = df_t.loc[df_t.postsite != df_t.postsite_t]
            df_enb_ex = pd.concat([df_enb_ex, df_t[['postsite', 'xid', 'plmn', 'enbid', 'flag', 'fdn', 'x2id', 'ipv4', 'x2fdn']]])
            df_enb_ex = df_enb_ex.drop_duplicates().groupby(['postsite', 'plmn', 'enbid'], sort=False,
                                                            as_index=False).head(1).reset_index(inplace=False, drop=True)
            df_enb_ec = pd.concat([df_enb_ec, df_t[['postsite', 'celltype', 'xid', 'xcellid', 'cellid', 'tac', 'pci', 'freqid',
                                                    'flag', 'fdn', 'enbid', 'plmn', 'earfcndl']]])
            df_enb_ec = df_enb_ec.drop_duplicates().groupby(['postsite', 'plmn', 'enbid', 'cellid'], sort=False,
                                                            as_index=False).head(1).reset_index(inplace=False, drop=True)
            # --- Addition of EUtranCellRelation ---
            df_t = df_n[['postsite', 'postcell', 'flag']].groupby(['postsite', 'postcell', 'flag'], as_index=False).head(1)
            df_t = df_t.merge(df_n, on='flag', suffixes=('', '_t'))
            df_t = df_t.loc[df_t.postcell != df_t.postcell_t]
            df_t = df_t[['xcellid', 'israllowed', 'scell', 'xid', 'celltype', 'flag', 'fdn', 'plmn', 'enbid', 'cellid', 'postsite', 'postcell',
                         'earfcndl']].rename(columns={'xcellid': 'crelid'})
            df_enb_ee = pd.concat([df_enb_ee, df_t])
            df_enb_ee = df_enb_ee.drop_duplicates().groupby(['postsite', 'postcell', 'plmn', 'enbid', 'cellid',
                                                             'earfcndl', 'celltype'], sort=False, as_index=False).head(1)
            df_enb_ee.reset_index(inplace=True, drop=True)
            del df_t, df_n

        # --- Addition of EUtranFreqRelation ---
        if self.cix.edx.get('EUtranFreqRelation').shape[0] > 0:
            df_n = self.cix.edx.get('EUtranFreqRelation').rename(
                columns={'eutrancellfddid': 'postcell', 'eutranfreqrelationid': 'relid', 'cellreselectionpriority': 'creprio',
                         'connectedmodemobilityprio': 'cprio', 'voiceprio': 'vprio', 'threshxhigh': 'thhigh', 'threshxlow': 'thlow',
                         'arfcnvalueeutrandl': 'earfcndl', 'externaleutranfreqid': 'freqid'})
            df_n[['presite', 'precell', 'fdn', 'flag']] = df_n.apply(lambda x: pd.Series([None, None, None, True]), axis=1)
            df_n = df_n.merge(self.df_enb_cell[['postcell', 'postsite']], on=['postcell'], how='left')
            df_n = df_n.loc[~df_n.postsite.isna()]
            df_enb_er = pd.concat([df_enb_er, df_n])
        # Addition Based on Cell for All earfcn
        df_t = self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD', 'TDD']), ['postsite', 'postcell']]
        df_t['flag'] = True
        df_t1 = self.df_enb_cell.loc[self.df_enb_cell.celltype.isin(['FDD', 'TDD']), ['earfcndl']].drop_duplicates().groupby(
            ['earfcndl'], sort=False, as_index=False).head(1)
        if df_t1.shape[0] > 0:
            df_t1[['flag', 'fdn', 'presite', 'precell', 'relid', 'freqid', 'creprio', 'cprio', 'vprio', 'thhigh', 'thlow']] = \
                df_t1.apply(lambda x: pd.Series([True, None, None, None, F'{x.earfcndl}', F'{x.earfcndl}',  F'2', F'7', F'6', F'8', F'0']), axis=1)
            df_t = df_t.merge(df_t1, on='flag', suffixes=('', '_t'))
            df_enb_er = pd.concat([df_enb_er, df_t])
        df_enb_er = df_enb_er.drop_duplicates().groupby(['postsite', 'postcell', 'earfcndl'], sort=False,
                                                        as_index=False).head(1).reset_index(inplace=False, drop=True)

        # --- Addition of External FDD/TDD based on migrations and Logs
        temp_list = ['postsite', 'celltype', 'plmn', 'enbid', 'cellid', 'earfcndl']
        df_enb_ee.drop(['xid', 'xcellid'], axis=1, inplace=True)
        df_enb_ee = df_enb_ee.merge(df_enb_ec[['xid', 'xcellid'] + temp_list], on=temp_list, how='left')
        for _, row in df_enb_ee.loc[df_enb_ee.xcellid.isna()].drop_duplicates().groupby(temp_list, as_index=False).head(1).iterrows():
            if row.enbid == self.df_enb_cell.loc[self.df_enb_cell.postsite == row.postsite].enbid.iloc[0]: continue
            df_t = df_enb_ec.loc[(df_enb_ec.plmn == row.plmn) & (df_enb_ec.celltype == row.celltype) &
                                 (df_enb_ec.enbid == row.enbid) & (df_enb_ec.cellid == row.cellid) & (df_enb_ec.earfcndl == row.earfcndl)].head(1)
            if df_t.shape[0] == 0: continue
            df_t[['postsite', 'flag', 'fdn']] = df_t.apply(lambda x: pd.Series([row.postsite, True, None]), axis=1)
            df_enb_ec = pd.concat([df_enb_ec, df_t]).reset_index(inplace=False, drop=True)
        # --- Addition of ExternalENodeBFunction based on migrations and Logs
        df_enb_ec.drop(['xid'], axis=1, inplace=True)
        df_enb_ec = df_enb_ec.merge(df_enb_ex[['postsite', 'plmn', 'enbid', 'xid']], on=['postsite', 'plmn', 'enbid'], how='left')
        for _, row in df_enb_ec.loc[df_enb_ec.xid.isna()].drop_duplicates().groupby(['postsite', 'plmn', 'enbid'], as_index=False).head(1).iterrows():
            df_t = df_enb_ex.loc[(df_enb_ex.plmn == row.plmn) & (df_enb_ex.plmn == row.plmn) & (df_enb_ex.enbid == row.enbid)].head(1)
            if df_t.shape[0] == 0: continue
            df_t[['postsite', 'flag', 'fdn', 'x2fdn']] = df_t.apply(lambda x: pd.Series([row.postsite, True, None, None]), axis=1)
            df_enb_ex = pd.concat([df_enb_ex, df_t]).reset_index(inplace=False, drop=True)

        # --- Addition of EUtranFrequency based on migrations and Logs
        df_t = pd.concat([df_enb_ec[['postsite', 'freqid', 'earfcndl']],
                          df_enb_er[['postsite', 'freqid', 'earfcndl']]]).reset_index(inplace=False, drop=True)
        df_t['flag'] = True
        df_enb_ef = pd.concat([df_enb_ef, df_t])
        df_enb_ef = df_enb_ef.drop_duplicates().groupby(['postsite', 'earfcndl'], sort=False,
                                                        as_index=False).head(1).reset_index(inplace=False, drop=True)
        # --- Update IDs for to EUtranFrequency remove dublicate IDs
        df_enb_ef = df_enb_ef.loc[~(df_enb_ef.postsite.isna() | df_enb_ef.freqid.isna() | df_enb_ef.earfcndl.isna())]
        df_enb_ef = df_enb_ef.drop_duplicates().groupby(['postsite', 'earfcndl'], sort=False,
                                                        as_index=False).head(1).reset_index(inplace=False, drop=True)
        df_enb_ef['mo_count'] = df_enb_ef.groupby(['postsite', 'freqid']).cumcount() + 1
        df_enb_ef.loc[df_enb_ef.mo_count > 1, 'freqid'] = df_enb_ef.loc[df_enb_ef.mo_count > 1, ['freqid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_ef = df_enb_ef.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # --- Update IDs for to EUtranFreqRelation remove dublicate IDs
        df_enb_er.drop(['freqid'], axis=1, inplace=True)
        df_enb_er = df_enb_er.merge(df_enb_ef[['postsite', 'freqid', 'earfcndl']], on=['postsite', 'earfcndl'], how='left')
        df_enb_er = df_enb_er.loc[~(df_enb_er.postsite.isna() | df_enb_er.postcell.isna() | df_enb_er.relid.isna() |
                                    df_enb_er.freqid.isna() | df_enb_er.earfcndl.isna())]
        df_enb_er = df_enb_er.drop_duplicates().groupby(['postsite', 'postcell', 'earfcndl'], sort=False,
                                                        as_index=False).head(1).reset_index(inplace=False, drop=True)
        df_enb_er['mo_count'] = df_enb_er.groupby(['postsite', 'postcell', 'relid']).cumcount() + 1
        df_enb_er.loc[df_enb_er.mo_count > 1, 'relid'] = (
            df_enb_er.loc[df_enb_er.mo_count > 1, ['relid', 'mo_count']].apply(lambda x: '_'.join(x.astype(str)), axis=1))
        df_enb_er = df_enb_er.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # --- Update IDs for to ExternalENodeBFunction remove dublicate IDs
        df_enb_ex = df_enb_ex.loc[~(df_enb_ex.postsite.isna() | df_enb_ex.xid.isna() | df_enb_ex.plmn.isna() | df_enb_ex.enbid.isna())]
        df_enb_ex = df_enb_ex.drop_duplicates().groupby(['postsite', 'plmn', 'enbid'], sort=False,
                                                        as_index=False).head(1).reset_index(inplace=False, drop=True)
        df_enb_ex['mo_count'] = df_enb_ex.groupby(['postsite', 'xid']).cumcount() + 1
        df_enb_ex.loc[df_enb_ex.mo_count > 1, 'xid'] = df_enb_ex.loc[df_enb_ex.mo_count > 1, ['xid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_ex = df_enb_ex.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # --- Update IDs for to External FDD/TDD remove dublicate IDs
        df_enb_ec.drop(['xid', 'freqid'], axis=1, inplace=True)
        df_enb_ec = df_enb_ec.merge(df_enb_ex[['postsite', 'xid', 'plmn', 'enbid']], on=['postsite', 'plmn', 'enbid'], how='left')
        df_enb_ec = df_enb_ec.merge(df_enb_ef[['postsite', 'freqid', 'earfcndl']], on=['postsite', 'earfcndl'], how='left')
        df_enb_ec = df_enb_ec.loc[~(df_enb_ec.postsite.isna() | df_enb_ec.xid.isna() | df_enb_ec.xcellid.isna() |
                                    df_enb_ec.freqid.isna() | df_enb_ec.earfcndl.isna())]
        df_enb_ec = df_enb_ec.drop_duplicates().groupby(['postsite', 'celltype', 'plmn', 'enbid', 'cellid', 'earfcndl'], sort=False,
                                                        as_index=False).head(1).reset_index(inplace=False, drop=True)
        df_enb_ec['mo_count'] = df_enb_ec.groupby(['postsite', 'xid', 'xcellid']).cumcount() + 1
        df_enb_ec.loc[df_enb_ec.mo_count > 1, 'xcellid'] = df_enb_ec.loc[df_enb_ec.mo_count > 1, ['xcellid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_ec = df_enb_ec.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # --- Update IDs for to EUtranCellRelation israllowed dublicate IDs and create Final DataFrame
        df_enb_ee.loc[(df_enb_ee.enbid.isin(list(filter(None, self.df_enb_cell['enbid'].unique())))), 'crelid'] = \
            df_enb_ee.loc[(df_enb_ee.enbid.isin(list(filter(None, self.df_enb_cell['enbid'].unique())))), ['enbid', 'cellid']].apply(
                lambda x: F'{PlmnId["mcc"]}{PlmnId["mnc"]}-' + '-'.join(x.astype(str)), axis=1)

        df_enb_ee.drop(['xid', 'xcellid', 'relid'], axis=1, inplace=True)
        df_enb_ee = df_enb_ee.merge(df_enb_ec[['xid', 'xcellid', 'postsite', 'celltype', 'plmn', 'enbid', 'cellid', 'earfcndl']],
                                    on=['postsite', 'celltype', 'plmn', 'enbid', 'cellid', 'earfcndl'], how='left')
        df_enb_ee = df_enb_ee.merge(df_enb_er[['postsite', 'postcell', 'relid', 'earfcndl']], on=['postsite', 'postcell', 'earfcndl'], how='left')
        df_enb_ee = df_enb_ee.merge(self.df_enb_cell[['enbid', 'cellid', 'postcell']].rename(columns={'postcell': 't_postcell'}),
                                    on=['enbid', 'cellid'], how='left')
        df_enb_ee.loc[(~df_enb_ee.t_postcell.isna()), ['scell']] = df_enb_ee.loc[(~df_enb_ee.t_postcell.isna()), ['postcell', 't_postcell']].apply(
            lambda x: '1 (ALLOWED)' if x.postcell[-2] == x.t_postcell[-2] else '2 (AUTO)', axis=1)
        df_enb_ee.loc[(~df_enb_ee.t_postcell.isna()), 'israllowed'] = 'false'
        df_enb_ee.loc[df_enb_ee.xid.isna(), 'xid'] = '1'
        df_enb_ee.loc[df_enb_ee.xcellid.isna(), 'xcellid'] = df_enb_ee.loc[df_enb_ee.xcellid.isna(), ['t_postcell']].apply(
            lambda x: x.t_postcell, axis=1)
        df_enb_ee = df_enb_ee.loc[~(df_enb_ee.postsite.isna() | df_enb_ee.postcell.isna() | df_enb_ee.relid.isna() | df_enb_ee.crelid.isna() |
                                    df_enb_ee.xid.isna() | df_enb_ee.xcellid.isna())]
        df_enb_ee = df_enb_ee.drop_duplicates().groupby(['postsite', 'postcell', 'celltype', 'plmn', 'enbid', 'cellid', 'earfcndl'],
                                                        sort=False, as_index=False).head(1).reset_index(inplace=False, drop=True)
        df_enb_ee['mo_count'] = df_enb_ee.groupby(['postsite', 'postcell', 'relid', 'crelid']).cumcount() + 1
        df_enb_ee.loc[df_enb_ee.mo_count > 1, 'crelid'] = df_enb_ee.loc[df_enb_ee.mo_count > 1, ['crelid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        
        # Update neighborCellRef for Cell Relations
        if df_enb_ee.shape[0] > 0:
            df_enb_ee['extcell'] = df_enb_ee[['xid', 'xcellid', 'celltype', 'postsite']].apply(
                lambda x: F'ENodeBFunction=1,EUtraNetwork={self.enodeb[x.postsite]["EUtraNetwork"]},'
                          F'ExternalENodeBFunction={x.xid},ExternalEUtranCell{x.celltype}={x.xcellid}', axis=1)
            df_enb_ee.loc[df_enb_ee.xid == '1', 'extcell'] = df_enb_ee.loc[df_enb_ee.xid == '1', ['xcellid', 'celltype']].apply(
                lambda x: F'ENodeBFunction=1,EUtranCell{x.celltype}={x.xcellid}', axis=1)
        else:
            df_enb_ee['extcell'] = None
            df_enb_ee['extcell'] = None
        
        # Update EUtranCellRelation for isRemoveAllowed and sCellCandidate for co-site Cell Relations based on CIQ
        df_enb_ee = df_enb_ee.merge(self.cix.edx.get('CA'), on=['postcell', 'crelid'], how='left')
        df_enb_ee.loc[(~df_enb_ee.scell_ciq.isna()), 'scell'] = df_enb_ee.loc[(~df_enb_ee.scell_ciq.isna()), ['scell_ciq']].apply(
            lambda x: x.scell_ciq, axis=1)
        df_enb_ee.loc[(~df_enb_ee.remove_ciq.isna()), 'israllowed'] = df_enb_ee.loc[(~df_enb_ee.remove_ciq.isna()), ['remove_ciq']].apply(
            lambda x: x.remove_ciq, axis=1)
        df_enb_ee = df_enb_ee.replace({np.nan: None}).drop(['mo_count', 'scell_ciq', 'scell_ciq', 't_postcell', 'remove_ciq'], axis=1, inplace=False)

        # df_enb_ee.loc[df_enb_ee.t_postcell.isin(self.df_enb_cell.loc[self.df_enb_cell.addcell & self.df_enb_cell.celltype.isin(['FDD', 'TDD']) &
        #                                                              (~self.df_enb_cell.precell.isna())].postcell.unique()), 'flag'] = True
        #
        df_enb_ex['plmn'] = df_enb_ex.plmn.apply(json.loads)
        self.df_enb_ef = df_enb_ef.copy()
        self.df_enb_ex = df_enb_ex.copy()
        self.df_enb_ec = df_enb_ec.copy()
        self.df_enb_er = df_enb_er.copy()
        self.df_enb_ee = df_enb_ee.copy()

    def eNodeB_GUtraNetwork(self):
        temp_list, temp1_list, temp2_list = [], [], []
        for site in self.sites:
            site = self.sites.get(site)
            mo = site.find_mo_ending_with_parent_str('ENodeBFunction')
            if len(mo) == 0: continue
            nwmo = site.find_mo_ending_with_parent_str('GUtraNetwork', mo[0])
            if len(nwmo) == 0: continue
            node = site.node
            # GUtranSyncSignalFrequency
            for mo in site.find_mo_ending_with_parent_str('GUtranSyncSignalFrequency', nwmo[0]):
                mo_data = site.site_extract_data(mo)
                temp_list.append({'postsite': node, 'freqid': mo.split("=")[-1], 'arfcn': mo_data.get('arfcn'),
                                  'smtcOffset': mo_data.get('smtcOffset'), 'smtcScs': mo_data.get('smtcScs'),
                                  'smtcPeriodicity': mo_data.get('smtcPeriodicity'), 'smtcDuration': mo_data.get('smtcDuration'),
                                  'flag': False, 'fdn': mo})
            # ExternalGNodeBFunction & TermPointToGNB, ExternalGUtranCell
            for xmo in site.find_mo_ending_with_parent_str('ExternalGNodeBFunction', nwmo[0]):
                mo_data = site.site_extract_data(xmo)
                if len(site.find_mo_ending_with_parent_str('TermPointToGNB', xmo)) > 0:
                    mot = site.find_mo_ending_with_parent_str('TermPointToGNB', xmo)[0]
                    mot_data = site.site_extract_data(mot)
                else: mot, mot_data = None, None
                temp1_list.append({'postsite': node, 'xid': xmo.split("=")[-1], 'gnbid': mo_data.get('gNodeBId'),
                                   'gnblen': mo_data.get('gNodeBIdLength'),
                                   'plmn': mo_data.get('gNodeBPlmnId'), 'flag': False, 'fdn': xmo,
                                   'x2id': None if mot is None else mot.split("=")[-1],
                                   'ipv4': None if mot is None else mot_data.get('ipAddress'),
                                   'xt_ipv6': None if mot is None else mot_data.get('ipv6Address'),
                                   'xt_domain': None if mot is None else mot_data.get('domainName'), 'x2fdn': mot})
                for mo in site.find_mo_ending_with_parent_str('ExternalGUtranCell', xmo):
                    mo_data = site.site_extract_data(mo)
                    temp2_list.append({
                        'postsite': node, 'xid': mo.split(",")[-2].split("=")[-1], 'xcellid': mo.split("=")[-1],
                        'cellid': mo_data.get('localCellId'),
                        'pci': int(float(mo_data.get('physicalLayerCellIdGroup'))) * 3 + int(float(mo_data.get('physicalLayerSubCellId'))),
                        'freqid': mo_data.get('gUtranSyncSignalFrequencyRef').split("=")[-1], 'israllowed': mo_data.get('isRemoveAllowed'),
                        'abssub': mo_data.get('absSubFrameOffset'), 'abstime': mo_data.get('absTimeOffset'), 'flag': False, 'fdn': mo
                    })

        ecolumns = ['postsite', 'freqid', 'arfcn', 'smtcScs', 'smtcPeriodicity', 'smtcOffset', 'smtcDuration', 'flag', 'fdn']
        df_enb_nf = self.df_nan_to_none(df=pd.DataFrame(temp_list)) if len(temp_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        ecolumns = ['postsite', 'xid', 'gnbid', 'gnblen', 'plmn', 'flag', 'fdn', 'x2id', 'ipv4', 'xt_ipv6', 'xt_domain', 'x2fdn']
        df_enb_nx = self.df_nan_to_none(df=pd.DataFrame(temp1_list)) if len(temp1_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        ecolumns = ['postsite', 'xid', 'xcellid', 'pci', 'cellid', 'freqid', 'israllowed', 'abssub', 'abstime', 'flag', 'fdn']
        df_enb_nc = self.df_nan_to_none(df=pd.DataFrame(temp2_list)) if len(temp2_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)

        # GUtranFreqRelation, GUtranCellRelation
        temp1_list, temp2_list = [], []
        for _, row in self.df_enb_cell.iterrows():
            if row.fdn is None: continue
            site = self.sites.get(F'site_{row.presite}')
            precell = row.precell
            node = site.node
            for rel_mo in site.find_mo_ending_with_parent_str('GUtranFreqRelation', row.fdn):
                rel_data = site.site_extract_data(rel_mo)
                relid = rel_mo.split("=")[-1]
                temp1_list.append({'presite': node, 'precell': precell, 'relid': relid,
                                   'creprio': rel_data.get('cellReselectionPriority'),
                                   'freqid': rel_data.get('gUtranSyncSignalFrequencyRef').split("=")[-1],
                                   'flag': False, 'fdn': rel_mo})
                for cellrel_mo in site.find_mo_ending_with_parent_str('GUtranCellRelation', rel_mo):
                    mo_data = site.site_extract_data(cellrel_mo)
                    temp2_list.append({'presite': node, 'precell': precell, 'relid': relid, 'crelid': cellrel_mo.split("=")[-1],
                                       'israllowed': mo_data.get('isRemoveAllowed'),
                                       'xid': mo_data.get('neighborCellRef').split(",")[-2].split("=")[-1],
                                       'xcellid': mo_data.get('neighborCellRef').split("=")[-1],
                                       'flag': False, 'fdn': cellrel_mo})

        ecolumns = ['presite', 'precell', 'relid', 'creprio', 'freqid', 'flag', 'fdn']
        df_enb_nr = self.df_nan_to_none(df=pd.DataFrame(temp1_list)) if len(temp1_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        ecolumns = ['presite', 'precell', 'relid', 'crelid', 'israllowed', 'xid', 'xcellid', 'flag', 'fdn']
        df_enb_ne = self.df_nan_to_none(df=pd.DataFrame(temp2_list)) if len(temp2_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)

        # Update Existing Data
        sfrq_par_list = ['arfcn', 'smtcScs', 'smtcPeriodicity', 'smtcOffset', 'smtcDuration']
        # if df_enb_nx.shape[0] > 0:
        df_enb_nx['plmn'] = df_enb_nx.plmn.apply(json.dumps)
        df_enb_nc = df_enb_nc.merge(df_enb_nf[['postsite', 'freqid'] + sfrq_par_list], on=['postsite', 'freqid'], how='left')
        df_enb_nc = df_enb_nc.merge(df_enb_nx[['postsite', 'xid', 'plmn', 'gnbid']], on=['postsite', 'xid'], how='left')
        df_enb_nr = df_enb_nr.merge(df_enb_nf[['postsite', 'freqid'] + sfrq_par_list].rename(columns={'postsite': 'presite'}),
                                    on=['presite', 'freqid'], how='left')
        df_enb_nr = df_enb_nr.merge(self.df_enb_cell[['presite', 'precell', 'postsite', 'postcell']], on=['presite', 'precell'], how='left')
        df_enb_ne = df_enb_ne.merge(df_enb_nr[['presite', 'precell', 'postsite', 'postcell', 'relid'] + sfrq_par_list],
                                    on=['presite', 'precell', 'relid'], how='left')
        df_enb_ne = df_enb_ne.merge(df_enb_nc[['postsite', 'xid', 'xcellid', 'plmn', 'gnbid', 'cellid']].rename(
            columns={'postsite': 'presite'}), on=['presite', 'xid', 'xcellid'], how='left')
        # New Relation Addition need to be added here
        # Add & Update Beased on Migration and New Addition
        # Add ExternalGUtranCell
        df_enb_ne.drop(['xid', 'xcellid'], axis=1, inplace=True)
        df_enb_ne = df_enb_ne.merge(df_enb_nc[['postsite', 'xid', 'xcellid', 'plmn', 'gnbid', 'cellid']],
                                    on=['postsite', 'plmn', 'gnbid', 'cellid'], how='left')
        for _, row in df_enb_ne.loc[df_enb_ne.xcellid.isna()].drop_duplicates().groupby(['postsite', 'plmn', 'gnbid', 'cellid'],
                                                                                        as_index=False).head(1).iterrows():
            df_n = df_enb_nc.loc[(df_enb_nc.plmn == row.plmn) & (df_enb_nc.gnbid == row.gnbid) & (df_enb_nc.cellid == row.cellid)].head(1)
            if df_n.shape[0] == 0: continue
            df_n[['postsite', 'flag', 'fdn']] = df_n.apply(lambda x: pd.Series([row.postsite, True, None]), axis=1)
            df_enb_nc = pd.concat([df_enb_nc, df_n]).reset_index(inplace=False, drop=True)

        # Add ExternalGNodeBFunction
        df_enb_nc.drop(['xid'], axis=1, inplace=True)
        df_enb_nc = df_enb_nc.merge(df_enb_nx[['postsite', 'xid', 'plmn', 'gnbid']], on=['postsite', 'plmn', 'gnbid'], how='left')
        for _, row in df_enb_nc.loc[df_enb_nc.xid.isna()].drop_duplicates().groupby(['postsite', 'plmn', 'gnbid'], as_index=False).head(1).iterrows():
            df_n = df_enb_nx.loc[(df_enb_nx.plmn == row.plmn) & (df_enb_nx.gnbid == row.gnbid)].head(1)
            if df_n.shape[0] == 0: continue
            df_n[['postsite', 'flag', 'fdn', 'x2fdn']] = df_n.apply(lambda x: pd.Series([row.postsite, True, None, None]), axis=1)
            df_enb_nx = pd.concat([df_enb_nx, df_n]).reset_index(inplace=False, drop=True)

        # Add GUtranSyncSignalFrequency
        df_n = pd.concat([df_enb_nr[['postsite'] + sfrq_par_list], df_enb_nc[['postsite'] + sfrq_par_list]])
        # df_n = df_enb_nr[['postsite'] + sfrq_par_list].append(df_enb_nc[['postsite'] + sfrq_par_list])
        if df_n.shape[0] > 0:
            df_n = df_n.drop_duplicates().groupby(['postsite'] + sfrq_par_list, sort=False, as_index=False).head(1)
            df_n[['freqid', 'flag', 'fdn']] = df_n.apply(lambda x: pd.Series([F'{x.arfcn}-{x.smtcScs}', True, None]), axis=1)
            df_enb_nf = pd.concat([df_enb_nf, df_n])

        # Update GUtranSyncSignalFrequency
        df_enb_nf = df_enb_nf.loc[~(df_enb_nf.postsite.isna() | df_enb_nf.arfcn.isna() | df_enb_nf.smtcScs.isna() |
                                    df_enb_nf.smtcPeriodicity.isna() | df_enb_nf.smtcOffset.isna() | df_enb_nf.smtcDuration.isna())]
        df_enb_nf = df_enb_nf.drop_duplicates().groupby(['postsite'] + sfrq_par_list, sort=False, as_index=False).head(1).reset_index(
            drop=True, inplace=False)
        df_enb_nf['mo_count'] = df_enb_nf.groupby(['postsite', 'freqid']).cumcount() + 1
        df_enb_nf.loc[df_enb_nf.mo_count > 1, 'freqid'] = df_enb_nf.loc[df_enb_nf.mo_count > 1, ['freqid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_nf = df_enb_nf.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # Update ExternalGNodeBFunction
        df_enb_nx = df_enb_nx.loc[~(df_enb_nx.postsite.isna() | df_enb_nx.xid.isna() | df_enb_nx.plmn.isna() | df_enb_nx.gnbid.isna())]
        df_enb_nx = df_enb_nx.drop_duplicates().groupby(['postsite', 'plmn', 'gnbid'], sort=False, as_index=False).head(1).reset_index(
            inplace=False, drop=True)
        df_enb_nx['mo_count'] = df_enb_nx.groupby(['postsite', 'xid']).cumcount() + 1
        df_enb_nx.loc[df_enb_nx.mo_count > 1, 'xid'] = df_enb_nx.loc[df_enb_nx.mo_count > 1, ['xid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_nx = df_enb_nx.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # Update ExternalGUtranCell
        df_enb_nc.drop(['xid', 'freqid'], axis=1, inplace=True)
        df_enb_nc = df_enb_nc.merge(df_enb_nx[['postsite', 'xid', 'plmn', 'gnbid']], on=['postsite', 'plmn', 'gnbid'], how='left')
        df_enb_nc = df_enb_nc.merge(df_enb_nf[['postsite', 'freqid'] + sfrq_par_list], on=['postsite'] + sfrq_par_list, how='left')
        df_enb_nc = df_enb_nc.loc[~(df_enb_nc.postsite.isna() | df_enb_nc.xid.isna() | df_enb_nc.xcellid.isna() | df_enb_nc.freqid.isna())]
        df_enb_nc = df_enb_nc.drop_duplicates().groupby(['postsite', 'plmn', 'gnbid', 'cellid'], sort=False, as_index=False).head(1).reset_index(
            inplace=False, drop=True)
        df_enb_nc['mo_count'] = df_enb_nc.groupby(['postsite', 'xid', 'xcellid']).cumcount() + 1
        df_enb_nc.loc[df_enb_nc.mo_count > 1, 'xcellid'] = df_enb_nc.loc[df_enb_nc.mo_count > 1, ['xcellid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_nc = df_enb_nc.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # Update GUtranFreqRelation
        df_enb_nr.drop(['freqid'], axis=1, inplace=True)
        df_enb_nr = df_enb_nr.merge(df_enb_nf[['postsite', 'freqid'] + sfrq_par_list], on=['postsite'] + sfrq_par_list, how='left')
        df_enb_nr = df_enb_nr.loc[~(df_enb_nr.postsite.isnull() | df_enb_nr.postcell.isnull() | df_enb_nr.relid.isnull() | df_enb_nr.freqid.isnull())]
        df_enb_nr = df_enb_nr.drop_duplicates().groupby(['postsite', 'postcell'] + sfrq_par_list, sort=False, as_index=False).head(1).reset_index(
            inplace=False, drop=True)
        df_enb_nr['mo_count'] = df_enb_nr.groupby(['postsite', 'postcell', 'relid']).cumcount() + 1
        df_enb_nr.loc[df_enb_nr.mo_count > 1, 'relid'] = df_enb_nr.loc[df_enb_nr.mo_count > 1, ['relid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_nr = df_enb_nr.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # Update GUtranCellRelation
        df_enb_ne.drop(['relid', 'xid', 'xcellid'], axis=1, inplace=True)
        df_enb_ne = df_enb_ne.merge(df_enb_nc[['postsite', 'xid', 'xcellid', 'plmn', 'gnbid', 'cellid']],
                                    on=['postsite', 'plmn', 'gnbid', 'cellid'], how='left')
        df_enb_ne = df_enb_ne.merge(df_enb_nr[['postsite', 'postcell', 'relid'] + sfrq_par_list],
                                    on=['postsite', 'postcell'] + sfrq_par_list, how='left')
        df_enb_ne = df_enb_ne.loc[~(df_enb_ne.postsite.isnull() | df_enb_ne.postcell.isnull() | df_enb_ne.relid.isnull() |
                                    df_enb_ne.xcellid.isnull() | df_enb_ne.xid.isnull() | df_enb_ne.xcellid.isnull())]
        df_enb_ne = df_enb_ne.drop_duplicates().groupby(['postsite', 'postcell', 'plmn', 'gnbid', 'cellid'] + sfrq_par_list, sort=False,
                                                        as_index=False).head(1).reset_index(inplace=False, drop=True)
        df_enb_ne['mo_count'] = df_enb_ne.groupby(['postsite', 'postcell', 'relid', 'crelid']).cumcount() + 1
        df_enb_ne.loc[df_enb_ne.mo_count > 1, 'crelid'] = df_enb_ne.loc[df_enb_ne.mo_count > 1, ['crelid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_ne = df_enb_ne.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # Update data type of plmn to dict
        df_enb_nx['plmn'] = df_enb_nx.plmn.apply(json.loads)
        self.df_enb_nf = df_enb_nf.copy()
        self.df_enb_nx = df_enb_nx.copy()
        self.df_enb_nc = df_enb_nc.copy()
        self.df_enb_nr = df_enb_nr.copy()
        self.df_enb_ne = df_enb_ne.copy()

    def eNodeB_UtraNetwork(self):
        temp_list, temp1_list = [], []
        for site in self.sites:
            site = self.sites.get(site)
            node = site.node
            mo = site.find_mo_ending_with_parent_str('ENodeBFunction')
            if len(mo) == 0: continue
            nwmo = site.find_mo_ending_with_parent_str('UtraNetwork', mo[0])
            if len(nwmo) == 0: continue
            # UtranFrequency , ExternalUtranCellFDD
            for mo in site.find_mo_ending_with_parent_str('UtranFrequency', nwmo[0]):
                freqid = mo.split("=")[-1]
                temp_list.append({
                    'postsite': node,
                    'freqid': freqid,
                    'uarfcn': site.site_extract_data(mo).get('arfcnValueUtranDl'),
                    'flag': False,
                    'fdn': mo
                })
                for xmo in site.find_mo_ending_with_parent_str('ExternalUtranCellFDD', mo):
                    data = site.site_extract_data(xmo)
                    temp1_list.append({
                        'postsite': node,
                        'freqid': freqid,
                        'xcellid': xmo.split('=')[-1],
                        'plmn': data.get('plmnIdentity'),
                        'cellid': data.get('cellIdentity'),
                        'pci': data.get('physicalCellIdentity'),
                        'lac': data.get('lac'),
                        'rac': data.get('rac'),
                        'flag': False,
                        'fdn': mo
                    })

        ecolumns = ['postsite', 'freqid', 'uarfcn', 'flag', 'fdn']
        df_enb_uf = self.df_nan_to_none(df=pd.DataFrame(temp_list)) if len(temp_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        ecolumns = ['postsite', 'freqid', 'xcellid', 'pci', 'cellid', 'lac', 'rac', 'plmn', 'flag', 'fdn']
        df_enb_uc = self.df_nan_to_none(df=pd.DataFrame(temp1_list)) if len(temp1_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)

        # UtranFreqRelation, UtranCellRelation
        temp1_list, temp2_list = [], []
        for _, row in self.df_enb_cell.iterrows():
            if row.fdn is None: continue
            site = self.sites.get(F'site_{row.presite}')
            precell = row.precell
            node = site.node
            for rel_mo in site.find_mo_ending_with_parent_str('UtranFreqRelation', row.fdn):
                rel_data = site.site_extract_data(rel_mo)
                relid = rel_mo.split("=")[-1]
                temp1_list.append({
                    'presite': node,
                    'precell': precell,
                    'relid': relid,
                    'creprio': rel_data.get('cellReselectionPriority'),
                    'cprio': rel_data.get('connectedModeMobilityPrio'),
                    'csprio': rel_data.get('csFallbackPrio'),
                    'csprioec': rel_data.get('csFallbackPrioEC'),
                    'freqid': rel_data.get('utranFrequencyRef').split('=')[-1],
                    'flag': False,
                    'fdn': rel_mo
                })
                for cellrel_mo in site.find_mo_ending_with_parent_str('UtranCellRelation', rel_mo):
                    mo_data = site.site_extract_data(cellrel_mo)
                    temp2_list.append({
                        'presite': node,
                        'precell': precell,
                        'relid': relid,
                        'crelid': cellrel_mo.split("=")[-1],
                        'freqid': mo_data.get('externalUtranCellFDDRef').split(',')[-2].split('=')[-1],
                        'xcellid': mo_data.get('externalUtranCellFDDRef').split("=")[-1],
                        'flag': False,
                        'fdn': cellrel_mo
                    })

        ecolumns = ['presite', 'precell', 'relid', 'creprio', 'cprio', 'csprio', 'csprioec', 'freqid', 'flag', 'fdn']
        df_enb_ur = self.df_nan_to_none(df=pd.DataFrame(temp1_list)) if len(temp1_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        ecolumns = ['presite', 'precell', 'relid', 'crelid', 'freqid', 'xcellid', 'flag', 'fdn']
        df_enb_ue = self.df_nan_to_none(df=pd.DataFrame(temp2_list)) if len(temp2_list) > 0 else (
            pd.DataFrame([], columns=ecolumns))

        # Update Existing Data
        # if df_enb_uc.shape[0] > 0:
        df_enb_uc['plmn'] = df_enb_uc.plmn.apply(json.dumps)
        df_enb_uc['cellid'] = df_enb_uc.cellid.apply(json.dumps)
        df_enb_uc = df_enb_uc.merge(df_enb_uf[['postsite', 'freqid', 'uarfcn']], on=['postsite', 'freqid'], how='left')
        df_enb_ur = df_enb_ur.merge(df_enb_uf[['postsite', 'freqid', 'uarfcn']].rename(columns={'postsite': 'presite'}),
                                    on=['presite', 'freqid'], how='left')
        df_enb_ur = df_enb_ur.merge(self.df_enb_cell[['presite', 'precell', 'postsite', 'postcell']], on=['presite', 'precell'], how='left')
        df_enb_ue = df_enb_ue.merge(df_enb_ur[['presite', 'precell', 'postsite', 'postcell', 'relid', 'uarfcn']],
                                    on=['presite', 'precell', 'relid'], how='left')
        df_enb_ue = df_enb_ue.merge(df_enb_uc[['postsite', 'freqid', 'xcellid', 'plmn', 'cellid']].rename(columns={'postsite': 'presite'}),
                                    on=['presite', 'freqid', 'xcellid'], how='left')

        # New Relation Addition need to be added here
        if self.cix.edx.get('UtranFreqRelation').shape[0] > 0:
            df_n = self.cix.edx.get('UtranFreqRelation').copy()
            df_n = df_n.rename(columns={'eutrancellfddid': 'postcell', 'arfcnvalueutrandl': 'uarfcn', 'utranfreqrelationid': 'relid',
                                        'cellreselectionpriority': 'creprio', 'csfallbackprio': 'csprio', 'csfallbackprioec': 'csprioec',
                                        'connectedmodemobilityprio': 'cprio', 'externalutranfreqid': 'freqid'})
            df_n = df_n[['postcell', 'relid', 'uarfcn', 'creprio', 'cprio', 'csprio', 'csprioec', 'freqid']]
            df_n = df_n.merge(self.df_enb_cell[['postsite', 'postcell']], on=['postcell'], how='left')
            df_n[['flag', 'fdn', 'presite', 'precell']] = df_n.apply(lambda x: pd.Series([True, None, None, None]), axis=1)
            df_enb_ur = df_enb_ur.append(df_n).drop_duplicates().groupby(['postcell', 'uarfcn'], sort=False, as_index=False).head(1)

        # Add & Update Beased on Migration and New Addition
        # Add ExternalUtranCell
        df_enb_ue.drop(['xcellid'], axis=1, inplace=True)
        df_enb_ue = df_enb_ue.merge(df_enb_uc[['postsite', 'xcellid', 'plmn', 'cellid', 'uarfcn']],
                                    on=['postsite', 'plmn', 'cellid', 'uarfcn'], how='left')
        for _, row in df_enb_ue.loc[df_enb_ue.xcellid.isna()].drop_duplicates().groupby(
                ['postsite', 'plmn', 'cellid', 'uarfcn'], as_index=False).head(1).iterrows():
            df_t = df_enb_uc.loc[(df_enb_uc.plmn == row.plmn) & (df_enb_uc.cellid == row.cellid) & (df_enb_uc.uarfcn == row.uarfcn)].head(1)
            if df_t.shape[0] == 0: continue
            df_t[['postsite', 'flag', 'fdn']] = df_t.apply(lambda x: pd.Series([row.postsite, True, None]), axis=1)
            df_enb_uc = pd.concat([df_enb_uc, df_t]).reset_index(inplace=False, drop=True)

        df_n = pd.concat([df_enb_ur[['postsite', 'uarfcn', 'freqid']], df_enb_uc[['postsite', 'uarfcn', 'freqid']]])
        if df_n.shape[0] > 0:
            df_n = df_n.drop_duplicates().groupby(['postsite', 'uarfcn'], sort=False,
                                                  as_index=False).head(1).reset_index(drop=True, inplace=False)
            df_n = df_n.assign(flag=True, fdn=None)
        df_enb_uf = pd.concat([df_enb_uf, df_n]).reset_index(drop=True, inplace=False).drop_duplicates().groupby(['postsite', 'uarfcn'],
                                                                                                                 sort=False, as_index=False).head(1)
        df_enb_uf = df_enb_uf.loc[~(df_enb_uf.postsite.isna() | df_enb_uf.freqid.isna())].reset_index(drop=True, inplace=False)
        df_enb_uf['mo_count'] = df_enb_uf.groupby(['postsite', 'freqid']).cumcount() + 1
        df_enb_uf.loc[df_enb_uf.mo_count > 1, 'freqid'] = df_enb_uf.loc[df_enb_uf.mo_count > 1, ['freqid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_uf = df_enb_uf.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False).reset_index(drop=True, inplace=False)

        df_enb_uc = df_enb_uc.drop(['freqid'], axis=1, inplace=False).merge(df_enb_uf[['postsite', 'freqid', 'uarfcn']],
                                                                            on=['postsite', 'uarfcn'], how='left')
        df_enb_uc = df_enb_uc.loc[~(df_enb_uc.postsite.isna() | df_enb_uc.freqid.isna() | df_enb_uc.cellid.isna())]
        df_enb_uc['mo_count'] = df_enb_uc.groupby(['postsite', 'freqid', 'xcellid']).cumcount() + 1
        df_enb_uc.loc[df_enb_uc.mo_count > 1, 'xcellid'] = df_enb_uc.loc[df_enb_uc.mo_count > 1, ['xcellid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_uc = df_enb_uc.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False).reset_index(drop=True, inplace=False)

        df_enb_ur = df_enb_ur.drop(['freqid'], axis=1, inplace=False).merge(df_enb_uf[['postsite', 'freqid', 'uarfcn']],
                                                                            on=['postsite', 'uarfcn'], how='left')
        df_enb_ur = df_enb_ur.loc[~(df_enb_ur.postsite.isna() | df_enb_ur.freqid.isna() | df_enb_ur.relid.isna() | df_enb_ur.creprio.isna())]
        df_enb_ur['mo_count'] = df_enb_ur.groupby(['postsite', 'postcell', 'relid']).cumcount() + 1
        df_enb_ur.loc[df_enb_ur.mo_count > 1, 'relid'] = df_enb_ur.loc[df_enb_ur.mo_count > 1, ['relid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_ur = df_enb_ur.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False).reset_index(drop=True, inplace=False)

        df_enb_ue.drop(['relid', 'xcellid', 'freqid'], axis=1, inplace=True)
        df_enb_ue = df_enb_ue.merge(df_enb_uc[['postsite', 'freqid', 'xcellid', 'plmn', 'cellid', 'uarfcn']],
                                    on=['postsite', 'plmn', 'cellid', 'uarfcn'], how='left')
        df_enb_ue = df_enb_ue.merge(df_enb_ur[['postsite', 'postcell', 'relid', 'uarfcn']], on=['postsite', 'postcell', 'uarfcn'], how='left')
        df_enb_ue = df_enb_ue.loc[~(df_enb_ue.freqid.isna() | df_enb_ue.xcellid.isna() | df_enb_ue.relid.isna() | df_enb_ue.crelid.isna())]
        df_enb_ue['mo_count'] = df_enb_ue.groupby(['postsite', 'postcell', 'relid', 'crelid']).cumcount() + 1
        df_enb_ue.loc[df_enb_ue.mo_count > 1, 'crelid'] = df_enb_ue.loc[df_enb_ue.mo_count > 1, ['crelid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_ue = df_enb_ue.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False).reset_index(drop=True, inplace=False)

        df_enb_uc['plmn'] = df_enb_uc.plmn.apply(json.loads)
        df_enb_uc['cellid'] = df_enb_uc.cellid.apply(json.loads)
        self.df_enb_uf = df_enb_uf.copy()
        self.df_enb_uc = df_enb_uc.copy()
        self.df_enb_ur = df_enb_ur.copy()
        self.df_enb_ue = df_enb_ue.copy()

    def eNodeB_GeraNetwork(self):
        # GeranFreqGroup, GeranFrequency, ExternalGeranCell
        temp_list, temp1_list, temp2_list = [], [], []
        for site in self.sites:
            site = self.sites.get(site)
            mo = site.find_mo_ending_with_parent_str('ENodeBFunction')
            if len(mo) == 0: continue
            nwmo = site.find_mo_ending_with_parent_str('GeraNetwork', mo[0])
            if len(nwmo) == 0: continue
            node = site.node
            for mo in site.find_mo_ending_with_parent_str('GeranFreqGroup', nwmo[0]):
                temp_list.append({
                    'postsite': node,
                    'gfreqgid': mo.split("=")[-1],
                    'group': site.site_extract_data(mo).get('frequencyGroupId'),
                    'flag': False, 'fdn': mo
                })
            for mo in site.find_mo_ending_with_parent_str('GeranFrequency', nwmo[0]):
                mo_data = site.site_extract_data(mo)
                if len(mo_data.get('geranFreqGroupRef')) > 0:
                    temp1_list.append({
                        'postsite': node,
                        'freqid': mo.split("=")[-1],
                        'bcch': mo_data.get('arfcnValueGeranDl'),
                        'band': mo_data.get('bandIndicator'),
                        'gfreqgid': mo_data.get('geranFreqGroupRef')[0].split("=")[-1],
                        'flag': False, 'fdn': mo
                    })
            for mo in site.find_mo_ending_with_parent_str('ExternalGeranCell', nwmo[0]):
                mo_data = site.site_extract_data(mo)
                temp2_list.append({
                    'postsite': node,
                    'xcellid': mo.split("=")[-1],
                    'ci': mo_data.get('cellIdentity'),
                    'ncc': mo_data.get('ncc'),
                    'bcc': mo_data.get('bcc'),
                    'lac': mo_data.get('lac'),
                    'plmn': mo_data.get('plmnIdentity'),
                    'freqid': mo_data.get('geranFrequencyRef').split("=")[-1],
                    'flag': False, 'fdn': mo
                })
        ecolumns = ['postsite', 'gfreqgid', 'group', 'flag', 'fdn']
        df_enb_gs = self.df_nan_to_none(df=pd.DataFrame(temp_list)) if len(temp_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        ecolumns = ['postsite', 'freqid', 'bcch', 'band', 'gfreqgid', 'flag', 'fdn']
        df_enb_gf = self.df_nan_to_none(df=pd.DataFrame(temp1_list)) if len(temp1_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        ecolumns = ['postsite', 'xcellid', 'ci', 'ncc', 'bcc', 'lac', 'plmn', 'freqid', 'flag', 'fdn']
        df_enb_gc = self.df_nan_to_none(df=pd.DataFrame(temp2_list)) if len(temp2_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)

        # GeranFreqGroupRelation, GeranCellRelation
        temp1_list, temp2_list = [], []
        for _, row in self.df_enb_cell.iterrows():
            if row.fdn is None: continue
            site = self.sites.get(F'site_{row.presite}')
            precell = row.precell
            node = site.node
            for rel_mo in site.find_mo_ending_with_parent_str('GeranFreqGroupRelation', row.fdn):
                rel_data = site.site_extract_data(rel_mo)
                relid = rel_mo.split("=")[-1]
                temp1_list.append({
                    'presite': node,
                    'precell': precell,
                    'relid': relid,
                    'creprio': rel_data.get('cellReselectionPriority'),
                    'gfreqgid': rel_data.get('geranFreqGroupRef').split('=')[-1],
                    'flag': False, 'fdn': rel_mo
                })
                for cellrel_mo in site.find_mo_ending_with_parent_str('GeranCellRelation', rel_mo):
                    mo_data = site.site_extract_data(cellrel_mo)
                    temp2_list.append({
                        'presite': node,
                        'precell': precell,
                        'relid': relid,
                        'crelid': cellrel_mo.split('=')[-1],
                        'xcellid': mo_data.get('extGeranCellRef').split('=')[-1],
                        'flag': False, 'fdn': cellrel_mo
                    })
        ecolumns = ['presite', 'precell', 'relid', 'creprio', 'gfreqgid', 'flag', 'fdn']
        df_enb_gr = self.df_nan_to_none(df=pd.DataFrame(temp1_list)) if len(temp1_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        ecolumns = ['presite', 'precell', 'relid', 'crelid', 'xcellid', 'flag', 'fdn']
        df_enb_ge = self.df_nan_to_none(df=pd.DataFrame(temp2_list)) if len(temp2_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)

        # Update Existing Data
        df_enb_gc['plmn'] = df_enb_gc.plmn.apply(json.dumps)
        df_enb_gf = df_enb_gf.merge(df_enb_gs[['postsite', 'gfreqgid', 'group']], on=['postsite', 'gfreqgid'], how='left')
        df_enb_gc = df_enb_gc.merge(df_enb_gf[['postsite', 'freqid', 'bcch']], on=['postsite', 'freqid'], how='left')
        df_enb_gr = df_enb_gr.merge(df_enb_gs[['postsite', 'gfreqgid', 'group']].rename(columns={'postsite': 'presite'}),
                                    on=['presite', 'gfreqgid'], how='left')
        df_enb_gr = df_enb_gr.merge(self.df_enb_cell[['presite', 'precell', 'postsite', 'postcell']], on=['presite', 'precell'], how='left')
        df_enb_ge = df_enb_ge.merge(df_enb_gc[['postsite', 'xcellid', 'ci', 'lac', 'plmn']].rename(columns={'postsite': 'presite'}),
                                    on=['presite', 'xcellid'], how='left')
        df_enb_ge = df_enb_ge.merge(df_enb_gr[['presite', 'precell', 'postsite', 'postcell', 'relid', 'group']],
                                    on=['presite', 'precell', 'relid'], how='left')
        # df_enb_gc.drop(['freqid'], axis=1, inplace=True)
        # df_enb_gf.drop(['gfreqgid'], axis=1, inplace=True)
        # df_enb_ge.drop(['xcellid', 'relid'], axis=1, inplace=True)

        # Addition of New Cell Relations
        if self.cix.edx.get('GSMCellRel').shape[0] > 0:
            df_n = self.cix.edx.get('GSMCellRel').rename(columns={'ltesiteid': 'postsite', 'sourcecell': 'postcell', 'gsmlac': 'lac'})
            df_n = df_n[['postsite', 'postcell', 'ci', 'bcch', 'ncc', 'bcc', 'lac', 'group']]
            df_n[['crelid', 'xcellid', 'plmn', 'gfreqgid', 'freqid', 'relid', 'band', 'creprio', 'flag', 'presite', 'precell', 'fdn']] = \
                df_n.apply(lambda x: pd.Series([F'{PlmnId["mcc"]}{PlmnId["mnc"]}-{x.lac}-{x.ci}',
                                                F'{PlmnId["mcc"]}{PlmnId["mnc"]}-{x.lac}-{x.ci}', json.dumps(PlmnId), x.group,
                                                x.bcch, x.group, '1 (PCS_1900)', '1', True, None, None, None]), axis=1)
            df_enb_gs = pd.concat([df_enb_gs, df_n[['postsite', 'gfreqgid', 'group', 'flag', 'fdn']]])
            df_enb_gf = pd.concat([df_enb_gf, df_n[['postsite', 'bcch', 'group', 'freqid', 'band', 'flag', 'fdn']]])
            df_enb_gc = pd.concat([df_enb_gc, df_n[['postsite', 'xcellid', 'ci', 'ncc', 'bcc', 'lac', 'plmn', 'bcch', 'flag', 'fdn']]])
            df_enb_gr = pd.concat([df_enb_gr, df_n[['presite', 'precell', 'postsite', 'postcell', 'relid', 'group', 'creprio', 'flag', 'fdn']]])
            df_enb_ge = pd.concat([df_enb_ge, df_n[['presite', 'precell', 'crelid', 'flag', 'fdn', 'ci', 'lac', 'plmn', 'group',
                                                    'postsite', 'postcell']]])
            #
            #
            # df_enb_gs = df_enb_gs.append(df_n[['postsite', 'gfreqgid', 'group', 'flag', 'fdn']])
            # df_enb_gf = df_enb_gf.append(df_n[['postsite', 'bcch', 'group', 'freqid', 'band', 'flag', 'fdn']])
            # df_enb_gc = df_enb_gc.append(df_n[['postsite', 'xcellid', 'ci', 'ncc', 'bcc', 'lac', 'plmn', 'bcch', 'flag', 'fdn']])
            # df_enb_gr = df_enb_gr.append(df_n[['presite', 'precell', 'postsite', 'postcell', 'relid', 'group', 'creprio', 'flag', 'fdn']])
            # df_enb_ge = df_enb_ge.append(df_n[['presite', 'precell', 'crelid', 'flag', 'fdn', 'ci', 'lac', 'plmn', 'group',
            # 'postsite', 'postcell']])
            df_enb_gs = df_enb_gs.drop_duplicates().groupby(['postsite', 'group'], sort=False,
                                                            as_index=False).head(1).reset_index(inplace=False, drop=True)
            df_enb_gf = df_enb_gf.drop_duplicates().groupby(['postsite', 'bcch'], sort=False,
                                                            as_index=False).head(1).reset_index(inplace=False, drop=True)
            df_enb_gc = df_enb_gc.drop_duplicates().groupby(['postsite', 'plmn', 'ci', 'lac', 'bcch'], sort=False,
                                                            as_index=False).head(1).reset_index(inplace=False, drop=True)
            df_enb_gr = df_enb_gr.drop_duplicates().groupby(['postsite', 'postcell', 'group'], sort=False,
                                                            as_index=False).head(1).reset_index(inplace=False, drop=True)
            df_enb_ge = df_enb_ge.drop_duplicates().groupby(['postsite', 'postcell', 'plmn', 'ci', 'lac', 'group'], sort=False,
                                                            as_index=False).head(1).reset_index(inplace=False, drop=True)

        # Update Beased on Migration and New Addition
        df_enb_ge.drop(['xcellid'], axis=1, inplace=True)
        df_enb_ge = df_enb_ge.merge(df_enb_gc[['postsite', 'plmn', 'ci', 'lac', 'xcellid']], on=['postsite', 'plmn', 'ci', 'lac'], how='left')
        for index, row in df_enb_ge.loc[df_enb_ge.xcellid.isnull()].drop_duplicates().groupby(
                ['postsite', 'plmn', 'ci', 'lac'], as_index=False).head(1).iterrows():
            df_n = df_enb_gc.loc[(df_enb_gc.plmn == row.plmn) & (df_enb_gc.ci == row.ci) & (df_enb_gc.lac == row.lac)].head(1)
            if df_n.shape[0] == 0: continue
            df_n[['postsite', 'flag', 'fdn']] = df_n.apply(lambda x: pd.Series([x.postsite, True, None]), axis=1)
            df_enb_gc = pd.concat([df_enb_gc, df_n]).reset_index(inplace=False, drop=True)

        df_enb_gc = df_enb_gc.drop(['freqid'], axis=1, inplace=False).merge(df_enb_gf[['postsite', 'freqid', 'bcch']],
                                                                            on=['postsite', 'bcch'], how='left')
        for index, row in df_enb_gc.loc[df_enb_gc.freqid.isnull()].drop_duplicates().groupby(['postsite', 'bcch'], as_index=False).head(1).iterrows():
            df_n = df_enb_gf.loc[(df_enb_gf.bcch == row.bcch)].head(1)
            if df_n.shape[0] == 0: continue
            df_n[['postsite', 'flag', 'fdn']] = df_n.apply(lambda x: pd.Series([x.postsite, True, None]), axis=1)
            df_enb_gf = pd.concat([df_enb_gf, df_n]).reset_index(inplace=False, drop=True)

        # GeranFreqGroup
        df_n = pd.concat([df_enb_gf[['postsite', 'group']], df_enb_gr[['postsite', 'group']]]).groupby(
            ['postsite', 'group'], sort=False, as_index=False).head(1)
        # df_n = df_n.drop_duplicates().groupby(['postsite', 'group'], sort=False, as_index=False).head(1)
        # df_n = df_enb_gf[['postsite', 'group']].append(df_enb_gr[['postsite', 'group']]).drop_duplicates().groupby(
        #     ['postsite', 'group'], sort=False, as_index=False).head(1)
        if df_n.shape[0] > 0:
            df_n[['gfreqgid', 'flag', 'fdn']] = df_n.apply(lambda x: pd.Series([x.group, True, None]), axis=1)
            df_enb_gs = pd.concat([df_enb_gs, df_n])
            # df_enb_gs = df_enb_gs.append(df_n)
        # Update On 12/13
        if self.cix.edx.get('FreqGroupRel').shape[0] > 0:
            df_tmp = self.cix.edx.get('FreqGroupRel')[['postsite', 'gfreqgid', 'group', 'flag']]
            df_enb_gs = pd.concat([df_enb_gs, df_tmp])
        # Update End
        df_enb_gs = df_enb_gs.drop_duplicates().groupby(['postsite', 'group'], sort=False,
                                                        as_index=False).head(1).reset_index(drop=True, inplace=False)
        df_enb_gs['mo_count'] = df_enb_gs.groupby(['postsite', 'group']).cumcount() + 1
        df_enb_gs.loc[df_enb_gs.mo_count > 1, 'gfreqgid'] = df_enb_gs.loc[df_enb_gs.mo_count > 1, ['group', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_gs = df_enb_gs.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # GeranFrequency
        df_enb_gf = df_enb_gf.drop(['gfreqgid'], axis=1, inplace=False).merge(df_enb_gs[['postsite', 'gfreqgid', 'group']],
                                                                              on=['postsite', 'group'], how='left')
        df_enb_gf = df_enb_gf.loc[~(df_enb_gf.postsite.isna() | df_enb_gf.freqid.isna() | df_enb_gf.gfreqgid.isna())]
        df_enb_gf = df_enb_gf.drop_duplicates().groupby(['postsite', 'bcch'], sort=False,
                                                        as_index=False).head(1).reset_index(drop=True, inplace=False)
        df_enb_gf['mo_count'] = df_enb_gf.groupby(['postsite', 'freqid']).cumcount() + 1
        df_enb_gf.loc[df_enb_gf.mo_count > 1, 'freqid'] = df_enb_gf.loc[df_enb_gf.mo_count > 1, ['group', 'bcch']].apply(
            lambda x: '__'.join(x.astype(str)), axis=1)
        df_enb_gf = df_enb_gf.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # ExternalGeranCell
        df_enb_gc = df_enb_gc.drop(['freqid'], axis=1, inplace=False).merge(df_enb_gf[['postsite', 'freqid', 'bcch']],
                                                                            on=['postsite', 'bcch'], how='left')
        df_enb_gc = df_enb_gc.loc[~(df_enb_gc.postsite.isna() | df_enb_gc.xcellid.isna() | df_enb_gc.freqid.isna())]
        df_enb_gc = df_enb_gc.drop_duplicates().groupby(['postsite', 'plmn', 'ci', 'lac', 'bcch'], sort=False,
                                                        as_index=False).head(1).reset_index(drop=True, inplace=False)
        df_enb_gc['mo_count'] = df_enb_gc.groupby(['postsite', 'xcellid']).cumcount() + 1
        df_enb_gc.loc[df_enb_gc.mo_count > 1, 'xcellid'] = df_enb_gc.loc[df_enb_gc.mo_count > 1, ['xcellid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_gc = df_enb_gc.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # GeranFreqGroupRelation
        df_enb_gr = df_enb_gr.drop(['gfreqgid'], axis=1, inplace=False).merge(df_enb_gs[['postsite', 'gfreqgid', 'group']],
                                                                              on=['postsite', 'group'], how='left')
        # Update On 12/13
        if self.cix.edx.get('FreqGroupRel').shape[0] > 0:
            df_tmp = self.cix.edx.get('FreqGroupRel')[['postsite', 'postcell', 'relid', 'creprio', 'gfreqgid', 'flag', 'group']]
            df_enb_gr = pd.concat([df_enb_gr, df_tmp])
            # df_enb_gr = df_enb_gr.append(df_tmp)
        # Update End
        df_enb_gr = df_enb_gr.loc[~(df_enb_gr.postsite.isna() | df_enb_gr.postcell.isna() | df_enb_gr.relid.isna() | df_enb_gr.gfreqgid.isna())]
        df_enb_gr = df_enb_gr.drop_duplicates().groupby(['postsite', 'postcell', 'group'], sort=False,
                                                        as_index=False).head(1).reset_index(inplace=False, drop=True)
        df_enb_gr['mo_count'] = df_enb_gr.groupby(['postsite', 'postcell', 'relid']).cumcount() + 1
        df_enb_gr.loc[df_enb_gr.mo_count > 1, 'relid'] = df_enb_gr.loc[df_enb_gr.mo_count > 1, ['relid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_gr = df_enb_gr.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False)

        # GeranCellRelation
        df_enb_ge.drop(['xcellid', 'relid'], axis=1, inplace=True)
        df_enb_ge = df_enb_ge.merge(df_enb_gc[['postsite', 'plmn', 'ci', 'lac', 'xcellid']], on=['postsite', 'plmn', 'ci', 'lac'], how='left')
        df_enb_ge = df_enb_ge.merge(df_enb_gr[['postsite', 'postcell', 'relid', 'group']], on=['postsite', 'postcell', 'group'], how='left')
        df_enb_ge = df_enb_ge.loc[~(df_enb_ge.postsite.isna() | df_enb_ge.postcell.isna() | df_enb_ge.xcellid.isna() |
                                    df_enb_ge.relid.isna() | df_enb_ge.crelid.isna())]
        df_enb_ge = df_enb_ge.drop_duplicates().groupby(['postsite', 'postcell', 'plmn', 'ci', 'lac', 'group'], sort=False, as_index=False).head(1)
        df_enb_ge.reset_index(inplace=True, drop=True)
        df_enb_ge['mo_count'] = df_enb_ge.groupby(['postsite', 'postcell', 'relid', 'crelid']).cumcount() + 1
        df_enb_ge.loc[df_enb_ge.mo_count > 1, 'crelid'] = df_enb_ge.loc[df_enb_ge.mo_count > 1, ['crelid', 'mo_count']].apply(
            lambda x: '_'.join(x.astype(str)), axis=1)
        df_enb_ge = df_enb_ge.replace({np.nan: None}).drop(['mo_count'], axis=1, inplace=False).reset_index(drop=True, inplace=False)

        df_enb_gc['plmn'] = df_enb_gc.plmn.apply(json.loads)
        self.df_enb_gs = df_enb_gs.copy()
        self.df_enb_gf = df_enb_gf.copy()
        self.df_enb_gc = df_enb_gc.copy()
        self.df_enb_gr = df_enb_gr.copy()
        self.df_enb_ge = df_enb_ge.copy()
        
    def antenna_system_cell(self, site, presite, precell, rfb_list):
        rfb_list = list(OrderedDict.fromkeys(rfb_list).keys())
        rf_branches, temp_fru = [], []
        for _, rf_branch_ref in enumerate(rfb_list):
            rfb_tmp_dict = {'presite': presite, 'precell': precell, 'raug': None, 'rfb': None, 'dl_ul_delay_att': None,
                            'fru': None, 'isshared': 'false', 'rfp': None, 'trecid': None,
                            'aug': None, 'au': None, 'asu': None, 'aup': None, 'rfbfdn': None,  'frufdn': None,
                            'aufdn': None, 'asufdn': None, 'aupfdn': None, 'retfdn': None, 'tmafdn': None}
            rfbfdn = site.get_mo_name_ending_str(rf_branch_ref)
            rfb_data = site.site_extract_data(rfbfdn)
            rfbfdn_ids = {_.split('=')[0]: _.split('=')[-1] for _ in rfbfdn.split(',')}
            if 'Transceiver' in rfbfdn_ids.keys():
                frufdn = ','.join(rfbfdn.split(',')[:[_.split('=')[0] for _ in rfbfdn.split(',')].index('FieldReplaceableUnit') + 1])
                rfb_tmp_dict.update({
                    'rfb': rfbfdn_ids.get('Transceiver', None),
                    'fru': rfbfdn_ids.get('FieldReplaceableUnit', None),
                    'rfbfdn': rfbfdn,
                    'frufdn': frufdn,
                })
            else:
                tmafdn = site.get_mo_name_ending_str(rfb_data.get('tmaRef')) if rfb_data.get('tmaRef') is not None else None
                rfb_tmp_dict.update({
                    'raug': rfbfdn_ids.get('AntennaUnitGroup'),
                    'rfb': rfbfdn_ids.get('RfBranch'),
                    'dl_ul_delay_att': [rfb_data.get('dlTrafficDelay')[0], rfb_data.get('ulTrafficDelay')[0],
                                        rfb_data.get('dlAttenuation')[0], rfb_data.get('ulAttenuation')[0]],
                    'tmafdn': tmafdn,
                    'rfbfdn': rfbfdn,
                })
                aupfdn = rfb_data.get('auPortRef')
                if aupfdn is not None and len(aupfdn) > 0:
                    aupfdn = site.get_mo_name_ending_str(aupfdn[0])
                    aupfdn_ids = {_.split('=')[0]: _.split('=')[-1] for _ in aupfdn.split(',')}
                    aufdn = ','.join(aupfdn.split(',')[:[_.split('=')[0] for _ in aupfdn.split(',')].index('AntennaUnit') + 1])
                    asufdn = ','.join(aupfdn.split(',')[:[_.split('=')[0] for _ in aupfdn.split(',')].index('AntennaSubunit') + 1])
                    retfdn = site.site_extract_data(asufdn).get('retSubunitRef', None)
                    if retfdn is not None and len(retfdn) > 0: retfdn = site.get_mo_name_ending_str(retfdn)
                    rfb_tmp_dict.update({
                        'aug': aupfdn_ids.get('AntennaUnitGroup', None),
                        'au': aupfdn_ids.get('AntennaUnit', None),
                        'asu': aupfdn_ids.get('AntennaSubunit', None),
                        'aup': aupfdn_ids.get('AuPort', None),
                        'mt': site.site_extract_data(aufdn).get('mechanicalAntennaTilt', '0'),
                        'retfdn': retfdn,
                        'aufdn': aufdn,
                        'asufdn': asufdn,
                        'aupfdn': aupfdn,
                    })
                rfpfdn = rfb_data.get('rfPortRef')
                if rfpfdn is not None and len(rfpfdn) > 0:
                    rfpfdn = site.get_mo_name_ending_str(rfpfdn)
                    frufdn = ','.join(rfpfdn.split(',')[:[_.split('=')[0] for _ in rfpfdn.split(',')].index('FieldReplaceableUnit') + 1])
                    rfpfdn_ids = {_.split('=')[0]: _.split('=')[-1] for _ in rfpfdn.split(',')}
                    rfb_tmp_dict.update({
                        'fru': rfpfdn_ids.get('FieldReplaceableUnit', None),
                        'isshared': site.site_extract_data(frufdn).get('isSharedWithExternalMe', 'false'),
                        'rfp': rfpfdn_ids.get('RfPort', None),
                        'frufdn': frufdn,
                    })
            # rf_branches.append(rfb_tmp_dict.copy())
            self.ant_system_list.append(rfb_tmp_dict.copy())
            if rfb_tmp_dict.get('frufdn') is None:
                temp_fru.append([None, None, None])
            else:
                fru_data = site.site_extract_data(rfb_tmp_dict.get('frufdn')).get('productData')
                temp_fru.append([rfb_tmp_dict.get('fru'),
                                 ''.join(fru_data.get('productName')).upper() if fru_data.get('productName', None) is not None else None,
                                 fru_data.get('serialNumber', None)])
        temp_fru_a = []
        for item in temp_fru:
            if item not in temp_fru_a: temp_fru_a.append(item)
        return temp_fru_a
        # return rf_branches, temp_fru_a

    def enodeb_gnodeb_antenna_system(self):
        ecolumns = ['presite', 'precell', 'raug', 'rfb', 'dl_ul_delay_att', 'fru', 'isshared', 'rfp', 'trecid', 'aug', 'au', 'asu', 'aup',
                    'rfbfdn', 'frufdn', 'retfdn', 'tmafdn', 'aufdn']
        df_ant = self.df_nan_to_none(df=pd.DataFrame(self.ant_system_list)) if len(self.ant_system_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)
        df_ant = self.df_nan_to_none(df=df_ant)
        df_ant['antflag'] = False
        cell_col_list = ['celltype', 'presite', 'precell', 'postsite', 'postcell', 'prefru', 'prefrutype', 'prefrusn', 'frutypecix',
                         'presc', 'addcell', 'sef', 'sefcix', 'sccix', 'carrier', 'rrushared', 'sc', 'nooftx', 'noofrx', 'confpow',
                         'confpowcix', 'fruchange', 'dl_ul_delay_att']
        df_cell = pd.DataFrame()
        if self.df_enb_cell.shape[0] > 0:
            df_cell = self.df_enb_cell.loc[~self.df_enb_cell.celltype.str.contains('IOT')][cell_col_list]
        if self.df_gnb_cell.shape[0] > 0:
            df_cell = pd.concat([df_cell, self.df_gnb_cell[cell_col_list]]).reset_index(drop=True, inplace=False)
            # df_cell = df_cell.append(self.df_gnb_cell[cell_col_list]).reset_index(drop=True, inplace=False)
        cell_col_list.pop(-1)
        df_ant = df_ant.merge(df_cell[cell_col_list], on=['presite', 'precell'], how='left')

        new_antenna = []
        for _, row in df_cell.loc[df_cell.fruchange].iterrows():  # & (df_cell.carrier.str.upper().contains('MC'))
            tmp_dict = {'presite': row.presite, 'precell': row.precell, 'raug': None, 'rfb': None, 'dl_ul_delay_att': None,
                        'fru': None, 'isshared': 'false',
                        'rfp': None, 'trecid': None, 'aug': row.sef, 'au': '1', 'asu': '1', 'aup': None, 'rfbfdn': None, 'frufdn': None,
                        'retfdn': None, 'tmafdn': None, 'aufdn': None, 'asufdn': None, 'mt': '0', 'aupfdn': None,
                        'antflag': True, 'celltype': row.celltype,
                        'postsite': row.postsite, 'postcell': row.postcell, 'prefru': row.prefru, 'prefrutype': row.prefrutype,
                        'prefrusn': row.prefrusn, 'frutypecix': row.frutypecix, 'presc': row.presc, 'addcell': row.addcell,
                        'sef': row.sef, 'sefcix': row.sefcix, 'sccix': row.sccix, 'carrier': row.carrier, 'rrushared': row.rrushared,
                        'sc': row.sc, 'nooftx': row.nooftx, 'noofrx': row.noofrx, 'confpow': row.confpow, 'confpowcix': row.confpowcix,
                        'fruchange': row.fruchange}

            if ('MC' in str(row.carrier).upper()) and \
                    (('4460' in row.frutypecix) or max([False] + [True for i in row.frutypecix if ('4460' in i) or ('2260' in i)])):
                tmp_dict['sef'] = row.sefcix

            rfpids, rfbids = ['A', 'C', 'B', 'D'], [1, 2, 3, 4]
            
            if ('4460' in row.frutypecix) or max([False] + [True for i in row.frutypecix if ('4460' in i) or ('2260' in i)]):
                fruid = F'AWPC-0{tmp_dict["sef"]}' if 'AWPC' not in tmp_dict["sef"] else tmp_dict["sef"]
            elif '-' in str(tmp_dict["sef"]): fruid = F'{tmp_dict["sef"]}'
            else: fruid = F'RRU-{tmp_dict["sef"]}'
            fru = row.frutypecix[0]
            if (('4424' in fru) and (len(row.frutypecix) == 1)) or (('2212' in fru) and (len(row.frutypecix) == 2)):
                rfpids = ['A', 'B', 'A', 'B']
                for i in rfbids:
                    if i == 2: j = i
                    elif i == 3: j = i - 2
                    else: j = i - 1
                    fruid_next = F'{fruid}-{1 if i < 3 else 2}'
                    tmp_dict1 = tmp_dict.copy()
                    tmp_dict1.update({'raug': tmp_dict["sef"], 'rfb': str(i), 'dl_ul_delay_att': row.dl_ul_delay_att[i - 1],
                                      'fru': fruid_next, 'rfp': rfpids[i - 1], 'aup': F'{j}', 'frutypecix': fru})
                    new_antenna.append(tmp_dict1)

            elif (('4460' in fru) and (len(row.frutypecix) == 1)) or (('2260' in fru) and (len(row.frutypecix) == 2)):
                rfpids = ['A', 'A', 'B', 'B']
                for i in rfbids:
                    if i == 2: j = i
                    elif i == 3: j = i - 2
                    else: j = i - 1
                    fruid_next = F'{fruid}-{"01" if i in [1, 3] else "02"}'
                    tmp_dict1 = tmp_dict.copy()
                    tmp_dict1.update({'raug': tmp_dict["sef"], 'rfb': str(i), 'dl_ul_delay_att': row.dl_ul_delay_att[i - 1],
                                      'fru': fruid_next, 'rfp': rfpids[i - 1], 'aup': F'{j}', 'frutypecix': fru})
                    new_antenna.append(tmp_dict1)
            
            elif '8863' in fru:
                if (row.rrushared is None) and len(df_cell.loc[df_cell.rrushared == row.postcell].index) == 0:
                    rfpids, rfbids = ['A', 'C', 'B', 'D', 'E', 'G', 'F', 'H'], [1, 2, 3, 4, 5, 6, 7, 8]
                elif (row.rrushared is None) and len(df_cell.loc[df_cell.rrushared == row.postcell].index) > 0:
                    rfpids, rfbids = ['A', 'C', 'B', 'D'], [1, 2, 3, 4]
                elif (row.rrushared is not None) and len(df_cell.loc[df_cell.postcell == row.rrushared].index) > 0:
                    rfpids, rfbids = ['E', 'G', 'F', 'H'], [1, 2, 3, 4]
                    fruid = df_cell.loc[(df_cell.postcell == row.rrushared), 'sefcix'].values[0]
                else: rfpids, rfbids = ['A', 'C', 'B', 'D', 'E', 'G', 'F', 'H'], [1, 2, 3, 4, 5, 6, 7, 8]
                
                for i in rfbids:
                    if i == 2 or i == 6: j = i
                    elif i == 3 or i == 7: j = i - 2
                    else: j = i - 1
                    tmp_dict1 = tmp_dict.copy()
                    tmp_dict1.update({'raug': tmp_dict["sef"], 'rfb': F'{i}', 'dl_ul_delay_att': row.dl_ul_delay_att[i - 1 if i < 5 else i - 5],
                                      'fru': fruid, 'rfp': rfpids[i - 1], 'aup': F'{j}', 'frutypecix': fru})
                    new_antenna.append(tmp_dict1)
                    
            elif len(row.frutypecix) == 1:
                # fru = row.frutypecix[0]
                if ('AIR6449' in fru) or ('AIR3246' in fru) or ('AIR6419' in fru) or ('AIR5322' in fru):
                    tmp_dict1 = tmp_dict.copy()
                    tmp_dict1.update({'fru': fruid, 'trecid': '1', 'frutypecix': fru})
                    new_antenna.append(tmp_dict1)
                
                elif (('AIR32' in fru) or ('4415' in fru) or ('4449' in fru) or ('4480' in fru) or ('4402' in fru) or
                      ('4455' in fru) or ('4435' in fru) or ('4455' in fru) or ('4495' in fru)):
                    for i in rfbids:
                        if i == 2: j = i
                        elif i == 3: j = i - 2
                        else: j = i - 1
                        tmp_dict1 = tmp_dict.copy()
                        tmp_dict1.update({'raug': tmp_dict["sef"], 'rfb': str(i), 'dl_ul_delay_att': row.dl_ul_delay_att[i-1],
                                          'fru': fruid, 'rfp': rfpids[i-1], 'aup': F'{j}', 'frutypecix': fru})
                        new_antenna.append(tmp_dict1)
                
                elif ('RRUS11' in fru) or ('RRUS12' in fru):
                    for i in rfbids[:2]:
                        tmp_dict1 = tmp_dict.copy()
                        tmp_dict1.update({'raug': tmp_dict["sef"], 'rfb': str(i), 'dl_ul_delay_att': row.dl_ul_delay_att[i-1],
                                          'fru': fruid, 'rfp': rfpids[i-1], 'aup': F'{i-1}', 'frutypecix': fru})
                        new_antenna.append(tmp_dict1)
                elif 'RUS01' in fru:
                    # for i in rfbids[:1]:
                    #     fruid = F'RU-{tmp_dict["sef"]}'
                    tmp_dict1 = tmp_dict.copy()
                    tmp_dict1.update({'raug': tmp_dict["sef"], 'rfb': '1', 'dl_ul_delay_att': row.dl_ul_delay_att[0],
                                      'fru': F'RU-{tmp_dict["sef"]}-1', 'rfp': 'A', 'aup': '0', 'frutypecix': fru})
                    new_antenna.append(tmp_dict1)
            elif len(row.frutypecix) == 2:
                rfpids = ['A', 'A', 'B', 'B']
                if ('RRUS11' in fru) or ('RRUS12' in fru) or ('2212' in fru):
                    for i in rfbids:
                        if i == 2: j = i
                        elif i == 3: j = i - 2
                        else: j = i - 1
                        fruid = F'RRU-{tmp_dict["sef"]}-{1 if i < 3 else 2}'
                        tmp_dict1 = tmp_dict.copy()
                        tmp_dict1.update({'raug': tmp_dict["sef"], 'rfb': str(i), 'dl_ul_delay_att': row.dl_ul_delay_att[i-1],
                                          'fru': fruid, 'rfp': rfpids[i-1], 'aup': F'{j}', 'frutypecix': fru})
                        new_antenna.append(tmp_dict1)
                elif 'RUS01' in fru:
                    tmp_dict1 = tmp_dict.copy()
                    tmp_dict1.update({'raug': tmp_dict["sef"], 'rfb': '1', 'dl_ul_delay_att': row.dl_ul_delay_att[0],
                                      'fru': F'RU-{tmp_dict["sef"]}-1', 'rfp': 'A', 'aup': '0', 'frutypecix': fru})
                    new_antenna.append(tmp_dict1)
                    tmp_dict1 = tmp_dict.copy()
                    tmp_dict1.update({'raug': tmp_dict["sef"], 'rfb': '1', 'dl_ul_delay_att': row.dl_ul_delay_att[0],
                                      'fru': F'RU-{tmp_dict["sef"]}-2', 'rfp': 'A', 'aup': '0', 'frutypecix': fru})
                    new_antenna.append(tmp_dict1)
        if len(new_antenna) > 0:
            df_ant = pd.concat([df_ant, self.df_nan_to_none(df=pd.DataFrame(new_antenna))])
        for car in df_ant.carrier.unique():
            if len(df_ant.loc[df_ant.antflag & (df_ant.carrier == car)].postsite.unique()) > 1:
                df_ant.loc[df_ant.antflag & (df_ant.carrier == car), 'isshared'] = 'true'
        self.df_ant = df_ant.copy()

    def enodeb_gnodeb_antnearunit(self):
        ecolumns = ['aug', 'anu', 'uniqueId', 'fru', 'rfp', 'flag', 'anufdn', 'presite', 'precell', 'postsite', 'postcell',
                    'addcell', 'antflag', 'fruchange']
        ant_near_unit_list = []
        for key in self.sites:
            site = self.sites.get(key)
            for mo in site.find_mo_ending_with_parent_str('AntennaNearUnit', ''):
                mo_dict = {_.split('=')[0]: _.split('=')[1] for _ in mo.split(',')}
                rfp_ref = site.site_extract_data(mo).get('rfPortRef')
                if rfp_ref is None: continue
                rfp_ref_dict = {_.split('=')[0]: _.split('=')[1] for _ in rfp_ref.split(',')}
                tmp_dict = {'presite': site.node, 'aug': mo_dict['AntennaUnitGroup'], 'anu': mo_dict['AntennaNearUnit'],
                            'uniqueId': site.site_extract_data(mo).get('uniqueId'),
                            'fru': None if rfp_ref is None else rfp_ref_dict.get('FieldReplaceableUnit'),
                            'rfp': None if rfp_ref is None else rfp_ref_dict['RfPort'], 'flag': False, 'anufdn': mo}
                ant_near_unit_list.append(tmp_dict)
        if len(ant_near_unit_list) > 0:
            df = self.df_nan_to_none(df=pd.DataFrame(ant_near_unit_list))
            df_ant_cell = self.df_ant.loc[~self.df_ant.antflag, ['fru', 'presite', 'precell', 'postsite', 'postcell',
                                                                 'addcell', 'antflag', 'fruchange']].drop_duplicates()
            df = df.merge(df_ant_cell, on=['presite', 'fru'], how='left').drop_duplicates()
            self.df_ant_near_unit = df.copy()
        else:
            self.df_ant_near_unit = pd.DataFrame([], columns=ecolumns)

    def xmu_all_site(self):
        ecolumns = ['postsite', 'xmu1', 'flag1', 'xmu1p1', 'xmu1p2', 'xmu1p3', 'xmu2', 'flag2', 'xmu2p1', 'xmu2p2', 'xmu2p3']
        temp_list = []
        for index, row in self.cix.edx.get('ENodeB').iterrows():
            temp_dict = {'postsite': row.node, 'xmu1': None, 'flag1': False, 'xmu1p1': None, 'xmu1p2': None, 'xmu1p3': None,
                         'xmu2': None, 'flag2': False, 'xmu2p1': None, 'xmu2p2': None, 'xmu2p3': None}
            site = self.sites.get(F'site_{row.node}')
            if (row.xmu1 is not None) and (str(row.xmu1).lower() == 'yes' or str(row.xmu1) == '1'):
                if (site is None) or (len(site.site_xmu_dict[row.node]) < 1): xmu, flag_val = 'XMU03-1-1', True
                else:
                    xmu = sorted(site.site_xmu_dict[row.node], key=str.upper)[0]
                    flag_val = self.enodeb[row.node]['BBChange']

                temp_dict.update({'xmu1p1': row.xmu1p1, 'xmu1p2': row.xmu1p2, 'xmu1p3': row.xmu1p3, 'xmu1': xmu, 'flag1': flag_val})
            if (row.xmu2 is not None) and (str(row.xmu2).lower() == 'yes' or str(row.xmu2) == '1'):
                if (site is None) or (len(site.site_xmu_dict[row.node]) < 2): xmu, flag_val = 'XMU03-1-2', True
                else:
                    xmu = sorted(site.site_xmu_dict[row.node], key=str.upper)[1]
                    flag_val = self.enodeb[row.node]['BBChange']
                temp_dict.update({'xmu2p1': row.xmu2p1, 'xmu2p2': row.xmu2p2, 'xmu2p3': row.xmu2p3, 'xmu2': xmu, 'flag2': flag_val})
            temp_list.append(temp_dict)

        for index, row in self.cix.edx.get('gNodeB').iterrows():
            if row.node in self.cix.edx.get('ENodeB').node.unique(): continue
            temp_dict = {'postsite': row.node, 'xmu1': None, 'flag1': False, 'xmu1p1': None, 'xmu1p2': None, 'xmu1p3': None,
                         'xmu2': None, 'flag2': False, 'xmu2p1': None, 'xmu2p2': None, 'xmu2p3': None}
            site = self.sites.get(F'site_{row.node}')
            if (row.xmu1 is not None) and (str(row.xmu1).lower() == 'yes' or str(row.xmu1) == '1'):
                if (site is None) or (len(site.site_xmu_dict[row.node]) < 1): xmu, flag_val = 'XMU03-1-1', True
                else:
                    xmu = sorted(site.site_xmu_dict[row.node], key=str.upper)[0]
                    flag_val = self.gnodeb[row.node]['BBChange']
                temp_dict.update({'xmu1p1': row.xmu1p1, 'xmu1p2': row.xmu1p2, 'xmu1p3': row.xmu1p3, 'xmu1': xmu, 'flag1': flag_val})
            if (row.xmu2 is not None) and (str(row.xmu2).lower() == 'yes' or str(row.xmu2) == '1'):
                if (site is None) or (len(site.site_xmu_dict[row.node]) < 2): xmu, flag_val = 'XMU03-1-2', True
                else:
                    xmu = sorted(site.site_xmu_dict[row.node], key=str.upper)[1]
                    flag_val = self.gnodeb[row.node]['BBChange']
                temp_dict.update({'xmu2p1': row.xmu2p1, 'xmu2p2': row.xmu2p2, 'xmu2p3': row.xmu2p3, 'xmu2': xmu, 'flag2': flag_val})
            temp_list.append(temp_dict)
        if len(temp_list) > 0: self.df_xmu = pd.DataFrame(temp_list)
        else: self.df_xmu = pd.DataFrame([], columns=ecolumns)
        self.df_xmu = self.df_nan_to_none(df=self.df_xmu)

    def rilink_all_site(self):
        tmp_list = []
        for key in self.sites.keys():
            site = self.sites.get(key)
            for mo in site.find_mo_ending_with_parent_str('RiLink', ''):
                data = site.site_extract_data(mo)
                ref1 = ','.join(data.get('riPortRef1').split(',')[-2:])
                ref2 = ','.join(data.get('riPortRef2').split(',')[-2:])
                tmp_list.append([site.node, ref1, ref2, data.get('riLinkId')])
        df = self.df_nan_to_none(df=pd.DataFrame(tmp_list, columns=['site', 'ref1', 'ref2', 'rilid']))
        df[['fru1', 'rip1']] = self.df_nan_to_none(df=pd.DataFrame([[key.split('=')[-1] for key in _.split(',')] for _ in df.ref1.tolist()], columns=['fru1', 'rip1']))
        df[['fru2', 'rip2']] = self.df_nan_to_none(df=pd.DataFrame([[key.split('=')[-1] for key in _.split(',')] for _ in df.ref2.tolist()], columns=['fru2', 'rip2']))
        del df['ref1'], df['ref2']
        df_ant_cell = self.df_ant.loc[~self.df_ant.antflag, ['fru', 'presite', 'precell', 'postsite', 'postcell', 'addcell',
                                                             'antflag', 'fruchange']].drop_duplicates()

        df = df.merge(df_ant_cell, left_on='fru2', right_on='fru', how='left')
        df = df.merge(df_ant_cell, left_on='fru1', right_on='fru', how='left', suffixes=('', '_1'))
        df['port_index'] = df.sort_values(['precell', 'fru2']).groupby('precell').cumcount() + 1
        numeric_fru2_mask = pd.to_numeric(df['fru2'], errors='coerce').notna()
        df['port_index'] = df['port_index'].astype('string')
        df.loc[numeric_fru2_mask, 'port_index'] = df.loc[numeric_fru2_mask, 'fru2'].astype('string')

        df.drop([_ for _ in df.columns if _.endswith('_1')], axis=1, inplace=True)
        self.df_pre_ril = df.copy()
        del df

        # New Rilink


        if self.cix.edx.get('EutranCellFDD').index.size > 0:
            df_cix_enb = self.cix.edx.get('EutranCellFDD')[['node', 'eutrancellfddid', 'carrier', 'bbuxmu', 'port1',
                                                        'port2', 'port3', 'port4', 'rrutype']]
        else:
            df_cix_enb = self.df_nan_to_none(df=pd.DataFrame([], columns=['node', 'eutrancellfddid', 'carrier', 'bbuxmu', 'port1', 'port2', 'port3', 'port4', 'rrutype']))
        df_cix_enb = df_cix_enb.rename(columns={'eutrancellfddid': 'postcell'}, inplace=False)
        if self.cix.edx.get('gUtranCell').index.size > 0:
            df_cix_gnb = self.cix.edx.get('gUtranCell')[['node', 'gutrancell', 'carrier', 'bbuxmu', 'port1', 'port2', 'port3', 'port4', 'radiotype']]
        else:
            df_cix_gnb = self.df_nan_to_none(df=pd.DataFrame([], columns=['node', 'gutrancell', 'carrier', 'bbuxmu', 'port1', 'port2', 'port3', 'port4', 'radiotype']))
        df_cix_gnb = df_cix_gnb.rename(columns={'gutrancell': 'postcell', 'radiotype': 'rrutype'}, inplace=False)

        df_cix = pd.concat([df_cix_enb, df_cix_gnb])
        for index, row in df_cix.iterrows():
            if 'BB' in row.bbuxmu.upper():
                df_cix.loc[df_cix.node == row.node, 'bbuxmu'] = (
                    self.enodeb[row.node]['BBId'] if row.node in self.enodeb.keys() else self.gnodeb[row.node]['BBId'])
            elif 'XMU1' in row.bbuxmu.upper():
                df_cix.loc[df_cix.node == row.node, 'bbuxmu'] = self.df_xmu.loc[self.df_xmu.postsite == row.node].xmu1.iloc[0]
            elif 'XMU2' in row.bbuxmu.upper():
                df_cix.loc[df_cix.node == row.node, 'bbuxmu'] = self.df_xmu.loc[self.df_xmu.postsite == row.node].xmu2.iloc[0]
        del df_cix_enb, df_cix_gnb

        df_ril = self.df_ant[['presite', 'precell', 'postsite', 'postcell', 'fru', 'antflag', 'addcell', 'fruchange']].drop_duplicates()
        df_ril = df_ril.merge(df_cix, on='postcell')

        ecolumns = [['site', 'rilid', 'fru1', 'rip1', 'fru2', 'rip2', 'fru', 'presite', 'precell', 'postsite', 'postcell',
                     'addcell', 'antflag', 'fruchange']]
        temp_list = []
        self.temp_1 = df_ril.copy()
        for site in set(list(self.enodeb.keys()) + list(self.gnodeb.keys())):
            # XMU RiLink
            for _, row in self.df_xmu.loc[self.df_xmu.postsite == site].iterrows():
                for i in range(1, 3):
                    if row.get(F'xmu{i}') is not None:
                        xmu_id = row.get(F'xmu{i}')
                        for j in range(1, 4):
                            if row.get(F'xmu{i}p{j}') is not None:
                                bbid = self.enodeb[site]['BBId'] if site in self.enodeb.keys() else self.gnodeb[site]['BBId']
                                max_rilid = F'{bbid}-' + row.get(F'xmu{i}p{j}') + '-' + xmu_id + F'-{j}'
                                temp_dict = {
                                    'site': site, 'rilid': max_rilid,
                                    'fru1': bbid, 'rip1': row.get(F'xmu{i}p{j}'),
                                    'fru2': row.get(F'xmu{i}'), 'rip2': str(j),
                                    'fru': xmu_id, 'presite': None, 'precell': None, 'postsite': site, 'postcell': None,
                                    'addcell': row.get(F'flag{i}'), 'antflag': row.get(F'flag{i}'), 'fruchange': row.get(F'flag{i}')
                                }
                                temp_list.append(temp_dict)
            # Radios RiLink
            df_site = df_ril.loc[df_ril.postsite == site]
            # Old Radios
            for postcell in df_site.postcell.unique():
                df_t = df_site.loc[(df_site.postcell == postcell) & (~df_site.antflag)]
                temp_int = 0
                ril_ids = self.df_pre_ril.loc[self.df_pre_ril.postcell == postcell, 'rilid'].tolist()
                if df_t.shape[0] == 1:
                    row = df_t.iloc[0]
                    for i in range(1, 5):
                        if row.get(F'port{i}') is not None:
                            temp_int += 1
                            max_rilid = F'{row.get("bbuxmu")}-' + row.get(F'port{i}') + F'-{row.get("fru")}-DATA{i}' if len(ril_ids) < temp_int else ril_ids[temp_int - 1]
                            temp_dict = {
                                'site': site, 'rilid': max_rilid,
                                'fru1': row.get("bbuxmu"), 'rip1': row.get(F'port{i}'),
                                'fru2': row.get("fru"), 'rip2': F'DATA_{i}',
                                'fru': row.get("fru"), 'presite': row.presite, 'precell': row.precell, 'postsite': site, 'postcell': postcell,
                                'addcell': row.addcell, 'antflag': row.antflag, 'fruchange': row.fruchange
                            }
                            temp_list.append(temp_dict)
                elif df_t.shape[0] == 2:
                    row_1 = df_t.iloc[0]
                    row_2 = df_t.iloc[1]
                    temp_int += 1
                    max_rilid = F'{row_1.get("bbuxmu")}-{row_1.get("port1")}-{row_1.get("fru")}-DATA' \
                                F'{"2" if (("4460" in row_1.rrutype) or ("2260" in row_1.rrutype)) else "1"}' \
                        if len(ril_ids) < temp_int else ril_ids[temp_int - 1]
                    temp_dict = {
                        'site': site, 'rilid': max_rilid,
                        'fru1': row_1.get("bbuxmu"), 'rip1': row_1.port1,
                        'fru2': row_1.fru, 'rip2': F'DATA_{"2" if (("4460" in row_1.rrutype) or ("2260" in row_1.rrutype)) else "1"}',
                        'fru': row_1.fru, 'presite': row_1.presite, 'precell': row_1.precell, 'postsite': site, 'postcell': postcell,
                        'addcell': row_1.addcell, 'antflag': row_1.antflag, 'fruchange': row_1.fruchange
                    }
                    temp_list.append(temp_dict)
                    if row_1.get(F'port2') is None:
                        temp_int += 1
                        max_rilid = F'{row_1.get("fru")}-DATA2-{row_2.get("fru")}-DATA1' if len(ril_ids) < temp_int else ril_ids[temp_int - 1]
                        temp_dict = {
                            'site': site, 'rilid': max_rilid,
                            'fru1': row_1.fru, 'rip1': 'DATA_2',
                            'fru2': row_2.fru, 'rip2': F'DATA_1',
                            'fru': row_2.fru, 'presite': row_2.presite, 'precell': row_2.precell, 'postsite': site, 'postcell': postcell,
                            'addcell': row_2.addcell, 'antflag': row_2.antflag, 'fruchange': row_2.fruchange
                        }
                        temp_list.append(temp_dict)
                        # temp_list.append([site, row_2.get('postcell'), str(max_rilid), row_1.get("fru"), 'DATA_2', row_2.get("fru"), 'DATA1'])
                    else:
                        temp_int += 1
                        max_rilid = F'{row_2.get("bbuxmu")}-{row_2.get("port2")}-{row_2.get("fru")}-DATA1' if len(ril_ids) < temp_int else ril_ids[temp_int - 1]
                        temp_dict = {
                            'site': site, 'rilid': max_rilid,
                            'fru1': row_2.get("bbuxmu"), 'rip1': row_2.get("port2"),
                            'fru2': row_2.fru, 'rip2': F'DATA_1',
                            'fru': row_2.fru, 'presite': row_2.presite, 'precell': row_2.precell,  'postsite': site, 'postcell': postcell,
                            'addcell': row_2.addcell, 'antflag': row_2.antflag, 'fruchange': row_2.fruchange
                        }
                        temp_list.append(temp_dict)
            # New Radio
            for postcell in df_site.postcell.unique():
                df_t = df_site.loc[(df_site.postcell == postcell) & df_site.antflag]
                if df_t.shape[0] == 1:
                    row = df_t.iloc[0]
                    for i in range(1, 5):
                        if row.get(F'port{i}') is not None:
                            max_rilid = F'{row.get("bbuxmu")}-' + row.get(F'port{i}') + F'-{row.get("fru")}-DATA{i}'
                            temp_dict = {
                                'site': site, 'rilid': max_rilid,
                                'fru1': row.get("bbuxmu"), 'rip1': row.get(F'port{i}'),
                                'fru2': row.get("fru"), 'rip2': F'DATA_{i}',
                                'fru': row.get("fru"), 'presite': row.presite, 'precell': row.precell, 'postsite': site, 'postcell': postcell,
                                'addcell': row.addcell, 'antflag': row.antflag, 'fruchange': row.fruchange
                            }
                            temp_list.append(temp_dict)
                elif df_t.shape[0] == 2:
                    # elif ('4460' in fru) or max([False] + [True for i in fru if ('4460' in i) or ('2260' in i)]):
                    row_1 = df_t.iloc[0]
                    row_2 = df_t.iloc[1]
                    max_rilid = F'{row_1.get("bbuxmu")}-{row_1.get("port1")}-{row_1.get("fru")}-DATA' \
                                F'{"2" if (("4460" in row_1.rrutype) or ("2260" in row_1.rrutype)) else "1"}'
                    temp_dict = {
                        'site': site, 'rilid': max_rilid,
                        'fru1': row_1.get("bbuxmu"), 'rip1': row_1.port1,
                        'fru2': row_1.fru, 'rip2': F'DATA_{"2" if (("4460" in row_1.rrutype) or ("2260" in row_1.rrutype)) else "1"}',
                        'fru': row_1.fru, 'presite': row_1.presite, 'precell': row_1.precell, 'postsite': site, 'postcell': postcell,
                        'addcell': row_1.addcell, 'antflag': row_1.antflag, 'fruchange': row_1.fruchange
                    }
                    temp_list.append(temp_dict)
                    if row_1.get(F'port2') is None:
                        max_rilid = F'{row_1.get("fru")}-DATA2-{row_2.get("fru")}-DATA1'
                        temp_dict = {
                            'site': site, 'rilid': max_rilid,
                            'fru1': row_1.fru, 'rip1': 'DATA_2',
                            'fru2': row_2.fru, 'rip2': F'DATA_1',
                            'fru': row_2.fru, 'presite': row_2.presite, 'precell': row_2.precell, 'postsite': site, 'postcell': postcell,
                            'addcell': row_2.addcell, 'antflag': row_2.antflag, 'fruchange': row_2.fruchange
                        }
                        temp_list.append(temp_dict)
                    else:
                        max_rilid = F'{row_2.get("bbuxmu")}-{row_2.get("port2")}-{row_2.get("fru")}-DATA1'
                        temp_dict = {
                            'site': site, 'rilid': max_rilid,
                            'fru1': row_2.get("bbuxmu"), 'rip1': row_2.get("port2"),
                            'fru2': row_2.fru, 'rip2': F'DATA_1',
                            'fru': row_2.fru, 'presite': row_2.presite, 'precell': row_2.precell,  'postsite': site, 'postcell': postcell,
                            'addcell': row_2.addcell, 'antflag': row_2.antflag, 'fruchange': row_2.fruchange
                        }
                        temp_list.append(temp_dict)

        self.df_ril = self.df_nan_to_none(df=pd.DataFrame(temp_list)) if len(temp_list) > 0 \
            else pd.DataFrame([], columns=ecolumns)

    def save_xls(self, *, data: dict, file_name: str) -> None:
        data_time_now = datetime.now().strftime('%Y%m%d%H%M%S')
        xls_path = os.path.join(self.base_dir, F'{file_name}_{data_time_now}.xlsx')
        with ExcelWriter(xls_path) as writer:
            for key in data:
                if key == 'Cell_Move':
                    df = data.get(key).copy()
                    df.index.name = 'cell'
                    df.reset_index().to_excel(writer, key, index=False)
                else:
                    data.get(key).to_excel(excel_writer=writer, sheet_name=key, index=False)

    def save_different_dataframe(self):
        data_time_now = datetime.now().strftime('%Y%m%d%H%M%S')
        data = {'Node': pd.concat([self.df_nan_to_none(df=pd.DataFrame.from_dict(self.enodeb).T),
                                   self.df_nan_to_none(df=pd.DataFrame.from_dict(self.gnodeb).T)])}
        if self.df_gnb_cell.shape[0] > 0:
            data['GUtranCell'] = self.df_gnb_cell[['celltype', 'presite', 'precell', 'postsite', 'postcell', 'pregnbid', 'precellid',
                                                   'gnbid', 'cellid', 'carrier', 'BBChange', 'addcell', 'nrpci', 'nrtac', 'rachrootsequence',
                                                   'ssbsubcarrierspacing', 'sc', 'arfcndl', 'arfcnul', 'confpow', 'bschannelbwdl', 'bschannelbwul',
                                                   'sef', 'prefru', 'prefrutype']]
        if self.df_enb_cell.shape[0] > 0:
            data['EUtranCell'] = self.df_enb_cell[['celltype', 'presite', 'precell', 'postsite', 'postcell', 'preenbid', 'precellid',
                                                   'enbid', 'cellid', 'carrier', 'BBChange', 'addcell', 'freqband', 'earfcndl', 'earfcnul',
                                                   'dlchannelbandwidth', 'ulchannelbandwidth', 'physicallayercellid', 'rachrootsequence',
                                                   'cellrange', 'tac', 'userlabel', 'isdlonly', 'latitude', 'longitude', 'altitude',
                                                   'eutrancellcoverage', 'sc', 'noofrx', 'nooftx', 'confpow', 'sef', 'prefru', 'prefrutype',
                                                   'nbiotcelltype', 'precellref', 'postcellref']]
        if self.df_ant.shape[0] > 0:
            data['AntennaSystem'] = self.df_ant[['presite', 'precell', 'postsite', 'postcell', 'celltype', 'addcell', 'antflag', 'fruchange',
                                                 'prefru', 'prefrutype', 'frutypecix', 'rrushared', 'sef', 'confpow', 'confpowcix', 'sc', 'carrier',
                                                 'nooftx', 'noofrx', 'raug', 'rfb', 'dl_ul_delay_att', 'fru', 'rfp',
                                                 'trecid', 'aug', 'au', 'asu', 'aup', 'mt']]
        if self.df_ril.shape[0] > 0:
            data['RiLink'] = self.df_ril[['site', 'rilid', 'fru1', 'rip1', 'fru2', 'rip2', 'fru', 'presite', 'precell', 'postsite',
                                          'postcell', 'addcell', 'antflag', 'fruchange']]
        if self.df_pre_ril.shape[0] > 0:
            data['Pre_RiLink'] = self.df_pre_ril[['site', 'rilid', 'fru1', 'rip1', 'fru2', 'rip2', 'fru', 'presite', 'precell', 'postsite',
                                                  'postcell', 'addcell', 'antflag', 'fruchange', 'port_index']]
        self.save_xls(data=data, file_name='1_Node_Report')

        # Save Different DataFrames for LTE
        if len(self.enodeb) > 0:
            data = {
                'EUtranFrequency': self.df_enb_ef[['postsite', 'freqid', 'earfcndl', 'flag', 'fdn']],
                'EUtranFreqRelation': self.df_enb_er[['postsite', 'postcell', 'relid', 'earfcndl', 'freqid', 'creprio', 'cprio',
                                                      'vprio', 'thhigh', 'thlow', 'flag', 'presite', 'precell', 'fdn']],
                'EUtranCellRelation': self.df_enb_ee[['postsite', 'postcell', 'relid', 'crelid', 'israllowed', 'scell', 'celltype',
                                                      'flag', 'plmn', 'enbid', 'cellid', 'xid', 'xcellid', 'earfcndl', 'fdn']],
                'ExternalENodeBFunction': self.df_enb_ex[['postsite', 'xid', 'plmn', 'enbid', 'x2id', 'ipv4', 'flag', 'fdn', 'x2fdn']],
                'ExternalEUtranCell': self.df_enb_ec[['postsite', 'xid', 'xcellid', 'celltype', 'plmn', 'enbid', 'cellid', 'tac',
                                                      'pci', 'freqid', 'earfcndl',  'flag', 'fdn']],
            }
            if (self.df_enb_ef.shape[0] > 0 or self.df_enb_er.shape[0] > 0 or self.df_enb_ee.shape[0] > 0 or
                    self.df_enb_ex.shape[0] > 0 or self.df_enb_ec.shape[0] > 0):
                self.save_xls(data=data, file_name='2_lte_EUtraNetwork_Report')

            data = {
                'GUtranSyncSignalFrequency': self.df_enb_nf[['postsite', 'freqid', 'arfcn', 'smtcScs', 'flag']],
                'GUtranFreqRelation': self.df_enb_nr[['postsite', 'postcell', 'relid', 'arfcn', 'smtcScs', 'freqid', 'creprio',
                                                      'flag', 'presite', 'precell']],
                'GUtranCellRelation': self.df_enb_ne[['postsite', 'postcell', 'relid', 'crelid', 'israllowed', 'flag', 'plmn',
                                                      'gnbid', 'cellid', 'xid', 'xcellid', 'arfcn']],
                'ExternalGNodeBFunction': self.df_enb_nx[['postsite', 'xid', 'plmn', 'gnbid', 'gnblen', 'x2id', 'ipv4', 'flag']],
                'ExternalGUtranCell': self.df_enb_nc[['postsite', 'xid', 'xcellid', 'plmn', 'gnbid', 'cellid', 'pci', 'freqid', 'arfcn', 'flag']],
            }
            if (self.df_enb_nf.shape[0] > 0 or self.df_enb_nr.shape[0] > 0 or self.df_enb_ne.shape[0] > 0 or
                    self.df_enb_nx.shape[0] > 0 or self.df_enb_nc.shape[0] > 0):
                self.save_xls(data=data, file_name='3_lte_GUtraNetwork_Report')

            data = {
                'UtranFrequency': self.df_enb_uf[['postsite', 'freqid', 'uarfcn', 'flag']],
                'UtranFreqRelation': self.df_enb_ur[['postsite', 'postcell', 'relid', 'uarfcn', 'freqid', 'creprio', 'csprio',
                                                     'csprioec', 'cprio', 'flag', 'presite', 'precell']],
                'UtranCellRelation': self.df_enb_ue[['postsite', 'postcell', 'relid', 'crelid', 'flag', 'xcellid', 'plmn', 'cellid', 'uarfcn']],
                'ExternalUtranCell': self.df_enb_uc[['postsite', 'xcellid', 'plmn', 'cellid', 'pci', 'lac', 'rac', 'freqid', 'flag', 'uarfcn']],
            }
            if self.df_enb_uf.shape[0] > 0 or self.df_enb_ur.shape[0] > 0 or self.df_enb_ue.shape[0] > 0 or self.df_enb_uc.shape[0] > 0:
                self.save_xls(data=data, file_name='4_lte_UtraNetwork_Report')
            data = {
                'GeranFreqGroup': self.df_enb_gs[['postsite', 'gfreqgid', 'group', 'flag']],
                'GeranFrequency': self.df_enb_gf[['postsite', 'freqid', 'bcch', 'band', 'gfreqgid', 'flag', 'group', ]],
                'ExternalGeranCell': self.df_enb_gc[['postsite', 'xcellid', 'ci', 'ncc', 'bcc', 'lac', 'plmn', 'freqid', 'flag', 'bcch']],
                'GeranFreqGroupRelation': self.df_enb_gr[['postsite', 'postcell', 'relid', 'creprio', 'gfreqgid', 'flag',
                                                          'presite', 'precell', 'group']],
                'GeranCellRelation': self.df_enb_ge[['postsite', 'postcell', 'relid', 'crelid', 'xcellid', 'flag',
                                                     'presite', 'precell', 'ci', 'lac', 'plmn', 'group']],
            }
            if (self.df_enb_gs.shape[0] > 0 or self.df_enb_gf.shape[0] > 0 or self.df_enb_gc.shape[0] > 0 or
                    self.df_enb_gr.shape[0] > 0 or self.df_enb_ge.shape[0] > 0):
                self.save_xls(data=data, file_name='5_lte_GeraNetwork_Report')

    """
!!!!!!!!!!!!!!!!!!!!!!!!! Band and Cell Name in T-Mobile !!!!!!!!!!!!!!!!!!!!!!!!!
Tech	Frequency	Naming convention	BAND	Band name
N2500	2500 MHz	A+EutranCellName	B41	N2500
N600    600 MHz	    K+EutranCellName	B71	N600
N1900	1900 MHz	J+EutranCellName	B71	N1900
NBIoT	2100 MHz	Z+EutranCellName	 	NB-IOT AWS
NBIoT	1900 MHz	Y+EutranCellName	 	NB-IOT PCS
NBIoT	700 MHz	    X+EutranCellName	 	NB-IOT 700
L2500	2500 MHz	T+EutranCellName	B41	L2500
L2100	2100 MHz	L+EutranCellName	B4/B66	LTE AWS
L1900	1900 MHz	B+EutranCellName	B2	LTE PCS
L700	700 MHz	    D+EutranCellName	B12	L700
L600	600 MHz	    E+EutranCellName	B71	L600
L850	850 MHz	    C+EutranCellName	B26	L850
AWS 3	 	    F+EutranCellName	B66	LTE AWS 3
LAA     46          G+EutranCellName    B46

    """

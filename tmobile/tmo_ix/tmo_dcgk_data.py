import re
import sys


from .tmo_data import BB_dict


class tmo_dcgk_data:
    def __init__(self, node: str, merged_dict: dict):
        self.node = node
        self.dcg = merged_dict
        if self.dcg is None: sys.exit(1)
        self.mo_list = sorted([_ for _ in self.dcg.keys()])
        if len(self.mo_list) < 1: sys.exit(1)
        self.BBType, self.BBId = self.set_equipment_name()
        self.fingerprint = self.site_extract_data(self.find_mos_with_end_str(end_str=',SystemFunctions=1,Lm=1')[0]).get('fingerprint') if (
                len(self.find_mos_with_end_str(end_str=',SystemFunctions=1,Lm=1')) > 0) else None
        self.site_xmu_dict = {}
        self.set_site_xmu_dict()

    def set_equipment_name(self) -> (str or None, str or None):
        for mo in self.find_mos_with_end_moc(moc='FieldReplaceableUnit'):
            tmp_str = self.dcg.get(mo).get('productData', {}).get('productName')
            if tmp_str is not None:
                for val in BB_dict.keys():
                    if val in tmp_str:
                        return val, mo.split('=')[-1]
        return None, None

    def set_site_xmu_dict(self):
        self.site_xmu_dict[self.node] = []
        for mo in self.find_mos_with_end_moc(moc='FieldReplaceableUnit'):
            data = self.site_extract_data(mo)
            product_name = data.get('productData', {}).get('productName')
            if product_name is not None:
                if 'R503' in product_name: self.site_xmu_dict[self.node].append(data.get('fieldReplaceableUnitId'))

    # def set_enodeb_id(self):
    #     mo = self.find_mos_with_end_moc(moc='ENodeBFunction')[0]
    #     self.enodeb_id = self.dcg.get(mo).get('eNBId')

    def get_related_mo(self, mo, attribute):
        reference = self.dcg.get(mo).get(attribute)
        mo = None
        if (reference is not None) & (len([_ for _ in self.mo_list if reference in _]) > 0):
            mo = [_ for _ in self.mo_list if reference in _][0]
        return mo if mo else None
    
    @staticmethod
    def normalize_ip6(ip):
        return ':'.join([_.lstrip('0') for _ in ip.split(':')]) if ip else None

    def set_oam_ip_vlan_du(self):
        oam_ip, vlan = None, None
        if len([_ for _ in self.mo_list if ('IpOam=' in _) and ('Ip=' in _)]) > 0:
            mo = [_ for _ in self.mo_list if ('IpOam=' in _) and ('Ip=' in _)][0]
            oam_ip = self.dcg.get(mo).get('nodeIpv6Address')
        oam_ip = self.normalize_ip6(oam_ip)
        if len([_ for _ in self.mo_list if ('IpHostLink' in _)]) > 0:
            mo = [_ for _ in self.mo_list if ('IpHostLink' in _)][0]
            mo = self.get_related_mo(mo, 'ipInterfaceMoRef')
            if mo: vlan = self.dcg.get(mo).get('vid')
        self.oam_ip = oam_ip
        self.oam_vlan = vlan

    def get_ip_vlan_bu(self, first_str, second_str):
        oam_ip, vlan, accesspoint = None, None, None
        if len([_ for _ in self.mo_list if (first_str + '=' in _)]) > 0:
            mo = [_ for _ in self.mo_list if (first_str + '=' in _)][0]
        else: return None
        accesspoint = self.dcg.get(mo, {}).get(second_str)
        mo = self.get_related_mo(mo, second_str)
        if mo is None:
            return None, None
        oam_ip = self.dcg.get(mo).get('address', '')
        oam_ip = self.normalize_ip6(oam_ip)
        parent = self.get_parent_mo_form_mo(mo=mo)
        mo = self.get_related_mo(parent, 'encapsulation')
        if mo is None:
            return oam_ip, None
        vlan = self.dcg.get(mo).get('vlanId', '')
        return oam_ip, vlan, accesspoint

    def set_oam_ip_vlan_bu(self):
        self.oam_ip, self.oam_vlan, self.oam_access_point = self.get_ip_vlan_bu('OamAccessPoint', 'accessPoint')

    def set_bearer_ip_vlan_bu(self):
        self.bearer_ip, self.bearer_vlan, self.oam_access_point = self.get_ip_vlan_bu('ENodeBFunction', 'upIpAddressRef')

    def set_bearer_ip_vlan_du(self):
        bearer_ip, vlan = None, None
        mo = [_ for _ in self.mo_list if ('ENodeBFunction=' in _)]
        if len(mo) > 0:
            mo = self.get_related_mo(mo[0], 'upIpAddressRef')
            if mo:
                bearer_ip = self.dcg.get(mo).get('ipAddress')
                mo = self.get_related_mo(mo, 'ipInterfaceMoRef')
                if mo: vlan = self.dcg.get(mo).get('vid')
        self.bearer_ip = self.normalize_ip6(bearer_ip)
        self.bearer_vlan = vlan

    def set_default_router_du(self):
        router_ip = None
        if len([_ for _ in self.mo_list if ('IpRoutingTable=' in _ )]) > 0:
            mo = [_ for _ in self.mo_list if ('IpRoutingTable=' in _ )][0]
            static_routes = self.dcg.get(mo).get('staticRoutes', [])
            for route in static_routes:
                route_ip = self.normalize_ip6(route.get('nextHopIpAddr'))
                if ':'.join(self.bearer_ip.split(':')[:-1]) in route_ip: router_ip = route_ip
        self.oam_default_router = router_ip

    def set_default_router_bu(self):
        router_add = None
        if len([_ for _ in self.mo_list if ('OamAccessPoint=' in _)]) > 0:
            mo = [_ for _ in self.mo_list if ('OamAccessPoint=' in _)][0]
        else: return None
        accesspoint = self.dcg.get(mo).get('accessPoint', '')
        router_info_list = [_ for _ in accesspoint.split(',') if 'Router' in _]
        if len(router_info_list) != 1:
            return None
        router_info = router_info_list[0]
        if len([_ for _ in self.mo_list if ('NextHop=' in _) & (router_info in _)]) > 0:
            mo = [_ for _ in self.mo_list if ('NextHop=' in _) & (router_info in _)][0]
            router_add = self.dcg.get(mo).get('address')
        self.oam_default_router = router_add

    def set_ntp_server_address(self):
        ntp_address = []
        for ntp_mo in [_ for _ in self.mo_list if ('NtpServer' in _)]: ntp_address.append(self.dcg.get(ntp_mo).get('serverAddress'))
        self.ntp_server = list(set([self.normalize_ip6(_) for _ in ntp_address if _]))

    def set_bearer_default_router(self): self.bearer_default_router = ''

    # def convert_dict_to_str(self, in_dict):
    #     if (type(in_dict) == str): return in_dict
    #     elif (type(in_dict) == int): return str(in_dict)
    #     elif (type(in_dict) == dict): return '##'.join([str(key) + '=' + str(val) for key, val in in_dict.items()])

    def site_extract_data(self, mo):
        data = self.dcg.get(mo)
        if data is None: data = self.dcg.get(self.get_mo_name_ending_str(mo))
        return {key[0].lower() + key[1:]: data[key] for key in data}

    def find_mos_with_end_moc(self, *, moc: str) -> list: return [_ for _ in self.mo_list if re.match(F'.*,{moc}=[^,=]*$', _)]

    def find_mos_with_end_str(self, *, end_str: str) -> list: return [_ for _ in self.mo_list if re.match(F'.*{end_str}$', _)]

    def find_mos_list_from_fdn_moc(self, *, mo_fdn: str, moc: str) -> list:
        return [_ for _ in self.mo_list if re.match(F'{mo_fdn},{moc}=[^,=]*$', _)]

    def get_sau_id(self):
        mo = self.find_mo_ending_with_parent_str('FieldReplaceableUnit')
        mo = [_ for _ in mo if 'SAU' in _]
        return self.site_extract_data(mo[0]).get('fieldReplaceableUnitId', 'SAU-1') if len(mo) > 0 else 'SAU-1'

    def find_mo_ending_with_parent_str(self, moc, parent=''):
        if parent == '': return [_ for _ in self.mo_list if re.match(F'.*,{moc}=[^,=]*$', _)]
        else: return [_ for _ in self.mo_list if re.match(F'{parent},{moc}=[^,=]*$', _)]

    def find_mo_ending_with_parent_str_with_id(self, moc, moid='', parent=''):
        if parent == '': return self.find_mo_ending_with_id(moc, moid)
        else: return [_ for _ in self.find_mo_ending_with_parent_str(moc, parent) if _.endswith('=' + str(moid))]

    def get_mo_attr_str(self, mo): return {key[0].lower() + key[1:]: self.dcg.get(mo).get(key) for key in self.dcg.get(mo)}

    def find_mo_ending_with_id(self, mo, moid): return [_ for _ in self.mo_list if re.match(F'.*,{mo}={moid}$', _)]

    def get_mo_name_ending_str(self, search): return [_ for _ in self.mo_list if _.endswith(search)][0]

    def get_mos_w_end_str(self, *, mo_ldn: str) -> list: return [_ for _ in self.mo_list if _.endswith(mo_ldn)]

    def get_para_value_for_mo(self, *, mo: str, para: str) -> str or list or dict: return self.dcg.get(mo).get(para)

    @staticmethod
    def get_parent_mo_form_mo(*, mo: str) -> str: return ','.join(mo.split(',')[:-1])

    @staticmethod
    def lower_first_character(*, para: str) -> str: return para[0].lower() + para[1:]

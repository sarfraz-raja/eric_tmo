from .BaseScript import BaseScript


class A_01_OAM(BaseScript):
    def create_msg(self):
        self.script['txt'].extend([
            F'setenv p AUTH yes',
            F'setenv p BOOTPORT {self.site_dict["bootport"]}',
            F'setenv p {self.site_dict["bootport"]}_IPV6_IP {self.site_dict["ipv6_ip"]}',
            F'setenv p {self.site_dict["bootport"]}_IPV6_GW {self.site_dict["ipv6_gw"]}',
            F'setenv p {self.site_dict["bootport"]}_IPV6_NM {self.site_dict["ipv6_nm"]}',
            F'setenv p {self.site_dict["bootport"]}_IPVER {self.site_dict["ipver"]}',
            F'delenv p DEFAULT_VLANID',
            F'setenv p {self.site_dict["bootport"]}_VLANID {self.site_dict["vlanid"]}',
            F'delenv p BOOTMODE',
            F'setenv p BOOTMODE static',
            F'setenv p RS_IP {self.site_dict["rs_ip"]}',
            F'setenv p SAP_ID {self.site_dict["node"]}',
            F'setenv p FTPTELNET_ON NO',
            F'setenv p MAX_PNP_CLEAR_COUNT 1',
            F'setenv p ECMP_ENABLE 1',
            F'setenv p NE_TYPE {self.site_dict["ne_type"]}',
            F'setenv p NE_ID {self.site_dict["ne_id"]}',
        ])
        if self.site_dict["ne_type2"]:
            self.script['txt'].extend([F'setenv p NE_TYPE2 {self.site_dict["ne_type2"]}',
                                       F'setenv p NE_ID2 {self.site_dict["ne_id2"]}'])
        self.script['txt'].extend([
            F'setenv p PORT_0_0_0_SPEED {self.site_dict["speed"]}',
            F'setenv p MAX_PNP_CLEAR_COUNT 1',
        ])
        if self.site_dict["flag"]: self.script['txt'].append(F'setenv p DU_LD_FLAG {self.site_dict["flag"]}')
        self.script['txt'].extend(['', 'sync', 'reboot'])

from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C05_NodeInfo(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        if self.enbdata.get('BBChange') is False or self.gnbdata.get('BBChange') is False: return
        node_data = self.gnbdata if (self.enbdata.get('MMBB') and self.gnbdata['lte_plength'] != '32') or len(self.enbdata) == 0 else self.enbdata
        self.relative_path = ['01_AP', self.node, self.node, 'NodeInfo.xml']
        tmp_dict = {
                    'attributes': {'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', 'xsi:noNamespaceSchemaLocation': 'NodeInfo.xsd'},
                    'name': self.node,
                    'nodeIdentifier': node_data['nodeIdentifier'],
                    'ipAddress': node_data['oam_ip'],
                    'nodeType': node_data['nodeType'],
                    'ossPrefix': node_data['dnPrefix'],
                    'timeZone': node_data['timeZone'],
                    'autoIntegration': {'upgradePackageName': node_data["sw"]},
                    'users': {'secureUser': {'name': node_data["username"], 'password': node_data["password"]}},
                    'license': {
                        # 'licenseFile': F'ATTL-{self.node}-BB{self.enbdata["BBType"]}.zip',
                        'installLicense': 'true' if node_data["fingerprint"] == self.node else 'false'
                    },
                    'artifacts': {
                        'siteBasic': self.usid.script_dict["SB"],
                        'siteEquipment': self.usid.script_dict["SE"],
                        'siteInstallation': self.usid.script_dict["SI"],
                        # 'configurations': {
                        #     'nodeConfiguration': [
                        #         F'RN_01_TMO_Transport_{self.enbdata["BBType"]}_{self.node}.xml',
                        #         F'RN_02_TMO_ENodeBFunction_{self.enbdata["BBType"]}_{self.node}.xml',
                        #         F'RN_03_TMO_TermPointToMme_{self.enbdata["BBType"]}_{self.node}.xml',
                        #     ]
                        # }
                    }
                }
        if len(self.usid.script_dict['conf']) > 0:
            tmp_dict['artifacts']['configurations'] = {'nodeConfiguration': self.usid.script_dict['conf']}


        self.script_list = [self.ap_xml_document_form_dict(mo_name='nodeInfo', para_dict=tmp_dict)]

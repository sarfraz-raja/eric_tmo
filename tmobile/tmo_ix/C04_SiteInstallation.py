from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C04_SiteInstallation(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        if self.enbdata.get('BBChange') is False or self.gnbdata.get('BBChange') is False: return
        node_data = self.gnbdata if (self.enbdata.get('MMBB') and self.gnbdata['lte_plength'] != '32') or len(self.enbdata) == 0 else self.enbdata
        self.usid.script_dict["SI"] = F'SiteInstallation_{self.node}.xml'
        self.relative_path = ['01_AP', self.node, self.node, self.usid.script_dict["SI"]]
        self.script_list = [
            self.ap_xml_document_form_dict(
                mo_name='RbsSiteInstallationFile',
                para_dict={
                    'attributes': {'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                                   'xsi:noNamespaceSchemaLocation': F'SiteInstallation.xsd'},
                    'Format': {'attributes': {'revision': 'K'}},
                    'InstallationData': {
                        'attributes': {'logicalName': self.node, 'tnPort': node_data["TnPort"], 'vlanId': node_data['oam_van']},
                        'OamIpConfigurationData': {'attributes': {'defaultRouter0': node_data['oam_gway'], 'ipAddress': node_data['oam_ip'],
                                                                  'subnetMask': node_data['oam_mask']}},
                        'SmrsData': {'attributes': {'summaryFilePath': '', 'address': ''}}
                    },

                }
            )
        ]

from xml.dom.minidom import Document
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C07_01b_lte_nr_InternalRouting(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        if not self.enbdata.get('MMBB') or self.enbdata.get('BBChange') is False: return
        if self.enbdata['lte_plength'] == '32' or self.gnbdata['lte_plength'] == '32': return
        me_dict = {'managedElementId': self.node, 'Transport': {'transportId': '1', 'Router': [
            {'routerId': self.gnbdata['lte'], 'RouteTableIPv4Static': {'routeTableIPv4StaticId': '1', 'Dst': {
                'attributes': {'xc:operation': 'create'}, 'dstId': '2', 'dst': F'{self.enbdata.get("lte_ip")}/32', 'NextHop': {
                    'attributes': {'xc:operation': 'create'}, 'nextHopId': '1', 'adminDistance': '1', 'bfdMonitoring': 'false',
                    'reference': F'Transport=1,Router={self.enbdata["lte"]}'}   # 'discard': 'false',
            }}},
            {'routerId': self.enbdata['lte'], 'RouteTableIPv4Static': {'routeTableIPv4StaticId': '1', 'Dst': {
                'attributes': {'xc:operation': 'create'}, 'dstId': '2', 'dst': F'{self.gnbdata.get("lte_ip")}/32', 'NextHop': {
                    'attributes': {'xc:operation': 'create'}, 'nextHopId': '1', 'adminDistance': '1', 'bfdMonitoring': 'false',
                    'reference': F'Transport=1,Router={self.gnbdata["lte"]}'}   # 'discard': 'false',
            }}},
        ]}}

        self.write_backup_script_file(script_list=self.mos_script_list_form_dict(para_dict=me_dict, mo_fdn='ManagedElement'))
        doc, config = self.main_rcp_msg_start(msg_id='MMBB_InternalRouting')
        config.appendChild(self.netconf_mo_form_dict(para_dict=me_dict, moc='ManagedElement'))
        self.script_list = [self.rcp_msg_capabilities(), doc, self.rcp_msg_close()]

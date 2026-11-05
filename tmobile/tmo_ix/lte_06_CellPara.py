from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class lte_06_CellPara(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0: return
        if len(self.df_enb_cell.loc[(self.df_enb_cell.addcell & self.df_enb_cell.celltype.isin(['FDD', 'TDD']))].index) == 0: return

        self.motype = 'Lrat'
        self.script_list.extend([self.rcp_msg_capabilities(), self.create_rpc_msg(), self.rcp_msg_close()])

    def create_rpc_msg(self):
        doc, config = self.main_rcp_msg_start(msg_id='cell_para')
        me_mo = self.mo_add_form_dict_xml({'managedElementId': self.node}, 'ManagedElement')
        config.appendChild(me_mo)
        enb_mo = self.mo_add_form_dict_xml({'eNodeBFunctionId': '1'}, 'ENodeBFunction')
        me_mo.appendChild(enb_mo)
        tmp_celltype = {'FDD': 'EUtranCellFDD', 'FDDId': 'eUtranCellFDDId', 'TDD': 'EUtranCellTDD', 'TDDId': 'eUtranCellTDDId', 'IOT': 'NbIotCell', 'IOTId': 'NbIotCellId'}
        for index, row in self.usid.df_enb_cell.loc[(self.usid.df_enb_cell.postsite == self.node) &
                                                    self.usid.df_enb_cell.addcell & self.usid.df_enb_cell.celltype.isin(['FDD', 'TDD'])].iterrows():
            tag = F'{tmp_celltype.get(row.celltype, "")}MO'
            parent = tmp_celltype.get(row.celltype, "")
            parentid = tmp_celltype.get(F'{row.celltype}Id', "")
            ecell_mo = self.mo_add_form_dict_xml({parentid: row.postcell}, parent)
            enb_mo.appendChild(ecell_mo)
            parent_str = '' if row.fdn is None else row.fdn
            children = self.MoRelation.objects.filter(parent=parent, tag=tag, software=self.usid.client.software)
            for child in children:
                mos = self.log_append_child_tags(moc=child.child, tag=tag, parent_str=parent_str, pre_site=row.presite)
                for mo in mos: ecell_mo.appendChild(mo)
        return doc

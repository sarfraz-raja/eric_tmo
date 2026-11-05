from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class lte_04_Delete_EUtranCell(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        # if len(self.enbdata) == 0: return
        self.script_list.extend(self.delete_cell_mos())

    def delete_cell_mos(self):
        lines = []
        for index, row in self.usid.df_enb_cell.loc[(self.usid.df_enb_cell.presite == self.node) &
                            (self.usid.df_enb_cell.movement == 'yes') & (~self.usid.df_enb_cell.fdn.isnull())].iterrows():
            site = self.usid.sites.get(F'site_{row.presite}')
            cell_ldn = self.mos_check_text_element(row.fdn)
            lines.extend([F'####:----------------> DELETE MOs for CELL {row.precell} <----------------:####',
                          F'get {cell_ldn}$ operationalState 1',
                          'if $nr_of_mos > 0', 'print ERROR: Soft Lock the cells manually. ABORT !!!', 'l-', 'return', 'fi'])
            # NbIotCell
            for ref in site.site_extract_data(row.fdn).get('reservedBy'):
                if 'NbIotCell' in ref:
                    lines.extend([F'bl {self.mos_check_text_element(ref)}$', F'del {self.mos_check_text_element(ref)}$'])
            lines.extend([F'set {cell_ldn}$ sectorCarrierRef null', F'del {cell_ldn},UeMeasControl=1,PmUeMeasControl=',
                          F'del {cell_ldn},ReportConfigEUtraInt', F'del {cell_ldn},ReportConfigInterRatPm',
                          F'rdel {cell_ldn}$', ''])
            rfb_list = []
            
            # SectorCarrier
            for sc in site.site_extract_data(row.fdn).get('sectorCarrierRef'):
                if sc is None: continue
                mo_ldn = site.get_mo_name_ending_str(sc)
                for sc_res in site.site_extract_data(mo_ldn).get('reservedBy'):
                    if (sc_res is None) or (sc_res == ''):
                        pass
                    elif 'UlCompGroup' in sc_res:
                        lines.extend([F'bl {self.mos_check_text_element(sc_res)}$', F'del {self.mos_check_text_element(sc_res)}$'])
                    elif 'NbIotCell' in sc_res:
                        lines.extend([F'bl {self.mos_check_text_element(sc_res)}$', F'del {self.mos_check_text_element(sc_res)}$'])
                lines.extend([F'del {self.mos_check_text_element(mo_ldn)}$'])
                rfb_list.extend(site.site_extract_data(mo_ldn).get('rfBranchTxRef'))
                rfb_list.extend(site.site_extract_data(mo_ldn).get('rfBranchRxRef'))
                # SectorEquipmentFunction
                mo_ldn = site.site_extract_data(mo_ldn).get('sectorFunctionRef')
                if (mo_ldn is not None) or (mo_ldn != ''):
                    mo_ldn = site.get_mo_name_ending_str(mo_ldn)
                    rfb_list.extend(site.site_extract_data(mo_ldn).get('rfBranchRef'))
                    lines.extend([F'bl {self.mos_check_text_element(mo_ldn)}$',
                                  F'get {self.mos_check_text_element(mo_ldn)}$ reservedBy SectorCarrier=',
                                  F'if $nr_of_mos = 0', F'del {self.mos_check_text_element(mo_ldn)}$', F'fi', F''])

                rfb_list = list(dict.fromkeys(rfb_list).keys())
                aup_refs, rfp_refs = [], []
                for rfb in rfb_list:
                    rfb_mo = site.get_mo_name_ending_str(rfb)
                    rfb_data = site.site_extract_data(rfb_mo)
                    lines.extend([
                        F'get {self.mos_check_text_element(rfb_mo)}$ reservedBy SectorEquipmentFunction=',
                        F'if $nr_of_mos = 0', F'del {self.mos_check_text_element(rfb_mo)}$', F'fi'
                    ])
                    aup_ref, rfp_ref = rfb_data.get('auPortRef'), rfb_data.get('rfPortRef')
                    if aup_ref is not None and len(aup_ref) > 0: aup_refs.extend(aup_ref)
                    if rfp_ref is not None and len(rfp_ref) > 0: rfp_refs.append(rfp_ref)
                fru_refs = [','.join(_.split(',')[:-1]) for _ in rfp_refs]
                fru_refs = list(dict.fromkeys(fru_refs).keys())
                for fru_ref in fru_refs:
                    fru_mo = site.get_mo_name_ending_str(fru_ref)
                    lines.extend(['', F'bl {self.mos_check_text_element(fru_mo)},', F'bl {self.mos_check_text_element(fru_mo)}$'])
                    # RiLink Delete
                    fruid = fru_mo.split('=')[-1]
                    for mo in site.find_mo_ending_with_parent_str('RiLink'):
                        if mo is None: continue
                        riPortRefs = [site.site_extract_data(mo).get('riPortRef1', None), site.site_extract_data(mo).get('riPortRef2', None)]
                        for riPortRef in riPortRefs:
                            if (riPortRef is None) or (riPortRef == ''): continue
                            elif F'={fruid},RiPort=' in riPortRef:  lines.append(F'del {self.mos_check_text_element(mo)}$')

                    rfp_refs = site.find_mo_ending_with_parent_str('RfPort', fru_mo)
                    for rfp_ref in rfp_refs:
                        rfp_mo = site.get_mo_name_ending_str(rfp_ref)
                        rfp_data = site.site_extract_data(rfp_mo)
                        ret_tma_mos = rfp_data.get('reservedBy')
                        for ret_tma in ret_tma_mos:
                            if (ret_tma is None) or (ret_tma == ''): continue
                            ret_tma_mo = site.get_mo_name_ending_str(ret_tma)
                            if ',AntennaNearUnit=' in ret_tma_mo:
                                lines.extend([F'bl {self.mos_check_text_element(ret_tma_mo)}$'])
                                ret_rel_mos = site.find_mo_ending_with_parent_str('RetSubUnit', ret_tma_mo)
                                for ret_rel in ret_rel_mos:
                                    ret_rel_ress = site.site_extract_data(site.get_mo_name_ending_str(ret_rel)).get('reservedBy')
                                    if len(ret_rel_ress) != 0: lines.extend([
                                        F'set {self.mos_check_text_element(site.get_mo_name_ending_str(_))}$ retSubunitRef null' for _ in ret_rel_ress])
                                tma_rel_mos = site.find_mo_ending_with_parent_str('TmaSubUnit', ret_tma_mo)
                                for tma_rel in tma_rel_mos:
                                    tma_rel_ress = site.site_extract_data(site.get_mo_name_ending_str(tma_rel)).get('reservedBy')
                                    if len(tma_rel_ress) != 0: lines.extend([
                                        F'set {self.mos_check_text_element(site.get_mo_name_ending_str(_))}$ tmaRef null' for _ in tma_rel_ress])
                                lines.extend([F'del {self.mos_check_text_element(ret_tma_mo)},', F'del {self.mos_check_text_element(ret_tma_mo)}$'])
                    lines.extend([F'del {self.mos_check_text_element(fru_mo)},'])
                    lines.extend([F'del {self.mos_check_text_element(fru_mo)}$', ''])
                # ---AuPort---
                if len(aup_refs) > 0: aup_refs = [site.get_mo_name_ending_str(_) for _ in aup_refs if len(_) > 0]
                if len(aup_refs) > 0: aup_refs = list(dict.fromkeys(aup_refs).keys())
                if len(aup_refs) > 0: lines.extend([F'del {self.mos_check_text_element(_)}$' for _ in aup_refs if len(_) > 0])
                # ---AntennaSubunit---
                asu_refs = []
                if len(aup_refs) > 0: asu_refs = [','.join(_.split(',')[:-1]) for _ in aup_refs if len(_) > 0]
                if len(asu_refs) > 0: asu_refs = list(dict.fromkeys(asu_refs).keys())
                for asu in asu_refs:
                    asu_mo = self.mos_check_text_element(asu)
                    lines.extend([
                        '', F'$asu_delete_1 = 0', F'lpr {asu_mo},AuPort=',
                        F'if $nr_of_mos = 0', F'$asu_delete_1 = 1', 'fi',
                        F'get {asu_mo} retSubunitRef RetSubUnit', 'if $nr_of_mos = 0 && $asu_delete_1 = 1', F'del {asu_mo}$', 'fi', ''
                    ])
                # ---AntennaUnit---
                au_refs = []
                if len(asu_refs) > 0: au_refs = [','.join(_.split(',')[:-1]) for _ in asu_refs if len(_) > 0]
                if len(au_refs) > 0: au_refs = list(dict.fromkeys(au_refs).keys())
                for au in au_refs:
                    lines.extend([
                        F'lpr {self.mos_check_text_element(au)},',
                        'if $nr_of_mos = 0', F'del {self.mos_check_text_element(au)}$', 'fi', ''
                    ])
                # ---AntennaUnitGroup---
                aug_refs = []
                if len(au_refs) > 0: aug_refs = [','.join(_.split(',')[:-1]) for _ in au_refs if len(_) > 0]
                if len(aug_refs) > 0: aug_refs = list(dict.fromkeys(aug_refs).keys())
                for aug in aug_refs:
                    lines.extend([
                        F'lpr {self.mos_check_text_element(aug)},',
                        'if $nr_of_mos = 0', F'del {self.mos_check_text_element(aug)}$', 'fi', ''
                    ])
            if len(lines) > 0:
                lines += ['', '']

        if len(lines) > 0: lines = self.get_parameters() + lines + self.get_parameters()
        return lines

    def get_parameters(self):
        return [
            'sts',
            'hget ^ENodeBFunction=1$ ^eNBId$|^eNodeBPlmnId$|^sctpRef$|^upIpAddressRef$|^intraRanIpAddressRef$|6eranVlanPortRef$',
            'hget ^GNBCUUPFunction=.* ^gNBId$|^gNBIdLength$|^pLMNIdList$',
            'hget ^GNBDUFunction=.* ^gNBId$|^gNBIdLength$|^f1SctpEndPointRef$',
            'hget ^TermPointToMme=.* State|ipAddress',
            'hget ^TermPointToAmf=.* State|ipv4Address',
            'hget ^(FieldReplaceableUnit|PlugInUnit|AuxPlugInUnit)=.* state|productData|isSharedWithExternalMe',
            'hget ^RiLink=.* linkRate|operationalState|riPortRef',
            'hget ^RfBranch=.* ^auPortRef$|^rfPortRef$',
            'hget ^RfBranch=.* ^dlAttenuation$|^ulAttenuation$',
            'hget ^RfBranch=.* ^dlTrafficDelay$|^ulTrafficDelay$',
            'hget ^SectorEquipmentFunction= rfBranchRef|reservedBy',
            'hget ^SectorCarrier= ^configuredMaxTxPower$|^noOfRxAntennas$|^noOfTxAntennas$|^sectorFunctionRef$|^rfBranchRxRef$|^rfBranchTxRef$',
            'st sec',
            '',
            '',
        ]

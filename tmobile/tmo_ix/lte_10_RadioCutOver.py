import os
from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class lte_10_RadioCutOver(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)
        if len(self.enbdata) == 0: return
        self.motype = 'Lrat'
        self.relative_path = []
        self.secmo = []
        self.df_cell = self.df_enb_cell.copy()
        self.df_ant = self.usid.df_ant.loc[(self.usid.df_ant.postsite == self.node)]
        self.fru_change_cell_list = list(set(self.df_ant.loc[((~self.df_ant.antflag) & self.df_ant.fruchange), 'postcell'].tolist()))
        self.df_ant = self.df_ant.loc[(self.df_ant.postcell.isin(self.fru_change_cell_list) & self.df_ant.antflag)]
        self.df_ril = self.usid.df_ril.loc[(self.usid.df_ril.postsite == self.node)]
        self.df_ril = self.df_ril.loc[(self.df_ril.postcell.isin(self.fru_change_cell_list) & self.df_ril.antflag)]
        for postcell in self.fru_change_cell_list:
            self.script_list = []
            self.relative_path = [F'lte_1_RadioCutOver_{postcell}.mos']
            self.script_list.extend(self.delete_cell_mos(postcell))
            self.cr_file_path_radio_cutover()
            self.writemos(cvname=F'1_RadioCutOver_RRUDel_{postcell}')

            self.script_list = []
            self.relative_path = [F'lte_2_RadioAddition_{postcell}.mos']
            self.script_list.extend(self.create_radios(postcell))
            self.cr_file_path_radio_cutover()
            self.writemos(cvname=F'1_RadioAddition_RRUAdd_{postcell}')

    def write_script_file(self): pass
    def cr_file_path(self): pass

    def cr_file_path_radio_cutover(self):
        self.script_file = os.path.join(self.usid.base_dir, '02_REMOTE', 'RADIO_CUTOVER', self.node, *self.relative_path)
        out_dir = os.path.dirname(self.script_file)
        if not os.path.exists(out_dir): os.makedirs(out_dir)

    def writemos(self, cvname):
        if len(self.script_list) == 0: pass
        elif type(self.script_list[0]) is str:
            with open(self.script_file, 'w') as f:
                f.write('\n'.join(self.mos_files_start()))
                f.write('\n'.join(self.get_parameters()))
                f.write('\n'.join(self.script_list))
                f.write('\n'.join(self.get_parameters()))
                f.write('\n'.join(self.mos_files_end()))
        else:
            with open(self.script_file, 'w') as f:
                f.write(F'Check the Script Class ---> {self.__class__.__name__}')

    def create_radios(self, postcell=''):
        lines = [F'####:----------------> Radio, Antenna System & SectorEquipmentFunction for cell {postcell} <----------------:####']
        df_temp = self.df_ant.loc[self.df_ant.postcell == postcell]
        if df_temp.shape[0] == 0: return []
        rfb_ref = []
        # FieldReplaceableUnit
        for fru in df_temp.fru.unique():
            ldn = F'Equipment=1,FieldReplaceableUnit={fru}'
            for _, row in df_temp.loc[df_temp.fru == fru].head(1).iterrows():
                if self.validate_db_mo(mo=row.frufdn):
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('FieldReplaceableUnit', row.presite, row.frufdn)
                    temp_dict.update({'fieldReplaceableUnitId': fru, 'auxPlugInUnitId': ''})
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'FieldReplaceableUnit', ldn))
                    site = self.usid.sites.get(F'site_{row.presite}')
                    lines.extend(self.append_mos_equipment_elems(site=site, parent_fdn=row.frufdn, mo_tag='RiPort', parent_ldn=ldn))
                    lines.extend(self.append_mos_equipment_elems(site=site, parent_fdn=row.frufdn, mo_tag='RfPort', parent_ldn=ldn))
                    lines.extend(self.append_mos_equipment_elems(site=site, parent_fdn=row.frufdn, mo_tag='Transceiver', parent_ldn=ldn))
                    lines.extend(self.append_mos_equipment_elems(site=site, parent_fdn=row.frufdn, mo_tag='AlarmPort', parent_ldn=ldn))
                else:
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('FieldReplaceableUnit', None, '')
                    temp_dict.update({'isSharedWithExternalMe': row.isshared})
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'FieldReplaceableUnit', ldn))
                    riport_R, vswrsup, vswrsen = True, 'true', '100'
                    if 'AIR' in row.frutypecix:
                        riport_R, vswrsup, vswrsen = False, 'false', '-1'
                    if 'AIR32' in row.frutypecix:
                        riport_R = True
                    riport = ['DATA_1', 'DATA_2']
                    if ('AIR6449' in row.frutypecix) or ('AIR6448' in row.frutypecix) or ('AIR3246' in row.frutypecix):
                        riport = riport + ['DATA_3', 'DATA_4']
                    for port in riport:
                        temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RiPort', None, '')
                        lines.extend(self.create_mos_script_from_dict(temp_dict, 'RiPort', F'{ldn},RiPort={port}'))
                    if riport_R:
                        temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RfPort', None, '')
                        temp_dict.update({'vswrSupervisionActive': 'false', 'vswrSupervisionSensitivity': '-1'})
                        lines.extend(self.create_mos_script_from_dict(temp_dict, 'RiPort', F'{ldn},RfPort=R'))
                    for _, row_rfp in df_temp.loc[df_temp.fru == fru, ['rfp', 'trecid']].drop_duplicates().iterrows():
                        if self.validate_db_moid(moid=row_rfp.rfp):
                            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RfPort', None, '')
                            temp_dict.update({'vswrSupervisionActive': vswrsup, 'vswrSupervisionSensitivity': vswrsen})
                            lines.extend(self.create_mos_script_from_dict(temp_dict, 'RfPort', F'{ldn},RfPort={row_rfp.rfp}'))
                        elif self.validate_db_moid(moid=row_rfp.trecid):
                            lines.extend(self.create_mos_script_from_dict({}, 'Transceiver', F'{ldn},Transceiver={row_rfp.trecid}'))
                            rfb_ref += [F'{ldn},Transceiver={row_rfp.trecid}']
        # AntennaUnitGroup
        for aug in df_temp.loc[~df_temp.aup.isnull()].aug.unique():
            ldn = F'Equipment=1,AntennaUnitGroup={aug}'
            lines.extend(self.create_mos_script_from_dict({'antennaUnitGroupId': aug}, 'AntennaUnitGroup', F'{ldn}'))
            for _, row_au in df_temp.loc[df_temp.aug == aug, ['presite', 'au', 'aufdn', 'mt']].drop_duplicates().iterrows():
                ldn_au = F'{ldn},AntennaUnit={row_au.au}'
                if self.validate_db_mo(mo=row_au.aufdn):
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('AntennaUnit', row_au.presite, row_au.aufdn)
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'AntennaUnit', ldn_au))
                else:
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('AntennaUnit', None, '')
                    temp_dict.update({'mechanicalAntennaTilt': row_au.mt})
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'AntennaUnit', ldn_au))
                for _, row_asu in df_temp.loc[((df_temp.aug == aug) & (df_temp.au == row_au.au)), ['presite', 'asu', 'asufdn']].drop_duplicates().iterrows():
                    ldn_asu = F'{ldn_au},AntennaSubunit={row_au.au}'
                    if self.validate_db_mo(mo=row_asu.asufdn):
                        temp_dict = self.update_db_with_mo_for_siteid_and_fdn('AntennaSubunit', row_asu.presite, row_asu.asufdn)
                        lines.extend(self.create_mos_script_from_dict(temp_dict, 'AntennaSubunit', ldn_asu))
                    else:
                        temp_dict = self.update_db_with_mo_for_siteid_and_fdn('AntennaSubunit', None, '')
                        lines.extend(self.create_mos_script_from_dict(temp_dict, 'AntennaSubunit', ldn_asu))
                    for _, row_aup in df_temp.loc[(df_temp.aug == aug) & (df_temp.au == row_au.au) & (df_temp.asu == row_asu.asu)].iterrows():
                        ldn_aup = F'{ldn_asu},AuPort={row_aup.aup}'
                        temp_dict = self.update_db_with_mo_for_siteid_and_fdn('AuPort', None, '')
                        lines.extend(self.create_mos_script_from_dict(temp_dict, 'AuPort', ldn_aup))
                        ldn_rfb = F'Equipment=1,AntennaUnitGroup={row_aup.raug},RfBranch={row_aup.rfb}'
                        if self.validate_db_mo(mo=row_aup.rfbfdn):
                            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RfBranch', row_aup.presite, row_aup.rfbfdn)
                            lines.extend(self.create_mos_script_from_dict(temp_dict, 'RfBranch', ldn_rfb))
                        else:
                            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RfBranch', None, '')
                            temp_dict.update({
                                'rfBranchId': row_aup.rfb,
                                'auPortRef': ldn_aup,
                                'dlAttenuation': [row_aup.dl_ul_delay_att[1]]*15,
                                'dlTrafficDelay': [row_aup.dl_ul_delay_att[0]]*15,
                                'rfPortRef': F'Equipment=1,FieldReplaceableUnit={row_aup.fru},RfPort={row_aup.rfp}',
                                'ulAttenuation': [row_aup.dl_ul_delay_att[3]]*15,
                                'ulTrafficDelay': [row_aup.dl_ul_delay_att[2]]*15,
                            })
                            lines.extend(self.create_mos_script_from_dict(temp_dict, 'RfBranch', ldn_rfb))
                        rfb_ref += [ldn_rfb]
        # RiLink
        for _, row in self.df_ril.loc[self.df_ril.postcell == postcell].iterrows():
            lines.extend([
                F'pr Equipment=1,RiLink={row.rilid}$',
                F'if $nr_of_mos = 0',
                F'crn Equipment=1,RiLink={row.rilid}',
                F'riPortRef1 Equipment=1,FieldReplaceableUnit={row.fru1},RiPort={row.rip1}',
                F'riPortRef2 Equipment=1,FieldReplaceableUnit={row.fru2},RiPort={row.rip2}',
                F'fronthaulDeviceLineRate 0',
                F'transportType 0',
                F'end',
                F'fi',
                F''
            ])
        
        # ---SectorEquipmentFunction---
        rfBranchRef = ''
        for i in rfb_ref: rfBranchRef += F' {i}'
        rfBranchRef = rfBranchRef.strip()
        for sef in df_temp.sef.unique():
            lines.extend([
                F'pr NodeSupport=1,SectorEquipmentFunction={sef}$',
                F'if $nr_of_mos = 0',
                F'cr NodeSupport=1,SectorEquipmentFunction={sef}',
                F'fi',
                F'set NodeSupport=1,SectorEquipmentFunction={sef}$ rfBranchRef {rfBranchRef}',
                F'set NodeSupport=1,SectorEquipmentFunction={sef}$ administrativeState 1',
                F''
            ])

        # ---SectorCarrier---
        if 'MC' in str(df_temp.iloc[0].carrier).upper():
            lines.append(F'set ENodeBFunction=1,SectorCarrier={str(df_temp.iloc[0].sc)}$ sectorFunctionRef '
                         F'NodeSupport=1,SectorEquipmentFunction={str(df_temp.iloc[0].sef)}')
        lines.extend(self.secmo)
        self.secmo = []

        return lines + ['', '']

    def delete_cell_mos(self, postcell=''):
        lines = []
        self.secmo = []
        for index, row in self.usid.df_enb_cell.loc[self.usid.df_enb_cell.postcell == postcell].iterrows():
            site = self.usid.sites.get(F'site_{row.presite}')
            cell_ldn = self.mos_check_text_element(row.fdn)
            lines.extend([F'####:----------------> DELETE MOs for CELL {row.precell} <----------------:####',
                          F'get {cell_ldn}$ operationalState 1',
                          'if $nr_of_mos > 0', 'print ERROR: Soft Lock the cells manually. ABORT !!!', 'l-', 'return', 'fi'])
            rfb_list = []
            # SectorCarrier
            for sc in site.site_extract_data(row.fdn).get('sectorCarrierRef'):
                if sc is None: continue
                sec_ldn = site.get_mo_name_ending_str(sc)
                self.secmo.extend([F'set {self.mos_check_text_element(sec_ldn)}$ noOfRxAntennas {row.noofrx}',
                                   F'set {self.mos_check_text_element(sec_ldn)}$ noOfTxAntennas {row.nooftx}',
                                   F'set {self.mos_check_text_element(sec_ldn)}$ configuredMaxTxPower {row.confpowcix}', ''])

                lines.extend([
                    F'set {self.mos_check_text_element(sec_ldn)}$ rfBranchRxRef null',
                    F'set {self.mos_check_text_element(sec_ldn)}$ rfBranchTxRef null',
                    F'set {self.mos_check_text_element(sec_ldn)}$ sectorFunctionRef null' if 'MC' in str(row.carrier).upper() else '',
                    F'',
                ])
                # if 'MC' in str(row.carrier).upper():
                
                rfb_list.extend(site.site_extract_data(sec_ldn).get('rfBranchTxRef'))
                rfb_list.extend(site.site_extract_data(sec_ldn).get('rfBranchRxRef'))
                # SectorEquipmentFunction
                sef_ldn = site.site_extract_data(sec_ldn).get('sectorFunctionRef')
                if (sef_ldn is not None) or (sef_ldn != ''):
                    sef_ldn = site.get_mo_name_ending_str(sef_ldn)
                    rfb_list.extend(site.site_extract_data(sef_ldn).get('rfBranchRef'))
                    lines.extend([
                        F'set {self.mos_check_text_element(sef_ldn)}$ administrativeState 0',
                        F'set {self.mos_check_text_element(sef_ldn)}$ rfBranchRef null',
                        F'del {self.mos_check_text_element(sef_ldn)}$' if 'MC' in str(row.carrier).upper() else '',
                        F''
                    ])

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
                    if (aup_ref is not None) and (len(aup_ref) > 0): aup_refs.extend(aup_ref)
                    if (rfp_ref is not None) and (len(rfp_ref) > 0): rfp_refs.append(rfp_ref)
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
                        '',
                        F'$asu_delete_1 = 0',
                        F'lpr {asu_mo},AuPort=',
                        F'if $nr_of_mos = 0',
                        F'$asu_delete_1 = 1',
                        'fi',
                        F'get {asu_mo} retSubunitRef RetSubUnit',
                        'if $nr_of_mos = 0 && $asu_delete_1 = 1',
                        F'del {asu_mo}$',
                        'fi',
                        ''
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

        return lines + ['', '']

    def get_parameters(self):
        return [
            'sts',
            'hget ^ENodeBFunction=1$ ^eNBId$|^eNodeBPlmnId$|^sctpRef$|^upIpAddressRef$|^intraRanIpAddressRef$|eranVlanPortRef$',
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
    
    def create_mos_script_from_dict(self, adddict, moname, moc='', change_me=True):
        cmo = []
        if len(moc) > 0:
            cmo.extend([F'pr {moc}$', F'if $nr_of_mos = 0', F'crn {moc}'])
            for key in adddict:
                if (str(key).lower() == F'{moname}Id'.lower()) or (adddict[key] is None) or (adddict[key] == ''): continue
                elif (type(adddict[key]) == int) or (type(adddict[key]) == str):
                    if (self.mos_check_text_element(str(adddict[key]), change_me) is None) or \
                            (self.mos_check_text_element(str(adddict[key]), change_me) == ''): continue
                    val = self.mos_check_text_element(str(adddict[key]), change_me)
                    cmo.append(F'{str(key)} {val}')
                elif type(adddict[key]) == dict:
                    val = self.parameter_dict_values(para_dict=adddict[key], change_me=True, delime=',')
                    if len(val) > 1: cmo.append(F'{str(key)} {val[:-1]}')
                elif type(adddict[key]) == list:
                    val = self.parameter_list_values(adddict[key])
                    if len(val) > 1: cmo.append(F'{str(key)} {val[:-1]}')
            cmo.extend(['end', 'fi', ''])
        return cmo

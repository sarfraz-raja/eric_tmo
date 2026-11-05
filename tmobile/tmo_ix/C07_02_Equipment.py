from .tmo_usid_data import tmo_usid_data
from .tmo_xml_base import tmo_xml_base


class C07_02_Equipment(tmo_xml_base):
    def __init__(self, usid: tmo_usid_data, node: str):
        super().__init__(usid=usid, node=node)

        # self.relative_path = [F'REMOTE_{self.node}', F'{self.__class__.__name__}_{self.node}.mos']
        self.df_xmu = self.usid.df_xmu.loc[(self.usid.df_xmu.postsite == self.node)]
        self.df_ant = self.usid.df_ant.loc[(self.usid.df_ant.postsite == self.node)]
        self.df_ant = self.df_ant.loc[~(self.df_ant.carrier.str.contains('MC'))]
        self.df_ant = self.df_ant.loc[(self.df_ant.addcell & ~self.df_ant.antflag) | (self.df_ant.addcell & self.df_ant.presite.isnull())]
        self.df_ant_near_unit = self.usid.df_ant_near_unit.loc[(self.usid.df_ant_near_unit.postsite == self.node)]
        self.df_ril = self.usid.df_ril.loc[(self.usid.df_ril.postsite == self.node)]
        self.df_ril = self.df_ril.loc[(self.df_ril.addcell & ~self.df_ril.antflag) | (self.df_ril.addcell & self.df_ril.presite.isnull())]

        # Equipments & cellReselectionPriority for UtranFreqRelation
        self.script_list.extend(self.default_parameter_basedon_tmo_input() + self.create_mos_doc())

    def create_mos_doc(self):
        lines = []
        for _, row in self.df_xmu.iterrows():
            if row.flag1 is True or row.flag2 is True:
                lines.extend([F'####:----------------> XMU <----------------:####'])
                lines.extend(self.create_xmu(row=row))

        if self.df_ant.shape[0] == 0: return lines
        for postcell in self.df_ant.postcell.unique():
            df_temp = self.df_ant.loc[self.df_ant.postcell == postcell]
            rfb_ref = []
            lines.extend([F'####:----------------> Radio, Antenna System & SectorEquipmentFunction for cell {postcell} <----------------:####'])

            # FieldReplaceableUnit
            for fru in df_temp.fru.unique():
                ldn = F'Equipment=1,FieldReplaceableUnit={fru}'
                for _, row in df_temp.loc[df_temp.fru == fru].head(1).iterrows():
                    if row.frufdn is not None:
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
                        if 'AIR' in row.frutypecix: riport_R, vswrsup, vswrsen = False, 'false', '-1'
                        if 'AIR32' in row.frutypecix: riport_R = True
                        riport = ['DATA_1', 'DATA_2']
                        if (('AIR6449' in row.frutypecix) or ('AIR6448' in row.frutypecix) or
                                ('AIR3246' in row.frutypecix) or ('AIR5322' in row.frutypecix)):
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

                    # AntennaNearUnit
                    for _, row_ret in self.df_ant_near_unit.loc[self.df_ant_near_unit.fru == fru].iterrows():
                        if row_ret.anufdn is not None:
                            ldn = F'Equipment=1,AntennaUnitGroup={row_ret.aug}'
                            lines.extend(self.create_mos_script_from_dict({'antennaUnitGroupId': row_ret.aug}, 'AntennaUnitGroup', ldn))
                            ldn = F'{ldn},AntennaNearUnit={row_ret.anu}'
                            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('AntennaNearUnit', row_ret.presite, row_ret.anufdn)
                            temp_dict.update({'antennaNearUnitId': row_ret.anu, 'rfPortRef': F'Equipment=1,FieldReplaceableUnit={row_ret.fru},RfPort={row_ret.rfp}'})
                            lines.extend(self.create_mos_script_from_dict(temp_dict, 'AntennaNearUnit', ldn))
                            site = self.usid.sites.get(F'site_{row_ret.presite}')
                            lines.extend(self.append_mos_equipment_elems(site=site, parent_fdn=row_ret.anufdn, mo_tag='TmaSubUnit', parent_ldn=ldn))
                            lines.extend(self.append_mos_equipment_elems(site=site, parent_fdn=row_ret.anufdn, mo_tag='RetSubUnit', parent_ldn=ldn))

            # AntennaUnitGroup
            for aug in df_temp.loc[(~df_temp.aup.isnull()) & (df_temp.trecid.isnull())].aug.unique():
                ldn = F'Equipment=1,AntennaUnitGroup={aug}'
                lines.extend(self.create_mos_script_from_dict({'antennaUnitGroupId': aug}, 'AntennaUnitGroup', F'{ldn}'))
                for _, row_au in df_temp.loc[df_temp.aug == aug, ['presite', 'au', 'aufdn', 'mt']].drop_duplicates().iterrows():
                    ldn_au = F'{ldn},AntennaUnit={row_au.au}'
                    if row_au.aufdn is not None:
                        temp_dict = self.update_db_with_mo_for_siteid_and_fdn('AntennaUnit', row_au.presite, row_au.aufdn)
                        lines.extend(self.create_mos_script_from_dict(temp_dict, 'AntennaUnit', ldn_au))
                    else:
                        temp_dict = self.update_db_with_mo_for_siteid_and_fdn('AntennaUnit', None, '')
                        temp_dict.update({'mechanicalAntennaTilt': row_au.mt})
                        lines.extend(self.create_mos_script_from_dict(temp_dict, 'AntennaUnit', ldn_au))
                    for _, row_asu in df_temp.loc[((df_temp.aug == aug) & (df_temp.au == row_au.au)), ['presite', 'asu', 'asufdn']].drop_duplicates().iterrows():
                        ldn_asu = F'{ldn_au},AntennaSubunit={row_au.au}'
                        if row_asu.asufdn is not None:
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
                            if row_aup.rfbfdn is not None:
                                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RfBranch', row_aup.presite, row_aup.rfbfdn)
                                lines.extend(self.create_mos_script_from_dict(temp_dict, 'RfBranch', ldn_rfb))
                            else:
                                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RfBranch', None, '')
                                temp_dict.update({
                                    'rfBranchId': row_aup.rfb,
                                    'auPortRef': ldn_aup,
                                    'dlAttenuation': [row_aup.dl_ul_delay_att[2]]*15,
                                    'dlTrafficDelay': [row_aup.dl_ul_delay_att[0]]*15,
                                    'rfPortRef': F'Equipment=1,FieldReplaceableUnit={row_aup.fru},RfPort={row_aup.rfp}',
                                    'ulAttenuation': [row_aup.dl_ul_delay_att[3]]*15,
                                    'ulTrafficDelay': [row_aup.dl_ul_delay_att[1]]*15,
                                })
                                lines.extend(self.create_mos_script_from_dict(temp_dict, 'RfBranch', ldn_rfb))
                            rfb_ref += [ldn_rfb]
            for _, row_aup in df_temp.loc[(df_temp.aup.isnull()) & (df_temp.trecid.isnull())].iterrows():
                ldn_rfb = F'Equipment=1,AntennaUnitGroup={row_aup.raug},RfBranch={row_aup.rfb}'
                if row_aup.rfbfdn is not None:
                    temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RfBranch', row_aup.presite, row_aup.rfbfdn)
                    lines.extend(self.create_mos_script_from_dict(temp_dict, 'RfBranch', ldn_rfb))
                    rfb_ref += [ldn_rfb]
                
            # SectorEquipmentFunction
            for sef in df_temp.sef.unique():
                lines.extend([F'crn NodeSupport=1,SectorEquipmentFunction={sef}', 'administrativeState 1'])
                for i in rfb_ref: lines.extend([F'rfBranchRef {i}'])
                lines.extend(['end', ''])

        # RiLink
        if len(lines) > 0:
            ril_lines = []
            for postcell in self.df_ant.postcell.unique():
                for _, row in self.df_ril.loc[self.df_ril.postcell == postcell].iterrows():
                    ril_lines.append(F'Create_RiLink {row.rilid} {row.fru1} {row.rip1} {row.fru2} {row.rip2} {row.postcell}')
            if len(ril_lines) > 0:
                lines.extend([
                    '###########------------------------------------------------------------###########',
                    '#### Create_RiLink riLinkId riPortRef1 riPortRef2, CellId',
                    'func Create_RiLink',
                    'crn Equipment=1,RiLink=$1',
                    'riPortRef1 Equipment=1,FieldReplaceableUnit=$2,RiPort=$3',
                    'riPortRef2 Equipment=1,FieldReplaceableUnit=$4,RiPort=$5',
                    'fronthaulDeviceLineRate 0',
                    'transportType 0',
                    'end',
                    'endfunc',
                    '###########------------------------------------------------------------###########',
                    '',
                    '####:----------------> RiLink <----------------:####',
                    '',
                ])
                lines = lines + ril_lines + ['', '']
        return lines + ['', '']

    def create_xmu(self, row):
        lines = []
        if row.flag1 == True:
            ldn = F'Equipment=1,FieldReplaceableUnit={row.xmu1}'
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('FieldReplaceableUnit', None, '')
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'FieldReplaceableUnit', ldn))
            for i in range(1, 17):
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RiPort', None, '')
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'RiPort', F'{ldn},RiPort={i}'))
            for _, row_ril in self.df_ril.loc[self.df_ril.fru == row.xmu1].iterrows():
                lines.extend([
                    F'crn Equipment=1,RiLink={row_ril.rilid}',
                    F'riPortRef1 Equipment=1,FieldReplaceableUnit={row_ril.fru1},RiPort={row_ril.rip1}',
                    F'riPortRef2 Equipment=1,FieldReplaceableUnit={row_ril.fru2},RiPort={row_ril.rip2}',
                    F'fronthaulDeviceLineRate 0',
                    F'transportType 0',
                    F'end',
                    F'',
                ])
            lines += ['', '']

        if row.flag2 == True:
            ldn = F'Equipment=1,FieldReplaceableUnit={row.xmu2}'
            temp_dict = self.update_db_with_mo_for_siteid_and_fdn('FieldReplaceableUnit', None, '')
            lines.extend(self.create_mos_script_from_dict(temp_dict, 'FieldReplaceableUnit', ldn))
            for i in [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16]:
                temp_dict = self.update_db_with_mo_for_siteid_and_fdn('RiPort', None, '')
                lines.extend(self.create_mos_script_from_dict(temp_dict, 'RiPort', F'{ldn},RiPort={i}'))
            for _, row_ril in self.df_ril.loc[self.df_ril.fru == row.xmu2].iterrows():
                lines.extend([
                    F'crn Equipment=1,RiLink={row_ril.rilid}',
                    F'riPortRef1 Equipment=1,FieldReplaceableUnit={row_ril.fru1},RiPort={row_ril.rip1}',
                    F'riPortRef2 Equipment=1,FieldReplaceableUnit={row_ril.fru2},RiPort={row_ril.rip2}',
                    F'fronthaulDeviceLineRate 0',
                    F'transportType 0',
                    F'end',
                    F'',
                    F''
                ])
        return lines + ['', '']

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
            'hget ^ENodeBFunction=1,EUtranCell[FT]DD=.*Relation= cellReselectionPriority',
            'st sec',
            '',
            '',
        ]

    def default_parameter_basedon_tmo_input(self):
        return []
        

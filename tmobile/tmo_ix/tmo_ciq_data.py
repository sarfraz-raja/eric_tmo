import numpy as np
import pandas as pd
import re


class tmo_ciq_data:
    def __init__(self, infile=None, sites=None):
        self.sites = sites
        self.edx = {}
        self.site_sheet_col_dict = {
            'EDP': 'node', 'ENodeB': 'node', 'EutranCellFDD': 'eutrancellfddid', 'NbIotCell': 'nbiotcellname', 'PCI': 'eutrancellfddid',
            'Losses and Delays': 'eutrancellfddid', 'EUtranFreqRelation': 'eutrancellfddid',  'UtranFreqRelation': 'eutrancellfddid',
            'FreqGroupRel': 'sourcecell', 'GSMCellRel': 'ltesiteid', 'CA': 'eutrancellfddid', 'UMTSSIB19': 'utrancell', 'GSMLTE': 'cellgsm',
            'EDP5G': 'node', 'gNodeB': 'node', 'gUtranCell': 'gutrancell'
        }

        site_sheet_dataframe = {
            'eNodeB Ericsson': 'EDP', 'eNB Info': 'ENodeB', 'eUtran Parameters': 'EutranCellFDD', 'NBIoT Parameters': 'NbIotCell',
            'LTE-LTE- FreqRelation': 'EUtranFreqRelation', 'LTE-UMTS-UtranFreqRelation': 'UtranFreqRelation', 'LTE-GSM-FreqGroupRel': 'FreqGroupRel',
            'LTE-GSM-CELLS': 'GSMCellRel', 'PCI': 'PCI', 'Losses and Delays': 'Losses and Delays', 'LTE Carrier Aggregation': 'CA',
            'UMTS-LTE-Relations': 'UMTSSIB19',  'GSM-LTE-Relation': 'GSMLTE',
            'gNodeB Ericsson': 'EDP5G', 'gNB Info': 'gNodeB', 'gUtranCell info': 'gUtranCell'
        }

        for sheet in site_sheet_dataframe:
            df = pd.read_excel(infile, sheet_name=sheet, dtype='str')
            df.columns = df.columns.str.replace(r'[^a-zA-Z0-9]', '', regex=True)
            df = df.replace('[^a-zA-Z0-9.,-_/+]', '', regex=True)
            df.rename(columns=lambda x: str(x).lower(), inplace=True)
            df.replace({np.nan: None, '': None}, inplace=True)
            if (self.sites is not None) and (sheet != 'GSM-LTE-Relation'): df = df.loc[df[self.site_sheet_col_dict.get(sheet)].str.contains(sites)]
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            if site_sheet_dataframe.get(sheet) in ['EDP5G', 'EDP', 'gNodeB', 'ENodeB']:
                df.rename(columns={'gnodebname': 'node', 'enodebname': 'node', 'gnbname': 'node', 'siteid': 'node'}, inplace=True)
            df = df.loc[~df[self.site_sheet_col_dict.get(site_sheet_dataframe.get(sheet))].isnull()]
            self.edx[site_sheet_dataframe.get(sheet)] = df.copy()

        # ---eNodeBs and gNodeBs List for Scripting ---
        self.enodeb_list = [_ for _ in self.edx['ENodeB'].node.unique() if _ is not None]
        self.gnodeb_list = [_ for _ in self.edx['gNodeB'].node.unique() if _ is not None]

        # ---ENodeB CIX Data Frame Modification---
        if self.edx['ENodeB'].shape[0] > 0:
            # Make Unique instance
            self.edx['EDP'] = self.edx['EDP'].loc[self.edx['EDP']['node'].isin(self.enodeb_list)]
            self.edx['EDP'] = self.edx['EDP'].groupby(['node'], sort=False, as_index=False).head(1)

            self.edx['ENodeB'] = self.edx['ENodeB'].loc[self.edx['ENodeB']['node'].isin(self.enodeb_list)]
            self.edx['ENodeB'] = self.edx['ENodeB'].groupby(['node'], sort=False, as_index=False).head(1)
            self.edx['ENodeB'][['BBType', 'RBSType']] = self.edx['ENodeB'][['bbtype', 'rbstype']].replace('[^0-9]', '', regex=True)
            self.edx['ENodeB']['IDLE'] = self.edx['ENodeB'].idle.apply(lambda x: x if x in ['IDL_A1', 'IDL_A2', 'IDL_A3', 'TN_IDL_A', 'TN_IDL_C',
                                                                                            'TN_IDL_B', 'TN_IDL_D', 'TN_IDL_E'] else None)

            # ---NbIotCell CIX Data Frame Modification---
            self.edx['NbIotCell'] = self.edx['NbIotCell'].groupby(['nbiotcellname'], sort=False, as_index=False).head(1)
            self.edx['NbIotCell'] = self.edx['NbIotCell'].merge(self.edx['ENodeB'][['enbid', 'node']], on='enbid', how='left', suffixes=('', '_'))
            self.edx['NbIotCell'] = self.edx['NbIotCell'].loc[self.edx['NbIotCell']['node'].isin(self.enodeb_list)]

            # ---EutranCellFDD CIX Data Frame Modification---
            if self.edx.get('EutranCellFDD').shape[0] > 0:
                self.edx['EutranCellFDD'] = self.edx['EutranCellFDD'].groupby(['eutrancellfddid'], sort=False, as_index=False).head(1)
                self.edx['EutranCellFDD'] = self.edx['EutranCellFDD'].merge(
                    self.edx['ENodeB'][['enbid', 'node', 'tac']], on='enbid', how='left', suffixes=('', '_enb'))
                self.edx['EutranCellFDD'] = self.edx['EutranCellFDD'].loc[self.edx['EutranCellFDD']['node'].isin(self.enodeb_list)]
                self.edx['PCI'] = self.edx['PCI'].groupby(['eutrancellfddid'], sort=False, as_index=False).head(1)
                self.edx['EutranCellFDD'] = self.edx['EutranCellFDD'].merge(self.edx['PCI'][[
                    'eutrancellfddid', 'sectorcarriertype', 'sectorid', 'cellid', 'pci', 'rachrootsequence', 'radiotype', 'carrier',
                    'sefcix', 'rrushared', 'bbuxmu', 'port1', 'port2', 'port3', 'port4']], on='eutrancellfddid', how='left', suffixes=('', '_pci'))
                self.edx['EutranCellFDD'].rename(columns={
                    'pci': 'physicallayercellid', 'dlonly': 'isdlonly', 'configuredoutputpower': 'confpow', 'nooftxantennas': 'nooftx',
                    'noofrxantennas': 'noofrx', 'eutraoperatingband': 'freqband', 'radiotype': 'rrutype'}, inplace=True)
                self.edx.get('EutranCellFDD')[['cell', 'celltype', 'latitude', 'longitude',
                                               'userlabel', 'eutrancellcoverage', 'dl_ul_delay_att', 'rrutype']] = \
                    self.edx.get('EutranCellFDD').apply(self.get_enodeb_cell_Data, axis=1, result_type='expand')

                self.edx.get('CA')
                self.edx.get('CA').rename(columns={'eutrancellfddid': 'postcell', 'eutrancellrelation': 'crelid', 'scellcandidate': 'scell_ciq'}, inplace=True)
                self.edx.get('CA').replace({'0': '0 (NOT_ALLOWED)', '1': '1 (ALLOWED)', '2': '2 (AUTO)', '3': '3 (ONLY_ALLOWED_FOR_DL)'}, inplace=True)
                self.edx.get('CA')['remove_ciq'] = 'false'

            # if self.edx.get('CA').shape[0] > 0:
            #     self.edx.get('CA')
            #     self.edx.get('CA').rename(columns={'eutrancellfddid': 'postcell', 'eutrancellrelation': 'crelid', 'scellcandidate': 'scell_ciq'}, inplace=True)
            #     self.edx.get('CA').replace({'1': '1 (ALLOWED)', '2': '2 (AUTO)'}, inplace=True)
            #     self.edx.get('CA')['remove_ciq'] = 'false'
            # else:
            #     self.edx.get('CA').rename(columns={'eutrancellfddid': 'postcell', 'eutrancellrelation': 'crelid', 'scellcandidate': 'scell_ciq'}, inplace=True)


            if self.edx.get('GSMCellRel').shape[0] > 0:
                self.edx['GSMCellRel'] = self.edx['GSMCellRel'].loc[self.edx['GSMCellRel']['ltesiteid'].isin(self.enodeb_list)]
                self.edx['GSMCellRel'] = self.edx['GSMCellRel'].groupby(['sourcecell', 'ci'], sort=False, as_index=False).head(1)
                self.edx.get('GSMCellRel')['group'] = self.edx.get('GSMCellRel').bcch.apply(self.get_gfreqgroop_for_bcch)
            
            if self.edx.get('FreqGroupRel').shape[0] > 0:
                self.edx.get('FreqGroupRel').rename(columns={'sourcecell': 'eutrancellfddid'}, inplace=True)
                self.edx['FreqGroupRel'] = self.edx['FreqGroupRel'].merge(
                    self.edx['EutranCellFDD'][['eutrancellfddid', 'node']], on='eutrancellfddid', how='left', suffixes=('', '_rel'))
                self.edx['FreqGroupRel'] = self.edx['FreqGroupRel'].loc[self.edx['FreqGroupRel']['node'].isin(self.enodeb_list)]
                if self.edx.get('FreqGroupRel').shape[0] > 0:
                    self.edx.get('FreqGroupRel')[['gfreqgid', 'group', 'flag', 'postsite', 'postcell', 'relid', 'creprio']] = \
                        self.edx.get('FreqGroupRel').apply(self.update_values_for_gsm_group_relations, axis=1, result_type='expand')
                
        # gNodeB CIX Data Frame Modification
        if self.edx['gNodeB'].shape[0] > 0:
            # Make Unique instance
            self.edx['EDP5G'] = self.edx['EDP5G'].loc[self.edx['EDP5G']['node'].isin(self.gnodeb_list)]
            self.edx['EDP5G'] = self.edx['EDP5G'].groupby(['node'], sort=False, as_index=False).head(1)

            self.edx['gNodeB'].rename(columns={'temptac': 'nrtac'}, inplace=True)
            self.edx['gNodeB'] = self.edx['gNodeB'].loc[self.edx['gNodeB']['node'].isin(self.gnodeb_list)]
            self.edx['gNodeB'] = self.edx['gNodeB'].groupby(['node'], sort=False, as_index=False).head(1)
            self.edx['gNodeB'][['BBType', 'RBSType']] = self.edx['gNodeB'][['bbtype', 'rbstype']].replace('[^0-9]', '', regex=True)
            self.edx['gNodeB']['IDLE'] = self.edx['gNodeB'].idle.apply(lambda x: x if x in ['IDL_A1', 'IDL_A2', 'IDL_A3', 'TN_IDL_A', 'TN_IDL_C',
                                                                                            'TN_IDL_D', 'TN_IDL_E'] else None)
            #
            # self.edx['gNodeB'][['BBType', 'RBSType']] = self.edx['gNodeB'][['bbtype', 'rbstype']].replace('[^0-9]', '', regex=True)

            if self.edx.get('gUtranCell').shape[0] > 0:
                self.edx['gUtranCell'] = self.edx['gUtranCell'].groupby(['gutrancell'], sort=False, as_index=False).head(1)
                self.edx['gUtranCell'] = self.edx['gUtranCell'].merge(self.edx['gNodeB'][['gnbid', 'node', 'nrtac']], on='gnbid', how='left', suffixes=('', '_gnb'))
                self.edx['gUtranCell'] = self.edx['gUtranCell'].loc[self.edx['gUtranCell']['node'].isin(self.gnodeb_list)]
                self.edx['gUtranCell'].rename(columns={'pci': 'nrpci', 'channelbandwidth': 'bschannelbwdl'}, inplace=True)
                self.edx.get('gUtranCell')[['cell', 'bschannelbwdl', 'bschannelbwul', 'celltype', 'dl_ul_delay_att', 'radiotype']] = \
                    self.edx.get('gUtranCell').apply(self.get_gnodeb_cell_Data, axis=1, result_type='expand')
        else:
            self.edx['gUtranCell']['node'] = None
        for key in self.edx.keys(): self.edx[key].reset_index(inplace=True, drop=True)

    def get_enodeb_cell_Data(self, row):

        def get_loss_val(cellrow, para):
            try: val = int(float(cellrow.get(para)))
            except: val = None
            if val is None: val = 0
            return str(val)

        cell_type = 'TDD' if row.earfcndl == row.earfcnul else 'FDD'
        try:
            lat = int(float(re.sub(r'[.]', '', str(row.latitude))[:15]))
            while 90000000 < lat or lat < -90000000:
                lat = int(float(str(lat)[:-1]))
        except: lat = '0'
        lat = str(lat)

        try:
            longg = int(float(re.sub(r'[.]', '', row.longitude)[:15]))
            while 180000000 < longg or longg < -180000000:
                longg = int(float(str(longg)[:-1]))
        except: longg = 0
        longg = str(longg)

        try: ulabel = str(row.userlabel)
        except: ulabel = row.eutrancellfddid
        if len(ulabel) == 0: ulabel = row.eutrancellfddid

        try:
            pbearing = int(float(row.poscellbearing))
            pbearing = pbearing if -1 <= pbearing <= 3599 else -1
        except: pbearing = -1
        try:
            angle = int(float(row.poscellopeningangle))
            angle = angle if -1 <= angle <= 3599 else -1
        except: angle = -1
        try:
            pradius = int(float(row.poscellradius))
            pradius = pradius if 0 <= pradius <= 200000 else 0
        except: pradius = '0'
        eutcellcov = {'posCellBearing': F'{pbearing}', 'posCellOpeningAngle': F'{angle}', 'posCellRadius': F'{pradius}'}

        if self.edx['Losses and Delays'].loc[self.edx['Losses and Delays'].eutrancellfddid == row.eutrancellfddid].shape[0] > 0:
            los = self.edx['Losses and Delays'].loc[self.edx['Losses and Delays'].eutrancellfddid == row.eutrancellfddid].iloc[0]
            dl_ul_delay_att = [
                [F'{get_loss_val(los, "rfbranchru1dltrafficdelay")}', F'{get_loss_val(los, "rfbranchru1ultrafficdelay")}', F'{get_loss_val(los, "rfbranchru1dlattenuation")}', F'{get_loss_val(los, "rfbranchru1ulattenuation")}'],
                [F'{get_loss_val(los, "rfbranchru2dltrafficdelay")}', F'{get_loss_val(los, "rfbranchru2ultrafficdelay")}', F'{get_loss_val(los, "rfbranchru2dlattenuation")}', F'{get_loss_val(los, "rfbranchru2ulattenuation") }'],
                [F'{get_loss_val(los, "rfbranchru3dltrafficdelay")}', F'{get_loss_val(los, "rfbranchru3ultrafficdelay")}', F'{get_loss_val(los, "rfbranchru3dlattenuation")}', F'{get_loss_val(los, "rfbranchru3ulattenuation")}'],
                [F'{get_loss_val(los, "rfbranchru4dltrafficdelay")}', F'{get_loss_val(los, "rfbranchru4ultrafficdelay")}', F'{get_loss_val(los, "rfbranchru4dlattenuation")}', F'{get_loss_val(los, "rfbranchru4ulattenuation")}']
            ]
        else:
            dl_ul_delay_att = [['0', '0', '0', '0'], ['0', '0', '0', '0'], ['0', '0', '0', '0'], ['0', '0', '0', '0']]
        rrutype = str(row.rrutype).upper().split(',')
        rrutype.sort()
        # 'cell', 'celltype', 'latitude', 'longitude', 'userlabel', 'eutrancellcoverage', 'dl_ul_delay_att', 'rrutype'
        temp_list = [row.eutrancellfddid, cell_type, lat, longg, ulabel, eutcellcov, dl_ul_delay_att, rrutype]
        return temp_list

    def get_gnodeb_cell_Data(self, row):
        # 'cell', 'bschannelbwdl', 'bschannelbwul', 'celltype', 'dl_ul_delay_att', 'radiotype'
        def get_loss_val(cellrow, para):
            if cellrow.get(para, None) is None:
                val = 0
            else:
                try: val = int(float(cellrow.get(para)))
                except: val = 0
            return str(val)

        if self.edx['Losses and Delays'].loc[self.edx['Losses and Delays'].eutrancellfddid == row.gutrancell].shape[0] > 0:
            los = self.edx['Losses and Delays'].loc[self.edx['Losses and Delays'].eutrancellfddid == row.gutrancell].iloc[0]
            dl_ul_delay_att = [
                [F'{get_loss_val(los, "rfbranchru1dltrafficdelay")}', F'{get_loss_val(los, "rfbranchru1ultrafficdelay")}', F'{get_loss_val(los, "rfbranchru1dlattenuation")}', F'{get_loss_val(los, "rfbranchru1ulattenuation")}'],
                [F'{get_loss_val(los, "rfbranchru2dltrafficdelay")}', F'{get_loss_val(los, "rfbranchru2ultrafficdelay")}', F'{get_loss_val(los, "rfbranchru2dlattenuation")}', F'{get_loss_val(los, "rfbranchru2ulattenuation") }'],
                [F'{get_loss_val(los, "rfbranchru3dltrafficdelay")}', F'{get_loss_val(los, "rfbranchru3ultrafficdelay")}', F'{get_loss_val(los, "rfbranchru3dlattenuation")}', F'{get_loss_val(los, "rfbranchru3ulattenuation")}'],
                [F'{get_loss_val(los, "rfbranchru4dltrafficdelay")}', F'{get_loss_val(los, "rfbranchru4ultrafficdelay")}', F'{get_loss_val(los, "rfbranchru4dlattenuation")}', F'{get_loss_val(los, "rfbranchru4ulattenuation")}']
            ]
        else:
            dl_ul_delay_att = [['0', '0', '0', '0'], ['0', '0', '0', '0'], ['0', '0', '0', '0'], ['0', '0', '0', '0']]
        ch_bw = str(int(int(row.bschannelbwdl)/1000))
        radiotype = str(row.radiotype).upper().split(',')
        radiotype.sort()
        # 'cell', 'bschannelbwul', 'celltype', 'dl_ul_delay_att', 'radiotype'
        return [row.gutrancell, ch_bw, ch_bw, 'ASS' if row.arfcndl == row.arfcnul else '5GNR', dl_ul_delay_att, radiotype]

    def get_gfreqgroop_for_bcch(self, bcch):
        gfreqgroup_gfreq = {
            '1': [128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152],
            '2': [512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536],
            '3': [537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561],
            '4': [562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586],
            '5': [587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611],
            '6': [612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636],
            '7': [637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661],
            '8': [662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686],
            '9': [687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711],
            '10': [712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736],
            '11': [737, 738, 739, 740, 741, 742, 743, 744, 745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761],
            '12': [762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786],
            '13': [787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810],
        }
        ggroup, bcch = None, int(bcch)
        for key in gfreqgroup_gfreq.keys():
            if bcch in gfreqgroup_gfreq.get(key): ggroup = str(key)
        return ggroup

    def update_values_for_gsm_group_relations(self, row):
        group = ''.join(i for i in row.geranfreqgroup if i.isdigit())
        if group == '': group = '0'
        # 'gfreqgid', 'group', 'flag', 'postsite', 'postcell', 'relid', 'creprio'
        return [group, group, True, row.node, row.eutrancellfddid, group, '1']

    def get_ru_type_for_cell(self, cell, outcol):
        return self.edx.get('EutranCellFDD').loc[self.edx.get('EutranCellFDD').EutranCellFDDId.str.contains(cell)].iloc[0][outcol]

    def get_sheet_data(self, sheet_name, field_name):
        return self.edx.get(sheet_name).to_dict('records')[0].get(field_name)

    def get_sheet_data_upper(self, sheet_name, field_name):
        if self.edx.get(sheet_name).to_dict('records')[0].get(field_name) is None: return None
        else: return self.edx.get(sheet_name).to_dict('records')[0].get(field_name).upper()

    def get_site_field_data_upper(self, node, sheet_name, field):
        if self.site_sheet_data(sheet_name, node).iloc[0][field] is None: return None
        else: return self.site_sheet_data(sheet_name, node).iloc[0][field].upper()

    def get_edp_ip_site_data_upper(self, node, field):
        if (self.site_sheet_data('EDP', node).iloc[0][field] != '') and (not pd.isnull(self.site_sheet_data('EDP', node).iloc[0][field])):
            return ':'.join([i.lstrip('0') for i in self.site_sheet_data('EDP', node).iloc[0][field].upper().split(':')])
        else: return ''

    def get_eutrancell_field(self, cell, field):
        return self.edx.get('EutranCellFDD')[self.edx.get('EutranCellFDD').cell == cell][field].iloc[0]

    def site_sheet_data(self, sheet_name, node):
        return self.edx.get(sheet_name).loc[self.edx.get(sheet_name)[self.site_sheet_col_dict.get(sheet_name)] == node]

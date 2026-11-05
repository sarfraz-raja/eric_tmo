import re, os, sys, copy
import numpy as np
import pandas as pd

# usm_dict = {
#     'USM1': {
#         'RS_IP': 'USM1_IP___2001:4888:a47:3165:406:292:0:100',
#         'IPV6_NM': '126',
#         'IPVER': '6',
#     },
# }


class BaseCIQ:
    def __init__(self, cqfile, usm):
        self.usm = usm
        cqfile = cqfile
        df = pd.read_excel(cqfile, sheet_name='CQ', header=1, dtype='str')
        data_column = [i.replace(' ', "_").replace('.', "_n") for i in df.columns]
        df.columns = data_column
        df.replace(r'[^a-zA-Z0-9.,-_/+:]', '', regex=True, inplace=True)
        df.replace(r'_x001C_', '', regex=True, inplace=True)
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df.replace({np.nan: None, '': None, 'null': None, 'None': None}, inplace=True)
        df = df.loc[~(df.ENODEB_VENDOR.isnull() | df.ALIAS_NAME.isnull() | df.ENODEB_ID.isnull())]
        df = df.loc[(df.ENODEB_VENDOR.str.lower().str.startswith('samsung'))]
        df.reset_index(drop=True, inplace=True)
        self.df_ciq = copy.deepcopy(df)

    # def __init__(self, cqfile, usm):
    #     self.usm = copy.deepcopy(usm_dict.get(usm))
    #     cqfile = cqfile
    #     df = pd.read_excel(cqfile, sheet_name='CQ', dtype='str')
    #     tmp_str = ''
    #     data_column = []
    #     for index, item in enumerate(df.columns):
    #         if item.startswith('Unnamed:'):
    #             data_column.append(tmp_str + "--" + df.iat[0, index].replace(' ', "_"))
    #         else:
    #             tmp_str = item.replace(' ', "_")
    #             data_column.append(tmp_str + "--" + df.iat[0, index].replace(' ', "_"))
    #     df.columns = data_column
    #
    #     df.drop([0], inplace=True)
    #     df = df.loc[(df['Enode-B_Info--ENODEB_VENDOR'].str.lower().str.startswith('samsung'))]
    #     df.replace({np.nan: None, '': None, 'null': None}, inplace=True)
    #     df.reset_index(drop=True, inplace=True)
    #     self.df_ciq = copy.deepcopy(df)

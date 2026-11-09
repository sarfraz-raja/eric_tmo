PlmnId = {'mcc': '310', 'mnc': '260', 'mncLength': '3'}
node_username = 'prbs'
node_password = '@WtIwQ-Bo2m0'
timeOffset_dict = {
    'US/Eastern': '-04:00',
    'US/Central': '-05:00',
    'US/Mountain': '-06:00',
    'US/Pacific': '-07:00',
    'US/Alaskan': '-08:00',
    'US/Hawaiian': '-9:00'
}
bb_riport = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
BB_dict = {
    '6672': {
        'RiPort': bb_riport[:18],
        'TnPort': 'TN_IDL_C',
        'IDLE': 'TN_IDL_D',
        'FeatureState': [],
    },
    '6655': {
        'RiPort': bb_riport[:18],
        'TnPort': 'TN_IDL_C',
        'IDLE': 'TN_IDL_D',
        'FeatureState': [],
    },
    '6651': {
        'RiPort': bb_riport[:12],
        'TnPort': 'TN_IDL_B',
        'IDLE': 'TN_IDL_C',
        'FeatureState': [],
    },
    '6648': {
        'RiPort': bb_riport[:12],
        'TnPort': 'TN_IDL_B',
        'IDLE': 'TN_IDL_C',
        'FeatureState': [],
    },
    # ToDo Need to validate Ports
    '6502': {
        'RiPort': bb_riport[:6],
        'TnPort': 'TN_B',
        'IDLE': '',
        'FeatureState': [],
    },
    '6630': {
        'RiPort': bb_riport[:15],
        'TnPort': 'TN_A',
        'IDLE': '',
        'FeatureState': [],
    },
    '5216': {
        'RiPort': bb_riport[:6],
        'TnPort': 'TN_B',
        'IDLE': '',
        'FeatureState': [],
    },
}

software_dict = {
    'TMO_26_Q3_EC2': {
        '6672': {'package': 'RadioNode CXP2010174/2 R59C52 26.Q3', 'nodeIdentifier': '3300-192-417'},
        '6655': {'package': 'RadioNode CXP2010174/2 R59C52 26.Q3', 'nodeIdentifier': '3300-192-417'},
        '6651': {'package': 'RadioNode CXP2010174/2 R59C52 26.Q3', 'nodeIdentifier': '3300-192-417'},
        '6648': {'package': 'RadioNode CXP2010174/2 R59C52 26.Q3', 'nodeIdentifier': '3300-192-417'},
        '6630': {'package': 'RadioNode CXP9024418/16 R20C43 RCG123.8', 'nodeIdentifier': '4172-064-366'},
        '5216': {'package': 'RadioNode CXP9024418/16 R20C43 RCG123.8', 'nodeIdentifier': '4172-064-366'},
        '6502': {'package': 'RadioNode CXP9024418/16 R20C43 RCG123.8', 'nodeIdentifier': '4172-064-366'},
        '6630_L41_N41': {'package': 'RadioNode CXP9024418/22 R87C44 RCG123.8', 'nodeIdentifier': '1196-600-262'},
    },
    'TMO_26_Q2_EC2': {
        '6672': {'package': 'RadioNode CXP2010174/2 R53C46 26.Q2', 'nodeIdentifier': '6591-287-219'},
        '6655': {'package': 'RadioNode CXP2010174/2 R53C46 26.Q2', 'nodeIdentifier': '6591-287-219'},
        '6651': {'package': 'RadioNode CXP2010174/2 R53C46 26.Q2', 'nodeIdentifier': '6591-287-219'},
        '6648': {'package': 'RadioNode CXP2010174/2 R53C46 26.Q2', 'nodeIdentifier': '6591-287-219'},
        '6630': {'package': 'RadioNode CXP9024418/16 R20C30 RCG123.8', 'nodeIdentifier': '4172-064-366'},
        '5216': {'package': 'RadioNode CXP9024418/16 R20C30 RCG123.8', 'nodeIdentifier': '4172-064-366'},
        '6502': {'package': 'RadioNode CXP9024418/16 R20C30 RCG123.8', 'nodeIdentifier': '4172-064-366'},
        '6630_L41_N41': {'package': 'RadioNode CXP9024418/22 R87C30 RCG123.8', 'nodeIdentifier': '1196-600-262'},
    },
    'TMO_26_Q1_EC2': {
        '6672': {'package': 'RadioNode CXP2010174/2 R48C47 26.Q1', 'nodeIdentifier': '3277-817-896'},
        '6655': {'package': 'RadioNode CXP2010174/2 R48C47 26.Q1', 'nodeIdentifier': '3277-817-896'},
        '6651': {'package': 'RadioNode CXP2010174/2 R48C47 26.Q1', 'nodeIdentifier': '3277-817-896'},
        '6648': {'package': 'RadioNode CXP2010174/2 R48C47 26.Q1', 'nodeIdentifier': '3277-817-896'},
        '6630': {'package': 'RadioNode CXP9024418/16 R17C21 26.Q1', 'nodeIdentifier': '4486-761-225'},
        '5216': {'package': 'RadioNode CXP9024418/16 R17C21 26.Q1', 'nodeIdentifier': '4486-761-225'},
        '6502': {'package': 'RadioNode CXP9024418/16 R17C21 26.Q1', 'nodeIdentifier': '4486-761-225'},
        '6630_L41_N41': {'package': 'RadioNode CXP9024418/22 R84C25 26.Q1', 'nodeIdentifier': '1196-600-262'},
    },
    'TMO_25_Q4_RC5': {
        '6672': {'package': 'RadioNode CXP2010174/2 R42C72 25.Q4', 'nodeIdentifier': '25.Q4-R42C18'},
        '6655': {'package': 'RadioNode CXP2010174/2 R42C72 25.Q4', 'nodeIdentifier': '25.Q4-R42C18'},
        '6651': {'package': 'RadioNode CXP2010174/2 R42C72 25.Q4', 'nodeIdentifier': '25.Q4-R42C18'},
        '6648': {'package': 'RadioNode CXP2010174/2 R42C72 25.Q4', 'nodeIdentifier': '25.Q4-R42C18'},
        '6630': {'package': 'RadioNode CXP9024418/16 R15C74 25.Q4', 'nodeIdentifier': '4060-712-598'},
        '5216': {'package': 'RadioNode CXP9024418/16 R15C74 25.Q4', 'nodeIdentifier': '4060-712-598'},
        '6502': {'package': 'RadioNode CXP9024418/16 R15C74 25.Q4', 'nodeIdentifier': '4060-712-598'},
        '6630_L41_N41': {'package': 'RadioNode CXP9024418/22 R82C75 25.Q4', 'nodeIdentifier': '4060-712-598'},
    },
    'TMO_25_Q3_EC2': {
        '6672': {'package': 'RadioNode CXP2010174/2 R38C38 25.Q3', 'nodeIdentifier': '3807-674-657'},
        '6655': {'package': 'RadioNode CXP2010174/2 R38C38 25.Q3', 'nodeIdentifier': '3807-674-657'},
        '6651': {'package': 'RadioNode CXP2010174/2 R38C38 25.Q3', 'nodeIdentifier': '3807-674-657'},
        '6648': {'package': 'RadioNode CXP2010174/2 R38C38 25.Q3', 'nodeIdentifier': '3807-674-657'},
        '6630': {'package': 'RadioNode CXP9024418/16 R13C42 25.Q3', 'nodeIdentifier': '3415-809-908'},
        '5216': {'package': 'RadioNode CXP9024418/16 R13C42 25.Q3', 'nodeIdentifier': '3415-809-908'},
        '6502': {'package': 'RadioNode CXP9024418/16 R13C42 25.Q3', 'nodeIdentifier': '3415-809-908'},
        '6630_L41_N41': {'package': 'RadioNode CXP9024418/22 R80C28 25.Q3', 'nodeIdentifier': '4060-712-598'},
    },
}

nodeIdentifier_dict = {
    'TMO_26_Q3_EC2': {
        'PON09CNM': {
            'RadioNode CXP2010174/2 R59C52 26.Q3': '7766-922-709',
            'RadioNode CXP9024418/16 R20C43 RCG123.8': '4172-064-366',
            'RadioNode CXP9024418/22 R87C44 RCG123.8': '1196-600-262',
        },
        'TIN18CNM': {
            'RadioNode CXP2010174/2 R59C52 26.Q3': '7766-922-709',
            'RadioNode CXP9024418/16 R20C43 RCG123.8': '4172-064-366',
            'RadioNode CXP9024418/22 R87C44 RCG123.8': '1196-600-262',
        },
    },
    'TMO_26_Q2_EC2': {},
    'TMO_26_Q1_EC2': {
        'TIN18CNM': {
            'RadioNode CXP2010174/2 R48C47 26.Q1': '26.Q1-R47A85',
            'RadioNode CXP9024418/16 R17C21 26.Q1': '4486-761-225',
            'RadioNode CXP9024418/22 R84C25 26.Q1': '1196-600-262',
        },
    },
    'TMO_25_Q4_RC5': {},
    'TMO_25_Q3_EC2': {
        'PON03CNM': {
            'RadioNode CXP2010174/2 R38C38 25.Q3': '5108-272-185',
            'RadioNode CXP9024418/16 R13C42 25.Q3': '3415-809-908',
            'RadioNode CXP9024418/22 R80C28 25.Q3': '4060-712-598',
        },
        'PON04CNM': {
            'RadioNode CXP2010174/2 R38C38 25.Q3': '4800-618-123',
            'RadioNode CXP9024418/16 R13C42 25.Q3': '4060-712-598',
            'RadioNode CXP9024418/22 R80C28 25.Q3': '4060-712-598',
        },
        'PON05CNM': {
            'RadioNode CXP2010174/2 R38C38 25.Q3': '4800-618-123',
            'RadioNode CXP9024418/16 R13C42 25.Q3': '3415-809-908',
            'RadioNode CXP9024418/22 R80C28 25.Q3': '4060-712-598',
        },
        'PON08CNM': {
            'RadioNode CXP2010174/2 R38C38 25.Q3': '4800-618-123',
            'RadioNode CXP9024418/16 R13C42 25.Q3': '3415-809-908',
            'RadioNode CXP9024418/22 R80C28 25.Q3': '4060-712-598',
        },
        'PON09CNM': {
            'RadioNode CXP2010174/2 R38C38 25.Q3': '3807-674-657',
            'RadioNode CXP9024418/16 R13C42 25.Q3': '4060-712-598',
            'RadioNode CXP9024418/22 R80C28 25.Q3': '4060-712-598',
        },
        'PON10CNM': {
            'RadioNode CXP2010174/2 R38C38 25.Q3': '4800-618-123',
            'RadioNode CXP9024418/16 R13C42 25.Q3': '3415-809-908',
            'RadioNode CXP9024418/22 R80C28 25.Q3': '4060-712-598',
        },
        'TIN05CNM': {
            'RadioNode CXP2010174/2 R38C38 25.Q3': '4800-618-123',
            'RadioNode CXP9024418/16 R13C42 25.Q3': '4060-712-598',
            'RadioNode CXP9024418/22 R80C28 25.Q3': '4060-712-598',
        },
        'TIN13CNM': {
            'RadioNode CXP2010174/2 R38C38 25.Q3': '4800-618-123',
            'RadioNode CXP9024418/16 R13C42 25.Q3': '3415-809-908',
            'RadioNode CXP9024418/22 R80C28 25.Q3': '4060-712-598',
        },
        'TIN18CNM': {
            'RadioNode CXP2010174/2 R38C38 25.Q3': '4800-618-123',
            'RadioNode CXP9024418/16 R13C42 25.Q3': '4060-712-598',
            'RadioNode CXP9024418/22 R80C28 25.Q3': '1314-743-866',
        },
    },
}


def get_sw_nodeidentifier(sw: str, bb_type: str, enm: str) -> (str, str):
    if sw is None or bb_type is None or enm is None: return None, None
    package = software_dict.get(sw, {}).get(bb_type, {}).get('package')
    nodeIdentifier = software_dict.get(sw, {}).get(bb_type, {}).get('nodeIdentifier')
    if package is not None and sw in nodeIdentifier_dict and enm in nodeIdentifier_dict[sw]:
        nodeIdentifier = nodeIdentifier_dict.get(sw).get(enm).get(package)
    return package, nodeIdentifier



def get_cell_type(*, cell: str) -> str:
    cell_mapping = {
        'A': 'N2500',
        'K': 'N600',
        'J': 'N1900',
        'I': 'N2100',
        # 'Q': 'N3700',
        # 'S': 'N3700',
        # 'M': 'N261',
        # 'N': 'N260',
        # '0': 'N258',

        'T': 'L2500',
        'L': 'L2100',
        'B': 'L1900',
        'D': 'L700',
        'E': 'L600',
        'C': 'L850',
        'F': 'AWS3',
        'G': 'B46_LAA',

        'X': 'NB-IOT 700',
        'Y': 'NB-IOT PCS',
        'Z': 'NB-IOT AWS',
    }
    key = (cell[0] or '').upper()
    return cell_mapping[key] if key in cell_mapping else None


def global_amos_logic() -> list:
    # $GenCheck = Gen3or4
    # $GenCheck = Gen2
    # $A_Cell_Present = 1
    # $IJK_Cell_Present = 1
    # $J_Cell_Present = 1
    # $K_Cell_Present = 1
    # $QSH_Cell_Present = 1
    # $RP6672_Present = 1

    lines = []
    lines += [F"""
####:----------------> Global Implementation <----------------:####
func GenCheck
	get SystemFunctions=1,SwInventory=1,SwVersion= swVersionId > $OLDUP
	$OLDUP = $OLDUP -s -.*
	if $OLDUP ~ ^CXP2010174/2
		$GenCheck = Gen3or4
	else if $OLDUP ~ ^CXP9024418
		$GenCheck = Gen2
	fi
endfunc

func CellCheck
    $A_Cell_Present = 0
    pr GNBDUFunction=1,NRCellDU=[A]
	if $nr_of_mos != 0
		$A_Cell_Present = 1
	fi
    $IJK_Cell_Present = 0		
	pr GNBDUFunction=1,NRCellDU=[IJK]
	if $nr_of_mos != 0
		$IJK_Cell_Present = 1
	fi
    $J_Cell_Present = 0
	pr GNBDUFunction=1,NRCellDU=[J]
	if $nr_of_mos != 0
		$J_Cell_Present = 1
	fi
    $K_Cell_Present = 0
	pr GNBDUFunction=1,NRCellDU=[K]
	if $nr_of_mos != 0
		$K_Cell_Present = 1
	fi
    $QSH_Cell_Present = 0
	pr GNBDUFunction=1,NRCellDU=[QSH]
	if $nr_of_mos != 0
		$QSH_Cell_Present = 1
	fi
endfunc

GenCheck
CellCheck

get FieldReplaceableUnit productData RAN.*Processor.*6672
if $nr_of_mos != 0
$RP6672_Present = 1
else
$RP6672_Present = 0
fi

func UL_SU_MIMO_Config
    scw RP904:2
    scw RP3290:0
endfunc

func PreempMob
  for $mo in 2ndC_barred_cells
    $rdn = rdn($mo)
    get $rdn nRCellDUId > $nRCell_Id
    if $nRCell_Id ~ ^A
      set UeMC=1,UeMCCellProfile=$nRCell_Id connModeUeAllowedToBarredCellType 0
    else 
      set UeMC=1,UeMCCellProfile=$nRCell_Id connModeUeAllowedToBarredCellType 2
    fi
  done
endfunc

"""]
    return lines

import csv
import gzip
import json
import os
import re
from xml.dom.minidom import parseString
from xml.etree import ElementTree
from django.db.models import Q
from tmobile.models import MoDetail

COLUMNS = ['node', 'script', 'file', 'message_id', 'mo_name', 'moc', 'parameter_name', 'operator', 'parameter_value', 'in_script', 'source',
           'source_method', 'value_file', 'db_value', 'dcgk_value', 'backupflag', 'mom_flags', 'takes_effect', 'mom_file', 'remark']
FUNCTION_MOTYPE = {'ENodeBFunction': 'Lrat', 'GNBDUFunction': 'GNBDU', 'GNBCUCPFunction': 'GNBCUCP', 'GNBCUUPFunction': 'GNBCUUP'}
MOS_WRITE = ['crn', 'cr', 'set', 'mset', 'rset', 'lset', 'lmset', 'del', 'rdel', 'ldel', 'lrdel', 'bl', 'deb', 'lbl', 'ldeb', 'acc', 'lacc', 'ld']
MOS_READ = ['get', 'hget', 'kget', 'lget', 'lhget', 'st', 'lst', 'pr', 'lpr']
XML_OPERATION = {'create': 'crn', 'delete': 'del', 'remove': 'del', 'merge': 'set', 'replace': 'set'}
SCRIPT_EXT = ('.xml', '.mos')


def files_snapshot(base_dir: str) -> dict or None:
    try:
        snap = {}
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [_ for _ in dirs if _ != 'CSV']
            for f in files:
                p = os.path.join(root, f)
                st = os.stat(p)
                snap[p] = (st.st_mtime_ns, st.st_size)
        return snap
    except Exception:
        return None


def write_debug_csv(script, files_before: dict or None) -> None:
    try:
        if files_before is None or not getattr(script.usid, 'debug_csv', False): return
        files_after = files_snapshot(script.usid.base_dir) or {}
        changed = sorted(p for p, s in files_after.items() if files_before.get(p) != s and p.lower().endswith(SCRIPT_EXT))
        for path in changed:
            try:
                same_file = script.script_file and os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(script.script_file))
                tracked = script.csv_rows if script.csv_rows and not script.csv_failed and same_file else None
                rows = with_message_ids(script, path, tracked) if tracked else rows_from_file(script, path)
                if rows: write_rows(script, path, rows)
            except Exception as e:
                script.usid.log.info(F'Debug CSV not created for {path}: {e}')
    except Exception as e:
        script.usid.log.info(F'Debug CSV not created for {script.__class__.__name__} {script.node}: {e}')


def write_rows(script, path: str, rows: list) -> None:
    base_dir = script.usid.base_dir
    stem, ext = os.path.splitext(os.path.basename(path))
    if os.path.relpath(path, base_dir).split(os.sep)[0] == '01_AP':
        csv_dir, name = os.path.join(base_dir, '02_REMOTE', script.node, 'CSV'), F'AP__{stem}'
    else:
        csv_dir, name = os.path.join(os.path.dirname(path), 'CSV'), stem
    used = script.usid.__dict__.setdefault('csv_names', set())
    if os.path.normcase(os.path.join(csv_dir, name)) in used: name = F'{name}_{ext.lstrip(".")}'
    used.add(os.path.normcase(os.path.join(csv_dir, name)))
    csv_file = os.path.join(csv_dir, name + '.csv')
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    rel_file = os.path.relpath(path, base_dir).replace(os.sep, '/')
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction='ignore')
        writer.writeheader()
        for row in rows: writer.writerow({**row, 'file': rel_file})


def get_cache(script) -> dict: return script.usid.__dict__.setdefault('csv_cache', {})


def get_mom(script) -> dict:
    cache = script.usid.__dict__.setdefault('mom_cache', {})
    if script.node not in cache:
        mom, data = {}, getattr(script.usid, 'mom_files', {}).get(script.node)
        try:
            for text in gzip.decompress(data).decode('utf-8', 'ignore').split('<?xml')[1:] if data else []:
                text = re.sub(r'<!DOCTYPE[^>]*>', '', text[text.find('?>') + 2:], count=1)
                text = text[:text.rfind('>') + 1]
                for mim in ElementTree.fromstring(text).iter('mim'):
                    for cls in mim.iter('class'):
                        attrs = {a.get('name'): ([f for f in ['readOnly', 'restricted', 'mandatory'] if a.find(f) is not None],
                                                 (a.findtext('takesEffect') or '').strip()) for a in cls.findall('attribute')}
                        mom[(mim.get('name'), cls.get('name'))] = (cls.find('systemCreated') is not None, attrs)
        except Exception as e:
            script.usid.log.info(F'{script.node}: node MOM not read for debug CSV ({e})')
        cache[script.node] = mom
    return cache[script.node]


def mom_class(script, moc: str, motype: str or None):
    mom = get_mom(script)
    return mom.get((motype, moc)) or mom.get((script.mo_attr.get(moc), moc)) or next((v for k, v in mom.items() if k[1] == moc), None)


def db_index(script) -> dict:
    cache = get_cache(script)
    if ('db', script.bbversion) not in cache:
        idx = {}
        qs = MoDetail.objects.filter((Q(mo__software=script.usid.client.software) & Q(flag=True)) &
                                     (Q(bbversion='') | Q(bbversion__contains=script.bbversion)))
        for motype, moc, moid, para, value, backupflag in qs.values_list('mo__motype', 'mo__moc', 'mo__moid', 'parameter', 'value', 'backupflag'):
            try: value = json.loads(value) if value else ''
            except Exception: pass
            idx.setdefault((moc, moid), {}).setdefault(motype, {})[para[:1].lower() + para[1:]] = (value, backupflag)
        cache[('db', script.bbversion)] = idx
    return cache[('db', script.bbversion)]


def db_lookup(script, mo_name: str, motype: str = None) -> (str or None, dict):
    parts = [_.split('=', 1) for _ in mo_name.split(',') if '=' in _]
    if not parts: return motype, {}
    moc = parts[-1][0]
    fi = next((i for i, (m, _) in enumerate(parts) if m in FUNCTION_MOTYPE), None)
    motype = motype or (FUNCTION_MOTYPE[parts[fi][0]] if fi is not None else None)
    ids = [v for _, v in parts[fi + 1:]] if fi is not None and fi < len(parts) - 1 else [parts[-1][1]]
    idx = db_index(script)
    for moid in [','.join(ids[k:]) for k in range(len(ids))] + ['']:
        by_type = idx.get((moc, moid))
        if not by_type: continue
        if motype in by_type: return motype, by_type[motype]
        if motype is None and len(by_type) == 1: return next(iter(by_type.items()))
    return motype, {}


def dcgk_index(script, site: str) -> dict:
    cache = get_cache(script)
    if ('dcgk', site) not in cache:
        dcg = getattr(script.usid.sites.get(F'site_{site}'), 'dcg', None) or {}
        cache[('dcgk', site)] = {script.csv_ldn(mo): {k[:1].lower() + k[1:]: v for k, v in (attrs or {}).items()} for mo, attrs in dcg.items()}
    return cache[('dcgk', site)]


def flat_value(script, key: str, value) -> list:
    if type(value) is dict: return [_ for k, v in value.items() for _ in flat_value(script, F'{key}.{k}', v)]
    if type(value) is list and any(type(_) is dict for _ in value):
        return [_ for i, v in enumerate(value) for _ in flat_value(script, F'{key}[{i}]', v)]
    if type(value) is list: return [(key, ';'.join(script.check_text_element(str(_)) for _ in value))]
    return [(key, '' if value is None else script.check_text_element(str(value)))]


def flat_map(script, params: dict) -> dict:
    out = {}
    for key, value in params.items():
        flat = flat_value(script, key, value[0] if type(value) is tuple else value)
        for para, val in flat:
            out[para] = val
            if '[0]' in para:
                prefix = para.split('[0]')[0]
                if not any(_.startswith(prefix + '[1]') for _, __ in flat): out[para.replace('[0]', '', 1)] = val
    return out


def mos_value(script, value) -> str:
    if type(value) is dict: return script.parameter_dict_values(para_dict=value)[:-1]
    if type(value) is list: return script.parameter_list_values(value)[:-1]
    return script.mos_check_text_element(str(value))


def value_file(script, source: str, dcgk_site: str) -> str:
    files = []
    if 'DCGK' in source: files.append(getattr(script.usid, 'source_files', {}).get(dcgk_site, {}).get('dcgk', 'DCGK'))
    if 'MOC' in source: files.append(F'{script.usid.client.software.swname}.xlsx > MOC sheet (DB tmobile_modetail)')
    if not files: files.append(code_source(script, script.__class__.__module__.replace('.', '/') + '.py'))
    return ' | '.join(files)


def code_source(script, name: str) -> str:
    return name if getattr(script.usid, 'debug_csv_local', False) else 'Source code'


def mom_file(script, cls, key: str) -> str:
    if not (cls and key in cls[1]): return ''
    return getattr(script.usid, 'source_files', {}).get(script.node, {}).get('mom', '')


def mom_operator(script, cls, key: str, moc: str, flags: list) -> str:
    if not (cls and cls[0]): return 'crn'
    if moc and key.lower() == script.get_moc_id(moc).lower(): return 'ld'
    return 'rset' if 'restricted' in flags else 'set'


def mom_remarks(script, cls, key: str, flags: list) -> list:
    remark = []
    if get_mom(script) and cls is None: remark.append('MOC not in node MOM')
    elif cls and key not in cls[1]: remark.append('attribute not in node MOM (new SW attribute?)')
    if 'readOnly' in flags: remark.append('readOnly attribute in script')
    return remark


def bf_text(value) -> str: return {True: 'TRUE', False: 'FALSE', 1: 'TRUE', 0: 'FALSE'}.get(value, '')


def track_mo(script, *, mo_name: str, moid: str or None, final: dict, default: dict = None, dcgk: dict = None, source: dict = None,
             default_source: str = 'MOC', dcgk_site: str = '') -> None:
    if not script.csv_enabled or script.csv_failed: return
    try:
        moc = mo_name.split(',')[-1].split('=')[0]
        db_params = db_index(script).get((moc, moid), {}).get(script.motype, {}) if moid is not None else {}
        db_values = {k: db_params[k][0] if k in db_params else (default or {}).get(k, '') for k in final}
        dcgk, source = dcgk or {}, source or {}
        cls = mom_class(script, moc, script.motype)
        for key, value in final.items():
            src = source.get(key, default_source)
            if src == script.__class__.__name__: src = code_source(script, src)
            flags, takes_effect = cls[1].get(key, ([], '')) if cls else ([], '')
            db_flat = dict(flat_value(script, key, db_values[key])) if key in db_values else {}
            dcgk_flat = dict(flat_value(script, key, dcgk[key])) if key in dcgk else {}
            rows = [(para, val, False) for para, val in flat_value(script, key, value)]
            rows += [(para, '', True) for para in db_flat if src == 'DCGK' and para not in [_[0] for _ in rows]]
            for para, val, dropped in rows:
                remark = []
                if dropped: remark.append('member in MOC but missing in DCGK struct, not in script')
                elif val == '': remark.append('empty value, not in script')
                remark += mom_remarks(script, cls, key, flags)
                if not dropped and src == 'DCGK' and db_flat.get(para, '') not in ['', val]: remark.append('DCGK value differs from MOC')
                if not dropped and key not in db_params and db_flat.get(para, '') != '':
                    remark.append('db_value from MOC default (no DB row for this MO id)')
                row_src = 'MOC' if dropped else src
                script.csv_rows.append({
                    'node': script.node, 'script': script.__class__.__name__, 'mo_name': mo_name, 'moc': moc, 'parameter_name': para,
                    'operator': mom_operator(script, cls, key, moc, flags), 'parameter_value': val, 'in_script': 'no' if val == '' else 'yes',
                    'source': row_src, 'source_method': 'tracked', 'value_file': value_file(script, row_src, dcgk_site or script.node),
                    'db_value': db_flat.get(para, ''), 'dcgk_value': dcgk_flat.get(para, ''), 'backupflag': bf_text(db_params.get(key, ('', None))[1]),
                    'mom_flags': ';'.join(flags), 'takes_effect': takes_effect, 'mom_file': mom_file(script, cls, key), 'remark': '; '.join(remark)})
    except Exception as e:
        script.csv_failed = True
        script.usid.log.info(F'Debug CSV tracking stopped for {script.__class__.__name__} {script.node} ({e}), CSV derived from file')


def rows_from_file(script, path: str) -> list:
    with open(path, encoding='utf-8', errors='ignore') as f: text = f.read()
    if path.lower().endswith('.xml'): return derived_rows(script, xml_entries(script, text), 'xml')
    return derived_rows(script, mos_entries(script, text), 'mos')


def with_message_ids(script, path: str, rows: list) -> list:
    if not path.lower().endswith('.xml'): return rows
    with open(path, encoding='utf-8', errors='ignore') as f: text = f.read()
    msg_ids = {}
    for _, mo, _, _, msg_id in xml_entries(script, text):
        if msg_id not in msg_ids.setdefault(mo, []): msg_ids[mo].append(msg_id)
    return [{**row, 'message_id': '|'.join(msg_ids.get(row['mo_name'], []))} for row in rows]


def xml_entries(script, text: str) -> list:
    entries = []

    def walk(elem, parent, msg_id):
        kids = [_ for _ in elem.childNodes if _.nodeType == 1]
        tag = elem.tagName.split(':')[-1]
        id_tag = tag[:1].lower() + tag[1:] + 'Id'
        id_elem = [_ for _ in kids if _.tagName.split(':')[-1] == id_tag]
        mo_id = id_elem[0].firstChild.data.strip() if id_elem and id_elem[0].firstChild else ''
        mo_name = F'{parent},{tag}={mo_id}'.lstrip(',')
        attrs = dict(elem.attributes.items()) if elem.attributes else {}
        op = next((XML_OPERATION.get(v, v) for k, v in attrs.items() if k.split(':')[-1] == 'operation'), '')
        entries.append((op, mo_name, id_tag, mo_id, msg_id))
        values, counts = {}, {}
        for c in kids:
            c_tag = c.tagName.split(':')[-1]
            c_kids = [_ for _ in c.childNodes if _.nodeType == 1]
            if c_tag == id_tag: continue
            if c_kids and any(_.tagName.split(':')[-1] == c_tag[:1].lower() + c_tag[1:] + 'Id' for _ in c_kids):
                walk(c, '' if tag == 'ManagedElement' else mo_name, msg_id)
                continue
            counts[c_tag] = counts.get(c_tag, 0) + 1
            for para, val in flat_xml(c, c_tag, counts[c_tag] - 1, sum(1 for _ in kids if _.tagName.split(':')[-1] == c_tag)):
                values[para] = F'{values[para]};{val}' if para in values else val
        entries.extend((op, mo_name, para, val, msg_id) for para, val in values.items())

    def flat_xml(elem, name, index, total):
        kids = [_ for _ in elem.childNodes if _.nodeType == 1]
        if not kids: return [(name, (elem.firstChild.data if elem.firstChild else '').strip())]
        name = F'{name}[{index}]' if total > 1 else name
        return [_ for c in kids for _ in flat_xml(c, F'{name}.{c.tagName.split(":")[-1]}', 0, 1)]

    for part in text.split(']]>]]>'):
        if '<config' not in part: continue
        try: doc = parseString(re.sub(r'<\?xml[^>]*\?>', '', part).strip())
        except Exception as e:
            script.usid.log.info(F'Debug CSV: xml part not read ({e})')
            continue
        msg_id = next((_.getAttribute('message-id') for _ in doc.getElementsByTagName('*') if _.tagName.split(':')[-1] == 'rpc'), '')
        for config in [_ for _ in doc.getElementsByTagName('*') if _.tagName.split(':')[-1] == 'config']:
            for mo in [_ for _ in config.childNodes if _.nodeType == 1]: walk(mo, '', msg_id)
    return entries


def mos_entries(script, text: str) -> list:
    entries, crn_mo = [], None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(('#', '$', '//')): continue
        if crn_mo is not None:
            if s == 'end': crn_mo = None
            else:
                para, _, val = s.partition(' ')
                entries.append(('crn', crn_mo, para, val.strip()))
            continue
        cmd, _, rest = s.partition(' ')
        rest = rest.strip()
        if cmd not in MOS_WRITE + MOS_READ or not rest: continue
        mo, _, rest = rest.partition(' ')
        mo = script.csv_ldn(mo)
        if cmd == 'crn':
            crn_mo = mo
            moc, _, mo_id = mo.split(',')[-1].partition('=')
            entries.append(('crn', mo, moc[:1].lower() + moc[1:] + 'Id', mo_id))
        elif cmd in ['set', 'mset', 'rset', 'lset', 'lmset']:
            para, _, val = rest.strip().partition(' ')
            entries.append((cmd, mo, para, val.strip()))
        else:
            entries.append((cmd, mo, rest.strip(), ''))
    return entries


def derived_rows(script, entries: list, fmt: str) -> list:
    rows, mo_cache = [], {}
    site_dcgk = dcgk_index(script, script.node)
    for op, mo_name, para, val, *msg_id in entries:
        key = re.sub(r'\[\d+\]', '', para).split('.')[0]
        mo = mo_name.rstrip('$,')
        moc = mo.split(',')[-1].split('=')[0]
        pattern = mo_name.endswith(('=', '$', ',')) or mo_name.startswith(',') or any(_ in mo_name for _ in ['^', '.*', '|'])
        if mo not in mo_cache:
            motype, db_params = db_lookup(script, mo) if not pattern else (None, {})
            cls = mom_class(script, moc, motype)
            dcgk = site_dcgk.get(mo, {}) if not pattern else {}
            mo_cache[mo] = (motype, db_params, cls, dcgk, flat_map(script, db_params) if fmt == 'xml' else {},
                            flat_map(script, dcgk) if fmt == 'xml' else {})
        motype, db_params, cls, dcgk, db_flat, dcgk_flat = mo_cache[mo]
        flags, takes_effect = cls[1].get(key, ([], '')) if cls else ([], '')
        remark, read_cmd = [], op in MOS_READ
        if fmt == 'xml':
            db_val, dcgk_val = db_flat.get(para, ''), dcgk_flat.get(para, '')
            operator = op or mom_operator(script, cls, key, moc, flags)
        else:
            db_val = mos_value(script, db_params[key][0]) if key in db_params else ''
            dcgk_val = mos_value(script, dcgk[key]) if key in dcgk else ''
            operator = op
        if read_cmd: source = 'Script (read command)'; remark.append('read command, no change on node')
        elif para == '' or (moc and para.lower() == script.get_moc_id(moc).lower()): source = 'Script (MO id / command)'
        elif key in dcgk and dcgk_val == val and key in db_params and db_val == val: source = 'MOC/DCGK (same value)'
        elif key in dcgk and dcgk_val == val: source = 'DCGK'
        elif key in db_params and db_val == val: source = 'MOC'
        else: source = 'Script (CIQ / calculated)'
        if pattern: remark.append('MO pattern, applies to all matching MOs')
        if source == 'DCGK' and db_val not in ['', val]: remark.append('DCGK value differs from MOC')
        if val == '' and op in ['crn', 'set', 'mset', 'rset', 'lset', ''] and para: remark.append('empty value')
        if not read_cmd and para and not pattern and operator in ['crn', 'set', 'rset', 'mset', 'ld']: remark += mom_remarks(script, cls, key, flags)
        rows.append({'node': script.node, 'script': script.__class__.__name__, 'message_id': msg_id[0] if msg_id else '', 'mo_name': mo_name, 'moc': moc, 'parameter_name': para,
                     'operator': operator, 'parameter_value': val, 'in_script': 'yes', 'source': source, 'source_method': 'derived (value match)',
                     'value_file': value_file(script, source if 'Script' not in source else '', script.node),
                     'db_value': db_val, 'dcgk_value': dcgk_val, 'backupflag': bf_text(db_params[key][1]) if key in db_params else '',
                     'mom_flags': ';'.join(flags), 'takes_effect': takes_effect, 'mom_file': mom_file(script, cls, key), 'remark': '; '.join(remark)})
    return rows

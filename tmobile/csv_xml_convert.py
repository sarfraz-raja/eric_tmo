"""
CSV <-> NETCONF XML conversion for the CSV / XML Convert page. Works only on in-memory text, nothing is written to disk.

CSV columns (TEMPLATE_COLUMNS): node, message_id, mo_name, operator, parameter_name, parameter_value
    mo_name          GNBCUCPFunction=1,Mcpc=1,McpcPCellProfile=X,McpcPCellProfileUeCfg=VoNR (ManagedElement=<id>, prefix optional)
    parameter_name   attr | struct.member | structList[0].member ; the MO id attribute (e.g. mcpcPCellProfileUeCfgId) starts a new MO
    parameter_value  list values separated by ';'
    operator         blank/crn/cr/set/ld/merge/create = merge, del/rdel/delete = xc:operation="delete", others (get, lset, pr, ...) skipped
The debug CSV of the tool (02_REMOTE/<node>/CSV) can be used directly, extra columns are ignored.
"""
import io
import re
import csv
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

TEMPLATE_COLUMNS = ['node', 'message_id', 'mo_name', 'operator', 'parameter_name', 'parameter_value']
REQUIRED_COLUMNS = ['mo_name', 'parameter_name', 'parameter_value']
LIST_SEPARATOR = ';'
DEFAULT_NODE = 'NODE'
DEFAULT_MESSAGE_ID = 'csv_to_xml'
MERGE_OPS, DELETE_OPS = {'', 'crn', 'cr', 'set', 'ld', 'merge', 'create', 'update'}, {'del', 'rdel', 'delete'}
NETCONF_NS = 'urn:ietf:params:xml:ns:netconf:base:1.0'
FALLBACK_NS = {'ManagedElement': 'ComTop', 'ENodeBFunction': 'Lrat', 'GNBDUFunction': 'GNBDU', 'GNBCUCPFunction': 'GNBCUCP',
               'GNBCUUPFunction': 'GNBCUUP', 'NodeSupport': 'RmeSupport', 'Equipment': 'ReqEquipment'}
HELLO = ('<?xml version="1.0" encoding="UTF-8"?>\n<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">\n  <capabilities>\n'
         '    <capability>urn:ietf:params:netconf:base:1.0</capability>\n    <capability>urn:com:ericsson:ebase:2.0.0</capability>\n'
         '  </capabilities>\n</hello>\n]]>]]>')
CLOSING = '<rpc message-id="Closing" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">\n  <close-session></close-session>\n</rpc>\n]]>]]>'
MO_SPLIT = re.compile(r',(?=[A-Za-z]\w*=)')
SEGMENT = re.compile(r'^(\w+)(?:\[(\d+)\])?$')
SAFE_NAME = re.compile(r'[^A-Za-z0-9_.-]+')


class ConvertError(ValueError):
    pass


def id_tag(moc: str) -> str: return moc[:1].lower() + moc[1:] + 'Id'
def local(tag: str) -> str: return tag.rsplit('}', 1)[-1].split(':')[-1]
def safe_name(name: str) -> str: return SAFE_NAME.sub('_', name).strip('_') or 'output'
def ordinal(n: int) -> str: return F'{n}{"th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")}'


def decode(data: bytes) -> str:
    for enc in ('utf-8-sig', 'cp1252'):
        try: return data.decode(enc)
        except UnicodeDecodeError: continue
    raise ConvertError('File encoding not supported, save it as UTF-8')


# ------------------------------------------------------------------ CSV -> XML
class Mo:
    def __init__(self, moc, mo_id, op=''):
        self.moc, self.mo_id, self.op = moc, mo_id, op
        self.attrs, self.children = {}, []

    def set_attr(self, para, value):
        segs = [SEGMENT.match(_) for _ in para.split('.')]
        if not all(segs): raise ConvertError(F'Invalid parameter_name: {para}')
        node = self.attrs
        for seg in segs[:-1]:
            items = node.setdefault(seg.group(1), [])
            index = int(seg.group(2) or 0)
            while len(items) <= index: items.append({})
            if not isinstance(items[index], dict): raise ConvertError(F'{para}: {seg.group(1)} is used both as value and as struct')
            node = items[index]
        node[segs[-1].group(1)] = value.split(LIST_SEPARATOR) if value != '' else ['']

    def to_xml(self, ns_map, depth):
        pad = '  ' * depth
        attr = F' xmlns="urn:com:ericsson:ecim:{ns_map[self.moc]}"' if self.moc in ns_map else ''
        if self.op == 'delete': attr += F' xmlns:xc="{NETCONF_NS}" xc:operation="delete"'
        lines = [F'{pad}<{self.moc}{attr}>', F'{pad}  <{id_tag(self.moc)}>{escape(self.mo_id)}</{id_tag(self.moc)}>']
        if self.op != 'delete':
            lines += attr_xml(self.attrs, depth + 1)
            for child in self.children: lines += child.to_xml(ns_map, depth + 1)
        return lines + [F'{pad}</{self.moc}>']


def attr_xml(attrs, depth):
    pad, lines = '  ' * depth, []
    for name, value in attrs.items():
        for item in value:
            if isinstance(item, dict): lines += [F'{pad}<{name}>'] + attr_xml(item, depth + 1) + [F'{pad}</{name}>']
            else: lines.append(F'{pad}<{name}>{escape(item)}</{name}>')
    return lines


def parse_mo_name(mo_name, me_id, line_no):
    parts = [tuple(_.split('=', 1)) for _ in MO_SPLIT.split(mo_name.strip())]
    if any(len(_) != 2 or not re.match(r'^[A-Za-z]\w*$', _[0]) for _ in parts): raise ConvertError(F'Row {line_no}: invalid mo_name "{mo_name}"')
    if parts[0][0] != 'ManagedElement': parts.insert(0, ('ManagedElement', me_id))
    return tuple(parts)


def build_rpc(rows, node, msg_id, ns_map):
    latest = {}
    me_id = next((r['mo_name'].split(',')[0].split('=', 1)[1] for r in rows if r['mo_name'].startswith('ManagedElement=')), node)

    def get_mo(path, create_new=False, op=''):
        if not create_new and path in latest: return latest[path]
        mo = Mo(*path[-1], op)
        if len(path) > 1: get_mo(path[:-1]).children.append(mo)
        latest[path] = mo
        return mo

    for row in rows:
        path = parse_mo_name(row['mo_name'], me_id, row['line'])
        op = 'delete' if row['op'] in DELETE_OPS else ''
        if row['parameter_name'] == id_tag(path[-1][0]):
            if len(path) == 1 and path in latest: continue
            get_mo(path, create_new=True, op=op)
            continue
        mo = get_mo(path)
        if op: mo.op = op
        if row['parameter_name']:
            try: mo.set_attr(row['parameter_name'], row['parameter_value'])
            except ConvertError as e: raise ConvertError(F'Row {row["line"]}: {e}')
    lines = [F'<rpc message-id="{escape(msg_id, {chr(34): "&quot;"})}" xmlns="{NETCONF_NS}">', '  <edit-config>', '    <target>',
             '      <running/>', '    </target>', F'    <config xmlns="{NETCONF_NS}">']
    for path, mo in latest.items():
        if len(path) == 1: lines += mo.to_xml(ns_map, 3)
    return '\n'.join(lines + ['    </config>', '  </edit-config>', '</rpc>', ']]>]]>'])


def read_csv_rows(text: str):
    reader = csv.DictReader(io.StringIO(text))
    columns = [(_ or '').strip() for _ in (reader.fieldnames or [])]
    missing = [_ for _ in REQUIRED_COLUMNS if _ not in columns]
    if missing: raise ConvertError(F'Required column missing: {", ".join(missing)}. Download the template for the column names.')
    reader.fieldnames = columns
    rows, skipped = [], 0
    for line_no, r in enumerate(reader, start=2):
        op = (r.get('operator') or '').strip().lower()
        mo_name = (r.get('mo_name') or '').strip()
        if not mo_name or (r.get('in_script') or '').strip().lower() == 'no' or op not in MERGE_OPS | DELETE_OPS:
            skipped += 1
            continue
        rows.append({'line': line_no, 'node': (r.get('node') or '').strip() or DEFAULT_NODE, 'op': op, 'mo_name': mo_name,
                     'msg_id': (r.get('message_id') or '').split('|')[0].strip() or DEFAULT_MESSAGE_ID,
                     'parameter_name': (r.get('parameter_name') or '').strip(), 'parameter_value': (r.get('parameter_value') or '').strip()})
    if not rows: raise ConvertError('No usable rows found in the CSV')
    return rows, skipped


def csv_to_xml(text: str, stem: str, ns_map: dict, split_by_message_id: bool = True):
    """Returns ([(file_name, xml_text), ...], used_rows, skipped_rows)."""
    rows, skipped = read_csv_rows(text)
    stem, files = safe_name(stem), []
    nodes = list(dict.fromkeys(r['node'] for r in rows))
    for node in nodes:
        node_rows = [r for r in rows if r['node'] == node]
        msg_ids = list(dict.fromkeys(r['msg_id'] for r in node_rows))
        rpcs = [(m, build_rpc([r for r in node_rows if r['msg_id'] == m], node, m, ns_map)) for m in msg_ids]
        name = F'{stem}_{safe_name(node)}' if len(nodes) > 1 else stem
        if split_by_message_id:
            groups = [(F'{name}_{ordinal(i)}_{safe_name(m)}' if len(rpcs) > 1 else name, [rpc]) for i, (m, rpc) in enumerate(rpcs, 1)]
        else: groups = [(name, [rpc for _, rpc in rpcs])]
        files += [(F'{file_name}.xml', '\n'.join([HELLO] + parts + [CLOSING]) + '\n') for file_name, parts in groups]
    return files, len(rows), skipped


# ------------------------------------------------------------------ XML -> CSV
def xml_to_rows(text: str) -> list:
    if re.search(r'<!DOCTYPE|<!ENTITY', text, re.I): raise ConvertError('XML with DOCTYPE/ENTITY is not supported')
    rows, found = [], False
    for part in text.split(']]>]]>'):
        part = re.sub(r'<\?xml[^>]*\?>', '', part).strip()
        if not part or 'config' not in part: continue
        try: root = ET.fromstring(part)
        except ET.ParseError as e: raise ConvertError(F'Invalid XML: {e}')
        msg_id = root.get('message-id', '') if local(root.tag) == 'rpc' else ''
        for config in [e for e in root.iter() if local(e.tag) == 'config']:
            found = True
            for mo in config: walk_mo(mo, (), msg_id, '', rows)
    if not found: raise ConvertError('No <config> block found, upload a NETCONF edit-config XML')
    return rows


def walk_mo(elem, parent, msg_id, node, rows):
    moc = local(elem.tag)
    id_elem = next((c for c in elem if local(c.tag) == id_tag(moc)), None)
    mo_id = (id_elem.text or '').strip() if id_elem is not None else ''
    path = parent + (F'{moc}={mo_id}',)
    node = node or mo_id
    op = 'del' if any(local(k) == 'operation' and v == 'delete' for k, v in elem.attrib.items()) else ('ld' if moc == 'ManagedElement' else 'crn')
    mo_name = ','.join(path)
    rows.append([node, msg_id, mo_name, op, id_tag(moc), mo_id])
    kids = [c for c in elem if local(c.tag) != id_tag(moc)]
    totals = {}
    for c in kids: totals[local(c.tag)] = totals.get(local(c.tag), 0) + 1
    values, counts, children = {}, {}, []
    for c in kids:
        tag = local(c.tag)
        if len(c) and any(local(g.tag) == id_tag(tag) for g in c):
            children.append(c)
            continue
        counts[tag] = counts.get(tag, 0) + 1
        for para, val in flat_leaf(c, tag, counts[tag] - 1, totals[tag]):
            values[para] = F'{values[para]}{LIST_SEPARATOR}{val}' if para in values else val
    rows.extend([node, msg_id, mo_name, op, para, val] for para, val in values.items())
    for c in children: walk_mo(c, path, msg_id, node, rows)


def flat_leaf(elem, name, index, total):
    if not len(elem): return [(name, (elem.text or '').strip())]
    name = F'{name}[{index}]' if total > 1 else name
    return [_ for c in elem for _ in flat_leaf(c, F'{name}.{local(c.tag)}', 0, 1)]


def xml_to_csv(text: str) -> tuple:
    """Returns (csv_text, row_count)."""
    rows = xml_to_rows(text)
    out = io.StringIO()
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(TEMPLATE_COLUMNS)
    writer.writerows(rows)
    return out.getvalue(), len(rows)


def template_csv() -> str:
    out = io.StringIO()
    csv.writer(out, lineterminator='\n').writerow(TEMPLATE_COLUMNS)
    return out.getvalue()


def zip_files(files: list) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, text in files: z.writestr(name, text)
    return buf.getvalue()

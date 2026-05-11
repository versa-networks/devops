#!/usr/bin/env python3
import os
import sys
import xml.etree.ElementTree as ET

script_dir = os.path.dirname(os.path.abspath(__file__))


def qn(name):
    if ' ' in name:
        return f'"{name}"'
    return name


def fmt_members(members):
    if len(members) == 1:
        return qn(members[0])
    return '[ ' + ' '.join(qn(m) for m in members) + ' ]'


def fmt_val(text):
    if '\n' in text or ' ' in text:
        return f'"{text}"'
    return text


def get_members(el):
    return [m.text for m in el.findall('member') if m.text is not None]


def obj_base(loc, section, name):
    return f'set shared {section} {qn(name)}'


def convert_address(panorama, lines):
    el = panorama.find('address')
    if el is None:
        return 0
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'address', name)
        emitted = False
        for child in entry:
            tag = child.tag
            text = (child.text or '').strip()
            if tag in ('ip-netmask', 'ip-range', 'fqdn', 'ip-wildcard'):
                if text:
                    lines.append(f'{base} {tag} {fmt_val(text)}')
                    emitted = True
            elif tag == 'description':
                if text:
                    lines.append(f'{base} description {fmt_val(text)}')
            elif tag == 'tag':
                members = get_members(child)
                if members:
                    lines.append(f'{base} tag {fmt_members(members)}')
        if not emitted:
            lines.append(base)
        count += 1
    return count


def convert_address_group(panorama, lines):
    el = panorama.find('address-group')
    if el is None:
        return 0
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'address-group', name)
        for child in entry:
            tag = child.tag
            if tag == 'static':
                members = get_members(child)
                if members:
                    lines.append(f'{base} static {fmt_members(members)}')
            elif tag == 'dynamic':
                filt = child.find('filter')
                if filt is not None and filt.text:
                    lines.append(f'{base} dynamic filter {fmt_val(filt.text.strip())}')
            elif tag == 'description':
                if child.text and child.text.strip():
                    lines.append(f'{base} description {fmt_val(child.text.strip())}')
            elif tag == 'tag':
                members = get_members(child)
                if members:
                    lines.append(f'{base} tag {fmt_members(members)}')
        count += 1
    return count


def convert_service(panorama, lines):
    el = panorama.find('service')
    if el is None:
        return 0
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'service', name)
        proto_el = entry.find('protocol')
        if proto_el is not None:
            for proto in ('tcp', 'udp', 'sctp'):
                p = proto_el.find(proto)
                if p is not None:
                    port_el = p.find('port')
                    if port_el is not None and port_el.text:
                        lines.append(f'{base} protocol {proto} port {port_el.text.strip()}')
                    src_el = p.find('source-port')
                    if src_el is not None and src_el.text:
                        lines.append(f'{base} protocol {proto} source-port {src_el.text.strip()}')
                    override_el = p.find('override')
                    if override_el is not None:
                        if override_el.find('no') is not None:
                            lines.append(f'{base} protocol {proto} override no')
                        elif override_el.find('yes') is not None:
                            lines.append(f'{base} protocol {proto} override yes')
        desc = entry.find('description')
        if desc is not None and desc.text and desc.text.strip():
            lines.append(f'{base} description {fmt_val(desc.text.strip())}')
        tag_el = entry.find('tag')
        if tag_el is not None:
            members = get_members(tag_el)
            if members:
                lines.append(f'{base} tag {fmt_members(members)}')
        count += 1
    return count


def convert_service_group(panorama, lines):
    el = panorama.find('service-group')
    if el is None:
        return 0
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'service-group', name)
        members_el = entry.find('members')
        if members_el is not None:
            members = get_members(members_el)
            if members:
                lines.append(f'{base} members {fmt_members(members)}')
        tag_el = entry.find('tag')
        if tag_el is not None:
            members = get_members(tag_el)
            if members:
                lines.append(f'{base} tag {fmt_members(members)}')
        count += 1
    return count


def convert_application(panorama, lines):
    el = panorama.find('application')
    if el is None:
        return 0
    SIMPLE = {
        'subcategory', 'category', 'technology', 'description', 'risk',
        'used-by-malware', 'able-to-transfer-file', 'has-known-vulnerability',
        'tunnel-other-application', 'tunnel-applications', 'pervasive-use',
        'evasive-behavior', 'consume-big-bandwidth', 'prone-to-misuse',
        'file-type-ident', 'virus-ident', 'data-ident', 'parent-app',
        'timeout', 'tcp-timeout', 'udp-timeout', 'tcp-half-closed-timeout',
        'tcp-time-wait-timeout', 'no-appid-caching', 'alg-disable-capability',
        'decode-as'
    }
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'application', name)
        for child in entry:
            tag = child.tag
            if tag == 'default':
                port_el = child.find('port')
                if port_el is not None:
                    members = get_members(port_el)
                    if members:
                        lines.append(f'{base} default port {fmt_members(members)}')
                if child.find('ident-by-icmp-type') is not None:
                    lines.append(f'{base} default ident-by-icmp-type yes')
                if child.find('ident-by-icmp6-type') is not None:
                    lines.append(f'{base} default ident-by-icmp6-type yes')
            elif tag in SIMPLE:
                if child.text and child.text.strip():
                    lines.append(f'{base} {tag} {fmt_val(child.text.strip())}')
        count += 1
    return count


def convert_application_group(panorama, lines):
    el = panorama.find('application-group')
    if el is None:
        return 0
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'application-group', name)
        members_el = entry.find('members')
        if members_el is not None:
            members = get_members(members_el)
            if members:
                lines.append(f'{base} members {fmt_members(members)}')
        count += 1
    return count


def convert_tag(panorama, lines):
    el = panorama.find('tag')
    if el is None:
        return 0
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'tag', name)
        color_el = entry.find('color')
        comments_el = entry.find('comments')
        if color_el is not None and color_el.text:
            lines.append(f'{base} color {color_el.text.strip()}')
        if comments_el is not None and comments_el.text:
            lines.append(f'{base} comments {fmt_val(comments_el.text.strip())}')
        if color_el is None and comments_el is None:
            lines.append(base)
        count += 1
    return count


def convert_schedule(panorama, lines):
    el = panorama.find('schedule')
    if el is None:
        return 0
    DAYS = ('sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday')
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'schedule', name)
        stype = entry.find('schedule-type')
        if stype is None:
            count += 1
            continue
        recurring = stype.find('recurring')
        non_recurring = stype.find('non-recurring')
        if recurring is not None:
            weekly = recurring.find('weekly')
            daily = recurring.find('daily')
            if weekly is not None:
                for day in DAYS:
                    day_el = weekly.find(day)
                    if day_el is not None:
                        members = get_members(day_el)
                        if members:
                            lines.append(f'{base} schedule-type recurring weekly {day} {fmt_members(members)}')
            elif daily is not None:
                members = get_members(daily)
                if members:
                    lines.append(f'{base} schedule-type recurring daily {fmt_members(members)}')
        elif non_recurring is not None:
            members = get_members(non_recurring)
            if members:
                lines.append(f'{base} schedule-type non-recurring {fmt_members(members)}')
        count += 1
    return count


def convert_external_list(panorama, lines):
    el = panorama.find('external-list')
    if el is None:
        return 0
    RECURRING_TYPES = ('five-minute', 'hourly', 'daily', 'weekly', 'monthly')
    LIST_TYPES = ('ip', 'url', 'domain', 'imsi', 'imei', 'predefined-ip', 'predefined-url')
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'external-list', name)
        type_el = entry.find('type')
        if type_el is not None:
            for ltype in LIST_TYPES:
                lt = type_el.find(ltype)
                if lt is not None:
                    url_el = lt.find('url')
                    if url_el is not None and url_el.text:
                        lines.append(f'{base} type {ltype} url {fmt_val(url_el.text.strip())}')
                    recurring = lt.find('recurring')
                    if recurring is not None:
                        for rt in RECURRING_TYPES:
                            if recurring.find(rt) is not None:
                                lines.append(f'{base} type {ltype} recurring {rt}')
                                break
                    description = lt.find('description')
                    if description is not None and description.text:
                        lines.append(f'{base} type {ltype} description {fmt_val(description.text.strip())}')
        count += 1
    return count


def convert_region(panorama, lines):
    el = panorama.find('region')
    if el is None:
        return 0
    count = 0
    for entry in el.findall('entry'):
        name = entry.get('name', '')
        loc = entry.get('loc') or 'shared'
        base = obj_base(loc, 'region', name)
        geo = entry.find('geo-location')
        addr_el = entry.find('address')
        if geo is not None:
            lat = geo.find('latitude')
            lon = geo.find('longitude')
            if lat is not None and lat.text:
                lines.append(f'{base} geo-location latitude {lat.text.strip()}')
            if lon is not None and lon.text:
                lines.append(f'{base} geo-location longitude {lon.text.strip()}')
        if addr_el is not None:
            members = get_members(addr_el)
            if members:
                lines.append(f'{base} address {fmt_members(members)}')
        if geo is None and addr_el is None:
            lines.append(base)
        count += 1
    return count


RULE_MEMBER_FIELDS = {
    'to', 'from', 'source', 'destination', 'source-user',
    'category', 'application', 'service', 'source-hip',
    'destination-hip', 'tag'
}

RULE_SIMPLE_FIELDS = {
    'action', 'rule-type', 'log-setting', 'disabled',
    'description', 'log-start', 'log-end', 'schedule',
    'negate-source', 'negate-destination', 'group-tag'
}


def rule_entry_to_lines(prefix, rule_name, entry):
    lines = []
    base = f'set {prefix} {qn(rule_name)}'
    for child in entry:
        tag = child.tag
        if tag == 'profile-setting':
            group_el = child.find('group')
            if group_el is not None:
                members = get_members(group_el)
                if members:
                    lines.append(f'{base} profile-setting group {qn(members[0])}')
            profiles_el = child.find('profiles')
            if profiles_el is not None:
                for ptype in profiles_el:
                    members = get_members(ptype)
                    for m in members:
                        lines.append(f'{base} profile-setting profiles {ptype.tag} {qn(m)}')
        elif tag in RULE_MEMBER_FIELDS:
            members = get_members(child)
            if members:
                lines.append(f'{base} {tag} {fmt_members(members)}')
        elif tag == 'target':
            negate_el = child.find('negate')
            if negate_el is not None and negate_el.text:
                lines.append(f'{base} target negate {negate_el.text.strip()}')
        elif tag == 'option':
            for opt_child in child:
                if opt_child.text and opt_child.text.strip():
                    lines.append(f'{base} option {opt_child.tag} {opt_child.text.strip()}')
        elif tag in RULE_SIMPLE_FIELDS or child.text:
            text = child.text
            if text is not None:
                text = text.strip()
                if text:
                    lines.append(f'{base} {tag} {fmt_val(text)}')
    return lines


def convert_security_rules(panorama, rulebase_tag, lines):
    rb = panorama.find(rulebase_tag)
    if rb is None:
        return 0
    sec = rb.find('security')
    if sec is None:
        return 0
    rules = sec.find('rules')
    if rules is None:
        return 0
    count = 0
    for entry in rules.findall('entry'):
        rule_name = entry.get('name', '')
        prefix = f'shared post-rulebase security rules'
        lines.extend(rule_entry_to_lines(prefix, rule_name, entry))
        count += 1
    return count


def main():
    if len(sys.argv) >= 2:
        xml_path = os.path.join(script_dir, sys.argv[1])
    else:
        xml_path = os.path.join(script_dir, '../temp/sp-config.xml')

    if len(sys.argv) >= 3:
        out_path = os.path.join(script_dir, sys.argv[2])
    else:
        out_path = os.path.join(script_dir, '../source-pan-rules.txt')

    if not os.path.isfile(xml_path):
        print(f'ERROR: XML file not found: {xml_path}')
        sys.exit(1)

    tree = ET.parse(xml_path)
    root = tree.getroot()
    all_lines = []

    panorama = root.find('panorama')
    if panorama is None:
        print('ERROR: No <panorama> element found in XML')
        sys.exit(1)

    converters = [
        ('address',           convert_address),
        ('address-group',     convert_address_group),
        ('service',           convert_service),
        ('service-group',     convert_service_group),
        ('application',       convert_application),
        ('application-group', convert_application_group),
        ('tag',               convert_tag),
        ('schedule',          convert_schedule),
        ('external-list',     convert_external_list),
        ('region',            convert_region),
    ]

    for label, fn in converters:
        n = fn(panorama, all_lines)
        if n:
            print(f'{label}: {n} entries')

    for rb_tag in ('pre-rulebase', 'post-rulebase'):
        n = convert_security_rules(panorama, rb_tag, all_lines)
        if n:
            print(f'security rules ({rb_tag}): {n} rules')

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        for line in all_lines:
            f.write(line + '\n')

    print(f'\nTotal output lines: {len(all_lines)}')
    print(f'Output: {out_path}')


main()

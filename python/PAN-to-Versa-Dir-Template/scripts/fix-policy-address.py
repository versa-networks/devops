#!/usr/bin/env python3
import re
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
source_file = os.path.join(script_dir, "../source-pan-rules.txt")

IP_RE = re.compile(r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$')
RULE_LINE_RE = re.compile(r'^set\s+\S+\s+(pre|post)-rulebase\s+security\s+rules\s+')
FIELD_RE = re.compile(r'\b(source|destination)\s+(\[([^\]]*)\]|(\S+))')


def ip_to_name(ip):
    return ip.replace('.', '_').replace('/', '_')


def ip_to_netmask(ip):
    if '/' not in ip:
        return ip + '/32'
    return ip


def process_field_match(match, new_objects):
    field = match.group(1)
    full_val = match.group(2).strip()

    if full_val.startswith('['):
        inner_str = match.group(3).strip() if match.group(3) else ''
        tokens = inner_str.split()
        new_tokens = []
        for token in tokens:
            if IP_RE.match(token):
                name = ip_to_name(token)
                new_objects[name] = ip_to_netmask(token)
                new_tokens.append(name)
            else:
                new_tokens.append(token)
        return field + ' [ ' + ' '.join(new_tokens) + ' ]'
    else:
        single = match.group(4)
        if single and IP_RE.match(single):
            name = ip_to_name(single)
            new_objects[name] = ip_to_netmask(single)
            return field + ' ' + name
        return match.group(0)


with open(source_file, 'r') as fh:
    lines = fh.readlines()

new_objects = {}
modified_lines = []

for line in lines:
    stripped = line.rstrip('\n')
    if RULE_LINE_RE.match(stripped):
        def replacer(m):
            return process_field_match(m, new_objects)
        new_line = FIELD_RE.sub(replacer, stripped)
        modified_lines.append(new_line + '\n')
    else:
        modified_lines.append(line)

address_lines = []
for name, netmask in new_objects.items():
    address_lines.append(f'set shared address {name} ip-netmask {netmask}\n')
    address_lines.append(f'set shared address {name} description "Created by PAN Conversion scripts"\n')

with open(source_file, 'w') as fh:
    fh.writelines(modified_lines)
    if address_lines:
        fh.write('\n')
        fh.writelines(address_lines)

print(f"Done. {len(new_objects)} address object(s) created.")
for name, netmask in new_objects.items():
    print(f"  {name}  ({netmask})")

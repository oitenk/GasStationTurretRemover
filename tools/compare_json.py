"""Compare two WolvenKit JSON exports, ignoring the header and handle/buffer numbering.

usage: python compare_json.py <a.json> <b.json>
Exits non-zero and prints the first differences when the resource data differs.
"""
import json
import sys

import zlib

IGNORED = {'HandleId', 'HandleRefId', 'BufferId', 'Type'}


def fnv1a64(text):
    h = 0xcbf29ce484222325
    for b in text.encode('utf-8'):
        h = ((h ^ b) * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


def as_hash(obj):
    """A name stored as a hash reads back as the bare hash when the reader cannot look the
    name up, so names are compared by the hash the game file holds."""
    value = obj['$value']
    if obj['$storage'] != 'string':
        return int(value)
    if obj.get('$type') == 'ResourcePath':
        return fnv1a64(value.lower())
    if obj.get('$type') == 'TweakDBID':
        data = value.encode('utf-8')
        return (len(data) << 32) | zlib.crc32(data)
    return value


def strip(obj):
    if isinstance(obj, dict):
        if '$storage' in obj and obj.get('$type') in ('ResourcePath', 'TweakDBID'):
            return {'$type': obj['$type'], 'hash': as_hash(obj)}
        return {k: strip(v) for k, v in obj.items() if k not in IGNORED}
    if isinstance(obj, list):
        return [strip(v) for v in obj]
    return obj


def diff(a, b, path, out):
    if len(out) >= 20:
        return
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f'{path}/{k}: only in {"b" if k not in a else "a"}')
            else:
                diff(a[k], b[k], f'{path}/{k}', out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f'{path}: length {len(a)} vs {len(b)}')
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f'{path}/{i}', out)
    elif a != b:
        out.append(f'{path}: {json.dumps(a)[:80]} vs {json.dumps(b)[:80]}')


def main(a_path, b_path):
    a = strip(json.load(open(a_path, encoding='utf-8'))['Data'])
    b = strip(json.load(open(b_path, encoding='utf-8'))['Data'])
    out = []
    diff(a, b, '', out)
    if out:
        print('\n'.join(out))
        raise SystemExit(1)
    print('identical:', a_path.replace('\\', '/').rsplit('/', 1)[-1])


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])

"""Generate the mod's sector and streaming block JSON from the vanilla game sectors.

The two standing turrets outside the q104 gas station are copied, unchanged, out of
the always-on part of their vanilla sectors into a new sector whose only node range
is the "q104" variant of the station's devices prefab. The quest already switches
that variant on during Life During Wartime and off when it ends.

Inputs are WolvenKit JSON exports (WolvenKit.CLI convert serialize) of:
  base\\worlds\\03_night_city\\_compiled\\default\\exterior_-29_-67_1_0.streamingsector
  base\\worlds\\03_night_city\\_compiled\\default\\exterior_-29_-68_1_0.streamingsector
  base\\worlds\\03_night_city\\_compiled\\default\\blocks\\all.streamingblock

usage: python make_sources.py <folder with the three .json exports> <output source folder>
"""
import copy
import json
import os
import sys

DEFAULT = 'base\\worlds\\03_night_city\\_compiled\\default\\'
MOD_DIR = 'mod\\gas_station_turret_remover\\'
SECTOR_PATH = MOD_DIR + 'gas_station_turrets.streamingsector'
BLOCK_PATH = MOD_DIR + 'gas_station_turrets.streamingblock'

DEVICES_PREFAB = ('$/03_night_city/se5/loc_q104_gas_station_prefabHHXSKEQ/'
                  'loc_q104_gas_station_gameplay_prefabDBGQ7JI/#loc_q104_gas_station_devices')
VARIANT_NAME = 'q104'

# (sector, nodeData index, node ref the entry must carry). The indices are also the
# nodeDeletions in the .xl file, and the counts its expectedNodes.
TURRETS = [
    ('exterior_-29_-67_1_0', 842, DEVICES_PREFAB + '/#q104_gas_station_turret1'),
    ('exterior_-29_-68_1_0', 251, DEVICES_PREFAB + '/#q104_gas_station_turret3'),
]
EXPECTED_NODES = {'exterior_-29_-67_1_0': 3624, 'exterior_-29_-68_1_0': 1418}


def load(folder, name):
    with open(os.path.join(folder, name + '.json'), encoding='utf-8') as f:
        return json.load(f)


def renumber(node, counters):
    """Give every handle and buffer in a copied node a fresh id.

    References between handles inside the node follow the new ids; a reference to a
    handle outside the node cannot be carried over and stops the build.
    """
    mapping = {}

    def assign(obj):
        if isinstance(obj, dict):
            if 'HandleId' in obj:
                mapping[obj['HandleId']] = str(counters['handle'])
                obj['HandleId'] = mapping[obj['HandleId']]
                counters['handle'] += 1
            if 'BufferId' in obj:
                obj['BufferId'] = str(counters['buffer'])
                counters['buffer'] += 1
            for v in obj.values():
                assign(v)
        elif isinstance(obj, list):
            for v in obj:
                assign(v)

    def relink(obj):
        if isinstance(obj, dict):
            if 'HandleRefId' in obj:
                if obj['HandleRefId'] not in mapping:
                    raise SystemExit('copied node references a handle outside itself')
                obj['HandleRefId'] = mapping[obj['HandleRefId']]
            for v in obj.values():
                relink(v)
        elif isinstance(obj, list):
            for v in obj:
                relink(v)

    assign(node)
    relink(node)


def main(src, out):
    block = load(src, 'all.streamingblock')
    descriptors = {d['data']['DepotPath']['$value']: d for d in block['Data']['RootChunk']['descriptors']}

    template = None
    nodes, node_data, node_refs = [], [], []
    box_min = [float('inf')] * 3
    box_max = [float('-inf')] * 3
    counters = {'handle': 0, 'buffer': 1}  # buffer 0 is the nodeData buffer

    for sector_name, index, ref in TURRETS:
        sector = load(src, sector_name + '.streamingsector')
        root = sector['Data']['RootChunk']
        entries = root['nodeData']['Data']
        if len(entries) != EXPECTED_NODES[sector_name]:
            raise SystemExit(f'{sector_name} has {len(entries)} nodes, expected {EXPECTED_NODES[sector_name]}')

        entry = copy.deepcopy(entries[index])
        if entry['QuestPrefabRefHash']['$value'] != ref:
            raise SystemExit(f'{sector_name}[{index}] is {entry["QuestPrefabRefHash"]["$value"]}, expected {ref}')
        if index >= root['variantIndices'][1]:
            raise SystemExit(f'{sector_name}[{index}] is not in the always-on range')

        node = copy.deepcopy(root['nodes'][entry['NodeIndex']])
        if node['Data']['$type'] != 'worldEntityNode':
            raise SystemExit(f'{sector_name}[{index}] is a {node["Data"]["$type"]}, expected worldEntityNode')
        renumber(node, counters)

        entry['NodeIndex'] = len(nodes)
        nodes.append(node)
        node_data.append(entry)
        node_refs.append(copy.deepcopy(entry['QuestPrefabRefHash']))

        # Stream the new sector whenever either source sector would be streamed.
        sbox = descriptors[DEFAULT + sector_name + '.streamingsector']['streamingBox']
        for i, axis in enumerate('XYZ'):
            box_min[i] = min(box_min[i], sbox['Min'][axis])
            box_max[i] = max(box_max[i], sbox['Max'][axis])

        if template is None:
            template = sector
            vanilla_desc = descriptors[DEFAULT + sector_name + '.streamingsector']

    variant = next(v for v in vanilla_desc['variants']
                   if v['nodeRef']['$value'] == DEVICES_PREFAB and v['name']['$value'] == VARIANT_NAME)

    # Sector: one empty always-on range, then the q104 variant range holding both turrets.
    sector = {
        'Header': {k: v for k, v in template['Header'].items() if k not in ('ExportedDateTime', 'ArchiveFileName')},
        'Data': {
            'Version': template['Data']['Version'],
            'BuildVersion': template['Data']['BuildVersion'],
            'RootChunk': None,
            'EmbeddedFiles': [],
        },
    }
    troot = template['Data']['RootChunk']
    root = {
        '$type': 'worldStreamingSector',
        'category': troot['category'],
        'cookingPlatform': troot['cookingPlatform'],
        'externInplaceResource': troot['externInplaceResource'],
        'level': troot['level'],
        'localInplaceResource': [],
        'nodeData': {k: v for k, v in troot['nodeData'].items() if k != 'Data'},
        'nodeRefs': node_refs,
        'nodes': nodes,
        'persistentNodeIndex': 0,
        'persistentNodes': [],
        'variantIndices': [0, 0],
        'variantNodes': [[]],
        'version': troot['version'],
    }
    root['nodeData']['BufferId'] = '0'
    root['nodeData']['Data'] = node_data
    sector['Data']['RootChunk'] = root

    # Block: one descriptor for the new sector, with the vanilla q104 variant copied as range 1.
    new_variant = copy.deepcopy(variant)
    new_variant['rangeIndex'] = 1
    block_index = {'$type': 'worldStreamingBlockIndex', 'oup': 'Base', 'rldGridCell': 0}
    descriptor = {
        '$type': 'worldStreamingSectorDescriptor',
        'blockIndex': copy.deepcopy(block_index),
        'category': vanilla_desc['category'],
        'data': {'DepotPath': {'$type': 'ResourcePath', '$storage': 'string', '$value': SECTOR_PATH},
                 'Flags': 'Soft'},
        'level': vanilla_desc['level'],
        'numNodeRanges': 2,
        'questPrefabNodeRef': {'$type': 'NodeRef', '$storage': 'uint64', '$value': '0'},
        'streamingBox': {
            '$type': 'Box',
            'Max': {'$type': 'Vector4', 'W': 1, 'X': box_max[0], 'Y': box_max[1], 'Z': box_max[2]},
            'Min': {'$type': 'Vector4', 'W': 1, 'X': box_min[0], 'Y': box_min[1], 'Z': box_min[2]},
        },
        'variants': [new_variant],
    }
    new_block = {
        'Header': {k: v for k, v in block['Header'].items() if k not in ('ExportedDateTime', 'ArchiveFileName')},
        'Data': {
            'Version': block['Data']['Version'],
            'BuildVersion': block['Data']['BuildVersion'],
            'RootChunk': {
                '$type': 'worldStreamingBlock',
                'cookingPlatform': block['Data']['RootChunk']['cookingPlatform'],
                'descriptors': [descriptor],
                'index': block_index,
            },
            'EmbeddedFiles': [],
        },
    }

    for path, data in ((SECTOR_PATH, sector), (BLOCK_PATH, new_block)):
        dest = os.path.join(out, *path.split('\\')) + '.json'
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
        print('wrote', dest)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])

"""国土数値情報 N03 (2024-01-01) -> 市区町村単位に dissolve + 簡略化 -> data/kansai_muni.geojson"""
import json, glob, collections
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
groups = collections.defaultdict(list)
for f in sorted(glob.glob('/workspace/ppp-dashboard/raw/n03/N03-20240101_*.geojson')):
    for ft in json.load(open(f))['features']:
        p = ft['properties']
        if not p['N03_004'] or p['N03_004'] == '所属未定地': continue
        groups[(p['N03_001'], p['N03_004'])].append(shape(ft['geometry']))
feats = []
for (pref, muni), gs in groups.items():
    g = unary_union(gs).simplify(0.003, preserve_topology=True)
    g = shape(json.loads(json.dumps(mapping(g))))  # normalize
    def r(o):
        if isinstance(o, (list, tuple)):
            return [r(x) for x in o] if not isinstance(o[0], float) else [round(o[0], 4), round(o[1], 4)]
        return o
    m = mapping(g); m = {'type': m['type'], 'coordinates': r(m['coordinates'])}
    feats.append({'type': 'Feature', 'properties': {'name': pref + muni, 'pref': pref, 'muni': muni}, 'geometry': m})
json.dump({'type': 'FeatureCollection', 'features': feats}, open('/workspace/ppp-dashboard/data/kansai_muni.geojson', 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(feats))

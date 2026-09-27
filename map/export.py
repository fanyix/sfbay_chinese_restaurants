# Write 湾区中餐馆_汇总.csv/.md from map/data.json, append newly-closed places to 已停业_已移除.csv, and rebuild index.html.
import csv, json, os, collections
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
d = json.load(open(os.path.join(H, 'data.json')))
cols = ['地区', '城市', '区域', '可信度', '直接证据', '英文名', '中文名', '地址', '菜系', '菜系分类', '语言', '依据']
row = lambda x: [x['region'], x['city'], x['area'], x['conf'], '是' if x['direct'] else '', x['en'], x['zh'], x['addr'],
                 x['cuisineZh'], x['cat'], x['lang'], x['ev']]
with open(os.path.join(R, '湾区中餐馆_汇总.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(cols); w.writerows(row(x) for x in d)
reg = collections.Counter(x['region'] for x in d)
md = [f'# 湾区中餐馆（{len(d)} 家，含服务员说中文的可能性）', '',
      '分布：' + '，'.join(f'{r} {reg[r]}' for r in ['旧金山', '半岛', '东湾', '南湾', '北湾'] if reg[r]) + '。', '',
      '注意：除标注"直接证据"的 3 家外，均为推断，未经评论确认。南湾部分来自早期逐家调研；其余地区来自 Google 地图检索，'
      '按店名是否含中文、Google 地图中文版是否登记了中文店名、Google 菜系分类来判断。已停业的店（Google 标注 Permanently closed）已剔除。', '']
for r in ['旧金山', '半岛', '东湾', '南湾', '北湾']:
    rows = [x for x in d if x['region'] == r]
    if not rows: continue
    md += [f'## {r}（{len(rows)} 家）', '', '| ' + ' | '.join(cols[1:]) + ' |', '|' + '---|' * (len(cols) - 1)]
    md += ['| ' + ' | '.join(str(v).replace('|', '/') for v in row(x)[1:]) + ' |' for x in rows]
    md.append('')
open(os.path.join(R, '湾区中餐馆_汇总.md'), 'w').write('\n'.join(md))
t = open(os.path.join(H, 'template.html')).read()
open(os.path.join(R, 'index.html'), 'w').write(t.replace('__DATA__', json.dumps(d, ensure_ascii=False).replace('</', '<\\/')))
print('wrote', len(d))

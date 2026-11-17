"""Build assets/app-ko.js from the English bundle + i18n/ko.txt (segment id|Korean, ⏎ = newline).
Rerun after any rebuild of the English bundle; it fails loudly if segment ids no longer line up."""
import glob, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from segments import segments

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = [p for p in glob.glob(f'{root}/assets/app-*.js') if not p.endswith('app-ko.js')]
assert len(src) == 1, src
s = open(src[0], encoding='utf-8').read()
seg = segments(s)
assert all(x[1] <= y[0] for x, y in zip(seg, seg[1:]))

ko = {}
for name in ('ko.txt', 'ko_teams.txt'):  # main page, team pages
    for line in open(f'{os.path.dirname(__file__)}/{name}', encoding='utf-8'):
        i, _, t = line.rstrip('\n').partition('|')  # trailing spaces in ko*.txt are meaningful
        assert int(i) not in ko, f'duplicate id {i}'
        ko[int(i)] = t.replace('⏎', '\n')
# English ordinals (1st, 22nd, ...) become 1위, 22위
for i, (_, _, en) in enumerate(seg):
    if i not in ko and re.fullmatch(r'\d+(st|nd|rd|th)', en):
        ko[i] = en.rstrip('stndrh') + '위'

out = s
for i in sorted(ko, reverse=True):  # back to front so offsets stay valid
    a, b, en = seg[i]
    assert '`' not in ko[i] and '${' not in ko[i], i
    t = ko[i]
    if en[:1] == ' ' and t[:1] != ' ' and t: t = ' ' + t
    if en[-1:] == ' ' and t[-1:] != ' ' and t: t += ' '
    out = out[:a] + t + out[b:]

# Korean ordinals: 1위, 2위 ... (the English helper appends st/nd/rd/th)
old = 'function xt(e){let t=[`th`,`st`,`nd`,`rd`],n=e%100;return e+(t[(n-20)%10]||t[n]||t[0])}'
assert out.count(old) == 1
out = out.replace(old, 'function xt(e){return e+`위`}')

# Team page "N <cars> raced all eight rounds" sentence, rebuilt in Korean word order
old = 'return[...new Set(e.cars.map(e=>e.entrant))].length===1?`${Rn[t]} ${x(zn(n))} raced all eight rounds.`:e.id===`ferrari`?`Three 499Ps raced all eight rounds: the works #50 and #51, and AF Corse’s privateer #83.`:`${Rn[t]} ${x(zn(n))} raced all eight rounds: ${e.cars.map(e=>`the #${e.num} for ${x(e.entrant)}`).join(` and `)}.`'
assert out.count(old) == 1
out = out.replace(old, 'return[...new Set(e.cars.map(e=>e.entrant))].length===1?`${x(n)} ${t}대가 8라운드를 모두 달렸다.`:e.id===`ferrari`?`499P 세 대가 8라운드를 모두 달렸다. 제조사 직영(워크스) #50과 #51, 그리고 민간 팀 AF Corse의 #83이다.`:`${x(n)} ${t}대가 8라운드를 모두 달렸다. ${e.cars.map(e=>`${x(e.entrant)}의 #${e.num}`).join(`, `)}.`')

open(f'{root}/assets/app-ko.js', 'w', encoding='utf-8').write(out)
print('translated', len(ko), 'segments ->', f'{root}/assets/app-ko.js')

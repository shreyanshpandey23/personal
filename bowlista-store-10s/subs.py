"""subtitles_en.srt: one cue per narration line, switched at the next line (the same timing as the page's subtitle bar)."""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); LIB = os.environ['LIB']
lines = {l['id']: l['text'] for l in json.load(open(os.path.join(HERE, 'lines.json')))}
E = json.load(open(os.path.join(HERE, 'events.json'))); ev = sorted([e for e in E['ev'] if e['type'] == 'voice'], key=lambda e: e['t'])
cues = [{'t0': e['t'], 't1': (ev[i + 1]['t'] - .05) if i + 1 < len(ev) else E['dur'], 'text': lines[e['id']]} for i, e in enumerate(ev)]
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True); json.dump(cues, open(os.path.join(HERE, 'out', 'cues.json'), 'w'))
subprocess.run([os.path.join(LIB, '.venv/bin/python'), os.path.join(LIB, 'core/render/srt.py'), os.path.join(HERE, 'out', 'cues.json'), os.path.join(HERE, 'subtitles_en.srt')], check=True)

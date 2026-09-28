"""只检查双文件存在、HTML基本结构和未替换槽位；不判断语义或视觉。"""
import argparse
from pathlib import Path
import re
import json
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--md',required=True)
p.add_argument('--html',required=True)
a=p.parse_args()
errors=[]
texts={}
for kind,path in [('md',a.md),('html',a.html)]:
    f=Path(path)
    if not f.is_file(): errors.append(f'{kind}文件不存在');continue
    text=f.read_text(encoding='utf-8');texts[kind]=text
    if not text.strip():errors.append(f'{kind}文件为空')
h=texts.get('html','')
if h:
    if not re.search(r'<html\b',h,re.I) or not re.search(r'</html>',h,re.I):errors.append('HTML结构不完整')
    if re.search(r'\{\{[^{}]+\}\}|__[A-Z][A-Z0-9_]*__',h):errors.append('存在未替换槽位')
    if 'viewport' not in h:errors.append('缺少移动端viewport声明')
print(json.dumps({'errors':errors,'scope':'仅文件和占位检查；内容一致性、语义与视觉需另查'},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))

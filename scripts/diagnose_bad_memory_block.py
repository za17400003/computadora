import os
import sys
import site

paths = set(sys.path + site.getsitepackages())
found = 0
for p in paths:
    if not p or not os.path.isdir(p):
        continue
    for root, dirs, files in os.walk(p):
        for f in files:
            if f.endswith(('.py', '.pyc', '.txt', '.md', '.json', '.ini', '.cfg', '.yaml', '.yml')):
                full = os.path.join(root, f)
                try:
                    with open(full, 'r', encoding='utf-8', errors='ignore') as fh:
                        if 'Bad Memory Block' in fh.read():
                            print(full)
                            found += 1
                except Exception:
                    continue
print('DONE', found)

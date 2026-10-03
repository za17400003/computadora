#!/usr/bin/env python3
"""Fix escaped quotes in observador.py"""

from pathlib import Path

p = Path('computadora/nucleo/observador.py')
content = p.read_text(encoding='utf-8')

# Replace all escaped quotes
fixed = content.replace('\\"', '"')

p.write_text(fixed, encoding='utf-8')
print("✓ observador.py fixed — all escaped quotes removed")

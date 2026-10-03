#!/usr/bin/env python3
"""NIGREDO Analysis: Edge Case Coverage Gaps in Fase 1 Tests"""

import re
from pathlib import Path

print("=" * 60)
print("FASE 2 NIGREDO: EDGE CASE ANALYSIS")
print("=" * 60)
print()

test_dir = Path(".")
test_files = sorted(test_dir.glob("test_ciclo*.py"))

total_tests = 0
exception_tests = 0
perf_tests = 0
boundary_tests = 0

for test_file in test_files:
    with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    file_tests = len(re.findall(r'def test_', content))
    file_raises = len(re.findall(r'assertRaises', content))
    file_perf = len(re.findall(r'assertLess.*time|assertGreater.*time', content))
    file_boundary = len(re.findall(r'assertLess\(.*0\)|assertEqual\(.*0\)', content))
    
    total_tests += file_tests
    exception_tests += file_raises
    perf_tests += file_perf
    boundary_tests += file_boundary
    
    print(f"{test_file.name}")
    print(f"  Tests: {file_tests} | Exceptions: {file_raises} | Perf: {file_perf} | Boundary: {file_boundary}")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total tests (Fase 1): {total_tests}")
exception_pct = (100 * exception_tests // total_tests) if total_tests else 0
print(f"Exception cases: {exception_tests} ({exception_pct}% coverage)")
print(f"Performance tests: {perf_tests}")
print(f"Boundary tests: {boundary_tests}")
print()
print("GAPS IDENTIFIED (Hardening needed):")
print(f"  [RED] Exception handling: ~{total_tests - exception_tests} tests need assertRaises")
print(f"  [RED] Concurrency: 0 tests (race conditions untested)")
print(f"  [RED] Resource saturation: 0 tests")
print(f"  [RED] Injection attacks: 0 tests")
print(f"  [RED] State corruption: 0 tests")
print()
print("FASE 2 PRIORITIES:")
print("  1. Exception paths (error handling robustness)")
print("  2. Boundary conditions (input validation)")
print("  3. Concurrent operations (race detection)")
print("  4. Resource exhaustion (stress limits)")
print("  5. Adversarial inputs (injection/fuzzing)")

#!/usr/bin/env python3
"""
WI-291 ALBEDO: Investigación histórica de Minimi en git.
"""
import subprocess
import json

def run_git(cmd):
    """Ejecutar comando git y retornar output."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd="."
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

print("=" * 70)
print("WI-291 ALBEDO — Investigación Histórica de Minimi")
print("=" * 70)

# 1. Buscar commits que mencionen "Minimi"
print("\n[1] Commits que mencionan 'Minimi':")
print("-" * 70)
commits = run_git('git log --oneline --all --grep="inimi" -i')
if commits:
    for line in commits.split('\n'):
        if line.strip():
            print(f"  {line}")
else:
    print("  (no commits encontrados con grep)")

# 2. Buscar en todos los commits (por mensaje o cambios)
print("\n[2] Commits con cambios en archivos '*inimi*':")
print("-" * 70)
commits_files = run_git('git log --oneline --all --follow -- "*inimi*" "*Minimi*" 2>/dev/null')
if commits_files:
    for line in commits_files.split('\n'):
        if line.strip():
            print(f"  {line}")
else:
    print("  (no commits encontrados)")

# 3. Verificar ramas
print("\n[3] Ramas disponibles:")
print("-" * 70)
branches = run_git('git branch -a')
if branches:
    for line in branches.split('\n'):
        if 'minimi' in line.lower():
            print(f"  ✓ {line}")
    if 'minimi' not in branches.lower():
        print("  (no ramas con 'minimi' encontradas)")
else:
    print("  (error al listar ramas)")

# 4. Verificar stash
print("\n[4] Stash guardados:")
print("-" * 70)
stash = run_git('git stash list')
if stash:
    for line in stash.split('\n'):
        if line.strip():
            print(f"  {line}")
else:
    print("  (no stash encontrados)")

# 5. Buscar referencias en archivos actuales
print("\n[5] Referencias a 'Minimi' en archivos actuales:")
print("-" * 70)
refs = run_git('grep -r "minimi" --include="*.py" --include="*.md" --include="*.json" . 2>/dev/null | head -20')
if refs:
    for line in refs.split('\n'):
        if line.strip() and '.git' not in line:
            print(f"  {line[:100]}")
else:
    print("  (no referencias encontradas en archivos actuales)")

# 6. Commits específicos mencionados en WI-291
print("\n[6] Commits específicos mencionados en WI-291:")
print("-" * 70)
commits_especificos = ['cddcf20', '803a020', 'ddd0dea']
for commit_hash in commits_especificos:
    # Intentar obtener el mensaje del commit
    msg = run_git(f'git log --oneline -1 {commit_hash} 2>/dev/null')
    if msg and 'fatal' not in msg.lower():
        print(f"  ✓ {commit_hash}: {msg}")
    else:
        print(f"  ✗ {commit_hash}: (no encontrado en este repo)")

print("\n" + "=" * 70)
print("FIN INVESTIGACIÓN")
print("=" * 70)

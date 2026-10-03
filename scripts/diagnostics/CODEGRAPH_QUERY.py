#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CODEGRAPH QUERY CLI — Búsqueda rápida sin tool calls
Reemplaza grep_search, file_search, semantic_search para queries simples
"""

import json
from pathlib import Path
import sys
from typing import Optional
import argparse

class CodeGraphQuery:
    """Interface rápida para búsquedas sin tool calls"""
    
    def __init__(self, report_file: str = "codegraph_report.json"):
        self.report_file = Path(report_file)
        if not self.report_file.exists():
            print(f"ERROR: {report_file} no encontrado. Ejecuta CODEGRAPH_ANALYZER.py primero.")
            sys.exit(1)
        
        with open(report_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def find_class_definition(self, class_name: str) -> list:
        """Encontrar donde se define una clase"""
        results = []
        for module_path, info in self.data['modules'].items():
            if class_name in info.get('classes', []):
                results.append({
                    'file': module_path,
                    'class': class_name,
                    'line': info.get('class_lines', {}).get(class_name),
                })
        return results

    def find_function_definition(self, func_name: str) -> list:
        """Encontrar donde se define una función de módulo O un método de clase.

        FIX: antes solo buscaba en 'functions' (nivel de módulo) — la mayoría
        de búsquedas reales en este código son métodos, que viven en 'methods'
        (módulo -> {clase: {método: línea}}), agregado por CODEGRAPH_ANALYZER.
        """
        results = []
        for module_path, info in self.data['modules'].items():
            if func_name in info.get('functions', []):
                results.append({
                    'file': module_path,
                    'function': func_name,
                    'line': info.get('function_lines', {}).get(func_name),
                })
            for cls_name, cls_methods in info.get('methods', {}).items():
                if func_name in cls_methods:
                    results.append({
                        'file': module_path,
                        'function': func_name,
                        'class': cls_name,
                        'line': cls_methods[func_name],
                    })
        return results
    
    def find_module_imports(self, module_pattern: str) -> dict:
        """Qué importa un módulo y quién lo importa"""
        result = {
            'imports_from': [],
            'imported_by': []
        }
        
        # Encontrar el módulo
        module_info = None
        for path, info in self.data['modules'].items():
            if module_pattern.replace('.', '/') in path or path.endswith(module_pattern + '.py'):
                module_info = info
                result['module'] = path
                break
        
        if module_info:
            result['imports_from'] = module_info.get('imports', [])
            
            # Quién lo importa
            for path, info in self.data['modules'].items():
                if 'computadora' in info.get('imports', []):
                    result['imported_by'].append(path)
        
        return result
    
    def list_modules_with_pattern(self, pattern: str) -> list:
        """Listar módulos que contengan pattern"""
        return [
            path for path in self.data['modules'].keys()
            if pattern.lower() in path.lower()
        ]
    
    def print_class_location(self, class_name: str):
        """Formato amigable para imprimir ubicación de clase"""
        locations = self.find_class_definition(class_name)
        if not locations:
            print(f"[NOT FOUND] Clase '{class_name}' no encontrada")
            return

        print(f"[CLASS] {class_name}")
        for loc in locations:
            linea = f":{loc['line']}" if loc.get('line') else ""
            print(f"  -> {loc['file']}{linea}")

    def print_function_location(self, func_name: str):
        """Formato amigable para imprimir ubicación de función o método"""
        locations = self.find_function_definition(func_name)
        if not locations:
            print(f"[NOT FOUND] Función/método '{func_name}' no encontrado")
            return

        print(f"[FUNCTION] {func_name}")
        for loc in locations:
            linea = f":{loc['line']}" if loc.get('line') else ""
            if loc.get('class'):
                print(f"  -> {loc['file']}{linea}  (método de {loc['class']})")
            else:
                print(f"  -> {loc['file']}{linea}  (función de módulo)")
    
    def search_quick(self, query: str) -> Optional[str]:
        """Búsqueda rápida inteligente (clase, función, o módulo)"""
        # Intenta clase primero
        class_locs = self.find_class_definition(query)
        if class_locs:
            return f"CLASS: {class_locs[0]['file']}"
        
        # Intenta función
        func_locs = self.find_function_definition(query)
        if func_locs:
            return f"FUNCTION: {func_locs[0]['file']}"
        
        # Intenta módulo
        modules = self.list_modules_with_pattern(query)
        if modules:
            return f"MODULES: {len(modules)} encontrados - {modules[0]}"
        
        return None


def main():
    parser = argparse.ArgumentParser(description='CodeGraph Query CLI')
    parser.add_argument('--class', dest='search_class', help='Buscar clase')
    parser.add_argument('--function', dest='search_func', help='Buscar función')
    parser.add_argument('--module', dest='search_mod', help='Buscar módulo')
    parser.add_argument('--imports', dest='imports_of', help='Ver imports de módulo')
    
    args = parser.parse_args()
    
    query = CodeGraphQuery()
    
    if args.search_class:
        query.print_class_location(args.search_class)
    elif args.search_func:
        query.print_function_location(args.search_func)
    elif args.search_mod:
        mods = query.list_modules_with_pattern(args.search_mod)
        print(f"[MODULES] {len(mods)} encontrados:")
        for m in mods[:10]:
            print(f"  -> {m}")
    elif args.imports_of:
        imp = query.find_module_imports(args.imports_of)
        print(f"[MODULE] {imp.get('module', args.imports_of)}")
        print(f"  Imports: {', '.join(imp['imports_from'][:5])}")
        print(f"  Imported by: {len(imp['imported_by'])} modules")
    else:
        print("Use: python CODEGRAPH_QUERY.py --class NAME | --function NAME | --module PATTERN")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Sin argumentos, mostrar ejemplos
        query = CodeGraphQuery()
        print("[CODEGRAPH QUERY] Quick Search Tool")
        print("Ejemplos:")
        query.print_class_location("OrbeGolem")
        print()
        query.print_function_location("_animar")
        print()
        mods = query.list_modules_with_pattern("escucha")
        print(f"[MODULES] Escucha (encontrados {len(mods)}):")
        for m in mods:
            print(f"  -> {m}")
    else:
        main()

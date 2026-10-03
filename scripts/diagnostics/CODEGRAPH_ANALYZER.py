#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CODEGRAPH ANALYZER — Mapeo inteligente de estructura del Golem
Reemplaza múltiples tool calls con análisis AST + dependency graph
"""

import os
import sys
import json
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GolemCodeGraph:
    """Analiza estructura de código del proyecto Golem sin herramientas externas"""
    
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.modules = {}  # path -> AST info
        self.imports = defaultdict(set)  # quien_importa -> {qué_importa}
        self.classes = defaultdict(list)  # módulo -> [clases]
        self.class_lines = defaultdict(dict)  # módulo -> {clase: línea}
        self.functions = defaultdict(list)  # módulo -> [funciones de módulo]
        self.function_lines = defaultdict(dict)  # módulo -> {función: línea}
        # FIX: antes solo se indexaban funciones a nivel de módulo — la
        # mayoría de búsquedas reales en este código (muy orientado a
        # objetos) son MÉTODOS dentro de una clase, que _parse_file nunca
        # veía (solo recorría tree.body, no el cuerpo de cada ClassDef).
        # módulo -> {clase: {método: línea}}
        self.methods = defaultdict(dict)
        self.dependencies = defaultdict(set)  # módulo -> {módulos_que_depende}
        
    def scan_project(self, exclude_dirs=None):
        """Escanear todo el proyecto Python"""
        if exclude_dirs is None:
            exclude_dirs = {'.git', '__pycache__', '.venv', 'venv', 'env', 'node_modules', '_archive'}
        
        py_files = []
        for root, dirs, files in os.walk(self.root):
            # Filtrar directorios
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                if file.endswith('.py'):
                    py_files.append(Path(root) / file)
        
        logger.info(f"Escaneando {len(py_files)} archivos Python...")
        
        for py_file in py_files:
            try:
                rel_path = py_file.relative_to(self.root)
                self._parse_file(py_file, rel_path)
            except Exception as e:
                logger.debug(f"⚠️  Error parseando {py_file}: {e}")
    
    def _parse_file(self, file_path: Path, rel_path: Path):
        """Parsear un archivo Python con AST"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            file_key = str(rel_path).replace('\\', '/')
            
            # Extraer imports
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
            
            # Extraer clases, funciones de módulo, y métodos dentro de cada clase
            classes = []
            class_lines = {}
            functions = []
            function_lines = {}
            methods = {}
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    class_lines[node.name] = node.lineno
                    cls_methods = {}
                    for sub in node.body:
                        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            cls_methods[sub.name] = sub.lineno
                    if cls_methods:
                        methods[node.name] = cls_methods
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                    function_lines[node.name] = node.lineno

            self.imports[file_key] = imports
            self.classes[file_key] = classes
            self.class_lines[file_key] = class_lines
            self.functions[file_key] = functions
            self.function_lines[file_key] = function_lines
            self.methods[file_key] = methods
            
        except Exception as e:
            logger.debug(f"Error en {file_path}: {e}")
    
    def analyze_module_path(self, module_name: str) -> Dict:
        """Encontrar módulo y retornar información completa"""
        # Normalizar nombre
        module_name = module_name.replace('.', '/')
        
        results = {}
        for file_key, classes in self.classes.items():
            if module_name in file_key or file_key.startswith(module_name):
                results[file_key] = {
                    'classes': classes,
                    'functions': self.functions[file_key],
                    'imports': list(self.imports[file_key]),
                }
        
        return results
    
    def find_class(self, class_name: str) -> List[Tuple[str, str]]:
        """Encontrar dónde está definida una clase"""
        results = []
        for file_key, classes in self.classes.items():
            if class_name in classes:
                results.append((file_key, class_name))
        return results
    
    def find_function(self, func_name: str) -> List[Tuple[str, str]]:
        """Encontrar dónde está definida una función"""
        results = []
        for file_key, functions in self.functions.items():
            if func_name in functions:
                results.append((file_key, func_name))
        return results

    def find_method(self, method_name: str) -> List[Tuple[str, str, int]]:
        """Encontrar dónde está definido un método (dentro de alguna clase)"""
        results = []
        for file_key, methods_by_class in self.methods.items():
            for cls_name, methods in methods_by_class.items():
                if method_name in methods:
                    results.append((file_key, cls_name, methods[method_name]))
        return results
    
    def trace_imports(self, from_module: str) -> Dict:
        """Rastrear qué importa un módulo y quién lo importa"""
        from_module = from_module.replace('.', '/').replace('\\', '/')
        
        result = {
            'imports': set(),
            'imported_by': set()
        }
        
        # Qué importa este módulo
        for key, imports in self.imports.items():
            if from_module in key:
                result['imports'] = imports
                break
        
        # Quién lo importa
        for key, imports in self.imports.items():
            if from_module.split('/')[-1] in imports or from_module in imports:
                result['imported_by'].add(key)
        
        return {
            'imports': list(result['imports']),
            'imported_by': list(result['imported_by']),
        }
    
    def export_report(self, output_file: str = "codegraph_report.json"):
        """Exportar reporte completo"""
        total_methods = sum(
            len(cls_methods)
            for methods_by_class in self.methods.values()
            for cls_methods in methods_by_class.values()
        )
        report = {
            'total_files': len(self.imports),
            'total_classes': sum(len(c) for c in self.classes.values()),
            'total_functions': sum(len(f) for f in self.functions.values()),
            'total_methods': total_methods,
            'modules': {}
        }

        for file_key in self.imports.keys():
            report['modules'][file_key] = {
                'classes': self.classes.get(file_key, []),
                'class_lines': self.class_lines.get(file_key, {}),
                'functions': self.functions.get(file_key, []),
                'function_lines': self.function_lines.get(file_key, {}),
                'methods': self.methods.get(file_key, {}),
                'imports': list(self.imports[file_key]),
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Reporte exportado a {output_file}")
        return report
    
    def print_summary(self):
        """Imprimir resumen"""
        print("\n" + "=" * 80)
        print("CODEGRAPH ANALYSIS SUMMARY")
        print("=" * 80)
        total_methods = sum(
            len(cls_methods)
            for methods_by_class in self.methods.values()
            for cls_methods in methods_by_class.values()
        )
        print(f"Total archivos: {len(self.imports)}")
        print(f"Total clases: {sum(len(c) for c in self.classes.values())}")
        print(f"Total funciones de modulo: {sum(len(f) for f in self.functions.values())}")
        print(f"Total metodos: {total_methods}")
        print(f"\nTop 10 modulos mas importados:")
        
        import_counts = defaultdict(int)
        for imports in self.imports.values():
            for imp in imports:
                import_counts[imp] += 1
        
        for imp, count in sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {imp}: {count} veces")
        
        print(f"\nModulos mas complejos (mas clases):")
        for file_key, classes in sorted(self.classes.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            if len(classes) > 0:
                print(f"  - {file_key}: {len(classes)} clases")
        
        print("=" * 80 + "\n")


if __name__ == "__main__":
    graph = GolemCodeGraph()
    graph.scan_project()
    
    # Búsquedas comunes
    print("\n[BUSQUEDAS DE EJEMPLO]\n")
    
    # Encontrar clase HiloEscucha
    print("[1] Donde esta HiloEscucha?")
    escucha_locations = graph.find_class("HiloEscucha")
    for file, cls in escucha_locations:
        print(f"   -> {file}")
    
    # Encontrar clase OrbeGolem
    print("\n[2] Donde esta OrbeGolem?")
    orbe_locations = graph.find_class("OrbeGolem")
    for file, cls in orbe_locations:
        print(f"   -> {file}")
    
    # Qué importa escucha.py
    print("\n[3] Que importa escucha.py?")
    trace = graph.trace_imports("voz/escucha")
    print(f"   Importa: {', '.join(trace['imports'][:5])}")
    print(f"   Importado por: {len(trace['imported_by'])} modulos")
    
    # Exportar reporte
    graph.export_report()
    graph.print_summary()

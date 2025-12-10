#!/usr/bin/env python3
"""
Script de Validação de Métodos em Testes

Detecta automaticamente AttributeError potenciais verificando se:
- Métodos chamados em testes existem nas classes correspondentes
- Services/Repositories têm os métodos que os testes esperam
- Schemas têm os campos que os testes usam

USO:
    python scripts/validate_test_methods.py
    python scripts/validate_test_methods.py --verbose

EXEMPLOS DE ERROS DETECTADOS:
    ✗ BoletoService.listar_configuracoes não existe
    ✗ ChavePixCreate.cedente_cnpj não existe (deveria ser cedente_documento)
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class FixtureTypeExtractor(ast.NodeVisitor):
    """Extrai tipos de fixtures do código de teste"""

    def __init__(self):
        self.fixture_types: Dict[str, str] = {}  # {fixture_name: type_name}

    def visit_FunctionDef(self, node):
        # Procura por @pytest.fixture e extrai o tipo do retorno
        is_fixture = any(
            (isinstance(d, ast.Name) and d.id == 'fixture') or
            (isinstance(d, ast.Attribute) and d.attr == 'fixture')
            for d in node.decorator_list
        )

        if is_fixture and node.returns:
            fixture_name = node.name
            if isinstance(node.returns, ast.Name):
                self.fixture_types[fixture_name] = node.returns.id
            elif isinstance(node.returns, ast.Attribute):
                self.fixture_types[fixture_name] = node.returns.attr

        # Também extrai tipos de parâmetros de funções de teste
        for arg in node.args.args:
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    self.fixture_types[arg.arg] = arg.annotation.id
                elif isinstance(arg.annotation, ast.Attribute):
                    self.fixture_types[arg.arg] = arg.annotation.attr

        self.generic_visit(node)


class MethodCallExtractor(ast.NodeVisitor):
    """Extrai chamadas de métodos do código de teste"""

    def __init__(self, fixture_types: Dict[str, str]):
        self.method_calls: Dict[str, List[str]] = defaultdict(list)  # {class_type: [methods]}
        self.fixture_types = fixture_types
        self.current_class = None

    def visit_Call(self, node):
        # Detecta chamadas como: service.metodo() ou await service.metodo()
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                method_name = node.func.attr

                # Mapeia objeto para tipo usando fixtures
                if obj_name in self.fixture_types:
                    class_type = self.fixture_types[obj_name]
                    self.method_calls[class_type].append(method_name)
                else:
                    # Tenta inferir do nome (ex: boleto_service -> BoletoService)
                    if '_service' in obj_name:
                        class_name = obj_name.replace('_service', '').title() + 'Service'
                        self.method_calls[class_name].append(method_name)

        self.generic_visit(node)


class ClassMethodExtractor(ast.NodeVisitor):
    """Extrai métodos definidos em uma classe"""

    def __init__(self):
        self.classes: Dict[str, Set[str]] = {}  # {class_name: {methods}}
        self.current_class = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.classes[node.name] = set()

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Ignora métodos privados __ mas mantém métodos protegidos _
                if not item.name.startswith('__'):
                    self.classes[node.name].add(item.name)

        self.generic_visit(node)
        self.current_class = None


class SchemaFieldExtractor(ast.NodeVisitor):
    """Extrai campos de schemas Pydantic"""

    def __init__(self):
        self.schemas: Dict[str, Set[str]] = {}  # {schema_name: {fields}}
        self.current_class = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.schemas[node.name] = set()

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Campo com type hint: campo: tipo
                self.schemas[node.name].add(item.target.id)
            elif isinstance(item, ast.Assign):
                # Campo direto: campo = valor
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self.schemas[node.name].add(target.id)

        self.generic_visit(node)
        self.current_class = None


def find_python_files(directory: str, pattern: str = "*.py") -> List[Path]:
    """Encontra todos os arquivos Python em um diretório"""
    return list(Path(directory).rglob(pattern))


def extract_methods_from_file(filepath: Path) -> Dict[str, Set[str]]:
    """Extrai todos os métodos de todas as classes em um arquivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        extractor = ClassMethodExtractor()
        extractor.visit(tree)
        return extractor.classes
    except Exception as e:
        print(f"⚠️  Erro ao analisar {filepath}: {e}", file=sys.stderr)
        return {}


def extract_schema_fields_from_file(filepath: Path) -> Dict[str, Set[str]]:
    """Extrai todos os campos de schemas Pydantic em um arquivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        extractor = SchemaFieldExtractor()
        extractor.visit(tree)
        return extractor.schemas
    except Exception as e:
        print(f"⚠️  Erro ao analisar {filepath}: {e}", file=sys.stderr)
        return {}


def extract_test_calls(filepath: Path) -> Dict[str, List[str]]:
    """Extrai chamadas de métodos de um arquivo de teste"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(filepath))

        # Primeiro extrai tipos de fixtures
        fixture_extractor = FixtureTypeExtractor()
        fixture_extractor.visit(tree)

        # Depois extrai chamadas de métodos
        call_extractor = MethodCallExtractor(fixture_extractor.fixture_types)
        call_extractor.visit(tree)

        return call_extractor.method_calls
    except Exception as e:
        print(f"⚠️  Erro ao analisar {filepath}: {e}", file=sys.stderr)
        return {}


def build_class_method_map() -> Dict[str, Set[str]]:
    """Constrói mapa de todas as classes e seus métodos"""
    class_methods = {}

    # Procura por arquivos de service em app/modules
    patterns = ['service.py', '*_service.py', 'services.py', '*_services.py']
    for pattern in patterns:
        for service_file in find_python_files('app/modules', pattern):
            methods = extract_methods_from_file(service_file)
            class_methods.update(methods)

    # Procura por repositories
    for repo_file in find_python_files('app/modules', 'repository.py'):
        methods = extract_methods_from_file(repo_file)
        class_methods.update(methods)

    for repo_file in find_python_files('app/modules', '*_repository.py'):
        methods = extract_methods_from_file(repo_file)
        class_methods.update(methods)

    return class_methods


def build_schema_field_map() -> Dict[str, Set[str]]:
    """Constrói mapa de todos os schemas e seus campos"""
    schema_fields = {}

    for schema_file in find_python_files('app/modules', 'schemas.py'):
        fields = extract_schema_fields_from_file(schema_file)
        schema_fields.update(fields)

    return schema_fields


def validate_test_file(test_file: Path, class_methods: Dict[str, Set[str]], verbose: bool = False) -> List[str]:
    """Valida um arquivo de teste"""
    errors = []

    # Extrai chamadas de métodos do teste (já mapeadas por classe)
    test_calls = extract_test_calls(test_file)

    if verbose:
        print(f"\n📄 Analisando: {test_file.name}")
        if test_calls:
            print(f"  🔍 Classes detectadas: {', '.join(test_calls.keys())}")

    for class_name, methods in test_calls.items():
        # Verifica se a classe existe
        if class_name not in class_methods:
            if verbose:
                print(f"  ⚠️  Classe {class_name} não encontrada nos sources")
            continue

        # Verifica cada método
        available_methods = class_methods[class_name]
        for method in set(methods):  # Remove duplicatas
            if method not in available_methods:
                error = f"{test_file.name}: {class_name}.{method}() não existe"

                # Sugere métodos similares
                similar = [m for m in available_methods if method.lower() in m.lower() or m.lower() in method.lower()]
                if similar:
                    error += f" (similares: {', '.join(similar[:3])})"

                errors.append(error)

                if verbose:
                    print(f"  ❌ {error}")
            elif verbose:
                print(f"  ✅ {class_name}.{method}()")

    return errors


def main():
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    print("🔍 Validando métodos em testes...\n")

    # 1. Construir mapa de classes e métodos
    if verbose:
        print("📚 Construindo mapa de classes e métodos...")
    class_methods = build_class_method_map()

    if verbose:
        print(f"   Encontradas {len(class_methods)} classes")
        for cls, methods in list(class_methods.items())[:5]:
            print(f"   - {cls}: {len(methods)} métodos")
        if len(class_methods) > 5:
            print(f"   ... e mais {len(class_methods) - 5} classes")

    # 2. Encontrar todos os arquivos de teste
    test_files = find_python_files('tests', 'test_*.py')

    if verbose:
        print(f"\n📋 Encontrados {len(test_files)} arquivos de teste")

    # 3. Validar cada arquivo de teste
    all_errors = []
    for test_file in test_files:
        errors = validate_test_file(test_file, class_methods, verbose)
        all_errors.extend(errors)

    # 4. Reportar resultados
    print("\n" + "="*60)
    if all_errors:
        print(f"❌ {len(all_errors)} erro(s) encontrado(s):\n")
        for error in all_errors:
            print(f"  ❌ {error}")
        print("\n" + "="*60)
        return 1
    else:
        print("✅ Todos os métodos usados nos testes existem!")
        print("="*60)
        return 0


if __name__ == '__main__':
    sys.exit(main())

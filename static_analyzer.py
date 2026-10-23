import ast
from typing import Dict, List, Any, Set


class StaticCodeAnalyzer(ast.NodeVisitor):
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.tree = ast.parse(source_code)
        
        self.defined_imports: Dict[str, int] = {}
        self.used_names: Set[str] = set()
        self.defined_functions: Dict[str, int] = {}
        self.called_functions: Set[str] = set()
        
        self.detected_dead_code: List[Dict[str, Any]] = []
        self.unreachable_nodes: List[Dict[str, Any]] = []
        self.cyclomatic_complexity: Dict[str, int] = {}

    def analyze(self) -> Dict[str, Any]:
        self.visit(self.tree)
        
        unused_imports = [
            {
                "name": name,
                "line": line,
                "fix": f"Remove unreferenced import statement for '{name}' at line {line}."
            }
            for name, line in self.defined_imports.items()
            if name not in self.used_names
        ]
        
        unused_functions = [
            {
                "name": name,
                "line": line,
                "fix": f"Remove uncalled function '{name}' or connect it to an active call site."
            }
            for name, line in self.defined_functions.items()
            if name not in self.called_functions and not name.startswith("__")
        ]

        code_smells = [
            {
                "target": fn_name,
                "complexity": comp,
                "fix": f"Refactor function '{fn_name}' using guard clauses or break logic into smaller sub-functions."
            }
            for fn_name, comp in self.cyclomatic_complexity.items()
            if comp > 4
        ]

        return {
            "detected_dead_code": self.detected_dead_code,
            "unused_imports": unused_imports,
            "redundant_imports": unused_imports,
            "unused_functions": unused_functions,
            "unreachable_blocks": self.unreachable_nodes,
            "complexity_metrics": self.cyclomatic_complexity,
            "code_smells": code_smells,
            "summary_advice": self._generate_summary(len(self.detected_dead_code), len(unused_imports), len(code_smells))
        }

    def _generate_summary(self, dead_count: int, import_count: int, smell_count: int) -> str:
        total = dead_count + import_count + smell_count
        if total == 0:
            return "Code passes AST static analysis cleanly! No duplicate functions, dead code, or unused imports found."
        return f"Identified {total} code quality issue(s): {dead_count} dead/unreachable/duplicate item(s), {import_count} unused import(s), and {smell_count} complex code smell(s)."

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.defined_imports[name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.defined_imports[name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # 1. Detect Duplicate Functions
        if node.name in self.defined_functions:
            first_line = self.defined_functions[node.name]
            self.detected_dead_code.append({
                "title": f"Duplicate Function Definition: '{node.name}'",
                "line": node.lineno,
                "snippet": f"def {node.name}(...)",
                "fix": f"Remove or rename this duplicate function. First defined on line {first_line}."
            })
        else:
            self.defined_functions[node.name] = node.lineno
        
        # 2. Cyclomatic Complexity
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
                
        self.cyclomatic_complexity[node.name] = complexity
        
        # 3. Unreachable Code Check
        has_returned = False
        for stmt in node.body:
            if has_returned:
                snippet = ast.unparse(stmt) if hasattr(ast, "unparse") else "Unreachable Statement"
                unreachable_item = {
                    "function": node.name,
                    "title": f"Unreachable Statement in '{node.name}'",
                    "line": stmt.lineno,
                    "snippet": snippet,
                    "code_snippet": snippet,
                    "fix": f"Delete statement on line {stmt.lineno} as execution returns prior to this line."
                }
                self.unreachable_nodes.append(unreachable_item)
                self.detected_dead_code.append(unreachable_item)
                break
            
            if isinstance(stmt, ast.If):
                if self._all_branches_return(stmt):
                    has_returned = True
            elif isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                has_returned = True
                
        self.generic_visit(node)

    def _all_branches_return(self, if_node: ast.If) -> bool:
        """Helper to verify if an if/elif/else chain returns on every execution path."""
        def body_returns(body):
            return any(isinstance(s, (ast.Return, ast.Raise)) for s in body)

        has_if_return = body_returns(if_node.body)
        has_else_return = False
        
        if if_node.orelse:
            if len(if_node.orelse) == 1 and isinstance(if_node.orelse[0], ast.If):
                has_else_return = self._all_branches_return(if_node.orelse[0])
            else:
                has_else_return = body_returns(if_node.orelse)
                
        return has_if_return and has_else_return

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            self.called_functions.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.called_functions.add(node.func.attr)
        self.generic_visit(node)


def analyze_python_code(code_string: str) -> Dict[str, Any]:
    try:
        analyzer = StaticCodeAnalyzer(code_string)
        return analyzer.analyze()
    except SyntaxError as e:
        return {
            "detected_dead_code": [{
                "title": "Syntax Error",
                "line": e.lineno or 1,
                "snippet": e.text.strip() if e.text else "Syntax Error",
                "fix": f"Fix syntax error: {e.msg}"
            }],
            "unused_imports": [],
            "redundant_imports": [],
            "unused_functions": [],
            "unreachable_blocks": [],
            "complexity_metrics": {},
            "code_smells": [],
            "summary_advice": "Fix syntax error to complete analysis."
        }


# Alias for main.py backwards compatibility
run_static_analysis = analyze_python_code
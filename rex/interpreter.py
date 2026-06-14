
import re
import json
import sys

try:
    import requests
except ImportError:
    requests = None

class RexError(RuntimeError):
    pass

class RexInterpreter:
    def __init__(self):
        self.vars = {}
        self.version = "0.1.0"

    def eval_expr(self, expr: str):
        expr = expr.strip()
        # string literal
        if len(expr) >= 2 and ((expr[0] == '"' and expr[-1] == '"') or (expr[0] == "'" and expr[-1] == "'")):
            return expr[1:-1]
        # number
        try:
            if re.fullmatch(r'-?\d+\.\d+', expr):
                return float(expr)
            if re.fullmatch(r'-?\d+', expr):
                return int(expr)
        except:
            pass
        # rex.get("url")
        m = re.match(r'rex\.get\((.+)\)$', expr)
        if m:
            if requests is None:
                raise RexError("rex.get needs 'requests'. Install with: pip install requests")
            url_expr = m.group(1).strip()
            url = self.eval_expr(url_expr)
            if not isinstance(url, str):
                raise RexError(f"rex.get expects a string url, got {type(url).__name__}")
            try:
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                raise RexError(f"fetch failed for {url}: {e}")
        # rex.post(url, data) - v0.1.1
        m = re.match(r'rex\.post\((.+),\s*(.+)\)$', expr)
        if m:
            if requests is None:
                raise RexError("rex.post needs 'requests'. Install with: pip install requests")
            url = self.eval_expr(m.group(1).strip())
            data_expr = m.group(2).strip()
            data = self.eval_expr(data_expr)
            try:
                r = requests.post(url, json=data, timeout=15)
                r.raise_for_status()
                try:
                    return r.json()
                except:
                    return r.text
            except Exception as e:
                raise RexError(f"post failed for {url}: {e}")
        # property access obj.prop
        if '.' in expr and not expr.startswith('rex.'):
            parts = expr.split('.', 1)
            base, prop = parts[0].strip(), parts[1].strip()
            if base in self.vars:
                obj = self.vars[base]
                if isinstance(obj, dict):
                    return obj.get(prop)
        # variable
        if expr in self.vars:
            return self.vars[expr]
        # bare true/false/null
        if expr == "true": return True
        if expr == "false": return False
        if expr == "null": return None
        raise RexError(f"cannot evaluate: {expr}")

    def run_source(self, source: str, filename="<input>"):
        self.vars = {}
        lines = source.splitlines()
        output = []
        for i, raw in enumerate(lines, start=1):
            line = raw.split('#', 1)[0].strip()
            if not line:
                continue
            try:
                # rex.show(...)
                m = re.match(r'rex\.show\((.*)\)$', line)
                if m:
                    val = self.eval_expr(m.group(1))
                    if isinstance(val, (dict, list)):
                        out = json.dumps(val, indent=2)
                    else:
                        out = str(val)
                    output.append(out)
                    print(out)
                    continue
                # rex.let name = expr
                m = re.match(r'rex\.let\s+([A-Za-z_]\w*)\s*=\s*(.+)$', line)
                if m:
                    name, expr = m.groups()
                    self.vars[name] = self.eval_expr(expr)
                    continue
                # rex.return
                if re.match(r'rex\.return$', line):
                    break
                raise RexError(f"unknown statement: {line}")
            except RexError as e:
                raise RexError(f"{filename}:{i}: {e}") from None
        return output

    def run_file(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            return self.run_source(f.read(), filename=path)

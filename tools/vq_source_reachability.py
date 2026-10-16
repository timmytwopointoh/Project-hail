#!/usr/bin/env python3
"""Conservative, read-only VQ Python source reference inventory.

This tool intentionally NEVER labels modules dead or deletes anything. It
measures references visible in one checked-out commit only; other branches,
reflection, plugins, Android Java and user apps may still consume any module.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import re

WORKFLOW_PY = re.compile(r"(?<![\w/])veilforge/([A-Za-z0-9_./-]+\.py)\b")
SHA = re.compile(r"[0-9a-f]{40}\Z")
DYNAMIC_CALLS = {"__import__", "import_module", "run_module", "run_path"}


def _safe_python_files(root: Path):
    base = root / "veilforge"
    if not base.is_dir() or base.is_symlink():
        return [], ["veilforge/ directory missing or symbolic link"]
    files, problems = [], []
    for path in sorted(base.rglob("*.py")):
        if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
            problems.append("unsafe symbolic Python path: " + path.relative_to(root).as_posix())
        elif path.is_file():
            files.append(path)
    return files, problems


def _module_name(base: Path, path: Path):
    parts = list(path.relative_to(base).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _normalize_module(name: str, known: set[str]):
    if name.startswith("veilforge."):
        name = name[len("veilforge."):]
    if name in known:
        return name
    return None


def _from_base(current: str, node: ast.ImportFrom):
    if not node.level:
        return node.module or ""
    package = current.split(".")[:-1]
    if node.level > len(package) + 1:
        return ""
    prefix = package[: len(package) - (node.level - 1)]
    if node.module:
        prefix.extend(node.module.split("."))
    return ".".join(prefix)


def _references(tree: ast.AST, current: str, known: set[str]):
    edges, uncertain = set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = _normalize_module(alias.name, known)
                if target:
                    edges.add(target)
        elif isinstance(node, ast.ImportFrom):
            base = _from_base(current, node)
            if base:
                target = _normalize_module(base, known)
                if target:
                    edges.add(target)
                for alias in node.names:
                    if alias.name != "*":
                        child = _normalize_module(base + "." + alias.name, known)
                        if child:
                            edges.add(child)
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
            if name not in DYNAMIC_CALLS:
                continue
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                target = _normalize_module(node.args[0].value, known)
                if target:
                    edges.add(target)
                elif name == "run_path" and node.args[0].value.startswith("veilforge/"):
                    target = _normalize_module(node.args[0].value[len("veilforge/"):].removesuffix(".py").replace("/", "."), known)
                    if target:
                        edges.add(target)
            else:
                uncertain.append({"module": current, "line": node.lineno, "reason": "nonliteral dynamic module load"})
    return edges, uncertain


def audit(root: Path, source_sha: str | None = None):
    root = Path(root).resolve()
    base = root / "veilforge"
    files, problems = _safe_python_files(root)
    if source_sha is not None and not SHA.fullmatch(source_sha):
        problems.append("source SHA must be exactly 40 lowercase hexadecimal characters")
    source_by_module = {}
    for path in files:
        module = _module_name(base, path)
        if module:
            source_by_module[module] = path
    known = set(source_by_module)
    edges, uncertain = defaultdict(set), []
    source_hashes = {}
    for module, path in sorted(source_by_module.items()):
        relative = path.relative_to(root).as_posix()
        try:
            data = path.read_bytes()
            tree = ast.parse(data.decode("utf-8"), filename=relative)
        except (SyntaxError, UnicodeDecodeError, OSError) as exc:
            problems.append(f"cannot parse {relative}: {exc}")
            continue
        source_hashes[module] = hashlib.sha256(data).hexdigest()
        imported, dynamic = _references(tree, module, known)
        edges[module].update(imported)
        uncertain.extend(dynamic)
    workflow_root = root / ".github" / "workflows"
    workflow_roots = defaultdict(set)
    if workflow_root.is_dir() and not workflow_root.is_symlink():
        for path in sorted(workflow_root.glob("*.yml")) + sorted(workflow_root.glob("*.yaml")):
            if path.is_symlink():
                problems.append("unsafe workflow symlink: " + path.relative_to(root).as_posix())
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                problems.append(f"cannot read workflow {path.name}: {exc}")
                continue
            for match in WORKFLOW_PY.finditer(text):
                module = match.group(1).removesuffix(".py").replace("/", ".")
                if module in known:
                    workflow_roots[module].add(path.name)
    else:
        problems.append(".github/workflows/ missing or symbolic link")
    test_roots = {m for m in known if m.startswith("tests.test_")}
    roots = set(workflow_roots) | test_roots
    visited = set(roots)
    queue = deque(sorted(roots))
    while queue:
        current = queue.popleft()
        for target in sorted(edges[current] - visited):
            visited.add(target)
            queue.append(target)
    production = sorted(m for m in known if not m.startswith("tests."))
    candidates = [m for m in production if m not in visited]
    report = {
        "schema_version": 1,
        "source_sha": source_sha,
        "scope": "single checkout; Python AST and workflow literal references only",
        "source_file_count": len(files),
        "workflow_root_count": len(workflow_roots),
        "test_root_count": len(test_roots),
        "referenced_production_modules": sorted(set(production) & visited),
        "review_candidates_not_proven_unused": candidates,
        "dynamic_load_uncertainty": sorted(uncertain, key=lambda x: (x["module"], x["line"])),
        "workflow_entrypoints": {m: sorted(v) for m, v in sorted(workflow_roots.items())},
        "module_imports": {m: sorted(edges[m]) for m in sorted(known)},
        "module_sha256": dict(sorted(source_hashes.items())),
        "problems": problems,
        "static_audit_passed": not problems,
        "modules_deleted": False,
        "safe_to_delete_candidates": False,
        "game_or_other_branch_coverage": False,
        "release_approved": False,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha")
    args = parser.parse_args()
    report = audit(args.root, args.source_sha)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("VQ_SOURCE_REACHABILITY", "sources", report["source_file_count"],
          "review-only candidates", len(report["review_candidates_not_proven_unused"]),
          "passed", report["static_audit_passed"])
    if not report["static_audit_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

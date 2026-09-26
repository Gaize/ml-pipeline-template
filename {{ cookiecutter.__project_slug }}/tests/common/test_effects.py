"""Guards that aftereffects sit only where KissML will run them."""

import ast
from pathlib import Path

import pipeline

COMMON = Path(pipeline.__file__).parent / "common"

DECORATED = {"step_decorator", "step", "subpipeline"}


def _decorator_names(node: ast.FunctionDef) -> set[str]:
    names = set()
    for dec in node.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute):
            names.add(target.attr)
    return names


def _returns_annotated(node: ast.FunctionDef) -> bool:
    returns = node.returns
    if returns is None:
        return False
    return "Annotated" in ast.unparse(returns)


def test_annotated_effects_only_appear_on_steps_and_subpipelines():
    """An effect on a plain function is inert: it type-checks and never runs."""
    offenders = []
    for path in COMMON.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if _returns_annotated(node) and not (_decorator_names(node) & DECORATED):
                offenders.append(f"{path.name}:{node.name}")
    assert not offenders, f"Aftereffects on undecorated functions: {offenders}"

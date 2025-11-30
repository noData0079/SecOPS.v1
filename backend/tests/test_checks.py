# backend/tests/test_checks.py

from __future__ import annotations

import inspect

import pytest

from src.core.checks.base import BaseCheck
from src.core.checks import github_deps, github_security, k8s_misconfig, ci_hardening


@pytest.mark.parametrize(
    "cls_name, module",
    [
        ("GitHubDepsCheck", github_deps),
        ("GitHubSecurityCheck", github_security),
        ("K8sMisconfigCheck", k8s_misconfig),
        ("CIHardeningCheck", ci_hardening),
    ],
)
def test_check_classes_exist_and_subclass_base(cls_name, module) -> None:
    """
    Basic structural test:

    - The expected check class exists in its module
    - It is a subclass of BaseCheck (so it fits the check framework)
    """
    assert hasattr(module, cls_name), f"{cls_name} not found in {module.__name__}"
    cls = getattr(module, cls_name)

    assert inspect.isclass(cls), f"{cls_name} in {module.__name__} is not a class"
    assert issubclass(cls, BaseCheck), f"{cls_name} must subclass BaseCheck"


def test_base_check_has_required_interface() -> None:
    """
    Ensure BaseCheck defines the core interface methods we expect.

    This keeps the rest of the system safe if someone refactors BaseCheck.
    """
    # At minimum we expect:
    #   - name (or KIND)
    #   - async run(...) method
    attrs = dir(BaseCheck)

    # Allow either attribute or property for name/kind
    has_name_like = any(a in attrs for a in ("name", "NAME", "kind", "KIND"))
    assert has_name_like, "BaseCheck should expose a name/kind attribute"

    # Ensure there is an async run method (or similar)
    run_fn = getattr(BaseCheck, "run", None)
    assert run_fn is not None, "BaseCheck must define a 'run' method"

    # Even if BaseCheck.run is abstract, it should be a coroutine function
    is_async = inspect.iscoroutinefunction(run_fn) or inspect.iscoroutinefunction(
        getattr(BaseCheck, "run", None)
    )
    assert is_async, "BaseCheck.run should be an async coroutine function"

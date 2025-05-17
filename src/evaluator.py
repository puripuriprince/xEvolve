from __future__ import annotations

import time
from types import ModuleType
from typing import Any, Callable, Dict

__all__ = ["make_eval", "identity_evaluator"]


# helpers -------------------------------------------------------------------

def _exec(code: str) -> ModuleType:  # noqa: F401 – used for side-effect module
    ns: dict[str, Any] = {}
    exec(code, ns)
    return ns  # type: ignore[arg-type]


# Public API ----------------------------------------------------------------

def make_eval(test_fn: Callable[[ModuleType], bool]) -> Callable[[str], Dict[str, Any]]:
    """Return an evaluator that runs `test_fn` on the executed module."""

    def _evaluate(src: str) -> Dict[str, Any]:
        start = time.time()
        result = {
            "is_successful": False,
            "time_taken": 0.0,
            "debug_logs": "",
        }
        try:
            mod = _exec(src)
            outcome = test_fn(mod)
            if isinstance(outcome, tuple):
                success, output_val = outcome
            else:
                success, output_val = outcome, None

            result["is_successful"] = success
            result["output_value"] = output_val
            result["debug_logs"] = "Tests executed."
        except Exception as e:  # pragma: no cover
            result["debug_logs"] = f"Evaluation error: {e}"
        finally:
            result["time_taken"] = time.time() - start
        return result

    return _evaluate


# trivial evaluator that always passes
identity_evaluator = make_eval(lambda _m: True) 
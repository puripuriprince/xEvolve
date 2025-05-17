#!/usr/bin/env python
"""CLI entry-point for the iterative code-evolution framework.

This script simply wires together the default building blocks provided in the
package: Fibonacci prompt builder, Fibonacci evaluator, and the evolution loop.
Change the imports to experiment with your own prompt builders or evaluators.
"""
from __future__ import annotations

import argparse
import os
import textwrap

from src.evolution import run as evolution_run
from src.prompt import basic_diff_prompt
from src.evaluator import make_eval
from functools import lru_cache


DEFAULT_INITIAL_PROGRAM = """
# Initial seed program – intentionally naive.
def fib(n):
    pass  # LLM will improve this
"""
@lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

def _parse_cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Iterative code evolution harness")
    p.add_argument("--generations", type=int, default=5, help="Number of evolution rounds")
    p.add_argument("--parallelism", type=int, default=1, help="Children generated per generation")
    p.add_argument("--debug", action="store_true", help="Print debug information")
    return p.parse_args()


def main() -> None:
    args = _parse_cli()

    if os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY") == "YOUR_GEMINI_API_KEY":
        print("Warning: GEMINI_API_KEY is not set. LLM calls will be simulated.")

    # custom evaluator for Fibonacci
    def _fib_test(mod):
        N = 30
        try:
            out = mod.get("fib", lambda n: None)(N)
            return (out == fib(N), out)
        except Exception:
            return (False, None)

    fib_evaluator = make_eval(_fib_test)

    evolution_run(
        task_description="Improve the implementation so that fib(n) returns the nth Fibonacci number.",
        prompt_builder=basic_diff_prompt,
        evaluator=fib_evaluator,
        initial_program=textwrap.dedent(DEFAULT_INITIAL_PROGRAM).lstrip(),
        generations=args.generations,
        parallelism=args.parallelism,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
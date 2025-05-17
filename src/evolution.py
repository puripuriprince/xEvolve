from __future__ import annotations

from typing import Callable, List

from . import database as db
from . import diff as diff_util
from .llm import generate

from concurrent.futures import ThreadPoolExecutor, as_completed

import textwrap

PromptBuilder = Callable[[str, str, list[str] | None], str]
Evaluator = Callable[[str], dict]

__all__ = ["run"]


def run(
    *,
    task_description: str,
    prompt_builder: PromptBuilder,
    evaluator: Evaluator,
    initial_program: str,
    generations: int = 5,
    parallelism: int = 1,
    debug: bool = False,
) -> None:
    """Iteratively evolve `initial_program` for `generations` rounds."""

    db.initialize()

    # Seed DB if necessary.
    if not db.load():
        db.add(initial_program, evaluator(initial_program), idea="seed")

    for gen in range(1, generations + 1):
        print(f"\n=== Generation {gen} ===")
        parent, insp, p_uuid = db.sample()
        if not parent:
            print("Database empty – aborting.")
            break

        def _one_child(_):
            prompt = prompt_builder(task_description, parent, insp)
            if debug:
                print("\n--- Prompt ---\n", textwrap.shorten(prompt, 500, placeholder="..."))
            diff = generate(prompt)
            if not diff.strip():
                return None, "Empty diff"

            if debug:
                print("\n--- Diff ---\n", diff)

            # show search/replace if debug
            if debug:
                try:
                    search, replace = diff_util.split(diff)
                    print("--- SEARCH block ---\n", search)
                    print("--- REPLACE block ---\n", replace)
                except Exception:
                    pass

            child_code = diff_util.apply(parent, diff)
            if child_code == parent:
                return None, "No change"

            res = evaluator(child_code)
            db.add(child_code, res, parent_uuid=p_uuid, idea="llm change")
            return (child_code, res), None

        # run sequentially or in threads
        tasks: List = []
        if parallelism > 1:
            with ThreadPoolExecutor(max_workers=parallelism) as exe:
                futures = [exe.submit(_one_child, i) for i in range(parallelism)]
                tasks = [f.result() for f in futures]
        else:
            tasks = [_one_child(0)]

        for outcome, err in tasks:
            if err:
                print("Skipped child:", err)
                continue
            child_code, res = outcome  # type: ignore[misc]
            print("Program:\n", child_code.strip())
            summary = (
                f"success={res.get('is_successful')}  "
                f"time={res.get('time_taken', 0):.4f}s  "
                f"output={res.get('output_value', '')}"
            )
            print("Result:", summary)

        print(f"=== End Generation {gen} ===") 
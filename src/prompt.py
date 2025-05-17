from __future__ import annotations

from typing import List

__all__ = ["basic_diff_prompt"]


def basic_diff_prompt(task_description: str, parent_code: str, inspirations: List[str] | None = None) -> str:
    """Return a simple prompt asking the model to produce a diff.

    Parameters
    ----------
    task_description:
        Plain-text description of the programming task / spec.
    parent_code:
        Current implementation to improve.
    inspirations:
        Optional previous attempts that may inspire the model.
    """
    p = [
        "You are an expert programmer tasked with iteratively improving code.",
        task_description.strip(),
        "",  # spacer
    ]

    if inspirations:
        p.append("--- Prior programs (inspirations) ---")
        for i, code in enumerate(inspirations, 1):
            p.append(f"Inspiration {i}:\n```python\n{code}\n```\n")
    else:
        p.append("--- No inspirations available ---\n")

    p.extend(
        [
            "--- Current program (to be modified) ---",
            f"```python\n{parent_code}\n```\n",
            "--- Task ---",
            "Suggest ONE modification as a unified diff:",
            "<<<<<<< SEARCH",
            "# original snippet",
            "=======",
            "# replacement snippet",
            ">>>>>>> REPLACE\n",
            "Respond with the diff ONLY – no extra commentary or code fences.",
        ]
    )

    return "\n".join(p) 
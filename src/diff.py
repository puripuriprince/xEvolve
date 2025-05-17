from __future__ import annotations

__all__ = ["apply", "split"]


def apply(parent_code: str, diff: str) -> str:
    """Return new code by applying `diff` to `parent_code`.

    Diff format expected:
        <<<<<<< SEARCH
        ...
        =======
        ...
        >>>>>>> REPLACE
    """
    # 1. Preferred lightweight SEARCH/REPLACE format
    if "<<<<<<< SEARCH" in diff and "=======" in diff and ">>>>>>> REPLACE" in diff:
        try:
            search, replace = split(diff)
            if search in parent_code:
                return parent_code.replace(search, replace, 1)
            # common quick-fix
            if search.strip() == "pass" and "pass" in parent_code:
                return parent_code.replace("pass", replace, 1)
        except Exception:
            pass  # fall through to unified-diff handler

    # 2. Attempt to apply a minimal unified diff patch (--- / +++ lines)
    if "---" in diff and "+++" in diff:
        # drop code fences if present
        diff_body = []
        for line in diff.splitlines():
            if line.startswith("```"):
                continue
            diff_body.append(line)

        removed: list[str] = []
        added: list[str] = []
        for l in diff_body:
            if l.startswith("---") or l.startswith("+++") or l.startswith("@@"):
                continue  # header / hunk info
            if l.startswith("-") and not l.startswith("- -"):
                removed.append(l[1:])
            elif l.startswith("+") and not l.startswith("+ +"):
                added.append(l[1:])

        if removed:
            old_block = "\n".join(removed).rstrip()
            new_block = "\n".join(added).rstrip()
            if old_block in parent_code:
                return parent_code.replace(old_block, new_block, 1)

    return parent_code


# Public split for debug use
def split(diff: str) -> tuple[str, str]:
    before, after = diff.split("=======", 1)
    search = before.replace("<<<<<<< SEARCH", "").lstrip("\n").rstrip()
    replace = after.replace(">>>>>>> REPLACE", "").lstrip("\n").rstrip()
    return search, replace

# Preserve backward compat
_split = split 
#!/usr/bin/env python3
"""Deterministic safety/quality gate for self-hosted AI code proposals.

A model's JSON and replacement text are always untrusted. This gate is
independent of provider, CI permissions and the model's claimed confidence.
It does NOT sandbox Java by itself: only approved trusted runner code should
compile or execute any candidate. Keep code workers unprivileged.
"""
import re

MAX_EDITS = 3
MAX_REPLACEMENT_CHARS = 5000
MAX_TOTAL_INSERTED = 10000
MAX_RISKS = 8

# Java IEEE-754: NaN == anything and NaN != comparison to NaN do NOT
# provide a reliable finite-value test. Reject erroneous model additions
# early and give a precise, actionable correction to the next AI attempt.
BAD_NAN_COMPARISON = re.compile(
    r"(?:\\b(?:Float|Double)\\s*\\.\\s*NaN\\s*(?:==|!=)|"
    r"(?:==|!=)\\s*(?:Float|Double)\\s*\\.\\s*NaN\\b)"
)

# Remove Java whitespace and comments while preserving string/char literals.
# This is intentionally conservative: the guard may reject an unusual
# meaningful whitespace edit, but it must never accept cosmetic edits as
# evidence of an improved game behavior.
def semantic_fingerprint(source):
    """Compare Java tokens roughly, ignoring whitespace and comments only.

    String and character literal contents (including escaped quotes and
    comment markers inside them) are preserved byte-for-byte. Conservative:
    possible semantic changes can be rejected, never blessed as improvements.
    """
    kept = []
    index = 0
    length = len(source)
    while index < length:
        char = source[index]
        if char in ("'", '"'):
            quote = char
            kept.append(char)
            index += 1
            while index < length:
                char = source[index]
                kept.append(char)
                index += 1
                if ord(char) == 92 and index < length:
                    kept.append(source[index])
                    index += 1
                elif char == quote:
                    break
            continue
        if source.startswith("//", index):
            end_line = source.find(chr(10), index + 2)
            index = end_line if end_line != -1 else length
            continue
        if source.startswith("/*", index):
            end_comment = source.find("*/", index + 2)
            index = end_comment + 2 if end_comment != -1 else length
            continue
        if not char.isspace():
            kept.append(char)
        index += 1
    return "".join(kept)

# Reject NEW text that grants the model an execution/network/filesystem bridge.
# Matching only additions avoids punishing legitimate pre-existing code.
FORBIDDEN_JAVA_ADDITIONS = re.compile(
    r"\b(?:Runtime\s*\.\s*getRuntime|ProcessBuilder|"
    r"System\s*\.\s*(?:exit|setProperty|getenv)|"
    r"java\s*\.\s*(?:net|lang\s*\.\s*reflect|nio\s*\.\s*file)|"
    r"Class\s*\.\s*forName|ClassLoader|"
    r"(?:Socket|ServerSocket|URLClassLoader)\s*\(|"
    r"Files\s*\.\s*(?:write|delete|move|copy)|"
    r"Thread\s*\(|"
    r"static\s*\{)|\.\s*exec\s*\(",
    re.IGNORECASE,
)


def validate_proposal(proposal, allowed, read_source):
    """Return fully checked {repo_relative_path: replacement_source}.

    allowed: iterable of exact path strings; read_source(path) returns UTF-8
    current source. No filesystem mutations until all edits have passed.
    """
    if not isinstance(proposal, dict):
        raise ValueError("AI response must be a JSON object")
    if set(proposal) != {"summary", "edits", "risks"}:
        raise ValueError("AI response violates the exact proposal schema")
    summary = proposal["summary"]
    risks = proposal["risks"]
    if not isinstance(summary, str) or not 3 <= len(summary.strip()) <= 1200:
        raise ValueError("AI proposal has no meaningful bounded summary")
    if not isinstance(risks, list) or len(risks) > MAX_RISKS or not all(
            isinstance(x, str) and len(x) <= 350 for x in risks):
        raise ValueError("AI proposal has malformed risks")
    edits = proposal["edits"]
    if not isinstance(edits, list) or not 1 <= len(edits) <= MAX_EDITS:
        raise ValueError("AI proposal must include 1-3 real edits")
    allowed = set(allowed)
    replacement = {}
    seen_matches = set()
    total_inserted = 0
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"path", "find", "replace"}:
            raise ValueError("AI proposal has malformed edit keys")
        path, old, new = edit["path"], edit["find"], edit["replace"]
        if not isinstance(path, str) or path not in allowed:
            raise ValueError("AI proposal attempted to edit a file outside its role")
        if not isinstance(old, str) or not isinstance(new, str):
            raise ValueError("AI proposal edit must use literal source text")
        if (path, old) in seen_matches:
            raise ValueError("AI proposal repeated an exact match in the same source file")
        seen_matches.add((path, old))
        if (not old or old == new or len(old) > MAX_REPLACEMENT_CHARS
                or len(new) > MAX_REPLACEMENT_CHARS):
            raise ValueError("AI proposal contains a no-op or oversized edit")
        if semantic_fingerprint(old) == semantic_fingerprint(new):
            raise ValueError("AI proposal contains only formatting or comments")
        # New content can contain old content; remove the old occurrence once
        # to inspect genuinely added fragments for dangerous new capabilities.
        additions = new.replace(old, "", 1)
        if BAD_NAN_COMPARISON.search(additions):
            raise ValueError(
                "Invalid Java NaN comparison: == or != Float.NaN never "
                "detects NaN. Use Float.isNaN(x) instead.")
        if FORBIDDEN_JAVA_ADDITIONS.search(additions):
            raise ValueError("AI proposal introduces prohibited Java capabilities")
        if re.search(r"(?:==|!=)\\s*(?:(?:Float|Double)\\s*\\.\\s*NaN)\\b|"
                     r"(?:Float|Double)\\s*\\.\\s*NaN\\s*(?:==|!=)", additions):
            raise ValueError(
                "Java NaN comparisons using == or != never detect NaN; "
                "use Float.isNaN(x) or Double.isNaN(x) instead")
        total_inserted += len(new)
        if total_inserted > MAX_TOTAL_INSERTED:
            raise ValueError("AI proposal exceeds total change budget")
        current = replacement.get(path)
        if current is None:
            current = read_source(path)
        if current.count(old) != 1:
            raise ValueError("AI edit must match one exact existing source substring")
        replacement[path] = current.replace(old, new, 1)
    if not any(semantic_fingerprint(replacement[p]) !=
               semantic_fingerprint(read_source(p)) for p in replacement):
        raise ValueError("AI proposal has no functional Java token change")
    return replacement

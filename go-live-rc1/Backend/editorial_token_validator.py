"""
SCIP editorial_token_validator.py - Wave C structural guarantee

This is the single point that makes a hallucinated figure impossible to surface
in Narratives editorial. The constrained LLM is only ever given numbers as
pre-tokenized strings it must echo. After the model responds, this validator
extracts every numeric/percentage/multiple token from the output and asserts
each one already existed in the verified fact set. Any token that is not in the
allowed set causes the editorial to be REJECTED and replaced by a deterministic
phrase built from the verified facts.

Design notes
  - The check is deterministic and runs post-LLM. It does not trust the prompt.
  - Source identifiers (R18, S05_SM2, M032) are NOT treated as numbers: a digit
    immediately preceded by a letter or digit is ignored, so 'R18' never counts
    as the number 18. Standalone numbers (years, amounts, percentages) DO count
    and therefore must be present in the fact set to be allowed.
  - Normalisation strips thousands separators and lowercases magnitude/unit
    suffixes so 'AED 1.650B' and '1.650 b' compare equal, but rounding is NOT
    tolerated ('70%' != '70.0%') - per the rule that the model must not round.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Set, Tuple

# A number core not preceded by a letter or digit, with an optional unit/suffix.
# Longer suffixes (bn, mn) are listed before single letters so they win.
_NUM_RE = re.compile(
    r"(?<![A-Za-z0-9])(\d[\d,]*(?:\.\d+)?)\s*(%|×|x|X|bn|mn|B|M|K|b|m|k)?"
)


def _normalize(num: str, unit: str) -> str:
    n = num.replace(",", "")
    u = (unit or "").lower()
    if u in ("×", "x"):
        u = "x"
    return f"{n}{u}"


def extract_number_tokens(text: str) -> Set[str]:
    """Return the set of normalised number tokens that appear as real values."""
    out: Set[str] = set()
    for m in _NUM_RE.finditer(text or ""):
        out.add(_normalize(m.group(1), m.group(2)))
    return out


def allowed_tokens_from_values(value_tokens: Iterable[str]) -> Set[str]:
    """The whitelist: every number that appears inside a verified value_token."""
    allowed: Set[str] = set()
    for v in value_tokens:
        allowed |= extract_number_tokens(v)
    return allowed


def validate_editorial(text: str, value_tokens: Iterable[str]) -> Tuple[bool, List[str]]:
    """Returns (is_valid, offending_tokens). Valid iff every number token in the
    output exists in the whitelist derived from the verified value_tokens."""
    allowed = allowed_tokens_from_values(value_tokens)
    found = extract_number_tokens(text)
    offending = sorted(found - allowed)
    return (len(offending) == 0, offending)

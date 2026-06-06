"""Garbage-time tagging for possessions."""

from __future__ import annotations


def is_garbage_time(period: int, abs_margin: int, *, is_playoff: bool = True) -> bool:
  """Return True when a possession should be excluded per pass2_design_spec §2.3."""
  if period == 4 and abs_margin >= 20:
    return True
  if not is_playoff and period == 3 and abs_margin >= 30:
    return True
  return False

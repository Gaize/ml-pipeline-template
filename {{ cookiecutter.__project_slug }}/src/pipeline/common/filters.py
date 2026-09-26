"""Row filtering that records what each rule dropped.

A step that drops rows returns the survivors and this record, so an aftereffect
can report per-rule survival on every run without the step logging anything.
"""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class FilterStep:
    """One filtering rule and its effect on the frame."""

    name: str
    rows_in: int
    rows_out: int

    @property
    def dropped(self) -> int:
        """Number of rows the rule removed."""
        return self.rows_in - self.rows_out

    @property
    def survival(self) -> float:
        """Fraction of incoming rows the rule kept, or 1.0 when nothing came in."""
        return self.rows_out / self.rows_in if self.rows_in else 1.0


@dataclass
class FilterChain:
    """An ordered record of the rules applied to a frame."""

    steps: list[FilterStep] = field(default_factory=list)

    def record(self, name: str, rows_in: int, rows_out: int) -> None:
        """Append one rule's result to the chain."""
        self.steps.append(FilterStep(name=name, rows_in=rows_in, rows_out=rows_out))

    def apply(self, df: pd.DataFrame, name: str, mask: pd.Series) -> pd.DataFrame:
        """Return the rows of `df` where `mask` holds, recording the drop under `name`."""
        out = df[mask]
        self.record(name, len(df), len(out))
        return out

    def to_frame(self) -> pd.DataFrame:
        """Return the chain as one row per rule."""
        return pd.DataFrame(
            [
                {
                    "filter": s.name,
                    "rows_in": s.rows_in,
                    "rows_out": s.rows_out,
                    "dropped": s.dropped,
                    "survival": s.survival,
                }
                for s in self.steps
            ]
        )

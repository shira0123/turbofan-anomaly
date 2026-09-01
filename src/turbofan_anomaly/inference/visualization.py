"""Deterministic, dependency-free SVG timeline export."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd


DEMO_LABEL = "synthetic_interface_demonstration_not_research_evidence"


def render_timeline_svg(timeline: pd.DataFrame, destination: Path, *, label: str = DEMO_LABEL) -> None:
    """Write a small static SVG; callers must label non-research demonstrations."""
    required = {"end_cycle", "calibrated_score", "smoothed_score", "threshold", "alert"}
    if missing := required - set(timeline.columns):
        raise ValueError(f"Timeline lacks SVG columns: {sorted(missing)}")
    width, height, margin = 900, 360, 45
    values = pd.concat([timeline["calibrated_score"], timeline["smoothed_score"], timeline["threshold"]]).astype(float)
    lower, upper = float(values.min()), float(values.max())
    span = upper - lower or 1.0
    count = max(len(timeline) - 1, 1)
    def point(index: int, value: float) -> str:
        x = margin + index * (width - 2 * margin) / count
        y = height - margin - (value - lower) * (height - 2 * margin) / span
        return f"{x:.3f},{y:.3f}"
    def poly(column: str) -> str:
        return " ".join(point(index, float(value)) for index, value in enumerate(timeline[column]))
    alerts = "".join(f'<circle cx="{point(index, float(row.smoothed_score)).split(",")[0]}" cy="{point(index, float(row.smoothed_score)).split(",")[1]}" r="4" fill="#d62728"/>' for index, row in enumerate(timeline.itertuples(index=False)) if bool(row.alert))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/><text x="{margin}" y="22" font-size="12">{escape(label)}</text><line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="black"/><polyline fill="none" stroke="#1f77b4" points="{poly('calibrated_score')}"/><polyline fill="none" stroke="#2ca02c" points="{poly('smoothed_score')}"/><polyline fill="none" stroke="#ff7f0e" points="{poly('threshold')}"/>{alerts}</svg>'''
    Path(destination).write_text(svg, encoding="utf-8", newline="\n")

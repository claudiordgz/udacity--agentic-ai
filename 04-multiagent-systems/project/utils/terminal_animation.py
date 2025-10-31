"""Lightweight terminal animations for demonstrating agent workflows."""

from __future__ import annotations

import itertools
import sys
import time
from typing import Iterable, List


FRAMES = ["-", "\\", "|", "/"]


def _spin_line(label: str, *, iterations: int = 6, delay: float = 0.05) -> None:
    for _, frame in zip(range(iterations), itertools.cycle(FRAMES)):
        sys.stdout.write(f"\r[{frame}] {label}")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(f"\r[✓] {label}\n")
    sys.stdout.flush()


def render_workflow_animation(steps: Iterable[str], *, delay: float = 0.05) -> None:
    """Animate a deterministic view of how internal agents process a request.

    Args:
        steps: Sequence of text labels to animate one after the other.
        delay: Sleep delay (seconds) between spinner frames.
    """

    step_list: List[str] = list(steps)
    if not step_list:
        return
    for message in step_list:
        _spin_line(message, delay=delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def render_negotiation_animation(message: str, *, delay: float = 0.06) -> None:
    """Show a quick animation when the customer agent negotiates."""

    for frame in FRAMES:
        sys.stdout.write(f"\r[{frame}] {message}")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(f"\r[<>] {message}\n")
    sys.stdout.flush()


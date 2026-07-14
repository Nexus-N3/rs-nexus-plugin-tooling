"""Interactive prompt helpers for system-test mode."""

from __future__ import annotations

import sys
from contextlib import contextmanager

try:
    import termios
except ImportError:  # pragma: no cover
    termios = None


class WizardCancelled(RuntimeError):
    """Raised when the operator cancels the interactive flow."""


@contextmanager
def suppress_ctrl_c_echo():
    if termios is None or not sys.stdin.isatty():
        yield
        return
    try:
        fd = sys.stdin.fileno()
        original = termios.tcgetattr(fd)
    except (termios.error, ValueError):
        yield
        return
    if not hasattr(termios, "ECHOCTL"):
        yield
        return
    updated = original[:]
    updated[3] &= ~termios.ECHOCTL
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, updated)
        yield
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, original)
        except termios.error:
            pass


def prompt_text(prompt: str) -> str:
    try:
        with suppress_ctrl_c_echo():
            return input(prompt)
    except KeyboardInterrupt as exc:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise WizardCancelled("System test cancelled by operator.") from exc


def prompt_choice(prompt: str, options: list[str]) -> int:
    for index, option in enumerate(options, start=1):
        print(f"  {index}. {option}")
    while True:
        raw = prompt_text(prompt).strip().lower()
        if raw in {"q", "quit", "exit", "cancel"}:
            raise WizardCancelled("System test cancelled by operator.")
        try:
            value = int(raw)
        except ValueError:
            print("Enter a valid number.")
            continue
        if 1 <= value <= len(options):
            return value - 1
        print("Choice out of range.")


def prompt_bool(prompt: str, *, default: bool = False) -> bool:
    suffix = " [Y/n] " if default else " [y/N] "
    raw = prompt_text(prompt + suffix).strip().lower()
    if raw in {"q", "quit", "exit", "cancel"}:
        raise WizardCancelled("System test cancelled by operator.")
    if not raw:
        return default
    return raw in {"y", "yes"}


def prompt_int(prompt: str, *, minimum: int, maximum: int) -> int:
    while True:
        raw = prompt_text(prompt).strip().lower()
        if raw in {"q", "quit", "exit", "cancel"}:
            raise WizardCancelled("System test cancelled by operator.")
        try:
            value = int(raw)
        except ValueError:
            print("Enter a valid integer.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"Enter a value between {minimum} and {maximum}.")

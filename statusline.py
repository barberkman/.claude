#!/usr/bin/env python3
"""Claude Code status line: model | dir | git | effort | 5h remaining."""
import json
import os
import subprocess
import sys

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
SEP = f"{DIM} | {RESET}"


def git_segment(cwd: str) -> str:
    try:
        subprocess.check_output(
            ["git", "-C", cwd, "rev-parse", "--git-dir"],
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""

    try:
        branch = subprocess.check_output(
            ["git", "-C", cwd, "symbolic-ref", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        try:
            branch = subprocess.check_output(
                ["git", "-C", cwd, "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except subprocess.CalledProcessError:
            return ""

    if not branch:
        return ""

    dirty = subprocess.run(
        ["git", "-C", cwd, "status", "--porcelain"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    mark = f"{YELLOW}*{RESET}" if dirty else ""
    return f"{GREEN}{branch}{RESET}{mark}"


def main() -> None:
    data = json.load(sys.stdin)

    model = data.get("model", {}).get("display_name") \
        or data.get("model", {}).get("id") \
        or "unknown"

    cwd = data.get("workspace", {}).get("current_dir") or data.get("cwd") or ""
    home = os.path.expanduser("~").replace("\\", "/")
    norm = cwd.replace("\\", "/")
    short_dir = norm.replace(home, "~", 1) if norm.startswith(home) else norm

    segments = []

    git = git_segment(norm)
    if git:
        segments.append(git)

    segments.append(f"{YELLOW}{short_dir}{RESET}")
    segments.append(f"{CYAN}{BOLD}{model}{RESET}")

    effort = data.get("effort", {}).get("level")
    thinking = data.get("thinking", {}).get("enabled")
    if effort:
        segments.append(f"{MAGENTA}effort:{effort}{RESET}")
    elif thinking:
        segments.append(f"{MAGENTA}thinking:on{RESET}")

    ctx_pct = data.get("context_window", {}).get("used_percentage")
    if ctx_pct is not None:
        segments.append(f"{CYAN}ctx: {round(float(ctx_pct))}%{RESET}")

    rate = data.get("rate_limits", {})
    five_h = rate.get("five_hour", {}).get("used_percentage")
    seven_d = rate.get("seven_day", {}).get("used_percentage")
    parts = []
    if five_h is not None:
        parts.append(f"{round(float(five_h))}%")
    if seven_d is not None:
        parts.append(f"{round(float(seven_d))}%")
    if parts:
        segments.append(f"{BLUE}usage: {' / '.join(parts)}{RESET}")

    print(SEP.join(segments))


if __name__ == "__main__":
    main()

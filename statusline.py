#!/usr/bin/env python3
"""Claude Code status line: model | dir | git | effort | 5h remaining."""
import json
import os
import subprocess
import sys
import time

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
SEP = f"{DIM} | {RESET}"

CACHE_PATH = os.path.expanduser("~/.claude/.statusline-cache.json")


def load_cache() -> dict:
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_cache(cache: dict) -> None:
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f)
    except OSError:
        pass


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

    max_len = 40
    if len(short_dir) > max_len:
        short_dir = "..." + short_dir[-(max_len - 3):]

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

    cache = load_cache()
    session_id = data.get("session_id")

    ctx_pct = data.get("context_window", {}).get("used_percentage")
    if ctx_pct is None and session_id:
        ctx_pct = cache.get("ctx", {}).get(session_id)
    if ctx_pct is not None:
        segments.append(f"{CYAN}ctx: {round(float(ctx_pct))}%{RESET}")

    rate = data.get("rate_limits", {})
    five_h_data = rate.get("five_hour", {})
    five_h = five_h_data.get("used_percentage")
    five_h_reset = five_h_data.get("resets_at")
    seven_d_data = rate.get("seven_day", {})
    seven_d = seven_d_data.get("used_percentage")
    seven_d_reset = seven_d_data.get("resets_at")
    if five_h is None:
        five_h = cache.get("five_h")
        five_h_reset = cache.get("five_h_reset")
    if seven_d is None:
        seven_d = cache.get("seven_d")
        seven_d_reset = cache.get("seven_d_reset")
    parts = []
    if five_h is not None:
        s = f"{round(float(five_h))}%"
        if five_h_reset:
            delta = int(five_h_reset) - int(time.time())
            if delta > 0:
                hrs, mins = divmod(delta // 60, 60)
                s += f" (resets in {hrs:02d}:{mins:02d})"
        parts.append(s)
    if seven_d is not None:
        s = f"{round(float(seven_d))}%"
        if seven_d_reset and int(seven_d_reset) > int(time.time()):
            s += f" (resets {time.strftime('%a %-I:%M %p', time.localtime(int(seven_d_reset)))})"
        parts.append(s)
    if parts:
        segments.append(f"{BLUE}usage: {' / '.join(parts)}{RESET}")

    print(SEP.join(segments))

    fresh = {}
    fresh_ctx = data.get("context_window", {}).get("used_percentage")
    if fresh_ctx is not None and session_id:
        ctx_cache = cache.get("ctx", {})
        ctx_cache[session_id] = fresh_ctx
        fresh["ctx"] = ctx_cache
    elif "ctx" in cache:
        fresh["ctx"] = cache["ctx"]
    fresh_five = rate.get("five_hour", {}).get("used_percentage")
    if fresh_five is not None:
        fresh["five_h"] = fresh_five
        fresh["five_h_reset"] = rate.get("five_hour", {}).get("resets_at")
    elif "five_h" in cache:
        fresh["five_h"] = cache["five_h"]
        fresh["five_h_reset"] = cache.get("five_h_reset")
    fresh_seven = rate.get("seven_day", {}).get("used_percentage")
    if fresh_seven is not None:
        fresh["seven_d"] = fresh_seven
        fresh["seven_d_reset"] = rate.get("seven_day", {}).get("resets_at")
    elif "seven_d" in cache:
        fresh["seven_d"] = cache["seven_d"]
        fresh["seven_d_reset"] = cache.get("seven_d_reset")
    save_cache(fresh)


if __name__ == "__main__":
    main()

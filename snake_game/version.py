"""App version and the GitHub release update check."""
import json


APP_VERSION = "1.4.1"
GITHUB_REPO = "SpaceSquare640/Snake_Game_Python"


def parse_version(text: str) -> tuple:
    """Parse a version/tag string like 'v1.2.0' into a comparable tuple."""
    parts = []
    for chunk in text.strip().lstrip("vV").split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def fetch_latest_version() -> str:
    """Return the latest release tag from GitHub (raises on failure)."""
    import urllib.request

    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Snake_Game_Python",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=6) as resp:
        data = json.load(resp)
    return data.get("tag_name", "")

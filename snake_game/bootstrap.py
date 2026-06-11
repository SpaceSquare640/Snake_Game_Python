"""Dependency-free environment bootstrap (runs before Pygame is imported)."""
import importlib.util
import subprocess
import sys


def _run(cmd: list[str]) -> bool:
    """Run a subprocess command, returning ``True`` on success."""
    try:
        subprocess.check_call(cmd)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        print(f"  ! command failed: {' '.join(cmd)}\n    {exc}")
        return False


def _pip(*args: str) -> bool:
    return _run([sys.executable, "-m", "pip", *args])


def _pygame_package_name() -> str:
    """Pick the right Pygame distribution for the running interpreter.

    Mainline ``pygame`` can lag behind brand-new Python releases (it may not
    publish wheels yet). ``pygame-ce`` is a drop-in replacement that imports as
    ``pygame`` and ships wheels faster, so prefer it on very new interpreters.
    """
    if sys.version_info >= (3, 13):
        return "pygame-ce"
    return "pygame>=2.1"


def bootstrap() -> None:
    """Ensure a supported Python and an importable, up-to-date Pygame."""
    # A frozen (PyInstaller) build already bundles Pygame; never run pip there.
    if getattr(sys, "frozen", False):
        return
    print("Snake bootstrap: checking environment ...")

    # 1) Python version check (and a best-effort winget update on Windows).
    if sys.version_info < (3, 8):
        print(f"  Python {sys.version.split()[0]} is too old; 3.8+ is required.")
        if sys.platform.startswith("win"):
            print("  Attempting to update Python via winget ...")
            _run(["winget", "install", "-e", "--id", "Python.Python.3.12"])
        print("  Please re-run the game with Python 3.8 or newer.")
        sys.exit(1)

    # 2) Is Pygame importable? If not, install it.
    pkg = _pygame_package_name()
    if importlib.util.find_spec("pygame") is None:
        print(f"  Pygame not found; installing '{pkg}' ...")
        if not _pip("install", pkg):
            print("  Could not install Pygame automatically. Install it with:")
            print(f"    {sys.executable} -m pip install {pkg}")
            sys.exit(1)

    # 3) Version check / auto-update of an already-installed Pygame.
    try:
        import pygame  # noqa: F401  (import to read the version)

        version = tuple(int(p) for p in pygame.ver.split(".")[:2])
        if version < (2, 1):
            print(f"  Pygame {pygame.ver} is outdated; updating ...")
            _pip("install", "--upgrade", pkg)
    except Exception:  # pragma: no cover - defensive
        # If anything about the version probe fails, a fresh install is safest.
        _pip("install", "--upgrade", pkg)

    print("Snake bootstrap: environment ready.\n")

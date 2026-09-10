"""Run once from the root of the Telegram-shop repository."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "tests"}


def find_translation_file() -> Path:
    matches = []
    for path in ROOT.rglob("*.py"):
        if path.name == Path(__file__).name:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "TRANSLATIONS" in text and "DEFAULT_LOCALE" in text and '"en"' in text:
            matches.append(path)

    if not matches:
        raise SystemExit("Translation file not found.")
    if len(matches) > 1:
        print("Multiple possible files found:")
        for item in matches:
            print(f" - {item.relative_to(ROOT)}")
        raise SystemExit("More than one translation file was found.")
    return matches[0]


def patch_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = r"^DEFAULT_LOCALE\s*=\s*[\"'][^\"']+[\"']"
    text, count = re.subn(
        pattern,
        'DEFAULT_LOCALE = "en"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count == 0:
        raise SystemExit("DEFAULT_LOCALE line was not found.")

    marker = "# FORCE_ENGLISH_FOR_ALL_USERS"
    override = '''

# FORCE_ENGLISH_FOR_ALL_USERS
# Existing users may still have locale="ru" saved in PostgreSQL.
TRANSLATIONS["ru"] = TRANSLATIONS["en"]
DEFAULT_LOCALE = "en"
'''
    if marker not in text:
        text = text.rstrip() + override

    compile(text, str(path), "exec")
    path.write_text(text, encoding="utf-8")
    print(f"Patched successfully: {path.relative_to(ROOT)}")
    print("Commit the changed translation file to GitHub, then redeploy Railway.")


if __name__ == "__main__":
    patch_file(find_translation_file())

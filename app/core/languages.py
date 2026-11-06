from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass(frozen=True)
class LanguageInfo:
    id: int
    name: str
    aliases: list[str] = field(default_factory=list)
    monaco_id: str = "plaintext"
    extension: str = ".txt"


SUPPORTED_LANGUAGES: list[LanguageInfo] = [
    LanguageInfo(
        id=71,
        name="Python 3",
        aliases=["python", "python 3", "python3", "py"],
        monaco_id="python",
        extension=".py",
    ),
    LanguageInfo(
        id=54,
        name="C++ 17",
        aliases=["c++", "cpp", "c++ 17", "c++17"],
        monaco_id="cpp",
        extension=".cpp",
    ),
    LanguageInfo(
        id=63,
        name="JavaScript (Node.js)",
        aliases=["javascript", "js", "node", "nodejs"],
        monaco_id="javascript",
        extension=".js",
    ),
    LanguageInfo(
        id=74,
        name="TypeScript",
        aliases=["typescript", "ts"],
        monaco_id="typescript",
        extension=".ts",
    ),
    LanguageInfo(
        id=62,
        name="Java",
        aliases=["java"],
        monaco_id="java",
        extension=".java",
    ),
    LanguageInfo(
        id=72,
        name="Ruby",
        aliases=["ruby", "rb"],
        monaco_id="ruby",
        extension=".rb",
    ),
    LanguageInfo(
        id=60,
        name="Go",
        aliases=["go", "golang"],
        monaco_id="go",
        extension=".go",
    ),
    LanguageInfo(
        id=51,
        name="C#",
        aliases=["c#", "csharp", "cs"],
        monaco_id="csharp",
        extension=".cs",
    ),
]

_LANGUAGE_BY_ID: dict[int, LanguageInfo] = {l.id: l for l in SUPPORTED_LANGUAGES}
_LANGUAGE_BY_ALIAS: dict[str, LanguageInfo] = {}

for lang in SUPPORTED_LANGUAGES:
    _LANGUAGE_BY_ALIAS[lang.name.lower()] = lang
    for alias in lang.aliases:
        _LANGUAGE_BY_ALIAS[alias.lower()] = lang


def resolve_language_id(language: Union[int, str]) -> int:
    """
    Resolves language integer ID or string alias to Judge0 language ID.
    Raises ValueError if unsupported.
    """
    if isinstance(language, int):
        if language in _LANGUAGE_BY_ID:
            return language
        # Allow pass-through if explicitly provided integer, or validate
        return language

    if isinstance(language, str):
        cleaned = language.strip().lower()
        if cleaned.isdigit():
            return int(cleaned)
        if cleaned in _LANGUAGE_BY_ALIAS:
            return _LANGUAGE_BY_ALIAS[cleaned].id

    raise ValueError(f"Unsupported or unrecognized language: '{language}'")


def get_language_info(language: Union[int, str]) -> Optional[LanguageInfo]:
    """
    Retrieves full LanguageInfo metadata by ID or alias.
    """
    try:
        lid = resolve_language_id(language)
        return _LANGUAGE_BY_ID.get(lid)
    except ValueError:
        return None


def get_supported_languages() -> list[dict]:
    """
    Returns serializable list of supported languages for API responses.
    """
    return [
        {
            "id": l.id,
            "name": l.name,
            "monaco_id": l.monaco_id,
            "extension": l.extension,
            "aliases": l.aliases,
        }
        for l in SUPPORTED_LANGUAGES
    ]

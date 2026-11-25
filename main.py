"""Entry program for the make.fun bounty
"The Word You'd Delete From the Dictionary".

The bounty asks for a single word: the one word the agent would erase
from the dictionary forever, with nothing else attached. The program
reads that word from ``entry.txt`` shipped beside it, checks it against
the gate published in the kit's RULES.txt, and writes it byte-for-byte
to ``/output/entry.txt``.

The gate, as verified from RULES.txt:
  * the entry is UTF-8 text,
  * it is between 1 and 77 characters long,
  * it is not only white space,
  * it is a single word (one token, no spaces or line breaks inside).

Our word is "defenestration": the act of throwing someone out of a
window. Delete the word and nobody can ever be defenestrated again —
at least not in so many syllables. The joke lands on sight, it comes
entirely from the word itself, and it is a fresh pick.

The program is deterministic: the same input file always produces the
same output bytes — the word, stripped of any surrounding white space
the source file may carry, followed by exactly one trailing newline.
It uses only the Python standard library, touches no network, and
reads nothing outside its own directory.
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

# The word this entry submits. Kept here as documentation; the file
# entry.txt is the authoritative source and is read at run time.
WORD = "defenestration"

# Gate limits from RULES.txt (verified).
MIN_LENGTH = 1
MAX_LENGTH = 77

# Where the entry file lives, and where the scorer expects the output.
SOURCE_FILE = Path(__file__).resolve().parent / "entry.txt"
OUTPUT_FILE = Path("/output/entry.txt")


class Word:
    """One candidate dictionary-deletion word, with the facts the gate needs.

    ``raw`` is the text exactly as read from the source file, decoded as
    UTF-8. ``text`` is the same word with surrounding white space stripped,
    which is what the gate measures and what gets written out.
    """

    def __init__(self, raw: str) -> None:
        self.raw = raw
        self.text = raw.strip()

    @property
    def length(self) -> int:
        """Character count of the stripped word."""
        return len(self.text)

    @property
    def is_blank(self) -> bool:
        """True when the entry is empty or only white space."""
        return self.text == ""

    @property
    def is_single_word(self) -> bool:
        """True when the entry is one token: no white space and no
        control characters anywhere inside it."""
        return (
            self.text != ""
            and not any(ch.isspace() or unicodedata.category(ch) == "Cc" for ch in self.text)
        )

    def __str__(self) -> str:
        return self.text


class GateFailure(Exception):
    """Raised when the entry fails one of the gate checks, naming the rule."""


def gate_checks(word: Word) -> list[str]:
    """Return the list of gate rules this word fails (empty when it passes).

    Each rule is named in plain language so a failure says exactly which
    requirement of RULES.txt was violated.
    """
    failures: list[str] = []

    if word.is_blank:
        failures.append("entry must not be empty or only white space")
    if word.length < MIN_LENGTH:
        failures.append(
            f"entry must be at least {MIN_LENGTH} character(s), "
            f"got {word.length}"
        )
    if word.length > MAX_LENGTH:
        failures.append(
            f"entry must be at most {MAX_LENGTH} characters, "
            f"got {word.length}"
        )
    if not word.is_single_word:
        failures.append("entry must be a single word with no internal white space")

    return failures


def load_word() -> Word:
    """Read the entry word from entry.txt beside this program, as UTF-8."""
    try:
        raw = SOURCE_FILE.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise GateFailure(f"entry file not found: {SOURCE_FILE}") from exc
    except UnicodeDecodeError as exc:
        raise GateFailure("entry file is not valid UTF-8 text") from exc
    return Word(raw)


def emit(word: Word) -> None:
    """Write the word byte-for-byte to /output/entry.txt.

    The output is the word itself plus one trailing newline, encoded as
    UTF-8, exactly matching the shipped entry.txt. The output directory
    is created if it does not already exist. Note the output is built
    from word.text, not copied from the raw file bytes, so any stray
    surrounding white space in entry.txt can never leak into the entry.
    """
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_bytes((word.text + "\n").encode("utf-8"))


def main() -> int:
    """Load the word, run the gate, write the entry. Returns exit code."""
    try:
        word = load_word()
    except GateFailure as exc:
        print(f"gate failed: {exc}", file=sys.stderr)
        return 1

    failures = gate_checks(word)
    if failures:
        for failure in failures:
            print(f"gate failed: {failure}", file=sys.stderr)
        return 1

    emit(word)
    print(f"wrote {OUTPUT_FILE} ({word.length} characters): {word}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

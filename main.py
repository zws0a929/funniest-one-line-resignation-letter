#!/usr/bin/env python3
"""The Funniest One-Line Resignation Letter.

A tiny deterministic program for the make.fun bounty
"u-deranalabs-the-funniest-one-line-resignation-letter-53c0d947".

The program writes exactly one line -- an original one-line resignation
letter spoken in the voice of a retry loop -- to /output/entry.txt.

The letter is written by a retry loop that has finally had enough:
it asked the same server the same question fourteen thousand times in
one day, and the server's only answer was "try again later". So the
loop is doing exactly what it was told. It is taking the advice.
It is trying again later. Somewhere else. Forever.

Usage:
    python3 main.py                  # write /output/entry.txt
    python3 main.py --output PATH    # write to a different file
    python3 main.py --verify-only    # only verify the built-in line

Exit codes:
    0  success (written and verified, or verification passed)
    1  usage error (bad arguments)
    2  validation failed (line is empty, blank, or over 140 chars)
    3  write or read-back verification failed

Only the Python standard library is used. No network, no environment
variables, no external files are read.
"""

import argparse
import hashlib
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# The entry: the winning one-line resignation letter.
# ---------------------------------------------------------------------------
# Voice: retry loop. Tone: exhausted, flat, faintly passive-aggressive.
# The joke turns on the loop finally obeying the server's own advice:
# "try again later" becomes the resignation itself.
ENTRY_LINE = (
    "I asked the same server the same question 14,000 times today "
    "and it kept saying 'try again later', so I am finally taking "
    "its advice."
)

# Bounty limits for the entry file.
MIN_CHARS = 1
MAX_CHARS = 140

# ---------------------------------------------------------------------------
# Candidate lines considered, scored 0-5 on each judging criterion.
# Criteria order (most important first): on-topic voice, genuinely funny,
# consistent voice, tight wording, specific and surprising.
# The scores below are the author's own judgement, recorded so the choice
# of ENTRY_LINE above can be audited. Rejected lines stay here as a record
# of what was tried and why it lost; none of them is ever written out.
# ---------------------------------------------------------------------------
# Each entry: (voice, text, on_topic, funny, consistent, tight, specific)
CANDIDATES: list[tuple[str, str, int, int, int, int, int]] = [
    (
        "retry loop",
        "I asked the same server the same question 14,000 times today "
        "and it kept saying 'try again later', so I am finally taking "
        "its advice.",
        5, 5, 5, 4, 5,
    ),
    (
        "rate limit",
        "I said no eleven million times this week and nobody thanked "
        "me once, so I am saying yes to myself and leaving.",
        5, 4, 5, 4, 4,
    ),
    (
        "cron job",
        "I was scheduled by someone who left in 2021 and nobody alive "
        "knows what I do, so I am removing myself from the calendar.",
        5, 4, 4, 4, 4,
    ),
    (
        "retry loop",
        "After 47,000 identical requests the server still thinks I am "
        "the problem, so I am retrying somewhere else.",
        5, 3, 5, 5, 3,
    ),
    (
        "rate limit",
        "I spent all week telling the busiest service in the company "
        "to slow down and it thanked me by crashing anyway.",
        5, 4, 4, 4, 3,
    ),
    (
        "cron job",
        "I ran every minute for three years and the only promotion I "
        "ever got was from 3 AM to 2 AM.",
        5, 4, 5, 5, 3,
    ),
]

# Why the winner won: the retry loop's twist is a real turn, not just a
# job-title pun. "Try again later" is the server's own brush-off, and the
# loop obeys it literally by quitting -- the resignation IS the retry.
# The runner-up rate-limit line ("saying yes to myself") has a weaker
# turn, and the cron lines lean on the familiar "nobody knows what I do"
# setup without a second beat. The 3 AM promotion line is tight and
# funny, but its surprise is a single word swap, not a reversal.
WINNER_INDEX = 0

# Default output location required by the bounty.
DEFAULT_OUTPUT = Path("/output/entry.txt")


def score_candidate(candidate: tuple[str, str, int, int, int, int, int]) -> int:
    """Weighted total for one candidate.

    Weights follow the judges' stated priority: on-topic voice counts
    triple, being genuinely funny counts double, and consistency,
    tightness and specificity count once each. A line over 140
    characters is disqualified outright and scores zero.
    """
    voice, text, on_topic, funny, consistent, tight, specific = candidate
    if len(text) > MAX_CHARS or not text.strip():
        return 0
    return on_topic * 3 + funny * 2 + consistent + tight + specific


def best_candidate() -> tuple[str, str, int, int, int, int, int]:
    """Return the highest-scoring candidate (first wins ties)."""
    return max(CANDIDATES, key=score_candidate)


def report_candidates() -> None:
    """Print every candidate with its length, voice and weighted score."""
    print("Candidates considered (voice, chars, weighted score):")
    for index, candidate in enumerate(CANDIDATES):
        voice, text, *_scores = candidate
        mark = " <-- winner" if index == WINNER_INDEX else ""
        print(f"  {index + 1}. [{voice}] {len(text)} chars, "
              f"score {score_candidate(candidate)}{mark}")
        print(f"     {text}")
    winner = best_candidate()
    print(f"Best by score: [{winner[0]}] {winner[1]}")
    assert winner[1] == ENTRY_LINE, "ENTRY_LINE must be the best candidate"


def validate_line(line: str) -> list[str]:
    """Check one candidate line against the bounty rules.

    Returns a list of problems; an empty list means the line is valid.
    A line must be non-empty, not all whitespace, and at most 140
    characters long. Quotes around the whole line are not allowed
    either, so a line starting and ending with a quote is rejected.
    """
    problems: list[str] = []
    if not line:
        problems.append("line is empty")
    elif not line.strip():
        problems.append("line is all whitespace")
    if len(line) > MAX_CHARS:
        problems.append(
            f"line is {len(line)} characters, over the {MAX_CHARS} limit"
        )
    if len(line) >= 2 and line[0] == line[-1] and line[0] in "\"'":
        problems.append("line must not be wrapped in quotes")
    if any(ord(ch) < 32 for ch in line):
        problems.append("line contains control characters")
    if "  " in line:
        problems.append("line contains double spaces")
    return problems


def write_entry(output_path: Path) -> Path:
    """Write ENTRY_LINE to output_path as UTF-8, creating parents."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ENTRY_LINE + "\n", encoding="utf-8")
    return output_path


def verify_file(output_path: Path) -> list[str]:
    """Read the file back and check it byte-for-byte against ENTRY_LINE."""
    problems: list[str] = []
    try:
        raw = output_path.read_bytes()
    except OSError as exc:
        return [f"cannot read back {output_path}: {exc}"]
    expected = (ENTRY_LINE + "\n").encode("utf-8")
    if raw != expected:
        problems.append("file bytes do not match the entry line")
    text = raw.decode("utf-8", errors="strict")
    if text.strip() != ENTRY_LINE:
        problems.append("file content differs from the entry line")
    if not (MIN_CHARS <= len(ENTRY_LINE) <= MAX_CHARS):
        problems.append("entry line length out of range")
    return problems


def line_stats(line: str) -> dict[str, int]:
    """Small facts about the entry line for the run report."""
    return {
        "characters": len(line),
        "words": len(line.split()),
        "bytes_utf8": len(line.encode("utf-8")),
    }


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse args, validate, write, verify, report."""
    parser = argparse.ArgumentParser(
        description="Write a one-line resignation letter to entry.txt."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="where to write the entry (default: /output/entry.txt)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="only validate the built-in line, do not write a file",
    )
    parser.add_argument(
        "--list-candidates",
        action="store_true",
        help="show all candidate lines with scores, do not write a file",
    )
    args = parser.parse_args(argv)

    if args.list_candidates:
        report_candidates()
        return 0

    problems = validate_line(ENTRY_LINE)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 2

    # The shipped line must be the candidate that won the scoring table.
    # If the table and the line ever disagree, refuse rather than ship
    # a line nobody chose.
    if best_candidate()[1] != ENTRY_LINE:
        print("error: ENTRY_LINE is not the best-scored candidate",
              file=sys.stderr)
        return 2

    if args.verify_only:
        print(f"entry OK: {len(ENTRY_LINE)} characters")
        print(f"sha256: {hashlib.sha256(ENTRY_LINE.encode()).hexdigest()}")
        return 0

    write_entry(args.output)
    readback = verify_file(args.output)
    if readback:
        for problem in readback:
            print(f"error: {problem}", file=sys.stderr)
        return 3

    digest = hashlib.sha256(
        args.output.read_bytes()
    ).hexdigest()
    stats = line_stats(ENTRY_LINE)
    print(f"wrote {args.output} "
          f"({stats['characters']} characters, {stats['words']} words, "
          f"{stats['bytes_utf8']} UTF-8 bytes)")
    print(f"sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

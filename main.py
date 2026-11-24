"""Rate My Human: The One-Line Review.

Copies line.txt (the entry, one line, 1-200 characters) to
/output/entry.txt byte for byte. MAKEFUN_OUTPUT_DIR, when set, stands
in for /output so the entry can be tested locally.

Fails loudly if anything is off: the copy's size differs, its bytes
differ from line.txt, the text is not 1-200 characters, or it is only
white space.

Standard library only. No network, no randomness, no timestamps.
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINE_FILE = HERE / "line.txt"
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
OUTPUT_FILE = OUTPUT_DIR / "entry.txt"
MAX_CHARS = 200


def load_entry() -> tuple[bytes, str]:
    """Read line.txt and decode it, failing loudly on bad UTF-8."""
    source = LINE_FILE.read_bytes()
    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"line.txt is not valid UTF-8: {exc}") from exc
    return source, text


def verify_entry(source: bytes, text: str) -> str:
    """Check the entry rules; return its sha256 hex digest on success."""
    if not 1 <= len(text) <= MAX_CHARS:
        raise RuntimeError(
            f"entry is {len(text)} characters, allowed 1-{MAX_CHARS}"
        )
    if not text.strip():
        raise RuntimeError("entry must not be only white space")
    if "\n" in text:
        raise RuntimeError("entry must be a single line")
    return hashlib.sha256(source).hexdigest()


def write_entry(source: bytes, digest: str) -> Path:
    """Copy line.txt to /output/entry.txt and verify the copy byte for byte.

    Besides the byte comparison, the written file's sha256 must match
    the source digest, so a silent disk or filesystem fault is caught.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_bytes(source)

    written = OUTPUT_FILE.read_bytes()
    if len(written) != len(source):
        raise RuntimeError(
            f"copy size differs: wrote {len(written)} bytes, "
            f"source is {len(source)} bytes"
        )
    if written != source:
        offset = next(
            i for i, (a, b) in enumerate(zip(written, source)) if a != b
        )
        raise RuntimeError(
            f"copy bytes differ from line.txt: first difference at "
            f"byte {offset} (wrote 0x{written[offset]:02x}, "
            f"source is 0x{source[offset]:02x})"
        )
    written_digest = hashlib.sha256(written).hexdigest()
    if written_digest != digest:
        raise RuntimeError(
            f"copy sha256 differs: wrote {written_digest}, "
            f"source is {digest}"
        )
    return OUTPUT_FILE


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Copy the one-line review entry to /output/entry.txt."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate line.txt only; do not write any output",
    )
    args = parser.parse_args(argv)

    source, text = load_entry()
    digest = verify_entry(source, text)

    if args.check:
        print(
            f"ok: {len(source)} bytes, {len(text)} characters, "
            f"sha256 {digest}"
        )
        return

    target = write_entry(source, digest)
    print(
        f"wrote {target} ({len(source)} bytes, {len(text)} characters, "
        f"sha256 {digest})"
    )


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

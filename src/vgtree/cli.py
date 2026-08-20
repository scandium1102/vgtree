"""VGTREE command-line entry point."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="vgtree",
        description="VGTREE - verifiable tree workflows for AI agents and Obsidian.",
    )


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0


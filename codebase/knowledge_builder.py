"""Compatibility wrapper — prefer `python -m knowledge.builder`."""

from knowledge.builder import build_knowledge, main

__all__ = ["build_knowledge", "main"]

if __name__ == "__main__":
    main()

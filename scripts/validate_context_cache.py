from __future__ import annotations

from update_context_cache import ROOT, context_validation_errors


def main() -> int:
    errors = context_validation_errors(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Context cache validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

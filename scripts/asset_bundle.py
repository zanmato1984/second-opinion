"""Read production assets from this trusted installation, never the target tree."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.trusted_assets import bundle


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(bundle(args.review_root), ensure_ascii=True))
    except (ValueError, OSError, UnicodeError) as error:
        print(f"Trusted assets unavailable ({type(error).__name__}); no fallback allowed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

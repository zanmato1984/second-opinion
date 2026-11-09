"""Export production review assets without repository metadata or test fixtures."""

import argparse
from pathlib import Path
import shutil

FILES = ("README.md", "SKILL.md", "taxonomy.md")
DIRECTORIES = ("agents", "experts", "processes", "policies", "fragments", "prompts", "schemas")


def install(source, destination, *, include_fixtures=False):
    source = Path(source)
    destination = Path(destination)
    # Never overwrite an existing installation or follow a destination symlink.
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Destination already exists: {destination}")
    destination.mkdir(parents=True)
    for name in FILES:
        shutil.copy2(source / name, destination / name)
    for name in DIRECTORIES:
        shutil.copytree(source / name, destination / name)
    if include_fixtures:
        shutil.copytree(source / "tests" / "fixtures", destination / "tests" / "fixtures")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    install(Path(__file__).resolve().parents[1], args.destination)


if __name__ == "__main__":
    main()

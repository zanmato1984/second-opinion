"""Export production review assets without repository metadata or test fixtures."""

import argparse
from pathlib import Path
import shutil

FILES = ("README.md", "SKILL.md", "taxonomy.md")
DIRECTORIES = ("agents", "experts", "processes", "policies", "fragments", "prompts", "schemas")
OPTIONAL_DIRECTORIES = ("docs", "runtime", "scripts")
SAMPLES = {"experts/foo", "processes/foo", "policies/foo.yaml", "fragments/foo.md"}


def install(source, destination, *, include_fixtures=False):
    source = Path(source)
    destination = Path(destination)
    # Never overwrite an existing installation or follow a destination symlink.
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Destination already exists: {destination}")
    if source.resolve() == destination.resolve() or source.resolve() in destination.resolve().parents:
        raise ValueError("Installation must be separate from the source tree")
    if source.is_symlink() or any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("Symlinked source assets are not supported")

    def production_only(directory, names):
        parent = Path(directory).relative_to(source)
        return [name for name in names if name == "__pycache__" or name.endswith(".pyc")
                or (parent / name).as_posix() in SAMPLES]

    destination.mkdir(parents=True)
    for name in FILES:
        shutil.copy2(source / name, destination / name)
    for name in (*DIRECTORIES, *OPTIONAL_DIRECTORIES):
        if name in OPTIONAL_DIRECTORIES and not (source / name).is_dir():
            continue
        shutil.copytree(source / name, destination / name,
                        ignore=production_only)
    if include_fixtures:
        shutil.copytree(source / "tests" / "fixtures", destination / "tests" / "fixtures")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    install(Path(__file__).resolve().parents[1], args.destination)


if __name__ == "__main__":
    main()

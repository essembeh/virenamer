import argparse
import os
import shutil
import subprocess
from argparse import ArgumentParser
from os.path import isdir
from pathlib import Path
from tempfile import NamedTemporaryFile

from pytput import Style

from virenamer import __title__, __version__


def main():
    parser = ArgumentParser(prog=__title__, description="File renamer")
    parser.add_argument(
        "--version",
        action="version",
        version="{0} version {1}".format(__title__, __version__),
    )
    parser.add_argument(
        "-e", "--editor", action="store", help="Editor used to edit file list"
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite if target file already exists",
    )
    parser.add_argument(
        "-d", "--delete", action="store_true", help="Delete file if line is empty"
    )
    parser.add_argument(
        "-n", "--dryrun", action="store_true", help="Dryrun mode, don't rename any file"
    )
    parser.add_argument(
        "files", nargs=argparse.ONE_OR_MORE, type=Path, help="files to rename"
    )
    args = parser.parse_args()

    input_files = []
    output_lines = []
    # Filter existing files from input and avoid doublons
    for f in args.files:
        if f.exists() and f not in input_files:
            input_files.append(f)
    # Edit the files with editor
    with NamedTemporaryFile() as tmp:
        with open(tmp.name, "w") as fp:
            for f in input_files:
                fp.write(str(f) + "\n")
        subprocess.check_call([args.editor or os.getenv("EDITOR", "vi"), tmp.name])
        with open(tmp.name, "r") as fp:
            output_lines = list(map(str.strip, fp))
    # Check that the line count is the same
    if len(input_files) != len(output_lines):
        print(Style.RED.apply("File count has changed, cannot rename any file"))
        return 1
    # Iterate the two lists
    for source, dest in zip(input_files, output_lines):
        if len(dest.strip()) == 0:
            if args.delete:
                # delete mode
                if args.dryrun:
                    print(
                        Style.PURPLE.apply(
                            "(dryrun) Delete '{source}'".format(source=source)
                        )
                    )
                else:
                    print(Style.GREEN.apply("Delete '{source}'".format(source=source)))
                    if source.is_dir():
                        shutil.rmtree(str(source))
                    else:
                        source.unlink()
            else:
                print(
                    Style.RED.apply(
                        "'{source}' won't be deleted, use --delete to enable file deletion".format(
                            source=source
                        ),
                    )
                )
        else:
            dest = Path(dest)
            if source != dest:
                if dest.exists() and not args.force:
                    print(
                        Style.RED.apply(
                            "'{dest}' already exists, skip renaming, use --force to overwrite'{source}'".format(
                                source=source, dest=dest
                            ),
                        )
                    )
                else:
                    if args.dryrun:
                        print(
                            Style.PURPLE.apply(
                                "(dryrun) Rename '{source}' --> '{dest}'".format(
                                    source=source, dest=dest
                                ),
                            )
                        )
                    else:
                        print(
                            Style.GREEN.apply(
                                "Rename '{source}' --> '{dest}'".format(
                                    source=source, dest=dest
                                ),
                            )
                        )
                        if not dest.parent.is_dir():
                            dest.parent.mkdir()
                        source.rename(dest)
    return 0


if __name__ == "__main__":
    exit(main())

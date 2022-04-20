"""
virenamer
"""
import subprocess
import sys
from argparse import ONE_OR_MORE, ArgumentParser
from os import getenv
from pathlib import Path
from shutil import rmtree
from tempfile import NamedTemporaryFile
from typing import List, Optional

from colorama import Fore as F

from . import __version__

DEFAULT_EDITOR = getenv("EDITOR", "vim")


def bulk_rename(
    sources: List[Path],
    destinations: List[Optional[Path]],
    delete: bool = False,
    dryrun: bool = False,
    force: bool = False,
):
    """
    function that renames the source files to destination files given the options
    """

    assert len(sources) == len(
        destinations
    ), "File count has changed, cannot rename any file"

    # iterate the two lists
    for source, dest in zip(sources, destinations):
        if dest is None:
            if not delete:
                # delete is not allowed
                print(
                    f"{F.RED}'{source}' won't be deleted, use --delete to enable file deletion{F.RESET}"
                )
            elif dryrun:
                # dryrun mode
                print(f"{F.MAGENTA}(dryrun) Delete '{source}'{F.RESET}")
            else:
                # delete the source
                print(f"{F.GREEN}Delete '{source}'{F.RESET}")
                if source.is_dir():
                    rmtree(source)
                else:
                    source.unlink()
        else:
            if source == dest:
                # same source/dest, skip
                pass
            elif dest.exists() and not force:
                # file already exists
                print(
                    f"{F.RED}'{dest}' already exists, skip renaming, use --force to overwrite'{source}'{F.RESET}"
                )
            elif dryrun:
                # dryrun mode
                print(f"{F.MAGENTA}(dryrun) Rename '{source}' --> '{dest}'{F.RESET}")
            else:
                # rename the file
                print(f"{F.GREEN}Rename '{source}' --> '{dest}'{F.RESET}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                source.rename(dest)


def run():
    """
    cli entrypoint
    """
    parser = ArgumentParser(description="File renamer")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-e",
        "--editor",
        default=DEFAULT_EDITOR,
        action="store",
        help=f"editor used to edit file list (default is {DEFAULT_EDITOR})",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="overwrite if target file already exists",
    )
    parser.add_argument(
        "-d", "--delete", action="store_true", help="delete file if line is empty"
    )
    parser.add_argument(
        "-n", "--dryrun", action="store_true", help="dryrun mode, don't rename any file"
    )
    parser.add_argument("files", nargs=ONE_OR_MORE, type=Path, help="files to rename")
    args = parser.parse_args()

    try:
        # filter existing files from input and avoid doublons
        input_files = [f for f in dict.fromkeys(args.files) if f.exists()]
        assert len(input_files) > 0, "No valid file to rename"

        # edit the files list with editor
        with NamedTemporaryFile() as tmp:
            tmpfile = Path(tmp.name)
            # write the file list to file
            tmpfile.write_text("".join(f"{f}\n" for f in input_files), encoding="utf8")
            # user edit the file list
            subprocess.check_call([args.editor, tmp.name])
            # read the new file list
            output_files = [
                Path(l)
                if len(l.strip()) > 0
                else None  # handle file delete with None destination
                for l in tmpfile.read_text(encoding="utf8").splitlines()
            ]
            # rename the files
            bulk_rename(
                input_files,
                output_files,
                delete=args.delete,
                dryrun=args.dryrun,
                force=args.force,
            )
    except BaseException as exc:  # pylint: disable=broad-except
        print(f"{F.RED}ERROR: {exc}{F.RESET}", file=sys.stderr)
        exit(1)

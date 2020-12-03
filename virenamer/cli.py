"""
virenamer
"""
import argparse
import os
import shutil
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from tempfile import NamedTemporaryFile

from colorama import Fore

from . import __title__, __version__


def run():
    """
    cli entrypoint
    """
    parser = ArgumentParser(prog=__title__, description="File renamer")
    parser.add_argument(
        "--version", action="version", version=f"{__title__} version {__version__}"
    )
    parser.add_argument(
        "-e", "--editor", action="store", help="editor used to edit file list"
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
    parser.add_argument(
        "files", nargs=argparse.ONE_OR_MORE, type=Path, help="files to rename"
    )
    args = parser.parse_args()

    input_files = []
    output_lines = []
    # filter existing files from input and avoid doublons
    for file in args.files:
        if file.exists() and file not in input_files:
            input_files.append(file)

    # edit the files with editor
    with NamedTemporaryFile() as tmp:
        with open(tmp.name, "w") as tmpfp:
            tmpfp.write("\n".join(input_files) + "\n")
        subprocess.check_call([args.editor or os.getenv("EDITOR", "vi"), tmp.name])
        with open(tmp.name, "r") as tmpfp:
            output_lines = list(map(str.strip, tmpfp))

    # check that the line count is the same
    if len(input_files) != len(output_lines):
        print(f"{Fore.RED}File count has changed, cannot rename any file{Fore.RESET}")
        return 1

    # iterate the two lists
    for source, dest in zip(input_files, output_lines):
        if len(dest.strip()) == 0:
            if args.delete:
                # delete mode
                if args.dryrun:
                    print(f"{Fore.MAGENTA}(dryrun) Delete '{source}'{Fore.RESET}")
                else:
                    print(f"{Fore.GREEN}Delete '{source}'{Fore.RESET}")
                    if source.is_dir():
                        shutil.rmtree(str(source))
                    else:
                        source.unlink()
            else:
                print(
                    f"{Fore.RED}'{source}' won't be deleted, use --delete to enable file deletion{Fore.RESET}"
                )
        else:
            dest = Path(dest)
            if source != dest:
                if dest.exists() and not args.force:
                    print(
                        f"{Fore.RED}'{dest}' already exists, skip renaming, use --force to overwrite'{source}'{Fore.RESET}"
                    )
                else:
                    if args.dryrun:
                        print(
                            f"{Fore.MAGENTA}(dryrun) Rename '{source}' --> '{dest}'{Fore.RESET}"
                        )
                    else:
                        print(f"{Fore.GREEN}Rename '{source}' --> '{dest}'{Fore.RESET}")
                        if not dest.parent.is_dir():
                            dest.parent.mkdir()
                        source.rename(dest)
    return 0

# -*- coding: utf-8 -*-

import argparse
import logging

from add_localized_string import (
    XcodeLocalizationProject,
    InvalidXcodeProject,
)


KEY_HELP = "The key to fetch from the language project."
LANGUAGES_HELP = "The list of languages to fetch. Defaults to Base."
DIFF_KEY_HELP = "Identifies all missing keys from the non-base project in the specified languages."  # NOQA
PROJECT_DIR_HELP = "The Xcode project directory. Defaults to the current directory."  # NOQA


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def build_parser():
    """Builds an argument parser with the appropriate flags.

    returns:
        parser - a constructed ArgumentParser object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--key", type=str, help=KEY_HELP)
    parser.add_argument("-dk", "--diff-keys", type=str, help=DIFF_KEY_HELP)
    parser.add_argument(
        "-l", "--languages", type=str, default="Base", help=LANGUAGES_HELP
    )
    parser.add_argument(
        "-d", "--project-dir", type=str, default=".", help=PROJECT_DIR_HELP
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        xcode_project = XcodeLocalizationProject(args.project_dir)
    except InvalidXcodeProject as ixe:
        log.error(ixe)
        return

    if args.diff_keys:
        print(list(xcode_project.diff_keys()))
    elif args.key is not None:
        print(xcode_project.get(args.key, args.languages.split(',')))


if __name__ == '__main__':
    main()

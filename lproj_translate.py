# -*- coding: utf-8 -*-
#!/usr/bin/env python
import argparse
import json
import sys

import yaml

import constants
from translator import Translator


KEY_HELP = "An identifier for the word to be translated."
TEXT_HELP = "The text to be tralsated."
DEST_LANG_HELP = ("The ISO-693 two letter language code for all the"
                " languages to translate to.")
SRC_LANG_HELP = ("The ISO-693 two letter language code for the "
                 " destination language of the word to translate.")
FORMAT_HELP = ("The format of the outputted translation. Can be JSON or"
               " YAML.")


class TranslateCommand(object):
    """Encapsulates everything about a translation request"""
    def __str__(self):
        return "Key {} Text {} Language {}".format(
            self.key, self.text, self.language
        )

    def __init__(self, **kwargs):
        # cmd_args represents command line arguments returned from argparse
        if 'cmd_args' in kwargs:
            cmd_args = kwargs.pop('cmd_args')
            self.key = cmd_args.key
            self.text = cmd_args.text
            self.language = cmd_args.dest_lang
            self.format = cmd_args.format
        else:
            self.text = kwargs.get(constants.TEXT)
            self.key = kwargs.get(constants.KEY)
            self.language = kwargs.get(constants.LANGUAGE)
            self.format = kwargs.get(constants.FORMAT)

        self.format = self.format or 'JSON'

        if (self.key is None or 
            self.text is None or 
            self.language is None):
            raise ValueError("Invalid data: %s" % self)


def output_dict(key, text, dest_language):
    kv_dict = {
        constants.KEY: key,
        constants.TEXT: text,
        constants.LANGUAGE: dest_language,
    }

    return kv_dict


def parse_input_text(input_text, output_format):
    """Attempts to parse the input text provided from STDIN."""
    if output_format == constants.JSON:
        return json.loads(input_text)
    if output_format == constants.YAML:
        return yaml.load(input_text)

    raise ValueError(
        "Unexpected output format {}.".format(output_format)
    )


def build_parser():
    """Builds an argument parser with the appropriate flags.
    
    returns:
        parser - a constructed ArgumentParser object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--key", type=str, help=KEY_HELP)
    parser.add_argument("-t", "--text", type=str, help=TEXT_HELP)
    parser.add_argument(
        "-dl", "--dest-lang", type=str, help=DEST_LANG_HELP
    )
    parser.add_argument(
        "-sl", "--src-lang", default="en", help=SRC_LANG_HELP
    )
    parser.add_argument(
        "-f", "--format", default="JSON", help=FORMAT_HELP
    )

    return parser


def valid_command_args(args):
    """Validates the provided command line arguments"""
    return (
        args.text is not None and 
        args.key is not None and
        args.dest_lang is not None
    )


def get_cmd_args():
    """Builds the command arguments, either from STDIN or from the 
    provided command line arguments"""
    parser = build_parser()
    args = parser.parse_args()

    if valid_command_args(args):
        return [TranslateCommand(cmd_args=args)]
    
    command = parse_input_text(''.join(sys.stdin.readlines()), args.format)
    commands = []

    if type(command) is dict:
        commands = [TranslateCommand(**command)]
    elif type(command) is list:
        commands = [TranslateCommand(**obj) for obj in command]

    return commands


def get_final_output(commands, translate_func):
    """Gets the output for the function using the provided arguments
    and a function to translate the text."""
    cmd_output = []
    for command in commands:
        text = translate_func(command.text, command.language)
        cmd_output.append(
            output_dict(
                command.key, text, command.language
            )
        )

    return cmd_output


def main():
    commands = get_cmd_args()
    translator = Translator()

    print(get_final_output(commands, translator.translate))


if __name__ == '__main__':
    main()

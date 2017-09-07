# -*- coding: utf-8 -*-
#!/usr/bin/env python

import collections
import glob
import json
import logging
import os
import shutil
import sys
from uuid import uuid4

import constants


LOCALIZABLE_FILENAME = 'Localizable.strings'
PROJECT_EXTENSION = '.lproj'
RESOURCES_DIR = 'Resources'

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class InvalidXcodeProject(Exception):
    def __init__(self, project_dir):
        self.project_dir = project_dir

    def __str__(self):
        return "{} is an invalid Xcode project directory".format(
            self.project_dir
        )

    __repr__ = __str__


class Translator(object):
    """The Translator class wraps all of the functionality from the Google Python API library.

    Attributes:
        translate_service 

    """
    def __init__(self):
        # self.translate_service = discovery.build('translate', version='v2')
        self.translate_service = None

    def translate(self, text, target_lang):
        req = self.translate_service.translations().list(q=text, target=target_lang, source='en')
        texts = req.execute()

        return texts.get('translations')[0].get('translatedText')


class LanguageProject(object):
    def __init__(self, path, language_code, scratch_dir=None, translator=None):
        self.path = path
        self.language_code = language_code
        self.scratch_dir = scratch_dir or '/tmp/translations/'
        self.translator = translator or Translator()
        if not os.path.exists(self.scratch_dir):
            os.makedirs(self.scratch_dir)

    @property
    def scratch_file_path(self):
        return '{}/{}.{}'.format(self.scratch_dir, self.language_code, LOCALIZABLE_FILENAME)

    def commit(self):
        try:
            shutil.copy(self.scratch_file_path, self.path)
        except Exception as e:
            log.error('Error commiting %s', self.path, exc_info=True)
    
    def get_translated_line(self, key, value):
        translated_value = self.translator.translate(value, self.language_code)
        return '"{}" = "{}";'.format(key, translated_value)

    def _get_key_value(self, line):
        key, value = line.split('=')
        key = key.strip().replace('"','')
        value = value.strip()[1:-2]
        return key, value

    def parse_language_line(self, line, query_key):
        """Parses out the key/value pair from a Localizable.strings file"""
        try:
            key, value = self._get_key_value(line)
            assert query_key == key
        except ValueError:
            return 'Invalid line: {}'.format(line)
        except AssertionError:
            return None
        
        return value.strip()[1:-2]

    def get_keys(self):
        """Returns every key in the file"""
        with open(self.path, 'r') as lproj_file:
            for line in lproj_file.readlines():
                try:
                    key, value = self._get_key_value(line)
                except ValueError:
                    pass
                else:
                    yield key, value

    def get(self, key):
        """Opens the file, looks for the key, and returns the value"""
        with open(self.path, 'r') as lproj_file:
            for line in lproj_file.readlines():
                if line.find(key) != -1:
                    value = self.parse_language_line(line, key)
                    if value is not None:
                        return value
    
        return None
    
    def set(self, key, value):
        written = False
        prev_start_char = None
        replace_only = False

        existing_value = self.get(key)
        if existing_value is not None:
            replace_only = True

        translated_line = '"{}" = "{}";'.format(key, value)

        if self.language_code != 'Base':
            translated_line = self.get_translated_line(key, value)

        with open(self.scratch_file_path, 'w+') as scratch_file:
            with open(self.path, 'r') as lproj_file:
                for line in lproj_file.readlines():
                    try:
                        line_key, _ = line.split('=')
                    except ValueError:
                        print(line.strip('\n'), file=scratch_file)
                        continue

                    line_to_write = line
                    line_key = line_key.strip('\n').replace('"','')

                    if line_key == key:
                        if not written:
                            line_to_write = translated_line
                            written = True
                    elif not replace_only and prev_start_char is not None:
                        if key[0] >= prev_start_char and key[0] <= line_key[0]: 
                            if not written:
                                print(translated_line, file=scratch_file)
                                written = True
                    
                    prev_start_char = line_key[0]
                    print(line_to_write.strip('\n'), file=scratch_file)
            
            # This happens either when the file is blank to begin with, or when the key is 
            # greater than all the others.
            if not written:
                print(translated_line, file=scratch_file)

        return translated_line


class XcodeLocalizationProject(object):
    """Encapsulates all of the data for an Xcode project"""

    def __init__(self, project_dir, scratch_dir=None):
        self.lprojs = self.get_localization_projects(project_dir, scratch_dir)

    def get_language_code(self, path):
        """Gets the language code from a given path.

        >>> get_language_code('./project/Resources/de.lproj')
        'de'
        """
        if path[-1] == '/':
            path = path[0:-1]
        path = str(path.replace('/{}'.format(LOCALIZABLE_FILENAME), ''))
        return os.path.basename(path).replace(PROJECT_EXTENSION, '') 

    def get_localization_projects(self, project_dir, scratch_dir=None):
        """Parses the Xcode project and returns all language folders.

        Currently these are stored in the directory Resources under the root
        project.

        Ref: https://developer.apple.com/library/content/documentation/MacOSX/Conceptual/BPInternational/LocalizingYourApp/LocalizingYourApp.html
        """
        glob_str = '{}{}/*{}'.format(
            project_dir, RESOURCES_DIR, PROJECT_EXTENSION
        )
        matches = glob.glob(glob_str)
        projects = []
        translator = Translator() 

        for match in matches:
            full_path = os.path.join(match, LOCALIZABLE_FILENAME)
            if os.path.exists(full_path):
                lc = self.get_language_code(full_path)
                lp = LanguageProject(
                    path=full_path, language_code=lc, scratch_dir=scratch_dir, 
                    translator=translator
                )
                projects.append(lp)

        if len(projects) == 0:
            raise InvalidXcodeProject(project_dir)

        return projects

    def diff_keys(self):
        """Returns all of the keys that were not found in non-Base localization files.

        The output will look like the following, assuming we have one missing key and one language:
        
        >>> xcode_project.diff_keys()
        [
            {
                "language": "es",
                "key": "Greeting",
                "value": "Hello"
            }
        ]
        """
        base_project_values = {
            key: value
            for (key, value) in self.get_keys('Base')
        }
        base_keys = set(base_project_values.keys())

        for lproj in self.lprojs:
            lproj_keys = {key for (key, value) in lproj.get_keys()}
            missing_keys = base_keys - lproj_keys

            for key in missing_keys:
                yield {
                    constants.KEY: key,
                    constants.TEXT: base_project_values[key],
                    constants.LANGUAGE: lproj.language_code,
                    constants.FORMAT: constants.JSON,
                }
            

    def get_keys(self, language):
        """Fetches the keys from the specified language project"""
        for lproj in self.lprojs:
            if lproj.language_code == language:
                return lproj.get_keys()

    def get(self, key, languages):
        """Fetches the key from all the language projects"""
        for lproj in self.lprojs:
            if lproj.language_code in languages:
                yield {
                    constants.KEY: key,
                    constants.TEXT: lproj.get(key),
                    constants.LANGUAGE: lproj.language_code,
                    constants.FORMAT: constants.JSON
                } 
        
    def set(self, key, value):
        """Sets the key for all language projects"""
        for lproj in self.language_projects:
            try:
                translated_line = lproj.set(key, value)
            except Exception as e:
                translated_line = None
                log.error('Error setting %s to %s', key, value, exc_info=True)
                return
            else:
                log.info('Set %s=%s in file %s', key, value, lproj.path)
                lproj.commit()


def print_success(message):
    print("  {}✓{} {}".format('\033[92m', '\033[0m', message))


def print_fail(message):
    print("  {}✗{} {}".format('\033[91m', '\033[0m', message))


def print_and_quit():
    print("Usage: ./add_localized_string [project_dir] --set key=value")
    print("Usage: ./add_localized_string [project_dir] --get key")
    sys.exit()


def print_key(key, xcodeproject):
    """Fetches the key from all the language projects"""
    print(json.dumps(xcodeproject.get(key), sort_keys=True, indent=4))


def main():
    if len(sys.argv) < 4:
        print_and_quit()

    project_path = sys.argv[1]
    if project_path[-1] != '/':
        project_path += '/'

    scratch_dir = '/tmp/translations/'
    if len(sys.argv) > 4:
        scratch_dir = sys.argv[4]
    if not os.path.exists(scratch_dir):
        os.makedirs(scratch_dir)

    xcodeproject = XcodeLocalizationProject(project_path, scratch_dir)

    if sys.argv[2] == '--get':
        key = sys.argv[3]
        print_key(key, xcodeproject)

    if sys.argv[2] == '--set':
        try:
            kv_pair = sys.argv[3].split('=')
            xcodeproject.set(key=kv_pair[0], value=kv_pair[1])
        except IndexError:
            print("Key/value pair must be in the form key=value")
            print_and_quit()


if __name__ == '__main__':
    main()

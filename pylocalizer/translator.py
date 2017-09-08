# -*- coding: utf-8 -*-

import logging

from googleapiclient import discovery


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class Translator(object):
    """The Translator class wraps all of the functionality from the Google
    Python API library.

    Attributes:
        translate_service
    """
    def __init__(self, translate_service=None):
        self.translate_service = (
            translate_service or
            discovery.build('translate', version='v2')
        )

    def translate(self, text, target_lang):
        """Translates the given text.

        Arguments:
        text -- The text to translate
        dest_lang -- The ISO-639 language code to translate to

        Keyword Arguments:
        src_lang -- The language code to translate from, if None this
            will default to locale.getdefaultlocale()

        Returns the translated text.
        """

        req = self.translate_service.translations().list(
            q=text, target=target_lang, source='en'
        )
        texts = req.execute()

        return texts.get('translations')[0].get('translatedText')

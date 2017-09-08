# -*- coding: utf-8 -*-

import json
from unittest import mock

import pytest
import yaml

from pylocalizer import constants, lproj_translate


output_dict = {
    constants.KEY: 'greeting',
    constants.TEXT: 'hello',
    constants.LANGUAGE: 'es',
}

output_dict2 = {
    constants.KEY: 'farewell',
    constants.TEXT: 'bye',
    constants.LANGUAGE: 'jp'
}

output_dict_array = {
    constants.KEY: 'greeting',
    constants.TEXT: 'grüße',
    constants.LANGUAGE: 'jp',
}

bad_formats = [
    ('html'),
    ('bson'),
    ('yAmL'),
    ('jSoN'),
]

output_test_data = [
    ('greeting', 'hello', 'es', 'JSON', [output_dict]),
    ('greeting', 'hello', 'es', 'YAML', [output_dict]),
    ('greeting', 'grüße', ['es', 'jp'], 'YAML', output_dict_array),
    ('greeting', 'grüße', ['es', 'jp'], 'JSON', output_dict_array),
]


@pytest.mark.parametrize(
    'key,text,language,output_format,expected', output_test_data
)
def test_output_dict(key, text, language, output_format, expected):
    output = lproj_translate.output_dict(key, text, language, output_format)
    assert expected == output


@pytest.mark.parametrize('bad_format', bad_formats)
def test_output_key_exception(bad_format):
    with pytest.raises(ValueError):
        lproj_translate.output_dict('greeting', 'hello', 'es', bad_format)


@pytest.mark.parametrize('input_text,output_format,expected', [
    (json.dumps(output_dict), 'JSON', output_dict),
    (yaml.dump(output_dict), 'YAML', output_dict),
])
def test_parse_input_text(input_text, output_format, expected):
    output = lproj_translate.parse_input_text(input_text, output_format)
    assert expected == output


@pytest.mark.parametrize('bad_format', bad_formats)
def test_parse_input_text_exception(bad_format):
    with pytest.raises(ValueError):
        lproj_translate.parse_input_text(output_dict, bad_format)


@pytest.fixture(scope='module',
                params=[
                    ('hi', 'greeting', 'jp'),
                    ('hi', 'greeting', 'es')])
def valid_args(request):
    return mock.MagicMock(
        text=request.param[0],
        key=request.param[1],
        dest_lang=request.param[2],
        format='JSON'
    )


@pytest.fixture(scope='module',
                params=[
                    ('hi', None, 'es'),
                    ('hi', 'greeting', None)])
def invalid_args(request):
    return mock.MagicMock(
        text=request.param[0],
        key=request.param[1],
        dest_lang=request.param[2],
        format='JSON'
    )


def test_get_cmd_args(valid_args):
    with mock.patch('argparse.ArgumentParser') as mock_argument_parser:
        mock_argument_parser.return_value = mock.MagicMock(
            parse_args=mock.MagicMock(return_value=valid_args)
        )
        commands = lproj_translate.get_cmd_args()
        assert commands[0].text == valid_args.text
        assert commands[0].key == valid_args.key
        assert commands[0].language == valid_args.dest_lang.split(',')


def test_get_cmd_invalid_everything(invalid_args):
    with mock.patch('argparse.ArgumentParser') as mock_argument_parser:
        mock_argument_parser.return_value = mock.MagicMock(
            parse_args=mock.MagicMock(return_value=invalid_args)
        )
        with mock.patch('sys.stdin') as mock_stdin:
            mock_stdin.readlines = mock.MagicMock(
                return_value='{}'
            )
            with pytest.raises(ValueError):
                lproj_translate.get_cmd_args()


def test_get_cmd_invalid_args(invalid_args):
    with mock.patch('argparse.ArgumentParser') as mock_argument_parser:
        mock_argument_parser.return_value = mock.MagicMock(
            parse_args=mock.MagicMock(return_value=invalid_args)
        )
        with mock.patch('sys.stdin') as mock_stdin:
            mock_stdin.readlines = mock.MagicMock(
                return_value=json.dumps(output_dict)
            )
            commands = lproj_translate.get_cmd_args()

            assert output_dict.get(constants.TEXT) == commands[0].text
            assert output_dict.get(constants.KEY) == commands[0].key
            assert output_dict.get(constants.LANGUAGE) == commands[0].language


def test_get_final_output(valid_args):
    translator_func = mock.MagicMock(return_value='oh hi')

    lproj_translate.get_final_output(valid_args, translator_func)

    translator_func.assert_called_once()
    expected = ((valid_args.text, valid_args.dest_lang),)
    assert translator_func.call_args == expected


def test_get_cmd_args_multiple():
    with mock.patch('argparse.ArgumentParser') as mock_argument_parser:
        mock_argument_parser.return_value = mock.MagicMock(
            parse_args=mock.MagicMock(
                return_value=mock.MagicMock(text=None, format='JSON')
            )
        )
        with mock.patch('sys.stdin') as mock_stdin:
            mock_stdin.readlines = mock.MagicMock(
                return_value=json.dumps([output_dict, output_dict2])
            )
            commands = lproj_translate.get_cmd_args()

        assert len(commands) == 2
        for idx, expected in enumerate([output_dict, output_dict2]):
            assert expected.get(constants.TEXT) == commands[idx].text
            assert expected.get(constants.KEY) == commands[idx].key
            assert expected.get(constants.LANGUAGE) == commands[idx].language


def test_get_final_output_multiple():
    commands = [
        lproj_translate.TranslateCommand(**output_dict),
        lproj_translate.TranslateCommand(**output_dict2)
    ]
    translator_func = mock.MagicMock(return_value='word')

    lproj_translate.get_final_output(commands, translator_func)

    assert translator_func.call_count == 2

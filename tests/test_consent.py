"""Tests for ecotone_common.consent."""

from unittest.mock import MagicMock
from ecotone_common.consent import log_consent, get_current_eula_version


def test_log_consent_executes_insert():
    cursor = MagicMock()
    log_consent(cursor, 'user-123', 'eula', '1.0', True, '1.2.3.4', 'Mozilla/5.0')
    cursor.execute.assert_called_once()
    sql, params = cursor.execute.call_args[0]
    assert 'INSERT INTO consent_log' in sql
    assert params == ('user-123', 'eula', '1.0', True, '1.2.3.4', 'Mozilla/5.0')


def test_log_consent_optional_fields():
    cursor = MagicMock()
    log_consent(cursor, 'user-456', 'eula', '2.0', False)
    _, params = cursor.execute.call_args[0]
    assert params == ('user-456', 'eula', '2.0', False, None, None)


def test_get_current_eula_version_dict_cursor():
    cursor = MagicMock()
    cursor.fetchone.return_value = {'version': '2.1'}
    result = get_current_eula_version(cursor)
    assert result == '2.1'
    cursor.execute.assert_called_once()


def test_get_current_eula_version_tuple_cursor():
    cursor = MagicMock()
    cursor.fetchone.return_value = ('3.0',)
    result = get_current_eula_version(cursor)
    assert result == '3.0'


def test_get_current_eula_version_none():
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    result = get_current_eula_version(cursor)
    assert result is None

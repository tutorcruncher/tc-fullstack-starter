from datetime import datetime

from app.common.utils import escape_like, inclusive_end_of_day, sanitize_for_postgres

NULL = chr(0)
CTRL_1 = chr(1)
CTRL_2 = chr(2)
CTRL_3 = chr(3)


class TestEscapeLike:
    """Test the escape_like function for SQL LIKE pattern escaping."""

    def test_escapes_percent_character(self):
        """Test that percent signs are escaped."""
        assert escape_like('%') == '\\%'
        assert escape_like('100%') == '100\\%'
        assert escape_like('%match%') == '\\%match\\%'

    def test_escapes_underscore_character(self):
        """Test that underscores are escaped."""
        assert escape_like('_') == '\\_'
        assert escape_like('test_value') == 'test\\_value'
        assert escape_like('_prefix_suffix_') == '\\_prefix\\_suffix\\_'

    def test_escapes_backslash_character(self):
        """Test that backslashes are escaped."""
        assert escape_like('\\') == '\\\\'
        assert escape_like('path\\to\\file') == 'path\\\\to\\\\file'

    def test_escapes_multiple_special_characters(self):
        """Test that multiple special characters in one string are all escaped."""
        assert escape_like('%_\\') == '\\%\\_\\\\'
        assert escape_like('100% of _users\\data') == '100\\% of \\_users\\\\data'

    def test_preserves_normal_text(self):
        """Test that normal text without special characters is unchanged."""
        assert escape_like('hello') == 'hello'
        assert escape_like('Mathematics 101') == 'Mathematics 101'
        assert escape_like('Some Course Name') == 'Some Course Name'

    def test_handles_empty_string(self):
        """Test that empty string returns empty string."""
        assert escape_like('') == ''

    def test_preserves_other_special_characters(self):
        """Test that other special characters are not affected."""
        assert escape_like('test@example.com') == 'test@example.com'
        assert escape_like('$100') == '$100'
        assert escape_like('foo*bar') == 'foo*bar'
        assert escape_like('question?') == 'question?'


class TestInclusiveEndOfDay:
    """Test inclusive_end_of_day bumps midnight datetimes and passes explicit times through."""

    def test_bumps_midnight_to_end_of_day(self):
        """Test that a date-only datetime is bumped to 23:59:59.999999 the same day."""
        assert inclusive_end_of_day(datetime(2024, 3, 15)) == datetime(2024, 3, 15, 23, 59, 59, 999999)

    def test_passes_through_explicit_time(self):
        """Test that a datetime with an explicit time is returned unchanged."""
        dt = datetime(2024, 3, 15, 10, 0, 0)
        assert inclusive_end_of_day(dt) == dt

    def test_passes_through_time_with_microseconds(self):
        """Test that any non-midnight time, including sub-second precision, passes through."""
        dt = datetime(2024, 3, 15, 0, 0, 0, 1)
        assert inclusive_end_of_day(dt) == dt


class TestSanitizeForPostgres:
    """Test the sanitize_for_postgres function."""

    def test_removes_null_bytes(self):
        """Test that null bytes are removed from strings."""
        assert sanitize_for_postgres(f'Hello{NULL}World') == 'HelloWorld'
        assert sanitize_for_postgres(f'Test{NULL}String') == 'TestString'

    def test_removes_control_characters(self):
        """Test that control characters are removed except newline, carriage return and tab."""
        assert sanitize_for_postgres(f'Hello{CTRL_1}{CTRL_2}{CTRL_3}World') == 'HelloWorld'
        assert sanitize_for_postgres('Hello\nWorld\tTest\r\n') == 'Hello\nWorld\tTest\r\n'

    def test_sanitizes_dict_values(self):
        """Test that dictionary values are recursively sanitized."""
        input_dict = {
            'content': f'Fantastic teamwork{NULL} today',
            'score': 95,
            'nested': {'text': f'Good{NULL}work', 'count': 5},
        }
        assert sanitize_for_postgres(input_dict) == {
            'content': 'Fantastic teamwork today',
            'score': 95,
            'nested': {'text': 'Goodwork', 'count': 5},
        }

    def test_sanitizes_list_items(self):
        """Test that list items are recursively sanitized."""
        assert sanitize_for_postgres([f'Hello{NULL}World', 123, {'text': f'Test{NULL}String'}]) == [
            'HelloWorld',
            123,
            {'text': 'TestString'},
        ]

    def test_handles_nested_structures(self):
        """Test complex nested structures with multiple levels."""
        input_data = {
            'students': [
                {'name': f'John{NULL}Doe', 'scores': [95, 87, 92]},
                {'name': f'Jane{NULL}Smith', 'scores': [98, 91, 94]},
            ],
            'summary': f'Great{NULL}performance{CTRL_1}overall',
        }
        assert sanitize_for_postgres(input_data) == {
            'students': [
                {'name': 'JohnDoe', 'scores': [95, 87, 92]},
                {'name': 'JaneSmith', 'scores': [98, 91, 94]},
            ],
            'summary': 'Greatperformanceoverall',
        }

    def test_preserves_other_types(self):
        """Test that non-string, non-collection types are preserved unchanged."""
        assert sanitize_for_postgres(123) == 123
        assert sanitize_for_postgres(45.67) == 45.67
        assert sanitize_for_postgres(True) is True
        assert sanitize_for_postgres(False) is False
        assert sanitize_for_postgres(None) is None

#################################################################################
# Eclipse Tractus-X - Software Development KIT - Tests for the op class
#
# These tests have been refactored to reduce duplication, add descriptive
# comments in English, and improve clarity by grouping related tests.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

import math
import json
import os
import sys
import time
import io
import datetime
import pytest
from datetime import timezone
from shutil import copyfile
from dataspace.tools import op

# ---------------- FIXTURES ----------------

@pytest.fixture
def simple_data():
    """
    Provides simple test data for JSON serialization tests.
    """
    return {
        "valid": {
            "string": "",
            "bytes": bytes(),
            "bytearray": bytearray(),
            "whitespace": " ",
            "whitespace_bytes": bytes(" ", "utf-8"),
            "whitespace_bytearray": bytearray(" ", "utf-8"),
        },
        "invalid": {
            "int": 0,
            "boolean": False,
            "None": None,
            "array": [1, 2, 3],
            "dict": {},
            "float": 0.0,
            "set": set(),
            "tuple": tuple(),
            "date": datetime.datetime.now(),
            "non_string_key_dict": {1: "one", 2: "two"},
        },
    }

@pytest.fixture
def json_data():
    """
    Provides JSON test cases with both valid and invalid formats.
    """
    complex_json = json.dumps({
        "name": "John Doe",
        "age": 30,
        "email": "john.doe@example.com",
        "is_active": True,
        "tags": ["developer", "python", "tester"],
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": None,
            "postal_code": "12345"
        },
        "history": [
            {"year": 2010, "event": "Started first job"},
            {"year": 2015, "event": "Moved to a new city"},
            {"year": 2020, "event": "Started a new project"}
        ]
    })
    return {
        "valid": {
            "string": complex_json,
            "bytes": complex_json.encode("utf-8"),
            "bytearray": bytearray(complex_json, "utf-8"),
            "unicode": '{"name": "Jöhn", "age": 30}'
        },
        "invalid": {
            "extra_comma": '{"name": "John", "age": 30,}',
            "unquoted_key": '{name: "John", age: 30}',
            "missing_bracket": '{"name": "John", "age": 30',
            "mismatching_bracket": '{"name": "John"} "age": 30}'
            # Removed "unescaped_special" since it is accepted by json.loads
        }
    }

# ---------------- TESTS FOR JSON FUNCTIONS ----------------

# Function: json_string_to_object
@pytest.mark.parametrize("entry", [
    "string", "bytes", "bytearray",
    "whitespace", "whitespace_bytes", "whitespace_bytearray"
])
def test_json_string_to_object_empty_input_should_raise_JSONDecodeError(entry, simple_data):
    """
    Test json_string_to_object: Empty input should raise JSONDecodeError.
    """
    with pytest.raises(json.JSONDecodeError):
        op.json_string_to_object(simple_data["valid"][entry])

@pytest.mark.parametrize("entry", [
    "int", "boolean", "None", "array", "dict", "float", "set", "tuple", "date"
])
def test_json_string_to_object_invalid_input_should_raise_TypeError(entry, simple_data):
    """
    Test json_string_to_object: Non-string/bytes/bytearray types should raise TypeError.
    """
    with pytest.raises(TypeError):
        op.json_string_to_object(simple_data["invalid"][entry])

@pytest.mark.parametrize("entry", [
    "extra_comma", "unquoted_key", "missing_bracket", "mismatching_bracket"
])
def test_json_string_to_object_invalid_json_format_should_raise_JSONDecodeError(entry, json_data):
    """
    Test json_string_to_object: Malformed JSON should raise JSONDecodeError.
    """
    with pytest.raises(json.JSONDecodeError):
        op.json_string_to_object(json_data["invalid"][entry])

@pytest.mark.parametrize("entry", ["string", "bytes", "bytearray", "unicode"])
def test_json_string_to_object_valid_format_should_return_valid_JSON(entry, json_data):
    """
    Test json_string_to_object: Properly formatted JSON returns the expected object.
    """
    expected = json.loads(json_data["valid"][entry])
    assert op.json_string_to_object(json_data["valid"][entry]) == expected

# Function: to_json
@pytest.mark.parametrize("entry", [
    "string", "int", "float", "boolean", "None", "array", "tuple", "dict", "non_string_key_dict"
])
def test_to_json_serializable_input_should_return_valid_json(entry, simple_data):
    """
    Test to_json: Serializable input should return equivalent JSON string.
    """
    value = simple_data["invalid"].get(entry, "")
    assert op.to_json(value) == json.dumps(value)

@pytest.mark.parametrize("entry", ["bytes", "bytearray", "set", "date"])
def test_to_json_non_serializable_input_should_raise_TypeError(entry, simple_data):
    """
    Test to_json: Non-serializable input should raise TypeError.
    """
    # Use 'bytes' and 'bytearray' from valid group; others from invalid group.
    if entry in ["bytes", "bytearray"]:
        value = simple_data["valid"][entry]
    else:
        value = simple_data["invalid"][entry]
    with pytest.raises(TypeError):
        op.to_json(value)

@pytest.mark.parametrize("source, expected", [(True, "true"), (False, "false")])
def test_to_json_boolean_should_return_string(source, expected):
    """
    Test to_json: Boolean values are serialized as 'true' or 'false'.
    """
    assert op.to_json(source) == expected

@pytest.mark.parametrize("ensure_ascii, expected_substr", [
    (True, "\\u3053"), (False, "こんにちは")
])
def test_to_json_unicode_handling(ensure_ascii, expected_substr):
    """
    Test to_json: Unicode characters handling based on ensure_ascii parameter.
    """
    result = op.to_json({"greeting": "こんにちは"}, ensure_ascii=ensure_ascii)
    assert expected_substr in result

@pytest.mark.parametrize("special_number, expected_substr", [
    ("nan", "NaN"), ("inf", "Infinity")
])
def test_to_json_special_numbers(special_number, expected_substr):
    """
    Test to_json: Special numbers (NaN, Infinity) appear correctly in the JSON output.
    """
    value = getattr(math, special_number)
    result = op.to_json({"value": value})
    assert expected_substr in result

def test_to_json_custom_object_should_raise_TypeError():
    """
    Test to_json: Custom non-serializable objects should raise TypeError.
    """
    class Custom:
        pass
    with pytest.raises(TypeError):
        op.to_json(Custom())

# Function: to_json_file
@pytest.mark.parametrize("source", [
    {"name": "Alice", "age": 30},
    [1, "two", 3.0, True, None],
    None,
    {},
])
def test_to_json_file_should_write_valid_json(tmp_path, source):
    """
    Test to_json_file: Valid JSON is written to a file for various data types.
    """
    file_path = tmp_path / "output.json"
    op.to_json_file(source, str(file_path), "w", indent=2)
    # Compare the structure by parsing to avoid spacing differences
    assert json.loads(file_path.read_text()) == json.loads(json.dumps(source, indent=2))

def test_to_json_file_append_mode(tmp_path):
    """
    Test to_json_file: Append mode should add JSON to the existing file content.
    """
    source = {"appended": True}
    file_path = tmp_path / "append.json"
    initial_content = "Existing Content\n"
    file_path.write_text(initial_content)
    op.to_json_file(source, str(file_path), "a", indent=2)
    expected = initial_content + json.dumps(source, indent=2)
    assert file_path.read_text() == expected

def test_to_json_file_invalid_mode_should_raise_exception(tmp_path):
    """
    Test to_json_file: Invalid file open mode should raise ValueError.
    """
    file_path = tmp_path / "invalid_mode.json"
    with pytest.raises(ValueError):
        op.to_json_file({"error": "test"}, str(file_path), "invalid", indent=2)

def test_to_json_file_non_serializable_object_should_raise_TypeError(tmp_path):
    """
    Test to_json_file: Non-serializable objects should raise TypeError.
    """
    file_path = tmp_path / "non_serializable.json"
    with pytest.raises(TypeError):
        op.to_json_file({"non_serializable": lambda x: x}, str(file_path), "w", indent=2)

# Function: read_json_file
@pytest.mark.parametrize("source", [
    {"name": "John", "age": 30},
    [1, 2, 3, "four", True, None],
    {
        "company": "TechCorp",
        "employees": [
            {"id": 1, "name": "John Doe", "skills": ["Python", "Java"]},
            {"id": 2, "name": "Jane Smith", "skills": ["UI/UX", "Design"]}
        ],
        "active": True
    },
    {"saludo": "¡Hola, mundo!", "emoji": "😊"}
])
def test_read_json_file_should_return_correct_structure(tmp_path, source):
    """
    Test read_json_file: Correct JSON structure is retrieved from a file.
    """
    file_path = tmp_path / "input.json"
    file_path.write_text(json.dumps(source, indent=2), encoding="utf-8")
    result = op.read_json_file(str(file_path))
    assert result == source

def test_read_json_file_nonexistent_should_raise_FileNotFoundError(tmp_path):
    """
    Test read_json_file: Nonexistent file should raise FileNotFoundError.
    """
    file_path = tmp_path / "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        op.read_json_file(str(file_path))

def test_read_json_file_invalid_json_should_raise_JSONDecodeError(tmp_path):
    """
    Test read_json_file: File containing invalid JSON should raise JSONDecodeError.
    """
    file_path = tmp_path / "invalid.json"
    file_path.write_text("Invalid JSON", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        op.read_json_file(str(file_path))

def test_read_json_file_empty_file_should_raise_JSONDecodeError(tmp_path):
    """
    Test read_json_file: Empty file should raise JSONDecodeError.
    """
    file_path = tmp_path / "empty.json"
    file_path.write_text("", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        op.read_json_file(str(file_path))

def test_read_json_file_with_different_encoding(tmp_path):
    """
    Test read_json_file: File with a different encoding is read correctly.
    """
    source = {"mensaje": "¡Olé! – ñandú"}
    file_path = tmp_path / "latin1.json"
    file_path.write_text(json.dumps(source, indent=2), encoding="iso-8859-1")
    result = op.read_json_file(str(file_path), encoding="iso-8859-1")
    assert result == source

# Function: path_exists
def test_path_exists_file(tmp_path):
    """
    Test path_exists: Existing file returns True.
    """
    file = tmp_path / "existing.txt"
    file.write_text("Test content")
    assert op.path_exists(str(file)) is True

def test_path_exists_nonexistent(tmp_path):
    """
    Test path_exists: Nonexistent file returns False.
    """
    file = tmp_path / "nonexistent.txt"
    assert op.path_exists(str(file)) is False

def test_path_exists_directory(tmp_path):
    """
    Test path_exists: Existing directory returns True.
    """
    directory = tmp_path / "subdir"
    directory.mkdir()
    assert op.path_exists(str(directory)) is True

def test_path_exists_relative_path(tmp_path, monkeypatch):
    """
    Test path_exists: Relative path is handled correctly.
    """
    file = tmp_path / "relative.txt"
    file.write_text("Relative file content")
    monkeypatch.chdir(tmp_path)
    assert op.path_exists("relative.txt") is True

def test_path_exists_trailing_slash(tmp_path):
    """
    Test path_exists: Directory path with a trailing separator returns True.
    """
    directory = tmp_path / "dir_with_slash"
    directory.mkdir()
    path_with_slash = str(directory) + os.sep
    assert op.path_exists(path_with_slash) is True

def test_path_exists_with_none_should_raise_TypeError():
    """
    Test path_exists: Passing None as input should raise TypeError.
    """
    with pytest.raises(TypeError):
        op.path_exists(None)

def test_path_exists_with_symlink(tmp_path):
    """
    Test path_exists: Symbolic link to an existing file returns True.
    """
    target_file = tmp_path / "target.txt"
    target_file.write_text("Target content")
    symlink_file = tmp_path / "symlink.txt"
    try:
        os.symlink(str(target_file), str(symlink_file))
    except (AttributeError, NotImplementedError, OSError):
        pytest.skip("Symlink not supported on this platform")
    assert op.path_exists(str(symlink_file)) is True

# Functions: make_dir and delete_dir
def test_make_and_delete_dir(tmp_path):
    """
    Test make_dir: Create a directory when it doesn't exist, and
    delete_dir: Remove the directory correctly.
    """
    dir_path = tmp_path / "new_dir"
    # Ensure the directory does not exist
    if op.path_exists(str(dir_path)):
        op.delete_dir(str(dir_path))
    op.make_dir(str(dir_path))
    assert os.path.isdir(str(dir_path))
    # Delete the directory
    op.delete_dir(str(dir_path))
    assert not op.path_exists(str(dir_path))
    # Deleting a non-existent directory should return False
    assert op.delete_dir(str(dir_path)) is False

# Functions: copy_file and move_file
def test_copy_and_move_file(tmp_path):
    """
    Test copy_file: Copy a file correctly,
    and move_file: Move the file to the destination.
    """
    # Create original file
    original = tmp_path / "original.txt"
    original.write_text("Original content")
    # Copy the file
    copy_dest = tmp_path / "copy.txt"
    op.copy_file(str(original), str(copy_dest))
    assert op.path_exists(str(copy_dest)) is True
    assert original.read_text() == copy_dest.read_text()
    # Move the copied file
    move_dest = tmp_path / "moved.txt"
    op.move_file(str(copy_dest), str(move_dest))
    assert not op.path_exists(str(copy_dest))  # The original copy should no longer exist
    assert op.path_exists(str(move_dest)) is True
    assert original.read_text() == move_dest.read_text()

# Functions: to_string and load_file
def test_to_string_and_load_file(tmp_path):
    """
    Test to_string: Read file as string;
    load_file: Load file into a BytesIO buffer.
    """
    content = "Test file content."
    file_path = tmp_path / "text.txt"
    file_path.write_text(content, encoding="utf-8")
    # Test to_string
    assert op.to_string(str(file_path)) == content
    # Test load_file
    buffer = op.load_file(str(file_path))
    assert isinstance(buffer, io.BytesIO)
    assert buffer.getvalue() == content.encode("utf-8")

# Function: delete_file
def test_delete_file(tmp_path):
    """
    Test delete_file: Successfully delete an existing file,
    and return False if the file does not exist.
    """
    file_path = tmp_path / "to_delete.txt"
    file_path.write_text("Delete this file")
    # Delete the existing file
    assert op.delete_file(str(file_path)) is True
    # Trying to delete again should return False
    assert op.delete_file(str(file_path)) is False

# Function: write_to_file
def test_write_to_file(tmp_path):
    """
    Test write_to_file: Write data to a file.
    """
    file_path = tmp_path / "output.txt"
    data = "Data to be written."
    # Write valid data
    assert op.write_to_file(data, str(file_path), "w", end="END") is True
    assert file_path.read_text(encoding=sys.stdout.encoding) == data + "END"
    # Writing an empty string or None should return False
    assert op.write_to_file("", str(file_path)) is False
    assert op.write_to_file(None, str(file_path)) is False

# Functions: timestamp, get_filedatetime and get_filedate
def test_timestamp_and_file_date_functions():
    """
    Test timestamp: Returns a numeric value or string,
    get_filedatetime and get_filedate: Return strings in the expected format.
    """
    ts_numeric = op.timestamp(string=False)
    ts_string = op.timestamp(string=True)
    assert isinstance(ts_numeric, float)
    # The string should be convertible to float without error
    float(ts_string)
    file_dt = op.get_filedatetime()
    file_d = op.get_filedate()
    # Check basic length and format (YYYYMMDD and YYYYMMDD_HHMMSS)
    assert len(file_d) == 8
    assert len(file_dt) >= 15

# Function: get_path_without_file
def test_get_path_without_file(tmp_path):
    """
    Test get_path_without_file: Extracts the directory path from a file path.
    """
    file_path = tmp_path / "subdir" / "file.txt"
    expected_dir = os.path.dirname(str(file_path))
    assert op.get_path_without_file(str(file_path)) == expected_dir

# Function: wait
def test_wait(monkeypatch):
    """
    Test wait: Delegates to time.sleep and returns None.
    Uses monkeypatch to avoid an actual delay.
    """
    called = False
    def fake_sleep(seconds):
        nonlocal called
        called = True
    monkeypatch.setattr(time, "sleep", fake_sleep)
    result = op.wait(0.1)
    assert called is True
    assert result is None

# Function: get_attribute
def test_get_attribute():
    """
    Test get_attribute: Retrieves nested attributes from a dictionary.
    """
    source = {
        "a": {
            "b": {
                "c": 123
            }
        }
    }
    # Successful case: existing attribute
    assert op.get_attribute(source, "a.b.c") == 123
    # Default value case: non-existent attribute or invalid data
    assert op.get_attribute(source, "a.x.c", default_value="default") == "default"
    assert op.get_attribute(None, "a.b", default_value="default") == "default"
    # Case with empty path separator should return default
    assert op.get_attribute(source, "a.b.c", default_value="default", path_sep="") == "default"

#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################
# -----------------IMPORTS---------------------------

import math
import os
import pytest
import json
import datetime
from dataspace.tools import op

#------------TEST VARIABLES--------------------------

@pytest.fixture
def simple_data_for_test(): #Simple data examples
    return {
        "string": "",
        "bytes": bytes(),
        "bytearray": bytearray(),
        "string_whitespace": " ",
        "bytes_whitespace": bytes(" ", 'utf-8'),
        "bytearray_whitespace": bytearray(" ", 'utf-8'),   
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
    }
    
@pytest.fixture
def complex_json_for_test(): #Complete JSON with variances for testing purposes
    return """{
            "name": "John Doe",
            "age": 30,
            "email": "john.doe@example.com",
            "is_active": true,
            "tags": ["developer", "python", "tester"],
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": null,
                "postal_code": "12345"
            },
            "history": [
                {"year": 2010, "event": "Started first job"},
                {"year": 2015, "event": "Moved to a new city"},
                {"year": 2020, "event": "Started a new project"}
            ]
            }
            """

@pytest.fixture
def json_data_for_test(complex_json_for_test): #Json data for testing purposes
    return{
        "extra_comma" : '{"name": "John", "age": 30,}',
        "unquoted_key" : '{name: "John", age: 30}',
        "missing_bracket" : '{"name": "John", "age": 30',
        "mismatching_bracket" : '{"name": "John"} "age": 30}',
        "unescaped_special_characters" : '{"name": "John \n Doe"}',
        "complex_valid_string":  complex_json_for_test,
        "complex_valid_bytes": complex_json_for_test.encode('utf-8'), #converts string version to bytes
        "complex_valid_bytearray": bytearray(complex_json_for_test, 'utf-8'), #converts string version to bytearray
        "unicode_valid": '{"name": "Jöhn", "age": 30}'
    }


# -----------------TESTS-----------------------------

#Function 1 - json_string_to_object

@pytest.mark.parametrize("type", ["string", "bytes", "bytearray", "string_whitespace", "bytes_whitespace", "bytearray_whitespace"])
def test_json_string_to_object_with_empty_valid_input_should_return_JSONDecodeError(type, simple_data_for_test):
    value = simple_data_for_test[type] #Obtain the empty values
    with pytest.raises(json.JSONDecodeError):
        op.json_string_to_object(value) 
        
@pytest.mark.parametrize("type", ["int", "boolean", "None", "array", "dict", "float", "set", "tuple", "date"])
def test_json_string_to_object_with_invalid_input_should_return_TypeError(type, simple_data_for_test):
    value = simple_data_for_test[type] #Obtain the empty values
    with pytest.raises(TypeError):
        op.json_string_to_object(value) 
                             
@pytest.mark.parametrize("entries", ["extra_comma","unquoted_key","missing_bracket","unescaped_special_characters"])
def test_json_string_to_object_with_invalid_JSON_format_should_return_JSONDecodeError(entries,json_data_for_test):
    value = json_data_for_test[entries]
    with pytest.raises(json.JSONDecodeError):
        op.json_string_to_object(value)
        
@pytest.mark.parametrize("entries", ["complex_valid_string","complex_valid_bytes", "complex_valid_bytearray", "unicode_valid"])
def test_json_string_to_object_with_valid_format_should_return_valid_JSON(entries,json_data_for_test):
    expected = json.loads(json_data_for_test[entries])
    assert op.json_string_to_object(json_data_for_test[entries]) == expected

#Function 2 - to_json

@pytest.mark.parametrize("type", ["string", "int", "float", "boolean", "None", "array", "tuple", "dict", "non_string_key_dict"])
def test_to_json_with_serializable_input_should_return_valid_json(type,simple_data_for_test):
    value = simple_data_for_test[type]
    assert op.to_json(value) == json.dumps(simple_data_for_test[type])
    
@pytest.mark.parametrize("type", ["bytes", "bytearray", "set", "date"])
def test_to_json_with_non_serializable_input_should_return_TypeError(type,simple_data_for_test):
    with pytest.raises(TypeError):
        op.to_json(simple_data_for_test[type])

    #Arange
    source_true = True
    expected_true = "true"
    source_false = False
    expected_false = "false"
    #Act
    result_true = op.to_json(source_true)
    result_false = op.to_json(source_false)
    #Assert
    assert result_true == expected_true
    assert result_false == expected_false

def test_to_json_with_complex_data_should_return_valid_json(complex_json_for_test):
    expected = json.dumps(complex_json_for_test)
    assert op.to_json(complex_json_for_test) == expected
        
def test_to_json_with_indent_parameter_should_return_indented_json(complex_json_for_test):
    expected = json.dumps(complex_json_for_test, indent=4)
    assert op.to_json(complex_json_for_test, indent=4) == expected

def test_to_json_with_non_ascii_characters_ensure_ascii_true_should_escape_characters(): #Specific for this method
    #Arange
    source = {"greeting": "こんにちは"}
    #Act
    result = op.to_json(source, ensure_ascii=True)
    # Assert
    assert "\\u3053" in result #checks non ascii works correctly

def test_to_json_with_non_ascii_characters_ensure_ascii_false_should_not_escape_characters(): #Specific for this method
    # Arange
    source = {"greeting": "こんにちは"}
    # Act
    result = op.to_json(source, ensure_ascii=False)
    # Assert
    assert "こんにちは" in result # When ensure_ascii is False, non-ASCII characters appear as is.

def test_to_json_with_special_numbers(): #Specific for this method
    assert "NaN" in op.to_json({"value":math.nan})
    assert "Infinity" in op.to_json({"value":math.inf})

def test_to_json_with_custom_object_should_raise_TypeError(): #Specific edge case for this method
    #Arange
    class Custom:
        pass
    source = Custom()
    #Assert
    with pytest.raises(TypeError):# Custom objects are not serializable by default.
        op.to_json(source)

#Function 3 - to_json_file

def test_to_json_file_with_simple_dict_should_write_valid_json(tmp_path):
    #Arange
    source = {"name": "Alice", "age": 30}
    file_path = tmp_path / "simple_dict.json"
    expected = json.dumps(source, indent=2)
    #Act
    op.to_json_file(source_object=source, json_file_path=str(file_path), file_open_mode="w", indent=2)
    #Assert
    content = file_path.read_text()
    assert content == expected

def test_to_json_file_with_list_should_write_valid_json(tmp_path):
    #Arange
    source = [1, "two", 3.0, True, None]
    file_path = tmp_path / "list.json"
    expected = json.dumps(source, indent=2)
    #Act
    op.to_json_file(source_object=source, json_file_path=str(file_path), file_open_mode="w", indent=2)
    #Assert.
    content = file_path.read_text()
    assert content == expected

def test_to_json_file_with_none_should_write_valid_json(tmp_path):
    #Arange
    source = None
    file_path = tmp_path / "none.json"
    expected = json.dumps(source, indent=2) # "null"
    #Act
    op.to_json_file(source_object=source, json_file_path=str(file_path), file_open_mode="w", indent=2)
    #Assert
    content = file_path.read_text()
    assert content == expected

def test_to_json_file_with_nested_data_should_write_valid_json(tmp_path):
    #Arange
    source = {
        "company": "TechCorp",
        "founded": 1995,
        "active": True,
        "address": {
            "street": "123 Tech Lane",
            "city": "San Francisco",
            "zip": "94122",
            "geo": {"lat": 37.7749, "lng": -122.4194}
        },
        "employees": [
            {
                "id": 1,
                "name": "John Doe",
                "age": 35,
                "department": "Engineering",
                "skills": ["Python", "Java", "Docker"],
                "projects": ["Alpha", "Beta"]
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "age": 28,
                "department": "Design",
                "skills": ["UI/UX", "Sketch", "Photoshop"],
                "projects": ["Gamma"]
            }
        ],
        "products": ("Software A", "Software B", "Software C"), # tuple, will be serialized as a JSON array (list)
        "partners": None
    }
    file_path = tmp_path / "nested.json"
    expected = json.dumps(source, indent=2)
    #Act
    op.to_json_file(source_object=source, json_file_path=str(file_path), file_open_mode="w", indent=2)
    #Assert
    content = file_path.read_text()
    assert json.loads(content) == json.loads(expected)

def test_to_json_file_with_empty_dict_should_write_valid_json(tmp_path):
    #Arange
    source = {}
    file_path = tmp_path / "dict.json"
    expected = json.dumps(source, indent=2)
    #Act
    op.to_json_file(source_object=source, json_file_path=str(file_path), file_open_mode="w", indent=2)
    #Assert: An empty dictionary is correctly serialized.
    content = file_path.read_text()
    assert content == expected

def test_to_json_file_with_non_ascii_characters_should_write_valid_json(tmp_path):
    #Arange
    source = {"greeting": "こんにちは"} # Non-ASCII text
    file_path = tmp_path / "non_ascii.json"
    expected = json.dumps(source, indent=2)
    #Act
    op.to_json_file(source_object=source, json_file_path=str(file_path), file_open_mode="w", indent=2)
    #Assert
    content = file_path.read_text()
    assert content == expected #Ensure non-ASCII characters are serialized as expected (escaped if ensure_ascii is True).

def test_to_json_file_with_append_mode_should_append_valid_json(tmp_path):
    #Arange
    source = {"appended": True}
    file_path = tmp_path / "append.json"
    initial_content = "Existing Content\n"
    file_path.write_text(initial_content)
    expected = initial_content + json.dumps(source, indent=2)
    #Act
    op.to_json_file(source_object=source, json_file_path=str(file_path), file_open_mode="a", indent=2)
    #Assert
    content = file_path.read_text()
    assert content == expected #The JSON data should be appended after the initial content.

def test_to_json_file_with_invalid_file_mode_should_raise_exception(tmp_path):
    #Arange
    source = {"error": "test"}
    file_path = tmp_path / "invalid_mode.json"
    #Act
    
    # Assert
    with pytest.raises(ValueError): #  An invalid file mode should trigger an exception when opening the file.
        op.to_json_file(source_object=source, json_file_path=str(file_path), file_open_mode="invalid", indent=2)

def test_to_json_file_with_non_serializable_object_should_raise_type_error(tmp_path):
    #Arange
    source = {"non_serializable": lambda x: x} # Lambda functions cannot be JSON serialized.
    file_path = tmp_path / "non_serializable.json"
    #Act
    
    #Assert
    with pytest.raises(TypeError):
        op.to_json_file(source_object=source, json_file_path=str(file_path), file_open_mode="w", indent=2)

#Function 4 - read_json_file

def test_read_json_file_with_valid_dict_should_return_dict(tmp_path):
    #Arange
    source = {"name": "John", "age": 30}
    file_path = tmp_path / "valid_dict.json"
    file_path.write_text(json.dumps(source, indent=2), encoding="utf-8")
    #Act
    result = op.read_json_file(str(file_path))
    #Assert
    assert result == source

def test_read_json_file_with_mixed_list_should_return_valid_list(tmp_path):
    #Arange
    source = [1, 2, 3, "four", True, None]
    file_path = tmp_path / "valid_list.json"
    file_path.write_text(json.dumps(source, indent=2), encoding="utf-8")
    #Act
    result = op.read_json_file(str(file_path))
    #Assert
    assert result == source

def test_read_json_file_with_nested_data_should_return_nested_structure(tmp_path):
    #Arange
    source = {
        "company": "TechCorp",
        "employees": [
            {"id": 1, "name": "John Doe", "skills": ["Python", "Java"]},
            {"id": 2, "name": "Jane Smith", "skills": ["UI/UX", "Design"]}
        ],
        "active": True
    }
    file_path = tmp_path / "nested.json"
    file_path.write_text(json.dumps(source, indent=2), encoding="utf-8")
    #Act
    result = op.read_json_file(str(file_path))
    #Assert
    assert result == source

def test_read_json_file_with_utf8_encoding_should_return_correct_characters(tmp_path):
    #Arange
    source = {"saludo": "¡Hola, mundo!", "emoji": "😊"}
    file_path = tmp_path / "utf8.json"
    file_path.write_text(json.dumps(source, indent=2), encoding="utf-8")
    #Act
    result = op.read_json_file(str(file_path), encoding="utf-8")
    #Assert
    assert result == source

def test_read_json_file_with_nonexistent_file_should_raise_FileNotFoundError(tmp_path):
    #Arange
    file_path = tmp_path / "nonexistent.json"
    #Act
    
    #Assert
    with pytest.raises(FileNotFoundError):
        op.read_json_file(str(file_path))

def test_read_json_file_with_invalid_json_should_raise_JsonDecodeError(tmp_path):
    #Arange
    file_path = tmp_path / "invalid.json"
    file_path.write_text("This is not valid JSON", encoding="utf-8")
    #Act
    
    #Assert
    with pytest.raises(json.JSONDecodeError):
        op.read_json_file(str(file_path))

def test_read_json_file_with_empty_file_should_raise_JsonDecodeError(tmp_path):
    #Arange
    file_path = tmp_path / "empty.json"
    file_path.write_text("", encoding="utf-8")
    #Act
    
    #Assert
    with pytest.raises(json.JSONDecodeError):
        op.read_json_file(str(file_path))

def test_read_json_file_with_different_encoding_should_return_correct_data(tmp_path):
    #Arange
    source = {"mensaje": "¡Olé! – ñandú"}
    file_path = tmp_path / "latin1.json"
    file_path.write_text(json.dumps(source, indent=2), encoding="iso-8859-1")
    #Act
    result = op.read_json_file(str(file_path), encoding="iso-8859-1")
    #Assert
    assert result == source

#Function 5 - path_exists

def test_path_exists_with_existing_file_should_return_true(tmp_path):
    #Arange
    file = tmp_path / "existing.txt"
    file.write_text("Test content")
    #Act
    result = op.path_exists(str(file))
    #Assert
    assert result is True

def test_path_exists_with_nonexistent_file_should_return_false(tmp_path):
    #Arange
    file = tmp_path / "nonexistent.txt"
    #Act
    result = op.path_exists(str(file))
    #Assert
    assert result is False

def test_path_exists_with_existing_directory_should_return_true(tmp_path):
    #Arange
    directory = tmp_path / "subdir"
    directory.mkdir()
    #Act
    result = op.path_exists(str(directory))
    #Assert
    assert result is True

def test_path_exists_with_relative_path_should_return_true(tmp_path, monkeypatch):
    #Arange
    file = tmp_path / "relative.txt"
    file.write_text("Relative file content")
    monkeypatch.chdir(tmp_path)
    relative_path = "relative.txt"
    #Act
    result = op.path_exists(relative_path)
    #Assert
    assert result is True

def test_path_exists_with_directory_trailing_slash_should_return_true(tmp_path):
    #Arange
    directory = tmp_path / "dir_with_slash"
    directory.mkdir()
    path_with_slash = str(directory) + os.sep
    #Act
    result = op.path_exists(path_with_slash)
    #Assert
    assert result is True

def test_path_exists_with_None_input_should_raise_TypeError():
    #Arange
    invalid_input = None
    #Act
     
    #Assert
    with pytest.raises(TypeError):
        op.path_exists(invalid_input)
        
#Execute with privileges in some systems to ensure that the test passes, otherwise skipped
def test_path_exists_with_symbolic_link_should_return_true(tmp_path):
    #Arange
    target_file = tmp_path / "target.txt"
    target_file.write_text("Target content")
    symlink_file = tmp_path / "symlink.txt"
    try:
        os.symlink(str(target_file), str(symlink_file))
    except (AttributeError, NotImplementedError, OSError): #if platform doesn't support symbolic links
        pytest.skip("Symlink not supported on this platform")
    #Act
    result = op.path_exists(str(symlink_file))
    #Assert
    assert result is True

#Function 6 - make_dir



#Function 7 - delete_dir



#Function 8 - copy_file



#Function 9 - move_file



#Function 10 - to_string



#Function 11 - load_file



#Function 12 - delete_file



#Function 13 - timestamp



#Function 14 - get_filedatetime



#Function 15 - get_filedate



#Function 16 - get_path_without_file



#Function 17 - write_to_file



#Function 18 - wait



#Function 19 - get_attribute
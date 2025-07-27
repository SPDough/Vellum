"""
Basic unit tests
"""
import pytest
from datetime import datetime
import uuid


def test_basic_math():
    """Test basic mathematical operations"""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12
    assert 8 / 2 == 4


def test_string_operations():
    """Test string operations"""
    test_string = "Hello World"
    assert test_string.lower() == "hello world"
    assert test_string.upper() == "HELLO WORLD"
    assert len(test_string) == 11
    assert "World" in test_string


def test_list_operations():
    """Test list operations"""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert test_list[0] == 1
    assert test_list[-1] == 5
    assert sum(test_list) == 15


def test_datetime_operations():
    """Test datetime operations"""
    now = datetime.now()
    assert isinstance(now, datetime)
    assert now.year >= 2024


def test_uuid_generation():
    """Test UUID generation"""
    test_uuid = uuid.uuid4()
    assert isinstance(test_uuid, uuid.UUID)
    assert len(str(test_uuid)) == 36  # Standard UUID string length


def test_dictionary_operations():
    """Test dictionary operations"""
    test_dict = {"key1": "value1", "key2": "value2"}
    assert test_dict["key1"] == "value1"
    assert "key1" in test_dict
    assert len(test_dict) == 2
    
    test_dict["key3"] = "value3"
    assert len(test_dict) == 3
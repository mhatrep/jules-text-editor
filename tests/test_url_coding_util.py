import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.url_coding_util import url_encode_string, url_decode_string

class TestUrlCodingUtil(unittest.TestCase):

    def test_url_encode(self):
        self.assertEqual(url_encode_string("hello world"), "hello%20world")
        self.assertEqual(url_encode_string("key=value&other key=123 !"), "key%3Dvalue%26other%20key%3D123%20%21")
        self.assertEqual(url_encode_string("你好"), "%E4%BD%A0%E5%A5%BD") # Unicode
        self.assertEqual(url_encode_string(""), "") # Empty string
        self.assertEqual(url_encode_string("https://example.com/path?query=سلام"), "https%3A//example.com/path%3Fquery%3D%D8%B3%D9%84%D8%A7%D9%85")
        self.assertEqual(url_encode_string(None), "") # None input

    def test_url_decode(self):
        self.assertEqual(url_decode_string("hello%20world"), "hello world")
        self.assertEqual(url_decode_string("key%3Dvalue%26other%20key%3D123%20%21"), "key=value&other key=123 !")
        self.assertEqual(url_decode_string("%E4%BD%A0%E5%A5%BD"), "你好") # Unicode
        self.assertEqual(url_decode_string(""), "") # Empty string
        self.assertEqual(url_decode_string("https%3A//example.com/path%3Fquery%3D%D8%B3%D9%84%D8%A7%D9%85"), "https://example.com/path?query=سلام")
        self.assertEqual(url_decode_string("name=John+Doe"), "name=John Doe") # Plus for space
        self.assertEqual(url_decode_string(None), "") # None input

        # Test malformed sequences (urllib.parse.unquote handles them gracefully by default)
        self.assertEqual(url_decode_string("test%"), "test%") # Malformed, should return as is or with replacement char
        self.assertEqual(url_decode_string("test%2"), "test%2")
        self.assertEqual(url_decode_string("test%2X"), "test%2X")


if __name__ == '__main__':
    unittest.main()

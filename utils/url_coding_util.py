import urllib.parse

def url_encode_string(text_to_encode):
    """
    URL-encodes a given string.

    Args:
        text_to_encode (str): The string to be URL-encoded.

    Returns:
        str: The URL-encoded string.
        None: If an error occurs during encoding.
    """
    if text_to_encode is None: # Explicitly handle None input if desired
        return "" # Or None, depending on preferred behavior for None
    try:
        return urllib.parse.quote(text_to_encode)
    except Exception as e:
        print(f"Error during URL encoding: {e}")
        return None

def url_decode_string(text_to_decode):
    """
    URL-decodes a given string.

    Args:
        text_to_decode (str): The string to be URL-decoded.

    Returns:
        str: The URL-decoded string.
        None: If an error occurs during decoding.
    """
    if text_to_decode is None:
        return ""
    try:
        return urllib.parse.unquote_plus(text_to_decode) # Changed to unquote_plus
    except Exception as e:
        print(f"Error during URL decoding: {e}")
        return None

if __name__ == '__main__':
    print("URL Coding Utility Tests")
    print("=" * 25)

    # Test Encoding
    original_str1 = "Hello World!"
    encoded_str1 = url_encode_string(original_str1)
    print(f"Original: '{original_str1}' -> Encoded: '{encoded_str1}' (Expected: Hello%20World%21)")
    assert encoded_str1 == "Hello%20World%21"

    original_str2 = "key=value with spaces&another_key=!"
    encoded_str2 = url_encode_string(original_str2)
    print(f"Original: '{original_str2}' -> Encoded: '{encoded_str2}' (Expected: key%3Dvalue%20with%20spaces%26another_key%3D%21)")
    assert encoded_str2 == "key%3Dvalue%20with%20spaces%26another_key%3D%21"

    original_str3 = "你好，世界" # Unicode characters
    encoded_str3 = url_encode_string(original_str3)
    print(f"Original: '{original_str3}' -> Encoded: '{encoded_str3}' (Expected: %E4%BD%A0%E5%A5%BD%EF%BC%8C%E4%B8%96%E7%95%8C)")
    assert encoded_str3 == "%E4%BD%A0%E5%A5%BD%EF%BC%8C%E4%B8%96%E7%95%8C"

    empty_str_encoded = url_encode_string("")
    print(f"Original: '' -> Encoded: '{empty_str_encoded}' (Expected: '')")
    assert empty_str_encoded == ""

    none_encoded = url_encode_string(None)
    print(f"Original: None -> Encoded: '{none_encoded}' (Expected: '')")
    assert none_encoded == ""

    print("\n--- Test Decoding ---")
    # Test Decoding
    encoded_val1 = "Hello%20World%21"
    decoded_val1 = url_decode_string(encoded_val1)
    print(f"Encoded: '{encoded_val1}' -> Decoded: '{decoded_val1}' (Expected: Hello World!)")
    assert decoded_val1 == "Hello World!"

    encoded_val2 = "key%3Dvalue%20with%20spaces%26another_key%3D%21"
    decoded_val2 = url_decode_string(encoded_val2)
    print(f"Encoded: '{encoded_val2}' -> Decoded: '{decoded_val2}' (Expected: key=value with spaces&another_key=!)")
    assert decoded_val2 == "key=value with spaces&another_key=!"

    encoded_val3 = "%E4%BD%A0%E5%A5%BD%EF%BC%8C%E4%B8%96%E7%95%8C"
    decoded_val3 = url_decode_string(encoded_val3)
    print(f"Encoded: '{encoded_val3}' -> Decoded: '{decoded_val3}' (Expected: 你好，世界)")
    assert decoded_val3 == "你好，世界"

    # Test decoding of strings with plus for space (common in query strings)
    encoded_plus_space = "name=John+Doe&city=New+York"
    decoded_plus_space = url_decode_string(encoded_plus_space)
    print(f"Encoded (plus): '{encoded_plus_space}' -> Decoded: '{decoded_plus_space}' (Expected: name=John Doe&city=New York)")
    assert decoded_plus_space == "name=John Doe&city=New York" # urllib.parse.unquote handles + as space

    empty_str_decoded = url_decode_string("")
    print(f"Encoded: '' -> Decoded: '{empty_str_decoded}' (Expected: '')")
    assert empty_str_decoded == ""

    none_decoded = url_decode_string(None)
    print(f"Encoded: None -> Decoded: '{none_decoded}' (Expected: '')")
    assert none_decoded == ""

    print("\nAll URL Coding tests passed.")

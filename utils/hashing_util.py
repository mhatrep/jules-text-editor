import hashlib

def compute_hash(text, algorithm="sha256"):
    """
    Computes a hash for the given text using the specified algorithm.

    Args:
        text (str): The input string to hash.
        algorithm (str): The hashing algorithm to use.
                         Supported: "md5", "sha1", "sha256", "sha512".
                         Defaults to "sha256".

    Returns:
        str: The hexadecimal representation of the hash.
        None: If the algorithm is not supported.
    """
    try:
        text_bytes = text.encode('utf-8')
        if algorithm == "md5":
            hasher = hashlib.md5()
        elif algorithm == "sha1":
            hasher = hashlib.sha1()
        elif algorithm == "sha256":
            hasher = hashlib.sha256()
        elif algorithm == "sha512":
            hasher = hashlib.sha512()
        else:
            return None  # Algorithm not supported

        hasher.update(text_bytes)
        return hasher.hexdigest()
    except Exception as e:
        # Log error or handle as appropriate
        print(f"Error computing hash ({algorithm}) for text: {e}")
        return None

if __name__ == '__main__':
    sample_text = "Hello, Jules!"

    print(f"Hashing text: \"{sample_text}\"")

    md5_hash = compute_hash(sample_text, "md5")
    print(f"MD5:    {md5_hash}")

    sha1_hash = compute_hash(sample_text, "sha1")
    print(f"SHA1:   {sha1_hash}")

    sha256_hash = compute_hash(sample_text, "sha256")
    print(f"SHA256: {sha256_hash}")

    sha512_hash = compute_hash(sample_text, "sha512")
    print(f"SHA512: {sha512_hash}")

    unsupported_hash = compute_hash(sample_text, "sha3_256")
    print(f"Unsupported (sha3_256): {unsupported_hash}")

    empty_text_hash = compute_hash("", "sha256")
    print(f"SHA256 (empty string): {empty_text_hash}")
    # Expected for empty string SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    assert empty_text_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    # Test with some unicode
    unicode_text = "Jules, c'est très bien! 😊"
    unicode_sha256 = compute_hash(unicode_text, "sha256")
    print(f"SHA256 (unicode \"{unicode_text}\"): {unicode_sha256}")

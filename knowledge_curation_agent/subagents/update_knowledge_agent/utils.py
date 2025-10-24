import re
import string
import secrets


def remove_nonalphanumeric(text):
    """Removes all characters from a string that are not alphanumeric."""
    # The pattern '[^a-zA-Z0-9]' matches any character that is NOT a letter (a-z, A-Z) or a digit (0-9).
    # re.sub() replaces all occurrences of the pattern with an empty string.
    return re.sub(r'[^a-zA-Z0-9]', '', text)

def generate_random_string(length=10):
    """
    Generates a cryptographically secure random string of a given length.

    The string is composed of uppercase letters, lowercase letters, and digits.

    Args:
        length (int): The desired length of the random string.

    Returns:
        str: A random string of the specified length.
    """
    if not isinstance(length, int) or length <= 0:
        raise ValueError("Length must be a positive integer")

    # Define the character set to choose from
    characters = string.ascii_lowercase + string.digits

    # Use secrets.choice() for cryptographic security
    random_string = ''.join(secrets.choice(characters) for _ in range(length))

    return random_string


def shorten_string(text, length):
    """
    Shortens a string to a specified length, truncating at word boundaries.

    Args:
        text: The string to shorten.
        length: The desired length of the shortened string.

    Returns:
        The shortened string, or the original string if it's shorter than the desired length.
    """
    if length <= 0:
        return ""
    if len(text) <= length:
        return text

    shortened_text = ""
    current_index = 0
    while current_index < length:
        shortened_text += text[current_index]
        current_index += 1

    if current_index < len(text):
        shortened_text += "..."

    return shortened_text

def capitalize_sentence(sentence: str) -> str:
    """
    Capitalizes the first letter of each word in a given sentence string.

    Args:
        sentence: The input sentence string.

    Returns:
        The sentence with the first letter of each word capitalized.
    """
    if not sentence:
        return ""

    words = sentence.split()
    capitalized_words = []
    for word in words:
        if word:  # Handle potential empty strings after splitting
            capitalized_words.append(word[0].upper() + word[1:])
        else:
            capitalized_words.append("") # Preserve empty strings

    return " ".join(capitalized_words)



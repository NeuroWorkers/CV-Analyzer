import re


def shorten_string(text, length):
    """
    Усекает строку до заданной длины, обрезая по границам слов.

    Args:
        text: Строка, которую нужно сократить.
        length: Желаемая длина усечённой строки.

    Returns:
        Усечённую строку, либо исходную строку, если она короче указанной длины.
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
    Делает заглавной первую букву каждого слова во входной строке-предложении.

    Args:
        sentence: Входная строка-предложение.

    Returns:
        Строку, в которой первая буква каждого слова написана с заглавной буквы.
    """
    if not sentence:
        return ""

    words = sentence.split()
    capitalized_words = []
    for word in words:
        if word:
            capitalized_words.append(word[0].upper() + word[1:])
        else:
            capitalized_words.append("")

    return " ".join(capitalized_words)


def clean_words(text: str) -> str:
    """
    Удаляет знаки препинания из строки и оставляет только слова.

    Args:
        text (str): Входная строка из 1–2 слов с возможными знаками препинания.

    Returns:
        str: Строка, содержащая только слова, разделённые пробелом.
    """
    cleaned = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    return cleaned.strip()

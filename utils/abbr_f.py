import re

abbr1 = ["СММ","ИИ", "IT", "CEO", "CPO", "CX", "LBS", "OKR", "EX", "HR", "INST", "1С", "CMO", "AI", "ИТ", "GR", "НК", "UTC", "БФЛ", "CTO", "СЕО", "ИК", "IT", "УК", "SEO", "СПб", "МСК", "3D", "РФ", "СМО", "ООО", "В2В", "ТГ", "ИИ", "ТГ", "HR", "РГ", "PM", "ML", "MVP", "CFO", "IR", "VC", "ecom", "KFC", "ЦСР", "МГУ", "АО", "FB", "КСП", "КСГ", "MIPT", "CV", "ID", "COO", "ACC", "ICF", "PRO", "b2b", "b2c", "UX", "UI", "OZON", "HSE", "ISPRAS", "QA", "RU", "ES", "CCO", "L&D", "UK", "CET", "CRM", "PMM", "IB", "M&A", "ПО", "SERM", "MD", "CHO", "CMS", "КР", "n8n", "ceo", "АИС", "UA", "LLM", "ITMO", "MISIS", "IM", "СНГ", "NDT", "США", "BCN", "ФРИИ", "АМР", "PR", "UMI.CMS", "TDI", "FOM", "CIO", "vp", "GSOM", "IOC", "FIFA"]

trans1={ "ИИ" : "AI", "СММ" : "SMM" }


def abbr_capitalize(input_string, short_words):
    """
    Capitalizes words in a string that are present in a list of short words (case-insensitive).

    Args:
        input_string: The string to process.
        short_words: A list of short words to capitalize.

    Returns:
        The modified string with short words capitalized.
    """
    result_words = []
    short_words_lower = {word.lower() for word in short_words}

    for word in re.findall(r'\b\w+\b', input_string):
        if word.lower() in short_words_lower:
            result_words.append(word.upper())
        else:
            result_words.append(word)

    return " ".join(result_words)

############

def abbr_trans(text, trans1 = trans1):
    """
    Translates words in a string using the trans1 dictionary.

    Args:
        text: The input string.
        trans1: The translation dictionary.

    Returns:
        The translated string.
    """
    words = text.split()
    for i in range(len(words)):
        if words[i] in trans1:
            words[i] = trans1[words[i]]
    translated_text = " ".join(words)
    return translated_text





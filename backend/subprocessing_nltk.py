import re
from typing import List, Tuple, Dict
from nltk.stem import SnowballStemmer

stemmer_en = SnowballStemmer("english")
stemmer_ru = SnowballStemmer("russian")


def is_abbreviation(word: str) -> bool:
    return word.isupper() and len(word) <= 5


def detect_language(word: str) -> str:
    if re.search(r"[а-яА-Я]", word):
        return "russian"
    else:
        return "english"


def normalize_word(word: str) -> str:
    if is_abbreviation(word):
        return word.upper()
    lang = detect_language(word)
    stemmer = stemmer_ru if lang == "russian" else stemmer_en
    return stemmer.stem(word.lower())


def tokenize_and_normalize(text: str) -> List[str]:
    words = re.findall(r"\b\w+\b", text)
    return [normalize_word(w) for w in words]


async def post_proccessing(user_query: str, results: List[dict], highlights: List[str]) -> Tuple[List[dict], List[str]]:
    """
    Фильтрует результаты поиска по совпадениям с user_query на русском и английском.

    Возвращает только те записи, где хотя бы одно слово из запроса найдено в highlight.
    """
    if not results or not highlights:
        return [], []

    query_words = tokenize_and_normalize(user_query)

    filtered_results = []
    filtered_highlights = []

    for result, highlight in zip(results, highlights):
        highlight_words = tokenize_and_normalize(f"{result['author']} . {result['content']} . {highlight}")

        if any(qw in highlight_words for qw in query_words):
            filtered_results.append(result)
            filtered_highlights.append(highlight)

    return filtered_results, filtered_highlights

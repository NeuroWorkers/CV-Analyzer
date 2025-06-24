import asyncio
import edgedb
from configs.ai_config import *


async def generate_search_query(prompt: str) -> str:
    system_prompt = (
        "Ты помощник, который преобразует пользовательский запрос в оптимизированную строку "
        "для полнотекстового поиска в базе данных резюме. "
        "Выделяй ключевые слова, связанные термины, и если упомянет числовой диапазон — укажи все числа в нём. "
        "Например, 'от 20 до 25' превращай в '20 21 22 23 24 25'. "
        "Также добавляй синонимы: 'молодой' → 'начинающий, без опыта, джун'. "
        "Не добавляй лишних слов. Верни одну строку — готовую поисковую фразу."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response["choices"][0]["message"]["content"].strip()


client = edgedb.create_async_client("db")


async def fts_search(query: str):
    return await client.query("""
        WITH results := fts::search(ResumeMessage, <str>$q)
        SELECT results.object {
            content,
            author,
            created_at
        }
        LIMIT 10;
    """, q=query)


async def full_pipeline(user_query: str):
    print(f"[INFO] Запрос пользователя: {user_query}")

    search_phrase = await generate_search_query(user_query)
    print(f"[DEBUG] Сгенерированный поисковый запрос: {search_phrase}")

    # Передаём строку, не список
    results = await fts_search(search_phrase)

    return [
        {
            "content": r.content,
            "author": r.author,
            "created_at": r.created_at.isoformat()
        }
        for r in results
    ]


if __name__ == "__main__":
    query = "PRo People"
    output = asyncio.run(full_pipeline(query))

    print("\n--- Результаты поиска ---")
    for r in output:
        print(f"{r['created_at']} - {r['author']}: {r['content']}")
#!/usr/bin/env python3
"""
Утилита для анализа и валидации JSON файлов с данными сообщений
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Set


def analyze_json_file(file_path: str):
    """Анализирует структуру JSON файла с данными сообщений"""
    
    print(f"Анализ файла: {file_path}")
    print("=" * 50)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return
    
    # Общая статистика
    topics = list(data.keys())
    print(f"Количество топиков: {len(topics)}")
    
    total_messages = 0
    message_ids = set()
    duplicate_ids = set()
    authors = defaultdict(int)
    dates = []
    media_types = defaultdict(int)
    empty_content = 0
    
    for topic_id, messages in data.items():
        print(f"\nТопик {topic_id}:")
        print(f"  Сообщений: {len(messages)}")
        
        topic_message_ids = set()
        
        for i, message in enumerate(messages):
            total_messages += 1
            
            # Проверка структуры сообщения
            if not isinstance(message, dict):
                print(f"  ОШИБКА: Сообщение {i} не является объектом")
                continue
            
            if 'downloaded_text' not in message:
                print(f"  ОШИБКА: Сообщение {i} не содержит поле 'downloaded_text'")
                continue
            
            if 'downloaded_media' not in message:
                print(f"  ОШИБКА: Сообщение {i} не содержит поле 'downloaded_media'")
                continue
            
            downloaded_text = message['downloaded_text']
            downloaded_media = message.get('downloaded_media', {})
            
            if not isinstance(downloaded_text, list) or len(downloaded_text) < 4:
                print(f"  ОШИБКА: Некорректная структура downloaded_text в сообщении {i}")
                continue
            
            # Извлечение данных
            msg_id = downloaded_text[0]
            date = downloaded_text[1]
            content = downloaded_text[2]
            author = downloaded_text[3]
            
            # Проверка ID сообщения
            if msg_id in message_ids:
                duplicate_ids.add(msg_id)
            elif msg_id in topic_message_ids:
                print(f"  ПРЕДУПРЕЖДЕНИЕ: Дубликат ID {msg_id} в топике {topic_id}")
            
            message_ids.add(msg_id)
            topic_message_ids.add(msg_id)
            
            # Сбор статистики
            if author:
                authors[author] += 1
            
            if date:
                dates.append(date)
            
            if not content or content.strip() == '':
                empty_content += 1
            
            # Анализ медиа
            if isinstance(downloaded_media, dict):
                media_type = downloaded_media.get('type', 'none')
                media_types[media_type] += 1
        
        # Проверка сортировки по ID
        sorted_ids = sorted(topic_message_ids)
        actual_ids = [msg['downloaded_text'][0] for msg in messages if 'downloaded_text' in msg and len(msg['downloaded_text']) > 0]
        
        if sorted_ids != actual_ids:
            print(f"  ПРЕДУПРЕЖДЕНИЕ: Сообщения в топике {topic_id} не отсортированы по ID")
    
    print(f"\n{'='*50}")
    print("ОБЩАЯ СТАТИСТИКА:")
    print(f"Всего сообщений: {total_messages}")
    print(f"Уникальных ID: {len(message_ids)}")
    print(f"Дубликатов ID: {len(duplicate_ids)}")
    print(f"Пустых сообщений: {empty_content}")
    
    print(f"\nТоп-10 авторов:")
    top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]
    for author, count in top_authors:
        print(f"  {author}: {count} сообщений")
    
    print(f"\nТипы медиа:")
    for media_type, count in sorted(media_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {media_type}: {count}")
    
    if dates:
        dates.sort()
        print(f"\nПериод сообщений:")
        print(f"  От: {dates[0]}")
        print(f"  До: {dates[-1]}")
    
    if duplicate_ids:
        print(f"\nДубликаты ID (первые 10):")
        for dup_id in sorted(duplicate_ids)[:10]:
            print(f"  {dup_id}")


def validate_json_file(file_path: str) -> bool:
    """Валидирует JSON файл на соответствие ожидаемой структуре"""
    
    print(f"Валидация файла: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return False
    
    if not isinstance(data, dict):
        print("❌ Корневой элемент должен быть объектом")
        return False
    
    errors = []
    warnings = []
    
    for topic_id, messages in data.items():
        if not isinstance(messages, list):
            errors.append(f"Топик {topic_id}: значение должно быть массивом")
            continue
        
        message_ids = set()
        
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                errors.append(f"Топик {topic_id}, сообщение {i}: должно быть объектом")
                continue
            
            if 'downloaded_text' not in message:
                errors.append(f"Топик {topic_id}, сообщение {i}: отсутствует поле 'downloaded_text'")
                continue
            
            if 'downloaded_media' not in message:
                errors.append(f"Топик {topic_id}, сообщение {i}: отсутствует поле 'downloaded_media'")
                continue
            
            downloaded_text = message['downloaded_text']
            
            if not isinstance(downloaded_text, list):
                errors.append(f"Топик {topic_id}, сообщение {i}: 'downloaded_text' должно быть массивом")
                continue
            
            if len(downloaded_text) < 4:
                errors.append(f"Топик {topic_id}, сообщение {i}: 'downloaded_text' должно содержать минимум 4 элемента")
                continue
            
            # Проверка ID сообщения
            msg_id = downloaded_text[0]
            if not isinstance(msg_id, int):
                errors.append(f"Топик {topic_id}, сообщение {i}: ID должно быть числом")
                continue
            
            if msg_id in message_ids:
                warnings.append(f"Топик {topic_id}: дубликат ID {msg_id}")
            
            message_ids.add(msg_id)
    
    # Результаты валидации
    if errors:
        print("❌ ОШИБКИ:")
        for error in errors[:20]:  # Показываем только первые 20
            print(f"  {error}")
        if len(errors) > 20:
            print(f"  ... и еще {len(errors) - 20} ошибок")
    
    if warnings:
        print("⚠️  ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings[:10]:  # Показываем только первые 10
            print(f"  {warning}")
        if len(warnings) > 10:
            print(f"  ... и еще {len(warnings) - 10} предупреждений")
    
    if not errors and not warnings:
        print("✅ Файл прошел валидацию без ошибок")
        return True
    elif not errors:
        print("✅ Файл прошел валидацию с предупреждениями")
        return True
    else:
        print("❌ Файл содержит ошибки")
        return False


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python3 analyze_json.py <file.json> [--validate]")
        print("  python3 analyze_json.py merged_result.json")
        print("  python3 analyze_json.py merged_result.json --validate")
        sys.exit(1)
    
    file_path = sys.argv[1]
    validate_only = "--validate" in sys.argv
    
    if not Path(file_path).exists():
        print(f"Файл не найден: {file_path}")
        sys.exit(1)
    
    if validate_only:
        success = validate_json_file(file_path)
        sys.exit(0 if success else 1)
    else:
        analyze_json_file(file_path)


if __name__ == "__main__":
    main()

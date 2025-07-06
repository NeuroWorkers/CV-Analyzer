#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для объединения двух JSON файлов с данными сообщений.

Поддерживает:
- Объединение массивов сообщений по ключам топиков
- Удаление дубликатов по ID сообщений
- Сортировку по ID сообщений
- Валидацию структуры данных
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Set


def load_json_file(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Загружает JSON файл и валидирует его структуру.
    
    Args:
        file_path (str): Путь к JSON файлу
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Словарь с данными
        
    Raises:
        FileNotFoundError: Если файл не найден
        json.JSONDecodeError: Если файл содержит невалидный JSON
        ValueError: Если структура данных некорректна
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Ошибка парсинга JSON в файле {file_path}: {e}", e.doc, e.pos)
    
    # Валидация структуры
    if not isinstance(data, dict):
        raise ValueError(f"Файл {file_path} должен содержать объект JSON")
    
    for topic_id, messages in data.items():
        if not isinstance(messages, list):
            raise ValueError(f"Значение для ключа '{topic_id}' должно быть массивом")
        
        # Проверяем структуру сообщений
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                raise ValueError(f"Сообщение {i} в топике {topic_id} должно быть объектом")
            
            if 'downloaded_text' not in message:
                raise ValueError(f"Сообщение {i} в топике {topic_id} должно содержать поле 'downloaded_text'")
            
            if not isinstance(message['downloaded_text'], list) or len(message['downloaded_text']) < 1:
                raise ValueError(f"Поле 'downloaded_text' в сообщении {i} топика {topic_id} должно быть непустым массивом")
    
    return data


def get_message_id(message: Dict[str, Any]) -> int:
    """
    Извлекает ID сообщения из структуры данных.
    
    Args:
        message (Dict[str, Any]): Сообщение
        
    Returns:
        int: ID сообщения
    """
    try:
        return int(message['downloaded_text'][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return -1


def merge_messages(messages1: List[Dict[str, Any]], messages2: List[Dict[str, Any]], 
                  remove_duplicates: bool = True) -> List[Dict[str, Any]]:
    """
    Объединяет два списка сообщений.
    
    Args:
        messages1 (List[Dict[str, Any]]): Первый список сообщений
        messages2 (List[Dict[str, Any]]): Второй список сообщений
        remove_duplicates (bool): Удалять ли дубликаты по ID
        
    Returns:
        List[Dict[str, Any]]: Объединенный список сообщений
    """
    merged = messages1.copy()
    
    if remove_duplicates:
        # Собираем ID уже существующих сообщений
        existing_ids: Set[int] = set()
        for msg in merged:
            msg_id = get_message_id(msg)
            if msg_id != -1:
                existing_ids.add(msg_id)
        
        # Добавляем только новые сообщения
        for msg in messages2:
            msg_id = get_message_id(msg)
            if msg_id == -1 or msg_id not in existing_ids:
                merged.append(msg)
                if msg_id != -1:
                    existing_ids.add(msg_id)
    else:
        merged.extend(messages2)
    
    return merged


def sort_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Сортирует сообщения по ID.
    
    Args:
        messages (List[Dict[str, Any]]): Список сообщений
        
    Returns:
        List[Dict[str, Any]]: Отсортированный список сообщений
    """
    return sorted(messages, key=get_message_id)


def merge_json_files(file1_path: str, file2_path: str, output_path: str = None,
                    remove_duplicates: bool = True, sort_by_id: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    """
    Объединяет два JSON файла с данными сообщений.
    
    Args:
        file1_path (str): Путь к первому файлу
        file2_path (str): Путь ко второму файлу
        output_path (str): Путь к выходному файлу (опционально)
        remove_duplicates (bool): Удалять ли дубликаты по ID
        sort_by_id (bool): Сортировать ли по ID сообщений
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Объединенные данные
    """
    print(f"Загрузка файла 1: {file1_path}")
    data1 = load_json_file(file1_path)
    print(f"Загружено топиков: {len(data1)}")
    
    print(f"Загрузка файла 2: {file2_path}")
    data2 = load_json_file(file2_path)
    print(f"Загружено топиков: {len(data2)}")
    
    # Объединение данных
    merged_data = {}
    all_topics = set(data1.keys()) | set(data2.keys())
    
    total_messages_before = 0
    total_messages_after = 0
    
    for topic_id in all_topics:
        messages1 = data1.get(topic_id, [])
        messages2 = data2.get(topic_id, [])
        
        total_messages_before += len(messages1) + len(messages2)
        
        print(f"Обработка топика {topic_id}: {len(messages1)} + {len(messages2)} сообщений")
        
        # Объединение сообщений
        merged_messages = merge_messages(messages1, messages2, remove_duplicates)
        
        # Сортировка если требуется
        if sort_by_id:
            merged_messages = sort_messages(merged_messages)
        
        merged_data[topic_id] = merged_messages
        total_messages_after += len(merged_messages)
        
        print(f"Результат для топика {topic_id}: {len(merged_messages)} сообщений")
    
    print(f"\nИтого:")
    print(f"Сообщений до объединения: {total_messages_before}")
    print(f"Сообщений после объединения: {total_messages_after}")
    if remove_duplicates:
        print(f"Удалено дубликатов: {total_messages_before - total_messages_after}")
    
    # Сохранение результата
    if output_path:
        print(f"\nСохранение в файл: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        print("Сохранение завершено")
    
    return merged_data


def main():
    parser = argparse.ArgumentParser(
        description="Объединитель двух JSON файлов с данными сообщений",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python merge_json.py file1.json file2.json -o merged.json
  python merge_json.py cv.json output.json -o combined.json --no-duplicates
  python merge_json.py input1.json input2.json --no-sort
        """
    )
    
    parser.add_argument("file1", help="Путь к первому JSON файлу")
    parser.add_argument("file2", help="Путь ко второму JSON файлу")
    parser.add_argument("-o", "--output", help="Путь к выходному файлу (если не указан, выводится в stdout)")
    parser.add_argument("--no-duplicates", action="store_false", dest="remove_duplicates", 
                       help="Не удалять дубликаты по ID сообщений")
    parser.add_argument("--no-sort", action="store_false", dest="sort_by_id",
                       help="Не сортировать сообщения по ID")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Подробный вывод")
    
    args = parser.parse_args()
    
    try:
        # Проверка существования файлов
        if not Path(args.file1).exists():
            print(f"Ошибка: файл '{args.file1}' не найден", file=sys.stderr)
            sys.exit(1)
        
        if not Path(args.file2).exists():
            print(f"Ошибка: файл '{args.file2}' не найден", file=sys.stderr)
            sys.exit(1)
        
        # Объединение файлов
        result = merge_json_files(
            args.file1, 
            args.file2, 
            args.output,
            args.remove_duplicates,
            args.sort_by_id
        )
        
        # Если нет выходного файла, выводим в stdout
        if not args.output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

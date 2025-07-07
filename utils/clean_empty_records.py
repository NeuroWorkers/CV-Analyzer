#!/usr/bin/env python3
"""
Скрипт для удаления записей из JSON файла с пустым третьим полем в downloaded_text.
"""

import json
import sys
import os
from pathlib import Path

def clean_empty_records(json_data):
    """
    Удаляет записи с пустым третьим полем в downloaded_text.
    
    Args:
        json_data: Словарь с данными JSON
        
    Returns:
        Очищенный словарь
    """
    cleaned_data = {}
    
    for key, records in json_data.items():
        if isinstance(records, list):
            cleaned_records = []
            
            for record in records:
                # Проверяем, есть ли downloaded_text и является ли он списком
                if (isinstance(record, dict) and 
                    'downloaded_text' in record and 
                    isinstance(record['downloaded_text'], list) and
                    len(record['downloaded_text']) >= 3):
                    
                    # Проверяем, не является ли третий элемент пустой строкой
                    if record['downloaded_text'][2] != "":
                        cleaned_records.append(record)
                else:
                    # Если структура не соответствует ожидаемой, сохраняем запись
                    cleaned_records.append(record)
            
            cleaned_data[key] = cleaned_records
        else:
            # Если не список, сохраняем как есть
            cleaned_data[key] = records
    
    return cleaned_data

def main():
    """Основная функция скрипта."""
    if len(sys.argv) != 2:
        print("Использование: python clean_empty_records.py <путь_к_json_файлу>")
        print("Пример: python clean_empty_records.py dump.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Проверяем, существует ли файл
    if not os.path.exists(input_file):
        print(f"Ошибка: файл '{input_file}' не найден")
        sys.exit(1)
    
    # Создаем резервную копию
    backup_file = input_file + ".backup"
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            original_data = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_data)
        
        print(f"Создана резервная копия: {backup_file}")
    except Exception as e:
        print(f"Ошибка при создании резервной копии: {e}")
        sys.exit(1)
    
    # Загружаем и обрабатываем JSON
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Загружен файл: {input_file}")
        
        # Подсчитываем количество записей до очистки
        total_before = 0
        for key, records in data.items():
            if isinstance(records, list):
                total_before += len(records)
        
        # Очищаем данные
        cleaned_data = clean_empty_records(data)
        
        # Подсчитываем количество записей после очистки
        total_after = 0
        for key, records in cleaned_data.items():
            if isinstance(records, list):
                total_after += len(records)
        
        removed_count = total_before - total_after
        
        # Сохраняем очищенные данные
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        
        print(f"Обработка завершена!")
        print(f"Записей до очистки: {total_before}")
        print(f"Записей после очистки: {total_after}")
        print(f"Удалено записей с пустым третьим полем: {removed_count}")
        
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

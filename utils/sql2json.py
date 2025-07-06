import json
import argparse

def parse_copy_block(sql_path, source_filter="TG"):
    data_list = []
    in_copy = False
    with open(sql_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith('COPY public.person_source_data'):
                in_copy = True
                continue
            if in_copy:
                if line.startswith('\\.'):
                    break
                line = line.strip()
                if not line:
                    continue
                cols = line.split('\t')
                if len(cols) != 5:
                    continue  # не та строка
                fetch_id, person_id, source, fetch_date, data_json = cols
                if source != source_filter:
                    continue
                try:
                    data = json.loads(data_json)
                except Exception:
                    continue
                data_list.append((fetch_date, data))
    return data_list

def convert_to_json(data_list, topic_id, start_message_id):
    messages = []
    msg_id = start_message_id
    for fetch_date, d in data_list:
        username = d.get("username") or d.get("tg_username") or ""
        first_name = d.get("first_name") or ""
        last_name = d.get("last_name") or ""
        about = d.get("about", "")
        username_part = f"@{username}" if username else ""
        fio_part = f"{last_name} {first_name}".strip()
        fio_full = f"{username_part} {fio_part}".strip()
        downloaded_text = [
            msg_id,
            fetch_date,
            about,
            fio_full
        ]
        messages.append({
            "downloaded_text": downloaded_text,
            "downloaded_media": {
                "type": "",
                "path": ""
            }
        })
        msg_id += 1
    return {str(topic_id): messages}

def main():
    parser = argparse.ArgumentParser(
        description="Конвертер из SQL COPY-дампа person_source_data в нужный JSON."
    )
    parser.add_argument("sql_file", help="Путь к SQL-дампу")
    parser.add_argument("-o", "--output", help="Имя выходного JSON-файла (по умолчанию stdout)")
    parser.add_argument("-s", "--start", type=int, default=1, help="Начальный номер сообщения (default: 1)")
    parser.add_argument("-t", "--topic", type=int, default=1275, help="ID топика (default: 1275)")
    parser.add_argument("--source", default="TG", help="Фильтруемый источник (default: TG)")
    args = parser.parse_args()

    data = parse_copy_block(args.sql_file, source_filter=args.source)
    res = convert_to_json(data, topic_id=args.topic, start_message_id=args.start)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            json.dump(res, out, ensure_ascii=False, indent=4)
    else:
        print(json.dumps(res, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    main()

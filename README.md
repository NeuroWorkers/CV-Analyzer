# CV-Analyzer
### Инструкция / Настройка по инсталяции EdgeDB 😢
#### установка edgedb
**(1 вариант) mac os:**
```
brew tap edgedb/tap
brew install edgedb-cli
```
дополнительно (возможно это еще сработает)

**(2 вариант) mac os:**
```
brew install edgedb/tap/edgedb-cli 
```

**linux:**
```
curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh
```

#### настройки
далее переходим в папку database/db
```
cd database/db
```

_(по дефолту db там оставляем и инициализируем)_
```
edgedb project init
```

можно просмотреть список инстансов через
```
edgedb instance list   
```

проверки
```
edgedb
```
и там можно ввести запрос (например select)
```sql
select ResumeMessage;
```

активация виртуального окружения и установка зависимостей
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

настройки конфигов:
- убрать sample .. 
- указать `openai.api_key` в ai_config
- указать `API_ID`, `API_HASH`, `SESSION_STRING` в telegram_config

запуск основной через auto_run
```
python3 auto_run.py
```

### Остальное
Запуск question_analyzer.py: 
1) edgedb instance list -> look -> [│ local │ db   │ localhost:10700 │ 6.8+9fb0925 │ running │]
2) edgedb -I db
3) ALTER ROLE edgedb {
  SET password := '1';
};
4) exit
5) edgedb instance link local --trust-tls-cert
6) Specify server host [default: localhost]: 
localhost
7) Specify server port [default: 5656]: 
10700
8) Specify database user [default: edgedb]:
edgedb
9) Specify database/branch (CTRL + D for default):
CTRL + D
10) ALL next -> click Enter
11) Rewrite credentials -> Yes

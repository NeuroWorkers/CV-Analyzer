# CV-Analyzer
### Инструкция / Настройка по инсталяции EdgeDB 😢
ставим edgedb (mac os)
```
brew tap edgedb/tap
brew install edgedb-cli
```
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


### Остальное
Старый Деплой db - 
1) MACOS: brew install edgedb/tap/edgedb-cli или
   (brew tap edgedb/tap
    brew install edgedb-cli) 
LINUX: curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh
2) cd database/db
3) edgedb project init
4) dbschema/default.esdl: 
module default {
  type ResumeMessage {
    required property telegram_id -> int64 {
      constraint exclusive;
    };
    required property created_at -> datetime;
    required property content -> str;
    required property author -> str;
    optional property fwd_date -> datetime;
    optional property fwd_author -> str;
    required property topic_id -> int64;
    optional property media_type -> str;
    optional property media_path -> str;
  };
};
5) edgedb migration create 
   edgedb migrate
6) python3 import_to_db.py

CHECK: 
1) edge db
2) SELECT ResumeMessage;


Новый деплой с гита: 

1) MACOS: brew install edgedb/tap/edgedb-cli или
   (brew tap edgedb/tap
    brew install edgedb-cli) 
LINUX: curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh
2) cd database/db
3) edgedb project init

CHECK: 
1) edge db
2) SELECT ResumeMessage;


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

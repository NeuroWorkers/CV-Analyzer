# CV-Analyzer
Деплой db - 
1) brew install edgedb/tap/edgedb-cli     //     curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh
2) cd database/db
3) edgedb project init
4) dbschema/default.esdl: 
module default {
  type ResumeMessage {
    required telegram_id: int64;
    required created_at: datetime;
    required content: str;
    required author: str;
    optional fwd_date: datetime;
    optional fwd_author: str;
    required topic_id: int64;
    optional media_type: str;
    optional media_path: str;
  };
}; 
5) edgedb migration create
edgedb migrate
6) python3 import_to_db.py

CHECK: 
1) edge db
2) SELECT ResumeMessage {
    telegram_id
}
LIMIT 10;



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

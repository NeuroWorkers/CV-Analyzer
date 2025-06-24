using extension ai;

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

    # index fts::index on (
    #   fts::with_options(
    #     .content,
    #     language := fts::Language.rus
    #   )
    # );

    deferred index ext::ai::index(
      embedding_model := 'text-embedding-3-small'
    ) on (.content);
  };
};

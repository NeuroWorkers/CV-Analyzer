using extension ai;

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

    deferred index ext::ai::index(
      embedding_model := 'text-embedding-3-small'
    ) on (.content);
  };
};
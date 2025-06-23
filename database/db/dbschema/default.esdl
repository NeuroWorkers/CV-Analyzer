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

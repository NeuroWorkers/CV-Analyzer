CREATE MIGRATION m1bby7at4cta7hq7tbyyrz56leo4isyocoddl2dizvn2ybk5n6itdq
    ONTO initial
{
  CREATE FUTURE simple_scoping;
  CREATE TYPE default::ResumeMessage {
      CREATE REQUIRED PROPERTY author: std::str;
      CREATE REQUIRED PROPERTY content: std::str;
      CREATE REQUIRED PROPERTY created_at: std::datetime;
      CREATE OPTIONAL PROPERTY fwd_author: std::str;
      CREATE OPTIONAL PROPERTY fwd_date: std::datetime;
      CREATE OPTIONAL PROPERTY media_path: std::str;
      CREATE OPTIONAL PROPERTY media_type: std::str;
      CREATE REQUIRED PROPERTY telegram_id: std::int64;
      CREATE REQUIRED PROPERTY topic_id: std::int64;
  };
};

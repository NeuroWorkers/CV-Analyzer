CREATE MIGRATION m1q4vpvygjfpyah5ut2mwyy7mxh3w4aggxidximlplizrrjauew23a
    ONTO initial
{
  CREATE EXTENSION pgvector VERSION '0.7';
  CREATE EXTENSION ai VERSION '1.0';
  CREATE FUTURE simple_scoping;
  CREATE TYPE default::ResumeMessage {
      CREATE REQUIRED PROPERTY content: std::str;
      CREATE DEFERRED INDEX ext::ai::index(embedding_model := 'text-embedding-3-small') ON (.content);
      CREATE REQUIRED PROPERTY author: std::str;
      CREATE REQUIRED PROPERTY created_at: std::datetime;
      CREATE OPTIONAL PROPERTY fwd_author: std::str;
      CREATE OPTIONAL PROPERTY fwd_date: std::datetime;
      CREATE OPTIONAL PROPERTY media_path: std::str;
      CREATE OPTIONAL PROPERTY media_type: std::str;
      CREATE REQUIRED PROPERTY telegram_id: std::int64 {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE REQUIRED PROPERTY topic_id: std::int64;
  };
};

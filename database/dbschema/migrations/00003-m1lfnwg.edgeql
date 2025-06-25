CREATE MIGRATION m1lfnwgi5xrnqzpbofaaq3t7hs4r5suywdejtggkxav2mqvl2m3exq
    ONTO m1zxfbkroi75mcqeqv6nvxg5rsql4fgn3fvywbb5bcbvjgya4fvnua
{
  CREATE EXTENSION pgvector VERSION '0.7';
  CREATE EXTENSION ai VERSION '1.0';
  ALTER TYPE default::ResumeMessage {
      CREATE DEFERRED INDEX ext::ai::index(embedding_model := 'text-embedding-3-small') ON (.content);
  };
  ALTER TYPE default::ResumeMessage {
      DROP INDEX std::fts::index ON (std::fts::with_options(.content, language := std::fts::Language.rus));
  };
};

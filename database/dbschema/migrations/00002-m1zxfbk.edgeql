CREATE MIGRATION m1zxfbkroi75mcqeqv6nvxg5rsql4fgn3fvywbb5bcbvjgya4fvnua
    ONTO m1bby7at4cta7hq7tbyyrz56leo4isyocoddl2dizvn2ybk5n6itdq
{
  ALTER TYPE default::ResumeMessage {
      CREATE INDEX std::fts::index ON (std::fts::with_options(.content, language := std::fts::Language.rus));
  };
};

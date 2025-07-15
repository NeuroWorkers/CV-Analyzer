max_processing_message_count = 100

sentence_transformers_embedding_model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
sentence_transformers_embedding_dim = 384
sentence_transformers_threshold = 0.81

openai_embedding_model = "text-embedding-3-large"
openai_embedding_dim = 3072
openai_threshold = 0.4

preprocessing_model = "google/gemini-2.5-flash"
postprocessing_model = "google/gemini-2.5-flash"

llm_search_model = "openai/gpt-4"

faiss_deep = 100
N_LIST = 100
N_PROBE = 20

EMBEDDING_MODE = "sentence_transformers"
# EMBEDDING_MODE = "openai"

SEARCH_MODE = "FAISS"
# SEARCH_MODE = "LLM"

PRE_PROCESSING_FLAG = False
POST_PROCESSING_FLAG = False

import os
import openai
from pathlib import Path

import configs.keys_sample
import configs.main_paths_config_sample
import configs.ai_config_sample
import configs.server_config_sample
import configs.telegram_config_sample

DATA_PATH = configs.main_paths_config_sample.DATA_PATH
DATABASE_PATH = configs.main_paths_config_sample.DATABASE_PATH
FAISS_PATH = configs.main_paths_config_sample.FAISS_PATH

max_processing_message_count = configs.ai_config_sample.max_processing_message_count
faiss_model = configs.ai_config_sample.faiss_model
sort_model = configs.ai_config_sample.sort_model
analyze_query_model = configs.ai_config_sample.analyze_query_model
highlight_model = configs.ai_config_sample.highlight_model
filter_trash_model = configs.ai_config_sample.filter_trash_model
faiss_deep = configs.ai_config_sample.faiss_deep
chunk_threshold = configs.ai_config_sample.chunk_threshold
EMBEDDING_DIM = configs.ai_config_sample.EMBEDDING_DIM
N_LIST = configs.ai_config_sample.N_LIST
N_PROBE = configs.ai_config_sample.N_PROBE
POST_PROCESSING_FLAG = configs.ai_config_sample.POST_PROCESSING_FLAG


SERVER_HOST = configs.server_config_sample.SERVER_HOST
SERVER_PORT = configs.server_config_sample.SERVER_PORT
SEARCH_MODE = configs.server_config_sample.SEARCH_MODE
db_conn_name = configs.server_config_sample.db_conn_name

group_username = configs.telegram_config_sample.group_username
specific_topic_id = configs.telegram_config_sample.specific_topic_id

openai.api_key = configs.keys_sample.openai_api_key
openrouter_api_key = configs.keys_sample.openrouter_api_key
API_ID = configs.keys_sample.API_ID
API_HASH = configs.keys_sample.API_HASH
SESSION_STRING = configs.keys_sample.SESSION_STRING

main_paths_config = Path('configs/main_paths_config.py')
ai_config = Path('configs/ai_config.py')
server_config = Path('configs/server_config.py')
telegram_config = Path('configs/telegram_config.py')
keys = Path('configs/keys.py')

try:
    if main_paths_config.exists():
        import configs.main_paths_config

        if hasattr(configs.main_paths_config, 'DATA_PATH'):
            DATA_PATH = configs.main_paths_config.DATA_PATH

        if hasattr(configs.main_paths_config, 'DATABASE_PATH'):
            DATABASE_PATH = configs.main_paths_config.DATABASE_PATH

        if hasattr(configs.main_paths_config, 'FAISS_PATH'):
            FAISS_PATH = configs.main_paths_config.FAISS_PATH
except Exception as e:
    print(e)

try:
    if ai_config.exists():
        import configs.ai_config

        if hasattr(configs.ai_config, 'max_processing_message_count'):
            max_processing_message_count = configs.ai_config.max_processing_message_count

        if hasattr(configs.ai_config, 'faiss_model'):
            faiss_model = configs.ai_config.faiss_model

        if hasattr(configs.ai_config, 'analyze_query_model'):
            analyze_query_model = configs.ai_config.analyze_query_model

        if hasattr(configs.ai_config, 'highlight_model'):
            highlight_model = configs.ai_config.highlight_model

        if hasattr(configs.ai_config, 'filter_trash_model'):
            filter_trash_model = configs.ai_config.filter_trash_model

        if hasattr(configs.ai_config, 'sort_model'):
            sort_model = configs.ai_config.sort_model

        if hasattr(configs.ai_config, 'faiss_deep'):
            faiss_deep = configs.ai_config.faiss_deep

        if hasattr(configs.ai_config, 'chunk_threshold'):
            chunk_threshold = configs.ai_config.chunk_threshold

        if hasattr(configs.ai_config, 'EMBEDDING_DIM'):
            EMBEDDING_DIM = configs.ai_config.EMBEDDING_DIM

        if hasattr(configs.ai_config, 'N_LIST'):
            N_LIST = configs.ai_config.N_LIST

        if hasattr(configs.ai_config, 'N_PROBE'):
            N_PROBE = configs.ai_config.N_PROBE

        if hasattr(configs.ai_config, 'POST_PROCESSING_FLAG'):
            POST_PROCESSING_FLAG = configs.ai_config.POST_PROCESSING_FLAG
except Exception as e:
    print(e)

try:
    if server_config.exists():
        import configs.server_config

        if hasattr(configs.server_config, 'SERVER_PORT'):
            SERVER_PORT = configs.server_config.SERVER_PORT

        if hasattr(configs.server_config, 'SERVER_HOST'):
            SERVER_HOST = configs.server_config.SERVER_HOST

        if hasattr(configs.server_config, 'SEARCH_MODE'):
            SEARCH_MODE = configs.server_config.SEARCH_MODE

        if hasattr(configs.server_config, 'db_conn_name'):
            db_conn_name = configs.server_config.db_conn_name
except Exception as e:
    print(e)

try:
    if telegram_config.exists():
        import configs.telegram_config

        if hasattr(configs.telegram_config, 'group_username'):
            group_username = configs.telegram_config.group_username

        if hasattr(configs.telegram_config, 'specific_topic_id'):
            specific_topic_id = configs.telegram_config.specific_topic_id
except Exception as e:
    print(e)

try:
    if keys.exists():
        import configs.keys

        if hasattr(configs.keys, 'openai_api_key'):
            openai_api_key = configs.keys.openai_api_key
            openai.api_key = openai_api_key

        if hasattr(configs.keys, 'openrouter_api_key'):
            openrouter_api_key = configs.keys.openrouter_api_key

        if hasattr(configs.keys, 'API_ID'):
            API_ID = configs.keys.API_ID

        if hasattr(configs.keys, 'API_HASH'):
            API_HASH = configs.keys.API_HASH

        if hasattr(configs.keys, 'SESSION_STRING'):
            SESSION_STRING = configs.keys.SESSION_STRING
except Exception as e:
    print(e)

relevant_path = os.path.join(DATA_PATH, "relevant")
relevant_media_path = os.path.join(relevant_path, "media")
relevant_text_path = os.path.join(relevant_path, "text")

tg_dump_path = os.path.join(DATA_PATH, "tg_dump")
tg_dump_media_path = os.path.join(tg_dump_path, "media")
tg_dump_text_path = os.path.join(tg_dump_path, "text")
tg_dump_last_dump_path = os.path.join(tg_dump_path, "last_dump")

faiss_content_index_path = os.path.join(FAISS_PATH, "cv_faiss_c.index")
faiss_content_metadata_path = os.path.join(FAISS_PATH, "cv_metadata_c.json")
faiss_content_chunk_vectors_path = os.path.join(FAISS_PATH, "faiss_chunks_c.npy")

faiss_author_index_path = os.path.join(FAISS_PATH, "cv_faiss_a.index")
faiss_author_metadata_path = os.path.join(FAISS_PATH, "cv_metadata_a.json")
faiss_author_chunk_vectors_path = os.path.join(FAISS_PATH, "faiss_chunks_a.npy")

db_path = os.path.join(DATABASE_PATH, "database")
db_schema_path = os.path.join(db_path, "dbschema")

from deep_translator import GoogleTranslator

#from ui.server.app import logger
from utils.logger import setup_logger

from utils.misc_func import capitalize_sentence
from utils.abbr_f import abbr_capitalize,abbr1,abbr_trans,trans1

#from configs.cfg import index_path, metadata_path, chunk_path, embedding_model, embedding_dim, threshold, db_conn_name, \
#    N_PROBE, EMBEDDING_MODE, POST_PROCESSING_FLAG, PRE_PROCESSING_LLM_FLAG

logger = setup_logger("preprocess") #from backend.search_FAISS import logger
#logger = None

# MAIN
def query_preprocess_faiss(user_query: str ) -> str:
    logger.info(f"Rewriting for query: '{user_query}'")
    
    #user_query=capitalize_sentence(user_query)
    # translate using google
    user_query=translate_sentence(user_query)
    #user_query=abbr_capitalize(user_query,abbr1)
    #user_query=abbr_trans(user_query)
    logger.info(f"Rewrited: '{user_query}'")

def init_logger(l):
    global logger
    logger=l


def translate_sentence(user_query):
    #translator = GoogleTranslator(source='ru', target='en', api_key=api_key)
    translator = GoogleTranslator(source='ru', target='en')
    user_query=translator.translate(user_query)
    return user_query



from openai import OpenAI
from configs.cfg import openrouter_api_key

config1 = {
  "openrouter": {
    "model": "google/gemma-3-27b-it",
    "api_url": "https://openrouter.ai/api/v1",
    "max_tokens": 100000,
    "temperature": 0.1
  },
}

def _request_simple(r)
    openrouter_config = config1['openrouter']
    print(openrouter_config)
    
    # Get API key 
    #api_key = os.getenv('OPENROUTER_API_KEY')
    #if not api_key:
    #    raise ValueError("OPENROUTER_API_KEY environment variable not set")
    api_key=openrouter_api_key
    
    # Initialize OpenAI client with OpenRouter endpoint
    client = OpenAI(
        api_key=api_key,
        base_url=openrouter_config['api_url']
    )
    
    try:
        response = client.chat.completions.create(
            model=openrouter_config['model'],
            messages=[
                {
                    "role": "user",
                    "content": translation_config['prompt_template'].format(text=text)
                }
            ],
            max_tokens=openrouter_config['max_tokens'],
            temperature=openrouter_config['temperature']
        )
        
        result = response.choices[0].message.content.strip()
        return result

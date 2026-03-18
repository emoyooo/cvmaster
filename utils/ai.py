from openai import OpenAI
from .config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text: str, model="text-embedding-3-small"):
    if not text:
        return None
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

def generate_ai_response(prompt: str, system_prompt: str = "You are a helpful career assistant."):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
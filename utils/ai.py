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

def analyze_answer(question, answer, rubric=None):
    prompt = f"""
    Analyze this interview answer:
    Question: {question}
    User Answer: {answer}
    Evaluation Rubric: {rubric if rubric else "Standard interview quality"}

    Return ONLY a JSON:
    {{
        "rating": "Poor/Fair/Good",
        "red_flags": ["list of flags or empty"],
        "feedback_for_report": "short technical critique"
    }}
    """
    response = generate_ai_response(prompt, system_prompt="You are an expert interviewer analyzer.")
    try:
        import re, json
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        return json.loads(json_match.group(0))
    except:
        return {"rating": "Fair", "red_flags": [], "feedback_for_report": "Analysis failed"}
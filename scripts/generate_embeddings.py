import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ai import get_embedding
from utils.db import supabase

TABLES_TO_PROCESS = {
    "occupations": ["title", "description"],
    "skills": ["name", "description"],
    "cv_rules": ["rule_name", "description"],
    "technical_questions": ["question_text"],
    "behavioral_questions": ["question_template"],
    "action_verbs": ["verb"],
    "ats_keywords": ["keyword"],
    "soft_skill_indicators": ["green_flags", "red_flags"]
}

def fill_all_embeddings():
    for table_name, columns in TABLES_TO_PROCESS.items():
        print(f"Checking table: {table_name}...")
        
        rows = supabase.table(table_name).select("*").is_("embedding", "null").execute()
        
        if not rows.data:
            print(f"No empty embeddings in {table_name}.")
            continue
            
        print(f"Processing {len(rows.data)} rows in {table_name}...")
        
        for row in rows.data:
            text_to_embed = " ".join([str(row[col]) for col in columns if row.get(col)])
            
            if text_to_embed:
                vector = get_embedding(text_to_embed)
                supabase.table(table_name).update({"embedding": vector}).eq("id", row["id"]).execute()
                print(f"Updated row {row['id']}")

if __name__ == "__main__":
    fill_all_embeddings()
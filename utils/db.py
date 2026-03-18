from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def search_knowledge_base(rpc_name: str, query_embedding: list, match_threshold=0.5, match_count=3):
    response = supabase.rpc(
        rpc_name,
        {
            'query_embedding': query_embedding,
            'match_threshold': match_threshold,
            'match_count': match_count
        }
    ).execute()
    return response.data
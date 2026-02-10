"from supabase import create_client, Client
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SupabaseManager:
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            supabase_url = os.environ.get(\"SUPABASE_URL\")
            supabase_key = os.environ.get(\"SUPABASE_ANON_KEY\")
            
            if not supabase_url or not supabase_key:
                raise ValueError(\"Supabase credentials not configured\")
            
            cls._instance = create_client(supabase_url, supabase_key)
            logger.info(\"Supabase client initialized\")
        
        return cls._instance


def get_supabase() -> Client:
    return SupabaseManager.get_client()
"

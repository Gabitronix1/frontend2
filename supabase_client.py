
from supabase import create_client

SUPABASE_URL = "https://kvenozirujsvjrsmpqhu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2ZW5vemlydWpzdmpyc21wcWh1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTM1NDM0MiwiZXhwIjoyMDYwOTMwMzQyfQ.PHyDwgHefWFTQkNKPRZ-Xdj7v6cg6j9oZ3VWTbseKLc"

def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

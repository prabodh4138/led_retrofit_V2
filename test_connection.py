from utils.db import supabase

result = (
    supabase
    .table("profiles")
    .select("*")
    .limit(1)
    .execute()
)

print(result.data)
from utils.db import supabase

result = (
    supabase
    .table("vw_pending_matrix")
    .select("*")
    .limit(5)
    .execute()
)

print(result.data)
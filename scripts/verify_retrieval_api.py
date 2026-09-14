"""Verify live retrieval endpoint via HTTP."""
import json
import urllib.parse
import urllib.request

queries = [
    ("How does Kazuha Elemental Mastery scaling work?", 3),
    ("What artifacts are recommended for Arlecchino?", 3),
    ("What is the best weapon for Kaedehara Kazuha?", 3),
    ("How much ER does Xiangling need?", 3),
    ("What materials does Mavuika need to farm?", 3),
]

print("================================================================")
print("  Verifying Live Production Retrieval API (GET /api/knowledge/retrieve)")
print("================================================================")

for q, k in queries:
    params = urllib.parse.urlencode({"q": q, "top_k": k})
    url = f"http://127.0.0.1:8000/api/knowledge/retrieve?{params}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        print(f"\nQuery: '{data['query']}'")
        print(f"Status: {data['retrieval_status']} | Latency: {data['latency_ms']}ms | Candidates: {data['total_candidates_examined']}")
        print(f"Signals: mode={data['signals']['retrieval_mode']}, chars={data['signals']['detected_characters']}")
        for item in data["items"]:
            print(f"  #{item['rank']} [{item['chunk_id']}]")
            print(f"     Score: {item['composite_score']} (Lex: {item['lexical_score']}, Sem: {item['semantic_score']})")
            print(f"     Tier: {item['authority_tier']} | Freshness: {item['freshness_status']} | Method: {item['retrieval_method']}")
            print(f"     Source: {item['source']} -> {item['canonical_url']}")
            print(f"     Heading: {item['section_heading']}")

print("\n================================================================")
print("  ALL LIVE RETRIEVAL ENDPOINT CHECKS PASSED SUCCESSFULLY!")
print("================================================================")

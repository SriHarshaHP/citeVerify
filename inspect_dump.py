import json

with open("tests/stress_test_report_dump.json", "r", encoding="utf-8-sig") as f:
    data = json.load(f)

print("Document name:", data.get("document_name"))
print("Total claims:", data.get("total_claims"))
print("Citation style:", data.get("citation_style"))
print("Orphan references count:", len(data.get("orphan_references", [])))
print("Unmatched markers:", data.get("unmatched_markers"))

cards = data.get("claim_cards", [])
print(f"Total claim cards: {len(cards)}")

for c in cards:
    cid = c.get("claim_id")
    text = c.get("verbatim_text")
    markers = c.get("citation_markers")
    pairs = c.get("citations", [])
    primary_v = c.get("primary_verdict", {})
    label = primary_v.get("label")
    pair_refs = [p.get("reference_key") for p in pairs]
    print(f"[{cid}] (markers={markers}) -> refs={pair_refs} | verdict={label}")
    print(f"    Text: {text}")
    print(f"    Reason: {primary_v.get('reason')}")
    print()

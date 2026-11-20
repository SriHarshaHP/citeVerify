import json

with open("tests/stress_test_report_dump.json", "r", encoding="utf-8-sig") as f:
    d = json.load(f)

cards = d.get("claim_cards", [])
print(f"Total claim cards: {len(cards)}\n")

all_sentences = []
for idx, c in enumerate(cards):
    claim = c.get("claim", {})
    cid = claim.get("id")
    v_text = claim.get("verbatim_text")
    markers = claim.get("citation_markers")
    has_cit = claim.get("has_citation")
    pv = c.get("primary_verdict", {})
    label = pv.get("label")
    pairs = c.get("pairs", [])
    ref_keys = [p.get("reference_key") for p in pairs]
    flags = pv.get("flags", [])
    all_sentences.append(v_text)
    print(f"[{cid}] markers={markers} has_cit={has_cit} refs={ref_keys} verdict={label} flags={flags}")
    print(f"    Text: {v_text}")
    print(f"    Reason: {pv.get('reason')}")
    sub = claim.get("atomic_subclaims", [])
    if len(sub) > 1:
        print(f"    Subclaims ({len(sub)}):")
        for sc in sub:
            print(f"      - {sc.get('subclaim_id')}: {sc.get('text')}")
    print()

with open("tests/reconstructed_stress_test_doc.txt", "w", encoding="utf-8") as out:
    out.write("\n\n".join(all_sentences))
print("Saved all sentences to tests/reconstructed_stress_test_doc.txt")

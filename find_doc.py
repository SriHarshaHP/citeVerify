import json

full_transcript_path = r"C:\Users\harsh\.gemini\antigravity\brain\5fb5d309-cde6-41ba-91fd-b848ddb919da\.system_generated\logs\transcript_full.jsonl"

with open(full_transcript_path, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if "Esteva" in line and "FINAL ACCURACY CORRECTION" not in line:
            obj = json.loads(line)
            content = str(obj.get("content", ""))
            print(f"Match at line {idx}, step_index={obj.get('step_index')}, type={obj.get('type')}, len={len(content)}")
            if len(content) > 500:
                print("Content preview:")
                print(content[:500])
                with open("tests/stress_test_doc_extracted.txt", "w", encoding="utf-8") as out:
                    out.write(content)
                print("Saved content to tests/stress_test_doc_extracted.txt")

import os
import re

pages_dir = r"c:\Users\dhruv\.gemini\antigravity-ide\scratch\f1_dw\f1-race-intelligence\logic\other_pages"
jury_dir = r"c:\Users\dhruv\.gemini\antigravity-ide\scratch\f1_dw\f1-race-intelligence\jury\pages"

def audit_file(fpath):
    print(f"\n=== Auditing {os.path.basename(fpath)} ===")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for sqlite3
    if "sqlite" in content:
        print("  [!] Uses sqlite!")
        for i, line in enumerate(content.splitlines(), 1):
            if "sqlite" in line:
                print(f"      L{i}: {line.strip()}")

    # Check for get_local_data or query_snowflake calls
    calls = re.findall(r'(get_local_data\([^)]+\)|query_snowflake\([^)]+\)|get_local_json\([^)]+\))', content)
    if calls:
        print("  Data calls:", set(calls))

    # Check for target_ or hardcoded sensitive columns
    target_matches = re.findall(r'\[["\'](target_[^"\']+|is_win|is_podium|finish_position)["\']\]', content)
    if target_matches:
        print("  Direct column lookups:", set(target_matches))

print("--- AUDITING OTHER_PAGES ---")
for p in sorted(os.listdir(pages_dir)):
    if p.endswith(".py"):
        audit_file(os.path.join(pages_dir, p))

print("\n--- AUDITING JURY PAGES ---")
for p in sorted(os.listdir(jury_dir)):
    if p.endswith(".py"):
        audit_file(os.path.join(jury_dir, p))

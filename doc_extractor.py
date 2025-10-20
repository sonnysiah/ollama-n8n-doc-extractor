import os
import time
import json
import csv
import re
import fitz  # pip install pymupdf
from ollama import Client  # pip install ollama

SOURCE_DIR = r"c:\test\source"
OUTPUT_DIR = r"c:\test\output"
OLLAMA = Client(host="http://127.0.0.1:11434")
MODEL = "deepseek-r1"

FIELDS = ["DATE", "INVOICE", "CUSTOMER ID", "SALESPERSON", "TO", "TOTAL"]

# -------- PDF --------
def extract_text_from_pdf(path):
    text = []
    with fitz.open(path) as doc:
        for page in doc:
            text.append(page.get_text())
    return "\n".join(text).strip()

# -------- LLM --------
def build_prompt(doc_text):
    return f"""
Extract ONLY these fields from the document:

- DATE
- INVOICE
- CUSTOMER ID
- SALESPERSON
- TO
- TOTAL

Rules:
- Output only valid JSON.
- Keys must be exactly: DATE, INVOICE, CUSTOMER ID, SALESPERSON, TO, TOTAL.
- If missing, use "".
- No explanation, no markdown, no code fences.

Document Content:
\"\"\"{doc_text}\"\"\"
""".strip()

def call_llm(prompt):
    res = OLLAMA.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
    content = res["message"]["content"]

    # Remove <think>...</think>
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    # Remove code fences
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE)

    # Try parsing whole string
    try:
        json.loads(content)
        return content
    except:
        pass

    # Fallback: extract first {...} block
    m = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if m:
        return m.group(0)

    # Last fallback: return empty schema
    return json.dumps({k: "" for k in FIELDS}, ensure_ascii=False)

# -------- Schema --------
def coerce_to_schema(json_text):
    try:
        data = json.loads(json_text)
    except:
        data = {}
    if not isinstance(data, dict):
        data = {}

    normalized = {}
    for key in FIELDS:
        val = ""
        if key in data:
            val = data.get(key, "")
        else:
            for k in data.keys():
                if k.strip().lower() == key.lower():
                    val = data[k]
                    break
        if isinstance(val, (list, dict)):
            val = json.dumps(val, ensure_ascii=False)
        elif val is None:
            val = ""
        normalized[key] = str(val)
    return normalized

# -------- Save --------
def save_results(file_path, record):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base = os.path.splitext(os.path.basename(file_path))[0]

    json_path = os.path.join(OUTPUT_DIR, f"{base}_JSON.json")
    csv_path  = os.path.join(OUTPUT_DIR, f"{base}_CSV.csv")

    with open(json_path, "w", encoding="utf-8") as jf:
        jf.write(json.dumps(record, ensure_ascii=False, indent=2))

    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(record)

    print(f"✓ Saved: {json_path} and {csv_path}")

# -------- Main --------
def process_file(pdf_path):
    print(f"→ Processing: {os.path.basename(pdf_path)}")
    doc_text = extract_text_from_pdf(pdf_path)
    prompt = build_prompt(doc_text)
    raw = call_llm(prompt)
    record = coerce_to_schema(raw)
    save_results(pdf_path, record)

def main():
    print(f"🚀 Watching folder: {SOURCE_DIR}")
    seen = set()
    while True:
        for name in os.listdir(SOURCE_DIR):
            if not name.lower().endswith(".pdf"):
                continue
            full = os.path.join(SOURCE_DIR, name)
            if full in seen:
                continue
            try:
                process_file(full)
                seen.add(full)
            except Exception as e:
                print(f"! Error on {name}: {e}")
        time.sleep(3)

if __name__ == "__main__":
    main()

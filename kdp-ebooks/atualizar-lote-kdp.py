#!/usr/bin/env python3
"""Atualiza status do tracker do lote KDP.
Uso:
  python atualizar-lote-kdp.py <book_id> <status>
Status sugeridos: ready | uploading | uploaded | in_review | live
"""
import json
import sys
from pathlib import Path
from datetime import datetime

STATUS_FILE = Path(__file__).resolve().parent / "kdp-pronto-upload" / "_lote-status.json"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    book_id = sys.argv[1].strip()
    new_status = sys.argv[2].strip()

    if not STATUS_FILE.exists():
        print(f"❌ Tracker não encontrado: {STATUS_FILE}")
        sys.exit(1)

    data = json.loads(STATUS_FILE.read_text())
    found = False
    for b in data.get("books", []):
        if b.get("id") == book_id:
            b["status"] = new_status
            b["updated_at"] = datetime.now().isoformat()
            found = True
            print(f"✅ {book_id} -> {new_status}")
            break

    if not found:
        print(f"❌ Livro não encontrado: {book_id}")
        sys.exit(1)

    STATUS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

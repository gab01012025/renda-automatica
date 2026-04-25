#!/usr/bin/env python3
"""Inicializa e imprime a ordem de publicacao do lote KDP."""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "kdp-pronto-upload"
STATUS_FILE = BASE / "_lote-status.json"

ORDEM = [
    # Comecar com maior ticket e maior demanda B2B
    "copywriting-ia-pt",
    "chatgpt-advogados-pt",
    "chatgpt-imobiliaria-pt",
    "excel-ia-pt",
    # Mercado EN grande, fica no fim para ajustar descricao depois de validar 4 PT
    "receitas-low-carb-ia-en",
]


def load_meta(book_id):
    p = BASE / book_id / "metadata.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def init_status():
    data = {
        "created_at": datetime.now().isoformat(),
        "books": [],
        "notes": [
            "Status por livro: ready -> uploaded -> in_review -> live",
            "KDP demora tipicamente 24-72h para review",
        ],
    }

    for i, book_id in enumerate(ORDEM, 1):
        meta = load_meta(book_id)
        if not meta:
            continue
        folder = BASE / book_id
        data["books"].append({
            "rank": i,
            "id": book_id,
            "status": "ready",
            "title": meta.get("titulo", book_id),
            "price": meta.get("preco"),
            "language": meta.get("lingua"),
            "files": {
                "epub": str(folder / "manuscript.epub"),
                "cover": str(folder / "cover.jpg"),
                "metadata": str(folder / "metadata.json"),
            },
        })
    return data


def print_runbook(data):
    print("\nKDP lote iniciado. Ordem recomendada:\n")
    for b in data["books"]:
        print(f"{b['rank']}. {b['title']}  |  ${b['price']}  |  {b['language']}  | status={b['status']}")

    first = next((b for b in data["books"] if b["status"] == "ready"), None)
    if first:
        print("\nPROXIMO LIVRO PARA SUBIR AGORA:")
        print(first["title"])
        print(f"EPUB: {first['files']['epub']}")
        print(f"COVER: {first['files']['cover']}")
        print(f"META:  {first['files']['metadata']}")

    print("\nChecklist rapido no KDP:")
    print("1) Details: copiar titulo/subtitulo/descricao/keywords de metadata.json")
    print("2) Content: subir manuscript.epub + cover.jpg")
    print("3) Pricing: usar preco definido no metadata.json")
    print("4) Publish e passar para o proximo da lista")


def main():
    data = init_status()
    STATUS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"✅ Tracker criado em: {STATUS_FILE}")
    print_runbook(data)


if __name__ == "__main__":
    main()

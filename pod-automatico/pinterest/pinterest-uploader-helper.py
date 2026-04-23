#!/usr/bin/env python3
"""
Pinterest Pin Upload Helper — Gera copy-paste pronto para cada pin
Use: python3 pinterest-uploader-helper.py
"""
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_FILE = ROOT / "pinterest" / "pins-pinterest-upload.csv"
PINS_DIR = ROOT / "pinterest" / "pins-prontos"

def main():
    if not CSV_FILE.exists():
        print(f"❌ CSV não encontrado: {CSV_FILE}")
        return
    
    with open(CSV_FILE) as f:
        reader = list(csv.DictReader(f))
    
    print("\n" + "="*80)
    print("📌 PINTEREST PIN UPLOAD HELPER")
    print("="*80)
    print(f"\n✅ {len(reader)} pins prontos para upload\n")
    
    for i, row in enumerate(reader, 1):
        print(f"\n{'='*80}")
        print(f"📌 PIN {i}/30 — {row['Title'][:60]}")
        print(f"{'='*80}")
        
        print(f"\n🖼️  IMAGEM:")
        print(f"   📁 {row['Local file']}\n")
        
        print(f"📝 TÍTULO (copy-cola):")
        print(f"   {row['Title']}\n")
        
        print(f"📄 DESCRIÇÃO (copy-cola):")
        print(f"   {row['Description']}\n")
        
        print(f"🔗 LINK (copy-cola):")
        print(f"   {row['Link']}\n")
        
        print(f"📂 PASTA (seleciona):")
        print(f"   {row['Pinterest board']}\n")
        
        print(f"🏷️  TAGS (copy-cola):")
        print(f"   {row['Keywords']}\n")
        
        # Menu
        resp = input("➡️  Digite 'ok' para continuar, 's' para saltar, 'q' para sair: ").lower()
        if resp == 'q':
            print("\n✅ Upload parado.")
            break
        elif resp == 's':
            print("⏭️  Saltando este pin...")

    print("\n" + "="*80)
    print("💡 DICA: Gera 5-7 pins/dia máximo (Pinterest penaliza spam)")
    print("="*80)

if __name__ == "__main__":
    main()

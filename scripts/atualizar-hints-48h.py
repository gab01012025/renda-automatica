#!/usr/bin/env python3
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YT_DIR = ROOT / "youtube-faceless"
UPLOADED = YT_DIR / "_uploaded.json"
VIDEOS = YT_DIR / "videos"
HINTS = YT_DIR / "_performance-hints.json"
TOKEN_FILE = YT_DIR / "token.json"

STOPWORDS = {
    "a", "o", "e", "de", "do", "da", "dos", "das", "um", "uma", "para", "com", "em",
    "na", "no", "nos", "nas", "que", "como", "por", "ao", "às", "as", "os", "se", "vs",
    "chatgpt", "ia", "gpt", "2026", "sobre", "mais", "menos", "você", "tu", "teu", "sua",
}


def parse_ts(text):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            pass
    return None


def load_uploaded():
    if not UPLOADED.exists():
        return []
    data = json.loads(UPLOADED.read_text())
    return data.get("videos", [])


def read_title_for_file(file_name):
    meta = VIDEOS / file_name.replace(".mp4", ".json")
    if meta.exists():
        try:
            return json.loads(meta.read_text()).get("titulo", file_name)
        except Exception:
            return file_name
    return file_name


def get_views_by_ids(video_ids):
    if not TOKEN_FILE.exists() or not video_ids:
        return {}
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except Exception:
        return {}

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), ["https://www.googleapis.com/auth/youtube.readonly"])
        service = build("youtube", "v3", credentials=creds)
        views = {}
        for i in range(0, len(video_ids), 50):
            ids = ",".join(video_ids[i:i + 50])
            resp = service.videos().list(part="statistics,snippet", id=ids).execute()
            for item in resp.get("items", []):
                vid = item.get("id")
                st = item.get("statistics", {})
                views[vid] = int(st.get("viewCount", 0))
        return views
    except Exception:
        return {}


def token_words(titles):
    words = []
    for t in titles:
        for w in re.findall(r"[a-zA-Zà-ÿÀ-Ÿ0-9]{3,}", (t or "").lower()):
            if w not in STOPWORDS:
                words.append(w)
    return words


def main():
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=48)

    vids = []
    for v in load_uploaded():
        ts = parse_ts(v.get("ts", ""))
        if ts is None or ts >= cutoff:
            vids.append(v)

    if not vids:
        hints = {
            "generated_at": now.isoformat(),
            "top_videos": [],
            "winning_words": ["truque", "segredo", "erro", "rápido", "passo"],
            "source": "fallback",
        }
        HINTS.write_text(json.dumps(hints, ensure_ascii=False, indent=2))
        print("ℹ️ Sem vídeos recentes; hints fallback atualizados.")
        return

    ids = [v.get("video_id") for v in vids if v.get("video_id")]
    views = get_views_by_ids(ids)

    ranked = []
    for v in vids:
        vid = v.get("video_id")
        title = read_title_for_file(v.get("file", ""))
        ranked.append({
            "video_id": vid,
            "file": v.get("file"),
            "url": v.get("url"),
            "title": title,
            "views": views.get(vid, 0),
            "ts": v.get("ts"),
        })

    ranked.sort(key=lambda x: x.get("views", 0), reverse=True)
    top = ranked[:5]
    words = token_words([x["title"] for x in top])
    common = [w for w, _ in Counter(words).most_common(12)]

    hints = {
        "generated_at": now.isoformat(),
        "source": "youtube_api" if views else "local_recent",
        "top_videos": top,
        "winning_words": common or ["truque", "segredo", "erro", "rápido", "passo"],
    }
    HINTS.write_text(json.dumps(hints, ensure_ascii=False, indent=2))
    print(f"✅ Hints 48h atualizados: {HINTS}")


if __name__ == "__main__":
    main()

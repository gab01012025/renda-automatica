#!/usr/bin/env python3
"""
YouTube Shorts Uploader (YouTube Data API v3)

Setup (1ª vez):
  1. Vai a https://console.cloud.google.com/ → cria projeto
  2. APIs & Services → Library → "YouTube Data API v3" → ENABLE
  3. APIs & Services → Credentials → Create Credentials → OAuth client ID
     - Tipo: Desktop app
     - Download JSON → guarda como `client_secret.json` nesta pasta
  4. OAuth consent screen → External + adiciona TEU email como Test user
  5. Corre: python upload-youtube.py --auth
     → abre browser, faz login, autoriza → gera token.json

Uso:
  python upload-youtube.py --auth           # 1ª vez, cria token
  python upload-youtube.py <video.mp4>      # upload 1 vídeo
  python upload-youtube.py --pending [N]    # upload N vídeos novos da pasta videos/
  python upload-youtube.py --status         # mostra uploads feitos
"""
import json, sys, os, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIDEOS = ROOT / "videos"
AI_GIRLS_VIDEOS = ROOT.parent / "ai-girls-shorts" / "videos"

def _all_video_dirs():
    dirs = [VIDEOS]
    if AI_GIRLS_VIDEOS.exists():
        dirs.append(AI_GIRLS_VIDEOS)
    return dirs
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_FILE = ROOT / "token.json"
UPLOADED_FILE = ROOT / "_uploaded.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def load_uploaded():
    if UPLOADED_FILE.exists():
        return json.loads(UPLOADED_FILE.read_text())
    return {"videos": []}


def save_uploaded(data):
    UPLOADED_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def get_credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                print(f"❌ Falta {CLIENT_SECRET}")
                print("   Cria OAuth client ID em https://console.cloud.google.com/")
                print("   Tipo: Desktop app. Download JSON e guarda como client_secret.json")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
        print(f"✅ Token guardado em {TOKEN_FILE}")
    return creds


def get_service():
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=get_credentials())


def upload_video(video_path: Path, meta: dict):
    """Upload de 1 vídeo. meta tem titulo/descricao/tags."""
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    service = get_service()
    titulo = meta.get("titulo", video_path.stem)[:100]
    descricao = meta.get("descricao", "")
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    # Hashtag #Shorts ajuda algoritmo
    if "#Shorts" not in descricao and "#shorts" not in descricao:
        descricao = (descricao or "") + "\n\n#Shorts"

    body = {
        "snippet": {
            "title": titulo,
            "description": descricao,
            "tags": tags[:15],
            "categoryId": "28",  # Science & Technology
            "defaultLanguage": "pt",
            "defaultAudioLanguage": "pt",
        },
        "status": {
            "privacyStatus": "public",   # public | unlisted | private
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    req = service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    retries = 0
    while response is None:
        try:
            status, response = req.next_chunk()
        except HttpError as e:
            retries += 1
            if retries > 3:
                raise
            print(f"   ⚠️  HTTP {e.resp.status}, retry {retries}/3")
            time.sleep(5)
    return response  # contém id do vídeo


def upload_one(video_path: Path):
    meta_path = video_path.with_suffix(".json")
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"titulo": video_path.stem}
    print(f"📤 Upload: {video_path.name}")
    print(f"   Título: {meta.get('titulo', video_path.stem)[:60]}")
    try:
        resp = upload_video(video_path, meta)
        vid = resp.get("id")
        url = f"https://youtube.com/shorts/{vid}"
        print(f"   ✅ {url}")
        state = load_uploaded()
        done = set(v["file"] for v in state["videos"])
        if video_path.name not in done:
            state["videos"].append({
                "file": video_path.name,
                "video_id": vid,
                "url": url,
                "ts": time.strftime("%Y-%m-%d %H:%M"),
            })
            save_uploaded(state)
        return vid, url
    except Exception as e:
        print(f"   ❌ {e}")
        return None, None


def upload_pending(n=1):
    state = load_uploaded()
    done = set(v["file"] for v in state["videos"])
    candidatos = []
    for d in _all_video_dirs():
        candidatos.extend(p for p in d.glob("*.mp4") if p.name not in done)
    candidatos.sort()
    if not candidatos:
        print("✅ Nenhum vídeo pendente.")
        return
    alvo = candidatos[:n]
    print(f"📺 {len(alvo)} vídeos a publicar (de {len(candidatos)} pendentes)\n")
    for v in alvo:
        vid, url = upload_one(v)
        if vid:
            state["videos"].append({
                "file": v.name,
                "video_id": vid,
                "url": url,
                "ts": time.strftime("%Y-%m-%d %H:%M"),
            })
            save_uploaded(state)
        # rate limit safe
        time.sleep(5)
    print(f"\n✅ Concluído. Total uploads: {len(state['videos'])}")


def status():
    state = load_uploaded()
    todos = []
    for d in _all_video_dirs():
        todos.extend(d.glob("*.mp4"))
    done = set(v["file"] for v in state["videos"])
    print(f"📺 {len(todos)} vídeos gerados")
    print(f"✅ {len(state['videos'])} já no YouTube")
    print(f"⏳ {len(todos) - len(done)} pendentes\n")
    for v in state["videos"][-5:]:
        print(f"  • {v['ts']}  {v['url']}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)
    if "--auth" in args:
        get_credentials()
        print("✅ Auth OK")
    elif "--status" in args:
        status()
    elif "--pending" in args:
        idx = args.index("--pending")
        n = int(args[idx + 1]) if len(args) > idx + 1 and args[idx + 1].isdigit() else 1
        upload_pending(n)
    else:
        upload_one(Path(args[0]))

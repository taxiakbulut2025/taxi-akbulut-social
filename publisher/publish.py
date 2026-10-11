"""Taxi Akbulut Social-Autopilot – Publisher.

Läuft in GitHub Actions. Veröffentlicht fällige Posts aus queue/ auf
Instagram (und optional auf der Facebook-Seite) über die Meta Graph API.

Regeln:
- Ein Post ist fällig, wenn publish_at (Europe/Berlin) erreicht ist.
- Höchstens ein Post pro Kalendertag, damit ein Rückstand nach einer
  Pause nicht auf einmal rausgeht.
- Bilder werden über raw.githubusercontent.com öffentlich bereitgestellt
  (Instagram verlangt eine öffentliche JPEG-Adresse).
"""
import datetime as dt
import glob
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

API = "https://graph.facebook.com/" + os.environ.get("GRAPH_API_VERSION", "v25.0")
TZ = ZoneInfo("Europe/Berlin")
TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
IG_USER_ID = os.environ.get("IG_USER_ID", "")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
STATE_FILE = "state.json"
MAX_ATTEMPTS = 3


def graph(method, path, params, token=None):
    params = dict(params, access_token=token or TOKEN)
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Graph API {path}: {e.code} {e.read().decode(errors='replace')}")


def publish_instagram(image_url, caption):
    c = graph("POST", f"{IG_USER_ID}/media", {"image_url": image_url, "caption": caption})
    cid = c["id"]
    for _ in range(20):
        s = graph("GET", cid, {"fields": "status_code"})
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram-Container fehlerhaft: {s}")
        time.sleep(6)
    p = graph("POST", f"{IG_USER_ID}/media_publish", {"creation_id": cid})
    return p["id"]


def publish_instagram_story(image_url):
    c = graph("POST", f"{IG_USER_ID}/media", {"image_url": image_url, "media_type": "STORIES"})
    cid = c["id"]
    for _ in range(20):
        s = graph("GET", cid, {"fields": "status_code"})
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Story-Container fehlerhaft: {s}")
        time.sleep(6)
    return graph("POST", f"{IG_USER_ID}/media_publish", {"creation_id": cid})["id"]


VERSION = API.rsplit("/", 1)[-1]


def wait_container(cid, tries=100, pause=6):
    for _ in range(tries):
        s = graph("GET", cid, {"fields": "status_code,status"})
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Container fehlerhaft: {s}")
        time.sleep(pause)
    raise RuntimeError("Container nach Wartezeit nicht fertig")


def publish_instagram_reel(video_path, caption):
    """Reel per Direkt-Upload (keine öffentliche Video-URL nötig)."""
    c = graph("POST", f"{IG_USER_ID}/media", {
        "media_type": "REELS", "upload_type": "resumable",
        "caption": caption, "share_to_feed": "true"})
    cid = c["id"]
    with open(video_path, "rb") as f:
        data = f.read()
    req = urllib.request.Request(
        f"https://rupload.facebook.com/ig-api-upload/{VERSION}/{cid}", data=data, method="POST",
        headers={"Authorization": f"OAuth {TOKEN}", "offset": "0", "file_size": str(len(data))})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Reel-Upload: {e.code} {e.read().decode(errors='replace')}")
    wait_container(cid)
    return graph("POST", f"{IG_USER_ID}/media_publish", {"creation_id": cid})["id"]


_PAGE_TOKEN = None


def page_token():
    """Facebook-Seiten verlangen einen Seiten-Zugangsschlüssel; er wird aus dem Systemnutzer-Token abgeleitet."""
    global _PAGE_TOKEN
    if _PAGE_TOKEN is None:
        _PAGE_TOKEN = graph("GET", FB_PAGE_ID, {"fields": "access_token"}).get("access_token") or TOKEN
    return _PAGE_TOKEN


def publish_facebook_video(video_path, caption):
    boundary = "----akbulut" + str(int(time.time()))
    with open(video_path, "rb") as f:
        video = f.read()
    parts = []
    for k, v in (("access_token", page_token()), ("description", caption)):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="source"; filename="reel.mp4"\r\n'
                  'Content-Type: video/mp4\r\n\r\n').encode() + video + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        f"https://graph-video.facebook.com/{VERSION}/{FB_PAGE_ID}/videos", data=b"".join(parts), method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read()).get("id")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Facebook-Video: {e.code} {e.read().decode(errors='replace')}")


def publish_facebook(image_url, caption):
    p = graph("POST", f"{FB_PAGE_ID}/photos", {"url": image_url, "caption": caption}, token=page_token())
    return p.get("post_id") or p.get("id")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def check_access():
    """Testlauf: prüft Secrets und Berechtigungen, ohne etwas zu veröffentlichen."""
    lines = [f"Testlauf {dt.datetime.now(TZ).isoformat(timespec='minutes')}"]
    try:
        ig = graph("GET", IG_USER_ID, {"fields": "username"})
        lines.append(f"OK Instagram erreichbar: @{ig.get('username')}")
        limit = graph("GET", f"{IG_USER_ID}/content_publishing_limit", {})
        lines.append(f"OK Posting-Berechtigung, Kontingent: {limit.get('data')}")
        if FB_PAGE_ID:
            page = graph("GET", FB_PAGE_ID, {"fields": "name"})
            lines.append(f"OK Facebook-Seite erreichbar: {page.get('name')}")
    except Exception as e:  # noqa: BLE001
        lines.append(f"FEHLER: {str(e)[:500]}")
    print("\n".join(lines))
    with open("testlauf.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    if not (TOKEN and IG_USER_ID):
        print("META_ACCESS_TOKEN oder IG_USER_ID fehlt (GitHub Secrets).")
        sys.exit(1)
    if DRY_RUN:
        check_access()
    now = dt.datetime.now(TZ)
    today = now.date().isoformat()
    state = load_state()
    if state.get("last_published_date") == today:
        print("Heute wurde bereits gepostet – nichts zu tun.")
        return

    for path in sorted(glob.glob("queue/*.json")):
        with open(path, encoding="utf-8") as f:
            post = json.load(f)
        due = dt.datetime.strptime(post["publish_at"], "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if due > now:
            continue
        is_reel = post.get("type") == "reel"
        caption = post["caption"][:2200]
        print(f"Fällig: {path} ({'Reel' if is_reel else 'Bild'})")
        if DRY_RUN:
            print("DRY_RUN – nichts veröffentlicht.\n" + caption)
            return
        try:
            # Bereits erledigte Kanäle (z. B. nach einem Teilfehler) werden nicht doppelt gepostet.
            if is_reel:
                if post.get("instagram", True) and not post.get("instagram_id"):
                    post["instagram_id"] = publish_instagram_reel(post["video"], caption)
                    save_json(path, post)
                if FB_PAGE_ID and post.get("facebook", True) and not post.get("facebook_id"):
                    post["facebook_id"] = publish_facebook_video(post["video"], caption)
                    save_json(path, post)
            else:
                image_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{post['image']}"
                if post.get("instagram", True) and not post.get("instagram_id"):
                    post["instagram_id"] = publish_instagram(image_url, caption)
                    save_json(path, post)
                # Story vor Facebook, damit ein Facebook-Fehler die Story nicht blockiert.
                if post.get("story") and post.get("story_image") and not post.get("story_id") \
                        and not post.get("story_error"):
                    story_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{post['story_image']}"
                    try:
                        post["story_id"] = publish_instagram_story(story_url)
                    except Exception as e:  # noqa: BLE001 – Story-Fehler stoppt den Feed-Post nicht
                        post["story_error"] = str(e)[:500]
                    save_json(path, post)
                if FB_PAGE_ID and post.get("facebook", True) and not post.get("facebook_id"):
                    post["facebook_id"] = publish_facebook(image_url, caption)
                    save_json(path, post)
            post.update(published_at=now.isoformat(timespec="minutes"))
            post.pop("last_error", None)
            os.makedirs("published", exist_ok=True)
            save_json(path, post)
            shutil.move(path, os.path.join("published", os.path.basename(path)))
            state["last_published_date"] = today
            save_json(STATE_FILE, state)
            print(f"Veröffentlicht: {path}")
        except Exception as e:  # noqa: BLE001
            post["attempts"] = post.get("attempts", 0) + 1
            post["last_error"] = str(e)[:1000]
            save_json(path, post)
            if post["attempts"] >= MAX_ATTEMPTS:
                os.makedirs("failed", exist_ok=True)
                shutil.move(path, os.path.join("failed", os.path.basename(path)))
            print(f"FEHLER: {e}")
            sys.exit(1)
        return  # höchstens ein Post pro Lauf
    print("Kein fälliger Post.")


if __name__ == "__main__":
    main()

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
YT_TEST = os.environ.get("YT_TEST", "false").lower() == "true"
YT_UPDATE_ID = os.environ.get("YT_UPDATE_ID", "").strip()
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


LOCATION_ID = os.environ.get("LOCATION_ID") or FB_PAGE_ID


def create_container(params, post):
    """Legt einen Container an – mit Standort-Markierung, falls möglich.
    Lehnt Instagram den Standort ab, wird ohne Standort weitergemacht und der Grund gespeichert."""
    if LOCATION_ID and not post.get("location_error"):
        try:
            return graph("POST", f"{IG_USER_ID}/media", dict(params, location_id=LOCATION_ID))["id"]
        except RuntimeError as e:
            post["location_error"] = str(e)[:300]
    return graph("POST", f"{IG_USER_ID}/media", params)["id"]


def publish_instagram(image_url, caption, post):
    params = {"image_url": image_url, "caption": caption}
    if post.get("alt_text"):
        params["alt_text"] = post["alt_text"][:1000]
    cid = create_container(params, post)
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


def publish_instagram_reel(video_path, caption, post):
    """Reel per Direkt-Upload (keine öffentliche Video-URL nötig)."""
    cid = create_container({
        "media_type": "REELS", "upload_type": "resumable",
        "caption": caption, "share_to_feed": "true"}, post)
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


# ---------------- YouTube (nur Reels/Videos) ----------------
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN", "")
YT_ENABLED = bool(YT_CLIENT_ID and YT_CLIENT_SECRET and YT_REFRESH_TOKEN)


def yt_token():
    data = urllib.parse.urlencode({"client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
                                   "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=data), timeout=60) as r:
            return json.loads(r.read())["access_token"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"YouTube-Token: {e.code} {e.read().decode(errors='replace')}")


# YouTube-SEO: Themen-Profile mit Tags (max. ~480 Zeichen), 3 Hashtags (erscheinen über dem Titel)
# und einer Leistungszeile. Nur belegte Fakten (siehe redaktion/fakten.md).
YT_PROFILES = {
    "flughafen": {
        "hashtags": ["#FlughafenStuttgart", "#Flughafentransfer", "#Tübingen"],
        "service": "✈️ Flughafentransfer Tübingen – Flughafen Stuttgart (STR) zum Festpreis, 60 Min. Wartezeit inklusive",
        "tags": ["Flughafentransfer Stuttgart", "Airport Shuttle Stuttgart", "Taxi Flughafen Stuttgart",
                 "Flughafen Stuttgart", "Flughafentransfer Tübingen", "Taxi Tübingen Flughafen",
                 "Flughafenshuttle Stuttgart", "Airport Transfer Stuttgart", "Taxi Reutlingen Flughafen",
                 "Flughafentaxi", "Festpreis Flughafen", "STR Airport"]},
    "krankenfahrten": {
        "hashtags": ["#Krankenfahrt", "#Tübingen", "#TaxiTübingen"],
        "service": "🏥 Krankenfahrten mit Direktabrechnung bei gesetzlichen Krankenkassen, Abholung an der Wohnungstür",
        "tags": ["Krankenfahrt Tübingen", "Krankenfahrten", "Taxi Krankenkasse", "Dialysefahrt",
                 "Krankenfahrt Reutlingen", "Taxi zum Arzt", "Krankentaxi Tübingen", "Fahrt zur Reha",
                 "Bestrahlungsfahrt", "Direktabrechnung Krankenkasse", "Taxi Tübingen"]},
    "medizinkurier": {
        "hashtags": ["#Medizinkurier", "#Kurierdienst", "#Tübingen"],
        "service": "🧊 Medizinischer Kurierdienst mit Kühlboxen für Praxen, Labore und Kliniken",
        "tags": ["Medizinkurier Tübingen", "Medizinischer Kurierdienst", "Laborkurier", "Kurier Blutproben",
                 "Medikamentenkurier", "Kurierdienst Tübingen", "Kurierdienst Reutlingen", "Laborproben Transport",
                 "Kurier Praxis", "Kühltransport Medizin"]},
    "event-shuttle": {
        "hashtags": ["#EventShuttle", "#Tübingen", "#VKlasse"],
        "service": "🎉 Event-Shuttle für Hochzeit, Firmenfeier, Messe und Abiball – Mercedes V-Klasse bis 7 Gäste",
        "tags": ["Event Shuttle Tübingen", "Shuttleservice Tübingen", "Hochzeit Shuttle", "Firmenfeier Shuttle",
                 "Messe Shuttle Stuttgart", "Shuttle Reutlingen", "VIP Shuttle", "Mercedes V-Klasse mit Fahrer",
                 "Weihnachtsfeier Shuttle", "Abiball Shuttle", "Gruppenfahrt Tübingen"]},
    "vip-shuttle": {
        "hashtags": ["#VIPShuttle", "#Chauffeurservice", "#Stuttgart"],
        "service": "🚐 VIP-Shuttle mit Chauffeur – Mercedes-Benz V-Klasse bis 7 Fahrgäste, auf Vorbestellung",
        "tags": ["VIP Shuttle Stuttgart", "VIP Shuttle Tübingen", "Chauffeurservice Stuttgart",
                 "Chauffeurservice Tübingen", "Mercedes V-Klasse mit Fahrer", "Limousinenservice Stuttgart",
                 "Business Shuttle", "Fahrservice Reutlingen", "Event Shuttle", "Shuttleservice Stuttgart",
                 "Fahrer mieten"]},
    "chauffeurservice": {
        "hashtags": ["#Chauffeurservice", "#Stuttgart", "#Tübingen"],
        "service": "🎩 Chauffeurservice für Geschäftsreisende – Mercedes E- und V-Klasse mit Fahrer, auf Vorbestellung",
        "tags": ["Chauffeurservice Stuttgart", "Chauffeurservice Tübingen", "Chauffeur Reutlingen",
                 "Limousinenservice Stuttgart", "Business Chauffeur", "Fahrservice Stuttgart", "Fahrer mieten",
                 "Mercedes mit Fahrer", "VIP Fahrservice", "Geschäftsreise Stuttgart", "Premium Fahrdienst"]},
    "ferntaxi": {
        "hashtags": ["#Ferntaxi", "#Langstrecke", "#Tübingen"],
        "service": "🛣️ Ferntaxi und Langstrecke deutschlandweit – Preis vorab online",
        "tags": ["Ferntaxi Tübingen", "Taxi Langstrecke", "Ferntaxi Stuttgart", "Taxi Fernfahrt",
                 "Taxi deutschlandweit", "Taxi Festpreis Langstrecke", "Ferntaxi Reutlingen", "Taxi Tübingen",
                 "Überführungsfahrt Taxi"]},
    "taxi-tuebingen": {
        "hashtags": ["#TaxiTübingen", "#Tübingen", "#Taxi"],
        "service": "🚕 Taxi Tübingen – Familienbetrieb seit 1986, Fahrten online buchen und bezahlen",
        "tags": ["Taxi Tübingen", "Taxi Reutlingen", "Taxiunternehmen Tübingen", "Taxi bestellen Tübingen",
                 "Taxi online buchen", "Mietwagen mit Fahrer Tübingen", "Taxi Kusterdingen", "Taxi Rottenburg",
                 "Taxi Akbulut"]},
}
YT_KEYWORDS = [("flughafen", "flughafen"), ("airport", "flughafen"), ("kranken", "krankenfahrten"),
               ("medizinkurier", "medizinkurier"), ("vipshuttle", "vip-shuttle"), ("eventshuttle", "event-shuttle"),
               ("chauffeur", "chauffeurservice"), ("ferntaxi", "ferntaxi")]
YT_BASE_TAGS = ["Taxi Akbulut", "Taxi Akbulut Tübingen"]


def yt_topic(post, caption):
    for key in (post.get("yt_topic"), post.get("category")):
        if key in YT_PROFILES:
            return key
    low = caption.lower()
    for word, topic in YT_KEYWORDS:
        if "#" + word in low or word in low.split("\n")[0]:
            return topic
    return "taxi-tuebingen"


def yt_tags(*lists, limit=480):
    out, seen, size = [], set(), 0
    for tag in (t for lst in lists for t in lst):
        key = tag.lower().replace(" ", "")
        cost = len(tag) + (2 if " " in tag else 0) + 1
        if key in seen or size + cost > limit:
            continue
        out.append(tag)
        seen.add(key)
        size += cost
    return out


def yt_metadata(post, caption):
    import re
    prof = YT_PROFILES[yt_topic(post, caption)]
    # Instagram-Hashtagzeile entfernen, Hashtags als Tags (CamelCase -> Wörter) weiterverwenden
    ig_tags = [re.sub(r"(?<=[a-zäöü])(?=[A-ZÄÖÜ])", " ", t.lstrip("#")) for t in re.findall(r"#\w+", caption)]
    body = "\n".join(l for l in caption.strip().split("\n") if not re.fullmatch(r"(\s*#\w+)+\s*", l)).strip()
    body = body.replace("taxi-akbulut.de (Link im Profil)", "https://www.taxi-akbulut.de")
    first = body.split("\n")[0].strip()
    title = post.get("yt_title") or (first if len(first) <= 95 else first[:92].rsplit(" ", 1)[0] + " …")
    info = "\n".join([
        "━━━━━━━━━━━━━━━━━━━━",
        prof["service"],
        "📞 Telefon: +49 7071 1438591",
        "🌐 Online buchen & bezahlen: https://www.taxi-akbulut.de",
        "📍 Taxi Akbulut, Schwärzlocher Str. 37, 72070 Tübingen",
        "🗺️ Einsatzgebiet: Tübingen, Reutlingen, Stuttgart, Flughafen Stuttgart (STR) – Fernfahrten deutschlandweit",
        "👨‍👩‍👦 Familienbetrieb seit 1986, in zweiter Generation",
    ])
    desc = post.get("yt_description") or f"{body}\n\n{info}\n\n{' '.join(prof['hashtags'])}"
    tags = yt_tags(post.get("yt_tags", []), prof["tags"], ig_tags, YT_BASE_TAGS)
    return {"snippet": {"title": title[:100], "description": desc[:4900], "tags": tags,
                        "categoryId": "2", "defaultLanguage": "de", "defaultAudioLanguage": "de"},
            "status": {"privacyStatus": post.get("yt_privacy", "public"), "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": bool(post.get("ki", False))}}


def publish_youtube(video_path, post, caption):
    token = yt_token()
    with open(video_path, "rb") as f:
        data = f.read()
    meta = json.dumps(yt_metadata(post, caption)).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=meta, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(data))})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            upload_url = r.headers["Location"]
        up = urllib.request.Request(upload_url, data=data, method="PUT",
                                    headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"})
        with urllib.request.urlopen(up, timeout=600) as r:
            return json.loads(r.read())["id"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"YouTube-Upload: {e.code} {e.read().decode(errors='replace')}")


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
        if LOCATION_ID:
            try:
                loc = graph("GET", LOCATION_ID, {"fields": "name,location"})
                if loc.get("location"):
                    lines.append(f"OK Standort-Markierung möglich: {loc.get('name')} {loc['location']}")
                else:
                    lines.append(f"HINWEIS Seite {loc.get('name')} hat keine Adresse – Posts erscheinen ohne Standort")
            except Exception as e:  # noqa: BLE001
                lines.append(f"HINWEIS Standort nicht prüfbar: {str(e)[:200]}")
    except Exception as e:  # noqa: BLE001
        lines.append(f"FEHLER: {str(e)[:500]}")
    if YT_ENABLED:
        try:
            tok = yt_token()
            req = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
                                         headers={"Authorization": f"Bearer {tok}"})
            with urllib.request.urlopen(req, timeout=60) as r:
                items = json.loads(r.read()).get("items", [])
            lines.append("OK YouTube-Kanal erreichbar: " + (items[0]["snippet"]["title"] if items else "KEIN KANAL GEFUNDEN"))
        except Exception as e:  # noqa: BLE001
            lines.append(f"FEHLER YouTube: {str(e)[:400]}")
    else:
        lines.append("HINWEIS YouTube nicht eingerichtet (Secrets YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN fehlen)")
    print("\n".join(lines))
    with open("testlauf.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def youtube_test_upload():
    """Test-Upload: lädt das bereits gepostete Reel vom 17.10. PRIVAT auf YouTube hoch."""
    src = "published/2026-10-17-reel-gelandet.json"
    lines = [f"YouTube-Testupload {dt.datetime.now(TZ).isoformat(timespec='minutes')}"]
    try:
        with open(src, encoding="utf-8") as f:
            post = json.load(f)
        post["yt_privacy"] = "private"
        if YT_UPDATE_ID:
            meta = yt_metadata(post, post["caption"])
            meta["id"] = YT_UPDATE_ID
            req = urllib.request.Request(
                "https://www.googleapis.com/youtube/v3/videos?part=snippet,status",
                data=json.dumps(meta).encode(), method="PUT",
                headers={"Authorization": f"Bearer {yt_token()}", "Content-Type": "application/json; charset=UTF-8"})
            try:
                with urllib.request.urlopen(req, timeout=60):
                    pass
            except urllib.error.HTTPError as e:
                raise RuntimeError(f"YouTube-Update: {e.code} {e.read().decode(errors='replace')}")
            lines.append(f"OK Titel/Beschreibung/Tags aktualisiert (privat): https://youtu.be/{YT_UPDATE_ID}")
        else:
            vid = publish_youtube(post["video"], post, post["caption"])
            lines.append(f"OK Video privat hochgeladen: https://youtu.be/{vid}")
    except Exception as e:  # noqa: BLE001
        lines.append(f"FEHLER YouTube-Testupload: {str(e)[:600]}")
    print("\n".join(lines))
    with open("testlauf.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def fetch_remote_videos():
    """Lädt Reel-Videos, die nur als URL vorliegen (Feld video_url), ins Repository (Ordner reels/)."""
    for path in sorted(glob.glob("queue/*.json")):
        with open(path, encoding="utf-8") as f:
            post = json.load(f)
        url, target = post.get("video_url"), post.get("video")
        if not (url and target) or os.path.exists(target):
            continue
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": "taxi-akbulut-social"})
            with urllib.request.urlopen(req, timeout=300) as r, open(target, "wb") as out:
                shutil.copyfileobj(r, out)
            print(f"Video geladen: {target} ({os.path.getsize(target)} Bytes)")
        except Exception as e:  # noqa: BLE001
            print(f"Video konnte nicht geladen werden ({target}): {e}")


def main():
    fetch_remote_videos()
    if not (TOKEN and IG_USER_ID):
        print("META_ACCESS_TOKEN oder IG_USER_ID fehlt (GitHub Secrets).")
        sys.exit(1)
    if YT_TEST:
        youtube_test_upload()
        return
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
                    post["instagram_id"] = publish_instagram_reel(post["video"], caption, post)
                    save_json(path, post)
                if FB_PAGE_ID and post.get("facebook", True) and not post.get("facebook_id"):
                    post["facebook_id"] = publish_facebook_video(post["video"], caption)
                    save_json(path, post)
                # YouTube zuletzt; ein YouTube-Fehler stoppt Instagram/Facebook nicht.
                if YT_ENABLED and post.get("youtube", True) and not post.get("youtube_id") \
                        and not post.get("youtube_error"):
                    try:
                        post["youtube_id"] = publish_youtube(post["video"], post, caption)
                    except Exception as e:  # noqa: BLE001
                        post["youtube_error"] = str(e)[:500]
                    save_json(path, post)
            else:
                image_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{post['image']}"
                if post.get("instagram", True) and not post.get("instagram_id"):
                    post["instagram_id"] = publish_instagram(image_url, caption, post)
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

"""Taxi Akbulut Social-Autopilot – Publisher.

Läuft in GitHub Actions. Veröffentlicht fällige Posts aus queue/ auf
Instagram (und optional auf der Facebook-Seite) über die Meta Graph API,
Reels zusätzlich auf YouTube, ausgewählte Themen auf der LinkedIn-Unternehmensseite.

Regeln:
- Ein Post ist fällig, wenn publish_at (Europe/Berlin) erreicht ist.
- Höchstens ein Post pro Kalendertag und Spur (Feld "lane": main = Standard,
  story = reine Story, extra = Zusatz-Beitrag), damit ein Rückstand nach
  einer Pause nicht auf einmal rausgeht.
- "type": "story" veröffentlicht nur eine Instagram-Story (story_image),
  optional mit "user_tags": ["benutzername", …].
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


def publish_instagram_story(image_url, usernames=None):
    params = {"image_url": image_url, "media_type": "STORIES"}
    if usernames:
        params["user_tags"] = json.dumps([{"username": u.lstrip("@")} for u in usernames])
    c = graph("POST", f"{IG_USER_ID}/media", params)
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
        "niche": "chauffeur",
        "hashtags": ["#EventShuttle", "#Tübingen", "#VKlasse"],
        "service": "🎉 Event-Shuttle für Hochzeit, Firmenfeier, Messe und Abiball – Mercedes V-Klasse bis 7 Gäste",
        "tags": ["Event Shuttle Tübingen", "Shuttleservice Tübingen", "Hochzeit Shuttle", "Firmenfeier Shuttle",
                 "Messe Shuttle Stuttgart", "Shuttle Reutlingen", "VIP Shuttle", "Mercedes V-Klasse mit Fahrer",
                 "Weihnachtsfeier Shuttle", "Abiball Shuttle", "Gruppenfahrt Tübingen"]},
    "chauffeurservice": {
        "niche": "chauffeur",
        "hashtags": ["#Chauffeurservice", "#ChauffeurserviceStuttgart", "#ChauffeurserviceTübingen"],
        "service": "🎩 Exklusiver Chauffeurservice – Mercedes-Benz E- und V-Klasse mit Fahrer, auf Vorbestellung",
        "tags": ["Exklusiver Chauffeurservice", "Chauffeurservice Stuttgart", "Chauffeurservice Tübingen",
                 "Chauffeurservice Reutlingen", "Mercedes V-Klasse mit Chauffeur", "Business Chauffeur",
                 "Fahrservice Stuttgart", "Chauffeur mieten", "Mercedes mit Fahrer", "Premium Fahrdienst",
                 "Geschäftsreise Stuttgart"]},
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
               ("medizinkurier", "medizinkurier"), ("vipshuttle", "chauffeurservice"), ("eventshuttle", "event-shuttle"),
               ("chauffeur", "chauffeurservice"), ("ferntaxi", "ferntaxi")]
# Zwei Nischen, klar getrennt: klassisches Taxi und exklusiver Chauffeurservice.
# Die Kern-Hashtags/Tags der jeweiligen Nische stehen in JEDEM Video dieser Nische.
# YouTube ignoriert ALLE Hashtags, wenn es mehr als 15 sind – daher Gesamtzahl begrenzt.
YT_BASE = {
    "taxi": {
        "tags": ["Taxi Tübingen", "Flughafentransfer Stuttgart", "Flughafentransfer Tübingen",
                 "Krankenfahrten Tübingen", "Ferntaxi", "Chauffeurservice", "Taxi Akbulut"],
        "hashtags": ["#TaxiTübingen", "#FlughafentransferStuttgart", "#FlughafentransferTübingen",
                     "#KrankenfahrtenTübingen", "#Ferntaxi", "#Chauffeurservice", "#TaxiAkbulut"],
        "area": "Tübingen, Reutlingen, Stuttgart, Flughafen Stuttgart (STR) – Fernfahrten deutschlandweit"},
    "chauffeur": {
        "tags": ["Chauffeurservice", "Exklusiver Chauffeurservice", "Chauffeurservice Tübingen",
                 "Chauffeurservice Stuttgart", "Chauffeurservice Reutlingen", "Taxi Akbulut"],
        "hashtags": ["#Chauffeurservice", "#ChauffeurserviceStuttgart", "#ChauffeurserviceTübingen",
                     "#ChauffeurserviceReutlingen", "#MercedesVKlasse", "#TaxiAkbulut"],
        "area": "Tübingen, Reutlingen, Stuttgart und Flughafen Stuttgart (STR)"},
}


def yt_topic(post, caption):
    alias = {"vip-shuttle": "chauffeurservice"}
    for key in (alias.get(post.get("yt_topic"), post.get("yt_topic")), post.get("category")):
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
    base = YT_BASE[prof.get("niche", "taxi")]
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
        "🗺️ Einsatzgebiet: " + base["area"],
        "👨‍👩‍👦 Familienbetrieb seit 1986, in zweiter Generation",
    ])
    hashtags = list(dict.fromkeys(prof["hashtags"] + base["hashtags"]))[:15]
    desc = post.get("yt_description") or f"{body}\n\n{info}\n\n{' '.join(hashtags)}"
    tags = yt_tags(post.get("yt_tags", []), base["tags"], prof["tags"], ig_tags, ["Taxi Akbulut Tübingen"])
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


# ---------------- LinkedIn-Unternehmensseite ----------------
# Zugang: entweder Refresh-Token (läuft ca. 1 Jahr) oder direkt ein Access-Token (läuft ca. 60 Tage).
LI_CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID", "")
LI_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
LI_REFRESH_TOKEN = os.environ.get("LINKEDIN_REFRESH_TOKEN", "")
LI_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LI_ORG_ID = os.environ.get("LINKEDIN_ORG_ID", "").strip()
LI_ENABLED = bool(LI_ORG_ID and (LI_ACCESS_TOKEN or (LI_CLIENT_ID and LI_CLIENT_SECRET and LI_REFRESH_TOKEN)))
LI_ORG = f"urn:li:organization:{LI_ORG_ID}"
# LinkedIn nur für Geschäftsfahrten: diese Themen gehen automatisch mit.
# Reels und alle anderen Themen nur mit "linkedin": true im Post; "linkedin": false schließt aus.
LI_CATEGORIES = {"ferntaxi", "flughafen", "event-shuttle"}  # Chauffeur nur V-Klasse über die LinkedIn-Spur
LI_RESERVED = set("\\|{}@[]()<>#*_~")
_LI_TOKEN = None


def li_version():
    """LinkedIn verlangt eine API-Version JJJJMM; drei Monate zurück ist immer noch gültig."""
    if os.environ.get("LINKEDIN_VERSION"):
        return os.environ["LINKEDIN_VERSION"]
    d = dt.date.today().replace(day=1)
    for _ in range(3):
        d = (d - dt.timedelta(days=1)).replace(day=1)
    return d.strftime("%Y%m")


def li_token(state=None):
    global _LI_TOKEN
    if _LI_TOKEN:
        return _LI_TOKEN
    if not (LI_CLIENT_ID and LI_CLIENT_SECRET and LI_REFRESH_TOKEN):
        _LI_TOKEN = LI_ACCESS_TOKEN
        return _LI_TOKEN
    data = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": LI_REFRESH_TOKEN,
                                   "client_id": LI_CLIENT_ID, "client_secret": LI_CLIENT_SECRET}).encode()
    req = urllib.request.Request("https://www.linkedin.com/oauth/v2/accessToken", data=data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LinkedIn-Token: {e.code} {e.read().decode(errors='replace')} "
                           "(Refresh-Token abgelaufen? Dann in LinkedIn neu erzeugen und Secret ersetzen.)")
    _LI_TOKEN = res["access_token"]
    if state is not None and res.get("refresh_token_expires_in"):
        until = dt.date.today() + dt.timedelta(seconds=int(res["refresh_token_expires_in"]))
        state["linkedin_refresh_token_expires"] = until.isoformat()
    return _LI_TOKEN


def li_request(method, path, body=None, raw=None, url=None, headers=None, timeout=120):
    """Aufruf der LinkedIn-REST-API. Gibt (JSON-Antwort, Header) zurück."""
    h = {"Authorization": f"Bearer {li_token()}", "LinkedIn-Version": li_version(),
         "X-Restli-Protocol-Version": "2.0.0"}
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    if url:  # Upload-Adressen: eigener Header-Satz
        h = {"Authorization": f"Bearer {li_token()}", "Content-Type": "application/octet-stream"}
    h.update(headers or {})
    req = urllib.request.Request(url or f"https://api.linkedin.com/rest/{path}", data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read()
            return (json.loads(text) if text.strip() else {}), r.headers
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LinkedIn {path or 'Upload'}: {e.code} {e.read().decode(errors='replace')[:600]}")


def li_wanted(post):
    if "linkedin" in post:
        return bool(post["linkedin"])
    return post.get("category") in LI_CATEGORIES


def li_caption(post, caption):
    """Instagram-Text für LinkedIn anpassen: klickbarer Link, max. 3 Hashtags, Sonderzeichen maskiert."""
    text = post.get("linkedin_caption") or caption
    text = text.replace("taxi-akbulut.de (Link im Profil)", "https://taxi-akbulut.de")
    text = text.replace(" (Link im Profil)", "")
    paras = text.rstrip().split("\n\n")
    last = paras[-1].split()
    if last and all(w.startswith("#") for w in last):
        paras[-1] = " ".join(last[:3])
    text = "\n\n".join(paras)
    out, i = [], 0
    while i < len(text):
        c = text[i]
        if c == "#" and i + 1 < len(text) and (text[i + 1].isalnum()) and (i == 0 or text[i - 1].isspace()):
            j = i + 1
            while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                j += 1
            tag = "".join("\\" + ch if ch in LI_RESERVED else ch for ch in text[i + 1:j])
            out.append("{hashtag|\\#|" + tag + "}")
            i = j
            continue
        out.append("\\" + c if c in LI_RESERVED else c)
        i += 1
    return "".join(out)[:3000]


def li_upload_image(path):
    res, _ = li_request("POST", "images?action=initializeUpload",
                        body={"initializeUploadRequest": {"owner": LI_ORG}})
    v = res["value"]
    with open(path, "rb") as f:
        li_request("PUT", "", raw=f.read(), url=v["uploadUrl"])
    return v["image"]


def li_upload_video(path):
    size = os.path.getsize(path)
    res, _ = li_request("POST", "videos?action=initializeUpload",
                        body={"initializeUploadRequest": {"owner": LI_ORG, "fileSizeBytes": size,
                                                          "uploadCaptions": False, "uploadThumbnail": False}})
    v = res["value"]
    etags = []
    with open(path, "rb") as f:
        for part in v["uploadInstructions"]:
            f.seek(part["firstByte"])
            chunk = f.read(part["lastByte"] - part["firstByte"] + 1)
            _, hdr = li_request("PUT", "", raw=chunk, url=part["uploadUrl"], timeout=600)
            etags.append(hdr.get("ETag", "").strip('"'))
    li_request("POST", "videos?action=finalizeUpload",
               body={"finalizeUploadRequest": {"video": v["video"], "uploadToken": v.get("uploadToken", ""),
                                               "uploadedPartIds": etags}})
    urn = urllib.parse.quote(v["video"], safe="")
    for _ in range(60):  # bis zu ca. 6 Minuten auf die Verarbeitung warten
        info, _ = li_request("GET", f"videos/{urn}")
        status = info.get("status")
        if status == "AVAILABLE":
            break
        if status == "PROCESSING_FAILED":
            raise RuntimeError(f"LinkedIn-Video: Verarbeitung fehlgeschlagen {info.get('processingFailureReason', '')}")
        time.sleep(6)
    return v["video"]


def publish_linkedin(post, caption):
    is_video = post.get("type") == "reel"
    if is_video:
        media = {"id": li_upload_video(post["video"]), "title": post.get("yt_title") or post.get("motiv", "Video")}
    else:
        media = {"id": li_upload_image(post["image"]), "altText": post.get("alt_text", "")[:4086]}
    body = {"author": LI_ORG, "commentary": li_caption(post, caption), "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "content": {"media": media}, "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False}
    _, hdr = li_request("POST", "posts", body=body)
    return hdr.get("x-restli-id") or hdr.get("x-linkedin-id") or "ok"


# Erster Kommentar unter jedem LinkedIn-Post: passender Link zur Website.
# Pro Post änderbar mit "linkedin_comment": "eigener Text" oder false (kein Kommentar).
LI_COMMENTS = {
    "ferntaxi": "Jetzt Ferntaxi buchen: https://www.taxi-akbulut.de/ferntaxi",
    "flughafen": "Jetzt Flughafentransfer buchen: https://www.taxi-akbulut.de/flughafentransfer-tuebingen",
    "event-shuttle": "Event-Shuttle anfragen: https://www.taxi-akbulut.de/event-shuttle-tuebingen",
    "chauffeurservice": "Chauffeurservice mit der V-Klasse buchen: https://www.taxi-akbulut.de/chauffeur-service-stuttgart",
    "medizinkurier": "Mehr zum medizinischen Kurierdienst: https://www.taxi-akbulut.de/blut-medikamententransport",
    "krankenfahrten": "Krankenfahrt buchen: https://www.taxi-akbulut.de/krankenfahrten-tuebingen",
    "taxi-tuebingen": "Taxi in Tübingen buchen: https://www.taxi-akbulut.de/taxi-tuebingen",
}


def li_comment_text(post):
    if "linkedin_comment" in post:
        return post["linkedin_comment"] or ""
    topic = post.get("category")
    if topic == "reel" or post.get("type") == "reel":
        topic = post.get("yt_topic") or topic
    return LI_COMMENTS.get(topic, "Jetzt online buchen: https://www.taxi-akbulut.de/buchen")


def li_comment_step(post, path):
    """Link-Kommentar unter den eigenen LinkedIn-Post setzen (einmalig, Fehler stoppt nichts)."""
    urn = post.get("linkedin_id", "")
    if not (LI_ENABLED and urn.startswith("urn:li:")) or post.get("linkedin_comment_id") \
            or post.get("linkedin_comment_error"):
        return
    text = li_comment_text(post)
    if not text:
        return
    try:
        _, hdr = li_request("POST", f"socialActions/{urllib.parse.quote(urn, safe='')}/comments",
                            body={"actor": LI_ORG, "object": urn, "message": {"text": text}})
        post["linkedin_comment_id"] = hdr.get("x-restli-id") or hdr.get("x-linkedin-id") or "ok"
        print(f"LinkedIn-Kommentar gesetzt: {text}")
    except Exception as e:  # noqa: BLE001
        post["linkedin_comment_error"] = str(e)[:500]
    save_json(path, post)


def report_li_comment_error(post, path):
    if post.get("linkedin_comment_error") and not post.get("linkedin_comment_error_reported"):
        post["linkedin_comment_error_reported"] = True
        save_json(path, post)
        print(f"FEHLER LinkedIn-Kommentar ({post.get('motiv', path)}): {post['linkedin_comment_error']}")
        sys.exit(1)


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
    if LI_ENABLED:
        try:
            st = {}
            li_token(st)
            lines.append(f"OK LinkedIn-Zugang gültig (API-Version {li_version()})"
                         + (f", Refresh-Token gültig bis {st['linkedin_refresh_token_expires']}"
                            if st.get("linkedin_refresh_token_expires") else ""))
            try:
                org, _ = li_request("GET", f"organizations/{LI_ORG_ID}")
                lines.append(f"OK LinkedIn-Seite erreichbar: {org.get('localizedName', LI_ORG_ID)}")
            except Exception as e:  # noqa: BLE001
                lines.append(f"HINWEIS LinkedIn-Seitenname nicht abrufbar (Posten kann trotzdem gehen): {str(e)[:200]}")
        except Exception as e:  # noqa: BLE001
            lines.append(f"FEHLER LinkedIn: {str(e)[:400]}")
    else:
        lines.append("HINWEIS LinkedIn nicht eingerichtet (Secrets LINKEDIN_ORG_ID und Zugang fehlen)")
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
        for url, target in ((post.get("video_url"), post.get("video")),
                            (post.get("yt_landscape_url"), post.get("yt_landscape"))):
            _fetch_video(url, target)


def _fetch_video(url, target):
        if not (url and target) or os.path.exists(target):
            return
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": "taxi-akbulut-social"})
            with urllib.request.urlopen(req, timeout=300) as r, open(target, "wb") as out:
                shutil.copyfileobj(r, out)
            print(f"Video geladen: {target} ({os.path.getsize(target)} Bytes)")
        except Exception as e:  # noqa: BLE001
            print(f"Video konnte nicht geladen werden ({target}): {e}")


def li_publish_step(post, path, caption, state):
    """LinkedIn zuletzt; ein LinkedIn-Fehler stoppt die anderen Kanäle nicht."""
    if not (LI_ENABLED and li_wanted(post)) or post.get("linkedin_id") or post.get("linkedin_error"):
        return
    if not post.get("instagram", True) and not post.get("facebook", True):
        # Reiner LinkedIn-Post: Fehler zählt als echter Fehlversuch (bis zu 3 Versuche, dann failed/).
        li_token(state)
        post["linkedin_id"] = publish_linkedin(post, caption)
        save_json(path, post)
        li_comment_step(post, path)
        return
    try:
        li_token(state)
        post["linkedin_id"] = publish_linkedin(post, caption)
    except Exception as e:  # noqa: BLE001
        post["linkedin_error"] = str(e)[:500]
    save_json(path, post)
    li_comment_step(post, path)


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
    blocked = False

    for path in sorted(glob.glob("queue/*.json")):
        with open(path, encoding="utf-8") as f:
            post = json.load(f)
        due = dt.datetime.strptime(post["publish_at"], "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if due > now:
            continue
        lane = post.get("lane", "main")
        lane_key = "last_published_date" if lane == "main" else f"last_{lane}_date"
        if state.get(lane_key) == today:
            blocked = True
            continue
        is_reel = post.get("type") == "reel"
        is_story = post.get("type") == "story"
        caption = post.get("caption", "")[:2200]
        print(f"Fällig: {path} ({'Reel' if is_reel else 'Story' if is_story else 'Bild'}, Spur {lane})")
        if DRY_RUN:
            print("DRY_RUN – nichts veröffentlicht.\n" + caption)
            return
        try:
            # Bereits erledigte Kanäle (z. B. nach einem Teilfehler) werden nicht doppelt gepostet.
            if is_story:
                if not post.get("story_id"):
                    story_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{post['story_image']}"
                    tags = post.get("user_tags") or []
                    try:
                        post["story_id"] = publish_instagram_story(story_url, tags)
                    except Exception as e:  # noqa: BLE001 – Markierung fehlerhaft: ohne Markierung posten
                        if not tags:
                            raise
                        post["user_tags_error"] = str(e)[:500]
                        post["story_id"] = publish_instagram_story(story_url)
                    save_json(path, post)
            elif is_reel:
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
                # Optionale 16:9-Fassung als normales YouTube-Video (eigener Titel, kein Short)
                if YT_ENABLED and post.get("yt_landscape") and not post.get("youtube_landscape_id") \
                        and not post.get("youtube_landscape_error"):
                    try:
                        lpost = dict(post, yt_title=post.get("yt_landscape_title") or post.get("yt_title"))
                        post["youtube_landscape_id"] = publish_youtube(post["yt_landscape"], lpost, caption)
                    except Exception as e:  # noqa: BLE001
                        post["youtube_landscape_error"] = str(e)[:500]
                    save_json(path, post)
                li_publish_step(post, path, caption, state)
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
                li_publish_step(post, path, caption, state)
            post.update(published_at=now.isoformat(timespec="minutes"))
            post.pop("last_error", None)
            os.makedirs("published", exist_ok=True)
            save_json(path, post)
            shutil.move(path, os.path.join("published", os.path.basename(path)))
            state[lane_key] = today
            save_json(STATE_FILE, state)
            print(f"Veröffentlicht: {path}")
            if post.get("linkedin_error") and not post.get("linkedin_error_reported"):
                # Instagram/Facebook sind raus; der rote Lauf meldet nur den LinkedIn-Fehler (kein erneutes Posten).
                post["linkedin_error_reported"] = True
                save_json(os.path.join("published", os.path.basename(path)), post)
                print(f"FEHLER LinkedIn ({post.get('motiv', path)}): {post['linkedin_error']}")
                sys.exit(1)
            report_li_comment_error(post, os.path.join("published", os.path.basename(path)))
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
    print("Heute wurde bereits gepostet – nichts zu tun." if blocked else "Kein fälliger Post.")


if __name__ == "__main__":
    main()

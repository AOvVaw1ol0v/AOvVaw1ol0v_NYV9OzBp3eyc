from flask import Flask, request
import json, time, os

app = Flask(__name__)

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def log_entry(text):
    with open("logs.txt", "a") as f:
        f.write(f"{time.ctime()} - {text}\n")

@app.route("/check", methods=["POST"])
def check():
    data = request.json
    hwid = data.get("hwid")

    if not hwid:
        return "MISSING_HWID", 400

    bans = load_json("bans.json")
    if hwid in bans:
        log_entry(f"BANNED - {hwid}")
        return "BANNED"

    whitelist = load_json("whitelist.json")
    info = whitelist.get(hwid)
    if info:
        expire = info.get("expire")
        if expire != "never" and time.time() > float(expire):
            log_entry(f"EXPIRED - {hwid}")
            return "EXPIRED"
        log_entry(f"AUTHORIZED - {hwid}")
        return "AUTHORIZED"
    else:
        log_entry(f"UNAUTHORIZED - {hwid}")
        return "UNAUTHORIZED"

@app.route("/redeem", methods=["POST"])
def redeem():
    data = request.json
    hwid = data.get("hwid")
    key = data.get("key")

    if not hwid or not key:
        return "MISSING_FIELDS", 400

    keys = load_json("keys.json")
    whitelist = load_json("whitelist.json")

    if key not in keys:
        return "INVALID_KEY"

    duration = keys[key]["duration"]
    expire = time.time() + duration if duration != "never" else "never"

    whitelist[hwid] = {
        "redeemed_key": key,
        "expire": expire
    }

    del keys[key]
    save_json("whitelist.json", whitelist)
    save_json("keys.json", keys)
    log_entry(f"KEY_REDEEMED - {hwid} | {key}")
    return "KEY_REDEEMED"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    key = data.get("key")
    duration = data.get("duration")

    if not key or duration is None:
        return "MISSING_FIELDS", 400

    if duration != "never":
        try:
            duration = int(duration)
        except:
            return "INVALID_DURATION", 400

    keys = load_json("keys.json")
    keys[key] = { "duration": duration }
    save_json("keys.json", keys)
    return "KEY_CREATED"

@app.route("/")
def root():
    return "Whitelist Server is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
  

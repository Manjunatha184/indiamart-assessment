import random, re, time

UA_STRINGS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)…",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3)…",
]

def slugify(txt): return re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")
def hdr(): return random.choice(UA_STRINGS)
def polite_sleep(): time.sleep(random.uniform(3, 6))

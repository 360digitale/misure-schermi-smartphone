"""Genera docs/index.html dal dataset GSMArena di bytecharts.

Uso: python build/build.py <cartella-dataset> [data-ultimo-aggiornamento-fonte]
"""
import collections
import datetime
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATE = os.path.join(HERE, "template.html")
OUT = os.path.join(ROOT, "docs", "index.html")

ANNO_MINIMO = 2020
MIN_RIGHE = 1000  # sotto questa soglia qualcosa è andato storto: non pubblicare

BRANDS = {"apple": "Apple", "google": "Google", "motorola": "Motorola", "nokia": "Nokia",
          "oneplus": "OnePlus", "oppo": "Oppo", "samsung": "Samsung", "sony": "Sony",
          "vivo": "vivo", "xiaomi": "Xiaomi", "honor": "Honor", "huawei": "Huawei",
          "realme": "Realme", "nothing": "Nothing", "tecno": "Tecno", "infinix": "Infinix",
          "zte": "ZTE", "asus": "Asus", "lenovo": "Lenovo", "tcl": "TCL"}
EXCL = re.compile(r"(\bPad\b|Pad\d|\bTab\b|Tab[ \d]|Tablet|iPad|Watch|\bBand\b|Buds|\bGear\b|\bFit\b|Vision Pro)", re.I)
STATUS = {"Available": "Disponibile", "Discontinued": "Fuori produzione", "Coming soon": "In arrivo"}
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July",
                                      "August", "September", "October", "November", "December"], 1)}
MESI = ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
        "settembre", "ottobre", "novembre", "dicembre"]


def year_of(s):
    m = re.search(r"(19|20)\d\d", s or "")
    return int(m.group(0)) if m else None


def sortdate(ann):
    m = re.match(r"(\d{4})(?:, (\w+))?(?: (\d+))?", ann or "")
    if not m:
        return 0
    y = int(m.group(1))
    mo = MONTHS.get(m.group(2) or "", 0)
    if m.group(2) and m.group(2).startswith("Q"):
        mo = {"Q1": 2, "Q2": 5, "Q3": 8, "Q4": 11}.get(m.group(2), 0)
    d = int(m.group(3) or 0)
    return y * 10000 + mo * 100 + d


def geom(diag, a, b):
    w, h = min(a, b), max(a, b)
    dpx = math.hypot(w, h)
    return round(diag * w / dpx * 25.4, 1), round(diag * h / dpx * 25.4, 1), round(dpx / diag)


def body(dim):
    def p(s):
        m = re.search(r"([\d.]+) x ([\d.]+) x ([\d.]+) mm", s or "")
        return [float(m.group(i)) for i in (1, 2, 3)] if m else None
    if "Unfolded" in (dim or ""):
        f = re.search(r"Folded:([^\n]*)", dim)
        return p(f.group(1)) if f else None
    return p(dim)


def brand_name(slug):
    key = slug.split("-")[0]
    return BRANDS.get(key, key.capitalize())


def load(root):
    rows, skipped = [], collections.Counter()
    for slug in sorted(os.listdir(root)):
        p = os.path.join(root, slug)
        if not os.path.isdir(p) or slug.startswith(".") or "-phones-" not in slug:
            continue
        brand = brand_name(slug)
        for m in os.listdir(p):
            f = os.path.join(p, m, "details.json")
            if not os.path.exists(f):
                continue
            try:
                with open(f, encoding="utf-8") as fh:
                    d = json.load(fh)["data"]
                s = d.get("specifications") or {}
            except Exception:
                skipped["file illeggibile"] += 1
                continue
            name = d.get("model") or m.replace("_", " ")
            L, D = s.get("Launch", {}), s.get("Display", {})
            y = year_of(L.get("Announced"))
            st = (L.get("Status") or "").split(".")[0].strip()
            if not y or y < ANNO_MINIMO:
                skipped["prima del %d" % ANNO_MINIMO] += 1
                continue
            if st not in STATUS:
                skipped["annullato/altro"] += 1
                continue
            if EXCL.search(name):
                skipped["tablet/smartwatch"] += 1
                continue
            ms = re.match(r"([\d.]+) inches", D.get("Size") or "")
            mr = re.match(r"(\d+) x (\d+) pixels", D.get("Resolution") or "")
            if not ms or not mr:
                skipped["dati schermo mancanti"] += 1
                continue
            diag = float(ms.group(1))
            a, b = int(mr.group(1)), int(mr.group(2))
            fold = "Foldable" in (D.get("Type") or "")
            if not fold and (diag >= 7.3 or diag < 3.5):
                skipped["tablet/non smartphone"] += 1
                continue
            w, h, ppi = geom(diag, a, b)
            bf = body(s.get("Body", {}).get("Dimensions"))
            if bf:
                bf = sorted(bf[:2], reverse=True) + [bf[2]]
            codes = re.sub(r"<[^>]+>", "", s.get("Misc", {}).get("Models") or "")
            base = dict(b=brand, m=name, y=y, ann=(L.get("Announced") or "").split(".")[0],
                        sd=sortdate(L.get("Announced")), st=STATUS[st], f=1 if fold else 0, body=bf,
                        c=[x.strip() for x in codes.split(",") if x.strip()])
            rows.append(dict(base, k="Principale" if fold else "", di=diag, rw=min(a, b), rh=max(a, b),
                             w=w, h=h, ppi=ppi))
            if fold:
                c = re.search(r"([\d.]+) inches, (\d+) x (\d+) pixels", D.get("Features") or "")
                if c:
                    cd = float(c.group(1))
                    ca, cb = int(c.group(2)), int(c.group(3))
                    cw, ch, cp = geom(cd, ca, cb)
                    rows.append(dict(base, k="Esterno", di=cd, rw=min(ca, cb), rh=max(ca, cb),
                                     w=cw, h=ch, ppi=cp))
    rows.sort(key=lambda r: (-r["sd"], r["b"], r["m"]))
    return rows, skipped


def data_it(d):
    return "%d %s %d" % (d.day, MESI[d.month], d.year)


def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: python build/build.py <cartella-dataset> [AAAA-MM-GG]")
    root = sys.argv[1]
    source_date = sys.argv[2] if len(sys.argv) > 2 else ""
    rows, skipped = load(root)
    models = {(r["b"], r["m"]) for r in rows}
    print("Righe:", len(rows), "- modelli:", len(models))
    print("Scartati:", dict(skipped))
    print("Per marca:", dict(collections.Counter(r["b"] for r in rows if r["k"] != "Esterno")))
    if len(rows) < MIN_RIGHE:
        sys.exit("Troppo pochi modelli (%d): la pagina non viene aggiornata." % len(rows))

    try:
        sd = data_it(datetime.date.fromisoformat(source_date[:10])) if source_date else "n.d."
    except ValueError:
        sd = source_date
    brands = sorted({r["b"] for r in rows}, key=str.lower)
    data = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(TEMPLATE, encoding="utf-8") as fh:
        html = fh.read()
    html = (html.replace("__DATA__", data)
                .replace("__SOURCE_DATE__", sd)
                .replace("__BRANDS__", ", ".join(brands))
                .replace("__UPDATED__", data_it(datetime.date.today())))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("Scritto", OUT, "(%d KB)" % (len(html) // 1024))


if __name__ == "__main__":
    main()

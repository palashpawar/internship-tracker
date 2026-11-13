"""Fill in square logos for applications that have a domain but no stored logo.

Usage: python3 make_logos.py in.json out.json [--force KEY ...]
Reads the tracker JSON ({applications: {...}}), and for each open application
without a data-URI logo, fetches the company's favicon and stores a 96x96 PNG
data URI in `logo`, so every logo renders the same size in every view.

- Icons with an opaque coloured background (full-bleed, e.g. Figma's black tile)
  are cropped square and fill the box edge to edge.
- Transparent or white-background icons are trimmed and centred on white with
  a small margin.
"""
import base64, io, json, sys, time, urllib.request
from PIL import Image, ImageChops, ImageStat

SIZE, INNER = 96, 84
CLOSED = {"rejected", "withdrawn"}


def fetch(domain, tries=3):
    for i in range(tries):
        try:
            return _fetch(domain)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(1 + i)


def _fetch(domain):
    url = f"https://www.google.com/s2/favicons?domain={domain}&sz=256"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGBA")


def is_full_bleed(im):
    w, h = im.size
    pts = [(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)]
    px = [im.getpixel(p) for p in pts]
    opaque = all(p[3] > 240 for p in px)
    whiteish = all(min(p[:3]) > 235 for p in px)
    return opaque and not whiteish


def square(im):
    on_white = Image.alpha_composite(Image.new("RGBA", im.size, "white"), im).convert("RGB")
    if max(ImageStat.Stat(on_white).stddev) < 2:
        return None  # flat colour tile with no mark (e.g. a blank brand swatch)
    if im.width < 24:
        return None  # generic globe / missing icon: keep the initials fallback
    if is_full_bleed(im):
        out = im.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    else:
        bg = Image.new("RGBA", im.size, "white")
        flat = Image.alpha_composite(bg, im).convert("RGB")
        diff = ImageChops.difference(flat, Image.new("RGB", flat.size, "white")).convert("L")
        box = diff.point(lambda v: 255 if v > 24 else 0).getbbox()  # ignore faint off-white halo
        if not box:
            return None
        flat = flat.crop(box)
        k = INNER / max(flat.size)  # scale up small icons too, so every mark fills the same box
        flat = flat.resize((max(1, round(flat.width * k)), max(1, round(flat.height * k))), Image.LANCZOS)
        out = Image.new("RGB", (SIZE, SIZE), "white")
        out.paste(flat, ((SIZE - flat.width) // 2, (SIZE - flat.height) // 2))
    buf = io.BytesIO()
    out.quantize(colors=64, method=Image.Quantize.MEDIANCUT).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    src, dst, *rest = sys.argv[1:]
    force = set(rest[1:]) if rest[:1] == ["--force"] else set()
    d = json.load(open(src))
    done, skipped = [], []
    for key, a in d["applications"].items():
        has = isinstance(a.get("logo"), str) and a["logo"].startswith("data:")
        if a.get("stage") in CLOSED or (has and key not in force) or not a.get("domain"):
            continue
        try:
            uri = square(fetch(a["domain"].replace("www.", "", 1)))
        except Exception:  # network or decode failure: leave the initials fallback
            uri = None
        if uri:
            a["logo"] = uri
            done.append(key)
        else:
            skipped.append(key)
    json.dump(d, open(dst, "w"), indent=1)
    print(f"logos added: {len(done)}; skipped: {skipped}")


if __name__ == "__main__":
    main()

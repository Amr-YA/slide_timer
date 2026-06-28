from PIL import Image, ImageGrab, ImageChops


# ── Hashing ───────────────────────────────────────────────────────────────────
HASH_SIZE = (64, 64)


def image_hash(image, size=HASH_SIZE):
    gray = image.convert("L").resize(size, Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    avg = sum(pixels) / len(pixels)
    bits = ["1" if p >= avg else "0" for p in pixels]
    return int("".join(bits), 2)


# ── Comparison ────────────────────────────────────────────────────────────────
MATCH_THRESHOLD = 10_000


def images_match(a, b, threshold=MATCH_THRESHOLD):
    if a.size != b.size:
        b = b.resize(a.size, Image.Resampling.LANCZOS)
    diff = ImageChops.difference(a, b)
    histogram = diff.convert("L").histogram()
    score = sum(value * (idx**2) for idx, value in enumerate(histogram))
    return score <= threshold


# ── Footer capture ────────────────────────────────────────────────────────────
def grab_footer():
    full = ImageGrab.grab()
    w, h = full.size
    return full.crop((w * 5 // 6, h * 5 // 6, w, h))


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_time(total_seconds):
    """Format seconds as MM:SS."""
    m, s = divmod(total_seconds, 60)
    return f"{m:02d}:{s:02d}"

"""Write Romanian text into a culture's L10N DataTables (cooked, unversioned UE5.1 assets) and pack a mod pak.

The FText source strings sit in the .uexp as FStrings; we swap them, then fix the two header fields that
depend on the .uexp length (export SerialSize, BulkDataStartOffset). Every output file is re-read and checked.

usage: patch_tables.py <culture> <extracted_l10n_dir> <out_dir>      e.g. it  extract/Pal/Content/L10N/it  build/it
  reads data/ro_strings.json (table, key, ro) produced by translate_all.py export"""
import json, re, struct, sys
from pathlib import Path

TAG = b"\xc1\x83\x2a\x9e"


def fstring_at(b, p):
    n = struct.unpack_from("<i", b, p)[0]
    q = p + 4
    if n == 0:
        return "", q
    if 0 < n <= 20000:
        end = q + n
        if end > len(b) or b[end - 1] != 0 or any(c < 9 for c in b[q:end - 1]):
            return None
        try:
            return b[q:end - 1].decode("utf-8"), end
        except UnicodeDecodeError:
            return None
    if -20000 <= n < 0:
        end = q - 2 * n
        if end > len(b) or b[end - 2:end] != b"\0\0":
            return None
        try:
            s = b[q:end - 2].decode("utf-16-le")
        except UnicodeDecodeError:
            return None
        return (None if any(ord(c) < 9 for c in s) else s), end
    return None


def ftexts(b):
    """[(key, source, src_start, src_end)] for FText Base histories (flags, type 0, namespace, key, source)."""
    out, p = [], 0
    while p < len(b) - 9:
        if b[p + 4] == 0 and struct.unpack_from("<I", b, p)[0] < 0x100:
            a = fstring_at(b, p + 5)
            if a and a[0] is not None:
                k = fstring_at(b, a[1])
                # keys are usually ROW_NAME_TextData, but some contain non-ASCII (e.g. full-width "？") and are
                # stored as UTF-16; inside a DT_* namespace accept any printable key
                if k and k[0] and (re.fullmatch(r"[0-9A-Fa-f]{32}|[\w\-.]{1,128}", k[0]) or
                                   (a[0].startswith("DT_") and len(k[0]) <= 256 and k[0].isprintable())):
                    s = fstring_at(b, k[1])
                    if s and s[0] is not None:
                        out.append((k[0], s[0], k[1], s[1]))
                        p = s[1]
                        continue
        p += 1
    return out


def encode_fstring(s):
    if s == "":
        return struct.pack("<i", 0)
    if all(ord(c) < 128 for c in s):
        raw = s.encode("ascii") + b"\0"
        return struct.pack("<i", len(raw)) + raw
    raw = s.encode("utf-16-le") + b"\0\0"
    return struct.pack("<i", -(len(raw) // 2)) + raw


def patch_one(uasset, uexp, ro_by_key):
    texts = ftexts(uexp)
    parts, last, replaced = [], 0, 0
    for key, src, a, b in texts:
        new = ro_by_key.get(key)
        if new is None or new == src:
            continue
        parts += [uexp[last:a], encode_fstring(new)]
        last, replaced = b, replaced + 1
    parts.append(uexp[last:])
    new_uexp = b"".join(parts)
    assert new_uexp[-4:] == TAG, "uexp tag lost"
    ua = bytearray(uasset)
    old_serial, new_serial = len(uexp) - 4, len(new_uexp) - 4
    hits = [o for o in range(0, len(ua) - 15) if struct.unpack_from("<qq", ua, o) == (old_serial, len(ua))]
    assert len(hits) == 1, f"SerialSize/SerialOffset pair not unique: {hits}"
    struct.pack_into("<q", ua, hits[0], new_serial)
    old_bulk = len(uasset) + len(uexp) - 4
    bh = [o for o in range(0, 400) if struct.unpack_from("<q", ua, o)[0] == old_bulk]
    assert len(bh) == 1, f"BulkDataStartOffset not unique: {bh}"
    struct.pack_into("<q", ua, bh[0], len(ua) + len(new_uexp) - 4)
    # verify: every FText still parses, keys unchanged, replacements present
    after = ftexts(new_uexp)
    assert [k for k, *_ in after] == [k for k, *_ in texts], "FText keys changed after patch"
    for k, s, *_ in after:
        if k in ro_by_key:
            assert s == ro_by_key[k], f"{k}: replacement not found after patch"
    return bytes(ua), new_uexp, replaced, len(texts)


def main():
    culture, src_dir, out_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    root = Path(__file__).parent
    ro_rows = json.load(open(root / "data" / "ro_strings.json", encoding="utf-8"))
    by_table = {}
    for r in ro_rows:
        by_table.setdefault(r["table"], {})[r["key"]] = r["ro"]
    dest = out_dir / "Pal" / "Content" / "L10N" / culture / "Pal" / "DataTable" / "Text"
    dest.mkdir(parents=True, exist_ok=True)
    total_rep = total_txt = 0
    for ua_path in sorted((src_dir / "Pal" / "DataTable" / "Text").glob("*.uasset")):
        name = ua_path.stem
        ue_path = ua_path.with_suffix(".uexp")
        ro_map = by_table.get(name, {})
        if not ro_map:
            print(f"  {name}: no translations, skipped")
            continue
        ua, ue, rep, n = patch_one(ua_path.read_bytes(), ue_path.read_bytes(), ro_map)
        (dest / ua_path.name).write_bytes(ua)
        (dest / ue_path.name).write_bytes(ue)
        total_rep, total_txt = total_rep + rep, total_txt + n
        print(f"  {name}: {rep}/{n} texts replaced, uexp {ue_path.stat().st_size} -> {len(ue)} bytes")
    print(f"done: {total_rep}/{total_txt} texts replaced -> {dest}")


if __name__ == "__main__":
    main()

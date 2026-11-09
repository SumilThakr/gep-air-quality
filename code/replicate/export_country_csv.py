#!/usr/bin/env python3
"""Write FID,Country,Deaths from a deaths_by_country .dbf. Replaces a manual QGIS export.

Matches the as-run format, with a quoted FID and the stored Deaths text padded to 11 decimals.
It parses the .dbf directly so that the stored digits pass through without float rounding.
Usage: python export_country_csv.py INPUT.dbf OUTPUT.csv
"""
import struct
import sys

raw = open(sys.argv[1], "rb").read()
nrec, hdr, rec = struct.unpack("<IHH", raw[4:12])
fields, pos, off = {}, 32, 1
while raw[pos] != 0x0D:
    name = raw[pos:pos + 11].split(b"\0")[0].decode()
    length = raw[pos + 16]
    fields[name] = (off, length)
    off += length
    pos += 32


def get(i, name):
    o, n = fields[name]
    return raw[hdr + i * rec + o:hdr + i * rec + o + n].split(b"\0")[0].decode("utf-8").strip()


def quote(s):
    return f'"{s}"' if "," in s or '"' in s else s


with open(sys.argv[2], "w", encoding="utf-8", newline="") as f:
    f.write("FID,Country,Deaths\n")
    for i in range(nrec):
        whole, _, frac = get(i, "Deaths").partition(".")
        f.write(f'"{get(i, "FID")}",{quote(get(i, "Country"))},{whole}.{frac[:11].ljust(11, "0")}\n')

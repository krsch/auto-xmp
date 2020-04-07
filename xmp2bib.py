#!/usr/bin/env python3
import sys
import traceback
import json
from datetime import datetime
from typing import Dict

def to_bib(info: Dict[str, str]):
    try:
        date = datetime.strptime(info.get("XMP-dc:Date"), "%Y:%m:%d %H:%M:%S%z")
    except ValueError:
        date = datetime.strptime(info.get("XMP-dc:Date"), "%Y:%m:%d %H:%M:%SZ")
    id = info["XMP-dc:Identifier"]
    eprinttype, eprint = id.split(':', 1)
    return """@misc{{{key},
    title = {{{title}}},
    author = {{{authors}}},
    year = {year},
    month = {month},
    eprint = {{{eprint}}},
    eprinttype = {{{eprinttype}}},
}}
""".format(key=id, eprint=eprint, eprinttype=eprinttype,
           authors=" and ".join(info["XMP-dc:Creator"]),
           title=info["XMP-dc:Title"],
           year=date.year, month=date.month,
          )

if __name__ == "__main__":
    for info in json.load(sys.stdin):
        try:
            sys.stdout.write(to_bib(info))
        except KeyboardInterrupt:
            sys.exit(-1)
        except:
            traceback.print_exc()
            # print("Unexpected error:", sys.exc_info(), file=sys.stderr)

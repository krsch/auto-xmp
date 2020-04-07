#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import requests

def fetch_bib(doi):
    response = requests.get('https://doi.org/' + doi, headers={
        'Accept': 'application/x-bibtex',
        'User-Agent': 'EmbedRDF/0.1 (;mailto:krsch@iitp.ru) BasedOn python3 requests/2.18',
        })
    return response.content

if __name__ == "__main__":
    # for doi in json.load(sys.stdin):
    for doi in sys.stdin:
        try:
            sys.stdout.buffer.write(fetch_bib(doi) + b'\n')
        except KeyboardInterrupt:
            sys.exit(-1)
        except:
            print("Unexpected error:", sys.exc_info(), file=sys.stderr)

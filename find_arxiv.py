#!/usr/bin/env python3
'''Find DOI by work title'''
import sys
from pathlib import Path
import subprocess
import json
from urllib.parse import urlparse
import tempfile
from typing import Dict
import xml.etree.ElementTree as ET
import re
import requests

def get_arxiv(filename):
    proc = subprocess.Popen(['pdftotext', '-l', '1', filename, '-'], stdout=subprocess.PIPE)
    out, _ = proc.communicate(timeout=1)
    matches = re.findall(r'^arxiv:(\d\d\d\d\.\d+(?:v\d+)?)', out.decode(), re.I | re.M)
    if len(matches) == 1:
        return matches[0]
    print(matches)
    return None

def get_atom(arxiv):
    response = requests.get('https://export.arxiv.org/api/query', params={
        'id_list': arxiv,
        })
    return response.content


def fill_xmp(info: Dict[str, str]):
    '''Finds DOI from PDF file'''
    # info: Dict[str, str] = json.loads(subprocess.run(['exiftool', '-G1', '-j', argv[1]],
    #                                                  stdout=subprocess.PIPE).stdout)[0]
    assert 'SourceFile' in info
    if 'XMP-prism:DOI' in info:
        return
    arxiv = get_arxiv(info['SourceFile'])
    if not arxiv:
        print('Cannot find arxiv for {}'.format(info['SourceFile']))
        return
    print(arxiv)
    atom = get_atom(arxiv)
    root = ET.fromstring(atom)
    ns = {'atom' :  "http://www.w3.org/2005/Atom"}
    authors = root.findall('./atom:entry/atom:author/atom:name', ns)
    author_names = [("".join(author.itertext())) for author in authors]
    title = ''.join(root.find('./atom:entry/atom:title',ns).itertext())
    url = ''.join(root.find('./atom:entry/atom:id',ns).itertext())
    date = ''.join(root.find('./atom:entry/atom:published',ns).itertext())
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp_json:
        json.dump({
            'XMP-dc:Creator': author_names,
            'Title': title,
            'URL': url,
            'Identifier': 'arxiv:' + arxiv,
            'date': date,
            }, tmp_json, ensure_ascii=False)
        tmp_json.flush()
        subprocess.run(['exiftool',
                        '-j=' + tmp_json.name,
                        '-overwrite_original_in_place',
                        info['SourceFile']])

if __name__ == "__main__":
    with Path(sys.argv[1]).open('r') as json_file:
        for f in json.load(json_file):
            try:
                fill_xmp(f)
            except KeyboardInterrupt:
                sys.exit(-1)
            # except:
            #     print("Unexpected error:", sys.exc_info())

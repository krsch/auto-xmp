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
import requests

INTERACTIVE = False

def find_doi(title):
    '''Searches for a work in crossref and returns its DOI. May ask for input'''
    response = requests.get('https://api.crossref.org/works', params={
        'query.bibliographic': title, 'rows': '3'})
    print(response.url)
    items = response.json()['message']['items']
    correct_title = [i for i in items if i['title'][0].casefold() == title.casefold()]
    if len(correct_title) != 1:
        # return None
        for idx, work in enumerate(items):
            print('{}: DOI: {} => {}'.format(idx, work['DOI'], work['title']))
        if INTERACTIVE:
            ans = input('Enter article number or 0 to quit --> ')
        else:
            ans = 0
        try:
            if int(ans) <= 0:
                return None
            return items[int(ans)-1]['DOI']
        except (ValueError, KeyError):
            return None
        return None
    else:
        return items[0]['DOI']

def doi_from_url(url):
    url = urlparse(url)
    if url.netloc == 'doi.org' or url.netloc == 'dx.doi.org':
        return url.path
    else:
        return None

def doi_from_ieee_title(title):
    response = requests.post('https://ieeexplore.ieee.org/rest/search/', json={
        "newsearch":True,
        "queryText": title,
        "highlight":True,
        "returnFacets":["ALL"],
        "returnType":"SEARCH",
        }, headers={
            'Accept': 'application/json',
            'Origin': 'https://ieeexplore.ieee.org',
        })
    items = response.json().get('records')
    if not items:
        return None
    print('Search IEEE for {}'.format(title))
    for idx, i in enumerate(items):
        print('{} {} - {}'.format(idx+1, i.get('doi'), i.get('articleTitle')))
    if len(items) == 1:
        return items[0].get('doi')
    if INTERACTIVE:
        ans = input('Enter article number or 0 to quit --> ')
    else:
        ans = 0
    try:
        if int(ans) <= 0:
            return None
        return items[int(ans)-1]['doi']
    except (ValueError, KeyError):
        return None

def doi_from_ieee(ieee_id):
    if not ieee_id:
        return None
    response = requests.post('https://ieeexplore.ieee.org/rest/search/', json={
        "newsearch":True,
        "queryText":"(\"Article Number\":{})".format(ieee_id),
        "highlight":True,
        "returnFacets":["ALL"],
        "returnType":"SEARCH",
        }, headers={
            'Accept': 'application/json',
            'Origin': 'https://ieeexplore.ieee.org',
        })
    items = response.json()['records']
    assert len(items) < 2
    if not items:
        return None
    return items[0].get('doi')

def remove_prefix(s, prefix):
    return s[len(prefix):] if s and s.startswith(prefix) else s

def get_doi(info):
    doi = list(filter(lambda x: x != None, [
        info.get("PDF:Doi"),
        remove_prefix(info.get("XMP-dc:Identifier"), 'doi:'),
        info.get("XMP-prism:DOI"),
        info.get("XMP-crossmark:Doi"),
        info.get("XMP-pdfx:Doi"),
        ]))
    if doi:
        if all(x == doi[0] for x in doi):
            return doi[0]
        print(doi)
        return None
    doi = list(filter(lambda x: x and x.startswith('10.'), [
        info.get("PDF:Subject", "").split(';')[-1],
        info.get("PDF:Subject", "").split(' ')[-1],
        info.get("XMP-dc:Description", "").split(';')[-1],
        info.get("XMP-dc:Description", "").split(' ')[-1],
        doi_from_url(info.get("XMP-prism:URL", "")),
        doi_from_ieee(info.get("PDF:IEEE_Article_ID")),
        ]))
    if doi:
        if all(x == doi[0] for x in doi):
            return doi[0]
        print(doi)
        return None
    # title = info.get("XMP-dc:Title") or Path(info["System:FileName"]).with_suffix('').name
    title = Path(info["System:FileName"]).with_suffix('').name
    doi = doi_from_ieee_title(title)
    if not doi:
        return find_doi(title)

def get_rdf(doi):
    response = requests.get('https://doi.org/' + doi, headers={
        'Accept': 'application/rdf+xml',
        'User-Agent': 'EmbedRDF/0.1 (;mailto:krsch@iitp.ru) BasedOn python3 requests/2.18',
        })
    return response.content

def fill_xmp(info: Dict[str, str]):
    '''Finds DOI from PDF file'''
    # info: Dict[str, str] = json.loads(subprocess.run(['exiftool', '-G1', '-j', argv[1]],
    #                                                  stdout=subprocess.PIPE).stdout)[0]
    assert 'SourceFile' in info
    # if 'XMP-dc:Identifier' in info:
        # return
    doi = get_doi(info)
    if not doi:
        print('Cannot find DOI for {}'.format(info['SourceFile']))
        return
    print(doi)
    rdf = get_rdf(doi)
    root = ET.fromstring(rdf)
    authors = root.findall('.'
                           '/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'
                           '/{http://purl.org/dc/terms/}creator'
                           '/{http://xmlns.com/foaf/0.1/}Person'
                           '/{http://xmlns.com/foaf/0.1/}name')
    author_names = [("".join(author.itertext())) for author in authors]
    with tempfile.NamedTemporaryFile(suffix='.xmp') as tmp:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp_json:
            json.dump({
                'XMP-dc:Creator': author_names,
                }, tmp_json, ensure_ascii=False)
            tmp_json.flush()
            tmp.write(rdf)
            tmp.flush()
            subprocess.run(['exiftool', '-tagsFromFile', tmp.name,
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
            except:
                print("Unexpected error:", sys.exc_info())

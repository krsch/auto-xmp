# Metadata miner and embedder for crossref and arxiv

Requires exiftool and python3-requests and (optionally) jq

To search for metadata in crossref and embed it into PDF run
```sh
exiftool -G1 -j -ext pdf -r . > meta.json
./find_doi.py meta.json
```

To search for metadata on arxiv for paper from arxiv:
```sh
exiftool -G1 -j -ext pdf -r . > meta.json
./find_arxiv.py meta.json
```

To print bibtex for all pdf that have DOI metadata:
```sh
exiftool -G1 -j -ext pdf -r . | jq 'map(select(has("XMP-prism:DOI")) | .["XMP-prism:DOI"])' | ./fetch_bibtex.py`
```

To print bibtex for all pdf that have arxiv identifier in metadata:
```sh
exiftool -G1 -j -ext pdf -r . | jq 'map(select(has("XMP-dc:Identifier")) | select (.["XMP-dc:Identifier"] | startswith("arxiv:")))' | ./xmp2bib.py
```

To embed DOI into PDF run `exiftool -doi=10.1109/TIT.2008.917682 file.pdf`.

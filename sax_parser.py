import gzip
import html
import json
from lxml import etree
from pathlib import Path
import requests
#import shutil
import subprocess
import sys
import unicodedata

def __download_file(url:str, filename:str) -> bool:
    """
        Borrowed from: https://github.com/angelosalatino/dblp-parser
        Function that downloads files (general).
        
        Args:
            url [string]: Url of where the model is located.
            filename [string]: location of where to save the model
        Returns:
            is_downloaded [boolean]: whether it is successful or not.
    """
    is_downloaded = False
    with open(filename, 'wb') as file:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')
        
        if total is None:
            #f.write(response.content)
            print('There was an error while downloading the DTD.')
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(total // 1000, 1024*1024)):
                downloaded += len(data)
                file.write(data)
                done = int(50*downloaded/total)
                sys.stdout.flush()
            sys.stdout.write('\n')
            is_downloaded = True

        return is_downloaded

def __download_dtd(args)->bool:
    """
        Borrowed from: https://github.com/angelosalatino/dblp-parser
        Function that downloads the DTD from the DBLP website.
    
        Args:
            url [str] : The URL of where to download it from. If None then default is
            filename [str]: location of where to save the dtd file
        Returns:
            None
        """
    url = "https://dblp.uni-trier.de/xml/dblp.dtd"
    return __download_file(url, args.dtd_file)

def __download_and_prepare_dataset(args)->bool:
    """
        Borrowed from: https://github.com/angelosalatino/dblp-parser
        Function that downloads the whole dataset (latest dump) from the DBLP website.
        Then it decompresses it

        Args:
            url [string]: URL of dblp database. If none provided will use default one.
            filename_zip [string]: name and path of zip archive containing all papers.
            filename_unzip [string]: name and path of folder into which we want unzip everything.

        Returns:
            None
    """

    url = "https://dblp.uni-trier.de/xml/dblp.xml.gz"

    filename_zip = args.data_file + '.gz'
    print('downloading data set')
    if not __download_file(url, filename_zip):
        return False
    print(f"Latest dump of DBLP downloaded from {url}. Unzipping now...")
    # filename_unzip = "data/dblp.xml"
    # with gzip.open(filename_zip, 'rb') as f_in:
    #     with open(filename_unzip, 'wb') as f_out:
    #         shutil.copyfileobj(f_in, f_out)
    subprocess.run(['gunzip', filename_zip])
    print("File unzipped and ready to be parsed.")
    return True

def download_data(args):
    print('downloading latest dump')
    if __download_dtd(args):
        print(f"DTD downloaded.")
        return __download_and_prepare_dataset(args)
    else:
        return False

def parse_files(prefixes, args):
    ELEMENTS = ['proceedings', 'article', 'inproceedings']
    # Feature types in DBLP
    ALL_FEATURES = {"author"   :"list",
                    "booktitle":"str",
                    "cdrom"    :"str",
                    "chapter"  :"str",
                    "cite"     :"list",
                    "crossref" :"str",
                    "editor"   :"list",
                    "ee"       :"list",
                    "isbn"     :"str",
                    "journal"  :"str",
                    "month"    :"str",
                    "note"     :"str",
                    "number"   :"str",
                    "pages"    :"str",
                    "publisher":"str",
                    "publnr"   :"str",
                    "school"   :"str",
                    "series"   :"str",
                    "title"    :"str",
                    "volume"   :"str",
                    "year"     :"str"}
    count = 0
    articles = []
    proceedings = {}
    article = None
    for event, elem in etree.iterparse('data/dblp.xml', load_dtd=True, dtd_validation=True, encoding='utf-8'):
        if elem.tag in ELEMENTS:
            key = elem.get('key')
            prefix = '/'.join(key.split('/')[:2])
            if prefix in prefixes:
                # Insert Publication information
                article = {
                    'key': elem.get('key'),
                    'mdate': elem.get('mdate'),
                    'type': elem.tag,
                    'authors': [],
                    'title': None,
                    'year': None,
                    'pages': None,
                    'volume': None,
                    'number': None,
                    'publisher': None,
                    'isbn': None,
                    'series': None,
                    'booktitle': None,
                    'journal': None,
                    'crossref': None
                }

                for e in ALL_FEATURES:
                    data = elem.findall(e)

                    if not data:
                        continue
                    if e == 'ee':
                        for d in data:
                            if 'doi.org/' in d.text:
                                article['doi'] = d.text
                    elif e == 'author':
                        for d in data:
                            orcid = d.attrib.get('orcid')
                            article['authors'].append((html.unescape(d.text), orcid))
                    else:
                        cleaned = unicodedata.normalize('NFKD',
                                                        etree.tostring(data[0], method='text', encoding='unicode')).encode(
                                                            'ascii', 'ignore').decode('ascii')
                        cleaned = cleaned.replace('\n', '')
                        cleaned = cleaned.replace('\t', '')
                        article[e] = cleaned
                if elem.tag == 'proceedings':
                    proceedings[article['key']] = article
                else:
                    articles.append(article)
            else:
                article = None
            elem.clear()
            count += 1
            if args.verbose and (count % 10000 == 0):
                print("Count: " + str(count) + " ")
    for article in articles:
        if article['crossref']:
            crossref = proceedings.get(article['crossref'])
            if crossref:
                for key in article:
                    if not article[key]:
                        article[key] = crossref.get(key)
    output_file = Path('articles.json')
    output_file.write_text(json.dumps(articles, indent=2), encoding='UTF-8')
    output_file = Path('proceedings.json')
    output_file.write_text(json.dumps(list(proceedings.values()), indent=2), encoding='UTF-8')

if __name__ == '__main__':
    prefixes = {'journals/joc',
                'journals/tosc',
                'journals/tches',
                'journals/cic',
                'conf/crypto',
                'conf/eurocrypt',
                'conf/asiacrypt',
                'conf/tcc',
                'conf/pkc',
                'conf/fse',
                'conf/ches',
                'conf/rwc',
                'conf/stoc',
                'conf/focs',
                'conf/uss',
                'conf/sp',
                'conf/ccs',
                'conf/ndss'}
    import argparse
    argparser = argparse.ArgumentParser(description='xml parser')
    argparser.add_argument('--download',
                           action='store_true')
    argparser.add_argument('--verbose',
                           action='store_true')
    argparser.add_argument('--dtd_file',
                           default='data/dblp.dtd')
    argparser.add_argument('--data_file',
                           default='data/dblp.xml')
    args = argparser.parse_args()
    if args.download:
        download_data(args)
    print('parsing...')
    parse_files(prefixes, args)

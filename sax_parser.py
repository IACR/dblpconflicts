import datetime
import gzip
import html
import json
from xml.dom import pulldom
from xml.sax import make_parser
from xml.sax.handler import feature_external_ges

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
    tagcount = 0
    count = 0
    articles = []
    proceedings = {}
    article = None
    parser = make_parser()
    parser.setFeature(feature_external_ges, True)
    verbose = False
    text = ''
    orcid = None
    for event, node in pulldom.parse('data/dblp.xml', parser=parser):
        match event:
            case pulldom.START_ELEMENT:
                tagcount += 1
                if node.localName in ELEMENTS:
                    count += 1
                    if args.verbose and (count % 10000 == 0):
                        print("Count: ", str(count), tagcount, len(articles), len(proceedings), str(datetime.datetime.now().time()))
                    key = node.getAttribute('key')
                    prefix = '/'.join(key.split('/')[:2])
                    if prefix in prefixes:
                        article = {
                            'key': key,
                            'mdate': node.getAttribute('mdate'),
                            'type': node.tagName,
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
                elif article and node.localName == 'author':
                    orcid = node.getAttribute('orcid')
                    if not orcid:
                        orcid = None
                pass
            case pulldom.END_ELEMENT:
                if article:
                    tagname = node.localName
                    if tagname in ELEMENTS:
                        if tagname == 'proceedings':
                            proceedings[article['key']] = article
                        else:
                            articles.append(article)
                        article = None
                        text = ''
                    elif tagname == 'ee':
                        doi = text.strip()
                        if 'doi.org/' in doi:
                            article['doi'] = doi
                        text = ''
                    elif tagname == 'author':
                        text = text.strip()
                        if text:
                            article['authors'].append((text, orcid))
                        orcid = None
                        text = ''
                    elif tagname in ALL_FEATURES:
                        article[tagname] = text.strip()
                        text = ''
                    elif tagname != 'sup' and tagname != 'sub':
                        text = ''
                pass
            case pulldom.CHARACTERS:
                if article:
                    text += node.data
                pass
            case pulldom.END_DOCUMENT:
                break
            case _:
                pass
    for article in articles:
        if article.get('crossref'):
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
                'conf/uss',
                'conf/sp',
                'conf/ccs',
                'conf/ndss'}
    # others to consider for inclusion:
    # 'conf/stoc', # these completely dominate the results with people who
    # 'conf/focs', # have never published anything on crypto and security.
    # Real world cryptography, not available in DBLP
    # 'conf/fc',      # Financial cryptography
    # 'conf/ctrsa',   # The Cryptographer's Track at RSA Conference (CT-RSA)
    # 'conf/esorics', # ESORICS
    # 'journals/tifs', # IEEE Transactions on Information Forensics and Security
    # 'journals/compsec', # Computers & Security
    # 'journals/istr', # Journal of Informatoin Security and Applications
    # 'conf/icbc2', # IEEE Conference on Blockchains and Cryptocurrency (ICBC)
    # 'conf/asiaccs', # Asia CCS
    # 'conf/eurosp'   # European Security & privacy
    # 'conf/soups'    # Symposium on Useful Privacy and Security
    # 'journals/popets', # Privacy Enhancing Technologies
    # 'conf/securecom', # Security and Privacy in Communication Networks
    # 'conf/cans',    # Cryptology and Network Security
    # 'conf/acsac',   # Annual Computer Security Applications Conference
    # 'conf/dsn',     # Dependable Systems and Networks
    # 'conf/cfsw',    # IEEE Computer Security Foundations Workshop
    # 'conf/cns',     # IEEE Conference and Communications and Network Security
    # 'conf/acns',    # International Conference on Applied Cryptography and Network Security
    # 'conf/sacrypt', # (SAC)
    # 'conf/icisc',   # International Conference on Information Security and Cryptology
    # 'conf/icics',   # International Conference on Information and Communication
    # 'conf/sec',     # IFIP International Information Security Conference (SEC)
    # 'conf/wisec',   # Conference on Security and Privacy in Wireless and Mobile Networks (WISEC)
    # 'conf/host',    # IEEE International Symposium on Hardware Oriented Security and Trust
    # 'conf/nspw',    # New Security Paradigms Workshop
    # 'conf/ih',      # Information Hiding and Multimedia Security Workshop
    # 'conf/acisp',   # Australasian Conference on Information Security and Privacy
    # 'conf/africacrypt',
    # 'conf/latincrypt',
    # 'conf/csr2',    # International Conference on Cyber Security and Resilience
    # 'conf/asiajcis', # Asia Joint COnference on information Security
    # 'conf/wisa',    # International Conference on information Security Applications
    # 'conf/asiapkc', # ACM Asia Public-Key Cryptography Workshop
    # 'conf/lightsec', # International Workshop on Lightweight Cryptography for Security and Privacy
    # 'conf/fdtc',    # Workshop on Fault Detection and Tolerance in Cryptography
    # 'conf/blocktea', # International Conference on Blockchain Technology and Emerging Technologies
    # 'conf/provsec', # Provable Security
    # 'conf/ccsw-ws', # Cloud Computing Security Workshop (CCSW)
    # 'conf/iwsec',   # International Workshop on Security (IWSEC)
    # 'conf/iciss',   # International Conference on Information System Security (ICISS)
    import argparse
    argparser = argparse.ArgumentParser(description='xml parser')
    argparser.add_argument('--download',
                           action='store_true')
    argparser.add_argument('--verbose',
                           action='store_true')
    argparser.add_argument('--dtd_file',
                           default='dblp.dtd')
    argparser.add_argument('--data_file',
                           default='data/dblp.xml')
    args = argparser.parse_args()
    if args.download:
        download_data(args)
    print('parsing...')
    parse_files(prefixes, args)

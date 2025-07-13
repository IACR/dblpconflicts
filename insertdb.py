from pathlib import Path
import json
import pymysql
import sys

db = pymysql.connect(host='localhost',
                     passwd='dblpd@t@',
                     db='dblpconflicts',
                     user='dblpconflicts',
                     charset='utf8',
                     use_unicode=True,
                     init_command='SET NAMES UTF8')
cursor = db.cursor(pymysql.cursors.DictCursor)
articles = json.loads(Path('articles.json').read_text(encoding='UTF-8'))
counter = 0
for article in articles:
    counter += 1
    if (counter % 1000 == 0):
        print('counter=', counter)
    args = (article['mdate'],
            article['key'],
            article['type'],
            article['title'],
            article['year'],
            article['pages'],
            article.get('volume'),
            article.get('number'),
            article.get('publisher'),
            article.get('isbn'),
            article.get('series'),
            article.get('booktitle'),
            article.get('journal'),
            article.get('doi'))
    cursor.execute('INSERT INTO `article` (mdate,dblpkey,type,title,year,pages,volume,number,publisher,isbn,series,booktitle,journal,doi) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', args)
    pubkey = cursor.lastrowid
    authornumber = 0
    for author in article['authors']:
        authornumber += 1
        dblpkey = author[0]
        orcid = author[1]
        parts = dblpkey.split(' ')
        if parts[-1].isnumeric():
            parts.pop()
        name = ' '.join(parts)
        cursor.execute("SELECT authorkey FROM author WHERE dblpkey=%s", (dblpkey,))
        row = cursor.fetchone()
        if row:
            authorkey = row['authorkey']
        else:
            cursor.execute('INSERT INTO author (name,orcid,dblpkey) values (%s,%s,%s)', (name, orcid, dblpkey))
            authorkey = cursor.lastrowid
        cursor.execute('INSERT INTO authorship (pubkey,authorkey,authornumber,publishedasname) VALUES (%s,%s,%s,%s)', (pubkey,authorkey,authornumber,name))
    db.commit()

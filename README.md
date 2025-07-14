This is sort of like cryptodb but includes things outside IACR. It isn't
clear where to draw the line, because there are a LOT of third-tier conferences
and journals. See the code in `sax_parser.py` where there are others listed
in comments.
See also [Google scholar](https://scholar.google.es/citations?view_op=top_venues&hl=en&vq=eng_computersecuritycryptography)

This includes a python parser for DBLP. There are quite a few
available, but this one uses minimal RAM and parses it
incrementally.

The code consists of several parts:
1. the `sax_parser.py` that downloads and parses the DBLP data to produce
   a JSON file of articles.
2. the `create.sql` to create the database. Note that we store ORCIDs but
   we do not cross-reference cryptodb.
3. the `insertdb.py` code to insert into the database.
4. the `www` code for the web interface. This is written in PHP for simplicity.

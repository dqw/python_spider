#!/usr/bin/pyhon

import argparse
import urllib2
from StringIO import StringIO
import gzip

def get_html(url):
    response = urllib2.urlopen(url, timeout=5)

    if response.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(response.read())
        f = gzip.GzipFile(fileobj=buf)
        html = f.read()
    else:
        html = response.read()

    return html

def save_html(data):
    fp = open("a.html","w+")
    fp.write(data)

def print_html(data):
    print data

parser = argparse.ArgumentParser()
parser.add_argument('-u', dest="url", default="http://www.sina.com.cn", help="")
parser.add_argument("-d", type=int, dest="deep", default=1, help="")  
args = parser.parse_args()
html = get_html(args.url)
save_html(html)



#!/usr/bin/pyhon

import argparse
import urllib2
from StringIO import StringIO
import gzip
from urlparse import urlparse
from BeautifulSoup import BeautifulSoup
import re

def get_html(url):
    response = urllib2.urlopen(url, timeout=5)

    if response.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(response.read())
        f = gzip.GzipFile(fileobj=buf)
        html = f.read()
    else:
        html = response.read()

    return html

def get_domain(url):
    hostname = urlparse(url).hostname
    index = hostname.index('.')
    return hostname[index + 1:]

def get_link_array(html, hostname):
    link_array = []
    soup = BeautifulSoup(html)
    #for link in soup.findAll('a'):
    #for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
    for link in soup.findAll('a', attrs={'href': re.compile("^http://" + ".*" + hostname)}):
        link_array.append(link.get('href'))
    return link_array

def save_html(data):
    fp = open("a.html","w+")
    fp.write(data)

def print_html(data):
    print data

def print_link(link_array):
    for link in link_array:
        print link
    print len(link_array)

parser = argparse.ArgumentParser()
parser.add_argument('-u', dest="url", default="http://www.sina.com.cn", help="")
parser.add_argument("-d", type=int, dest="deep", default=1, help="")
args = parser.parse_args()
html = get_html(args.url)
link_array = get_link_array(html, get_domain(args.url))
print_link(link_array)
#save_html(html)

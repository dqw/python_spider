#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import urllib2
import re
import gzip
import chardet
import logging
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup


def spider(url, args, flag_get_new_link):

    thread_name = threading.current_thread().getName()

    # 分析页面，获取链接
    def get_link(html):
        new_link = []

        soup = BeautifulSoup(html)
        for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
            href = link.get('href')
            new_link.append(href)

        return new_link

    # 获取页面
    def get_html(url, args, flag_get_new_link):
        html = ''
        new_link = []

        try:
            response = urllib2.urlopen(url, timeout=20)
            if response.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(response.read())
                f = gzip.GzipFile(fileobj=buf)
                html = f.read()
            else:
                html = response.read()
        except urllib2.URLError as e:
            logging.warning("{0} URL error: {1}".format(url.encode("utf8"), e.reason))
        except urllib2.HTTPError as e:
            logging.warning("{0} HTTP error: {1}".format(url.encode("utf8"), e.code))
        except Exception as e:
            logging.warning("{0} Unexpected: {1}".format(url.encode("utf8"), str(e)))
        else:
            logging.info("{0} downloaded {1}".format(thread_name, url.encode("utf8")))

            if args.key == "":
                if flag_get_new_link:
                    new_link = get_link(html)
            else:
                # 页面编码处理
                if not args.encoding:
                    charset = chardet.detect(html)
                    args.encoding = charset['encoding']

                # 下载匹配关键字的页面
                match = re.search(re.compile(args.key), html.decode(args.encoding, "ignore"))
                if match and flag_get_new_link:
                    logging.info("{0} {1} match key".format(thread_name, url.encode("utf8")))
                    new_link = get_link(html)
                else:
                    logging.info("{0} {1} not match key".format(thread_name, url.encode("utf8")))
        finally:
            return html, new_link

    return get_html(url, args, flag_get_new_link)

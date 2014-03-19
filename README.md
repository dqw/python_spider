# python_spider

python开发的Web爬虫

### 功能描述

    使用python编写一个网站爬虫程序，支持参数如下：
    spider.py -u url -d deep -f logfile -l loglevel(1-5)  --testself -thread number --dbfile  filepath  --key=”HTML5”

    参数说明：
    -u 指定爬虫开始地址
    -d 指定爬虫深度
    --thread 指定线程池大小，多线程爬取页面，可选参数，默认10
    --dbfile 存放结果数据到指定的数据库（sqlite）文件中
    --key 页面内的关键词，获取满足该关键词的网页，可选参数，默认为所有页面
    -l 日志记录文件记录详细程度，数字越大记录越详细，可选参数，默认spider.log
    --testself 程序自测，可选参数

### 具体要求

1. 指定网站爬取指定深度的页面，将包含指定关键词的页面内容存放到sqlite3数据库文件中
2. 程序每隔10秒在屏幕上打印进度信息
3. 支持线程池机制，并发爬取网页
4. 代码需要详尽的注释，自己需要深刻理解该程序所涉及到的各类知识点
5. 需要自己实现线程池

### 使用方法
    #起始地址新浪，下载2级，使用10个线程，保存到sina.db
    python main.py -u http://www.sina.com.cn -d 1 --thread 10 --dbfile sina.db

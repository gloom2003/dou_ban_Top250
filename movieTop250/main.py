# -*- coding = utf-8 -*-
# @Time : 2023/11/7
# @Software: PyCharm
import urllib.request
from bs4 import BeautifulSoup
import re
import sqlite3
from collections import Counter


# 正则表达式

findLink = re.compile(r'<a href="(.*?)/">')
findImgSrc = re.compile(r'<img.*src="(.*?)"',re.S) # re.S使.能够匹配换行符
findTitle = re.compile(r'<span class="title">(.*?)</span>')
# 评分
findRating = re.compile(r'<span class="rating_num" property="v:average">(.*?)</span>')
# 评分人数
findJudge = re.compile(r'<span>(.*?)人评价</span>')
# 简介
findInq = re.compile(r'<span class="inq">(.*?)</span>')
# 相关内容
findBd = re.compile(r'<p class="">(.*?)</p>',re.S)

# 匹配导演、主演、年份、国家、分类
pattern = re.compile(
    r'导演:\s*(?P<director>.*?)\s+'
    r'主演:\s*(?P<cast>.*?)\s+'
    r'(?P<year>\d{4})\s*/\s*'
    r'(?P<country>.*?)\s*/\s*'
    r'(?P<genre>.*)'
)

def main():
    url = "https://movie.douban.com/top250?start="
    # 保存到哪个数据库
    DbPath = "movie.db"
    dataList = getData(url)
    saveDataToDb(dataList,DbPath)
    print("爬取完毕！已存储到%s数据库"%DbPath)


def saveDataToDb(dataList, DbPath):
    connect = sqlite3.connect(DbPath)
    cursor = connect.cursor()
    for data in dataList:
        # 给文本类型添加双引号
        for i in range(0,len(data)):
            if(i==4 or i==5):
                continue
            data[i] = '"' + data[i] + '"'
        str = ",".join(data)
        sql = '''
            insert into movie250(info_link,pic_link,cname,ename,score,rated,instroduction,info) values(%s)
        '''%str
        cursor.execute(sql)
        connect.commit()
    connect.close()


def getData(baseUrl):
    dataList = []
    url = baseUrl
    for i in range(0,10):
        baseUrl = url + str(i*25)
        html = askUrl(baseUrl)
        bs = BeautifulSoup(html,"html.parser")
        # 使用bs找到每一个item
        items = bs.find_all('div',class_="item")
        for item in items:
            # 存储每条影片的相关数据
            data = []
            item = str(item)
            # 使用re匹配所有的信息，如：link，并且只获取第一个
            link = re.findall(findLink,item)[0]
            data.append(link)
            # 获取图片链接
            picture = re.findall(findImgSrc,item)[0]
            data.append(picture)
            # 获取标题名称
            titles = re.findall(findTitle,item)
            if(len(titles) == 2):
                # 中文标题
                cTitle = titles[0]
                data.append(cTitle)
                # 外国标题，去除无关符号
                oTitle = titles[1].replace("/","")
                data.append(oTitle)
            else:
                # 其他情况时，只添加中文标题，外国标题使用空字符串占位即可
                cTitle = titles[0]
                data.append(cTitle)
                oTitle = " "
                data.append(oTitle)
            # 获取评分、评价人数、简介、相关内容
            rating = re.findall(findRating,item)[0]
            data.append(rating)
            judge = re.findall(findJudge,item)[0]
            data.append(judge)
            # 有的inq简介是空的
            inqs = re.findall(findInq,item)
            inq = " "
            if len(inqs) != 0:
                inq = inqs[0]
            data.append(inq)
            # 处理Bd相关内容的字符串格式
            Bd = re.findall(findBd,item)[0]
            # (\s+)?：匹配任意数量（包括0）的空白字符（比如空格、制表符、换行等）
            Bd = re.sub(r'<br(\s+)?/>(\s+)?'," ",Bd) # 查找字符串Bd中所有的<br>或者<br />标签
            Bd = Bd.strip()
            data.append(Bd)
            dataList.append(data)
    return dataList

def askUrl(url):
    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    # 封装一个req对象，指定访问的url、请求头
    req = urllib.request.Request(url,headers=headers)
    html = ""
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print("error!:")
        if hasattr(e,"code"):
            print(e.code)
        if hasattr(e,"reason"):
            print(e.reason)
    return html

def initDb(DbPath):
    connect = sqlite3.connect(DbPath)
    cursor = connect.cursor()
    sql = '''
        create table movie250(
        id integer primary key autoincrement,
        info_link text,
        pic_link text,
        cname varchar,
        ename varchar,
        score numeric,
        rated numeric,
        instroduction text,
        info text
        )
    '''
    cursor.execute(sql)
    connect.commit()
    connect.close()

def score():
    connect = sqlite3.connect("movie.db")
    cursor = connect.cursor()

    print("===================评分方面=========================")
    # 平均评分：
    sql = '''
        select avg(score) from movie250
    '''
    cursor.execute(sql)
    # 获取查询结果
    avg = cursor.fetchone()
    # 打印查询结果
    print("豆瓣Top250电影的平均评分:%.2f"%avg[0])

    # 最高评分：
    sql = '''
        select max(score),cname from movie250
    '''
    cursor.execute(sql)
    # 获取查询结果
    max = cursor.fetchone()
    # 打印查询结果
    print(f"豆瓣Top250电影的最高评分:{max[0]},影片名：{max[1]}")

    # 最低评分：
    sql = '''
            select min(score),cname from movie250
        '''
    cursor.execute(sql)
    # 获取查询结果
    min = cursor.fetchone()
    # 打印查询结果
    print(f"豆瓣Top250电影的最低评分:{min[0]},影片名：{min[1]}")
    connect.close()
    print("===================评分方面=========================")

def ratedNumber():
    print("==================评价人数方面=======================")
    connect = sqlite3.connect("movie.db")
    cursor = connect.cursor()

    # 总评价人数
    sql = '''
        select sum(rated) from movie250
    '''
    cursor.execute(sql)
    # 获取查询结果
    sum = cursor.fetchone()
    # 打印查询结果
    print(f"豆瓣Top250电影的总人数为: {sum[0]}人")

    # 平均人数：
    sql = '''
        select avg(rated) from movie250
    '''
    cursor.execute(sql)
    # 获取查询结果
    avg = cursor.fetchone()
    # 打印查询结果
    print(f"豆瓣Top250每部电影的平均评分人数为: {avg[0]:.0f}人")

    # 最多评价人数及其影片名：
    sql = '''
            select max(rated),cname,score from movie250
        '''
    cursor.execute(sql)
    # 获取查询结果
    res = cursor.fetchone()
    max = res[0]
    cname = res[1]
    score = res[2]
    # 打印查询结果
    print(f"豆瓣Top250电影中评分人数最多的为: {max:.0f}人，影片名：{cname},评分:{score:.1f}")

    # 最少评价人数及其影片名：
    sql = '''
                select min(rated),cname,score from movie250
            '''
    cursor.execute(sql)
    # 获取查询结果
    res = cursor.fetchone()
    min = res[0]
    cname = res[1]
    score = res[2]
    # 打印查询结果
    print(f"豆瓣Top250电影中评分人数最少的为: {min:.0f}人，影片名：{cname},评分:{score:.1f}")
    print("==================评价人数方面=======================")
    connect.close()


# 统计字符串列表中每个字符串出现最多的字符串与次数
def find_most_frequent_strings(strings):
    # 使用Counter来计数,计算字符串列表中每个字符串出现的次数
    counter = Counter(strings)
    # 找到出现次数最多的字符串和次数
    return counter.most_common(1)[0]

# 统计字符串列表中每个字符串出现最少的字符串与次数
def find_min_frequent_strings(strings):
    # 使用Counter来计数,计算字符串列表中每个字符串出现的次数
    counter = Counter(strings)
    # 找到出现次数最少的字符串和次数
    return counter.most_common()[-1]


def get_max_director(dicts):
    directors = []
    for dict in dicts:
        director = dict.get("director")
        # 处理多个导演的情况
        str_list = director.split("/")
        for str in str_list:
            directors.append(str)
    return find_most_frequent_strings(directors)

def get_max_cast(dicts):
    casts = []
    for dict in dicts:
        cast = dict.get("cast")
        str_list = cast.split("/")
        for str in str_list:
            # 处理格式
            if(str.endswith("...")):
                continue
            casts.append(str)
    return find_most_frequent_strings(casts)


def get_max_year(dicts):
    years = []
    for dict in dicts:
        year = dict.get("year")
        years.append(year)
    return find_most_frequent_strings(years)


def get_min_year(dicts):
    years = []
    for dict in dicts:
        year = dict.get("year")
        years.append(year)
    return find_min_frequent_strings(years)


def get_max_country(dicts):
    countrys = []
    for dict in dicts:
        country = dict.get("country")
        # 处理格式
        str_list = country.split(" ")
        for str in str_list:
            countrys.append(str)
    return find_most_frequent_strings(countrys)


def get_min_country(dicts):
    countrys = []
    for dict in dicts:
        country = dict.get("country")
        # 处理格式
        str_list = country.split(" ")
        for str in str_list:
            countrys.append(str)
    return find_min_frequent_strings(countrys)

def get_max_genre(dicts):
    genres = []
    for dict in dicts:
        genre = dict.get("genre")
        # 处理格式
        str_list = genre.split(" ")
        for str in str_list:
            genres.append(str)
    counter = Counter(genres)
    return counter.most_common()


def get_min_genre(dicts):
    genres = []
    for dict in dicts:
        genre = dict.get("genre")
        # 处理格式
        str_list = genre.split(" ")
        for str in str_list:
            genres.append(str)
    counter = Counter(genres)
    return counter.most_common()


def otherMessage():
    connect = sqlite3.connect("movie.db")
    cursor = connect.cursor()

    print("===================其他信息方面=========================")
    sql = '''
        select info from movie250
    '''
    cursor.execute(sql)
    rows = cursor.fetchall()
    datas = []
    for row in rows:
        message = row[0]
        # 使用正则表达式进行匹配
        match = pattern.match(message)
        if match:
            # 把匹配到的数据保存到字典中
            dict = match.groupdict()
            datas.append(dict)
        # else:
        #     # print(f"Data does not match pattern: {message}")
    max_director = get_max_director(datas)
    max_cast = get_max_cast(datas)
    max_year = get_max_year(datas)
    min_year = get_min_year(datas)
    max_country = get_max_country(datas)
    min_country = get_min_country(datas)
    max_genre = get_max_genre(datas)
    min_genre = get_min_genre(datas)
    print("豆瓣Top250电影中:")
    print(f'出现次数最多的导演为:{max_director[0]},出现的次数为{max_director[1]}')
    print(f'出现次数最多的主演为:{max_cast[0]},出现的次数为{max_cast[1]}')
    print(f'出现次数最多的年份为:{max_year[0]},出现的次数为{max_year[1]}')
    print(f'出现次数最少的年份为:{min_year[0]},出现的次数为{min_year[1]}')
    print(f'出现次数最多的国家为:{max_country[0]},出现的次数为{max_country[1]}')
    print(f'出现次数最少的国家为:{min_country[0]},出现的次数为{min_country[1]}')
    print(f'最热门分类的前3名与出现次数分别为:{max_genre[0][0]}:{max_genre[0][1]},'
          f'{max_genre[1][0]}:{max_genre[1][1]},{max_genre[2][0]}:{max_genre[2][1]}')
    print(f'最不热门分类的前3名与出现次数分别为:{min_genre[-1][0]}:{min_genre[-1][1]},'
          f'{min_genre[-2][0]}:{min_genre[-2][1]},{min_genre[-3][0]}:{min_genre[-3][1]}')
    print("===================其他信息方面=========================")

if __name__ == "__main__":
    # 第一次运行时，需要先创建数据库
    # initDb("movie.db")
    # main函数：爬取数据并存储到数据库中
    # main()
    # 数据分析相关的函数
    score()
    print()
    ratedNumber()
    print()
    otherMessage()
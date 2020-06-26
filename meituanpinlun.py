# coding=utf-8


'''

获取美团商家评价并生成词云

'''
import json
import random
import requests
import sys
import os
import re
import time
import jieba.analyse
from wordcloud import WordCloud, ImageColorGenerator
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from http import cookiejar


# 浏览器标识
user_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3704.400 QQBrowser/10.4.3587.400', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
               'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)', 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4094.1 Safari/537.36']

# 存放IP
ip_list = []
# 商家评价星数
star = 0
# 美团cookie
cookie_str = ""


# 获取代理IP
def get_ip():
    global ip_list
    ip_shumu = 0
    ip_chengg = 0
    # 请求头
    header = {
        'User-Agent': user_agents[random.randint(0, len(user_agents)-1)],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Host': 'www.89ip.cn'
    }
    # 获取页数
    print('获取IP中。。。')
    for i in range(1, 2):
        ip_url = 'http://www.89ip.cn/index_{}.html'.format(i)
        try:
            ip_html = requests.get(ip_url, headers=header)
        except ConnectionError:
            time.sleep(2)
            ip_html = requests.get(ip_url, headers=header)
        if ip_html.status_code == 200:
            print("连接IP代理网站成功。。。")
        # 替换掉HTML的空格和换行
        html = ip_html.text.replace(" ", "").replace(
            "\n", "").replace("\t", "")
        # 匹配IP和端口的正则表达式
        r = re.compile('<tr><td>(.*?)</td><td>(.*?)</td><td>')
        # 匹配到的IP与端口
        ip_data = re.findall(r, html)
        ip_shumu += len(ip_data)
        for k in range(len(ip_data)):
            # 拼接IP与端口
            ip = "https://" + ip_data[k][0] + ":" + ip_data[k][1]
            ip_a = {"https://": ip}
            # 测试可不可用
            ping = requests.get("https://www.baidu.com", proxies=ip_a)
            if ping.status_code == 200:
                ip_list.append(ip_a)
                ip_chengg += 1
    print('获取到的IP数：{0}\n有效的IP数：{1}'.format(ip_shumu, ip_chengg))


# 获取美团cookie
def get_cookie():
    global cookie_str
    header = {
        'Host': 'www.meituan.com',
        'User-Agent': user_agents[random.randint(0, len(user_agents)-1)],
    }
    a = 0
    while True:
        cookie_req = requests.get(
            "https://gz.meituan.com/s/", headers=header, proxies=ip_list[
                random.randint(0, len(ip_list) - 1)])
        if cookie_req.status_code != 302:
            break
        a += a
        # 重试次数过多重新获取IP
        if a == 10:
            ip_list.clear()
            get_ip()
            a = 0
    cookie_dic = requests.utils.dict_from_cookiejar(cookie_req.cookies)
    for key in cookie_dic:
        for val in cookie_dic.values():
            cookie_str += key + '=' + val


# 获取美团商家ID
def get_shangjia(shangjia):
    header = {
        'User-Agent': user_agents[random.randint(0, len(user_agents)-1)],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Cookie': cookie_str,
        'Host': 'fs.meituan.com',
        'Upgrade-Insecure-Requests': '1',
    }
    url = "https://gz.meituan.com/s/{0}/".format(shangjia)
    for i in range(len(ip_list)):
        # 请求
        get_html = requests.get(url, headers=header, proxies=ip_list[i])
        # 替换掉空格换行
        html = get_html.text.replace(" ", "").replace("\n", "")
        try:
            # 匹配到错误信息进行下一轮循环
            re.search(r'error-word', html).group()
            continue
        except AttributeError:
            break
    # 匹配ID
    r = re.compile(r'data-poiid="[1-9]\d*"',)
    a = re.findall(r, html)
    try:
        return re.search(r'[1-9]\d*', a[0]).group()
    # 获取页面失败
    except IndexError:
        ip_list.clear()
        get_ip()
        get_shangjia(shangjia)


# 获取美团商家评价
def get_data(url):
    global ip_list
    global star
    pingjia = ""
    # 请求头
    header = {
        'Host': 'www.meituan.com',
        'User-Agent': user_agents[random.randint(0, len(user_agents)-1)],
    }
    data = requests.get(url, headers=header, proxies=ip_list[
        random.randint(0, len(ip_list) - 1)])
    try:
        for i in range(len(data.json()['data']['comments'])):
            # 评价
            pingjia += data.json()['data']['comments'][i]['comment']
            # 星数
            star += data.json()['data']['comments'][i]['star']
        return pingjia
    # 获取评价失败重新获取IP和数据
    except KeyError:
        ip_list.clear()
        get_ip()
        get_data(url)


# 生成词云
def ciyun(pingjia):
    img_bg = np.array(Image.open(
        "D:\\vscode\\My_Code\\meituanpinlun\\logo.png"))  # 打开图片
    # 分词
    data_jieba = jieba.analyse.extract_tags(
        pingjia, topK=1000, withWeight=True, allowPOS=())
    data = {a[0]: a[1] for a in data_jieba}  # 将数组形式转换为字典

    ciyun = WordCloud(font_path='C:\Windows\Fonts\simhei.ttf',  # 设置字体路径
                      background_color="white",  # 背景色
                      max_words=1000,  # 显示词语的最大个数
                      max_font_size=300,  # 最大字体大小
                      width=1920,  # 输出的画布宽度
                      height=1048,  # 输出的画布高度
                      scale=5,  # 长宽拉伸程度程度设置
                      mask=img_bg  # 设置图片蒙版
                      ).generate_from_frequencies(data)  # 根据词频生成词云

    plt.figure(figsize=(12, 12))  # 创建图形并设置画布大小
    plt.imshow(ciyun, interpolation='bilinear')
    plt.axis("off")  # 不显示坐标
    file_name = os.path.basename(__file__)
    file_path = os.path.splitext(file_name)[0]
    ciyun.to_file(
        "{0}\平均{1}颗星.png".format(file_path, star))  # 保存文件
    plt.show()


if __name__ == "__main__":
    get_ip()
    get_cookie()

    shangjia = input("输入商家全称：")
    shumu = input("输入需要查看的评论数目：")
    shangjia_ID = get_shangjia(shangjia)

    url = "https://www.meituan.com/meishi/api/poi/getMerchantComment?{0}&platform=1&partner=126&originUrl=https%3A%2F%2Fwww.meituan.com%2Fmeishi%2F{1}%2F&riskLevel=1&optimusCode=10&id={1}&userId=&offset=0&pageSize={2}&sortType=1".format(
        cookie_str, shangjia_ID, shumu)
    pingjia = get_data(url)
    # 计算平均评分
    star = (star / 10)/int(shumu)

    ciyun(pingjia)

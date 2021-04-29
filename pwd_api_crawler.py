# -*- coding:utf-8 -*-
# 2021/02/24 videorighter

from selenium import webdriver
import json
from bs4 import BeautifulSoup
import requests
import sys
import re

if __name__ == "__main__":
    # import db_model
    import time
    import pwd_api_crawler
    import argparse

    parser = argparse.ArgumentParser(description="Powderroom crawler")
    group = parser.add_mutually_exclusive_group()

    group.add_argument('-n', '--post_num', action='store_true', help='Crawling based on the post number.')
    group.add_argument('-d', '--post_date', action='store_true', help='Crawling based on the post date.')

    parser.add_argument('keyword', type=str, help='Enter the keyword.')
    parser.add_argument('type', type=str, help='Enter type -> REVIEW or MOTD')
    parser.add_argument('option', help='Enter the post number or date of the post.')

    arg = parser.parse_args()
    keyword = arg.keyword
    type = arg.type

    if arg.post_num:
        try:
            option = int(arg.option)
        except ValueError:
            print("Please enter '-d' or '--post_date' argument option.")
            sys.exit()
    elif arg.post_date:
        try:
            option = int(arg.option)
            print("Please enter '-n' or '--post_num' argument option.")
            sys.exit()
        except ValueError:
            option = arg.option
    else:
        print('Please enter the argument option.')
        sys.exit()

    start = time.time()
    crawler = pwd_api_crawler.powder_crawler(keyword, type, option)
    # contents, comments = crawler.get_post_info()
    boardIDs = crawler.get_post_info()
    print(boardIDs)
    print("time :", time.time() - start)


class powder_crawler():

    def __init__(self, keyword, type, option):

        # self.db_model = db_model.DB_model()
        self.post_list = []
        self.comment_list = []
        self.post_url = []
        self.boardIds = []
        self.count = 0

        self.keyword = keyword
        self.type = type
        self.option = option

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(executable_path="/Users/oldman/Documents/crawler/chromedriver",
                                       chrome_options=chrome_options)

    def addslashes(self, s):
        d = {'"': '\\"', "'": "\\'", "\0": "\\\0", "\\": "\\\\"}
        return ''.join(d.get(c, c) for c in s)

    def remove_emoji(string):
        # 이모티콘 제거
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   "]+", flags=re.UNICODE)

        # 분석에 어긋나는 불용어구 제외 (특수문자, 의성어)
        han = re.compile('[ㄱ-ㅎㅏ-ㅣ]+')
        url = re.compile('(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
        special = re.compile('[^\w\s#]')
        email = re.compile('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')

        tmp = emoji_pattern.sub('', string)
        tmp = han.sub('', tmp)
        tmp = url.sub('', tmp)
        tmp = special.sub('', tmp)
        tmp = email.sub('', tmp)

        return tmp

    def get_post_info(self):
        self.driver.get('https://www.powderroom.co.kr/')

        if type(self.option) == int:
            if self.type == "MOTD":
                offset = 1
                while True:
                    api_url = f"https://api.powderroom.co.kr/powderroom/search/board?offset={offset * 10}&limit=10&boardTypes={self.type}&query={self.keyword}"
                    self.driver.execute_script('''
                    function loadXMLDoc() {
                      var xhttp = new XMLHttpRequest();
                      xhttp.onreadystatechange = function() {
                        if (this.readyState == 4 && this.status == 200) {
                          document.write('<div id="find_me">'+this.responseText+'</div>');
                        }
                      };
                      xhttp.open("GET", "%s" , true);
                      xhttp.send()
                    }
                    loadXMLDoc()''' % (api_url))
                    time.sleep(1)
                    main = self.driver.find_element_by_css_selector('#find_me').text
                    try:
                        raw_json = json.loads(main, strict=False)
                    except json.decoder.JSONDecodeError:
                        print("json loads failed")
                        continue
                    for i in raw_json['data']:
                        self.boardIds.append(i['boardId'])
                    offset += 1
                    if len(self.boardIds) == self.option:
                        break

            elif self.type == "REVIEW":
                offset = 0
                while True:
                    if offset != 0:
                        api_url = f"https://api.powderroom.co.kr/powderroom/search/board?offset={offset * 4}&limit=4&boardTypes={self.type}&sort=POPULAR&order=DESC&query={self.keyword}"
                    else:
                        api_url = f"https://api.powderroom.co.kr/powderroom/search/board?limit=4&boardTypes={self.type}&sort=POPULAR&order=DESC&query={self.keyword}"
                    self.driver.execute_script('''
                    function loadXMLDoc() {
                      var xhttp = new XMLHttpRequest();
                      xhttp.onreadystatechange = function() {
                        if (this.readyState == 4 && this.status == 200) {
                          document.write('<div id="find_me">'+this.responseText+'</div>');
                        }
                      };
                      xhttp.open("GET", "%s" , true);
                      xhttp.send()
                    }
                    loadXMLDoc()''' % (api_url))
                    time.sleep(1)
                    main = self.driver.find_element_by_css_selector('#find_me').text
                    try:
                        raw_json = json.loads(main, strict=False)
                    except json.decoder.JSONDecodeError:
                        print("json loads failed")
                        continue

                    for i in raw_json['data']:
                        self.boardIds.append(i['boardId'])
                    offset += 1
                    if len(self.boardIds) == self.option:
                        break
            else:
                print("Entered type is wrong.")

        self.driver.close()
        return self.boardIds

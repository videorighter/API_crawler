# -*- coding:utf-8 -*-
'''
2020/07/16 videorighter
youtube crawler refactoring
2021/05/23 technical portfolio refactoring
'''

from selenium import webdriver as wd
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
# import db_model
import utils
import argparse
import youtube_crawler


class youtubecrawler():

    def __init__(self, args):

        self.post_list = []
        self.comment_list = []
        self.args = args
        # RDBMS 및 기타 util function 사용
        # if self.args.is_db:
        #     self.db_model = db_model.DB_model()

    def get_post_info(self):

        keyword = ''
        for i, word in enumerate(self.args.keyword):
            if i == 0:
                keyword += word
            else:
                keyword += "+" + word

        # db 사용 시
        # if self.args.is_db:
        #     row_id = self.db_model.set_daily_log(keyword, 1)

        start_url = "https://www.youtube.com/results?search_query="

        # search term setting
        term_dict = {
            'lasthour': 'AQ',
            'today': 'Ag',
            'thisweek': 'Aw',
            'thismonth': 'BA',
            'thisyear': 'BQ'
        }

        # 키워드 및 기간 설정 url 생성
        try:
            start_url = start_url + keyword + f'&sp=EgII{term_dict[self.args.choose_period]}%253D%253D'
        except ValueError:
            print('choose lasthour, today, thisweek, thismonth, thisyear')

        chrome_options = wd.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = wd.Chrome(executable_path="/Users/oldman/Documents/crawler/chromedriver",
                           chrome_options=chrome_options)
        driver.get(start_url)
        # 페이지 높이 설정
        last_page_height = driver.execute_script("return document.documentElement.scrollHeight")

        # 스크롤 끝까지 내리고 이전 시점과 스크롤 높이가 같다면 멈춤
        # 스크롤 횟수 argparser 추가
        while True:
            self.args.post_scroll_num -= 1
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(3)
            # Scroll down to bottom
            new_page_height = driver.execute_script("return document.documentElement.scrollHeight")

            if new_page_height == last_page_height:
                break
            elif self.args.post_scroll_num == 0:
                break

            last_page_height = new_page_height

        print('Post url crawling complete.')
        html_source = driver.page_source

        soup = BeautifulSoup(html_source, 'lxml')

        for title in soup.select("a#video-title"):
            unique_id = title.get('href')[9:]
            driver.get("https://www.youtube.com/" + title.get('href'))
            print("https://www.youtube.com/" + title.get('href'))
            last_page_height = driver.execute_script("return document.documentElement.scrollHeight")

            # RDBM log stack
            body_is_new = {'is_new': False, 'last_time_update': '1970-01-01 00:00:00'}

            # comment scroll
            # 스크롤 횟수 argparser 추가
            while True:
                self.args.comment_scroll_num -= 1
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(3.5)
                new_page_height = driver.execute_script("return document.documentElement.scrollHeight")

                if new_page_height == last_page_height:
                    break
                elif self.args.comment_scroll_num == 0:
                    break

                last_page_height = new_page_height

            print('Comment scroll complete.')

            html_source = driver.page_source
            soup = BeautifulSoup(html_source, 'lxml')

            # live streaming 여부 확인
            find_live = soup.select('div#date > yt-formatted-string')
            # waiting clip 여부 확인
            find_wait = soup.select('div#count > yt-view-count-renderer > span')
            try:
                try:
                    live_tmp = str(find_live[0].text).replace('\n', '').replace('\t', '').replace('              ', '')
                except ValueError:
                    live_tmp = 'No streaming'
            except IndexError:
                live_tmp = 'No streaming'

            try:
                try:
                    wait_tmp = str(find_wait[0].text).replace('\n', '').replace('\t', '').replace('              ', '')
                except ValueError:
                    wait_tmp = 'No Premieres'
            except IndexError:
                wait_tmp = 'No Premieres'

            live_comp = re.compile('Started streaming')
            wait_comp = re.compile('waiting')
            live_match = live_comp.match(live_tmp)
            wait_match = wait_comp.match(wait_tmp)

            if live_match:
                print('This is streaming')  # live일 경우
            elif wait_match:
                print('This is Premieres')  # waiting clip일 경우
            else:  # 모두 아닐 경우
                soup = BeautifulSoup(html_source, 'lxml')

                clip_content = soup.select('#description > yt-formatted-string')
                contents = ['']

                for content in clip_content:
                    str_tmp = utils.remove_emoji(
                        str(content.text).replace(
                            '\n', '').replace(
                            '\t', '').replace(
                            '              ', ''))
                    contents = contents[0] + ' ' + str_tmp

                # 댓글 개수
                print('comment_num is: ', len(soup.select('#author-text > span')))

                try:
                    like_count = utils.remove_str(soup.find("yt-formatted-string", {
                        "class": "style-scope ytd-toggle-button-renderer style-text"})["aria-label"][0])
                except KeyError:
                    like_count = 0

                try:
                    dislike_count = utils.remove_str(soup.find("yt-formatted-string", {
                        "class": "style-scope ytd-toggle-button-renderer style-text"})["aria-label"][1])
                except KeyError:
                    dislike_count = 0

                try:
                    posting_date = datetime.strptime(soup.select(
                        '#date > yt-formatted-string')[0].text, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    posting_date = utils.conv_date2(soup.select('#date > yt-formatted-string')[0].text)

                view_count = utils.remove_str(soup.select(
                        '#count > ytd-video-view-count-renderer > span.view-count.style-scope.ytd-video-view-count-renderer'
                    )[0].text.replace(
                        '\n', '').replace(
                        '\t', '').replace(
                        '조회수 ', '').replace('회', ''))
                view_comp = re.compile('대기 중')
                view_match = view_comp.match(str(view_count))

                if view_count == '조회수 없음':
                    view_count = 0
                elif view_match:
                    continue

                # post information
                post_dict = {
                    "unique_id": unique_id,
                    "keyword": keyword,
                    "title": utils.addslashes(soup.select(
                        '#container > h1 > yt-formatted-string')[0].text.replace(
                        '\n', '').replace(
                        '\t', '').replace(
                        '              ', '')),
                    "user_id": 0,
                    "user_name": utils.addslashes(soup.select('#text > a')[0].text.replace(
                        '\n', '').replace(
                        '\t', '').replace(
                        '              ', '')),
                    "posting_date": posting_date,
                    "view_count": view_count,
                    "like_count": utils.conv_digit(like_count),
                    "dislike_count": utils.conv_digit(dislike_count),
                    "contents": utils.addslashes(contents),
                    "user_follow": 0,
                    "user_follower": utils.conv_digit(soup.select(
                        'yt-formatted-string#owner-sub-count')[0].text),
                    "user_medias": 0,
                    "comment_count": len(soup.select('#author-text > span'))
                }

                # if self.args.is_db:
                #     body_is_new = self.db_model.set_data_body(1, post_dict)
                self.post_list.append(post_dict)

            # comment information
            for i in range(len(soup.select('#author-text > span'))):

                try:
                    comment_like = utils.remove_str(soup.find("span", {
                        "class": "style-scope ytd-comment-action-buttons-renderer"})["aria-label"][i])
                except (IndexError, KeyError):
                    comment_like = 0

                try:
                    comment_dict = {
                        "unique_id": unique_id,
                        "keyword": keyword,
                        "user_name": utils.addslashes(soup.select('#author-text > span')[i].text.replace(
                            '\n', '').replace(
                            '\t', '').replace(
                            '                ', '').replace(
                            '              ', '')),
                        "comment_date": utils.conv_date(soup.select(
                            '#header-author > yt-formatted-string > a')[i].text).strftime("%Y-%m-%d %H:%M:%S"),
                        "comment": utils.addslashes(soup.select(
                            '#content-text')[i].text.replace('\n', '').replace(
                            '\t', '').replace(
                            '                ', '').replace(
                            '              ', '')),
                        "comment_like": utils.conv_digit(comment_like)
                    }

                except IndexError:
                    comment_dict = {
                        "unique_id": unique_id,
                        "keyword": keyword,
                        "user_name": utils.addslashes(soup.select('#author-text > span')[i].text.replace(
                            '\n        ', '').replace(
                            '\t', '').replace(
                            '                ', '').replace(
                            '              ', '')),
                        "comment_date": utils.addslashes(soup.select(
                            '#header-author > yt-formatted-string > a')[i].text).strftime("%Y-%m-%d %H:%M:%S"),
                        "comment": utils.addslashes(soup.select(
                            '#content-text')[i].text.replace(
                            '\n        ', '').replace(
                            '\t', '').replace(
                            '                ', '').replace(
                            '              ', '')),
                        "comment_like": utils.conv_digit(comment_like)
                    }

                # RDBM 사용시 활성화
                # if self.args.is_db:
                #     self.db_model.set_data_comment(1, comment_dict, body_is_new['is_new'],
                #                                    body_is_new['last_time_update'])
                self.comment_list.append(comment_dict)

        driver.quit()
        # if self.args.is_db:
        #     self.db_model.set_daily_log('', '', row_id)
        print("Done")
        print(f'Crawled post num: {len(self.post_list)}\n'
              f'Crawled comment num: {len(self.comment_list)}')

        return self.post_list, self.comment_list


def main():
    # 2020-07-17 first test

    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', nargs='+', type=str, default='유튜브', help='Insert the keyword you want to crawl')
    parser.add_argument('--is_db', type=bool, default=True, help='Are you going to use DB?')
    parser.add_argument('--choose_period', type=str, default='thisweek',
                        help='Insert the time period you want to crawl (lasthour, today, thisweek, thismonth, thisyear)')
    parser.add_argument('--post_scroll_num', type=int, default=100, help='Insert the number of scroll of post')
    parser.add_argument('--comment_scroll_num', type=int, default=100, help='Insert the number of scroll of comment')
    args = parser.parse_args()

    start = time.time()
    crawler = youtube_crawler.youtubecrawler(args)
    post_list, comment_list = crawler.get_post_info()
    print(post_list)
    print("time :", time.time() - start)


if __name__ == "__main__":
    main()

# -*- coding:utf-8 -*-

# 2020/07/16 videorighter
# youtube crawler refactoring

from selenium import webdriver as wd
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import db_model


class youtubecrwaler():

    def __init__(self):

        self.post_list = []
        self.comment_list = []
        self.db_model = db_model.DB_model()

    def get_post_info(self, term):

        # 검색어 입력
        keyword = input('검색어를 입력하세요: ')
        row_id = self.db_model.set_daily_log(keyword, 1)

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
            start_url = start_url + keyword + '&sp=EgII{}%253D%253D'.format(term_dict[term])

        except ValueError:
            print('choose lasthour, today, thisweek, thismonth, thisyear')

        chrome_options = wd.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = wd.Chrome(executable_path="/usr/bin/chromedriver", chrome_options=chrome_options)
        driver.get(start_url)
        # 페이지 높이 설정
        last_page_height = driver.execute_script("return document.documentElement.scrollHeight")

        # 스크롤 끝까지 내리고 이전 시점과 스크롤 높이가 같다면 멈춤
        while True:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(3)
            # Scroll down to bottom
            new_page_height = driver.execute_script("return document.documentElement.scrollHeight")

            if new_page_height == last_page_height:
                break

            last_page_height = new_page_height

        html_source = driver.page_source

        soup = BeautifulSoup(html_source, 'lxml')

        for title in soup.select("a#video-title"):
            unique_id = title.get('href')[9:]
            driver.get("https://www.youtube.com/" + title.get('href'))
            print("https://www.youtube.com/" + title.get('href'))
            last_page_height = driver.execute_script("return document.documentElement.scrollHeight")

            body_is_new = {'is_new': False, 'last_time_update': '1970-01-01 00:00:00'}

            while True:
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(3.5)
                new_page_height = driver.execute_script("return document.documentElement.scrollHeight")

                if new_page_height == last_page_height:
                    break

                last_page_height = new_page_height

            html_source = driver.page_source
            soup = BeautifulSoup(html_source, 'lxml')

            # live streaming 여부 확인
            find_live = soup.select('div#date > yt-formatted-string')
            # waiting clip 여부 확인
            find_wait = soup.select('div#count > yt-view-count-renderer > span')

            try:
                live_tmp = str(find_live[0].text).replace('\n', '').replace('\t', '').replace('              ', '')
                wait_tmp = str(find_wait[0].text).replace('\n', '').replace('\t', '').replace('              ', '')
            except ValueError:
                live_tmp = 'No streaming'
                wait_tmp = 'No Premieres'
            except IndexError:
                print("This clip was deleted")

                continue


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
                    str_tmp = self.remove_emoji(
                        str(content.text).replace(
                            '\n', '').replace(
                            '\t', '').replace(
                            '              ', ''))
                    contents = contents[0] + ' ' + str_tmp

                # 댓글 개수
                print('comment_num is: ', len(soup.select('#author-text > span')))

                try:
                    like_count = self.remove_str(soup.find("yt-formatted-string", {
                        "class": "style-scope ytd-toggle-button-renderer style-text"})["aria-label"][0])
                except KeyError:
                    like_count = 0

                try:
                    dislike_count = self.remove_str(soup.find("yt-formatted-string", {
                        "class": "style-scope ytd-toggle-button-renderer style-text"})["aria-label"][1])
                except KeyError:
                    dislike_count = 0

                try:
                    posting_date = datetime.strptime(soup.select(
                        '#date > yt-formatted-string')[0].text, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    posting_date = self.db_model.conv_date2(soup.select('#date > yt-formatted-string')[0].text)



                # post information
                post_dict = {
                    "unique_id": unique_id,
                    "keyword": keyword,
                    "title": self.db_model.addslashes(soup.select(
                        '#container > h1 > yt-formatted-string')[0].text.replace(
                        '\n', '').replace(
                        '\t', '').replace(
                        '              ', '')),
                    "user_id": 0,
                    "user_name": self.db_model.addslashes(soup.select('#text > a')[0].text.replace(
                        '\n', '').replace(
                        '\t', '').replace(
                        '              ', '')),
                    "posting_date": posting_date,
                    "view_count": self.remove_str(soup.select(
                        '#count > yt-view-count-renderer > span.view-count.style-scope.yt-view-count-renderer'
                    )[0].text.replace(
                        '\n', '').replace(
                        '\t', '').replace(
                        '              ', '')),
                    "like_count": self.db_model.conv_digit(like_count),
                    "dislike_count": self.db_model.conv_digit(dislike_count),
                    "contents": self.db_model.addslashes(contents),
                    "user_follow": 0,
                    "user_follower": self.db_model.conv_digit(soup.select(
                        'yt-formatted-string#owner-sub-count')[0].text),
                    "user_medias": 0,
                    "comment_count": len(soup.select('#author-text > span'))
                }

                body_is_new = self.db_model.set_data_body(1, post_dict)
                # 혹시 몰라서 살려둠
                # self.post_list.append(post_dict)


            # comment information
            for i in range(len(soup.select('#author-text > span'))):

                try:
                    comment_like = self.remove_str(soup.find("span", {
                        "class": "style-scope ytd-comment-action-buttons-renderer"})["aria-label"][i])
                except (IndexError, KeyError):
                    comment_like = 0

                try:
                    comment_dict = {
                        "unique_id": unique_id,
                        "keyword": keyword,
                        "user_name": self.db_model.addslashes(soup.select('#author-text > span')[i].text.replace(
                            '\n', '').replace(
                            '\t', '').replace(
                            '                ', '').replace(
                            '              ', '')),
                        "comment_date": self.db_model.conv_date(soup.select(
                            '#header-author > yt-formatted-string > a')[i].text).strftime("%Y-%m-%d %H:%M:%S"),
                        "comment": self.db_model.addslashes(soup.select(
                            '#content-text')[i].text.replace('\n', '').replace(
                            '\t', '').replace(
                            '                ', '').replace(
                            '              ', '')),
                        "comment_like": self.db_model.conv_digit(comment_like)
                    }

                except IndexError:
                    comment_dict = {
                        "unique_id": unique_id,
                        "keyword": keyword,
                        "user_name": self.db_model.addslashes(soup.select('#author-text > span')[i].text.replace(
                            '\n        ', '').replace(
                            '\t', '').replace(
                            '                ', '').replace(
                            '              ', '')),
                        "comment_date": self.db_model.addslashes(soup.select(
                            '#header-author > yt-formatted-string > a')[i].text).strftime("%Y-%m-%d %H:%M:%S"),
                        "comment": self.db_model.addslashes(soup.select(
                            '#content-text')[i].text.replace(
                            '\n        ', '').replace(
                            '\t', '').replace(
                            '                ', '').replace(
                            '              ', '')),
                        "comment_like": self.db_model.conv_digit(comment_like)
                    }

                self.db_model.set_data_comment(1, comment_dict, body_is_new['is_new'], body_is_new['last_time_update'])

                # 혹시 몰라서 살려둠
                # self.comment_list.append(comment_dict)

        driver.quit()
        self.db_model.set_daily_log('', '', row_id)

        #return self.post_list, self.comment_list
        return print("Done")

    # 이모티콘 제거
    def remove_emoji(self, string):
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   "]+", flags=re.UNICODE)

        # 분석에 어긋나는 불용어구 제외 (특수문자, 의성어)
        han = re.compile('[ㄱ-ㅎㅏ-ㅣ]+')
        url = re.compile('(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
        special = re.compile('[^\w\s]')
        email = re.compile('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')

        tmp = emoji_pattern.sub('', string)
        tmp = han.sub('', tmp)
        tmp = url.sub('', tmp)
        tmp = special.sub('', tmp)
        tmp = email.sub('', tmp)

        return tmp

    # str 제거 함수
    def remove_str(self, str):
        if True:
            try:
                result = int(re.sub(r'[a-zA-Z가-힣ㄱ-ㅎ\s+]', '', str).strip())
            except ValueError:
                return 0
        else:
            return 0

        return result



if __name__ == "__main__":

    # 2020-07-17 first test
    import db_model
    import youtube_crawler
    import time

    start = time.time()

    crawler = youtube_crawler.youtubecrwaler()

    print('choose lasthour, today, thisweek, thismonth, thisyear')
    term = input('기간을 설정하세요: ')

    crawler.get_post_info(term)

    print("time :", time.time() - start)

# -*- coding:utf-8 -*-
'''
videorighter
# 2020-08-20 first test
naver blog crawler refactoring
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
import naver_crawler
import requests


class navercrawler():

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
                keyword += "%20" + word

        # db 사용 시
        # if self.args.is_db:
        #     row_id = self.db_model.set_daily_log(keyword, 3)

        first_url = f"https://section.blog.naver.com/Search/Post.nhn?pageNo=1&rangeType=PERIOD&orderBy=sim&startDate=" \
                    f"{self.args.start_date}&endDate={self.args.end_date}&keyword={keyword}"
        chrome_options = wd.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = wd.Chrome(executable_path="/Users/oldman/Documents/crawler/chromedriver",
                           chrome_options=chrome_options)
        driver.get(first_url)
        time.sleep(1.5)  # 안하면 못불러옴

        gunsu = driver.find_element_by_css_selector(
            '#content > section > div.category_search > div.search_information > span > span > em').text
        print(f'{keyword}에 대한 검색 결과 입니다. {gunsu}')

        if int(utils.remove_str(gunsu)) < self.args.num:
            print(f'요청 건수보다 적으므로 {gunsu}만큼 크롤링 합니다.')
            num = int(utils.remove_str(gunsu))
        else:
            num = self.args.num

        # 검색 게시글 수 입력 -> 개수 맞게 페이지수 넘김 -> 해당 포스팅 링크 수집
        for i in range(num // 7 + 1):

            loop_url = f"https://section.blog.naver.com/Search/" \
                       f"Post.nhn?pageNo={i + 1}&rangeType=PERIOD&orderBy=sim&startDate=" \
                       f"{self.args.start_date}&endDate={self.args.end_date}&keyword={keyword}"
            driver.get(loop_url)
            time.sleep(3)
            elems = driver.find_elements_by_css_selector("a.desc_inner")
            post_urls = [elem.get_attribute('href') for elem in elems]

            for j, jj in enumerate(post_urls):
                print(jj)
                blogno = jj.split("/")[-1]
                blogid = re.compile(".blog.me").sub('', jj.split("/")[-2])
                post_url = f"https://blog.naver.com/PostView.nhn?blogId={blogid}&logNo={blogno}" \
                           f"&redirect=Dlog&widgetTypeCall=true&directAccess=false"
                driver.get(post_url)
                time.sleep(5)

                # 좋아요 기능이 없고 댓글만 있는 경우는 통과
                try:
                    comment_click = driver.find_elements_by_css_selector(
                        '#printPost1 > tbody > tr > td.bcc > div.post-btn.post_btn2 >'
                        ' div.wrap_postcomment > div > a')[1]
                except IndexError:
                    continue

                comment_click.click()
                time.sleep(5)
                html_source = driver.page_source
                soup = BeautifulSoup(html_source, 'lxml')

                follow_res = requests.get("https://section.blog.naver.com/connect/ViewMoreFollowers.nhn",
                                          params={"blogId": blogid})
                time.sleep(2)
                follow_soup = BeautifulSoup(follow_res.content, 'lxml')

                # 블로그 종류 다른 경우
                try:
                    comment_count = int(
                        soup.find("div", {"class": "area_comment pcol3"}).find("a").find("em").get_text(strip=True))
                except AttributeError:
                    comment_count = 0
                # 블로그 종류 다른 경우
                try:
                    user_follower = int(follow_soup.select(
                        "body > div.bg_main > div.container > div > div.content_box > "
                        "div > div.function_box.buddy_cnt_admin > p > strong")[0].text)
                except (AttributeError, IndexError):
                    user_follower = 0
                # 블로그 종류 다른 경우
                try:
                    title = soup.find("div", {"class": "se-module se-module-text se-title-text"}).get_text(strip=True)
                except AttributeError:
                    try:
                        title = soup.find("span", {"class": "pcol1 itemSubjectBoldfont"}).get_text(strip=True)
                    except AttributeError:
                        title = soup.find("h3", {"class": "se_textarea"}).get_text(strip=True)
                # 블로그 종류 다른 경우
                try:
                    user_name = soup.find("span", {"class": "nick"}).find("a").text
                except AttributeError:
                    try:
                        user_name = soup.find("strong", {"id": "nickNameArea"}).text
                    except AttributeError:
                        user_name = soup.find("a", {"class": "link pcol2"}).text

                # 블로그 종류 다른 경우
                try:
                    posting_date = utils.conv_date_naver(
                        soup.find("span", {"class": "se_publishDate pcol2"}).text)
                except AttributeError:
                    try:
                        posting_date = utils.conv_date_naver(
                            soup.find("p", {"class": "date fil5 pcol2 _postAddDate"}).text)
                    except AttributeError:
                        posting_date = utils.conv_date_naver(
                            soup.find("span", {"class": "se_publishDate pcol2"}).text)

                # 블로그 종류 다른 경우
                try:
                    contents = re.compile("\\u200b").sub(' ', soup.find("div", {"class": "se-main-container"}).get_text(
                        strip=True))
                except AttributeError:
                    try:
                        contents = re.compile("\\u200b").sub(' ', soup.find("div", {"id": "postViewArea"}).get_text(
                            strip=True))
                    except AttributeError:
                        contents = re.compile("\\u200b").sub(' ', soup.find(
                            "div", {"class": "se_component_wrap sect_dsc __se_component_area"}).get_text(strip=True))
                # 값 없는 경우
                try:
                    like_count = int(soup.find("em", {"class": "u_cnt _count"}).text)
                except ValueError:
                    like_count = 0

                post_dict = {
                    'unique_id': blogno,
                    'keyword': keyword,
                    'title': utils.addslashes(title),
                    'user_id': blogid,
                    'user_name': user_name,
                    'posting_date': posting_date,
                    'view_count': 0,
                    'like_count': like_count,
                    'dislike_count': 0,
                    'contents': utils.addslashes(contents),
                    'user_follow': 0,
                    'user_follower': user_follower,
                    'user_medias': int(
                        soup.select("#category-list > div > ul > li.allview > span")[0].text.replace("(", '').replace(
                            ")", '')),
                    'comment_count': comment_count
                }
                time.sleep(1)
                # 쿼리
                # if self.args.is_db:
                #     body_is_new = self.db_model.set_data_body(3, post_dict)

                self.post_list.append(post_dict)

                for k in range(len(soup.find_all("span", {"class": "u_cbox_nick"}))):
                    comment_dict = {
                        "unique_id": blogno,
                        "keyword": self.args.keyword,
                        "user_name": soup.find_all("span", {"class": "u_cbox_nick"})[k].text,
                        "comment_date": datetime.strptime(soup.find_all("span", {"class": "u_cbox_date"})[k].text,
                                                          '%Y.%m.%d. %H:%M').strftime("%Y-%m-%d %H:%M:%S"),
                        "comment": utils.addslashes(
                            soup.find_all("span", {"class": "u_cbox_contents"})[k].text),
                        "comment_like": 0
                    }
                    time.sleep(1)

                    # 쿼리 / body_is_new여부에 따라
                    # if self.args.is_db:
                    #     self.db_model.set_data_comment(3, comment_dict, body_is_new['is_new'],
                    #                                    body_is_new['last_time_update'])

                    self.comment_list.append(comment_dict)

                comm_page_path = driver.find_elements_by_class_name("u_cbox_page")

                for k in range(len(comm_page_path) - 1):

                    comm_page_path = driver.find_elements_by_class_name("u_cbox_page")
                    comm_page_path[k].click()
                    time.sleep(1)
                    html_source = driver.page_source
                    soup = BeautifulSoup(html_source, 'lxml')

                    for l in range(len(soup.find_all("span", {"class": "u_cbox_nick"}))):
                        comment_dict = {
                            "unique_id": blogno,
                            "keyword": keyword,
                            "user_name": soup.find_all("span", {"class": "u_cbox_nick"})[l].text,
                            "comment_date": datetime.strptime(soup.find_all("span", {"class": "u_cbox_date"})[l].text,
                                                              '%Y.%m.%d. %H:%M').strftime("%Y-%m-%d %H:%M:%S"),
                            "comment": utils.addslashes(
                                soup.find_all("span", {"class": "u_cbox_contents"})[l].text),
                            "comment_like": 0
                        }
                        time.sleep(1)

                        # 쿼리 / body_is_new여부에 따라
                        # if self.args.is_db:
                        #     self.db_model.set_data_comment(3, comment_dict, body_is_new['is_new'],
                        #                                    body_is_new['last_time_update'])

                        self.comment_list.append(comment_dict)
        # RDBMS log
        # if self.args.is_db:
        #     self.db_model.set_daily_log('', '', row_id)
        driver.quit()
        print("Done")
        print(f'Crawled post num: {len(self.post_list)}\n'
              f'Crawled comment num: {len(self.comment_list)}')

        return self.post_list, self.comment_list


def main():
    # 2020-07-17 first test

    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', nargs='+', type=str, default='네이버블로그', help='Insert the keyword you want to crawl')
    parser.add_argument('--is_db', type=bool, default=True, help='Are you going to use DB?')
    parser.add_argument('--start_date', type=str, default='2021-01-01',
                        help='Insert the start date you want to crawl (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, default='2021-06-01',
                        help='Insert the end date you want to crawl (YYYY-MM-DD)')
    parser.add_argument('--num', type=int, default=7, help='Insert the number you want to crawl')
    args = parser.parse_args()

    start = time.time()
    crawler = naver_crawler.navercrawler(args)
    post_list, comment_list = crawler.get_post_info()
    print(post_list)
    print("time :", time.time() - start)


if __name__ == "__main__":
    main()

# -*- coding:utf-8 -*-
'''
videorighter
Glowpick crawler
2021/05/23 technical portfolio refactoring
'''

from selenium import webdriver as wd
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import re
import utils
import argparse
import glowpick_crawler
# import db_model
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class glowpickcrawler():

    def __init__(self, args):

        self.post_list = []
        self.comment_list = []
        self.post_urls = []
        self.args = args
        # RDBMS 및 기타 util function 사용
        # if self.args.is_db:
        #     self.db_model = db_model.DB_model()

    def get_post_info(self):

        # db 사용 시
        # if self.args.is_db:
        #     row_id = self.db_model.set_daily_log(self.args.keyword, 4)

        first_url = f"https://glowpick.com/search/result?query={self.args.keyword}"
        chrome_options = wd.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = wd.Chrome(executable_path="/Users/oldman/Documents/crawler/chromedriver",
                           chrome_options=chrome_options)
        driver.maximize_window()
        driver.implicitly_wait(20)
        driver.get(first_url)
        time.sleep(2)
        product = driver.find_element_by_css_selector(
            "#gp-default-main > div > div > section.result__section--product > h3").text
        re_prod = int(re.compile("[0-9]+").findall(product)[0])
        print(f"{self.args.keyword}의 검색결과: {re_prod}")

        # 스크롤 끝으로 이동하기 위해 화면을 클릭
        time.sleep(1)
        elem = driver.find_element_by_xpath('/html/body')
        elem.click()
        time.sleep(1)

        # 스크롤 END 버튼 한번에 제품 20개
        # 따라서 (총 검색결과)/20+1 만큼 END 버튼 누름
        while True:
            elem.send_keys(Keys.END)
            time.sleep(5)
            elem.send_keys(Keys.HOME)
            time.sleep(7)
            html_source = driver.page_source
            soup = BeautifulSoup(html_source, 'lxml')
            post_soup = [x for x in soup.select(
                "#gp-default-main > div > div > section.result__section--product > ul > li > div > meta")]
            if re_prod == len(post_soup):
                break

        # url 하나 가져오고 창 이동한 뒤 다시 돌아가면 다시 스크롤 내려야 하므로 모든 상품 url을 list에 저장
        for post_content in post_soup:
            post_url = post_content["content"]
            self.post_urls.append(post_url)
        print(self.post_urls)

        # 바탕 한번 클릭하고 수집된 url list에서 하나씩
        for post_url in self.post_urls:
            print(post_url)
            driver.get(post_url)
            driver.implicitly_wait(20)
            time.sleep(5)
            elem = driver.find_element_by_xpath('/html/body')
            elem.click()
            driver.implicitly_wait(10)
            time.sleep(5)

            try:
                review_count = driver.find_element_by_class_name("ratings__review_count").text
                review_count = int(re.compile("[0-9]+").findall(re.sub(",", "", review_count))[0])
            except:
                review_count = 0

            # 댓글 스크롤 내리기
            while True:
                html_source = driver.page_source
                soup = BeautifulSoup(html_source, 'lxml')
                comment_soup = [x for x in soup.select(
                    "#gp-default-main > section > div > ul.contents__reviews > "
                    "li.contents__reviews__li--right.contents__reviews__review-list > section > ul > li")]
                elem.send_keys(Keys.END)
                time.sleep(5)
                elem.send_keys(Keys.HOME)
                time.sleep(7)
                html_source2 = driver.page_source
                soup2 = BeautifulSoup(html_source2, 'lxml')
                comment_soup2 = [x for x in soup2.select(
                    "#gp-default-main > section > div > ul.contents__reviews > "
                    "li.contents__reviews__li--right.contents__reviews__review-list > section > ul > li")]
                if (review_count == len(comment_soup2)) or (len(comment_soup) == len(comment_soup2)):
                    break

            time.sleep(1)
            html_source = driver.page_source
            soup = BeautifulSoup(html_source, 'lxml')
            time.sleep(3)

            # 컬러타입 없을 경우
            try:
                color_type = ', '.join(soup.find('div', {'class': 'info__color-type-list'}).text.split(' / '))
            except:
                color_type = None
            # 판매자 이름 없을 경우
            try:
                sellers = soup.find('div', {'class': 'info__sellers'}).text
            except:
                sellers = None
            # 용량 없을 경우
            try:
                volume = eval(re.sub("[a-z]+", '', re.sub(
                    "X", "*", re.sub("x", "*", soup.find('div', {'class': 'product-main-info__volume_price'}).
                                     text.split(" / ")[0]))))
            except:
                volume = 0
            # 제목 없을 경우
            try:
                title = utils.addslashes(
                    soup.find('span', {'class': 'product-main-info__product_name__text'}).text)
            except:
                title = None
            # 좋아요 수 인식 못하는 경우
            try:
                like_count = soup.find('span', {'class': 'ratings__score'}).text
            except AttributeError:
                like_count = 0
            # 내용 인식 못하는 경우
            try:
                contents = utils.addslashes(
                    re.sub("\n", ' ', soup.find('div', {'class': 'info__description'}).text))
            except AttributeError:
                contents = None
            # 브랜드 없는 경우
            try:
                brand = utils.addslashes(soup.find("span", {"class": "brand_info__brand-name"}).text)
            except AttributeError:
                brand = None
            # 가격 인식 못하는 경우
            try:
                price_find = soup.find('span', {'class': 'product-main-info__volume_price--bold'}).text
                price = int(''.join(re.compile("[0-9]+").findall(price_find)))
            except AttributeError:
                price = None
            # 태그 인식 못하는 경우
            try:
                tags = ",".join([x.text for x in soup.find_all('p', {'class': 'info__tags'})])
            except AttributeError:
                tags = None

            post_dict = {
                'unique_id': post_url.split("/")[-1],
                'keyword': self.args.keyword,
                'title': title,
                'user_id': 0,
                'user_name': 0,
                'posting_date': "0000-00-00 00:00:00",
                'view_count': 0,
                'like_count': like_count,
                'dislike_count': 0,
                'contents': contents,
                "user_follow": 0,
                "user_follower": 0,
                "user_medias": 0,
                'comment_count': len(comment_soup2),
                'additional_data': [
                    {'data_key': 'brand',
                     'data_value': brand},
                    {'data_key': 'volume',
                     'data_value': volume},
                    {'data_key': 'price',
                     'data_value': price},
                    {'data_key': 'sellers',
                     'data_value': sellers},
                    {'data_key': 'color_type',
                     'data_value': color_type},
                    {'data_key': 'tags',
                     'data_value': tags},
                    {'data_key': 'ratio_best',
                     'data_value': int(driver.find_elements_by_class_name("joiner")[
                                           1].text) / review_count if not review_count == 0 else None},
                    {'data_key': 'ratio_good',
                     'data_value': int(driver.find_elements_by_class_name("joiner")[
                                           2].text) / review_count if not review_count == 0 else None},
                    {'data_key': 'ratio_soso',
                     'data_value': int(driver.find_elements_by_class_name("joiner")[
                                           3].text) / review_count if not review_count == 0 else None},
                    {'data_key': 'ratio_bad',
                     'data_value': int(driver.find_elements_by_class_name("joiner")[
                                           4].text) / review_count if not review_count == 0 else None},
                    {'data_key': 'ratio_worst',
                     'data_value': int(driver.find_elements_by_class_name("joiner")[
                                           5].text) / review_count if not review_count == 0 else None}
                ]
            }

            time.sleep(1)
            # 쿼리
            # if self.args.is_db:
            #     body_is_new = self.db_model.set_data_body(4, post_dict)
            #     self.db_model.set_data_body_info(4, body_is_new['is_new'], post_dict)
            self.post_list.append(post_dict)

            age_attr_select = [x.text for x in driver.find_elements_by_css_selector(
                "div.list-item > div > div > p > span.info > span.txt")]
            age = [re.compile("[0-9]+").findall(x)[0] for x in age_attr_select]
            attr = [x.split(" ")[2] for x in age_attr_select]

            gender_select = [x.get_attribute("class") for x in driver.find_elements_by_css_selector(
                "div.list-item > div > div > p > span.info > span.txt > span")]
            gender = ["female" if x == "icon-sprite icon-gender-f" else "male" for x in gender_select]

            grid = {
                "best": 5,
                "good": 4,
                "soso": 3,
                "bad": 2,
                "worst": 1
            }

            for j in range(len(driver.find_elements_by_class_name("user-name"))):
                comment_dict = {
                    "unique_id": post_url.split("/")[-1],
                    "keyword": self.args.keyword,
                    "comment_id": ", ".join([age[j], attr[j], gender[j]]),
                    "user_name": driver.find_elements_by_class_name("user-name")[j].text,
                    "comment_date": utils.conv_date_glow(driver.find_elements_by_css_selector(
                        "div > div > span.date")[j].text),
                    "comment": utils.addslashes(re.sub("\n", "", driver.find_elements_by_css_selector(
                        "div > p.review")[j].text)),
                    "comment_like": grid[driver.find_elements_by_css_selector(
                        "#gp-default-main > section > div > ul.contents__reviews > li.contents__reviews__li--right."
                        "contents__reviews__review-list > section > ul > li > div > div > div > p > span.info > "
                        "span.label > span")[j].get_attribute("class").split("-")[-2]]
                }
                time.sleep(1)
                # 쿼리
                # if self.args.is_db:
                #     self.db_model.set_data_comment(4, comment_dict, body_is_new['is_new'], body_is_new['last_time_update'])

                self.comment_list.append(comment_dict)
        # if self.args.is_db:
        #     self.db_model.set_daily_log('', '', row_id)
        print("Done")
        print(f'Crawled post num: {len(self.post_list)}\n'
              f'Crawled comment num: {len(self.comment_list)}')

        driver.quit()

        return self.post_list, self.comment_list


def main():
    # 2020-07-17 first test

    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', nargs='+', type=str, default='틴트', help='Insert the keyword you want to crawl')
    parser.add_argument('--is_db', type=bool, default=True, help='Are you going to use DB?')
    args = parser.parse_args()

    start = time.time()
    crawler = glowpick_crawler.glowpickcrawler(args)
    post_list, comment_list = crawler.get_post_info()
    print(post_list)
    print("time :", time.time() - start)


if __name__ == "__main__":
    main()
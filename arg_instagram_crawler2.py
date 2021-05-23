# -*- coding:utf-8 -*-

# 2020/07/29 videorighter
# 2021/01/26 argparser post num refactoring
# 2021/02/02 argparser date refactoring

import requests
import json
import re
from datetime import datetime
import db_model
from unicodedata import normalize
import sys

if __name__ == "__main__":
    # 2020/07/17 first test
    # 2021/01/12 modification test
    # 2021/01/26 argparser post num test
    # 2021/02/02 argparser date test
    import arg_instagram_crawler2
    import time
    import argparse

    parser = argparse.ArgumentParser(description="Instagram crawler")
    group = parser.add_mutually_exclusive_group()

    group.add_argument('-n', '--post_num', action='store_true', help='Crawling based on the post number.')
    group.add_argument('-d', '--post_date', action='store_true', help='Crawling based on the post date.')

    parser.add_argument('keyword', type=str, help='Enter the keyword.')
    parser.add_argument('option', help='Enter the post number or date of the post.')

    arg = parser.parse_args()
    keyword = arg.keyword

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
    crawler = arg_instagram_crawler2.instagramcrawler(keyword, option)
    txt_json_list = crawler.json_parser
    crawler.insta_post_attributes(txt_json_list)

    print("time :", time.time() - start)


class instagramcrawler:

    def __init__(self, keyword, option):
        self.txt_json_list = []
        self.shortcode_list = []
        self.keyword = keyword
        self.db_model = db_model.DB_model()
        self.request_num = 0
        self.post_num = 0
        self.total_cmt_num = 0
        self.option = option

    @property
    def json_parser(self):
        url = "https://instagram28.p.rapidapi.com/hash_tag_medias"
        querystring = {"hash_tag": self.keyword}
        headers = {
            'x-rapidapi-key': "b2e40330e9msh7950ea837c1c00bp138569jsnf852e2c621b6",
            'x-rapidapi-host': "instagram28.p.rapidapi.com"
        }

        if type(self.option) == int:
            for z in range(self.option // 60 + 1):
                print(querystring)
                while True:
                    response = requests.request("GET", url, headers=headers, params=querystring)
                    self.request_num += 1
                    # 2021-03-31 추가
                    # 너무 빨리 HashTagMedias를 불러오는 경우 end_cursor가 NULL이 됨(빈 데이터)
                    # 따라서 10초로 설정
                    time.sleep(10)
                    txt = response.text.encode('utf-8')
                    try:
                        txt_json = json.loads(txt)
                    except json.decoder.JSONDecodeError:
                        continue
                    try:
                        try:
                            txt_json['data']
                        except ValueError:
                            print(f" hash_tag_medias parsing failed.")
                            continue
                    except KeyError:
                        print(f" hash_tag_medias parsing failed.")
                        continue
                    if len(txt_json) != 0:
                        self.txt_json_list.append(txt_json)
                        print(f"hash_tag_medias {self.request_num} parsing succeeded.")
                        break

                    print(f" hash_tag_medias parsing failed.")
                try:
                    try:
                        end_cursor = txt_json['data']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor']
                        print("post end_cursor: ", end_cursor)
                        if end_cursor == None:
                            break
                    except KeyError:
                        print("End cursor crawling failed.")
                        continue
                except TypeError:
                    print("End cursor crawling failed.")
                    continue

                querystring = {"hash_tag": self.keyword,
                               "next_cursor": end_cursor}

        else:
            while True:
                print(querystring)
                while True:
                    response = requests.request("GET", url, headers=headers, params=querystring)
                    self.request_num += 1
                    # 2021-03-31 추가
                    # 너무 빨리 HashTagMedias를 불러오는 경우 end_cursor가 NULL이 됨(빈 데이터)
                    # 따라서 10초로 설정
                    time.sleep(10)
                    txt = response.text.encode('utf-8')
                    try:
                        txt_json = json.loads(txt)
                    except json.decoder.JSONDecodeError:
                        continue
                    try:
                        try:
                            txt_json['data']
                        except ValueError:
                            print(f" hash_tag_medias parsing failed.")
                            continue
                    except KeyError:
                        print(f" hash_tag_medias parsing failed.")
                        continue
                    if len(txt_json) != 0:
                        self.txt_json_list.append(txt_json)
                        print(f"hash_tag_medias {self.request_num} parsing succeeded.")
                        break
                    print(f" hash_tag_medias parsing failed.")
                try:
                    try:
                        end_cursor = txt_json['data']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor']
                        print("post end_cursor: ", end_cursor)
                        if end_cursor == None:
                            break
                    except KeyError:
                        print("End cursor crawling failed.")
                        continue
                except TypeError:
                    print("End cursor crawling failed.")
                    continue

                option = time.mktime(datetime.strptime(self.option, '%Y-%m-%d').timetuple())

                # 2021-03-31 추가
                # 한번에 불러와지는 데이터 60개 중 옛날 데이터가 섞여 있으므로 크롤링이 중간에 끊기게 됨
                # -1의 경우 1주일 전 포스트가 로드됨
                # -2의 경우 인기게시글 중 하나의 포스트가 로드됨
                last_post_time = txt_json['data']['hashtag']['edge_hashtag_to_media']['edges'][-3]['node'][
                    'taken_at_timestamp']

                # option으로 입력된 날짜가 마지막 포스트 날짜보다 이전인 경우 멈춤
                if last_post_time < option:
                    print("Entered time: ", self.option,
                          time.mktime(datetime.strptime(self.option, '%Y-%m-%d').timetuple()))
                    print("Posting time of last post of end cursor: ",
                          datetime.utcfromtimestamp(last_post_time).strftime('%Y-%m-%d %H:%M:%S'), last_post_time)
                    print("Stop crawling.")
                    break

                querystring = {"hash_tag": self.keyword,
                               "next_cursor": end_cursor}

        print("json_parser length: ", len(self.txt_json_list))

        return self.txt_json_list

    def insta_post_attributes(self, txt_json_list):

        row_id = self.db_model.set_daily_log(self.keyword, 2)
        # body attributes
        for txt_json_num, i in enumerate(txt_json_list):
            print("Processing num: ", txt_json_num + 1)
            # 해당 body attribute 접근 경로
            forward_path = i['data']['hashtag']['edge_hashtag_to_media']['edges']
            headers = {
                'x-rapidapi-key': "b2e40330e9msh7950ea837c1c00bp138569jsnf852e2c621b6",
                'x-rapidapi-host': "instagram28.p.rapidapi.com"
            }
            for crawling_num, j in enumerate(forward_path):
                # 20210112 반복문 추가
                # json parsing 할 시 데이터가 제대로 불러와지지 않는 경우 parsing 결과가 0으로 나타나는 점 참고하여 조건문 추가
                while True:
                    shortcode = j['node']['shortcode']
                    post_info_url = "https://instagram28.p.rapidapi.com/media_info"
                    querystring = {"short_code": shortcode}
                    response = requests.request("GET", post_info_url, headers=headers, params=querystring)
                    self.request_num += 1
                    time.sleep(5)
                    txt = response.text.encode('UTF-8')
                    try:
                        txt_json = json.loads(txt)
                    except json.decoder.JSONDecodeError:
                        continue
                    try:
                        try:
                            if txt_json['data']:
                                print(f"shortcode: {shortcode} media_info parsing succeeded.")
                                break
                        except TypeError:
                            print(f"shortcode: {shortcode} media_info parsing failed.")
                    except KeyError:
                        print(f"shortcode: {shortcode} media_info parsing failed.")

                # 20210112 조건문 추가
                # 동영상일 경우 조회수 포함 / 동영상이 아닌 경우 조회수 -1로 표기 조건문 추가
                if j['node']['is_video'] == True:
                    view_count = j['node']['video_view_count']
                else:
                    view_count = -1

                # 20210112 추가
                # contents가 없는 경우 예외 처리 추가
                try:
                    contents = normalize('NFC', self.db_model.addslashes(
                        j['node']['edge_media_to_caption']['edges'][0]['node']['text'].replace('\n', ' ').replace(
                            '\t', '').replace('\xa0', '').replace('#', ' #')))
                except IndexError:
                    contents = None
                try:
                    post_dict = {
                        'unique_id': shortcode,
                        'keyword': self.keyword,
                        'title': '0',
                        'user_id': j['node']['owner']['id'],
                        'user_name': txt_json['data']['shortcode_media']['owner']['username'],
                        'posting_date': datetime.utcfromtimestamp(j['node']['taken_at_timestamp']).strftime(
                            '%Y-%m-%d %H:%M:%S'),
                        'view_count': view_count,
                        'like_count': j['node']['edge_liked_by']['count'],
                        'dislike_count': 0,
                        'contents': contents,
                        'user_follow': 0,
                        'user_follower': txt_json['data']['shortcode_media']['owner']['edge_followed_by']['count'],
                        'user_medias': txt_json['data']['shortcode_media']['owner']['edge_owner_to_timeline_media'][
                            'count'],
                        'comment_count': txt_json['data']['shortcode_media']['edge_media_to_comment']['count']
                    }
                except TypeError:
                    print(txt_json)
                    print("Post TypeError occurred.")
                    continue
                self.post_num += 1

                # 쿼리
                body_is_new = self.db_model.set_data_body(2, post_dict)

                # comment attribute(if comment count is not 0, then crawl shortcode's comments.)
                if post_dict['comment_count'] != 0:

                    comment_json_list = []
                    # 20210112 추가
                    # comment request 시 end_point
                    is_end_cursor = 0
                    while True:
                        while True:
                            comment_url = "https://instagram28.p.rapidapi.com/media_comments"
                            response = requests.request("GET", comment_url, headers=headers, params=querystring)
                            self.request_num += 1
                            time.sleep(5)
                            txt = response.text.encode('UTF-8')
                            try:
                                txt_json = json.loads(txt)
                            except json.decoder.JSONDecodeError:
                                continue
                            try:
                                try:
                                    end_cursor = txt_json['data']['shortcode_media']['edge_media_to_parent_comment'][
                                        'page_info']['end_cursor']
                                except TypeError:
                                    print(f"shortcode: {shortcode} comment end_cursor loading is failed.")
                                    continue
                            except KeyError:
                                print(f"shortcode: {shortcode} comment end_cursor loading is failed.")
                                continue

                            if len(txt_json) != 0:
                                print(f"shortcode: {shortcode} media_comments parsing succeeded.")
                                break
                            else:
                                print(f"shortcode: {shortcode} media_comments parsing failed.")

                        comment_json_list.append(txt_json)

                        if not txt_json['data']['shortcode_media']['edge_media_to_parent_comment']['page_info'][
                            'has_next_page']:
                            print("comment end_cursor is None.")
                            break

                        end_cursor = txt_json['data']['shortcode_media']['edge_media_to_parent_comment'][
                            'page_info']['end_cursor']
                        querystring = {"short_code": shortcode, "next_cursor": end_cursor}

                        is_end_cursor += 1

                        if is_end_cursor == 5:
                            break

                    print("length of comment_json_list: ", len(comment_json_list))

                    for k in comment_json_list:
                        path_to_comment = k['data']['shortcode_media']['edge_media_to_parent_comment']['edges']

                        for l in path_to_comment:
                            try:
                                comment_dict = {
                                    "unique_id": shortcode,
                                    "keyword": self.keyword,
                                    "comment_id": l['node']['id'],
                                    "user_name": l['node']['owner']['username'],
                                    "comment_date": datetime.utcfromtimestamp(l['node']['created_at']).strftime(
                                        '%Y-%m-%d %H:%M:%S'),
                                    "comment": normalize('NFC', self.db_model.addslashes(l['node']['text'].replace(
                                        '\n', '').replace('\t', ''))),
                                    "comment_like": l['node']['edge_liked_by']['count']
                                }
                            except TypeError:
                                print(txt_json)
                                print("Comment TypeError occurred.")
                                continue
                            self.total_cmt_num += 1
                            # 쿼리 / body_is_new여부에 따라
                            self.db_model.set_data_comment(2, comment_dict, body_is_new['is_new'],
                                                           body_is_new['last_time_update'])

                            if l['node']['edge_threaded_comments']['count'] == 0:
                                continue
                            else:
                                path_comm_comm = l['node']['edge_threaded_comments']['edges']
                                for m in path_comm_comm:
                                    try:
                                        comment_dict = {
                                            "unique_id": shortcode,
                                            "keyword": self.keyword,
                                            "comment_id": m['node']['id'],
                                            "user_name": m['node']['owner']['username'],
                                            "comment_date": datetime.utcfromtimestamp(m['node']['created_at']).strftime(
                                                '%Y-%m-%d %H:%M:%S'),
                                            "comment": normalize('NFC', self.db_model.addslashes(m['node']['text'].replace(
                                                '\n', '').replace('\t', ''))),
                                            "comment_like": m['node']['edge_liked_by']['count']
                                        }
                                    except TypeError:
                                        print(txt_json)
                                        print("Comment TypeError occurred.")
                                        continue
                                    self.total_cmt_num += 1
                                    # 쿼리 / body_is_new여부에 따라
                                    self.db_model.set_data_comment(2, comment_dict, body_is_new['is_new'],
                                                                   body_is_new['last_time_update'])
                else:
                    continue

                self.shortcode_list.append(shortcode)
        self.db_model.set_daily_log('', '', row_id)
        print(f"total requests num: {self.request_num}")
        print(f"total number of posts: ", self.post_num)
        print(f"total number of comments: ", self.total_cmt_num)


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

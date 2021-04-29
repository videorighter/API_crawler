# 2020.07.15 Jason :: SNS crawl data logger
import MySQLdb
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re


class DB_model:

    def __init__(self):
        self.db = None
        self.room_data = {}
        self.room_timer = {}
        self.isConnect = False

        self.connect()

    def __del__(self):
        self.close()

    # Database connector
    def connect(self):
        self.db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="devasdf4112", db="videorighter",
                                  charset="utf8mb4",
                                  init_command="SET NAMES UTF8MB4")

        self.isConnect = True

    # Database disconnect
    def close(self):
        self.db.close()
        self.isConnect = False

    # Check data body exists ( 본문 기존에 입력된 내용인지 체크 )
    def get_data_body_exists(self, data_pk):

        # Connection resource 재사용
        if not self.isConnect:
            self.connect()

        c = self.db.cursor(MySQLdb.cursors.DictCursor)
        c.execute(
            "SELECT count(*) as cnt, MAX(time_update) as last_time_update "
            "FROM videorighter.TBL_DATA_LIST WHERE data_pk = %s",
            [data_pk])
        row = c.fetchone()

        if not row['cnt']:
            row['last_time_update'] = '0000-00-00 00:00:00'

        return row

    """
        본문 내용 입력 모듈 
        =================
        본문 내용을 기록하며 기존 입력 내용이 있을 경우 카운트만 업데이트 하며 변화 추이를 볼수 있도록 로그에 기록시켜줍니다.

        :Method Call Example : 
        >>> set_data_body(1, {unique_id : 1, user_name : 'sample'} )

        Parameters information
        -----------------
        :param channel_type : 채널 타입 ( 1=Youtube, 2=Instagram, 3=Naver, 4=Glowpick )
        :param row : 게시물 Dictionary
            Dictionary information :  
                :key unique_id : each postings unique_id ( e.g. : instagram shortcode ) 
                :key keyword : search keyword
                :key user_name : posting user name or user nicname
                :key title : posting title
                :key user_id : 업로드 유저의 id
                :key posting_date : 작성 시간 Y-m-d H:i:s
                :key view_count : 조회수
                :key like_count : 좋아요 수
                :key dislike_count : 싫어요 수
                :key contents : 본문 내용
                :key user_follow : 유저의 팔로우 수
                :key user_follower : 유저 팔로워 수
                :key user_medias : 유저의 포스팅(미디어) 수 
                :key comment_count : 게시글의 코멘트 갯수

            이러한 형태로 보내주면 됩니다. 
            {
                unique_id : '',
                keyword : '',
                user_name : '',
                title : '',
                user_id : '',
                posting_date : '',
                view_count : '',
                like_count : '',
                dislike_count : '',
                contents : '',
                user_follow : '',
                user_follower : '',
                user_medias : '',
                comment_count : ''

            }

        Return data
        -----------------
        :return Dictionary 
            {
                is_new(Boolean) : 신규 게시물인지 여부,
                last_time_update(String) : 마지막 업데이트 시간     
            }


    """

    def set_data_body(self, channel_type, row):

        # Connection resource 재사용
        if not self.isConnect:
            self.connect()

        # 기존 입력된 내용인지 검사
        last_data = self.get_data_body_exists(row['unique_id'])
        c = self.db.cursor()

        is_new = False

        if last_data['cnt'] < 1:
            is_new = True
            # data body 신규 입력
            c.execute((
                "INSERT INTO `videorighter`.`TBL_DATA_LIST` (`channel_type`, `data_pk`, `keyword`, `data_title`, "
                "`data_creater_id`, `data_creater_name`, `data_time_create`, `data_view_count`, `data_like_count`, "
                "`data_dislike_count`, `data_body`, `data_user_follow`, `data_user_follower`, `data_user_medias`, "
                "`data_cmt_count`, `time_update`)"
                "VALUES ('{channel_type}', '{data_pk}', '{keyword}', '{data_title}', '{data_creater_id}', "
                "'{data_creater_name}', '{data_time_create}', '{data_view_count}', '{data_like_count}', "
                "'{data_dislike_count}', '{data_body}', '{data_user_follow}', '{data_user_follower}', "
                "'{data_user_medias}', '{data_cmt_count}', now())").format(

                channel_type=channel_type,
                data_pk=row['unique_id'],
                keyword=row['keyword'],
                data_title=row['title'],
                data_creater_id=row['user_id'],
                data_creater_name=row['user_name'],
                data_time_create=row['posting_date'],
                data_view_count=row['view_count'],
                data_like_count=row['like_count'],
                data_dislike_count=row['dislike_count'],
                data_body=row['contents'],
                data_user_follow=row['user_follow'],
                data_user_follower=row['user_follower'],
                data_user_medias=row['user_medias'],
                data_cmt_count=row['comment_count']
            ))

        else:
            # data body 업데이트
            c.execute((
                "UPDATE `videorighter`.`TBL_DATA_LIST` SET "
                "data_title = '{data_title}',"
                "keyword = '{keyword}',"
                "data_view_count = '{data_view_count}',"
                "data_like_count = '{data_like_count}',"
                "data_dislike_count = '{data_dislike_count}',"
                "data_user_follow = '{data_user_follow}',"
                "data_user_follower = '{data_user_follower}',"
                "data_user_medias = '{data_user_medias}',"
                "data_cmt_count = '{data_cmt_count}',"
                "time_update = now()"
                "WHERE data_pk = '{data_pk}'").format(

                data_pk=row['unique_id'],
                data_title=row['title'],
                keyword=row['keyword'],
                data_view_count=row['view_count'],
                data_like_count=row['like_count'],
                data_dislike_count=row['dislike_count'],
                data_user_follow=row['user_follow'],
                data_user_follower=row['user_follower'],
                data_user_medias=row['user_medias'],
                data_cmt_count=row['comment_count']
            ))

        # Set Data Log
        c.execute((
            "INSERT INTO `videorighter`.`TBL_DATA_LIST_LOG` (`channel_type`, `data_pk`, `keyword`, `data_view_count`, "
            "`data_like_count`, `data_dislike_count`, `data_user_follow`, `data_user_follower`, `data_user_medias`, "
            "`data_cmt_count`)"
            "VALUES ('{channel_type}', '{data_pk}', '{keyword}', '{data_view_count}', '{data_like_count}', "
            "'{data_dislike_count}', '{data_user_follow}', '{data_user_follower}', '{data_user_medias}', "
            "'{data_cmt_count}')").format(

            channel_type=channel_type,
            data_pk=row['unique_id'],
            keyword=row['keyword'],
            data_view_count=row['view_count'],
            data_like_count=row['like_count'],
            data_dislike_count=row['dislike_count'],
            data_user_follow=row['user_follow'],
            data_user_follower=row['user_follower'],
            data_user_medias=row['user_medias'],
            data_cmt_count=row['comment_count']
        ))

        return {'is_new': is_new, 'last_time_update': str(last_data['last_time_update'])}

    """
    본문의 코멘트 입력 모듈 
    ===================

    :Method Call Example : 
        >>> set_data_comment({unique_id : 1, user_name : 'sample'}, True )

    Parameters information
    -----------------
    :param row : 코멘트 정보 Dictionary
        Dictionary information :  
            :key unique_id : each postings unique_id ( e.g. : instagram shortcode ) 
            :key keyword : search keyword
            :key user_name : comment user name or user nicname
            :key comment_date : 코멘트 작성 시간 Y-m-d H:i:s
            :key comment_like : 좋아요 수
            :key contents : 본문 내용

        이러한 형태로 보내주면 됩니다. 
        {
            unique_id : '',
            keyword : '',
            user_name : '',
            comment_date : '',
            comment_like : '',
            contents : ''
        }
    :param is_new : 본문 입력시 리턴된 신규게시물인지 여부 Boolean 값 (is_new)
    :param last_time_update : set_data_body 함수에서 리턴된 마지막 업데이트 시간 값

    Return data
        -----------------
        :return 처리 결과(Boolean) : True = 입력, False = 입력안함

    """

    def set_data_comment(self, channel_type, row, is_new=False, last_time_update="1970-01-01 00:00:00"):
        # Connection resource 재사용
        if not self.isConnect:
            self.connect()

        c = self.db.cursor()

        # 기존에 수집이 되었던 포스트라면 코멘트 입력 날짜를 기준으로 오늘 이전의 코멘트는 입력하지 않음
        if not is_new:
            # 기존 게시물이면서 코멘트가 마지막 업데이트시간 이전에 작성된거라면 입력하지 않음
            if self.days_between(last_time_update, row['comment_date']).days >= 0:
                return False
        c.execute((
            "INSERT INTO `videorighter`.`TBL_CMT_DATA_LIST` (`channel_type`, `data_pk`, `keyword`, `cmt_creater_name`, "
            "`cmt_body`, `cmt_time_create` , `cmt_like_count` )"
            "VALUES ('{channel_type}', '{data_pk}', '{keyword}', '{cmt_creater_name}', '{cmt_body}', "
            "'{cmt_time_create}', '{cmt_like_count}')").format(

            channel_type=channel_type,
            data_pk=row['unique_id'],
            keyword=row['keyword'],
            cmt_creater_name=row['user_name'],
            cmt_body=row['comment'],
            cmt_time_create=row['comment_date'],
            cmt_like_count=float(row['comment_like'])
        ))

        return True

    """
    일별 / 키워드별 / 채널별 수집 기록 
    ============================
    
    :Method Call Example : 
        >>> set_daily_log(키워드, 채널타입(숫자), 업데이트시 직전 row.primary_key )

    Parameters information
    :param keyword(String) : 수집한 키워드 
    :param channel_type(Int) : SNS 채널 종류 채널 타입 ( 1=Youtube, 2=Instagram, 3=Naver, 4=Glowpick )
    :param row_id(Int)[Optional] : 최초 기록 Insert 후 생성되는 row id ( Primary Key ) 값 , 
                                    업데이트시 해당 키값을 파라메터로 보내주면 업데이트 됩니다.
    -----------------
    
    """

    def set_daily_log(self, keyword, channel_type, row_id=0):
        # Connection resource 재사용
        if not self.isConnect:
            self.connect()

        c = self.db.cursor()

        # row_id 가 없다면 최초 신규 입력
        if row_id < 1:
            c.execute((
                "INSERT INTO `videorighter`.`TBL_DAILY_LOG` (`keyword`, `channel_type`, `time_start` )"
                "VALUES ('{keyword}', '{channel_type}', now())").format(

                keyword=keyword,
                channel_type=channel_type
            ))

            row_id = self.db.insert_id()

        else:

            # 프로세스 종료시점에 시간을 기록하기위해 업데이트 row_id 필요.
            c.execute(("UPDATE `videorighter`.`TBL_DAILY_LOG` SET time_end = now() WHERE idx = '{row_id}'").format(
                row_id=row_id
            ))

        return row_id

    def set_data_body_info(self, channel_type, is_new, row):
        # Connection resource 재사용
        if not self.isConnect:
            self.connect()

        c = self.db.cursor()

        if is_new:
            # data body 신규 입력
            for opt_row in row['additional_data']:
                c.execute((
                    "INSERT INTO `videorighter`.`TBL_DATA_LIST_OPT` ("
                    "`channel_type`, `data_pk`, `keyword`, `data_key`, `data_value`, `time_update`) "
                    "VALUES ('{channel_type}', '{data_pk}', '{keyword}', '{data_key}', '{data_value}', now())").format(

                    channel_type=channel_type,
                    data_pk=row['unique_id'],
                    keyword=row['keyword'],
                    data_key=opt_row['data_key'],
                    data_value=opt_row['data_value']
                ))

        else:
            # data body info 업데이트
            for opt_row in row['additional_data']:
                c.execute((
                    "UPDATE `videorighter`.`TBL_DATA_LIST_OPT` SET "
                    "data_key = '{data_key}',"
                    "data_value = '{data_value}',"
                    "time_update = now()"
                    "WHERE data_pk = '{data_pk}' AND data_key = '{data_key}' ").format(

                    data_pk=row['unique_id'],
                    data_key=opt_row['data_key'],
                    data_value=opt_row['data_value']
                ))

        return {'is_new': is_new}

    # Utility function : addslashes for mysql prevent syntax error
    def addslashes(self, s):
        d = {'"': '\\"', "'": "\\'", "\0": "\\\0", "\\": "\\\\"}
        return ''.join(d.get(c, c) for c in s)

    # Utility function : convert "~ ago" to date and time
    def conv_date(self, d2):
        tmp = re.compile(' \(edited\)').sub('', d2)
        date = tmp.split(' ', len(tmp.split(' ')) - 3)[-1]
        value = date.split(' ')[0]
        unit = date.split(' ')[1]

        try:
            d2 = datetime.now() - timedelta(**{unit: float(value)})

        except TypeError:
            if not re.search("s ago", d2):
                d2 = d2.replace(" ago", "s ago")

            if re.search("months", d2):
                d2 = "{} days ago".format(int(value) * 30)
            elif re.search("years", d2):
                d2 = "{} days ago".format(int(value) * 365)
            value = d2.split(' ', 2)[0]
            unit = d2.split(' ', 2)[1]

            d2 = datetime.now() - timedelta(**{unit: float(value)})

        return d2

    # 최초공개: YYYY-MM-DD 과 같은 형태를 Mmm DD, YYYY와 같은 형태로 변환
    def conv_date2(self, t):
        tmp = re.compile('Premieres ').sub('', t)
        tmp = re.compile('Premiered ').sub('', tmp)
        tmp = re.compile('Streamed live ').sub('', tmp)
        date = tmp.split(' ', len(tmp.split(' ')) - 3)[-1]

        if date.find("ago") == -1:
            date = datetime.strptime(date, "%b %d, %Y")

            return date.strftime("%Y-%m-%d %H:%M:%S")

        else:
            value = date.split(' ')[0]
            unit = date.split(' ')[1]

            try:
                d2 = datetime.now() - timedelta(**{unit: float(value)})

            except ValueError:

                if not re.search("s ago", date):
                    date = date.replace(" ago", "s ago")

                if re.search("months", date):
                    date = "{} days ago".format(int(value) * 30)
                elif re.search("years", date):
                    date = "{} days ago".format(int(value) * 365)
                value = date.split(' ', 2)[0]
                unit = date.split(' ', 2)[1]
                d2 = datetime.now() - timedelta(**{unit: float(value)})

            return d2

    # ~K 와 같은 표기들 INT로 변환
    # 가끔 None이나 ''와 같은 값들은 모두 예외처리
    def conv_digit(self, n):

        try:
            tmp = re.sub(' subscribers', '', str(n))
            if tmp.find('K') >= 0:
                num = re.findall("\d+.\d+", tmp)[0]
                return int(float(num) * 1000)
            elif tmp.find("M") >= 0:
                num = re.findall("\d+.\d+", tmp)[0]
                return int(float(num) * 1000000)
            elif tmp.find("B") >= 0:
                num = re.findall("\d+.\d+", tmp)[0]
                return int(float(num) * 1000000000)
            else:
                return int(tmp)

        except (IndexError, ValueError):

            return 0

    # Utility function : date diff between two days
    def days_between(self, d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d %H:%M:%S")
        d2 = datetime.strptime(d2, "%Y-%m-%d %H:%M:%S")

        return d1 - d2

    # Utility function : data diff between two days of glowpick
    def conv_date_glow(self, t):
        if t.find("전") == -1:
            d2 = datetime.strptime(t, "%Y.%m.%d")
            return d2.strftime("%Y-%m-%d %H:%M:%S")
        else:
            value = re.compile("[0-9]+").findall(t)[0]
            unit = re.compile("[가-힣]+").findall(t)[0]
            time = int(float(value))
            if unit == "개월":
                d2 = datetime.now() - relativedelta(months=time)
            elif unit == "일":
                d2 = datetime.now() - relativedelta(days=time)
            elif unit == "시간":
                d2 = datetime.now() - relativedelta(hours=time)
            elif unit == "분":
                d2 = datetime.now() - relativedelta(minutes=time)
            elif unit == "초":
                d2 = datetime.now() - relativedelta(seconds=time)
            return d2.strftime("%Y-%m-%d %H:%M:%S")

    # Utility function : data diff between two days of naver blog
    def conv_date_naver(self, t):
        if t.find("전") == -1:
            d2 = datetime.strptime(t, "%Y. %m. %d. %H:%M")
            return d2.strftime("%Y-%m-%d %H:%M:%S")
        else:
            value = re.compile("[0-9]+").findall(t)[0]
            unit = re.compile("[가-힣]+").findall(t)[0]
            time = int(float(value))
            if unit == "시간":
                d2 = datetime.now() - relativedelta(hours=time)
            elif unit == "분":
                d2 = datetime.now() - relativedelta(minutes=time)
            elif unit == "초":
                d2 = datetime.now() - relativedelta(seconds=time)
            return d2.strftime("%Y-%m-%d %H:%M:%S")

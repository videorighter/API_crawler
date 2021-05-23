# -*- coding: utf-8 -*-
'''
2020-07-15 Jason :: SNS crawl data logger
2021-05-23 videorighter :: technical portfolio refactoring
'''
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re


# Utility function : addslashes for mysql prevent syntax error
def addslashes(s):
    d = {'"': '\\"', "'": "\\'", "\0": "\\\0", "\\": "\\\\"}
    return ''.join(d.get(c, c) for c in s)


# Utility function : convert "~ ago" to date and time
def conv_date(d2):
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
def conv_date2(t):
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
def conv_digit(n):
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
def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d %H:%M:%S")
    d2 = datetime.strptime(d2, "%Y-%m-%d %H:%M:%S")

    return d1 - d2


# Utility function : data diff between two days of glowpick
def conv_date_glow(t):
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
def conv_date_naver(t):
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


# str 제거 함수
def remove_str(str):
    if True:
        try:
            result = int(re.sub(r'[a-zA-Z가-힣ㄱ-ㅎ\s+]', '', str).strip())
        except ValueError:
            result = 0
    else:
        result = 0

    return result


# 이모티콘 제거
def remove_emoji(string):
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
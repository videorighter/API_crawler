# -*- coding:utf-8 -*-

# 2021/01/13 videorighter
# 공동주택관리정보시스템 k-apt 크롤러

import urllib.request as ul
import xmltodict
import json
import csv
import pandas as pd
import re
import os

sggcode = pd.read_csv("법정동코드 전체자료.csv", encoding='euc-kr', sep='\t')
sggcode = sggcode[sggcode['폐지여부'] == '존재']
codelist = []

for i in sggcode['법정동코드']:
    p = re.compile('\d{5}00000')
    q = re.compile('\d{2}00000000')
    m = p.search(str(i))
    n = q.search(str(i))
    if m and not(n):
        codelist.append(i)
    else:
        codelist.append(None)
is_sgg = sggcode['법정동코드'] == codelist
result_sgg = sggcode[is_sgg].reset_index(drop=True)


num = 0
develop_key = "akv5qT%2FHoSzXB7ClAWtB6UI49q1OE01M4lGa%2BPiyajcKUa6HH7%2BmevM%2BQBzWu9Sq7%2FpMMVa7h6icnbYDPmKjuA%3D%3D"

if not os.path.isdir("./bjd_result"):
    os.mkdir("./bjd_result")

for i, code in enumerate(result_sgg['법정동코드']):
    danji_url = f"http://apis.data.go.kr/1613000/AptListService1/getSigunguAptList?serviceKey={develop_key}&sigunguCode={str(code)[:5]}&numOfRows=99999"

    request = ul.Request(danji_url)
    response = ul.urlopen(request)
    rescode = response.getcode()

    if (rescode == 200):
        responseData = response.read()
        rd = xmltodict.parse(responseData)
        rdj = json.dumps(rd)
        rdd = json.loads(rdj)
    try:
        danji_code_dict = rdd['response']['body']['items']['item']
    except TypeError:
        continue

    total_info = []
    for j in range(len(danji_code_dict)):
        try:
            kaptcode = danji_code_dict[j]['kaptCode']
        except KeyError:
            continue
        info_url = f"http://apis.data.go.kr/1611000/AptBasisInfoService/getAphusBassInfo?serviceKey={develop_key}&kaptCode={kaptcode}"
        request = ul.Request(info_url)
        response = ul.urlopen(request)
        rescode = response.getcode()

        if (rescode == 200):
            responseData = response.read()
            ird = xmltodict.parse(responseData)
            irdj = json.dumps(ird)
            irdd = json.loads(irdj)

            try:
                danji_info_dict = irdd['response']['body']['item']
                num += 1
            except KeyError:
                print("KeyError")
                print(irdd)

        print(f"processing num: {num}")
        print(danji_info_dict)
        total_info.append(danji_info_dict)

    field_names = ['bjdCode', 'codeAptNm', 'codeHallNm', 'codeHeatNm', 'codeMgrNm', 'codeSaleNm', 'doroJuso', 'hoCnt',
                   'kaptAcompany', 'kaptAddr', 'kaptBcompany', 'kaptCode', 'kaptDongCnt', 'kaptFax', 'kaptMarea',
                   'kaptMparea_135', 'kaptMparea_136', 'kaptMparea_60', 'kaptMparea_85', 'kaptName', 'kaptTarea',
                   'kaptTel', 'kaptUrl', 'kaptUsedate', 'kaptdaCnt', 'privArea']

    colnames = ['법정동코드', '단지분류', '복도유형', '난방방식', '관리방식', '분양형태', '도로명주소', '호수', '시행사', '법정동주소', '시공사',
                '단지코드', '동수', '관리사무소팩스', '관리비부과면적', '전용면적별 세대현황 85이상 135 이하', '전용면적별 세대현황 136 이상',
                '전용면적별 세대현황 60 이하', '전용면적별 세대현황 60 이상 85 이하', '단지명', '건축물대장상 연면적', '관리사무소연락처',
                '홈페이지주소', '사용승인일', '세대수', '대장 전용면적합계']
    sgg = sggcode["법정동명"][sggcode["법정동코드"] == code]
    name = str(sgg).split()
    name = ' '.join(name[1:3])

    with open(f'./bjd_result/{name}.csv', 'w', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        for data in total_info:
            writer.writerow(data)

    df = pd.read_csv(f'./bjd_result/{name}.csv', encoding='utf-8')
    df.columns = colnames
    df.to_csv(f'./bjd_result/{name}.csv', encoding='euc-kr')

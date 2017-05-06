# -*- coding:utf-8 -*-

import httplib
import md5
import urllib
import random
import json
import logging
logger = logging.getLogger('mylogger')

appid = '20170504000046408'
secretKey = 'KHOCq9HrtMKmDPL0N0uk'

httpClient = None
myurl = '/api/trans/vip/translate'
fromLang = 'auto'
toLang = 'zh'
salt = random.randint(32768, 65536)


def translate(word):
    logger.info(word)
    sign = (appid + word + str(salt) + secretKey).encode('utf8')
    m1 = md5.new()
    m1.update(sign)
    sign = m1.hexdigest()
    url = myurl + u'?appid=' + appid + u'&q=' + urllib.quote(str(word)) \
          + u'&from=' + fromLang + u'&to=' + toLang + u'&salt=' + \
          str(salt) + u'&sign=' + sign
    try:
        httpClient = httplib.HTTPConnection('api.fanyi.baidu.com')
        httpClient.request('GET', url)

        # response是HTTPResponse对象
        response = httpClient.getresponse()
        trans_result = json.loads(response.read())['trans_result'][0]
        logger.info(trans_result)
        dst = trans_result['dst']
        return dst
    except Exception, e:
        print e.message
    finally:
        if httpClient:
            httpClient.close()

# -*- coding:utf-8 -*-
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import logging
import dbhelper
import json
import re
import jieba.analyse
import nltk
import thaisegment
import engsegment
logger = logging.getLogger('mylogger')

# Create your views here.

#主页
@csrf_exempt
def home(request):
    db = None
    try:
        if request.method == 'POST':
            db = dbhelper.DBHelper()
            result_dict = {}
            result_dict['hot_search_word'] = ['曼谷','芭提雅','清迈']
            location_results = db.get_hot_search(1, 4)
            hot_locations = []
            for result in location_results:
                content = {}
                content['piciture'] = None if result['picture'] == None else result['picture'].split(';')[0]
                content['scene_name'] = result['scene_name']
                scores = db.get_score(result['scene_name'])
                scores = scores['score'].split(',')
                content['chi_score'] = scores[0] if scores[0] else 0
                content['eng_score'] = scores[1] if scores[1] else 0
                content['thai_score'] = scores[2] if scores[2] else 0
                hot_locations.append(content)
            result_dict['hot_location'] = hot_locations
            travel_note_results = db.get_notes_list(1, 4)
            result_dict['recommend_travel_notes'] = travel_note_results
            return HttpResponse(json.dumps(result_dict))
        else:
            raise Exception()
    except Exception as e:
        print e.message
        return HttpResponse('404 Not Found!!')


#获得中泰英key words
def get_tag(scene_name):
    db = None
    try:
        db = dbhelper.DBHelper()
        all_tag = []
        comments = db.get_scene_comments(scene_name, -1, 'chi')['comments']
        all_tag += get_chi_tag(comments)
        comments = db.get_scene_comments(scene_name, -1, 'thai')['comments']
        all_tag += thaisegment.extract_tags(comments)
        comments = db.get_scene_comments(scene_name, -1, 'eng')['comments']
        all_tag += engsegment.extract_tags(comments)
        return all_tag
    except Exception as e:
        logger.error(e.message)
    finally:
        db.close()

def check_search_word(search_word):
    print search_word
    pattern = u'[a-zA-Z]+$'
    match = re.match(pattern, search_word)
    if match:
        return 'eng'
    pattern = u'[\u4e00-\u9fa5]'
    match = re.match(pattern, search_word)
    if match:
        return 'chi'
    return 'thai'

def get_eng_tag(comments):
    for comment in comments:
        words = nltk.word_tokenize(comment)

def get_chi_tag(comments):
    dict = {}
    for comment in comments:
        comment = json.loads(comment)
        content = comment['content']
        key_words = jieba.analyse.extract_tags(content, topK=3, withWeight=False,
                                               allowPOS=['a', 'nv', 'nr'], withFlag=True)
        for k in key_words:
            if dict.has_key(k.word):
                dict[k.word] += 1
            else:
                dict[k.word] = 1
    result = sorted(dict.iteritems(), key=lambda d: d[1], reverse=True)[:3]
    result = [term[0] for term in result]
    return result


'''
获取评论，参数为景点名，偏移量和语言
'''
def get_scene_comments(request):
    db = dbhelper.DBHelper()
    try:
        scene_name = ''
        if request.method == 'GET':
            scene_name = request.GET["scene"]
            offset = request.REQUEST.get('offset', '0')
            lang = request.REQUEST.get('lang', 'chi')
        comments = db.get_scene_comments(scene_name, int(offset), lang)
        return HttpResponse(json.dumps(comments))
    except Exception as e:
        return HttpResponse('404 NOT FOUND!!')
    finally:
        db.close()

'''
搜索方法，使用GET获取search_word;
如果搜索为小景点，返回小景点内容;
如果搜索为大景点，返回大景点内容
'''
def search(request):
    #数据库
    db = dbhelper.DBHelper()
    #搜索词
    search_word = None
    try:
        if request.method == 'GET':
            search_word = request.GET['search_word']
        if not search_word:
            raise Exception()
        #检查search_word的语言类型，分别为chi,eng,thai
        lang = check_search_word(search_word)
        #将搜索词转换为中文，且检查该景点是否存在，是否是大小景点。
        # 1为大景点，0为小景点，-1为找不到
        status, search_word = db.check_word(search_word, lang)
        result = {}
        if status == 1:
            temp_result = db.get_big_scene_content(search_word)
            result['scene_name'] = temp_result['scene_name']
            if temp_result['picture']:
                result['picture'] = temp_result['picture'].split(';')
            result['introduction'] = temp_result['introduction']
            result['scene_num'] = len(temp_result['indices'])
            result['recommend_scene'] = temp_result['recommend_scene']
            return HttpResponse(json.dumps(result))
        elif status == 0:
            temp_result = db.get_small_scene_content(search_word)
            if temp_result['picture']:
                temp_result['picture'] = temp_result['picture'].split(';')
            return HttpResponse(json.dumps(temp_result))
        else:
            raise Exception()
    except Exception as e:
        logger.error(e.message)
        return HttpResponse('404 NOT FOUND!!')
    finally:
        db.close()

'''
获取每个大景点下的小景点列表
'''
def get_scene_list(request):
    db = dbhelper.DBHelper()
    scene_name = None
    offset = 0
    try:
        if request.method == 'GET':
            scene_name = request.GET['scene_name']
            offset = request.REQUEST.get('offset', '1')
        if scene_name == None or offset == None:
            raise Exception
        temp_result = db.get_scene_list(scene_name, int(offset))

        for t in temp_result:
            t['picture'] = t['picture'].split(';')[0]
            scores = t['score'].split(',')
            t['chi_score'] = scores[0]
            t['eng_score'] = scores[1]
            t['thai_score'] = scores[2]
        return HttpResponse(json.dumps(temp_result))

    except Exception as e:
        return HttpResponse('404 NOT FOUND!!')
    finally:
        db.close()

def recommend_hot_search(request):
    db = None
    try:
        db = dbhelper.DBHelper()
        results = db.get_hot_search(0, 4)
        result_content = []
        for result in results:
            content = {}
            content['piciture'] = None if result['picture'] == None else result['picture'].split(';')[0]
            # content['titleSrc'] = '../search/search?scene=' + result['scene_name']
            content['scene_name'] = result['scene_name']
            scores = db.get_score(result['scene_name'])
            scores = scores['score'].split(',')
            content['chi_score'] = scores[0] if scores[0] else 0
            content['eng_score'] = scores[1] if scores[1] else 0
            content['thai_score'] = scores[2] if scores[2] else 0
            result_content.append(content)
        return HttpResponse(json.dumps(result_content))
    except Exception as e:
        print e.message
        return HttpResponse('404 Not Found!')

def hot_search(request):
    db = None
    try:
        index = request.GET.get('page',default=1)
        db = dbhelper.DBHelper()
        results = db.get_hot_search(int(index), 8)
        result_content = []
        for result in results:
            content = {}
            content['piciture'] = None if result['picture'] == None else result['picture'].split(';')[0]
            # content['titleSrc'] = '../search/search?scene=' + result['scene_name']
            content['scene_name'] = result['scene_name']
            scores = db.get_score(result['scene_name'])
            scores = scores['score'].split(',')
            content['chi_score'] = scores[0] if scores[0] else 0
            content['eng_score'] = scores[1] if scores[1] else 0
            content['thai_score'] = scores[2] if scores[2] else 0
            result_content.append(json.dumps(content))
        return HttpResponse(json.dumps(result_content))
    except Exception as e:
        return HttpResponse('404 Not Found!!')


def get_translation(request):
    db = dbhelper.DBHelper()
    try:
        scene_name = request.GET.get('scene_name')
        index = request.GET.get('index')
        lang = request.GET.get('lang')
        result = db.get_single_scene_comments(scene_name, index, lang)
        return HttpResponse(json.dumps(result))
    except Exception as e:
        logger.error(e.message)
    finally:
        db.close()




# db = dbhelper.DBHelper()
# comments = db.get_scene_comments('皇陵', -1)
# get_tag(comments)

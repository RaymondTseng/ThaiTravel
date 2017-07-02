# -*- coding:utf8 -*-

import logging
import MySQLdb
import MySQLdb.cursors
import json
import numpy as np
import translate
logger = logging.getLogger('mylogger')
class DBHelper:
    def __init__(self):
        self.conn = MySQLdb.connect('localhost', 'root', '0719', 'NewThaiTravel',
                               cursorclass = MySQLdb.cursors.DictCursor,
                               charset = 'utf8mb4')
        self.cur = self.conn.cursor()


    '''
    检查景点是否存在且景点是否是大地点，若搜索词为英文或泰文，则会转换为中文
    1为大地点，0为小地点
    '''
    def check_word(self, word, lang):
        if lang != 'chi':
            location = lang + '_location'
            sql = 'select chi_location from location_set where ' + location + ' like %s' % '"' + word + '%"'
            self.cur.execute(sql)
            result = self.cur.fetchall()
            if result:
                word = result[0]['chi_location']
            else:
                return -1
        sql = 'select ifset from chi_scene where scene_name = %s' % '"' + word  + '"'
        self.cur.execute(sql)
        result = self.cur.fetchall()
        if result:
            return result[0]['ifset'], word
        else:
            return -1


    def get_scene_list(self, scene_name, index):
        sql = 'select indices from chi_scene where scene_name =%s' % '"' + scene_name + '"'
        self.cur.execute(sql)
        result = self.cur.fetchall()
        indices = []
        for i in result[0]['indices'].split(','):
            if i:
                indices.append(int(i))
        sql = "select scene_name,picture,score from chi_scene where id in (%s)"
        start_index = (index - 1) * 10
        end_index = index * 10
        indices_list = ', '.join((map(lambda x: '%s', indices[start_index:end_index])))
        self.cur.execute(sql % indices_list, indices[start_index:end_index])
        new_result = self.cur.fetchall()
        # for result in new_result:
        #     result['score'] = [float(s) for s in result['score'].split(',')]
        return new_result

    '''
    获取小景点内容
    '''
    def get_small_scene_content(self, scene_name):
        sql = 'select * from chi_scene where scene_name = %s' % '"' + scene_name + '"'
        self.cur.execute(sql)
        temp_result = self.cur.fetchall()
        result = temp_result[0]
        scores = result['score'].split(',')
        count = 0
        total_score = 0
        for index, s in enumerate(scores):
            s = float(str(s))
            scores[index] = s
            if s != 0:
                count += 1
                total_score += s
        result['chi_score'] = '%1.f' % scores[0]
        result['eng_score'] = '%1.f' % scores[1]
        result['thai_score'] = '%1.f' % scores[2]
        result['total_score'] = '%1.f' % (float(total_score) / count)
        if result['introduction'] != None:
            result['description'] = result['introduction'][:100] + '...'
        del result['score']
        del result['indices']
        result['comments_num'] = self.get_scene_comment_num(scene_name)
        result['tag'] = self.get_small_scene_tag(scene_name)
        sql = 'select x,y from location_set where chi_location like %s' % "'%" + scene_name + "%'"
        self.cur.execute(sql)
        temp_result = self.cur.fetchall()
        if temp_result:
            temp_result = temp_result[0]
            for key, value in temp_result.iteritems():
                result[key] = value
        return result

    def get_scene_comment_num(self, chi_scene_name):
        sql = 'select * from location_set where chi_location like %s' % ('"%' + chi_scene_name + '%"')
        self.cur.execute(sql)
        result = self.cur.fetchall()
        scene_names = {}
        scene_names['chi_scene'] = chi_scene_name
        if not result[0]['eng_location'] == 'null':
            scene_names['eng_scene'] = result[0]['eng_location']
        if not result[0]['thai_location'] == 'null':
            scene_names['thai_scene'] = result[0]['thai_location']
        num = 0
        for key,value in scene_names.iteritems():
            sql = 'select indices from %s where scene_name = %s' % (key, '"' + value + '"')
            self.cur.execute(sql)
            result = self.cur.fetchall()
            if result:
                result = result[0]
                temp = result['indices'].split(',')
                num += int(len(temp))
        return num
    '''
    获取大景点内容
    '''
    def get_big_scene_content(self, scene_name):
        sql = 'select * from chi_scene where scene_name = %s' % '"' + scene_name + '"'
        self.cur.execute(sql)
        temp_result = self.cur.fetchall()
        result = temp_result[0]
        if len(result['introduction']) > 800:
            result['introduction'] = result['introduction'][:800] + '...'
        result['recommend_scene'] = self.get_recommend_scene_list(scene_name)
        return result

    def get_small_scene_tag(self, scene_name):
        sql = 'select * from location_set where chi_location like %s' % '"%' + scene_name + '%"'
        self.cur.execute(sql)
        result = self.cur.fetchall()
        scene_names = {}
        scene_names['chi'] = scene_name
        if not result[0]['eng_location'] == 'null':
            scene_names['eng'] = result[0]['eng_location']
        if not result[0]['thai_location'] == 'null':
            scene_names['thai'] = result[0]['thai_location']
        sentiment = {}
        top_words_score = []
        top_words = []
        n_words = {}
        for key, value in scene_names.iteritems():
            table = key + '_scene'
            value = value.split('_')[-1]
            sql = 'select tag from %s where scene_name like %s' % (table, "'%" + value + "%'")
            self.cur.execute(sql)
            result = self.cur.fetchall()
            if result:
                tag_dict = eval(str(result[0]['tag']))
                if tag_dict:
                    if tag_dict.has_key('top4'):
                        sum = np.array([int(str(v)) for v in tag_dict['top4'].values()]).sum()
                        for word, count in tag_dict['top4'].iteritems():
                            if isinstance(word,str):
                                word = word.decode('unicode-escape')
                            top_words.append(word)
                            top_words_score.append(int(str(count)) / float(sum))
                    if tag_dict.has_key('nnn'):
                        n_words[key] = tag_dict['nnn']
            table = key + '_sentiment_score'
            sql = 'select score from %s where location like %s' % (table, '"%' + value + '"')
            self.cur.execute(sql)
            result = self.cur.fetchall()
            if result and n_words.has_key(key):
                sentiment[key] = {}
                sentiment_words = json.loads(str(result[0]['score']))
                colors = []
                data = []
                colors_ditc = {}
                colors_ditc['-2'] = '#B22222'
                colors_ditc['-1'] = '#ec5845'
                colors_ditc['0'] = '#C0C0C0'
                colors_ditc['1'] = '#46d185'
                colors_ditc['2'] = '#00a69d'
                for word, count in n_words[key].iteritems():
                    word = word.decode('unicode-escape')
                    if sentiment_words.has_key(word):
                        temp = {}
                        colors.append(str(sentiment_words[word]))
                        temp['name'] = word
                        temp['value'] = count
                        data.append(temp)
                        # words.append(word)
                        # values.append(count)
                sentiment[key]['data'] = data
                # sentiment[key]['words'] = words
                # sentiment[key]['values'] = values
                for index, color in enumerate(colors):
                    colors[index] = colors_ditc[color]
                sentiment[key]['color'] = colors
        result = {}
        if sentiment:
            result['pie'] = sentiment
        if top_words and top_words_score:
            result['bar'] = {}
            result['bar']['top_words'] = top_words
            result['bar']['score'] = top_words_score
        return result

    '''
    获取小景点概要内容，包括图片，景点名，分数
    '''
    def get_scene_summary_by_index(self, index):
        sql = 'select scene_name, score, picture from chi_scene where id = %s' % index
        self.cur.execute(sql)
        temp_result = self.cur.fetchall()
        result = temp_result[0]
        result['picture'] = result['picture'].split(';')[0]
        return result

    '''
    获取大景点内容中所推荐的小景点列表
    '''
    def get_recommend_scene_list(self, scene_name):
        sql = 'select indices from chi_scene where scene_name = %s' % '"' + scene_name + '"'
        self.cur.execute(sql)
        temp_result = self.cur.fetchall()
        indices = temp_result[0]['indices'].split(',')
        if len(indices) > 4:
            indices = self.sort_recommend_scene_list(indices)
        result = []
        for index in indices:
            if index:
                result.append(self.get_scene_summary_by_index(int(index)))
        for res in result:
            res['score'] = [float(s) for s in res['score'].split(',')]
        return result

    '''
    为大景点包含的小景点排序，认为评论数多的景点为热门景点，选取前4个展示
    '''
    def sort_recommend_scene_list(self, indices):
        sql = 'select length(indices) from chi_scene where id = %s'
        index_dict = {}
        for index in indices:
            if index:
                self.cur.execute(sql % int(index))
                result = self.cur.fetchall()
                index_dict[index] = result[0]
        result = []
        for index in sorted(index_dict.items(), key=lambda item:item[1], reverse=True)[:4]:
            result.append(index[0])
        return result
    '''
    计算用户等级
    '''
    def compute_user_level(self, line, index):
        user_level = 0
        if line['user_level']:
            user_level = int(line['user_level'])
            line.pop('user_level')
        comment_counts = 0
        if line['comment_counts']:
            comment_counts = int(line['comment_counts'])
            line.pop('comment_counts')
        scene_comment_counts = 0
        if line['scene_comment_counts']:
            scene_comment_counts = int(line['scene_comment_counts'])
            line.pop('scene_comment_counts')
        agree_counts = 0
        if line['agree_counts']:
            agree_counts = int(line['agree_counts'])
            line.pop('agree_counts')
        if user_level > 3 or comment_counts > 20 or scene_comment_counts > 10 \
                or agree_counts >10:
            line['user_label'] = u'旅游达人'
        else:
            line['user_label'] = u'旅游小白'
        line['index'] = index
        return line

    '''
    获取某个景点的某条评论
    args:
        scene_name:景点名
        index:评论偏移量
        lang:语种
    '''
    def get_single_scene_comments(self, scene_name, index, lang):
        table = lang + "_scene"
        result_dict = {}
        if lang != 'chi':
            sql = 'select %s from location_set where chi_location like %s' % (lang + '_location', '"%' + scene_name + '%"')
            self.cur.execute(sql)
            result = self.cur.fetchall()
            if result[0][lang + '_location'] == 'null':
                return
            else:
                scene_name = result[0][lang + '_location']
        scene_name = scene_name.split('_')[-1]
        table = lang + '_comments'
        sql = 'select id from %s where location like %s' % (table, '"%' + scene_name + '%"')
        self.cur.execute(sql)
        result = self.cur.fetchall()
        indices = []
        if result:
            for i in result:
                indices.append(int(i['id']))
        if not int(index) < len(indices):
            return
        id = indices[int(index)]
        sql = 'select user_name, head, content, title, user_level, comment_counts' \
              ', scene_comment_counts, agree_counts from %s where id = %s'
        self.cur.execute(sql % (lang + "_comments", int(id)))
        result = self.cur.fetchall()
        if result:
            result = result[0]
            temp = result['content']
            result['content'] = {}
            result['content']['chi'] = translate.translate(temp, 'zh')
            if lang == 'thai':
                result['content']['eng'] = translate.translate(temp, 'en')
        return result

    '''
    获取景点评论
    args:
        scene_name:景点名
        index:景点评论下标
        lang:语言 (chi,eng,thai)
    '''
    def get_scene_comments(self, scene_name, index, lang):
        #数据库表名
        table = lang + "_comments"
        result_dict = {}
        if lang != 'chi':
            sql = 'select %s from location_set where chi_location like %s' % (lang+'_location', '"%' + scene_name + '%"')
            self.cur.execute(sql)
            result = self.cur.fetchall()
            if result[0][lang+'_location'] == 'null':
                return
            else:
                scene_name = result[0][lang+'_location']
        scene_name = scene_name.split('_')[-1]
        sql = 'select id from %s where location like %s' % (table, '"%' + scene_name + '%"')
        self.cur.execute(sql)
        result = self.cur.fetchall()
        indices = []
        if result:
            for i in result:
                indices.append(int(i['id']))
            # for i in result[0]['indices'].split(','):
            #     if i:
            #         indices.append(int(i))
        result_set = []
        sql = 'select user_name, head, content, title, user_level, comment_counts' \
              ', scene_comment_counts, agree_counts, score from %s where id = %s'
        start = index * 5
        last = len(indices) if (start + 5) > len(indices) else (start + 5)
        if index == -1:
            start = 0
            last = len(indices)
        count = start
        for i in indices[start:last]:
            if i:
                self.cur.execute(sql % ( lang+"_comments",int(i)))
                result = self.cur.fetchall()
                if result:
                    result_set.append(self.compute_user_level(result[0], count))
                    count += 1
        if last == len(indices):
            sql = 'select url from %s where id = %s'
            self.cur.execute(sql % ( lang+"_comments", indices[0]))
            result = self.cur.fetchall()
            if result:
                result_dict['url'] = result[0]
        if index == 0:
            words, values = self.get_adj_words(scene_name, lang)
            result_dict['adj_words'] = {}
            if words and values:
                result_dict['adj_words']['words'] = words
                result_dict['adj_words']['values'] = values
            else:
                result_dict['adj_words'] = '暂无标签'
        if result_set:
            result_dict['comments'] = result_set
            result_dict['max_comments_num'] = len(indices)/ 5
            result_dict['lang'] = lang
        return result_dict

    def get_adj_words(self, scene_name, lang):
        table = lang + '_scene'
        sql = 'select tag from %s where scene_name like %s' % (table, "'%" + scene_name + "%'")
        self.cur.execute(sql)
        result = self.cur.fetchall()
        words = []
        values = []
        if result:
            result = result[0]
            if result.has_key('tag') and result['tag'] != None:
                temp = (eval(str(result['tag'])))
                if temp.has_key('adj'):
                    adj_words = temp['adj']
                    for key, value in adj_words.iteritems():
                        words.append(key.decode('unicode-escape'))
                        values.append(str('%.2f' % (float(value) * 100)) + '%')
        return words, values

    def get_score(self, scene_name):
        sql = 'select score from chi_scene where scene_name like %s' % "'%" + scene_name + "%'"
        self.cur.execute(sql)
        results = self.cur.fetchall()
        return results[0]

    def get_hot_search(self, index, page_size):
        start_index = (index - 1) * page_size
        end_index = index * page_size
        sql = 'select * from chi_scene where length(indices) > 100 and ' \
              'ifset = 0 and picture is not null order by length(indices) desc'
        self.cur.execute(sql)
        results = self.cur.fetchall()
        new_results = []
        for result in results:
            scores = result['score'].split(',')
            for score in scores:
                if score == "0":
                    break
            else:
                new_results.append(result)
        new_results = new_results[start_index:end_index]
        return new_results

    def get_notes_list(self, index, page_size):
        start_index = (index - 1) * page_size
        end_index = index * page_size
        sql = 'select * from chi_travel_notes where id >= %s and id <= %s' % (start_index, end_index)
        self.cur.execute(sql)
        results = self.cur.fetchall()
        for result in results:
            description = ''
            contents = result['content'].split('||')
            for content in contents:
                c = eval(str(content))
                if c['node'] == 'text':
                    description = c['text_content'][:50]
                    break
            del result['content']
            result['description'] = description
        return results


    def close(self):
        self.conn.close()

# db = DBHelper()
# print db.get_small_scene_tag(u'白金时尚购物中心')
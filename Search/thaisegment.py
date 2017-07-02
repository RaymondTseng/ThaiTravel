# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import tensorflow as tf
import numpy as np
from ThaiTravel import settings
import logging
import json
logger = logging.getLogger('mylogger')

max_sentence_len = 100
def load_graph(frozen_graph_filename):
  # We parse the graph_def file
  with tf.gfile.GFile(frozen_graph_filename, "rb") as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())

    # We load the graph_def in the default graph
  with tf.Graph().as_default() as graph:
    tf.import_graph_def(
      graph_def,
      input_map=None,
      return_elements=None,
      name="prefix",
      op_dict=None,
      producer_op_list=None
    )
  return graph


def length(data):
  used = tf.sign(tf.abs(data))
  length = tf.reduce_sum(used, reduction_indices=1)
  length = tf.cast(length, tf.int32)
  return length




def standard_data(text,vec_path):

    with open(vec_path,'r')as f:
        vec=[i.split('|')[0] for i in f]
    f.close()

    r_vec=vec[2:]
    test=[]#测试文本
    test.append(list(text))

    test_v=[]    #文本向量
    for each in test:#泰文数字化
        v=[]
        for e in each:
            if e in r_vec:
                v.append(r_vec.index(e))
            else:
                v.append(r_vec.index('<UNK>'))
        test_v.append(v)

    #按百分开，用0补齐
    target=[]
    source_text=[]#保存原文本
    index_text=0

    for x in test_v:
        text=test[index_text]
        index_text+=1

        if len(x)%100!=0:
            d=100-len(x)%100
            for i in range(d):
                x.append(0)
            d2=len(x)/100
            lin=[]#临时
            f=0
            g=100
            for j in range(d2):
                lin.append(x[f:g])
                source_text.append(text[f:g])
                f+=100
                g+=100
            target.append(lin)
        else:
            d2 = len(x) / 100
            lin = []  # 临时
            f = 0
            g = 100
            for j in range(d2):
                lin.append(x[f:g])
                source_text.append(text[f:g])
                f += 100
                g += 100
            target.append(lin)

    return np.asarray(target[0]),source_text

def thai_seg(sentence):
    source_vec_path = settings.BASE_DIR + "/static/resource/vec.txt"
    standard_sentence,source_text=standard_data(sentence,source_vec_path)
    frozen_model_filename = settings.BASE_DIR + "/static/resource/thai_seg_model.pbtxt"
    graph = load_graph(frozen_model_filename)
    # for op in graph.get_operations():
    #     print(op.name, op.values())
    #batchSize = 2000
    x = graph.get_tensor_by_name('prefix/input_placeholder:0')
    transition = graph.get_tensor_by_name('prefix/transitions:0')
    reshape7 = graph.get_tensor_by_name('prefix/Reshape_7:0')
    feed_dict = {x: standard_sentence[:]}#feed_dict = {x: tX[:batchSize]}

    result=[]#保存分词结果
    with tf.Session(graph=graph) as sess:
        sequence_length = length(standard_sentence)
        sequence_length_val = sequence_length.eval()
        y_transition, y_reshape7 = sess.run([transition, reshape7], feed_dict=feed_dict)

        sentence_index=0#句子索引
        results = []
        for size in range(len(standard_sentence)):
            sentence=source_text[sentence_index]
            sentence_index+=1
            sequence_length_ = sequence_length_val[size]
            viterbi_sequence, _ = tf.contrib.crf.viterbi_decode(
                y_reshape7[size][:sequence_length_], y_transition)
            seg_line=''
            #print viterbi_sequence


            seg_result=[]#保存分词结果
            text_index=0#原文本的索引
            seg=''#切片
            for i in viterbi_sequence:
                if i==0:
                    if seg!='':
                        seg_result.append(seg)
                    seg_result.append(sentence[text_index])
                    seg=''
                else:
                    if i==1:
                        seg=sentence[text_index]
                    if i==2:
                        seg+=sentence[text_index]
                    if i==3:
                        seg+=sentence[text_index]
                        seg_result.append(seg)
                        seg=''
                seg_line+=str(i)+' '#vec
                text_index+=1#text
            result.append(seg_line)
            temp = u''
            for line in seg_result:
                temp += str(line) + '/'
                results.append(str(line))
        return results

def extract_tags(comments):
    idf = {}
    temp = []
    if not comments:
        return []
    for comment in comments:
        comment = json.loads(comment)
        content = comment['content']
        result = thai_seg(content)
        tf = {}
        for r in result:
            if tf.has_key(r):
                tf[r] += 1
            else:
                tf[r] = 1
        for key, value in tf.iteritems():
            tf[key] = float(value) / len(result)
        temp.append(tf)
        result = set(result)
        for r in result:
            if idf.has_key(r):
                idf[r] += 1
            else:
                idf[r] = 1
    for key, value in idf.iteritems():
        idf[key] = len(comments) / (value + 1)
    result = []
    for tf in temp:
        for key, value in tf.iteritems():
            tf[key] = value * idf[key]
        result += (sorted(tf.items(), key=lambda d: d[1], reverse=True)[:3])
    result = sorted(result, key=lambda d: d[1], reverse=True)
    result = [term[0] for term in result[:3]]
    return result






#
# 对于单独字符，不跟前后构成词的，我们标注为S (0)
# 跟后面字符构成词且自身是第一个字符的，我们标注为B (1)
# 在成词的中间的字符，标注为M (2)
# 在词尾的字符，标注为E (3)

# s = [u'55 ผู้เชี่ยวชาญด้านความมั่นคง ของพรรครีพับลิกัน ลงนามจดหมายเปิดผนึกขวางโดนัลด์ ทรัมป์ ประกาศไม่ขอเลือกเป็นประธานาธิบดีสหรัฐฯ..เตือนมหาเศรษฐีจากนิวยอร์กผู้นี้ จะกลายเป็นปธน.ที่หุนหันพลันแล่นมากสุดในประวัติศาสตร์ผู้นำชาติพญาอินทรี',
# u'เมื่อวันที่ 9 ส.ค.59 สำนักข่าวต่างประเทศรายงานว่า บรรดาผู้เชี่ยวชาญด้านความมั่นคงแห่งชาติ สมาชิกพรรครีพับลิกัน จำนวนถึง 50 คน รวมทั้ง นายไมเคิล เฮย์เดน อดีตผู้อำนวยการสำนักงานข่าวกรองกลางแห่งสหรัฐฯ ​(ซีไอเอ) ได้พากันร่วมลงนามในจดหมายเปิดผนึก เตือนนายโดนัลด์ ทรัมป์ ตัวแทนพรรครีพับลิกันชิงตำแหน่งประธานาธิบดีสหรัฐฯ จะเป็นประธานาธิบดีที่หุนหันพลันแล่น ขาดความระมัดระวังมากที่สุดในประวัติศาสตร์ของสหรัฐฯ โดยนายเฮย์เดน อดีต ผอ.ซีไอเอ ชี้ว่า ทรัมป์ ขาดคุณสมบัติ, ขาดคุณค่าและไม่มีประสบการณ์ทางการเมืองในการเป็นประธานาธิบดีสหรัฐฯ',
# u'บีบีซี แจ้งว่า จดหมายเปิดผนึกดังกล่าวที่ลงนามโดยบรรดาผู้เชี่ยวชาญด้านความมั่นคงแห่งชาติ ของพรรครีพับลิกัน ถือเป็นความเคลื่อนไหวล่าสุดของสมาชิกพรรครีพับลิกันที่ร่วมขัดขวางนายโดนัลด์ ทรัมป์ มหาเศรษฐีจากรัฐนิวยอร์ก ในการชิงชัยตำแหน่งประธานาธิบดีสหรัฐฯ ในปลายปีนี้ หลังจากก่อนหน้านี้ มีนักการเมืองชื่อดังของพรรครีพับลิกันหลายคน รวมทั้งอดีตประธานาธิบดีจอร์จ ดับเบิลยู บุช แสดงท่าทีชัดเจน ไม่สนับสนุนทรัมป์ในการเป็นตัวแทนพรรคไปชิงตำแหน่งประธานาธิบดีสหรัฐฯ แข่งกับนางฮิลลารี คลินตัน ตัวแทนจากพรรคเดโมแครต',
# u'ทั้งนี้ เนื้อหาในจดหมายเปิดผนึกฉบับนี้ได้ชี้ให้เห็นว่า ทรัมป์ ได้ทำลายนโยบายต่างประเทศของพรรครีพับลิกันที่ดำเนินมาเป็นเวลาหลายปี จากการหาเสียงในบางโอกาสของเขา พร้อมกับระบุว่า ไม่มีใครในหมู่พวกเราที่จะโหวตเลือกโดนัลด์ ทรัมป์ เป็นประธานาธิบดีของสหรัฐฯ']
# print thai_seg(s)
# result = extract_tags(s)
# for r in result:
#     print r



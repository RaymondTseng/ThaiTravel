# -*- coding:utf-8 -*-
import MySQLdb
import MySQLdb.cursors
import base64
import logging
logger = logging.getLogger('mylogger')

class DBHelper:
    def __init__(self):
        self.conn = MySQLdb.connect('localhost', 'root', '0719', 'ThaiTravel',
                               cursorclass = MySQLdb.cursors.DictCursor,
                               charset = 'utf8mb4')
        self.cur = self.conn.cursor()

    '''
    注册方法，输入帐号密码
    '''
    def register(self, account, password, user_name):
        result = {}
        sql = "select * from user where account = %s"
        self.cur.execute(sql, [account])
        temp_result = self.cur.fetchall()
        if temp_result:
            result['status'] = False
            result['info'] = 'account exist'
        else:
            password = base64.b64decode(password)
            sql = 'insert into user values(null, %s, %s, %s)'
            self.cur.execute(sql, (account, password, user_name))
            self.conn.commit()
            result['status'] = True
            result['info'] = 'success'
        return result

    def login(self, account, password):
        result = {}
        sql = "select * from user where account = %s"
        self.cur.execute(sql, [account])
        temp_result = self.cur.fetchall()
        logger.info(temp_result)
        if temp_result:
            temp_result = temp_result[0]
            psw = temp_result['password']
            psw = base64.b64encode(psw)
            if psw == password:
                result['status'] = True
                result['info'] = 'success'
            else:
                result['status'] = False
                result['info'] = 'password error'
        else:
            result['status'] = False
            result['info'] = 'account not exist'
        return result
    def close(self):
        self.conn.close()

# db = DBHelper()
# temp = base64.b64encode('1234')
# print db.login('888', temp)

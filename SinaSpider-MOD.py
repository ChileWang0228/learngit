#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests
import json
import re
import pandas
import pymysql
import datetime
import pymongo

def WriteInText(id,page):

        Text, CommentID, Create_at, screen_name=getWeibo(id,page)
        for i in range(len(Text)):
                content=Create_at[i]+'->'+screen_name+':'+Text[i]
                with open('C:\\Users\\ZJT\\Desktop\\Weibo.txt', 'a+',encoding='utf-8')as f:
                        f.write('\n')
                        f.write(content + '\n')
                        f.write('--------------\n')

#正则处理微博内容多余字符
def ContentCoping(text):
        #text="<a href='/n/玩期货游戏'>@玩期货游戏</a>：我猜博主就是个穷屌丝，蜗居上海，连份像样工作都没有。"
        text_temp=re.findall("<a href=",text)
        if(text_temp):
                text=text.replace("<a href='/n/",'')
                text = text.replace("</a>", '')
                text = text.replace(">", '')
                text=re.split("'",text)
                return text[1]
        else:
                return text
#爬取微博内容
def getWeibo(id, page):  # id（字符串类型）：博主的用户id，page（整型）：微博翻页参数
        url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=' + str(id) + '&containerid=107603' + str(id)+ '&page=' + str(page)
        response = requests.get(url)
        ob_json = json.loads(response.text)
        Text=[]#微博内容
        CommentID=[]#评论id
        Create_at=[]#发表时间
        screen_name=''
        for i in ob_json['data']['cards']:
                if(i['card_type']==9):
                        screen_name=i['mblog']['user']['screen_name']#昵称
                        text=i['mblog']['text']
                        id=i['mblog']['id']#长文id，评论id
                        create_time=i['mblog']['created_at']
                        create_time=create_time
                        text=re.split('<span class="url-icon">',text)

                        text=text[0]
                        AllText=re.search('​​​...全文$',text)#长微博，则需要得到id并进入url得到相应的长文
                        try:
                                if(AllText):
                                        Long_Text_URL='https://m.weibo.cn/statuses/extend?id='+str(id)
                                        resp=requests.get(Long_Text_URL)
                                        long_text_json=json.loads(resp.text)
                                        text=long_text_json['data']['longTextContent']
                                text = text.replace('<br />', '\n')#换行
                        except:
                                pass

                        Create_at.append(create_time)
                        Text.append(ContentCoping(text))
                        CommentID.append(id)

        return Text,CommentID,Create_at,screen_name



# 返回某条微博的热门评论的list
def getComments(id, page):  # id（字符串类型）：某条微博的id，page（整型）：评论翻页参数
        try:
                url = 'https://m.weibo.cn/api/comments/show?id=' +str(id) + '&page=' + str(page)
                response = requests.get(url)
                if(response.text):#非空
                        ob_json = json.loads(response.text)
                        #print('data' in ob_json.keys())
                        #print('data' in ob_json['data'].keys())
                        if('data'in ob_json and 'data' in ob_json['data'].keys()):#判断是否存在键值对
                                Hot_Data_List=ob_json['data']['data']#评论列表
                                Like_Count=[]#赞
                                Comment=[]#热门评论
                                Comment_User=[]#评论用户
                                Creat_At=[]#评论时间
                                for i in Hot_Data_List:
                                        Creat_At.append(i['created_at'])
                                        Like_Count.append(i['like_counts'])
                                        text=re.split('<br/><span class="url-icon">',i['text'])
                                        Comment.append(text[0])
                                        Comment_User.append(i['user']['screen_name'])
                                return(Creat_At,Like_Count,Comment_User,Comment)
        except:
                print('完成')
        return None


def CommentMerge(list1,list2):#合并列表
        for i in list2:
                list1.append(i)
        return list1

def CommentTop(Creat_At,Like_Count, Comment_User,Comment_Text):#根据赞排序输出Top前20
        name=['Like_Count']
        Like=[]#赞
        Creat=[]#评论时间
        Comment_Content=[]#评论内容
        Comment_Player=[]#评论者
        Count_File=pandas.DataFrame(list(Like_Count),columns=name)
        Count_File_Sort=Count_File['Like_Count'].sort_values(ascending=False)
        for i in range(len(Count_File_Sort.index)):
                index=Count_File_Sort.index[i]#TOP前20索引
                Creat.append(Creat_At[index])
                Like.append(Like_Count[index])
                Comment_Player.append(Comment_User[index])
                Comment_Content.append(Comment_Text[index])
                if(i>19):
                        break
        return(Creat,Like,Comment_Player,Comment_Content)

def CommentCoping(str):#正则处理评论多余字符
                text = re.split('<a href=\'https://m.weibo.cn/n/', str)
                User_Name = text[0]
                if (len(text) > 1):
                        text = re.split("'>", text[1])
                        text = re.split('</a>', text[1])
                        name = text[0]
                        Reply_Content = text[1]
                        Comment = User_Name + name + Reply_Content#评论内容组装
                        return(Comment)
                else:
                        return text[0]


def DisplayWeibo(id,page,name):#热门大V
        Weibo=getWeibo(id,page)
        Content=Weibo[0]#微博内容列表
        CommentID=Weibo[1]#微博评论ID列表
        for i in range(len(CommentID)):
                Creat_At = []  # 评论时间
                Like_Count = []  # 赞
                Comment_User = []  # 评论用户
                Comment_Text = []  # 评论内容
                for j in range(500):#获取前100页排序并根据点赞数输出前20评论
                        Comment=getComments(CommentID[i], j)#第j页热门评论
                        if(Comment):#非空
                                Creat_At=CommentMerge(Creat_At,Comment[0])#合并列表
                                Like_Count=CommentMerge(Like_Count,Comment[1])
                                Comment_User=CommentMerge(Comment_User,Comment[2])
                                Comment_Text=CommentMerge(Comment_Text,Comment[3])

                CT=CommentTop(Creat_At,Like_Count, Comment_User,Comment_Text)
                print(Content[i])#微博内容
                for i in range(len(CT[0])):
                        time=CT[0][i]
                        like=CT[1][i]
                        user=CT[2][i]
                        content=CT[3][i]
                        content=CommentCoping(content)#处理评论内容多余字符
                        print(u'%s -> @%s:%s   %s👍'%(time,user,content,like))

                print('----------')




def DisplayCommonUser(id,page,name):
        Weibo = getWeibo(id, page)
        Content = Weibo[0]  # 微博内容列表
        for content in Content:
                WriteInText(content,name)


def WriteInMysql(user_id, page):
        # 连接数据数据库
        db = pymysql.connect('localhost', 'root', '', 'sinaweibo')
        # 获取操作游标
        cursor = db.cursor()
        # sql="create table WeiboContent(\
        #         id INT NOT NULL AUTO_INCREMENT,\
        #         user_id VARCHAR (100) NOT NULL,\
        #         create_date VARCHAR (20),\
        #         user_screen_name VARCHAR (100) ,\
        #         weibo_content VARCHAR (10000) NOT NULL ,\
        #         PRIMARY KEY (id))ENGINE=InnoDB DEFAULT CHARSET=utf8"#保证编码为utf-8
        # cursor.execute(sql)
        Text, CommentID, Create_at, screen_name = getWeibo(user_id, page)
        for i in range(len(Text)):
                if (len(Create_at[i]) == 5):#添加今年的年份,微博今年的年份是不显示的
                        Create_at[i] = str(datetime.datetime.now().year)+'-'+Create_at[i]
                try:
                        sql = "INSERT INTO WeiboContent(user_id, create_date, user_screen_name, weibo_content)VALUES('%s', '%s', '%s', '%s')"\
                              %(user_id,Create_at[i],str(screen_name),Text[i])

                        cursor.execute(sql)  # 执行sql语句
                        db.commit()  # 提交到数据库执行
                except:
                        print('error')
                        db.rollback()

        db.close()

def WriteInMongo(user_id, page):
        db=pymongo.MongoClient('mongodb://localhost:27017/')
        mydb=db['SinaWeibo']
        Text, CommentID, Create_at, screen_name = getWeibo(user_id, page)
        mycol=mydb['WeiboContent']
        for i in range(len(Text)):
                try:
                        mydict = {"user_id":user_id , "create_date": Create_at[i], "user_screen_name":str(screen_name), "weibo_content":Text[i]}
                        mycol.insert_one(mydict)
                except:
                          print('Error')
                          continue


if __name__=='__main__':
        # id='6077805247'#绿帽社
        # name='绿帽社'
        # id1='2326757172'
        # name1='五彩斑斓·黑'
        # id2='2273230451'
        # name2='HeJeo_Leong'
        id3='1565668374'
        id4='1670458304'#神嘛事儿
        # # for i in range(1):#页数
        # #         DisplayWeibo(id,i,name)
        # for i in range(5000):
        #         print(i)
        #         WriteInText(id3,i)
        for i in range(100000):
                print(i)
                WriteInMysql(id4,i)
        # ContentCoping('1')

from pymongo import *
import operator
import numpy as np
import re

HOST='127.0.0.1'
PORT=27017
DATABASE_NAME='JobInfo'
COLLECTION_NAME='test'


# 每个行业的关键字参数
jobKey={
    0:['软件','互联网','系统集成','计算机','IT','硬件'],
    1:['金融','投资','银行','证券','财产','理财','审计','基金','精算','保险','信托'],
    2:['房地产','建筑','土木','工业','化工','物业','售楼'],
    3:['贸易','销售','物流','零售','外贸','仓库','仓储','质量'],
    4:['教育','传媒','广告','教师','编导','老师','策划','制片','美术','公关'],
    5:['服务','客服','售后','旅游','医疗','护理'],
    6:['市场','销售','SEO','活动','营销','农/林'],
    7:['人事','财务','行政','人力','主管','出纳','会计'],
}

# 每个行业的工作职位名称关键字
jobNameKey={
    0:['java','ui','web','前端','net','PHP','python','android','算法','数据分析','人工智能','电气','电子','测试','硬件'
        ,'深度学习','知识图谱','数据挖掘','机器学习','运营','大数据'],
    1:['金融','投资','银行','证券','财产','理财','审计','信托','期货','操盘手','基金','精算','保险'],
    2:['房地产','建筑','土木','工业','化工','土建','施工','电气','物业'],
    3:['贸易','销售','物流','零售','外贸','仓库','仓储','质量','采购','货运'],
    4:['教育','传媒','广告','教师','编导','老师','策划','制片','美术','公关'
        ,'幼教','记者','文案','平面设计','网页设计','插画师','工业设计','视觉设计'],
    5:['服务','客服','售后','旅游','美容','美发','美甲','教练','收银','保安','保洁','保姆'],
    6:['市场','销售','SEO','活动','营销','农/林'],
    7:['人事','财务','行政','人力','主管','出纳','会计','税务','财务主管','法务主管','前台'],
}

# 首页视图函数
def index_data():
    conn = conn = MongoClient(HOST, PORT)
    db = conn[DATABASE_NAME]
    mycollection = db[COLLECTION_NAME]

    # 根据城市进行分组，获取城市职位数目数据,返回数组游标
    pipline=[
        {"$group":{"_id":"$city","count":{"$sum":1}}}
    ]
    cursor=mycollection.aggregate(pipline)

    # 遍历游标，获取职位数据
    result_map=[]
    for item in cursor:
        data={"name":item['_id'],"value":item['count']}
        result_map.append(data)

    # 对城市进行排序，输出前一百条数据
    result_map=sorted(result_map,key=operator.itemgetter('value'))[-100:]

    # 获取dataAxis值和data1
    dataAxis=[]
    data1=[]
    for i in range(len(result_map)):
        dataAxis.append(result_map[i]['name'])
        data1.append(result_map[i]['value'])

    # 获取数据最大值
    yMax=np.max(data1)

    # 柱状图数据（封装为list）
    result_bar=[dataAxis,data1,yMax]
    result=[result_map,result_bar]

    # 获取饼状图数据
    pipline_pie=[
        {"$group":{"_id":"$jobType","count":{"$sum":1}}}
    ]
    cursor2=mycollection.aggregate(pipline_pie)
    pie_jobType_list=['互联网','金融','房地产/建筑','贸易/销售','教育/传媒','服务业','市场/销售','人事/行政']
    temp_cursor2=[]

    # 游标是一次迭代，不可回退，因此要用临时变量存储
    for item in cursor2:
        temp_cursor2.append(item)

    pie_dict_data=[]
    for i in range(len(pie_jobType_list)):
        value=0
        for item in temp_cursor2:
            if judge_contain_str(item["_id"],i):
                value+=item['count']
        data={"value":value,"name":pie_jobType_list[i]}
        pie_dict_data.append(data)

    # print(pie_dict_data)

    result_pie=[pie_jobType_list,pie_dict_data]
    result.append(result_pie)

    conn.close()
    return result

# 获取地图数据
def get_map_data(page):
    conn=conn=MongoClient(HOST,PORT)
    db = conn[DATABASE_NAME]
    mycollection = db[COLLECTION_NAME]

    pipline=[
        {'$group': {'_id': {'city':'$city','jobType':'$jobType'}, 'value': {'$sum': 1}}}
    ]

    cursor =mycollection.aggregate(pipline)

    city_key=set()
    temp_data=list()

    for item in cursor:
        city_key.add(item['_id']['city'])
        temp_data.append(item)

    result=[]

    for city in city_key:
        value = 0
        for item in temp_data:
            if item['_id']['city'] ==city:
                if judge_contain_str(item['_id']['jobType'],page):
                    value+=item['value']
        data={"_id":city,"value":value}
        result.append(data)

    conn.close()
    return result

# 右侧上部柱状图，带滑动
def top100_city_data(page):

    rel = get_map_data(page)
    # 对数据进行排序
    sorted_result = sorted(rel, key=operator.itemgetter('value'))

    # 取Top5的数据
    data = sorted_result[-100:]
    city_list = list()
    num_list = list()

    for i in range(len(data)):
        city_list.append(data[i]['_id'])
        num_list.append(data[i]['value'])

    yMax=np.max(num_list)
    result = [city_list, num_list,yMax]
    return result


# 右侧上部柱状图(原函数)
def top5level(page):

    rel=get_map_data(page)
    # 对数据进行排序
    sorted_result=sorted(rel,key=operator.itemgetter('value'))

    # 取Top5的数据
    data=sorted_result[-5:]
    city_list=list()
    num_list=list()

    for i in range(len(data)):
        city_list.append(data[i]['_id'])
        num_list.append(data[i]['value'])

    result=[city_list,num_list]
    return result

# 右侧下部饼状图
def to5LevelCityPie(page):
    rel=top5level(page)
    city=rel[0]
    pie_data=[]
    for i in range(len(rel[0])):
        pie_data.append({'value':rel[1][i],'name':city[i]})

    result=[city,pie_data]
    return result

# 词云
def wordCloud(page):
    conn = conn = MongoClient(HOST, PORT)
    db = conn[DATABASE_NAME]
    mycollection = db[COLLECTION_NAME]

    pipline = [
        {'$group': {'_id': {'skill':'$extractSkillTag','jobType':'$jobType'}}}
    ]
    cursor = mycollection.aggregate(pipline)

    skill_key=set()
    skill_all = []
    # 获取技能词条并去重
    for item in cursor:
        # 对技能词条分类
        if judge_contain_str(item['_id']['jobType'],page):
            for i in range(len(item['_id']['skill'])):
                skill_key.add(item['_id']['skill'][i])
                skill_all.append(item['_id']['skill'][i])

    # 统计词频
    result=[]
    # data={"name":  , "value":  }
    for i in skill_key:
        value=0
        for item in skill_all:
            if item.__contains__(i):
                value+=1
        data={"name":i,"value":value}
        result.append(data)



    # 对结果排序，并取前100个词条
    result=sorted(result,key=operator.itemgetter('value'))
    result=result[-100:]

    # 关闭数据库连接
    conn.close()
    return result

# 职位排名前五
def getTop5JobNum(page):
    # 连接数据库
    conn = conn = MongoClient(HOST, PORT)
    db = conn[DATABASE_NAME]
    mycollection = db[COLLECTION_NAME]

    piplne=[
        {'$group': {'_id': {'jobType':'$jobType','jobName':'$jobName'},"count":{"$sum":1}}}
    ]
    cursor=mycollection.aggregate(piplne)

    temp_cursor=[]
    for item in cursor:
        temp_cursor.append(item)

    # 筛选对应工作中类的数据
    jobType_data=[]
    for item in temp_cursor:
        if judge_contain_str(item["_id"]["jobType"],page):
            data={"jobName":item["_id"]["jobName"],"value":item["count"]}
            jobType_data.append(data)

    result_dict=[]
    for jk in jobNameKey[page]:
        value=0
        for item in jobType_data:
            if judge_jobName_str(item['jobName'],jk):
               value+=item['value']
        data={'jobName':jk,'value':value}
        result_dict.append(data)

    # 如何合并教育产业中，教师和老师的值？
    if page==4:
        value=0
        temp=result_dict
        for item in temp:
            if item['jobName']=='老师' or item["jobName"]=="教师":
                value+=item['value']
                result_dict.remove(item)
        data={"jobName":"教师","value":value}
        result_dict.append(data)

    # 对获取结果进行排序
    result_dict=sorted(result_dict,key=operator.itemgetter("value"))[-5:]

    jobNameList=['product']
    value=['Top5职位']
    for item in result_dict:
        jobNameList.append(item["jobName"])
        value.append(item["value"])


    result=[jobNameList,value]
    conn.close()
    return result

# 工作经验与平均薪资
def exp_salary(page):
    conn = conn = MongoClient(HOST, PORT)
    db = conn[DATABASE_NAME]
    mycollection = db[COLLECTION_NAME]

    pipline = [
        {'$group': {'_id': {'exp':'$workingExp','salary':'$salary','jobType':"$jobType"},'count':{"$sum":1}}}
    ]
    cursor = mycollection.aggregate(pipline)

    # 对分组数据进行分类
    exp_salary_list=[]

    for item in cursor:
        if judge_contain_str(item["_id"]['jobType'],page):
            if item["_id"]["salary"] !=['薪资面议']:
                if item["_id"]["salary"]=='1K以下' or item["_id"]["salary"]=='校招' :
                    item["_id"]["salary"]=[0,1000]
                    salary_list = np.array(item["_id"]["salary"], dtype='float_')
                    average_salary = np.mean(salary_list)  # 用numpy库计算平均薪资
                    data = {"exp": item["_id"]["exp"], "salary": int(average_salary),"count":item["count"]}
                    exp_salary_list.append(data)
                else:
                    salary_list = np.array(item["_id"]["salary"], dtype='float_')
                    average_salary = np.mean(salary_list)  # 用numpy库计算平均薪资
                    data = {"exp": item["_id"]["exp"], "salary": int(average_salary),"count":item["count"]}
                    exp_salary_list.append(data)

    # print("经验和薪资的关系分组结果",len(exp_salary_list))

    # 针对工作年薪进行分组统计，职位数和平均薪资
    a1,a2,a3,a4,a5,a6,a7=0,0,0,0,0,0,0
    b1, b2, b3, b4, b5, b6, b7 = 0, 0, 0, 0, 0, 0, 0
    for item in exp_salary_list:
        # print(item)
        if item["exp"]=="不限":
            a1+=item["salary"]*item["count"]
            b1+=item["count"]

        if item["exp"]=="无经验":
            a2 += item["salary"]*item["count"]
            b2 += item["count"]

        if item["exp"]=="1年以下":
            a3 += item["salary"]*item["count"]
            b3 += item["count"]

        if item["exp"]==[1,3]:
            a4 += item["salary"]*item["count"]
            b4 += item["count"]

        if item["exp"]==[3,5]:
            a5 += item["salary"]*item["count"]
            b5 += item["count"]

        if item["exp"]==[5,10]:
            a6 += item["salary"]*item["count"]
            b6 += item["count"]

        if item["exp"]=="10年以上":
            a7+= item["salary"]*item["count"]
            b7 += item["count"]

    result=[]
    exp_job_num=[b1,b2,b3,b4,b5,b6,b7]
    # 使用numpy将数据取整
    exp_average_salary=np.array([a1/b1,a2/b2,a3/b3,a4/b4,a5/b5,a6/b6,a7/b7],dtype="int_")

    # print("经验和薪资之间的关系",exp_job_num)
    # print("经验和薪资之间的关系平均薪资", exp_average_salary)

    data1={"exp_job_num":exp_job_num}
    data2={"exp_average_salary":list(exp_average_salary)}

    result.append(data1)
    result.append(data2)

    conn.close()

    return result

# 学历与平均薪资
def level_salary(page):
    conn = conn = MongoClient(HOST, PORT)
    db = conn[DATABASE_NAME]
    mycollection = db[COLLECTION_NAME]

    # 修改bug，增加计数字段
    pipline = [
        {'$group': {'_id': {'eduLevel':'$eduLevel', 'salary': '$salary', 'jobType': "$jobType"},'count':{'$sum':1}}}
    ]
    cursor = mycollection.aggregate(pipline)

    # 对分组数据进行分类
    edu_salary_list = []
    data_tag=0
    for item in cursor:
        data_tag+=1
        # print(item)
        if judge_contain_str(item["_id"]['jobType'], page):
            if item["_id"]["salary"] != ['薪资面议']:
                if item["_id"]["salary"] == '1K以下'or item["_id"]["salary"]=='校招':
                    item["_id"]["salary"] = [0, 1000]
                    salary_list = np.array(item["_id"]["salary"], dtype='float_')
                    average_salary = np.mean(salary_list)  # 用numpy库计算平均薪资

                    # data = {"eduLevel": item["_id"]["eduLevel"], "salary": int(average_salary)}
                    data={"eduLevel": item["_id"]["eduLevel"], "salary": int(average_salary),"count":item['count']}
                    edu_salary_list.append(data)

                else:
                    salary_list = np.array(item["_id"]["salary"], dtype='float_')
                    average_salary = np.mean(salary_list)  # 用numpy库计算平均薪资
                    data = {"eduLevel": item["_id"]["eduLevel"], "salary": int(average_salary),"count":item['count']}
                    edu_salary_list.append(data)

    # 针对工作年薪进行分组统计，职位数和平均薪资
    a1, a2, a3, a4, a5, a6, a7 ,a8= 0, 0, 0, 0, 0, 0, 0,0   # 薪资和
    b1, b2, b3, b4, b5, b6, b7 ,b8 = 0, 0, 0, 0, 0, 0, 0,0  # 职位数

    # print("筛选之后的互联网行业职位数：",len(edu_salary_list),'游标中的数据',data_tag)

    for item in edu_salary_list:
        if item["eduLevel"] == "不限":
            a1 += item["salary"]
            b1 += item['count']

        if item["eduLevel"] == "中技":
            a2 += item["salary"]
            b2 += item['count']

        if item["eduLevel"] == "中专":
            a3 += item["salary"]
            b3 += item['count']

        if item["eduLevel"] == "高中":
            a4 += item["salary"]
            b4 += item['count']

        if item["eduLevel"] == "大专":
            a5 += item["salary"]
            b5 += item['count']

        if item["eduLevel"] == "本科":
            a6 += item["salary"]
            b6 += item['count']

        if item["eduLevel"] == "硕士":
            a7 += item["salary"]
            b7 += item['count']

        if item["eduLevel"] == "博士":
            a8+= item["salary"]
            b8 += item['count']

    result = []
    edu_average_salary=[]
    salary=[a1, a2, a3, a4, a5, a6, a7 ,a8]
    edu_job_num = [b1, b2, b3, b4, b5, b6, b7,b8]

    # print("每个学历对应的职位数据",edu_job_num)

    # 使用numpy将数据取整
    for i in range(len(salary)):
        if salary[i] is not 0:
            temp=salary[i]/edu_job_num[i]
            edu_average_salary.append(temp)
        else:
            edu_average_salary.append(0)

    edu_average_salary = np.array(edu_average_salary, dtype="int_")
    data1 = {"edu_job_num": edu_job_num}
    data2 = {"edu_average_salary": list(edu_average_salary)}

    result.append(data1)
    result.append(data2)

    conn.close()
    return result

# 辅助分组函数1
def judge_jobName_str(jobName,jk):
    pattern_str=jk
    regx = re.compile(pattern_str, re.I)
    if regx.search(jobName) is not None:
        return True
    return False

# 辅助分组函数2
def judge_contain_jobstr(jobName,page):
    for i in jobNameKey[page]:
        if jobName.__contains__(i):
            return True
    return False

# 辅助分组函数3
def judge_contain_str(jobType,page):
    # 对数据根据八个类别进行分组
    for i in jobKey[page]:
        if jobType.__contains__(i):
            return True
    return False


def crawl_monitor_page():
    conn = conn = MongoClient(HOST, PORT)
    db = conn[DATABASE_NAME]
    mycollection = db["crawler"]

    result=mycollection.find({})
    data=[]
    for item in result:
        data.append(item)

    data=data[-10:-1]



    return data

if __name__ == '__main__':

    # getTop5JobNum(4)
    # crawl_monitor_page()
    # index_data()
    exp_salary(0)
    # level_salary(0)

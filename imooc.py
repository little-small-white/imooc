import requests
import pymysql
import hashlib
import time


def get_token(uid, api, timestamp):
    s = '{uid}mkwapi!@#mobileimooc{api}{timestamp}'.format(uid=uid, api=api, timestamp=timestamp)
    m = hashlib.md5(s.encode())
    return m.hexdigest()


headers = {
    "User-Agent": "mukewang/5.0.0 (Android 7.0; HONOR BLN-AL40 Build/HONORBLN-AL40),Network WIFI",
    "Content-Type": "application/x-www-form-urlencoded",
    "Content-Length": "123",
    "Host": "www.imooc.com",
    "Accept-Encoding": "gzip",
    "Connection": "keep-alive"
}


conn = pymysql.connect(host="localhost", user="root", password="root", database="wei", charset="utf8")
cursor = conn.cursor()

sql_course = """
    insert imooc_course(id, course_name, level) 
    values(%s, %s, %s)
    """
sql_chapter = """
    insert imooc_chapter(course_id, chapter_id, chapter_name, 
    media_url, duration, media_size, media_down_size, node_name)
    values(%s, %s, %s, %s, %s, %s, %s, %s)
    """


def get_imooc(page):
    now = time.time() * 1000
    data = {
        "secrect": "dcd73b0d422a7c93533c2*************",
        "uuid": "3d33aca5ae1470d82aaffd53*******",
        "uid": "*******",
        "page": page,
        "timestamp": now,
        "token": get_token("*******", "courselistinfo", now),
        "exclude_learned": "0"
    }
    url = "https://www.imooc.com/api3/courselistinfo"
    r = requests.post(url, data=data)
    if r.status_code == 200:
        return r.json()
    else:
        return


def parse_imooc(json):
    for study in json["data"]:
        id = study["id"]
        course = study["name"]
        level = study["level"]
        yield id, course, level


def save(sql, value):
    cursor.execute(sql, value)
    conn.commit()


def get_chapter(course_id):
    now = time.time() * 1000
    data_chapter = {
        "cid": course_id,
        "timestamp": now,
        "uid": "*******",
        "secrect": "dcd73b0d422a7c93533c2*************",
        "token": get_token("*******", "getcpinfo_ver2", now)
    }
    url = "http://www.imooc.com/api3/getcpinfo_ver2"
    r = requests.post(url, data=data_chapter, headers=headers)
    return r.json()


def parse_chapter(json):
    for chapter in json["data"]:
        course_id = chapter["chapter"]["cid"]
        chapter_id = chapter["chapter"]["id"]
        chapter_name = "第{0}章 {1}".format(chapter["chapter"]["seq"], chapter["chapter"]["name"])
        for node in chapter["media"]:
            media_url = node["media_url"]
            duration = node["duration"]
            media_size = node["media_size"]
            media_down_size = node["media_down_size"]
            node_name = "{0}-{1} {2}".format(node["chapter_seq"], node["media_seq"], node["name"])

            yield course_id, chapter_id, chapter_name, media_url, duration, media_size, media_down_size, node_name


if __name__ == "__main__":
    for page in range(1, 100):
        course_json = get_imooc(str(page))
        if not course_json:
            break
        courses = parse_imooc(course_json)
        for course in courses:
            print("正在保存ID为{}的数据".format(course[0]))
            save(sql_course, course)
            json = get_chapter(course[0])
            print(json["errorDesc"])
            for chapter in parse_chapter(json):
                print("正在保存ID为{}的课程章节 {}".format(course[0], chapter[-1]))
                save(sql_chapter, chapter)

    conn.close()

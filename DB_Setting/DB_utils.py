import pymysql
from Config import dbhost, dbuser, dbpassword, dbname, dbport


def get_all_file_name():
    try:
        db = pymysql.connect(host=dbhost, user=dbuser, password=dbpassword, port=dbport, db=dbname)
        cur = db.cursor()
        sql = r"select name from data_logging"
        cur.execute(sql)
        name = cur.fetchall()
        if name:
            return [i[0] for i in name]
        return 'No File!!'
    except Exception as e:
        print(e)
    finally:
        cur.close()
        db.close()


def insert_into_file(name, last_block_index):
    filenames = get_all_file_name()
    if name in filenames:
        return
    try:
        db = pymysql.connect(host=dbhost, user=dbuser, password=dbpassword, port=dbport, db=dbname)
        cur = db.cursor()
        sql = r"insert into data_logging(name, last_block_index) values(%s, %s)"
        cur.execute(sql, args=(name, last_block_index))
        db.commit()
        if 'No File' in get_last_file():
            cur.execute("insert into last_data_logging(name) values(%s)", args=(name,))
        else:
            cur.execute("update last_data_logging set name=%s", args=(name,))
        db.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        db.close()


def get_last_file():
    try:
        db = pymysql.connect(host=dbhost, user=dbuser, password=dbpassword, port=dbport, db=dbname)
        cur = db.cursor()
        sql = r"select name from last_data_logging"
        cur.execute(sql)
        name = cur.fetchone()
        if name:
            return name[0]
        return 'No File!!'
    except Exception as e:
        print(e)
    finally:
        cur.close()
        db.close()

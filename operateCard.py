import nfc_module as nfc
import random
import string
import time
from peewee import SqliteDatabase, Model, TextField, IntegerField
from playhouse.csv_loader import dump_csv
import csv

temper = SqliteDatabase(':memory:')


class NewCard(Model):
    cardname = TextField()
    cardpass = TextField()
    money = IntegerField(default=0)

    class Meta:
        database = temper


def newCard(username, money):
    # 随机生成八位密码
    password = ''.join(
        random.sample(string.ascii_letters + string.digits, 8)).replace(
            " ", "")

    cardname = username
    password = password  # 可能的编码准备 nfc.nfc_encode()

    NewCard.create(cardname=cardname, cardpass=password, money=money)

    # 初始化串口
    if not nfc.start():
        return {"result": False, "reason": "DEVICE"}

    # 唤醒
    nfc.wakeUp()

    # 循环读卡
    uid = nfc.getUid()
    if len(uid) == 0:
        return {"result": False, "reason": "MOVE"}
    nfc.checkKey(uid, [])
    # nfc.writeBar(5, [1, 9, 9, 8, 1, 1, 2, 3])
    # print('user  id: ' + str(nfc.readBar(6)))
    # print('password: ' + str(nfc.readBar(5)))

    nfc.writeBar(6, username)
    nfc.writeBar(5, password)

    time.sleep(0.5)
    checked_name = (nfc.readBar(6)).decode()
    checked_pass = (nfc.readBar(5)).decode()

    if checked_name[:10] == username and checked_pass[:8] == password:
        return {"result": True, "reason": "SUCCESS"}
    else:
        return {"result": False, "reason": "UNKNOWN"}



def quantity_new_card(filename):
    f = None
    try:
        NewCard.delete().execute()
    finally:
        f = open(filename)
    lines = csv.reader(f)
    for line in lines:
        try:
            input("将卡放上，按下任意键开始刷卡, 当前卡号：{}".format(line[0]))
            result = newCard(line[0], line[1])
            print('当前卡号: ' + line[0])
            print('结果{},原因:{}'.format(result['result'], result['reason']))
        except Exception as e:
            continue
    f.close()

    dstname = '待上传.csv'
    open(dstname, 'w').close()
    dump_csv(
        NewCard.select(NewCard.cardname, NewCard.cardpass, NewCard.money),
        dstname)
    return


temper.create_table(NewCard, True)

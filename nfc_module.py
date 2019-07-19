import serial
import serial.tools.list_ports
import binascii
import time


def nfc_encode(string):
    '''
    把包含直接信息的字符串转成nfc模块可识别的数组
    '''
    if len(string) > 16:
        return None
    else:
        result = []
        for i in range(len(string)):
            result.append(ord(string[i]))

        return result


def nfc_decode(nfc_list):
    '''
    将nfc模块识别的数组转成数据库内存储的数据
    '''
    return (binascii.b2a_hex(bytes(nfc_list))).decode('ascii')


wakeUpCode = [
    0x55, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0xff, 0x03, 0xfd, 0xd4, 0x14, 0x01, 0x17, 0x00
]

getUidCode = [0x00, 0x00, 0xFF, 0x04, 0xFC, 0xD4, 0x4A, 0x01, 0x00, 0xE0, 0x00]

checkKeyCode = [
    0x00, 0x00, 0xfF, 0x0F, 0xF1, 0xD4, 0x40, 0x01, 0x60, 0x07, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xA1, 0x9F, 0xF5, 0x5E, 0xC2, 0x00
]

readBarCode = [
    0x00, 0x00, 0xff, 0x05, 0xfb, 0xD4, 0x40, 0x01, 0x30, 0x06, 0xB5, 0x00
]

writeBarCode = [
    0x00, 0x00, 0xff, 0x15, 0xEB, 0xD4, 0x40, 0x01, 0xA0, 0x06, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xCD, 0x00
]

ser = serial.Serial()


def start():
    global ser
    ser = serial.Serial()
    ser.baudrate = 115200
    port_list = serial.tools.list_ports.comports()
    for p in port_list:
        if 'USB' in p.description:
            ser.port = p.device
            ser.open()
            return True

    return False


def close():
    ser.close()


def wakeUp():
    '''
    唤醒pn532模块
    '''
    try:
        ser.write(wakeUpCode)
        time.sleep(0.15)
        response = ser.read_all()
        if response[3] != 0x00:
            print('pn532 module is not Ok')
            return False
        else:
            print('pn532..Ok')
            return True

    except:
        return False


def getUid():
    '''
    获取卡片Uid
    '''
    try:
        completeCheckSet(getUidCode)
        ser.write(getUidCode)
        time.sleep(0.15)
        response = ser.read_all()
        if len(response) == 6 or response[3] != 0x00:
            print('can not get uid')
            return None
        else:
            print('uid...Ok')
            cardUid = str(binascii.b2a_hex(response))
            uid = (cardUid[20 * 2:24 * 2])
            uid = binascii.a2b_hex(uid)
            return uid
    except:
        return None


def checkKey(uid, key):
    '''
    检查秘钥
    '''
    for i in (16, 17, 18, 19):
        checkKeyCode[i] = uid[i - 16]

    completeCheckSet(checkKeyCode)
    ser.write(checkKeyCode)
    time.sleep(0.15)
    response = ser.read_all()
    if response[3] != 0x00:
        print('key is wrong')
        return False
    else:
        print('check...Ok')
        return True


def readBar(num):
    '''
    读
    '''
    readBarCode[len(readBarCode) - 3] = num
    completeCheckSet(readBarCode)
    ser.write(readBarCode)
    time.sleep(0.2)
    response = ser.read_all()
    if response[3] != 0x00:
        print('read error')
        return None
    else:
        try:
            print('read bar ' + str(num))
            barData = str(binascii.b2a_hex(response))
            return binascii.a2b_hex(barData[-37:-5])
        except:
            print('don\'t move the card')
            return None


def writeBar(num, data):
    '''
    写, 不能写入0x10,读的时候会读成回车
    '''
    _data = [0] * len(data)
    for i in range(len(data)):
        if isinstance(data[i], int):
            _data[i] = data[i]
        else:
            _data[i] = ord(str(data[i]))

    writeBarCode[9] = num
    for i in range(len(_data)):
        writeBarCode[10 + i] = _data[i]
    completeCheckSet(writeBarCode)
    ser.write(writeBarCode)
    time.sleep(0.1)
    response = ser.read_all()
    if response[3] != 0x00:
        print('write error')
        return False
    else:
        print('write ' + str(binascii.b2a_hex(bytes(writeBarCode[10:26]))) +
              'to bar ' + str(num))


def completeCheckSet(codeList):
    '''
    自动填充校验位
    '''
    length = codeList[3]
    result = 0
    for i in range(len(codeList) - 2 - length, len(codeList) - 2):
        result += codeList[i]
    result = result % 256
    result = ~result & 0x00FF
    result = result + 0x0001
    result = result & 0x00FF
    codeList[-2] = result


if __name__ == '__main__':
    start()

    wakeUp()
    uid = getUid()
    checkKey(uid, [])
    writeBar(5, [1, 9, 9, 8, 1, 1, 2, 3])
    print('5s: ' + str(readBar(5)))

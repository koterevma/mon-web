import sqlite3
import requests
import json
from pathlib import Path

working_directory = Path(__file__).parent

def get_sensors(serial, uname):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 '
                      'Safari/537.36', }
    # serial, uname = serial_uname.split()
    url = 'http://webrobo.mgul.ac.ru:3000/db_api_REST/not_calibr/last_measurement/'
    url += uname + '/' + serial + '/'
    # print(url)
    try:
        f = requests.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        print(e)
        return None
    else:
        data = json.loads(f.text)
        sens_list = []
        for r in data:
            for s in data[r]['data']:
                try:
                    float(data[r]['data'][s])
                except ValueError:
                    pass
                else:
                    sens_list.append(s)

    return sens_list

def sensors(device_name, device_serial):
    conn = sqlite3.connect(working_directory / "mon.db")
    cur = conn.cursor()
    cur.execute("SELECT sensors.name FROM sensors LEFT JOIN devices ON devices.deviceid=sensors.deviceid WHERE devices.uname=? AND devices.serial=?", (device_name, device_serial))
    return cur.fetchall()


def sensors_with_units(device_name, device_serial):
    conn = sqlite3.connect(working_directory / "mon.db")
    cur = conn.cursor()
    cur.execute("SELECT sensors.name, sensors.units FROM sensors LEFT JOIN devices ON devices.deviceid=sensors.deviceid WHERE devices.uname=? AND devices.serial=?", (device_name, device_serial))
    return cur.fetchall()


def units(sensor_name):
    conn = sqlite3.connect(working_directory / "mon.db")
    cur = conn.cursor()
    cur.execute("SELECT sensors.units FROM sensors WHERE sensors.name=?", (sensor_name,))
    return cur.fetchone()


def devices():
    conn = sqlite3.connect(working_directory / "mon.db")
    cur = conn.cursor()
    cur.execute("SELECT uname, serial FROM devices")
    return cur.fetchall()


if __name__ == '__main__':  # Пример работы
    f = devices()[2]
    print(str(f))
    print(sensors(*f))  # Разыменование f, берем названия датчиков для прибора полученного 
    print()
    print("Sensors and units for device {}, serial {}".format(*f))
    print(*sensors_with_units(*f), sep='\n')
    print()
    print("Units for BMP280_temp")
    print(units("BMP280_temp"))
    
    conn = sqlite3.connect(working_directory / "mon.db")
    cur = conn.cursor()
    s = 97
    for i in get_sensors('01', 'Опорный%20барометр'):
        cur.execute("INSERT INTO sensors VALUES(?, ?, ?, ?)", (s, 19, i, 'UNKNOWN'))
        s += 1
    cur.execute("SELECT * FROM sensors")
    conn.commit()
    print(*cur.fetchall(), sep='\n')
    

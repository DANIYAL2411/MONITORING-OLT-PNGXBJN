import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime, timedelta

# =========================
# TELEGRAM
# =========================

BOT_TOKEN = "8860401989:AAHP5PqX7q56093L0DteC3HAQGyirAbcefc"
CHAT_ID = "1061791629"

# =========================
# OLT PONOROGO + BOJONEGORO
# =========================

OLTS = [
    "JKO-OLT-14","JKO-OLT-22","JKO-OLT-09","JKO-OLT-07","POR-OLT-04",
    "POR-OLT-01","PCO-OLT-12","PCO-OLT-01","PKE-OLT-12","PKE-OLT-07",
    "SEM-OLT-11","SEM-OLT-07","PCO-OLT-03","PCO-OLT-06","JKO-OLT-11",
    "JKO-OLT-13","JKO-OLT-06","JKO-OLT-18","JKO-OLT-08","JKO-OLT-19",
    "JKO-OLT-04","JKO-OLT-02","JKO-OLT-05","JKO-OLT-12","JKO-OLT-01",
    "JKO-OLT-03","JKO-OLT-16","JKO-OLT-15","JKO-OLT-17","SEM-OLT-02",
    "SEM-OLT-08","SEM-OLT-05","PKE-OLT-06","BLM-OLT-07","SEM-OLT-04",
    "SEM-OLT-09","PKE-OLT-01","SEM-OLT-12","PKE-OLT-04","SEM-OLT-01",
    "SEM-OLT-03","PCO-OLT-05","PCO-OLT-14","PCO-OLT-13","PKE-OLT-02",
    "PCO-OLT-02","PCO-OLT-10","PKE-OLT-05","PKE-OLT-08","PKE-OLT-03",
    "PKE-OLT-10","JKO-OLT-10","POR-OLT-03","PCO-OLT-11","PCO-OLT-04",
    "PKE-OLT-11","PKE-OLT-09","PCO-OLT-15","BLM-OLT-06","BLM-OLT-01",
    "PKE-OLT-15","BLM-OLT-03","BLM-OLT-05","BLM-OLT-02","BLM-OLT-04",
    "POR-OLT-06","BLM-OLT-11","PKE-OLT-13","POR-OLT-10","POR-OLT-02",
    "POR-OLT-05","POR-OLT-08","POR-OLT-09",

    "KPO-OLT-15","KPO-OLT-04","WDI-OLT-08","LWT-OLT-14","KPO-OLT-05",
    "KPO-OLT-20","KPO-OLT-03","KPO-OLT-17","KPO-OLT-18","BJO-OLT-22",
    "KPO-OLT-01","KPO-OLT-02","KPO-OLT-08","KPO-OLT-12","KPO-OLT-09",
    "KPO-OLT-23","KPO-OLT-22","KPO-OLT-14","WDI-OLT-04","WDI-OLT-11",
    "WDI-OLT-09","WDI-OLT-14","WDI-OLT-15","WDI-OLT-13","KPO-OLT-10",
    "WDI-OLT-16","KPO-OLT-16","KPO-OLT-11","BJO-OLT-17","KPO-OLT-21",
    "KPO-OLT-07","KPO-OLT-06","KPO-OLT-13","KPO-OLT-19","WDI-OLT-01",
    "KPO-OLT-24","WDI-OLT-03","WDI-OLT-07","WDI-OLT-12","BJO-OLT-01",
    "BJO-OLT-02","BJO-OLT-04","BJO-OLT-16","BJO-OLT-09","BJO-OLT-19",
    "BJO-OLT-21","BJO-OLT-15","BJO-OLT-18","LWT-OLT-15","LWT-OLT-03",
    "BJO-OLT-03","BJO-OLT-08","BJO-OLT-11","BJO-OLT-12","BJO-OLT-05",
    "BJO-OLT-06","BJO-OLT-07","BJO-OLT-10","BJO-OLT-13","BJO-OLT-14",
    "LWT-OLT-10","LWT-OLT-05","LWT-OLT-11","LWT-OLT-06","WDI-OLT-02",
    "LWT-OLT-13","LWT-OLT-07","LWT-OLT-01","WDI-OLT-05","LWT-OLT-04",
    "LWT-OLT-08","LWT-OLT-12","LWT-OLT-09","WDI-OLT-10","WDI-OLT-06"
]

BASE_URL = "http://202.77.116.37:28945/ftthbu5/ems_micro.php?olt={}"

DB_FILE = "sent_alarm.json"

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        sent = set(json.load(f))
else:
    sent = set()

while True:

    print("\n==========", datetime.now(), "==========")

    for olt_name in OLTS:

        try:
            url = BASE_URL.format(olt_name)

            html = requests.get(url, timeout=20).text
            soup = BeautifulSoup(html, "html.parser")

            rows = soup.find_all("tr")[1:]

            for row in rows:

                cols = [td.get_text(strip=True) for td in row.find_all("td")]

                if len(cols) < 8:
                    continue

                alarm_id = cols[0]
                start = cols[1]
                olt = cols[3]
                message = cols[4]
                ip = cols[5]
                severity = cols[6]
                ack = cols[7]

                if alarm_id in sent:
                    continue

                if ack != "Unack":
                    continue

                if severity not in ["Major", "Critical"]:
                    continue

                try:
                    alarm_time = datetime.strptime(
                        start,
                        "%Y-%m-%d %H:%M:%S"
                    )
                except:
                    continue

                # hanya alarm 15 menit terakhir
                if datetime.now() - alarm_time > timedelta(minutes=15):
                    sent.add(alarm_id)
                    continue

                pesan = (
                    f"🚨 ALARM OLT\n\n"
                    f"OLT : {olt}\n"
                    f"Severity : {severity}\n"
                    f"IP : {ip}\n\n"
                    f"Message:\n{message}\n\n"
                    f"Start:\n{start}"
                )

                r = requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={
                        "chat_id": CHAT_ID,
                        "text": pesan
                    },
                    timeout=20
                )

                print("Kirim:", alarm_id, r.status_code)

                sent.add(alarm_id)

        except Exception as e:
            print("ERROR", olt_name, e)

    with open(DB_FILE, "w") as f:
        json.dump(list(sent), f)

    print("Sleep 300 detik...")
    time.sleep(300)
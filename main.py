import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from collections import defaultdict

# =========================
# TELEGRAM CONFIG
# =========================
BOT_TOKEN = "8860401989:AAHP5PqX7q56093L0DteC3HAQGyirAbcefc"
CHAT_ID = "1061791629"

# =========================
# OLT LIST (FULL KAMU)
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

# =========================
# STATE MEMORY (RAM ONLY)
# =========================
sent_alarm = set()
event_buffer = defaultdict(list)
last_sent = {}
last_heartbeat = 0

# =========================
# TELEGRAM SEND (SAFE)
# =========================
def send_telegram(text):
    try:
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )
    except:
        pass

# =========================
# HEARTBEAT (1 JAM SEKALI)
# =========================
def heartbeat():
    global last_heartbeat
    now = time.time()

    if now - last_heartbeat > 3600:
        send_telegram("🟢 NOC BOT ACTIVE (HEARTBEAT OK)")
        last_heartbeat = now

# =========================
# FLUSH INCIDENT (CORE NOC LOGIC)
# =========================
def flush_events():
    now = time.time()

    for olt, events in list(event_buffer.items()):

        if not events:
            continue

        # suppression 5 menit per OLT
        if olt in last_sent:
            if now - last_sent[olt] < 300:
                continue

        critical = [e for e in events if e["severity"] == "Critical"]
        major = [e for e in events if e["severity"] == "Major"]

        msg = f"🚨 NOC INCIDENT REPORT\n\nOLT: {olt}\n"

        if critical:
            msg += f"🔥 Critical: {len(critical)}\n"
        if major:
            msg += f"⚠️ Major: {len(major)}\n"

        sample = events[0]

        msg += f"""
SAMPLE:
Severity: {sample['severity']}
IP: {sample['ip']}
Message: {sample['message']}
Start: {sample['start']}
"""

        send_telegram(msg)

        last_sent[olt] = now
        event_buffer[olt] = []

# =========================
# MAIN LOOP
# =========================
while True:
    try:
        print("\nSCAN:", datetime.now())

        heartbeat()

        for olt_name in OLTS:

            try:
                url = BASE_URL.format(olt_name)

                r = requests.get(url, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")

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

                    if alarm_id in sent_alarm:
                        continue

                    if ack != "Unack":
                        continue

                    if severity not in ["Major", "Critical"]:
                        continue

                    key = olt
                    event_buffer[key].append({
                        "alarm_id": alarm_id,
                        "severity": severity,
                        "message": message,
                        "ip": ip,
                        "start": start
                    })

                    sent_alarm.add(alarm_id)

            except Exception as e:
                print("OLT ERROR:", olt_name, e)

        flush_events()

    except Exception as e:
        print("LOOP ERROR:", e)

    print("SLEEP 300s")
    time.sleep(300)

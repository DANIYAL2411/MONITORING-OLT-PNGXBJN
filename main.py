import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta

# =========================
# TELEGRAM
# =========================
BOT_TOKEN = "8860401989:AAHP5PqX7q56093L0DteC3HAQGyirAbcefc"
CHAT_ID = "1061791629"

# =========================
# OLT LIST
# =========================
OLTS = [ 
    # (punya kamu tetap pakai yang lama)
]

BASE_URL = "http://202.77.116.37:28945/ftthbu5/ems_micro.php?olt={}"

# =========================
# STATE
# =========================
sent_alarm = set()
active_incident = set()

# =========================
# TELEGRAM SAFE
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
# MAIN LOOP
# =========================
while True:
    try:
        print("\nSCAN:", datetime.now())

        current_active = set()

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

                    if ack != "Unack":
                        continue

                    if severity not in ["Major", "Critical"]:
                        continue

                    try:
                        alarm_time = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
                    except:
                        continue

                    # =========================
                    # FILTER REALTIME ONLY
                    # =========================

                    # ❌ hanya hari ini
                    if alarm_time.date() != datetime.now().date():
                        continue

                    # ❌ hanya 5 menit terakhir
                    if datetime.now() - alarm_time > timedelta(minutes=5):
                        continue

                    current_active.add(alarm_id)

                    # =========================
                    # START INCIDENT
                    # =========================
                    if alarm_id not in sent_alarm:
                        sent_alarm.add(alarm_id)
                        active_incident.add(alarm_id)

                        send_telegram(
                            f"🚨 INCIDENT OPEN\n\n"
                            f"OLT: {olt}\n"
                            f"Severity: {severity}\n"
                            f"IP: {ip}\n\n"
                            f"Message:\n{message}\n\n"
                            f"Start:\n{start}"
                        )

                        print("OPEN:", alarm_id)

            except Exception as e:
                print("OLT ERROR:", olt_name, e)

        # =========================
        # END INCIDENT (CLOSE)
        # =========================
        for old in list(active_incident):
            if old not in current_active:
                send_telegram(
                    f"🟢 INCIDENT CLOSED\n\n"
                    f"Alarm ID: {old}\n"
                    f"Status: RECOVERED"
                )

                active_incident.remove(old)

                print("CLOSE:", old)

    except Exception as e:
        print("LOOP ERROR:", e)

    print("SLEEP 300s")
    time.sleep(300)

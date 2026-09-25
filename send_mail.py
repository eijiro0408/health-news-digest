"""digest.py が作ったメールを Gmail で送る。

必要な環境変数:
    GMAIL_ADDRESS       送信元の Gmail アドレス
    GMAIL_APP_PASSWORD  Gmail のアプリパスワード（16桁）
    MAIL_TO             送信先（カンマ区切りで複数可。省略時は送信元と同じ）

--wait-until 07:00 を付けると、その時刻（日本時間）まで待ってから送ります。
"""

from __future__ import annotations

import argparse
import os
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

JST = timezone(timedelta(hours=9))
OUT = Path(__file__).parent / "out"


def wait_until(hhmm: str) -> None:
    h, m = map(int, hhmm.split(":"))
    now = datetime.now(JST)
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    seconds = (target - now).total_seconds()
    if 0 < seconds < 4 * 3600:
        print(f"{hhmm} まで {int(seconds)} 秒待ちます")
        time.sleep(seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-until", help="例: 07:00（日本時間）")
    args = parser.parse_args()

    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
    to = [a.strip() for a in os.environ.get("MAIL_TO", sender).split(",") if a.strip()]

    msg = EmailMessage()
    msg["Subject"] = (OUT / "subject.txt").read_text(encoding="utf-8")
    msg["From"] = sender
    msg["To"] = sender
    msg["Bcc"] = ", ".join(to)  # 受信者同士にアドレスが見えないよう Bcc で送る
    msg.set_content("HTML メールを表示できる環境でご覧ください。")
    msg.add_alternative((OUT / "email.html").read_text(encoding="utf-8"), subtype="html")

    if args.wait_until:
        wait_until(args.wait_until)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)
    print(f"{len(to)} 件のアドレスに送信しました")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
from datetime import datetime
import argparse
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from woocommerce import API
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText


# ۱. بارگذاری متغیرها
load_dotenv()
WC_URL = os.getenv('WC_URL')
WC_KEY = os.getenv('WC_CONSUMER_KEY')
WC_SECRET = os.getenv('WC_CONSUMER_SECRET')

SMTP_HOST     = os.getenv('SMTP_HOST')
SMTP_PORT     = int(os.getenv('SMTP_PORT', 587))
SMTP_USER     = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_TO      = os.getenv('EMAIL_TO')

# ۲. اتصال به ووکامرس
wcapi = API(
    url=WC_URL,
    consumer_key=WC_KEY,
    consumer_secret=WC_SECRET,
    version="wc/v3",
    timeout=30
)

EXCEL_FILE = 'products.xlsx'

def fetch_all_products():
    """گرفتن همهٔ محصولات با pagination"""
    products = []
    page = 1
    while True:
        batch = wcapi.get(
            "products",
            params={"per_page": 100, "page": page}
        ).json()
        if not batch:
            break
        products.extend(batch)
        print(f"Fetched page {page}, got {len(batch)} products")
        page += 1
    return products

def fetch_exchange_rate():
    """استخراج نرخ دلار از صفحه TGJU از span مربوطه و تبدیل ریال -> تومان"""
    url = 'https://www.tgju.org/profile/price_dollar_rl'
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

    # ۱. سعی در یافتن span با data-col مشخص
    span = soup.find('span', {'data-col': 'info.last_trade.PDrCotVal'})
    if span:
        text = span.get_text(strip=True)               # e.g. "831,600"
        value_rial = float(text.replace(',', ''))      # 831600.0
        value_toman = value_rial / 10                   # 83160.0
        return value_toman

    # ۲. fallback قدیمی اگر span پیدا نشد
    header = soup.find('h2', string=lambda s: s and 'دلار' in s)
    if header:
        table = header.find_next('table')
    else:
        tables = soup.find_all('table')
        table = tables[0] if tables else None

    if not table:
        raise ValueError("نرخ دلار پیدا نشد (نه در span و نه در جدول)")

    # ۳. استخراج اولین عددِ قابل تبدیل از جدول
    for row in table.find_all('tr'):
        for cell in row.find_all(['th', 'td']):
            m = re.search(r'[\d,]+(?:\.\d+)?', cell.get_text())
            if m:
                return float(m.group(0).replace(',', ''))

    raise ValueError("نرخ دلار در جدول پیدا نشد")

def send_email(subject, body):
    """ارسال ایمیل اطلاع‌رسانی از طریق SMTP هاست شما (SSL یا STARTTLS)"""
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_TO]):
        print("[WARN] اطلاعات SMTP کامل نیست؛ هیچ ایمیلی ارسال نشد.")
        return

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From']    = SMTP_USER
    msg['To']      = EMAIL_TO

    try:
        if SMTP_PORT == 465:
            # اتصال SSL مستقیم
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        else:
            # اتصال STARTTLS
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()

        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("[EMAIL] پیام با موفقیت ارسال شد")
    except Exception as e:
        print(f"[ERROR] ارسال ایمیل ناموفق بود: {e}")


def initial_run():
    """نوبت اول: گرفتن لیست کامل محصولات و ذخیرهٔ Excel"""
    products = fetch_all_products()
    df = pd.DataFrame([
        {
            'product_id': p['id'],
            'name': p['name'],
            'price_usd': None,
            'price_irr': None,
            'last_updated': None
        }
        for p in products
    ])
    df.to_excel(EXCEL_FILE, index=False)
    print("فایل products.xlsx ایجاد شد. لطفاً ستون price_usd را پر کنید و دوباره اجرا کنید.")
    sys.exit(0)

def update_prices(dry_run=False):
    """خواندن Excel، محاسبه و (آپدیت یا پرینت) قیمت‌ها"""
    df = pd.read_excel(EXCEL_FILE)
    if df['price_usd'].isnull().any():
        print("ستون price_usd خالی دارد، لطفاً همه قیمت‌ها را وارد کنید.")
        sys.exit(1)

    rate = fetch_exchange_rate()
    df['price_irr'] = (df['price_usd'] * rate).round().astype(int)

    for _, row in df.iterrows():
        product_id = int(row['product_id'])
        new_price = str(row['price_irr'])
        if dry_run:
            print(f"[DRY-RUN] محصول {product_id} → regular_price = {new_price}")
        else:
            wcapi.put(f"products/{product_id}", data={
                "regular_price": new_price
            })
            print(f"محصول {product_id} → {new_price} تومان آپدیت شد")

    if not dry_run:
        df['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df.to_excel(EXCEL_FILE, index=False)
        send_email("آپدیت قیمت سایت",f"قیمت‌ها در ووکامرس با نرخ {rate:.2f} تومان به‌روزرسانی شدند.")
    else:
        print(f"[DRY-RUN] همه محصولات برای نرخ {rate} محاسبه شدند؛ هیچ تغییری اعمال نشد.")
        send_email("آپدیت قیمت سایت",f" تست تست تست قیمت‌ها در ووکامرس با نرخ {rate:.2f} تومان به‌روزرسانی شدند.")


def main():
    parser = argparse.ArgumentParser(description="به‌روزرسانی قیمت‌ها در ووکامرس")
    parser.add_argument('--dry-run', action='store_true',
                        help='حالت آزمایشی: فقط پرینت می‌کند و آپدیت نمی‌کند')
    args = parser.parse_args()


    if not os.path.exists(EXCEL_FILE):
        initial_run()
    else:
        update_prices(dry_run=args.dry_run)
    
        sys.exit(0)

if __name__ == '__main__':
    main()

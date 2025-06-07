# Copyright 2025 Calabaraburus (Artem Natalchishin)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import re
import csv
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from scraper.models import Product

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class Command(BaseCommand):
    help = 'Собирает предложения по моделям Nova Tec и сравнивает с РРЦ'

    def handle(self, *args, **kwargs):
        # Словарь моделей: РРЦ и ссылка на страницу
        models = {
            "Nova Tec NT-S 50": [3699, "https://hotline.ua/ua/remont-bojlery-kolonki-vodonagrevateli/nova-tec-nt-s-50/"],
            "Nova Tec NT-S 80": [4245, "https://hotline.ua/ua/remont-bojlery-kolonki-vodonagrevateli/nova-tec-nt-s-80/"],
            "Nova Tec NT-S 100": [4888, "https://hotline.ua/ua/remont-bojlery-kolonki-vodonagrevateli/nova-tec-nt-s-100/"]
        }

        # Подготовка логов и CSV
        log_path = "hotline_price_debug_log.txt"
        with open(log_path, "w", encoding="utf-8") as log, \
             open("hotline_prices.csv", "w", newline="", encoding="utf-8") as csvfile:

            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Модель", "Магазин", "Цена (грн)", "Отклонение от РРЦ (%)", "Ссылка"])

            def log_info(msg):
                print(msg)
                log.write(msg + "\n")

            def log_block(title, html):
                log.write("\n" + title + "\n")
                log.write("=" * 60 + "\n")
                log.write(html + "\n\n")

            def extract_valid_price(tag, counter):
                def clean_number(text):
                    try:
                        return float(re.sub(r"[^\d.]", "", text.replace('\xa0', '').replace(',', '.')))
                    except ValueError:
                        return None

                prices = []
                for span in tag.find_all("span"):
                    style = span.get("style", "")
                    class_attr = span.get("class", [])
                    if "display: none" in style:
                        continue
                    if any(cls.startswith(('apr-', 'opd-', 'psr-')) for cls in class_attr):
                        continue
                    text = ''.join(span.stripped_strings)
                    if not text or not re.search(r'\d', text):
                        continue
                    number = clean_number(text)
                    if number and number > 1000:
                        prices.append(number)
                        log_info(f"[{counter}] → Найдена цена {number} грн в span с классами: {class_attr}")

                return min(prices) if prices else None

            def get_price_range(soup):
                try:
                    block = soup.select_one("span.many__price-sum.orange")
                    values = block.select("span.price__value")
                    if len(values) >= 2:
                        min_str = values[0].text.replace('\xa0', '').replace(' ', '')
                        max_str = values[1].text.replace('\xa0', '').replace(' ', '')
                        return int(min_str), int(max_str)
                except Exception as e:
                    log_info(f"❗ Не удалось определить диапазон цен: {e}")
                return None, None

            for model_name, (rrc_price, url) in models.items():
                log_info(f"\n=====================\n🔍 Модель: {model_name} — {url}")

                # Настройка Selenium
                options = Options()
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)

                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })

                driver.get(url)
                log_info("⏬ Скроллим вниз...")
                for _ in range(10):
                    driver.execute_script("window.scrollBy(0, 800);")
                    time.sleep(2)
                time.sleep(7)

                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                min_limit, max_limit = get_price_range(soup)
                log_info(f"📊 Диапазон цен: от {min_limit} до {max_limit}")

                price_links = soup.select('a[href^="/go/price/"]')
                log_info(f"🔎 Найдено ссылок: {len(price_links)}")

                shop_prices = {}
                counter = 0

                for i, a_tag in enumerate(price_links, start=1):
                    if not a_tag.find("span"):
                        continue
                    counter += 1
                    try:
                        price = extract_valid_price(a_tag, counter)
                        if not price:
                            log_info(f"⚠️ [{counter}] Не найдены цены")
                            log_block(f"[{counter}] PRICE HTML BLOCK", str(a_tag))
                            continue
                        if min_limit and max_limit and not (min_limit <= price <= max_limit):
                            log_info(f"⚠️ [{counter}] Цена {price} вне диапазона")
                            continue

                        shop_el = None
                        for parent in a_tag.parents:
                            shop_el = parent.find("a", class_="shop__title")
                            if shop_el:
                                break

                        shop = shop_el.text.strip() if shop_el else "(неизвестный)"
                        shop_url = "https://hotline.ua" + shop_el["href"] if shop_el and shop_el.has_attr("href") else url

                        if shop not in shop_prices or price < shop_prices[shop]["price"]:
                            shop_prices[shop] = {
                                "price": price,
                                "shop_url": shop_url,
                                "a_tag": str(a_tag)
                            }

                    except Exception as e:
                        log_info(f"🚫 [{counter}] Ошибка: {e}")
                        log_block(f"[{counter}] EXCEPTION BLOCK", str(a_tag))

                for i, (shop, data) in enumerate(shop_prices.items(), start=1):
                    deviation = round((data['price'] - rrc_price) / rrc_price * 100, 2)
                    deviation_str = f"{deviation:+.2f}%"
                    if abs(deviation) > 2:
                        log_info(f"📉 [{i}] {model_name} | {shop} | {data['price']} грн ({deviation_str})")
                    csv_writer.writerow([model_name, shop, data['price'], deviation_str, data['shop_url']])

                    Product.objects.update_or_create(
                        name=model_name,
                        shop_name=shop,
                        defaults={
                            'brand': 'Nova Tec',
                            'price': data['price'],
                            'shop_url': data['shop_url'],
                            'hotline_url': url
                        }
                    )

                driver.quit()
                log_info(f"✅ Завершено: {model_name}. Обработано {counter} блоков")

        self.stdout.write(f"📄 Лог записан в: {os.path.abspath(log_path)}")

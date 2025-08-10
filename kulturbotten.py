from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
import psycopg2
import os
import re
from datetime import datetime, date
import uuid

os.makedirs("screenshots", exist_ok=True)

# Postgres-tilkobling
pg_url = os.getenv("DATABASE_URL")
if not pg_url:
    raise RuntimeError("DATABASE_URL må settes")
conn = psycopg2.connect(pg_url)
c = conn.cursor()

imdb = ""

# Opprett tabell hvis den ikke finnes
c.execute("""
CREATE TABLE IF NOT EXISTS movies(
    guid TEXT PRIMARY KEY,
    date TEXT,
    start_time TEXT,
    title TEXT,
    age TEXT,
    info TEXT,
    length TEXT,
    screen TEXT,
    filename TEXT,
    imdb TEXT
)
""")
conn.commit()

def parse_norsk_dato(date_str: str) -> date:
    months = {
        "januar": 1, "februar": 2, "mars": 3, "april": 4,
        "mai": 5, "juni": 6, "juli": 7, "august": 8,
        "september": 9, "oktober": 10, "november": 11, "desember": 12
    }
    parts = date_str.strip().split()
    if len(parts) < 3:
        raise ValueError(f"Unexpected date format: {date_str}")
    day_num = int(parts[1].replace(".", ""))
    month_name = parts[2].lower()
    if month_name not in months:
        raise ValueError(f"Unknown month: {month_name}")
    month = months[month_name]
    now = datetime.now()
    year = now.year
    if now.month == 12 and month in (1, 2):
        year += 1
    return date(year, month, day_num)

def parse_day_with_playwright(page, day):
    events = page.locator(".event").all()
    print(f" [{day}] fant {len(events)} event(s)")

    for i, item in enumerate(events):
        try:
            guid = str(uuid.uuid4())
            title = item.locator("div.event-details a h2").first.inner_text()
            date_val = parse_norsk_dato(day)
            start_time = item.locator("div.ticket-time").first.inner_text()

            length_scraped = item.locator("div.event-properties").first.inner_text()
            parts = [p.strip() for p in length_scraped.split("|")]

            age = info = length = ""
            if len(parts) == 1:
                age = parts[0]
            elif len(parts) == 2:
                age, length = parts
            elif len(parts) == 3:
                age, info, length = parts

            screen_scrape = item.locator("div.ticket-title").first.inner_text()
            screen = [s.strip() for s in screen_scrape.split("|")]

            poster_element = item.locator("a.event-poster").first
            style = poster_element.get_attribute("style")
            filename = None
            image_url = None
            match = re.search(r'url\("(.*?)"\)', style)
            if match:
                image_url = match.group(1).split("?")[0]
            if image_url:
                safe_title = re.sub(r'[^\w\-_.]', '_', title.strip())
                filename = f"posters/{safe_title}.jpg"
                os.makedirs("posters", exist_ok=True)
                if not os.path.exists(filename):
                    response = page.request.get(image_url)
                    if response.ok:
                        with open(filename, 'wb') as f:
                            f.write(response.body())
                        print(f"Lagret bilde: {filename}")

            print(f" Visning {i+1}: {guid}, {date_val}, {start_time}, {title}, {age}, {info}, {length}, {screen[1]}, {filename}, {imdb}")
            c.execute("""
                INSERT INTO movies VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (guid, str(date_val), start_time, title, age, info, length, screen[1] if len(screen) > 1 else "", filename, imdb))
            conn.commit()

        except Exception as e:
            print(f" Feil ved parsing av visning {i+1}: {e}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        page = browser.new_page()
        page.goto("https://namsos.kulturhus.no/kinoprogram/")
        page.wait_for_selector(".calendar-card")

        sett_med_datoer = set()
        tidligere_datoer = set()

        while True:
            dager = page.locator(".calendar-card").all()
            dagens_datoer = set()
            for dag in dager:
                day = dag.inner_text().strip().replace("\n", " ")
                if day:
                    dagens_datoer.add(day)

            if dagens_datoer.issubset(sett_med_datoer):
                print("Ingen nye dager – stopper")
                break
            sett_med_datoer.update(dagens_datoer)

            for i, dag in enumerate(dager):
                day = dag.inner_text().strip().replace("\n", " ")
                if day and day not in tidligere_datoer:
                    try:
                        dag.click()
                        page.wait_for_selector(".events", state="attached", timeout=5000)
                        parse_day_with_playwright(page, day)
                        tidligere_datoer.add(day)
                    except Exception as e:
                        print(f" Klarte ikke klikke: {e}")

            navigasjonsknapper = page.locator(".navigation .icon-button")
            if navigasjonsknapper.count() < 2:
                break
            høyre_pil = navigasjonsknapper.nth(1)
            try:
                høyre_pil.click()
                time.sleep(1)
            except:
                break
        browser.close()
    conn.close()

main()

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
import sqlite3
import os
import re
from datetime import datetime, date
import uuid




os.makedirs("screenshots", exist_ok=True)

conn = sqlite3.connect('culture.db') 
c = conn.cursor()
imdb = ""

c.execute('''CREATE TABLE IF NOT EXISTS movies(
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
''')


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
            date = parse_norsk_dato(day)  
            start_time = item.locator("div.ticket-time").first.inner_text()

            length_scraped = item.locator("div.event-properties").first.inner_text()           
            parts = [p.strip() for p in length_scraped.split("|")]

            parts = [p.strip() for p in length_scraped.split("|")]

            # Initialiser alle felter
            age = info = length = ""

            if len(parts) == 1:
                age = parts[0]
            elif len(parts) == 2:
                age, length = parts
            elif len(parts) == 3:
                age, info, length = parts
            else:
                print(f"Uventet format i event-properties: {length}")




            screen_scrape = item.locator("div.ticket-title").first.inner_text()
            screen = [s.strip() for s in screen_scrape.split("|")]



            #### poster
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

                if os.path.exists(filename):
                    print(f"Filen finnes allerede: {filename}")
                else:
                    response = page.request.get(image_url)
                    if response.ok:
                        with open(filename, 'wb') as f:
                            f.write(response.body())
                        print(f"Lagret bilde: {filename}")
                    else:
                        print(f"Feil ved nedlasting: {response.status}")
            else:
                print(f"Fant ikke bilde-URL for {title}")



                
            print(f" Visning {i+1}: {guid}, {date}, {start_time}, {title}, {age}, {info}, {length}, {screen[1]}, {filename}, {imdb}")
            c.execute('''INSERT INTO  movies VALUES(?,?,?,?,?,?,?,?,?,?)''', ((guid), (date), (start_time), (title), (age), (info), (length), (screen[1]), (filename), (imdb)))
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
            # 1) Hent datoene på skjermen
            dager = page.locator(".calendar-card").all()
            dagens_datoer = set()

            for dag in dager:
                day = dag.inner_text().strip().replace("\n", " ")                  
                if day:
                    dagens_datoer.add(day)
                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")                 
            #print(f" Fant {len(dagens_datoer)} dager på skjermen")

            # Har vi sett disse før?
            if dagens_datoer.issubset(sett_med_datoer):
                print("Ingen nye dager – stopper")
                break

            # Lagre datoene
            sett_med_datoer.update(dagens_datoer)

            # Klikk på hver dag
            for i, dag in enumerate(dager):
                day = dag.inner_text().strip().replace("\n", " ")
                if day and day not in tidligere_datoer:
                    #print(f" Klikker på: {day}")
                    try:
                        dag.click()
                        # Vent på at minst én program-item dukker opp i DOM
                        page.wait_for_selector(".events", state="attached", timeout=5000)

                        # Ekstra trygghet: vent på at minst én faktisk er der
                        for _ in range(10):
                            if page.locator(".events").count() > 0:
                                break
                            time.sleep(0.5)
                        else:
                            print("  Timeout – fant ingen events etter klikk")
                            continue

                        parse_day_with_playwright(page, day)
                        tidligere_datoer.add(day)
                    except Exception as e:
                        print(f" Klarte ikke klikke: {e}")

            # Finn høyre-pil og klikk
            navigasjonsknapper = page.locator(".navigation .icon-button")
            if navigasjonsknapper.count() < 2:
                print(" Fant ikke høyre-pil – avslutter")
                break

            høyre_pil = navigasjonsknapper.nth(1)
            try:
                høyre_pil.click()
                #print(" Klikket høyre-pil")
                time.sleep(1)
            except Exception as e:
                print(f" Klarte ikke klikke på høyre-pil: {e}")
                break

  
        browser.close()
    conn.commit()
    conn.close()  







main()


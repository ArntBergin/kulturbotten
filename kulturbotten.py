from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
import sqlite3
import os
import re

os.makedirs("screenshots", exist_ok=True)

conn = sqlite3.connect('culture.db') 
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS movies(
    day TEXT,
    title TEXT,
    start_time TEXT,
    length TEXT,
    screen TEXT,
    filename TEXT,
    UNIQUE(day, title, start_time)
)
''')




def parse_day_with_playwright(page, day):
    events = page.locator(".event").all() 
    print(f" [{day}] fant {len(events)} event(s)")

    for i, item in enumerate(events):
        try:
            title = item.locator("div.event-details a h2").first.inner_text()
            start_time = item.locator("div.ticket-time").first.inner_text()
            length = item.locator("div.event-properties").first.inner_text()
            screen = item.locator("div.ticket-title").first.inner_text()

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

                

     
        except Exception as e:
            print(f" Feil ved parsing av visning {i+1}: {e}")            



        print(f" Visning {i+1}: {day}, {title}, {start_time}, {length}, {screen}")
        c.execute('''INSERT INTO movies VALUES(?,?,?,?,?,?)''', ((day), (title), (start_time), (length), (screen), (filename)))



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

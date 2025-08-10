from sqlmodel import SQLModel, Field, create_engine, Session
from datetime import date
import os
import uuid
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

# === Database URL fra miljøvariabel ===
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL må settes som miljøvariabel")

engine = create_engine(DATABASE_URL, echo=True)

# === Modell definisjon (samme som i API) ===
class Movies(SQLModel, table=True):
    guid: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    date: str
    start_time: str
    title: str
    age: str
    info: str
    length: str
    screen: str
    filename: str
    imdb: str

# Opprett tabeller hvis de ikke finnes
def create_tables():
    SQLModel.metadata.create_all(engine)

# Eksempel på norsk dato parsing (kan justeres)
def parse_norsk_dato(date_str: str) -> date:
    months = {
        "januar": 1, "februar": 2, "mars": 3, "april": 4,
        "mai": 5, "juni": 6, "juli": 7, "august": 8,
        "september": 9, "oktober": 10, "november": 11, "desember": 12
    }
    parts = date_str.strip().split()
    day_num = int(parts[1].replace(".", ""))
    month_name = parts[2].lower()
    month = months[month_name]
    year = date.today().year
    return date(year, month, day_num)

# Hoved scraping-funksjon, som lagrer i DB
def parse_day_with_playwright(session: Session, page, day):
    events = page.locator(".event").all()
    print(f" [{day}] fant {len(events)} event(s)")

    for i, item in enumerate(events):
        try:
            title = item.locator("div.event-details a h2").first.inner_text()
            date_parsed = parse_norsk_dato(day)
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

            # Poster/filer håndtering (kan tilpasses)
            filename = None
            poster_element = item.locator("a.event-poster").first
            style = poster_element.get_attribute("style")
            match = re.search(r'url\("(.*?)"\)', style)
            if match:
                image_url = match.group(1).split("?")[0]
                safe_title = re.sub(r'[^\w\-_.]', '_', title.strip())
                filename = f"posters/{safe_title}.jpg"
                # Nedlasting av bildet kan implementeres her

            imdb = ""

            movie = Movies(
                date=str(date_parsed),
                start_time=start_time,
                title=title,
                age=age,
                info=info,
                length=length,
                screen=screen[1] if len(screen) > 1 else "",
                filename=filename or "",
                imdb=imdb
            )
            session.add(movie)
            session.commit()
            print(f" Lagret movie: {title}")

        except Exception as e:
            print(f" Feil ved parsing av visning {i+1}: {e}")

def main():
    create_tables()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://namsos.kulturhus.no/kinoprogram/")
        page.wait_for_selector(".calendar-card")

        with Session(engine) as session:
            seen_days = set()
            while True:
                dager = page.locator(".calendar-card").all()
                dagens_datoer = set()

                for dag in dager:
                    day = dag.inner_text().strip().replace("\n", " ")
                    if day:
                        dagens_datoer.add(day)

                if dagens_datoer.issubset(seen_days):
                    print("Ingen nye dager – stopper")
                    break

                seen_days.update(dagens_datoer)

                for dag in dager:
                    day = dag.inner_text().strip().replace("\n", " ")
                    if day not in seen_days:
                        try:
                            dag.click()
                            page.wait_for_selector(".events", state="attached", timeout=5000)
                            for _ in range(10):
                                if page.locator(".events").count() > 0:
                                    break
                                time.sleep(0.5)
                            else:
                                print("Timeout – fant ingen events")
                                continue
                            parse_day_with_playwright(session, page, day)
                            seen_days.add(day)
                        except Exception as e:
                            print(f"Klarte ikke klikke: {e}")

                nav_buttons = page.locator(".navigation .icon-button")
                if nav_buttons.count() < 2:
                    print("Fant ikke høyre-pil – avslutter")
                    break

                try:
                    nav_buttons.nth(1).click()
                    time.sleep(1)
                except Exception as e:
                    print(f"Klarte ikke klikke på høyre-pil: {e}")
                    break

        browser.close()

if __name__ == "__main__":
    main()

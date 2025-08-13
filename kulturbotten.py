from sqlmodel import SQLModel, Field, create_engine, Session, select
from datetime import date
from playwright.sync_api import sync_playwright


import subprocess
import os
import uuid
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

            # ===  filnavn-variabler ===

            filename_url = ""
            filename_local = ""

            # === Hent attributt fra posterelementet ===
            poster = item.locator("a.event-poster").first.get_attribute("style")

            # === Sjekk inneholder en bilde-URL ===
            if poster and "url(" in poster:
                # Hent ut selve URL
                url_start = poster.split('url("')[1].split('")')[0].split("?")[0]

                # Lag et trygt filnavn basert på tittelen
                safe_title = "".join(c if c.isalnum() else "_" for c in title.strip())

                # Lokal sti for lagring på disk
                filename_local = f"/app/posters/{safe_title}.jpg"

                # URL-sti som brukes i API og Home Assistant
                filename_url = f"posters/{safe_title}.jpg"

                # === Last ned bilde hvis det ikke finnes fra før ===
                if not os.path.exists(filename_local):
                    image_response = page.request.get(url_start)
                    with open(filename_local, "wb") as f:
                        f.write(image_response.body())
                    print(f"📸 Lagret bilde: {filename_local}")
                else:
                    print(f"🔁 Bilde finnes allerede: {filename_local}")



            imdb = ""

            # Sjekk om filmen allerede finnes
            existing = session.exec(
                select(Movies).where(
                    Movies.title == title,
                    Movies.date == str(date_parsed),
                    Movies.start_time == start_time
                )
            ).first()

            if existing:
                print(f" Hopper over duplikat: {title} {start_time}")
                continue

            # Hvis ikke, lagre filmen
            movie = Movies(
                date=str(date_parsed),
                start_time=start_time,
                title=title,
                age=age,
                info=info,
                length=length,
                screen=screen[1] if len(screen) > 1 else "",
                filename=filename_url,
                imdb=imdb
            )
            print("Klargjør for lagring:", movie.dict())
            session.add(movie)
            session.commit()
            print(f" Lagret movie: {title}")

        except Exception as e:
            print(f" Feil ved parsing av visning {i+1}: {e}")

def main():
    create_tables()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) #### Husk headless før jeg bygger image!
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

                

                for dag in dager:
                    day = dag.inner_text().strip().replace("\n", " ")
                    if day not in seen_days:
                        try:
                            dag.click(force=True)
                            ...
                            parse_day_with_playwright(session, page, day)
                            seen_days.add(day)  # ← Flytt hit
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


# Når kulturbotten er ferdig:
subprocess.run(["python", "get_imdb.py"])
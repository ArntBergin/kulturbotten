from sqlmodel import SQLModel, Field, Session, create_engine, select, and_
from datetime import date
import datetime
import requests, os, time


class Movies(SQLModel, table=True):
    guid: str = Field(primary_key=True)
    title: str
    movie_date: date = Field(index=True)
    start_time: str
    age: str
    info: str
    length: str
    screen: str
    filename: str
    imdb: str  


# DB fra env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL må settes som miljøvariabel")

engine = create_engine(DATABASE_URL)


# Søk etter tittel i IMDb API
def get_first_allowed_title(title):
    url = f"https://api.imdbapi.dev/search/titles?query={title}"
    response = requests.get(url)

    if response.status_code == 200:
        title_data = response.json()
        current_year = datetime.date.today().year
        allowed_years = {current_year, current_year - 1}

        # Returner første treff med gyldig årstall
        for item in title_data.get("titles", []):
            if item.get("startYear") in allowed_years:
                return item
        return None
    else:
        print(f"Feil ved henting fra IMDb API. Statuskode: {response.status_code}")
        return None


### Oppdater alle filmer med rating eller marker som NOT_FOUND 
with Session(engine) as session:
    # Hent alle filmer fra databasen
    all_movies = session.exec(select(Movies)).all()

    # Lag en liste over unike titler som mangler IMDb-rating
    unique_titles = set(
        movie.title for movie in all_movies
        if not movie.imdb or movie.imdb.strip() == "" or movie.imdb == "NOT_FOUND"
    )

    # Gå gjennom hver tittel og hent rating fra API
    for title in unique_titles:
        result = get_first_allowed_title(title)
        time.sleep(1.5)  # Unngå 429 timeout feil

        if result:
            rating = result.get("rating", {}).get("aggregateRating")
            if rating:
                updated = 0
                for movie in all_movies:
                    if movie.title == title:
                        movie.imdb = str(rating)
                        session.add(movie)
                        updated += 1
                session.commit()
                print(f"✅ Oppdatert {updated} filmer med tittel '{title}' → rating: {rating}")
            else:
                print(f"ℹ️ Ingen rating funnet for '{title}' – markerer som NOT_FOUND")
                for movie in all_movies:
                    if movie.title == title:
                        movie.imdb = "NOT_FOUND"
                        session.add(movie)
                session.commit()
        else:
            print(f"❌ Fant ikke IMDb-data for '{title}' – markerer som NOT_FOUND")
            for movie in all_movies:
                if movie.title == title:
                    movie.imdb = "NOT_FOUND"
                    session.add(movie)
            session.commit()

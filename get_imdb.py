from sqlmodel import SQLModel, Field, Session, create_engine, select
from datetime import date
import datetime, requests, os, time


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
    thumbnail: str
    imdb_rating: str
    imdb_orgtitle: str
    imdb_id: str


# DB fra env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL må settes som miljøvariabel")

engine = create_engine(DATABASE_URL)


# Søk etter tittel i IMDb API
def get_first_allowed_title(title: str):
    url = f"https://api.imdbapi.dev/search/titles?query={title}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Feil ved henting fra IMDb API. Statuskode: {response.status_code}")
        return None

    title_data = response.json()
    current_year = datetime.date.today().year
    allowed_years = {current_year, current_year - 1}

    for item in title_data.get("titles", []):
        if item.get("startYear") in allowed_years:
            return item
    return None


# Oppdater filmer
with Session(engine) as session:
    all_movies = session.exec(select(Movies)).all()

    # Finn unike titler uten rating og komplettere med rating, orgtitle og id
    unique_titles = {
        m.title for m in all_movies
        if not m.imdb_rating or m.imdb_rating.strip() == "" or m.imdb_rating == "NOT_FOUND"
    }

    for title in unique_titles:
        result = get_first_allowed_title(title)
        time.sleep(1.5)  # throttle

        if result:
            imdb_rating = result.get("rating", {}).get("aggregateRating") or "NOT_FOUND"
            imdb_orgtitle   = result.get("originalTitle") or "NOT_FOUND"
            imdb_id     = result.get("id") or "NOT_FOUND"
        else:
            imdb_rating = "NOT_FOUND"
            imdb_orgtitle   = "NOT_FOUND"
            imdb_id     = "NOT_FOUND"

        updated = 0
        for movie in all_movies:
            if movie.title == title:
                movie.imdb_rating = str(imdb_rating)
                movie.imdb_orgtitle = imdb_orgtitle
                movie.imdb_id = imdb_id
                session.add(movie)
                updated += 1

        session.commit()
        print(
            f"Oppdatert {updated} filmer med '{title}' → "
            f"rating={imdb_rating}, orgtitle={imdb_orgtitle}, id={imdb_id}"
        )

        session.commit()
        print(f"Oppdatert {updated} filmer med tittel '{title}' → '{imdb_rating}' og '{imdb_id}'")

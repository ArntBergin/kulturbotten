from main import get_session, Movies  # hvis du bruker separate filer

import requests
import datetime
import json

imdbapi_url = "https://api.imdbapi.dev"


# == funksjon som henter alle titler ==
def get_all_titles(session: Session) -> list[str]:
    movies = session.exec(select(Movies.title)).all()
    return movies

def get_first_allowed_title(title):
    url = f"{imdbapi_url}/search/titles?query={title}"
    response = requests.get(url)

    if response.status_code == 200:
        title_data = response.json()
        current_year = datetime.datetime.now().year
        allowed_years = {current_year, current_year - 1}

        for item in title_data.get("titles", []):
            if item.get("startYear") in allowed_years:
                return item

        print("Ingen titler med gyldig årstall funnet. Her er hele resultatlisten:")
        print(json.dumps(title_data.get("titles", []), indent=2, ensure_ascii=False))
        return None

    else:
        print(f"Feil ved henting fra IMDb API. Statuskode: {response.status_code}")
        return None


title = "Barske Bøller 2"
first_allowed = get_first_allowed_title(title)

if first_allowed:
    print(f"{title} finnes med gyldig årstall i IMDb-APIet.")
    print(f"imdb_ID: {first_allowed.get('id')}")
    print(f"imdb_rating: {first_allowed.get('rating', {}).get('aggregateRating')}")



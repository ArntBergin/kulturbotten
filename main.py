from typing import List, Optional
from fastapi import Depends, FastAPI, Query
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, Session, SQLModel, create_engine, select, desc, extract

from datetime import date, datetime

import os
import logging

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === DATABASE (PostgreSQL) ===
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL må settes")
engine = create_engine(DATABASE_URL, echo=True)


# === MODELLER ===
class MovieRead(SQLModel, table=True):
    __tablename__ = "movies"  # type: ignore
    guid: Optional[str] = Field(default=None, primary_key=True)
    movie_date: date = Field(index=True)
    start_time: str
    title: str = Field(index=True)
    age: str
    info: str
    length: str
    screen: str
    filename: str
    imdb: str


# === HJELPEFUNKSJONER ===
def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# === FASTAPI APP ===
app = FastAPI(title="Kulturbotten API")


# === EVENT HOOKS ===
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# === ENDEPUNKTER ===


os.makedirs("/app/posters", exist_ok=True)
app.mount("/posters", StaticFiles(directory="/app/posters"), name="posters")


@app.get("/movies/", response_model=dict[str, List[MovieRead]])
def read_movies(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1),
    sort_desc: bool = Query(False, description="Sort descending by date and start_time")
):
    if sort_desc:
        query = select(MovieRead).order_by(desc(MovieRead.movie_date), desc(MovieRead.start_time))
    else:
        query = select(MovieRead).order_by(MovieRead.movie_date, MovieRead.start_time) # type: ignore

    query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    movies = session.exec(query).all()
    return {"movies": movies}


@app.get("/movies/today", response_model=dict[str, List[MovieRead]])
def read_movies_today(
    session: Session = Depends(get_session),
    sort_desc: bool = Query(False, description="Sort descending by start_time")
):
    query_date = datetime.today().date()
    if sort_desc:
        query = select(MovieRead).where(MovieRead.movie_date == query_date).order_by(desc(MovieRead.start_time))
    else:
        query = select(MovieRead).where(MovieRead.movie_date == query_date)

    movies = session.exec(query).all()
    return {"movies": movies}


@app.get("/movies/by_date", response_model=dict[str, List[MovieRead]])
def read_movies_by_date(
    movie_date: date = Query(..., min_length=10, max_length=10, description="Date in format YYYY-MM-DD"),
    session: Session = Depends(get_session),
    sort_desc: bool = Query(False, description="Sort descending by start_time")
):
    if sort_desc:
        query = select(MovieRead).where(MovieRead.movie_date == movie_date).order_by(desc(MovieRead.start_time))
    else:
        query = select(MovieRead).where(MovieRead.movie_date == movie_date).order_by(MovieRead.start_time)

    movies = session.exec(query).all()
    return {"movies": movies}


@app.get("/movies/by_year", response_model=dict[str, List[MovieRead]])
def read_movies_by_year(
    year: int = Query(..., min_length=4, max_length=4, ge=1900, le=2100, description="Years in format YYYY"),
    session: Session = Depends(get_session),
    sort_desc: bool = Query(False, description="Sort descending by date and start_time")
):
    if sort_desc:
        query = select(MovieRead).where(extract("year", MovieRead.movie_date) == year).order_by(desc(MovieRead.movie_date), desc(MovieRead.start_time))
    else:
        query = select(MovieRead).where(extract("year", MovieRead.movie_date) == year).order_by(MovieRead.movie_date, MovieRead.start_time) # type: ignore

    movies = session.exec(query).all()
    return {"movies": movies}
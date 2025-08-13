from typing import List, Optional
from fastapi import Depends, FastAPI, Query
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, Session, SQLModel, create_engine, select
from starlette.responses import FileResponse
from datetime import datetime

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
    date: str = Field(index=True)
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

app.mount("/posters", StaticFiles(directory="/app/posters"), name="posters")

#Sortere først etter date, deretter start_time
@app.get("/movies/", response_model=dict[str, List[MovieRead]])
def read_movies(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1)
):
    query = select(MovieRead).order_by(MovieRead.date, MovieRead.start_time).offset(offset)
    if limit:
        query = query.limit(limit)
    movies = session.exec(query).all()
    return {"movies": movies}

@app.get("/movies/today", response_model=dict[str, List[MovieRead]])
def read_movies_today(
    date: Optional[str] = Query(None),
    description="Today's movies",
    session: Session = Depends(get_session)
):
    query_date = date or datetime.today().isoformat()
    movies = session.exec(
        select(MovieRead).where(MovieRead.date == query_date)
    ).all()
    return {"movies": movies}



@app.get("/movies/by_date", response_model=dict[str, List[MovieRead]])
def read_movies_by_date(
    date: str = Query(..., min_length=10, max_length=10), description="Date in format YYYY-MM-DD",
    session: Session = Depends(get_session)
):
    movies = session.exec(
        select(MovieRead).where(MovieRead.date.startswith(date))
    ).all()
    return {"movies": movies}


@app.get("/movies/by_year", response_model=dict[str, List[MovieRead]])
def read_movies_by_year(
    year: str = Query(..., min_length=4, max_length=4), description="Years in format YYYY",
    session: Session = Depends(get_session)
):
    movies = session.exec(
        select(MovieRead).where(MovieRead.date.startswith(year))
    ).all()
    return {"movies": movies}


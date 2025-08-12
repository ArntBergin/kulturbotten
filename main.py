from typing import List, Optional
from fastapi import Depends, FastAPI, Query
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, Session, SQLModel, create_engine, select

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
    date: str
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

app.mount("/posters", StaticFiles(directory="posters"), name="posters")


@app.get("/movies/", response_model=dict[str, List[MovieRead]])
def read_movies(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    movies = session.exec(select(MovieRead).offset(offset).limit(limit)).all()
    return {"movies": movies}

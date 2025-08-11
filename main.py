from typing import Annotated, Optional
from fastapi import Depends, FastAPI, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

import os
import logging

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === DATABASE (PostgreSQL) ===
pg_url = os.getenv("DATABASE_URL")
if not pg_url:
    raise RuntimeError("DATABASE_URL må settes")
engine = create_engine(pg_url, echo=True)


# === MODELLER ===
class Movies(SQLModel, table=True):
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
@app.get("/movies/")
def read_movies(
    session: Annotated[Session, Depends(get_session)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Movies]:
    movies = session.exec(select(Movies).offset(offset).limit(limit)).all()
    return list(movies)

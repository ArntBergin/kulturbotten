from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, BackgroundTasks
from sqlmodel import Field, Session, SQLModel, create_engine, select
from contextlib import asynccontextmanager
import logging
import subprocess

logging.basicConfig(level=logging.INFO)


sqlite_file_name = "culture.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

app = FastAPI()

@app.post("/run-kulturbotten/")
def run_scraper(background_tasks: BackgroundTasks):
    # Kjører kulturbotten.py som en bakgrunnsprosess
    background_tasks.add_task(subprocess.run, ["python", "kulturbotten.py"])
    return {"status": "Scraper startet"}


class Movies(SQLModel, table=True):
    guid: str | None = Field(primary_key=True)
    date: str
    start_time: str
    title: str  = Field(index=True)
    age: str
    info: str
    length: str
    filename: str
    imdb: str


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_session)]


async def lifespan(app: FastAPI):
    create_db_and_tables()


@app.get("/movies/")
def read_movies(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Movies]:
    movies = session.exec(select(Movies).offset(offset).limit(limit)).all()
    return list(movies)


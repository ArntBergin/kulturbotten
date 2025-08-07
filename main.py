from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from contextlib import asynccontextmanager

sqlite_file_name = "culture.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

app = FastAPI()


class Movies(SQLModel, table=True):
    guid: str | None = Field(primary_key=True)
    day: str = Field(index=True)
    title: str
    start_time: str
    length: str
    screen: str
    filename: str
    imdb: float


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_session)]


async def lifespan(app: FastAPI):
    create_db_and_tables()


@app.get("/titles/")
def read_titles(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Movies]:
    titles = session.exec(select(Movies).offset(offset).limit(limit)).all()
    return titles


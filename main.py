from typing import Annotated, Optional
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

import os
import logging
import subprocess

logging.basicConfig(level=logging.INFO)

# === KONFIG ===
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === DATABASE ===
sqlite_file_name = "culture.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None

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

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# === AUTENTISERING ===
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_session():
    with Session(engine) as session:
        yield session

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kunne ikke validere token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user

# === APP ===
app = FastAPI(title="Kulturbotten API")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    with Session(engine) as session:
        if not session.exec(select(User).where(User.username == "admin")).first():
            hashed_pw = get_password_hash("admin123")
            admin_user = User(username="admin", hashed_password=hashed_pw, full_name="Administrator")
            session.add(admin_user)
            session.commit()

def register_user(
    username: str,
    password: str,
    session: Annotated[Session, Depends(get_session)],
    full_name: Optional[str] = None

):
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Brukernavn er allerede i bruk")
    hashed_pw = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_pw, full_name=full_name)
    session.add(new_user)
    session.commit()
    return {"msg": "Bruker registrert"}

@app.post("/token")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)]
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Feil brukernavn eller passord")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# === Åpent API ===
@app.get("/movies/")
def read_movies(
    session: Annotated[Session, Depends(get_session)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Movies]:
    movies = session.exec(select(Movies).offset(offset).limit(limit)).all()
    return list(movies)


@app.post("/run-kulturbotten/")
def run_scraper(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)]
):
    background_tasks.add_task(subprocess.run, ["python", "kulturbotten.py"])
    return {"status": "Scraper startet"}

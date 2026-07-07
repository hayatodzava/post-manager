from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, select, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime
import os
from dotenv import load_dotenv

# ========== DATABASE CONGIGURATION ==========
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+asyncmy://root:secret@localhost:3306/fastapi_db"
)

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# ========== JWT SETTINGS ==========
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Configuring password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme (for Swagger and token retrieval)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ========== INITIALIZING THE DB ==========
async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ========== DATABASE MODELS ==========
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)

class PostDB(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String(2000), nullable=True, default="")  
    is_public = Column(Boolean, default=False)                 
    user_id = Column(Integer, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

# ========== PYDANTIC MODELS ==========

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: int | None = None

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    is_admin: bool | None = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_admin: bool

class PostCreate(BaseModel):
    title: str
    content: str | None = None
    is_public: bool = False

class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    is_public: bool | None = None

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    is_public: bool
    user_id: int
    created_at: datetime
    updated_at: datetime


# ========== FASTAPI APPLICATION ==========
app = FastAPI()

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


# ========== PASSWORD FUNCTIONS ==========
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# ========== FUNCTIONS FOR JWT ==========
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(UserDB).where(UserDB.id == token_data.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


# ========== ENDPOINTS ==========

@app.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if there are any users in the database at all
    result = await db.execute(select(UserDB))
    users_count = len(result.scalars().all())
    
    # If there are no users, the first one becomes the admin
    is_admin = (users_count == 0)
    
    # Check if a user with this email already exists
    existing_user = (await db.execute(select(UserDB).where(UserDB.email == user_data.email))).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Creating a new user
    hashed_password = get_password_hash(user_data.password)
    db_user = UserDB(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=is_admin
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@app.get("/me", response_model=UserResponse)
async def get_me(current_user: UserDB = Depends(get_current_user)):
    return current_user

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(UserDB).where(UserDB.email == form_data.username))).scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users")
async def list_users(
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    result = await db.execute(select(UserDB))
    users = result.scalars().all()
    return users

@app.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(post: PostCreate, current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    db_post = PostDB(
        title=post.title,
        content=post.content or "",   
        is_public=post.is_public,     
        user_id=current_user.id
    )
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    return db_post

@app.get("/posts")
async def list_posts(current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.is_admin:
        result = await db.execute(select(PostDB).order_by(PostDB.created_at.desc()))
    else:
        result = await db.execute(
            select(PostDB).where(
                (PostDB.is_public == True) | (PostDB.user_id == current_user.id)
            ).order_by(PostDB.created_at.desc())
        )
    posts = result.scalars().all()
    
    posts_with_authors = []
    for post in posts:
        author_result = await db.execute(select(UserDB).where(UserDB.id == post.user_id))
        author = author_result.scalar_one_or_none()
        post_dict = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "is_public": post.is_public,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "author_name": author.name if author else f"User #{post.user_id}"
        }
        posts_with_authors.append(post_dict)
    
    return posts_with_authors

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return None

@app.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PostDB).where(PostDB.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    await db.delete(post)
    await db.commit()
    return None

@app.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Only the admin can edit users
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    existing_user = (await db.execute(select(UserDB).where(UserDB.id == user_id))).scalar_one_or_none()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_data.name is not None:
        existing_user.name = user_data.name
    
    if user_data.email is not None and user_data.email != existing_user.email:
        existing_email = (await db.execute(select(UserDB).where(UserDB.email == user_data.email))).scalar_one_or_none()
        if existing_email:
            raise HTTPException(status_code=400, detail="This email is already taken")
        existing_user.email = user_data.email
    
    if user_data.is_admin is not None:
        existing_user.is_admin = user_data.is_admin
    
    await db.commit()
    await db.refresh(existing_user)
    return existing_user

@app.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PostDB).where(PostDB.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check: owner or admin only
    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if post_data.title is not None:
        post.title = post_data.title
    if post_data.content is not None:
        post.content = post_data.content
    if post_data.is_public is not None:
        post.is_public = post_data.is_public
    
    post.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(post)
    return post

# ========== STARTING INITIALIZATION ==========
@app.on_event("startup")
async def on_startup():
    await init_db()
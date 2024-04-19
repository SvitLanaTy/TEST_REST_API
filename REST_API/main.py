import re
import uvicorn
from pathlib import Path
from typing import Callable

import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.routes import contacts, auth, users
from src.conf.config import config


app = FastAPI()

origins = ["*"]

# origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_agent_ban_list = [r"Googlebot", r"Python-urllib"]


@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    """
    The user_agent_ban_middleware function is a middleware function that checks the user-agent header of an incoming request.
    If the user-agent matches any of the patterns in USER_AGENT_BAN_LIST, then it returns a 403 Forbidden response.
    Otherwise, it calls call_next and returns its result.
    
    :param request: Request: Get the request object
    :param call_next: Callable: Pass the request to the next middleware in line
    :return: A jsonresponse object if the user agent matches a pattern in the list
    :doc-author: Trelent
    """
    print(request.headers.get("Authorization"))
    user_agent = request.headers.get("user-agent")
    print(user_agent)
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    response = await call_next(request)
    return response

BASE_DIR = Path(__file__).parent
directory = BASE_DIR.joinpath("src").joinpath("static")
app.mount("/static", StaticFiles(directory=directory), name="static")

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
    It's a good place to initialize things that are used by the app, such as databases or caches.
    
    :return: A list of functions to be executed
    :doc-author: Trelent
    """
    r = await redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )
    await FastAPILimiter.init(r)
    
    
templates = Jinja2Templates(directory=BASE_DIR / "src" / "templates")


# @app.get("/")
# def index():
#     return {"message": "Contacts list Application"}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    
    """
    The index function is executed when you visit the root URL of our application.
    It returns a TemplateResponse, which contains the contents of index.html and 
    the context (data) that index.html expects.
    
    :param request: Request: Get the request object
    :return: A templateresponse object
    :doc-author: Trelent
    """
    return templates.TemplateResponse(
        "index.html", context={"request": request, "our": "Build WebPython example"}
    )


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    The healthchecker function is a simple function that checks if the database connection is working.
    It does this by making a request to the database and checking if it returns any results.
    If there are no results, then we know something went wrong with our connection.
    
    :param db: AsyncSession: Pass the database session to the function
    :return: A dict with the message
    :doc-author: Trelent
    """
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
    
if __name__ == '__main__':
    uvicorn.run('main:app', host="localhost", port=8000, reload=True)
    
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import posts, auth, users

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')

app.include_router(posts.router)
app.include_router(auth.router)
app.include_router(users.router)


@app.get('/')
def home():
  return {'hi': 'hello'}

import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get('/')
def home():
    return {"Message": 'Hello World'}


@app.post('/Welcome')
def get_name(name: str):
    return {f"welcome to Fast API Learning {name}"}


@app.post('/{name}')
def get_name_exact(name: str):
    return {f"welcome to Fast API Learning {name}"}


if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)

# uvicorn FastAPI.main:app --reload

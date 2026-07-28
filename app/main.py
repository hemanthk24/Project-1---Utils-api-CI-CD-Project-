from fastapi import FastAPI
from pydantic import BaseModel
from app.utils import (
    slugify,
    word_frequency,
    is_prime,
    fibonacci,
    is_palindrome,
    flatten_json,
)


app = FastAPI(title="Utils API", version="1.0.0")

# request schema
class TextIn(BaseModel):
    text: str
    
class NumberIn(BaseModel):
    n: int
    
class JsonIn(BaseModel):
    data: dict
    
@app.get("/")
def lobby():
    return {"message":"Welcome to the Utils Project"}

# routes
@app.get("/health")
def health():
    return {"status":"ok"}


@app.post("/string/slugify")
def route_slugify(payload: TextIn):
    return {"result": slugify(payload.text)}

@app.post("/string/word-frequency")
def route_word_frequency(payload: TextIn):
    return {"result": word_frequency(payload.text)}


@app.post("/math/is-prime")
def route_is_prime(payload: NumberIn):
    return {"result": is_prime(payload.n)}


@app.post("/math/fibonacci")
def route_fibonacci(payload: NumberIn):
    return {"result": fibonacci(payload.n)}


@app.post("/text/palindrome-check")
def route_palindrome(payload: TextIn):
    return {"result": is_palindrome(payload.text)}


@app.post("/json/flatten")
def route_flatten(payload: JsonIn):
    return {"result": flatten_json(payload.data)}

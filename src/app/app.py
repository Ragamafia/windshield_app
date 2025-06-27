import json

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.app.calc import CarGlass
from config import cfg


app = FastAPI()
templates = Jinja2Templates(directory=cfg.templates)

with open(cfg.path_to_json_base, "r", encoding='utf-8') as file:
    data = json.load(file)

with open(cfg.path_to_json_hard, "r", encoding='utf-8') as file:
    hard = json.load(file)

HARD_CARS = set([l.strip() for l in hard])


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    brands = list(data.keys())

    markup = {
        "request": request,
        "brands": brands
    }
    return templates.TemplateResponse("index.html", markup)


@app.get("/brand/{brand}", response_class=HTMLResponse)
async def show_models(request: Request, brand: str):
    brands = data.get(brand)
    models = list(brands.keys())

    markup = {
        "request": request,
        "brand": brand,
        "models": models
    }
    return templates.TemplateResponse("models.html", markup)


@app.get("/{brand}/{model}", response_class=HTMLResponse)
async def show_gens(request: Request, brand: str, model: str):
    brands = data.get(brand)
    models = brands.get(model)
    gens = list(models.keys())

    markup = {
        "request": request,
        "brand": brand,
        "model": model,
        "gens": gens
    }
    return templates.TemplateResponse("gens.html", markup)


@app.get("/{brand}/{model}/{gen}", response_class=HTMLResponse)
async def show_info(request: Request, brand: str, model: str, gen:str):
    brands = data.get(brand)
    models = brands.get(model)
    size = models.get(gen)
    high_level = False

    if '*'.join([brand, model, gen]) in HARD_CARS:
        high_level = True

    price_usa, price_korea = CarGlass(size[1], high_level).get_prices()

    markup = {
        "request": request,
        "brand": brand,
        "model": model,
        "gen": gen,
        "size": size,
        'price_usa': price_usa,
        'price_korea': price_korea
    }
    return templates.TemplateResponse("info.html", markup)
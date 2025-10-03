from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.calc import Calculate
from db.ctrl import db
from config import cfg


app = FastAPI()
templates = Jinja2Templates(directory=cfg.templates)


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    brands = await db.get_brands()
    markup = {
        "request": request,
        "brands": [brand.brand for brand in brands]
    }
    return templates.TemplateResponse("index.html", markup)


@app.get("/brand/{brand}", response_class=HTMLResponse)
async def show_models(request: Request, brand: str):
    models = await db.get_models(brand)
    markup = {
        "request": request,
        "brand": brand,
        "models": [model.model for model in models]
    }
    return templates.TemplateResponse("models.html", markup)


@app.get("/{brand}/{model}", response_class=HTMLResponse)
async def show_gens(request: Request, brand: str, model: str):
    gens = await db.get_gens(brand, model)
    markup = {
        "request": request,
        "brand": brand,
        "model": model,
        "gens": sorted(f"{gen.year_start}-{gen.year_end}" for gen in gens)
    }
    return templates.TemplateResponse("gens.html", markup)


@app.get("/{brand}/{model}/{years}", response_class=HTMLResponse)
async def show_info(request: Request, brand: str, model: str, years:str):
    year_start = years.split("-")[0]
    car = await db.get_car(brand, model, year_start)
    price_usa, price_korea = await Calculate(car.width, car.difficulty).get_prices()
    markup = {
        "request": request,
        "brand": brand,
        "model": model,
        "gen": f"{car.gen} поколение",
        "years": years,
        "size": f"{car.height} x {car.width} мм",
        'price_usa': price_usa,
        'price_korea': price_korea
    }
    return templates.TemplateResponse("info.html", markup)

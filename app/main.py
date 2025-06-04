import json

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


app = FastAPI()

templates = Jinja2Templates(directory="templates")

with open("glasses.json", "r") as file:
    data = json.load(file)


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    brand = list(data.keys())

    return templates.TemplateResponse("index.html", {
        "request": request,
        "brands": brand
    })


@app.get("/brand/{brand_name}", response_class=HTMLResponse)
async def show_models(request: Request, brand_name: str):
    brands = data.get(brand_name.lower())
    # if not model:
    #     return HTMLResponse(content=f"<h2>Марка {brand_name} не найдена</h2>", status_code=404)
    models = list(brands.keys())

    return templates.TemplateResponse("models.html", {
        "request": request,
        "brand": brand_name,
        "models": models
    })


@app.get("/{brand}/{model}", response_class=HTMLResponse)
async def show_gens(request: Request, brand: str, model: str):
    brands = data.get(brand.lower())
    models = brands.get(model.lower())
    gens = list(models.keys())

    return templates.TemplateResponse("gens.html", {
        "request": request,
        "brand": brand,
        "model": model,
        "gens": gens
    })


@app.get("/{brand}/{model}/{gen}", response_class=HTMLResponse)
async def show_info(request: Request, brand: str, model: str, gen:str):
    brands = data.get(brand.lower())
    models = brands.get(model)
    info = models.get(gen)

    return templates.TemplateResponse("info.html", {
        "request": request,
        "brand": brand,
        "model": model,
        "gen": gen,
        "info": info,
    })
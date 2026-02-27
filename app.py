from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import pickle
import numpy as np

app = FastAPI()


with open("model.pkl", "rb") as f:
    model = pickle.load(f)

class WineInput(BaseModel):
    fixed_acidity: float
    volatile_acidity: float
    citric_acid: float
    residual_sugar: float
    chlorides: float
    free_sulfur_dioxide: float
    total_sulfur_dioxide: float
    density: float
    pH: float
    sulphates: float
    alcohol: float
    
@app.get("/",include_in_schema=False)
def root():
    return RedirectResponse(url="/docs",status_code=301)

@app.post("/predict")
def predict(data: WineInput):
    X = np.array(data.features).reshape(1, -1)
    prediction = model.predict(X)[0]

    return {
        "name": "R J Hari",
        "roll_no": "2022BCS0125",
        "wine_quality": int(round(prediction))
    }


import numpy as np
from src.models.rainfall_model import build_models

def test_model_probability_bounds():
    m=build_models()["significant"]; x=np.arange(40).reshape(20,2); y=np.array([0,1]*10); m.fit(x,y)
    p=m.predict_proba(x)[:,1]; assert ((p>=0)&(p<=1)).all()

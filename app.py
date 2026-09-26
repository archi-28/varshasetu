"""VarshaSetu Streamlit application."""
from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.config import load_config
from src.data.loader import load_weather_data
from src.data.validator import validate_weather_frame
from src.data.preprocessing import preprocess
from src.features.engineering import BASE
from src.models.model_manager import load_models
from src.forecasting.predictor import predict_block
from src.risk.risk_engine import overall_risk, risk_level
from src.risk.onset_detector import detect_onset
from src.agriculture.crops import CROPS
from src.agriculture.advisory_engine import generate_advisory
from src.alerts.message_generator import generate_message
from src.alerts.notification_service import MockNotificationService
from src.gis.map_builder import build_map
from src.utils.logging_utils import get_logger

APP_NAME = load_config().get("app_name", "VarshaSetu")
st.set_page_config(page_title=APP_NAME, page_icon="🌦️", layout="wide")
log = get_logger()

def data_signature():
    cfg = load_config()
    paths = [ROOT / cfg["data"]["sample"]]
    return tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size)
                 for path in paths if path.exists())

@st.cache_data
def data_bundle(signature):
    del signature  # File stat signature participates in Streamlit's cache key.
    frame, mode = load_weather_data()
    if errors := validate_weather_frame(frame):
        raise ValueError("Input data failed validation: " + "; ".join(errors))
    return frame, preprocess(frame), mode

@st.cache_resource
def model_bundle(current_data_mode):
    from scripts.train_model import train
    cfg = load_config()
    path = ROOT / cfg["data"]["model"]
    existing = load_models() if path.exists() else None
    if existing is None or existing.get("data_mode") != current_data_mode:
        st.info("Model not found. Running first-time setup...")
        train()
    return load_models()

try:
    raw, features, data_mode = data_bundle(data_signature())
    models = model_bundle(data_mode)
except Exception as exc:
    log.exception("startup failed")
    st.error(f"Startup could not load data/model: {exc}")
    st.stop()
cfg = load_config()
observed_blocks = set(features["block"].astype(str).unique())
blocks = [name for name in cfg["blocks"] if name in observed_blocks]
if not blocks:
    st.error("The demo dataset has no configured blocks. Regenerate it with `python scripts/generate_demo_data.py`.")
    st.stop()

source_badge = "🧪 &nbsp;SYNTHETIC DEMO"
st.markdown(f"<div class='hero'><div><div class='eyebrow'>CLIMATE INTELLIGENCE · MEERUT, UTTAR PRADESH</div><h1>🌦️ {APP_NAME}</h1><p>Monsoon Risk Exploration &amp; Agricultural Advisory</p></div><div class='source-pill'>{source_badge}</div></div>", unsafe_allow_html=True)
st.markdown("""<style>
.hero{background:linear-gradient(115deg,#123d31,#18794e 65%,#6ba77b);padding:26px 32px;border-radius:18px;color:white;display:flex;justify-content:space-between;align-items:center;margin:0 0 22px}.hero h1{font-size:2.3rem;margin:4px 0;color:white}.hero p{margin:0;color:#e2f2e7}.eyebrow{letter-spacing:.15em;font-size:.72rem;opacity:.8}.source-pill{background:#ffffff24;border:1px solid #ffffff55;border-radius:20px;padding:10px 14px;font-size:.8rem}.metric{background:white;border:1px solid #e2ebe3;border-radius:14px;padding:14px 18px;box-shadow:0 3px 14px #173d2b0a}.metric-label{font-size:.8rem;color:#537264}.metric-value{font-size:1.8rem;font-weight:700;color:#183d2c}.metric-note{font-size:.78rem;color:#6b8176}.risk-badge{padding:4px 9px;border-radius:12px;background:#e7f3e9;color:#18794e;font-size:.78rem;font-weight:700}
</style>""", unsafe_allow_html=True)
st.sidebar.title(f"🌦️ {APP_NAME}")
st.sidebar.caption("DEMO DATA · Meerut district")
block = st.sidebar.selectbox("Block", ["All Blocks"] + blocks)
horizon = st.sidebar.select_slider("Forecast horizon", options=[7,14,30], value=7, format_func=lambda x:f"{x} days")
crop = st.sidebar.selectbox("Crop", list(CROPS))
language = st.sidebar.selectbox("Language", ["English", "हिन्दी"])
page = st.sidebar.radio("Workspace", ["Dashboard", "Block Details", "Model Performance", "Data Explorer", "Farmer Alert"])
st.sidebar.caption("Synthetic demonstration data; not observed weather.")

def latest_row(name):
    subset=features[features.block==name]
    return subset.iloc[-1]

@st.cache_data
def forecast_records(_features, _models, block_names, h):
    # Internal cache signature is provided by immutable latest feature values below.
    result=[]
    for name in block_names:
        row=_features[_features.block==name].iloc[-1]
        pred=predict_block(_models,row,h)
        recent=raw[raw.block==name].tail(30).rainfall_mm
        onset=detect_onset(recent, cfg["thresholds"]["onset_rainfall_mm"], cfg["thresholds"]["onset_consecutive_days"])
        score=overall_risk(pred["rain_probability"],pred["dry_spell_probability"],pred["heavy_rain_probability"])
        result.append({"block":name,"latitude":float(row.latitude),"longitude":float(row.longitude),**pred,"overall_score":score,**onset})
    return result

# Cached functions cannot hash mutable model objects, so build the small regional inference batch once per Streamlit run.
records=[]
for name in blocks:
    row=latest_row(name); pred=predict_block(models,row,horizon)
    recent=raw[raw.block==name].tail(30).rainfall_mm
    onset=detect_onset(recent,cfg["thresholds"]["onset_rainfall_mm"],cfg["thresholds"]["onset_consecutive_days"])
    records.append({"block":name,"latitude":float(row.latitude),"longitude":float(row.longitude),**pred,"overall_score":overall_risk(pred["rain_probability"],pred["dry_spell_probability"],pred["heavy_rain_probability"]),**onset})
selected=next((r for r in records if r["block"]==block),records[0])
advisory=generate_advisory(crop,selected["rain_probability"],selected["dry_spell_probability"],selected["heavy_rain_probability"],selected["expected_rainfall"],selected["status"],selected["false_onset_risk"],"hi" if language=="हिन्दी" else "en")

if page == "Dashboard":
    scope=records if block=="All Blocks" else [selected]
    avg=lambda key:sum(r[key] for r in scope)/len(scope)
    k1,k2,k3,k4=st.columns(4)
    for col,label,value,note in [(k1,"Rainfall probability",avg("rain_probability"),"Significant rain in horizon"),(k2,"Dry spell risk",avg("dry_spell_probability"),"4+ dry days heuristic"),(k3,"Heavy rain risk",avg("heavy_rain_probability"),"Threshold in config.yaml"),(k4,"Overall risk",avg("overall_score")/100,risk_level(avg("overall_score")) )]:
        col.markdown(f"<div class='metric'><div class='metric-label'>{label}</div><div class='metric-value'>{value:.0%}</div><div class='metric-note'>{note}</div></div>",unsafe_allow_html=True)
    st.write("")
    mcol,acol=st.columns([1.35,1],gap="large")
    with mcol:
        st.subheader("Block-level risk map")
        map_layer=st.selectbox("Map layer",["Overall Risk","Rainfall Risk","Dry Spell Risk","Heavy Rain Risk"],label_visibility="collapsed")
        st.caption("Demo marker locations; they are not official administrative boundaries.")
        st_folium(build_map(scope,map_layer),height=470,use_container_width=True,returned_objects=[])
    with acol:
        st.subheader(f"{horizon}-day monsoon outlook · {selected['block']}")
        st.caption(selected["model_label"] + (" · Daily shape is a disaggregation of the 7-day model total." if horizon>7 else ""))
        daily=selected["daily_rainfall"]
        days=[f"D{i+1}" for i in range(len(daily))]
        fig=px.bar(x=days,y=daily,labels={"x":"Forecast day","y":"Expected rainfall (mm)"},color=daily,color_continuous_scale=["#cde8dc","#23865b"])
        fig.update_layout(showlegend=False,coloraxis_showscale=False,margin=dict(l=0,r=0,t=10,b=0),height=260)
        st.plotly_chart(fig,use_container_width=True)
        st.markdown(f"#### {advisory['headline']}")
        st.write(advisory["summary"])
        for action in advisory["recommended_actions"]: st.markdown(f"- {action}")
        for warning in advisory["warnings"]: st.warning(warning)
    with st.expander("Why this forecast?"):
        st.write("Model feature importance is a predictive diagnostic, not causal attribution.")
        st.write("Latest inputs include recent rainfall, temperature, humidity, ENSO, IOD, and cyclic MJO phase features.")
    st.caption("Prototype decision support only. Forecasts use synthetic demonstration data and do not replace official meteorological forecasts or qualified agricultural advice.")
elif page == "Block Details":
    st.title(f"BLOCK DETAILS · {selected['block']}")
    st.caption("Coordinates are representative demo points, not verified block polygons.")
    st.write(f"Coordinates: {selected['latitude']:.4f}, {selected['longitude']:.4f}")
    cols=st.columns(4)
    for c,label,val in zip(cols,["Expected rainfall","Rain probability","Dry spell risk","Heavy rain risk"],[f"{selected['expected_rainfall']:.1f} mm",f"{selected['rain_probability']:.0%}",f"{selected['dry_spell_probability']:.0%}",f"{selected['heavy_rain_probability']:.0%}"]): c.metric(label,val)
    st.write("Monsoon status:",selected["status"]," · False onset risk:","High" if selected["false_onset_risk"] else "Low")
    st.info("Model probabilities are prototype estimates from synthetic training data. They have not been calibrated against operational observations.")
    st.subheader("Daily outlook")
    st.plotly_chart(px.bar(x=[f"Day {i+1}" for i in range(len(selected['daily_rainfall']))],y=selected["daily_rainfall"],labels={"x":"Day","y":"Rainfall (mm)"}),use_container_width=True)
elif page == "Model Performance":
    st.title("Model Performance")
    met=models.get("metrics",{})
    cols=st.columns(5)
    for c,label,key in zip(cols,["Model","MAE","RMSE","R²","Rain F1"],[None,"mae","rmse","r2","significant_f1"]): c.metric(label,"Random Forest" if key is None else f"{met.get(key,float('nan')):.3f}")
    st.write("Classifier metrics · Rain / Dry / Heavy")
    metric_rows=[]
    for key,label in [("significant","Significant rain"),("dry","Dry spell"),("heavy","Heavy rain")]:
        metric_rows.append({"Target":label,"Precision":met.get(f"{key}_precision",float("nan")),"Recall":met.get(f"{key}_recall",float("nan")),"F1":met.get(f"{key}_f1",float("nan")),"ROC-AUC":met.get(f"{key}_roc_auc",float("nan"))})
    st.dataframe(pd.DataFrame(metric_rows).set_index("Target"),use_container_width=True)
    st.caption("Chronological 80/20 holdout; values are for synthetic demo data, not field validation.")
    sample_test=features.tail(250)
    pred=models["rainfall"].predict(sample_test[BASE]); actual=sample_test.future_7day_rainfall_mm
    fig=px.scatter(x=actual,y=pred,labels={"x":"Actual next-7-day rainfall (mm)","y":"Predicted (mm)"},opacity=.5)
    fig.add_trace(go.Scatter(x=[0,max(actual.max(),pred.max())],y=[0,max(actual.max(),pred.max())],mode="lines",name="Ideal"))
    st.plotly_chart(fig,use_container_width=True)
    target=sample_test.significant_rain_target.to_numpy(); predcls=models["significant"].predict(sample_test[BASE]);
    from sklearn.metrics import confusion_matrix
    cm=confusion_matrix(target,predcls,labels=[0,1])
    st.plotly_chart(px.imshow(cm,text_auto=True,x=["Predicted no","Predicted yes"],y=["Actual no","Actual yes"],color_continuous_scale="Greens",title="Significant-rain confusion matrix"),use_container_width=True)
    importance=pd.Series(models["rainfall"].feature_importances_,index=BASE).sort_values().tail(12)
    st.subheader("Model feature importance — not causal influence")
    st.plotly_chart(px.bar(x=importance.values,y=importance.index,orientation="h",labels={"x":"Importance","y":"Feature"}),use_container_width=True)
elif page == "Data Explorer":
    st.title("Data Explorer")
    name=st.selectbox("Block",blocks,index=blocks.index(block) if block in blocks else 0)
    history=raw[raw.block==name].copy()
    chosen=st.selectbox("Variable",["rainfall_mm","temperature_c","humidity_pct","enso","iod","mjo_phase","mjo_amplitude"])
    dates=st.date_input("Date range",(history.date.min().date(),history.date.max().date()))
    if len(dates)==2: history=history[history.date.between(pd.Timestamp(dates[0]),pd.Timestamp(dates[1]))]
    st.plotly_chart(px.line(history,x="date",y=chosen,title=f"{chosen} · {name}"),use_container_width=True)
    st.dataframe(history[["date",chosen]].tail(100),use_container_width=True)
elif page == "Farmer Alert":
    st.title("Farmer Alert Generator")
    st.caption("Local mock notification mode; no phone number or API credentials are collected.")
    district=st.selectbox("District",["Meerut"]); target=st.selectbox("Block",blocks,index=blocks.index(block) if block in blocks else 0); target_crop=st.selectbox("Crop",list(CROPS),index=list(CROPS).index(crop)); lang=st.selectbox("Message language",["English","हिन्दी"])
    forecast=next(r for r in records if r["block"]==target)
    sms=generate_message(district,target,target_crop,forecast,"hi" if lang=="हिन्दी" else "en","sms")
    whatsapp=generate_message(district,target,target_crop,forecast,"hi" if lang=="हिन्दी" else "en","whatsapp")
    c1,c2=st.columns(2)
    with c1: st.subheader("SMS-style message"); st.code(sms,language=None); st.download_button("Download SMS message",sms,file_name="varshasetu-alert.txt")
    with c2: st.subheader("WhatsApp-style message"); st.code(whatsapp,language=None); st.download_button("Download WhatsApp message",whatsapp,file_name="varshasetu-whatsapp.txt")
    if st.button("Generate local alert",type="primary"):
        result=MockNotificationService().send(sms); st.success("✓ Alert generated successfully"); st.write(result["message"])

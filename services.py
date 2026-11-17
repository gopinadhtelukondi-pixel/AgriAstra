"""Application service facade for weather, analysis, and grounded advice."""
import os
import logging
from data_sources.open_meteo import geocode, get_weather, fetch_climate
from data_sources.nasa_power import fetch_nasa_power
from engine.climate_analyzer import analyze_climate, compare_nasa_power
from utils.i18n import tr

CROPS=["Paddy","Cotton","Maize","Chilli","Turmeric","Groundnut","Soybean","Red gram"]
STAGES={
"Paddy":["Nursery","Establishment","Vegetative / Tillering","Panicle Initiation","Booting","Flowering","Grain Filling","Maturity"],
"Cotton":["Sowing / Emergence","Seedling","Vegetative Growth","Squaring","Flowering","Boll Development","Boll Opening","Maturity"],
"Maize":["Germination","Seedling","Vegetative Growth","Tasseling","Silking","Grain Filling","Maturity"],
"Chilli":["Nursery","Transplant Establishment","Vegetative Growth","Flowering","Fruit Development","Harvest"],
"Turmeric":["Sprouting","Vegetative Growth","Rhizome Development","Maturity"],
"Groundnut":["Germination","Vegetative Growth","Flowering","Pegging","Pod Development","Maturity"],
"Soybean":["Emergence","Vegetative Growth","Flowering","Pod Formation","Seed Filling","Maturity"],
"Red gram":["Seedling","Vegetative Growth","Flowering","Pod Development","Maturity"]}

def get_api_key():
    key=os.getenv("GEMINI_API_KEY","")
    if key:return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY","")
    except Exception:
        return ""

def grounded_advice(question,profile,analysis,weather=None,climate=None,location=None):
    key=get_api_key()
    try:
        from rag.workflow import answer_with_evidence
        location = location or profile.get("_location_context")
        return answer_with_evidence(question,profile,analysis,key,weather=weather,history=climate,location=location)
    except Exception as exc:
        logging.exception("AgriAstra evidence workflow failed")
        return (tr("I couldn't create a grounded answer just now. Please try again later or review the crop references.", profile.get("language", "English")),[])


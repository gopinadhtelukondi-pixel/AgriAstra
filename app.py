import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import date

from database import (get_crop_profile, init_db, history_frame, save_advisory,
                      register_user, save_assessment, save_crop_profile, save_simulation, saved_crop_profiles)
from auth import require_authenticated_user
from components.loading_skeletons import show_advisory_skeleton, show_weather_skeleton
from engine.simulation_engine import simulate
from utils.i18n import tr
from services import (
    CROPS, STAGES, analyze_climate, compare_nasa_power, fetch_climate,
    fetch_nasa_power, geocode, get_weather, grounded_advice,
)

st.set_page_config(page_title="AgriAstra", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")
init_db()
identity = require_authenticated_user(st)
user_id = identity["user_id"]
if st.session_state.get("authenticated_user_id") != user_id:
    # Do not carry another account's unsaved workspace when the identity changes.
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.authenticated_user_id = user_id
register_user(user_id, identity["email"], identity["display_name"])

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Noto+Sans+Telugu:wght@400;500;600;700&display=swap');
:root{--green:#245B45;--forest:#173D30;--soft:#E8F1E7;--bg:#F7F8F3;--line:#E2E8E0;--muted:#68766D}
html,body,[class*="css"]{font-family:'DM Sans','Noto Sans Devanagari','Noto Sans Telugu',sans-serif}
.stApp{background:var(--bg)}[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line);min-width:305px!important;max-width:305px!important}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2{color:var(--forest)}
[data-testid="stSidebar"] [data-testid="stRadio"] label{border-radius:10px;padding:5px 8px}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:var(--soft)}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-weight:600;color:var(--forest)}
[data-testid="stSidebar"] button{border-radius:10px}
.stButton>button{border-radius:10px;transition:transform .15s ease,box-shadow .15s ease}
.stButton>button:hover{transform:translateY(-1px);box-shadow:0 5px 14px #173d301a}
.hero{background:linear-gradient(120deg,#173D30,#2E6D4D);color:white;padding:27px 31px;border-radius:18px;margin-bottom:20px}
.hero h1{color:#fff;margin:4px 0}.hero p{color:#dce9dc;margin:0}
.card{background:#fff;border:1px solid var(--line);border-radius:15px;padding:17px;height:100%}
.label{color:var(--muted);font-size:.84rem}.value{font-size:1.5rem;font-weight:700;color:var(--forest)}
</style>
""", unsafe_allow_html=True)

PAGES = ["Overview", "Climate intelligence", "Crop profile", "Crop analysis", "AI advisor", "What-if simulator", "Assessment history"]
if "location" not in st.session_state:
    st.session_state.location = None
if "profile" not in st.session_state:
    st.session_state.profile = {"crop": "Paddy", "language": identity.get("language", "English")}

with st.sidebar:
    st.markdown("## 🌱 AgriAstra")
    language_options = ["English", "हिन्दी", "తెలుగు"]
    current_language = st.session_state.get("ui_language", st.session_state.profile.get("language", "English"))
    language = st.selectbox(tr("Language", current_language), language_options,
                            index=language_options.index(current_language), key="ui_language")
    st.session_state.profile["language"] = language
    st.caption(tr("Climate intelligence for smarter farming", language))
    st.caption(f"{tr('Signed in as', language)} {identity['display_name']}")
    if st.button(tr("Log out", language), use_container_width=True):
        st.logout()
    st.caption(tr("Workspace", language))
    selected_page = st.radio(tr("Workspace", language), PAGES, format_func=lambda name: tr(name, language), label_visibility="collapsed", key="workspace_page")
    page = selected_page
    st.divider()
    country_scope = st.selectbox(tr("Search scope", language), ["India", "All countries"], format_func=lambda item: tr(item, language), key="country_scope")
    country_code = "IN" if country_scope == "India" else None
    query = st.text_input(tr("Search village, town, city or district", language), placeholder=tr("e.g. Warangal", language))
    if st.button(tr("Find locations", language), use_container_width=True):
        if len(query.strip()) < 2:
            st.warning(tr("Enter at least two characters.", language))
        else:
            try:
                geocode_language = {"English": "en", "हिन्दी": "hi", "తెలుగు": "te"}[language]
                st.session_state.matches = geocode(query.strip(), country_code=country_code, language=geocode_language)
                if not st.session_state.matches:
                    st.info(tr("No matching locations found. Try a village, town, or district name.", language))
            except Exception as exc:
                st.session_state.matches = []
                st.error(f"{tr('Location search failed', language)}: {exc}")
    matches = st.session_state.get("matches", [])
    if matches:
        if any(item.get("geocoding_stale") for item in matches):
            st.warning(tr("Location matches are stale cached results because the geocoding API could not be reached.", language))
        choice = st.selectbox(tr("Confirm the correct location", language), [item["label"] for item in matches])
        if st.button(tr("Use selected location", language), type="primary", use_container_width=True):
            st.session_state.location = next(item for item in matches if item["label"] == choice)
            for key in ("weather", "climate", "analysis", "nasa"):
                st.session_state.pop(key, None)
            st.rerun()
    if st.session_state.location:
        st.success(st.session_state.location["label"])
    else:
        st.info(tr("Search and confirm a location to start.", language))

st.markdown(
    f'<div class="hero"><small>{tr("Climate intelligence for smarter farming", language).upper()}</small>'
    f'<h1>{tr("From weather data to smarter farming decisions", language)}</h1>'
    f'<p>{tr("Explore local forecasts, climate history, and the conditions around your crop.", language)}</p></div>',
    unsafe_allow_html=True,
)

location = st.session_state.location
profile = st.session_state.profile
crop = profile.get("crop", "Paddy")
crop_display = tr(crop, language)


def load_data(refresh=False):
    if not location:
        return None, None, None
    profile_signature = (
        location.get("label"), profile.get("crop"), profile.get("variety"), profile.get("stage"),
        str(profile.get("sowing", "")), str(profile.get("transplant", "")), profile.get("soil"),
        profile.get("drainage"), profile.get("irrigation"), profile.get("language"),
    )
    if refresh or "weather" not in st.session_state:
        placeholder = st.empty()
        show_weather_skeleton(placeholder)
        try:
            weather = get_weather(location)
            try:
                climate = fetch_climate(location, weather["daily"]["time"])
            except Exception as history_exc:
                climate = {"daily": {}, "period": "unavailable", "source": "Open-Meteo Historical Archive API",
                           "fetched_at": None, "stale": False, "error": str(history_exc)}
            analysis = analyze_climate(weather, climate)
            st.session_state.weather = weather
            st.session_state.climate = climate
            st.session_state.analysis = analysis
            save_assessment(user_id, location, profile, weather, analysis)
            st.session_state.assessment_profile_signature = profile_signature
            placeholder.empty()
            if climate.get("error"):
                st.warning(f"{tr('Historical comparison unavailable; live forecast remains available.', language)} {climate['error']}")
        except Exception as exc:
            placeholder.empty()
            st.error(f"{tr('Climate data is unavailable', language)}: {exc}")
    if st.session_state.get("weather") and st.session_state.get("analysis") and st.session_state.get("assessment_profile_signature") != profile_signature:
        save_assessment(user_id, location, profile, st.session_state.weather, st.session_state.analysis)
        st.session_state.assessment_profile_signature = profile_signature
    return (
        st.session_state.get("weather"),
        st.session_state.get("climate"),
        st.session_state.get("analysis"),
    )


def show_metrics(analysis):
    if not analysis:
        st.warning(tr("Climate indicators are unavailable because the required data is incomplete.", language))
        return
    baseline_text = analysis.get("baseline_text", "")
    prefix = "ERA5 comparable-period baseline: "
    if baseline_text.startswith(prefix):
        baseline_text = f"{tr('ERA5 comparable-period baseline', language)}: {baseline_text.removeprefix(prefix)}"
    cards = st.columns(4)
    values = [
        (tr("7-day rainfall", language), f"{analysis['forecast_rain']:.1f} mm" if analysis["forecast_rain"] is not None else tr("Unavailable", language), tr("Forecast", language)),
        (tr("Rainfall comparison", language), tr(analysis["rain_text"], language), tr(baseline_text, language)),
        (tr("Mean temperature", language), f"{analysis['forecast_temp']:.1f} °C" if analysis["forecast_temp"] is not None else tr("Unavailable", language), tr("Forecast period", language)),
        (tr("Temperature comparison", language), tr(analysis["temp_text"], language), tr("Compared with ERA5", language)),
    ]
    for col, (label, value, note) in zip(cards, values):
        col.markdown(
            f'<div class="card"><div class="label">{label}</div>'
            f'<div class="value">{value}</div><div class="label">{note}</div></div>',
            unsafe_allow_html=True,
        )
    days_covered = analysis.get("historical_days_available", 0)
    total_days = len(st.session_state.get("weather", {}).get("daily", {}).get("time") or [])
    st.caption(f"{tr('Historical climate is a model estimate, not a station measurement.', language)} {tr('Coverage of comparable days', language)}: {days_covered}/{total_days} {tr('days', language)}.")
    if analysis.get("forecast_stale"):
        st.warning(tr("The forecast shown is stale cached data, not live. Check the retrieval time before using it.", language))
    if analysis.get("history_stale"):
        st.warning(tr("Historical comparison is from stale cached data.", language))


if page == "Crop profile":
    st.header(tr("Crop profile", language))
    st.write(tr("Growth stages update with the selected crop. Custom crops receive no inferred crop-specific thresholds.", language))
    existing_profiles = saved_crop_profiles(user_id)
    if existing_profiles:
        saved = st.selectbox(tr("Load a saved crop profile", language), existing_profiles, format_func=lambda row: f"{tr(row['profile_name'].split(' · ')[0], language)} · #{row['profile_id']}")
        if st.button(tr("Load selected profile", language)):
            st.session_state.profile = get_crop_profile(user_id, saved["profile_id"])
            st.rerun()
    old = profile
    with st.form("crop_profile"):
        crop_names = CROPS + ["Other / custom"]
        selected = st.selectbox(tr("Crop", language), crop_names, format_func=lambda name: tr(name, language), index=crop_names.index(old["crop"]) if old.get("crop") in crop_names else len(crop_names)-1)
        custom = st.text_input(tr("Custom crop name", language), value=old.get("custom", ""), disabled=selected != "Other / custom")
        actual_crop = custom.strip() if selected == "Other / custom" and custom.strip() else selected
        variety = st.text_input(tr("Variety (optional)", language), value=old.get("variety", ""))
        stages = STAGES.get(actual_crop, [])
        stage_options = stages or ["Not specified"]
        stage = st.selectbox(tr("Growth stage", language), stage_options, format_func=lambda name: tr(name, language), index=stage_options.index(old["stage"]) if old.get("stage") in stage_options else 0)
        c1, c2 = st.columns(2)
        sowing = c1.date_input(tr("Sowing date", language), value=old.get("sowing", date.today()))
        transplant = c2.date_input(tr("Transplanting date (optional)", language), value=old.get("transplant", date.today()))
        soil_values = ["Not specified", "Clay", "Loam", "Sandy", "Silt", "Black soil", "Red soil", "Other"]
        soil = st.selectbox(tr("Soil type", language), soil_values, format_func=lambda name: tr(name, language), index=soil_values.index(old.get("soil", "Not specified")))
        c1, c2 = st.columns(2)
        drainage_values = ["Not specified", "Good", "Moderate", "Poor"]
        irrigation_values = ["Not specified", "Available", "Limited", "Rain-fed"]
        drainage = c1.selectbox(tr("Drainage", language), drainage_values, format_func=lambda name: tr(name, language), index=drainage_values.index(old.get("drainage", "Not specified")))
        irrigation = c2.selectbox(tr("Irrigation", language), irrigation_values, format_func=lambda name: tr(name, language), index=irrigation_values.index(old.get("irrigation", "Not specified")))
        submitted = st.form_submit_button(tr("Save crop profile", language), type="primary")
    if submitted:
        new_profile = {
            "crop": actual_crop, "custom": custom, "variety": variety, "stage": stage,
            "sowing": sowing, "transplant": transplant, "soil": soil,
            "drainage": drainage, "irrigation": irrigation, "language": language,
        }
        save_crop_profile(user_id, f"{actual_crop} · {variety or 'profile'}", new_profile)
        st.session_state.profile = new_profile
        st.success(tr("Crop profile saved.", language))
        st.rerun()

elif page == "Assessment history":
    st.header(tr("Assessment history", language))
    history = history_frame(user_id)
    if history.empty:
        st.info(tr("No saved assessments, advisories, or simulations yet.", language))
    else:
        history_display = history.rename(columns={
            "timestamp": tr("Timestamp", language), "type": tr("Type", language), "location": tr("Location", language),
            "crop": tr("Crop", language), "growth_stage": tr("Growth stage", language),
            "forecast_rain_mm": f"{tr('7-day rainfall', language)} (mm)", "mean_temp_c": f"{tr('Mean temperature', language)} (°C)",
            "rainfall_comparison": tr("Rainfall comparison", language), "temperature_comparison": tr("Temperature comparison", language),
            "question": tr("Question", language), "response": tr("Response", language), "sources": tr("Sources", language),
        })
        history_display[tr("Type", language)] = history_display[tr("Type", language)].map({
            "Assessment": tr("Assessment", language), "AI advisory": tr("AI advisory", language),
            "Simulation (hypothetical)": tr("Simulation (hypothetical)", language),
        }).fillna(history_display[tr("Type", language)])
        st.dataframe(history_display, use_container_width=True, hide_index=True)
        st.download_button(
            tr("Download history as CSV", language), history_display.to_csv(index=False),
            file_name="agriaastra_history.csv", mime="text/csv",
        )

elif page == "AI advisor":
    st.header(tr("AI agricultural advisor", language))
    st.write(tr("The advisor uses crop-specific references, explains the weather in plain language, and cites its sources.", language))
    from rag import retriever
    # Read the configured persistent-store path directly. This also tolerates
    # an already-running Streamlit process that cached an older retriever module
    # before the has_index helper was added.
    if not (retriever.VECTOR_DIR / "chroma.sqlite3").is_file():
        st.info(tr("The semantic vector index is not built yet. Bundled verified text guides can still be used. To add more sources, place official PDFs or text guides in rag/documents, add their details and crop tags to manifest.json, then run python -m rag.ingest from the project folder.", language))
    with st.expander(tr("Example question and answer", language), expanded=False):
        st.caption(tr("This is a language and format example, not crop-specific advice.", language))
        st.markdown(f"**{tr('Example question', language)}:** {tr('What should I check when rain is forecast for my paddy field?', language)}")
        sample = "Illustrative answer: Check the local 7-day forecast and your field's drainage before making a decision. This is a sample format, not crop-specific advice; actual guidance should use verified local sources."
        st.markdown(f"**{tr('Example response', language)}:** {tr(sample, language)}")
    question = st.text_area(tr("Ask a question in your language", language), placeholder=tr("What should I check when rain is forecast for my paddy field?", language))
    if st.button(tr("Get evidence-based answer", language), type="primary"):
        if not location:
            st.warning(tr("Select a location first.", language))
        elif not question.strip():
            st.warning(tr("Enter a question.", language))
        else:
            weather, climate, analysis = load_data()
            answer_placeholder = st.empty()
            show_advisory_skeleton(answer_placeholder)
            with st.spinner(tr("Checking crop references and preparing your answer…", language)):
                advisor_profile = {**profile, "_location_context": location}
                answer, sources = grounded_advice(question, advisor_profile, analysis, weather=weather, climate=climate)
            answer_placeholder.empty()
            save_advisory(user_id, location, profile, question, answer, sources)
            st.subheader(tr("Response", language))
            st.write(answer)
            if sources:
                st.markdown(f"**{tr('Retrieved references', language)}**")
                for source in sources:
                    st.caption(source)

elif page == "What-if simulator":
    st.header(tr("What-if climate simulator", language))
    st.write(tr("Compare hypothetical values with the live forecast. The simulation never edits weather data.", language))
    if not location:
        st.info(tr("Select a location first.", language))
    else:
        weather, climate, analysis = load_data()
        if analysis and analysis.get("forecast_rain") is not None and analysis.get("forecast_temp") is not None:
            base_rain = float(analysis["forecast_rain"])
            base_temp = float(analysis["forecast_temp"])
            c1, c2 = st.columns(2)
            rain = c1.number_input(tr("Hypothetical 7-day rainfall (mm)", language), 0.0, 2000.0, base_rain, 5.0)
            temp = c2.number_input(tr("Hypothetical mean temperature (°C)", language), -20.0, 60.0, base_temp, 1.0)
            result = simulate(
                base_rain, base_temp, rain, temp,
                rainfall_baseline_mm=analysis.get("baseline_rain"),
                temperature_baseline_c=analysis.get("historical_temp"),
            )
            st.subheader(tr("Forecast and scenario", language))
            c1, c2 = st.columns(2)
            c1.metric(tr("Forecast rainfall", language), f"{base_rain:.1f} mm", tr("Forecast", language))
            c2.metric(tr("Hypothetical rainfall", language), f"{rain:.1f} mm", f"{result['rainfall_change_mm']:+.1f} mm")
            c1, c2 = st.columns(2)
            c1.metric(tr("Forecast mean temperature", language), f"{base_temp:.1f} °C", tr("Forecast", language))
            c2.metric(tr("Hypothetical mean temperature", language), f"{temp:.1f} °C", f"{result['temperature_change_c']:+.1f} °C")
            rain_comparison = result["rainfall_baseline_comparison"]
            if rain_comparison["forecast"] and rain_comparison["hypothetical"]:
                suffix = "%" if rain_comparison["forecast"]["kind"] == "percent" else " mm"
                st.caption(
                    f"{tr('Compared with the ERA5 calendar-period baseline: forecast', language)} "
                    f"{rain_comparison['forecast']['value']:+.1f}{suffix}; {tr('hypothetical', language)} "
                    f"{rain_comparison['hypothetical']['value']:+.1f}{suffix}."
                )
            temp_comparison = result["temperature_baseline_difference_c"]
            if temp_comparison["forecast"] is not None and temp_comparison["hypothetical"] is not None:
                st.caption(
                    f"{tr('Compared with the ERA5 temperature baseline: forecast', language)} {temp_comparison['forecast']:+.1f} °C; "
                    f"{tr('hypothetical', language)} {temp_comparison['hypothetical']:+.1f} °C."
                )
            st.info(tr("This is a descriptive scenario. It does not predict crop damage, yield, or response.", language))
            if st.button(tr("Save simulation", language)):
                save_simulation(user_id, location, profile, base_rain, base_temp, rain, temp, result)
                st.success(tr("Saved simulation.", language))
        else:
            st.warning(tr("A complete live forecast assessment is required before comparing a scenario.", language))

elif page == "Overview":
    st.header(tr("Farm snapshot", language))
    if not location:
        st.info(tr("Search for a village, town, city, or district in the sidebar and confirm the matching result.", language))
    else:
        st.write(f"**{location['label']}** · {crop_display} · {tr(profile.get('stage', 'stage not specified'), language)}")
        if st.button(tr("Refresh weather and climate data", language)):
            load_data(refresh=True)
        weather, climate, analysis = load_data()
        if weather:
            current = weather.get("current", {})
            if current:
                st.subheader(tr("Current conditions", language))
                current_cards = st.columns(4)
                current_metrics = [
                    ("Temperature", current.get("temperature_2m"), "°C"),
                    ("Relative humidity", current.get("relative_humidity_2m"), "%"),
                    ("Precipitation", current.get("precipitation"), "mm"),
                    ("Wind speed", current.get("wind_speed_10m"), "km/h"),
                ]
                for col, (label, value, unit) in zip(current_cards, current_metrics):
                    col.metric(label, f"{value:g} {unit}" if isinstance(value, (int, float)) else tr("Unavailable", language))
                st.caption(f"{tr('Current conditions timestamp', language)}: {current.get('time', tr('not provided', language))} {weather.get('timezone', '')}")
            show_metrics(analysis)
            forecast = pd.DataFrame(weather["daily"])
            st.subheader(tr("Next seven days", language))
            st.plotly_chart(
                px.bar(forecast, x="time", y="precipitation_sum",
                       labels={"time": tr("Date", language), "precipitation_sum": f"{tr('Rainfall', language)} (mm)"},
                       color_discrete_sequence=["#78A66A"]),
                use_container_width=True,
            )
            st.caption(f"{weather['source']} · {tr('Retrieved', language)} {weather['fetched_at']} · {tr('Units', language)}: mm, °C, km/h")
            st.caption(f"{tr('Forecast freshness', language)}: {tr(weather['freshness'], language)}")
            st.caption(
                f"{tr('Crop', language)}: {crop_display}; {tr('Variety', language)}: {profile.get('variety') or tr('Not specified', language)}; "
                f"{tr('soil', language)}: {tr(profile.get('soil', 'Not specified'), language)}; {tr('drainage', language)}: {tr(profile.get('drainage', 'Not specified'), language)}; "
                f"{tr('irrigation', language)}: {tr(profile.get('irrigation', 'Not specified'), language)}."
            )
    st.subheader(tr("Start here", language))
    cards = st.columns(3)
    for col, number, title, description in zip(
        cards, ["01", "02", "03"],
        [tr("Choose a place", language), tr("Add crop context", language), tr("Explore conditions", language)],
        [tr("Confirm the exact location.", language), tr("Choose crop, growth stage, soil, and field conditions.", language), tr("Compare forecast and historical climate, then simulate a scenario.", language)],
    ):
        col.markdown(
            f'<div class="card"><small>{number}</small><h3>{title}</h3>'
            f'<div class="label">{description}</div></div>',
            unsafe_allow_html=True,
        )

else:
    st.header(tr(page, language))
    if not location:
        st.info(tr("Select a location first.", language))
    else:
        weather, climate, analysis = load_data()
        if weather and analysis:
            show_metrics(analysis)
            if page == "Climate intelligence":
                forecast = pd.DataFrame(weather["daily"])
                st.subheader(tr("Forecast · next seven days", language))
                st.plotly_chart(
                    px.line(forecast, x="time", y=["temperature_2m_max", "temperature_2m_min"],
                            markers=True, labels={"time": tr("Date", language), "value": f"{tr('Temperature', language)} (°C)", "variable": tr("Series", language),
                                              "temperature_2m_max": tr("Maximum temperature", language), "temperature_2m_min": tr("Minimum temperature", language)},
                            color_discrete_sequence=["#D99A32", "#245B45"]),
                    use_container_width=True,
                )
                st.plotly_chart(
                    px.bar(forecast, x="time", y="precipitation_sum",
                           labels={"time": tr("Date", language), "precipitation_sum": f"{tr('Rainfall', language)} (mm)"},
                           color_discrete_sequence=["#78A66A"]),
                    use_container_width=True,
                )
                if climate and climate.get("daily", {}).get("time"):
                    st.subheader(tr("Historical reanalysis · ERA5", language))
                    st.caption(
                f"{climate['source']} · {climate['period']} · {tr('Retrieved', language)} {climate['fetched_at']}"
                + (f" · {tr('stale cache', language)}" if climate.get("stale") else (f" · {tr('recent cache', language)}" if climate.get("cached") else ""))
                    )
                    climate_table = pd.DataFrame(climate["daily"]).rename(columns={
                        "time": tr("Date", language), "precipitation_sum": f"{tr('Rainfall', language)} (mm)",
                        "temperature_2m_max": f"{tr('Maximum temperature', language)} (°C)",
                        "temperature_2m_min": f"{tr('Minimum temperature', language)} (°C)",
                    })
                    st.dataframe(climate_table, use_container_width=True, hide_index=True)
                if st.checkbox(tr("Optional independent NASA POWER cross-check", language)):
                    try:
                        with st.spinner(tr("Retrieving NASA POWER data…", language)):
                            nasa = fetch_nasa_power(location, weather["daily"]["time"])
                            st.session_state.nasa = nasa
                            cross = compare_nasa_power(nasa, weather["daily"]["time"])
                        st.subheader(tr("NASA POWER · separate historical dataset", language))
                        st.caption(
                            f"{nasa['source']} · {nasa['period']} · {tr('Retrieved', language)} {nasa['fetched_at']}"
                            + (f" · {tr('stale cache', language)}" if nasa.get("stale") else (f" · {tr('recent cache', language)}" if nasa.get("cached") else ""))
                        )
                        n1, n2, n3 = st.columns(3)
                        n1.metric(tr("Comparable rainfall baseline", language), f"{cross['rainfall_baseline_mm']:.1f} mm" if cross["rainfall_baseline_mm"] is not None else tr("Unavailable", language))
                        n2.metric(tr("Comparable mean temperature", language), f"{cross['temperature_baseline_c']:.1f} °C" if cross["temperature_baseline_c"] is not None else tr("Unavailable", language))
                        n3.metric(tr("Calendar-day coverage", language), f"{cross['coverage']:.0%}")
                        st.info(tr("NASA POWER uses a different product, grid, and UTC day definition. Its values are shown separately and are not combined with ERA5.", language))
                    except Exception as exc:
                        st.warning(f"{tr('NASA POWER cross-check unavailable', language)}: {exc}")
            else:
                if analysis["forecast_rain"] is None or analysis["forecast_temp"] is None:
                    st.warning(tr("Forecast contains missing daily values; a complete-period crop exposure summary cannot be calculated.", language))
                    st.stop()
                stage = profile.get("stage", "unspecified stage")
                st.subheader(tr("Interpreting this exposure", language))
                st.write(
                    f"{tr('Forecast summary', language)} **{crop_display} · {tr(stage, language)}**: "
                    f"{tr('7-day rainfall', language)} {analysis['forecast_rain']:.1f} mm; "
                    f"{tr('Mean temperature', language)} {analysis['forecast_temp']:.1f} °C. "
                    f"{tr('Rainfall comparison', language)}: {tr(analysis['rain_text'], language)}. "
                    f"{tr('Temperature comparison', language)}: {tr(analysis['temp_text'], language)}."
                )
                st.info(tr("These are transparent climate exposure indicators, not a validated crop-risk score, crop-loss prediction, or yield estimate. No crop thresholds are enabled until reviewed sources are indexed.", language))
                st.caption(
                    f"{tr('Field context on profile', language)}: {tr('soil', language)} {tr(profile.get('soil', 'Not specified'), language)}, "
                    f"{tr('drainage', language)} {tr(profile.get('drainage', 'Not specified'), language)}, "
                    f"{tr('irrigation', language)} {tr(profile.get('irrigation', 'Not specified'), language)}. "
                    f"{tr('These conditions are recorded for context; no unvalidated soil or crop weighting is applied.', language)}"
                )
                if crop not in CROPS:
                    st.warning(tr("This custom crop has no reviewed crop-specific profile; only general weather context is shown.", language))
                st.caption(tr("Forecasts and ERA5 reanalysis are separate model products. Reanalysis is not an exact ground-station record.", language))

st.caption(tr("AgriAstra is decision support. Confirm critical farm decisions with local agricultural experts.", language))


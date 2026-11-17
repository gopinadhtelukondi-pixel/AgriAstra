AgriAstra — Project Specification Sheet
Project Name: AgriAstra
Tagline: Turning Climate Intelligence into Smarter Farming Decisions
Hackathon Track: Track 2 — Climate, Resource Infrastructure & Global Supply Resilience
Project Type: Climate Intelligence and Multi-Crop Agricultural Decision Support Platform
Initial Budget: ₹0
Development Framework: Python + Streamlit

1. Project Overview
AgriAstra is a location-independent, multi-crop climate intelligence platform designed to help farmers understand changing weather conditions and make informed agricultural decisions.
The platform connects live weather information, historical climate data, farmer-provided crop details and trusted agricultural knowledge.
Unlike ordinary weather applications, AgriAstra considers:
Farmer-selected location.
Selected crop.
Crop growth stage.
Soil type.
Drainage conditions.
Irrigation availability.
Weather and historical climate patterns.
Based on these inputs, AgriAstra generates transparent climate analysis and evidence-backed agricultural guidance.
The platform is not restricted to a particular district, state or crop.
Core workflow
Farmer Location → Live Weather Data → Historical Climate Comparison → Crop Selection → Crop Context → Climate Exposure Analysis → AI Agricultural Guidance → What-If Simulation

2. Main Objectives
Fetch live weather information for user-selected locations.
Compare upcoming weather with historical climate patterns.
Identify unusual rainfall and temperature conditions.
Support multiple agricultural crops.
Adapt crop analysis according to growth stages and field conditions.
Provide transparent and explainable climate exposure indicators.
Generate agricultural guidance using trusted documents.
Support Telugu and English.
Allow farmers to explore hypothetical weather scenarios.
Maintain assessment and advisory history.

3. Target Users
Small and medium-scale farmers.
Farmers cultivating different crops.
Agricultural students and researchers.
Agricultural advisors.
Farmers interested in climate-aware agriculture.
The interface should be simple enough for farmers with limited technical knowledge.

4. Dynamic Location System
AgriAstra must not be restricted to any predefined location.
Location input
Farmers can enter:
Village.
Town.
City.
District.
Region.
Location resolution workflow
Farmer enters a location.
Application sends the location to the geocoding API.
API returns matching locations and coordinates.
Farmer selects the correct location.
Application stores the selected location and coordinates.
Weather and historical climate APIs use these coordinates.
Requirements
Support different locations wherever data-provider coverage is available.
Display matching location names and administrative regions.
Allow users to change locations.
Handle ambiguous location names.
Never silently select an uncertain location.
Never hardcode one location as the only supported option.

5. Multi-Crop Support
AgriAstra must support different agricultural crops rather than focusing on only one crop.
Initial crop catalogue
The initial application should include:
Paddy.
Cotton.
Maize.
Chilli.
Turmeric.
Groundnut.
Soybean.
Red gram.
Other crops through a custom crop-name input.
The crop catalogue should be expandable without redesigning the entire application.
Dynamic crop profile
The crop profile should adapt to the selected crop.
Field
Description
Location
Farmer-selected location
Crop
Selected crop
Variety
Optional crop variety
Sowing Date
Date of sowing
Transplanting Date
Optional, where applicable
Growth Stage
Crop-specific growth stage
Soil Type
Farmer-selected soil type
Drainage
Good, moderate or poor
Irrigation
Irrigation availability
Language
Telugu or English

Crop growth stages
Growth stages must depend on the selected crop.
For example:
Paddy
Nursery.
Establishment.
Vegetative / Tillering.
Panicle Initiation.
Booting.
Flowering.
Grain Filling.
Maturity.
Cotton
Sowing / Emergence.
Seedling.
Vegetative Growth.
Squaring.
Flowering.
Boll Development.
Boll Opening.
Maturity.
Maize
Germination.
Seedling.
Vegetative Growth.
Tasseling.
Silking.
Grain Filling.
Maturity.
These are initial examples, not a fixed list for every crop or variety. Crop-specific stages should be reviewed against authoritative agricultural references.
Important crop-support rule
Do not apply paddy-specific thresholds or recommendations to cotton, maize or other crops.
Every crop must have its own evidence-backed guidance and applicable growth stages.
If reliable information is unavailable for a selected crop, AgriAstra should clearly communicate that limitation rather than generate unsupported advice.

6. Technology Stack
Component
Technology
Programming Language
Python 3.11
Frontend
Streamlit
Data Processing
Pandas, NumPy
Charts
Plotly
API Requests
Requests
Geocoding
Open-Meteo Geocoding API
Weather Forecast
Open-Meteo Forecast API
Historical Climate
Open-Meteo Historical Archive API
Historical Cross-Check
NASA POWER Daily API
LLM
Gemini Flash
Agent Workflow
LangGraph
LLM Integration
LangChain
Vector Database
ChromaDB
Embeddings
Hugging Face Sentence Transformers
PDF Processing
PyPDF
Database
SQLite
Testing
Pytest
Deployment
Streamlit Community Cloud
Version Control
Git and GitHub

Use only necessary dependencies. Keep the code modular, straightforward and understandable.

7. Live API Integration
All weather and climate data must come from real API responses.
No fabricated weather values or hardcoded sample observations are allowed.
A. Open-Meteo Geocoding API
Purpose: Convert a location name into geographic coordinates.
Endpoint:
https://geocoding-api.open-meteo.com/v1/search
Expected information:
Location name.
Administrative region.
Country.
Latitude.
Longitude.
Timezone.
B. Open-Meteo Forecast API
Purpose: Retrieve current weather and upcoming forecasts.
Endpoint:
https://api.open-meteo.com/v1/forecast
Required daily variables:
temperature_2m_max.
temperature_2m_min.
precipitation_sum.
precipitation_probability_max.
wind_speed_10m_max.
Optional variables:
weather_code.
Current temperature.
Current precipitation.
Relative humidity.
Requirements:
Seven-day forecast.
Selected location coordinates.
Appropriate local timezone.
C. Open-Meteo Historical Archive API
Purpose: Retrieve historical weather information.
Endpoint:
https://archive-api.open-meteo.com/v1/archive
Required variables:
Daily maximum temperature.
Daily minimum temperature.
Daily precipitation.
Use comparable calendar periods and consistent datasets for meaningful historical comparisons.
Historical reanalysis must not be represented as exact ground-station measurements.
D. NASA POWER Daily API
Purpose: Provide an optional independent historical data cross-check.
Endpoint:
https://power.larc.nasa.gov/api/temporal/daily/point
Use it when its available parameters, spatial resolution and data coverage are appropriate.
Do not combine incompatible datasets without explaining their differences.
API reliability requirements
Display the source of each important dataset.
Show retrieval timestamps.
Show units.
Show forecast dates and historical periods.
Handle timeouts and API failures.
Cache successful responses with an explicit freshness policy.
Mark cached information as stale.
Never display stale data as live.
Never replace missing API values with fabricated values.
Clearly communicate when data is unavailable.

8. Core Application Modules
Module 1: Home Dashboard
Purpose: Provide an overview of the selected location, weather and crop.
Features:
Dynamic location selection.
Selected crop overview.
Current weather.
Seven-day forecast.
Rainfall summary.
Temperature summary.
Historical climate comparison.
Climate exposure indicators.
Crop profile summary.
Latest assessment.
Latest advisory.
Data freshness indicators.
Module 2: Climate Intelligence
Purpose: Understand local weather and historical climate patterns.
Features:
Daily rainfall chart.
Maximum and minimum temperature charts.
Seven-day forecast.
Historical rainfall comparison.
Historical temperature comparison.
Rainfall anomaly.
Temperature anomaly.
Unusual weather pattern indicators.
The application must distinguish between forecast data and historical reanalysis.
Module 3: Crop Profile
Purpose: Understand the farmer's crop and field conditions.
Features:
Dynamic crop selection.
Crop variety input.
Sowing date.
Transplanting date where applicable.
Crop-specific growth stages.
Soil type.
Drainage conditions.
Irrigation availability.
Selected language.
The growth-stage options must update according to the selected crop.
Module 4: Crop Risk and Exposure Analysis
Purpose: Understand how weather conditions may affect the selected crop.
Initial analysis factors:
Rainfall exposure.
Temperature exposure.
Soil and drainage context.
Crop growth-stage context.
Features:
Crop-specific weather indicators.
Unusual rainfall explanations.
Unusual temperature explanations.
Factors requiring attention.
Supporting agricultural evidence.
Data quality and uncertainty.
Clear explanations for displayed indicators.
Scientific reliability requirements
Do not invent:
Scientific thresholds.
Arbitrary risk weights.
Risk percentages.
Crop-loss predictions.
Yield predictions.
Use crop-specific thresholds only when supported by authoritative agricultural sources.
Until suitable evidence and validation are available, display transparent climate exposure indicators instead of presenting an unvalidated risk score as scientific fact.
Module 5: AI Agricultural Advisor
Purpose: Allow farmers to ask agricultural questions in natural language.
Supported languages:
Telugu.
English.
Example questions:
Will the upcoming rainfall affect my crop?
What should I consider during the flowering stage?
Why is the rainfall different from the historical average?
What weather conditions should I monitor during grain filling?
How should I interpret the current temperature conditions?
The AI advisor receives:
Selected location.
Selected crop.
Crop variety, if provided.
Growth stage.
Soil and drainage information.
Live weather forecast.
Historical climate comparison.
Python-generated climate analysis.
Retrieved agricultural documents.
It provides:
Simple explanations.
Crop-specific guidance.
Supporting references.
Relevant uncertainty statements.
The LLM must not independently invent weather values, calculate risk scores or fabricate agricultural recommendations.
Module 6: What-If Climate Simulator
Purpose: Allow farmers to explore hypothetical weather scenarios.
Inputs:
Hypothetical rainfall.
Hypothetical temperature.
Selected crop.
Growth stage.
Relevant field conditions.
Features:
Compare original conditions with simulated conditions.
Display changes in climate indicators.
Explain the differences.
Mark simulated values as hypothetical.
The simulator must not modify actual live forecasts.
Use crop-specific rules only when reliable supporting evidence is available.
Module 7: Assessment History
Purpose: Maintain previous farmer assessments.
Features:
Saved crop profiles.
Previous climate assessments.
Weather snapshots.
AI advisory history.
Simulation history.
Assessment timestamps.

9. AI and RAG Architecture
AgriAstra will use one understandable LangGraph workflow rather than a complex multi-agent system.
Agricultural knowledge sources
Priority sources:
ICAR publications.
Agricultural university publications.
PJTSAU publications.
State Agriculture Department publications.
Other verified agricultural research and extension publications.
The knowledge base should gradually expand to cover all supported crops.
Document ingestion workflow
PDF Documents → PyPDF Extraction → Text Splitting → Hugging Face Embeddings → ChromaDB
Initial text-splitting configuration:
Chunk size: 1000.
Chunk overlap: 200.
Store metadata:
Document title.
Issuing organization.
Crop category.
Page number.
Source URL where available.
Publication date where available.
LangGraph workflow
Receive farmer's question.
Read the selected location and crop profile.
Receive Python-generated climate analysis.
Retrieve relevant crop-specific agricultural documents.
Check whether sufficient evidence is available.
Generate a grounded answer using Gemini.
Return the answer with citations and uncertainty.
AI safety requirements
Never invent citations.
Do not use one crop's advice for another crop.
Do not provide unsupported pesticide or chemical-treatment instructions.
Do not diagnose diseases based only on weather information.
Do not guarantee yield improvements.
State when reliable crop-specific evidence is unavailable.
Keep answers simple and farmer-friendly.
Respond in the selected language.

10. Climate Analysis and Calculation Rules
All numerical calculations must be performed in Python.
Rainfall anomaly
When a suitable historical baseline exists:
Rainfall Anomaly (%) = ((Forecast Rainfall - Historical Baseline) / Historical Baseline) × 100
If the baseline is zero or too small for a meaningful percentage, show the absolute difference instead.
Temperature anomaly
Temperature Anomaly = Forecast Temperature - Comparable Historical Temperature Baseline
Comparisons must use appropriate calendar periods and consistent datasets.
Data quality
Every assessment should consider:
Data availability.
Source reliability.
Historical coverage.
Forecast period.
Missing values.
Dataset comparability.
Uncertainty.
The application must communicate uncertainty rather than hide it.

11. User Interface and Design
AgriAstra should look like a polished agricultural technology product, not a default Streamlit demonstration.
Color palette
Purpose
Color
Primary Green
#245B45
Deep Forest
#173D30
Secondary Green
#78A66A
Light Green
#E8F1E7
Background
#F7F8F3
White Cards
#FFFFFF
Main Text
#24332B
Secondary Text
#68766D
Warning Amber
#D99A32
Critical Red
#B94A48
Border
#E2E8E0

Design requirements
Clean sidebar navigation.
Modern dashboard cards.
Well-organized charts.
Consistent spacing.
Responsive desktop and mobile layout.
Readable typography.
Telugu-compatible fonts such as Noto Sans Telugu.
Clear labels and units.
Good contrast and accessibility.
Consistent crop-selection experience.
Loading states
Implement attractive skeleton loading states for:
Weather cards.
Forecast charts.
Historical comparisons.
Crop analysis.
AI advisory responses.
Use Streamlit placeholders and lightweight CSS.
Skeletons should appear only during actual loading. If an API request fails, display a clear error state.
Accessibility
Telugu and English.
Simple language.
Mobile-friendly layout.
Keyboard-friendly navigation.
Do not use color as the only way to communicate risk.
No login requirement for the initial MVP.

12. Database Design
Use SQLite for structured application data.
farmer_profiles
farmer_id.
location.
latitude.
longitude.
crop.
crop_variety.
sowing_date.
transplanting_date.
growth_stage.
soil_type.
drainage.
irrigation.
language.
created_at.
weather_snapshots
weather_id.
farmer_id.
source.
forecast_date.
rainfall_mm.
min_temp.
max_temp.
fetched_at.
risk_assessments
assessment_id.
farmer_id.
indicators.
factors.
explanation.
data_quality.
created_at.
advisories
advisory_id.
assessment_id.
question.
language.
response.
sources.
created_at.
simulation_runs
simulation_id.
farmer_id.
crop.
rainfall_mm.
temperature_c.
original_assessment.
simulated_assessment.
created_at.
Use parameterized SQL queries and foreign keys.
Keep personal information minimal. Farmer names should be optional.
ChromaDB will separately store agricultural document chunks and metadata.

13. Project Folder Structure
AgriAstra/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── .streamlit/
│   └── config.toml
│
├── pages/
│   ├── 1_Climate_Intelligence.py
│   ├── 2_Crop_Profile.py
│   ├── 3_Crop_Analysis.py
│   ├── 4_AI_Advisor.py
│   ├── 5_What_If_Simulator.py
│   └── 6_Assessment_History.py
│
├── components/
│   ├── sidebar.py
│   ├── metric_cards.py
│   ├── weather_charts.py
│   ├── loading_skeletons.py
│   └── risk_visualization.py
│
├── data_sources/
│   ├── geocoding.py
│   ├── open_meteo.py
│   └── nasa_power.py
│
├── services/
│   ├── weather_service.py
│   ├── climate_service.py
│   ├── crop_service.py
│   └── advisory_service.py
│
├── engine/
│   ├── climate_analyzer.py
│   ├── risk_engine.py
│   └── simulation_engine.py
│
├── ai/
│   ├── workflow.py
│   ├── state.py
│   └── prompts.py
│
├── rag/
│   ├── ingest.py
│   ├── retriever.py
│   └── documents/
│
├── database/
│   ├── db.py
│   ├── schema.sql
│   └── repository.py
│
├── utils/
│   ├── config.py
│   ├── constants.py
│   └── validators.py
│
├── data/
│   ├── cache/
│   └── agri_astra.db
│
└── tests/
    ├── test_geocoding.py
    ├── test_weather.py
    ├── test_climate.py
    ├── test_crop_service.py
    ├── test_risk_engine.py
    └── test_simulation.py

14. Development Phases
Phase 1 — Project Foundation
Create project structure.
Configure Streamlit theme.
Create navigation.
Implement dynamic location search.
Resolve location into coordinates.
Implement crop selection.
Build dynamic crop profile.
Add crop-specific growth stages.
Phase 2 — Live Climate Intelligence
Connect Open-Meteo Forecast API.
Connect Historical Archive API.
Implement data validation.
Display live forecast.
Display historical comparisons.
Implement climate anomaly calculations.
Phase 3 — Crop Context and Analysis
Implement multi-crop support.
Add crop-specific profiles.
Add soil and drainage context.
Build transparent climate exposure indicators.
Add source-backed explanations.
Handle unavailable crop-specific evidence.
Phase 4 — RAG and AI Advisor
Collect authoritative agricultural documents.
Organize documents by crop.
Extract and process PDFs.
Generate embeddings.
Store chunks in ChromaDB.
Implement crop-aware retrieval.
Build LangGraph workflow.
Integrate Gemini.
Add Telugu and English responses with citations.
Phase 5 — Simulator and History
Build what-if simulator.
Implement SQLite storage.
Save assessments.
Save advisory history.
Save simulations.
Phase 6 — Testing and Deployment
Test different locations.
Test different crops.
Test crop-specific growth stages.
Test API failures.
Test missing and inconsistent data.
Test numerical calculations.
Test Telugu interface.
Improve mobile responsiveness.
Finalize README.
Deploy on Streamlit Community Cloud.
Prepare hackathon demonstration.

 Technology Stack
AgriAstra will use Python and Streamlit as its primary development stack. The architecture will remain modular, lightweight and understandable, while supporting live API integration, multi-crop analysis, RAG and AI-powered agricultural guidance.
A. Frontend
Technology
Purpose
Streamlit
Main web application and user interface
HTML
Custom UI structure where required
CSS
Styling, dashboard design, loading skeletons and responsiveness
Plotly
Interactive weather and climate charts

B. Backend and Programming
Technology
Purpose
Python 3.11
Primary programming language
Pandas
Weather data processing and analysis
NumPy
Numerical and climate calculations
Requests
Communication with external APIs
SQLite
Store farmer profiles, assessments and history

C. Live Data and External APIs
API
Purpose
Open-Meteo Geocoding API
Convert user-entered locations into coordinates
Open-Meteo Forecast API
Retrieve live weather conditions and forecasts
Open-Meteo Historical Archive API
Retrieve historical weather and climate data
NASA POWER Daily API
Optional independent historical data cross-check

D. AI and Agent Workflow
Technology
Purpose
Gemini Flash
Generate farmer-friendly agricultural explanations
LangChain
Integrate the LLM and retrieval components
LangGraph
Manage the AI advisor workflow
Hugging Face Sentence Transformers
Generate document embeddings

E. RAG and Knowledge Base
Technology
Purpose
PyPDF
Extract text from agricultural PDF documents
RecursiveCharacterTextSplitter
Split documents into manageable chunks
ChromaDB
Store and retrieve agricultural document embeddings
Hugging Face Embeddings
Convert document text into vector representations

F. Testing and Deployment
Technology
Purpose
Pytest
Test calculations, API handling and application logic
Git
Version control
GitHub
Source code repository
Streamlit Community Cloud
Application deployment
Streamlit Secrets
Securely configure API keys during deployment

G. Development Environment
Visual Studio Code — Code editor.
Python 3.11 — Development runtime.
Git and GitHub — Version control.
Google Colab — Optional experimentation with embeddings or data processing.
Technology Architecture
User Interface: Streamlit + CSS + Plotly
Application Logic: Python + Pandas + NumPy
External Data: Open-Meteo + NASA POWER
AI Layer: Gemini Flash + LangChain + LangGraph
Knowledge Retrieval: PyPDF + Hugging Face Embeddings + ChromaDB
Storage: SQLite
Testing and Deployment: Pytest + GitHub + Streamlit Community Cloud
Important Technical Decisions
Python and Streamlit will be the primary application stack. React and FastAPI are not required for the initial version.
Python will perform all climate calculations; Gemini will explain the results.
ChromaDB will store verified agricultural knowledge, organized with crop-related metadata.
The application must continue providing weather and climate analysis even if the Gemini API is unavailable.
API keys must be stored securely and never committed to GitHub.
Avoid unnecessary libraries, complex architectures and multiple AI agents.
Use live API data instead of hardcoded weather examples.

15. Important Development Rules
Never restrict the application to one location.
Never restrict the application to one crop.
All weather data must come from real APIs.
Clearly distinguish forecasts, historical reanalysis and hypothetical simulations.
Never display stale cached data as live.
Crop growth stages must depend on the selected crop.
Never reuse one crop's scientific rules for another crop without evidence.
Never invent agronomic thresholds or risk scores.
Python performs numerical calculations.
Gemini explains results; it does not generate underlying weather data.
AI responses must be grounded in relevant agricultural evidence.
Show sources, units and timestamps.
Handle API and model failures.
Keep climate functionality working even when Gemini is unavailable.
Keep the code simple, modular and understandable.
Test calculations and edge cases.
Never expose API keys in GitHub.

16. Hackathon Demonstration Flow
Open AgriAstra.
Enter a farmer's village or town.
Select the correct location.
Select a crop, such as cotton, paddy or maize.
Enter crop details and growth stage.
Fetch live weather data for the selected coordinates.
Display the seven-day forecast.
Retrieve historical climate information.
Compare upcoming conditions with historical patterns.
Display crop-relevant climate exposure indicators.
Ask the AI advisor a question in Telugu.
Show evidence-backed guidance with document references.
Open the what-if simulator.
Change hypothetical rainfall or temperature.
Compare original and simulated results.
Save and view assessment history.
Demonstrate at least two different crops and two different locations to prove that the application is genuinely dynamic.

17. Definition of Success
AgriAstra will be considered successful when it provides:
Dynamic location selection.
Reliable live API integration.
Location-specific weather forecasts.
Meaningful historical climate comparisons.
Multiple crop support.
Crop-specific growth stages.
Transparent and explainable climate analysis.
Evidence-backed agricultural guidance.
Telugu and English accessibility.
Interactive what-if simulation.
Reliable error handling.
A polished and responsive interface.

18. Final Product Positioning
AgriAstra is a location-independent, multi-crop climate intelligence and agricultural decision-support platform that connects live weather data, historical climate patterns, crop-specific conditions and trusted agricultural knowledge to help farmers make informed farming decisions.
Core Differentiator
AgriAstra does not simply tell farmers what the weather is.
It helps farmers understand:
What is happening with the weather in their location?
How does it compare with historical climate patterns?
What could these conditions mean for their selected crop?
Which crop-specific factors deserve attention?
What does trusted agricultural knowledge recommend?
How might a hypothetical change in weather affect the analysis?
AgriAstra — From Weather Data to Smarter Farming Decisions.



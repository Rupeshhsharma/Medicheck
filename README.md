# MedShop AI
## Setup (VS Code terminal)
python -m venv venv
venv\Scripts\activate        # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env       # then put your ANTHROPIC_API_KEY inside
streamlit run app.py

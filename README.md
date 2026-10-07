# 💊 MediCheck AI

An AI "medical shop assistant" built with **Streamlit** and **Google Gemini**.
Upload a photo of a medicine (even a partial one), describe your problem or skin infection, and the app tells you:

- what the medicine is and what it is used for
- how to use it (standard leaflet guidance)
- whether it is suitable for your problem
- warnings and when to see a doctor

If the photo is incomplete, the app searches the web using the visible details. If it still can't identify the medicine confidently, it **refuses instead of guessing**.

> ⚠️ **Disclaimer:** This project is for information and learning only. It is not medical advice and is not a substitute for a doctor or pharmacist. Never start prescription medicines without professional guidance.

## How it works

1. User uploads a photo (or uses the camera) and describes the problem.
2. **Identify:** Gemini reads the visible text (brand, salt, strength) and uses Google Search for partial photos.
3. **Deny rule:** if the medicine is not identified or confidence is below 60%, the app declines.
4. **Advise:** for an identified medicine, it explains use, directions, suitability, warnings and red flags.

## Setup

Requires Python 3.10+.

```bash
git clone https://github.com/YOUR_USERNAME/medicheck.git
cd medicheck
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

Get a free API key at [Google AI Studio](https://aistudio.google.com), then create a `.env` file:

```bash
copy .env.example .env         # Mac/Linux: cp .env.example .env
```

Edit `.env`:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## Run

```bash
streamlit run app.py
```

Open http://localhost:8501.

## Configuration

| Setting | Where | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | `.env` | Your Google AI Studio key |
| `GEMINI_MODEL` | `.env` | Model name (try `gemini-2.5-flash-lite` if you hit limits) |
| `MIN_CONFIDENCE` | `app.py` | Minimum confidence (default 60) before the app answers |

## Notes

- The free tier has rate limits. If you see a limit message, wait a minute or switch to a lighter model.
- Never commit your `.env` file. It is already listed in `.gitignore`.
- Free-tier inputs may be used by Google to improve its products, so avoid uploading photos with personal information.

## Tech stack

Python, Streamlit, Google Gemini API (`google-genai`), Pillow, python-dotenv.

## Ideas for next steps

- Chat follow-up questions
- Multi-language support (e.g. Hindi)
- Barcode / batch number scanning
- Logging of refused photos to improve accuracy

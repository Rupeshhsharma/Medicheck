"""MedShop AI (free version, Google Gemini).
Photo of medicine (partial OK) + problem -> identify (with Google Search) -> advise, or deny.
"""
import io
import json
import os
import re

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MIN_CONFIDENCE = 60  # below this we deny
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

IDENTIFY_SYSTEM = """You are a careful pharmacy assistant that identifies medicines from photos.
The photo may show only part of the strip/box/tube/bottle.
1. Read every visible word: brand, generic/salt names, strength, manufacturer, colours, shape, imprint.
2. If details are incomplete, use Google Search with those details to find the matching product.
3. NEVER guess. If you cannot verify a specific medicine, set identified=false.
Reply with ONLY a JSON object, no markdown:
{"identified": true/false, "medicine_name": "", "generic_name": "", "strength": "",
 "form": "", "manufacturer": "", "visible_text": "",
 "photo_completeness": "full|partial|unreadable", "confidence": 0-100,
 "how_identified": "", "reason_if_not": ""}"""

ADVICE_SYSTEM = """You are a careful pharmacy assistant. Given a verified medicine and the customer's
problem, reply with ONLY a JSON object, no markdown:
{"used_for": "", "how_to_use": [""], "suitable_for_problem": "likely|partly|unlikely|unclear",
 "explanation": "", "warnings": [""], "prescription_needed": true/false, "see_doctor_if": [""]}
Rules: base directions on standard label/leaflet guidance, not a personal prescription. You cannot diagnose
skin conditions; if the problem sounds mismatched or serious (spreading, fever, pus, pain, children,
pregnancy, eyes, face), say so and advise seeing a doctor. Use Google Search to verify if unsure."""


def prepare_image(file) -> bytes:
    img = Image.open(file).convert("RGB")
    img.thumbnail((1568, 1568))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def ask(system: str, parts: list) -> dict:
    resp = client.models.generate_content(
        model=MODEL,
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    text = resp.text or ""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("Model did not return a valid answer. Please try again.")
    return json.loads(match.group(0))


def identify(img: bytes, problem: str) -> dict:
    return ask(IDENTIFY_SYSTEM, [
        types.Part.from_bytes(data=img, mime_type="image/jpeg"),
        f"Customer's note: {problem or 'none'}\nIdentify this medicine.",
    ])


def advise(med: dict, problem: str) -> dict:
    return ask(ADVICE_SYSTEM, [f"Medicine: {json.dumps(med)}\nCustomer's problem: {problem}"])


# ---------------- UI ----------------
st.set_page_config(page_title="MedShop AI", page_icon="💊", layout="centered")
st.title("💊 Medi Check")
st.caption("Show a medicine, describe your problem - get what it's for, how to use it, and if it fits.")
st.caption("This is a Demo Model and Need Further improvemets")
if not os.getenv("GEMINI_API_KEY"):
    st.error("GEMINI_API_KEY is missing. Add it to your .env file and restart.")
    st.stop()

with st.sidebar:
    st.warning("Informational only. Not a substitute for a doctor or pharmacist. "
               "Never start prescription medicines without medical advice.")

source = st.radio("Choose photo source", ["📁 Upload photo", "📷 Use camera"], horizontal=True)

if source == "📁 Upload photo":
    photo = st.file_uploader("Medicine photo (partial is OK)", type=["jpg", "jpeg", "png", "webp"])
else:
    photo = st.camera_input("Take a photo")

problem = st.text_area("Describe your problem / skin infection",
                       placeholder="e.g. itchy red circular rash on my arm for 5 days")

if photo:
    st.image(photo, caption="Your photo", width=300)

if st.button("Check medicine", type="primary", disabled=not photo):
    try:
        img = prepare_image(photo)
        with st.spinner("Reading the photo and searching for details..."):
            med = identify(img, problem)

        ok = med.get("identified") and int(med.get("confidence", 0)) >= MIN_CONFIDENCE
        if not ok:
            st.error("❌ Sorry, I couldn't identify this medicine reliably, so I won't guess.")
            st.write(med.get("reason_if_not") or "The visible details are not enough.")
            st.info("Try a clearer photo showing the brand/salt name and strength, or ask a pharmacist.")
            st.stop()

        st.success(f"Identified: **{med['medicine_name']}** ({med.get('generic_name', '')}) "
                   f"- confidence {med['confidence']}%")
        with st.expander("How I identified it"):
            st.write(f"Photo: {med.get('photo_completeness')}")
            st.write(med.get("visible_text"))
            st.write(med.get("how_identified"))

        with st.spinner("Preparing guidance..."):
            adv = advise(med, problem)

        st.subheader("What it's for")
        st.write(adv["used_for"])
        st.subheader("How to use")
        for s in adv["how_to_use"]:
            st.markdown(f"- {s}")

        st.subheader("Is it right for your problem?")
        verdict = {"likely": ("success", "Likely suitable"), "partly": ("warning", "Partly suitable"),
                   "unlikely": ("error", "Unlikely to help"), "unclear": ("info", "Unclear")}
        kind, label = verdict.get(adv["suitable_for_problem"], ("info", "Unclear"))
        getattr(st, kind)(label)
        st.write(adv["explanation"])

        if adv.get("prescription_needed"):
            st.warning("This medicine normally needs a doctor's prescription.")
        if adv.get("warnings"):
            st.subheader("⚠️ Warnings")
            for w in adv["warnings"]:
                st.markdown(f"- {w}")
        if adv.get("see_doctor_if"):
            st.subheader("🩺 See a doctor if")
            for w in adv["see_doctor_if"]:
                st.markdown(f"- {w}")
    except Exception as e:
        msg = str(e)
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            st.error("Free daily/minute limit reached. Wait a minute and try again.")
        else:
            st.error(f"Something went wrong: {msg}")

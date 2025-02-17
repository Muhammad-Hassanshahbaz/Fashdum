from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import tempfile
from gtts import gTTS
from difflib import SequenceMatcher
import os
from groq import Groq

# Initialize FastAPI app
app = FastAPI()

# Set your Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please add it to your environment variables.")

client = Groq(api_key=GROQ_API_KEY)

# Urdu Fashion Catalog
FASHION_CATALOG_URDU = {
    "101": {
        "description": "یہ ایک شاندار سیاہ شام کا گاؤن ہے جو جلپری کے انداز کا ہے۔ یہ ریشم کے بہترین کپڑے سے بنایا گیا ہے۔",
        "price": "120 ڈالر",
        "characteristics": "خوبصورت، جدید ڈیزائن، ریشمی کپڑا، فرش تک لمبائی۔",
    },
    "102": {
        "description": "یہ ایک خوبصورت پھولوں والا لباس ہے، خاص طور پر گرمیوں کے لیے موزوں۔",
        "price": "80 ڈالر",
        "characteristics": "پھولوں کا ڈیزائن، ہلکا پھلکا کپڑا، گھٹنے تک لمبائی۔",
    },
    "104": {
        "description": "یہ ایک خوبصورت پھولوں والا لباس ہے، خاص طور پر گرمیوں کے لیے موزوں۔",
        "price": "80 ڈالر",
        "characteristics": "پھولوں کا ڈیزائن، ہلکا پھلکا کپڑا، گھٹنے تک لمبائی۔",
    },
}

# Function to search catalog
def search_catalog_urdu(query: str) -> str:
    article_number_map = {
        "ایک سو ایک": "101",
        "ایک سو دو": "102",
        "ایک سو چار": "104"
    }
    matched_item = None
    matched_code = None

    for item_code, details in FASHION_CATALOG_URDU.items():
        if f"آرٹیکل نمبر {item_code}" in query or f"{int(item_code)}" in query:
            matched_item = details
            matched_code = item_code
            break
        for written_article_number, numeric_article_number in article_number_map.items():
            if written_article_number in query and item_code == numeric_article_number:
                matched_item = details
                matched_code = item_code
                break

    if matched_item:
        if "قیمت" in query:
            return f"آرٹیکل نمبر {matched_code}: قیمت: {matched_item['price']}."
        elif "خصوصیات" in query:
            return f"آرٹیکل نمبر {matched_code}: خصوصیات: {matched_item['characteristics']}."
        elif "تفصیل" in query or "وصف" in query:
            return f"آرٹیکل نمبر {matched_code}: {matched_item['description']}."
        else:
            return (
                f"آرٹیکل نمبر {matched_code}: {matched_item['description']} قیمت: {matched_item['price']} "
                f"خصوصیات: {matched_item['characteristics']}."
            )

    best_match = {"score": 0, "item_code": None, "details": None}
    for item_code, details in FASHION_CATALOG_URDU.items():
        combined_text = details["description"] + " " + details["characteristics"]
        similarity = SequenceMatcher(None, query, combined_text).ratio()
        if similarity > best_match["score"]:
            best_match.update({"score": similarity, "item_code": item_code, "details": details})

    if best_match["score"] > 0.4:
        details = best_match["details"]
        item_code = best_match["item_code"]
        return (
            f"آرٹیکل نمبر {item_code}: {details['description']} قیمت: {details['price']} "
            f"خصوصیات: {details['characteristics']}."
        )

    return "معاف کیجیے، آپ کے سوال سے متعلق کوئی معلومات نہیں مل سکیں۔"

# API Endpoint
@app.post("/process_audio")
async def process_audio(audio_file: UploadFile = File(...)):
    if not audio_file.filename.endswith((".wav", ".mp3", ".ogg")):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .wav, .mp3, and .ogg are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        contents = await audio_file.read()
        temp_audio.write(contents)
        temp_audio_path = temp_audio.name

    try:
        with open(temp_audio_path, "rb") as file:
            transcription = client.audio.translations.create(
                file=(temp_audio_path, file.read()),
                model="whisper-large-v3",
                prompt="Specify context or spelling",
                response_format="json",
                temperature=0.0
            )
        user_query = transcription.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during transcription: {e}")
    finally:
        os.remove(temp_audio_path)

    response_text = search_catalog_urdu(user_query)

    try:
        tts = gTTS(text=response_text, lang="ur")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_tts:
            tts.save(temp_tts.name)
            tts_file_path = temp_tts.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during TTS generation: {e}")

    return FileResponse(tts_file_path, media_type="audio/mpeg")

@app.get("/")
async def welcome():
    return {"message": "Welcome to Urdu Fashion Assistant API!"}

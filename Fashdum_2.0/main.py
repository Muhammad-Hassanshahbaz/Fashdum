from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os
from groq import Groq
from difflib import SequenceMatcher

groq_api_key = os.environ["GROQ_API_KEY"] = "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"
client = Groq(api_key=groq_api_key)

app = FastAPI()

FASHION_CATALOG_URDU = {
    "101": {
        "description": "یہ ایک شاندار سیاہ شام کا گاؤن ہے جو جلپری کے انداز کا ہے۔ یہ ریشم کے بہترین کپڑے سے بنایا گیا ہے اور رسمی تقریبات کے لیے موزوں ہے۔",
        "price": "120 ڈالر",
        "characteristics": "خوبصورت، جدید ڈیزائن، ریشمی کپڑا، فرش تک لمبائی۔",
    },
    "102": {
        "description": "یہ ایک خوبصورت پھولوں والا لباس ہے، خاص طور پر گرمیوں کے لیے موزوں۔ اس کا ہلکا پھلکا کپڑا آپ کو ٹھنڈک کا احساس دیتا ہے۔",
        "price": "80 ڈالر",
        "characteristics": "پھولوں کا ڈیزائن، ہلکا پھلکا کپڑا، گھٹنے تک لمبائی۔",
    },
}

def search_catalog_urdu(query: str) -> str:
    for item_code, details in FASHION_CATALOG_URDU.items():
        if f"آرٹیکل نمبر {item_code}" in query or f"{int(item_code)}" in query:
            return f"آرٹیکل نمبر {item_code}: {details['description']} قیمت: {details['price']} خصوصیات: {details['characteristics']}."
    return "معاف کیجیے، آپ کے سوال سے متعلق کوئی معلومات نہیں مل سکیں۔"

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
            translation = client.audio.translations.create(
                file=(temp_audio_path, file.read()),
                model="whisper-large-v3",
                response_format="json",
                temperature=0.0
            )
        user_query = translation.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during transcription: {e}")
    finally:
        os.remove(temp_audio_path)

    response_text = search_catalog_urdu(user_query)
    return {"response": response_text}

@app.get("/")
async def welcome():
    return {"message": "Welcome to Urdu Fashion Assistant API!"}

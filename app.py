import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

TELEGRAM_TOKEN = "9130889381:AAH4ckQZ5fjVNLsTyjg54tqCQhZ_inMmnUI"
GEMINI_API_KEY = "AQ.Ab8RN6LZKxJ-TOYik6Tn9HgkNuBs8mAyVeAYwQGoYjjwjFXXUQ"

client = genai.Client(api_key=GEMINI_API_KEY)

def get_youtube_id(url):
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    elif "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    return None

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def translate_text_with_gemini(text_lines):
    combined_text = "\n".join(text_lines)
    prompt = f"""
    Translate the following English subtitle lines into natural Kurdish (Sorani). 
    Keep the exact same number of lines and structure. Do not add extra lines or remove any.
    
    Text to translate:
    {combined_text}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        translated_text = response.text.strip().split("\n")
        return translated_text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return text_lines

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    video_id = get_youtube_id(url)
    
    if not video_id:
        await update.message.reply_text("تکایە لینکێکی دروست لە یوتیوب بنێرە!")
        return

    await update.message.reply_text("⏳ خەریکە ژێرنووسەکە دابەزێنم و بۆ کوردی وەرگێڕم، چاوەڕوان بە...")

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        eng_texts = [item['text'] for item in transcript_list]
        kurdish_texts = translate_text_with_gemini(eng_texts)
        
        srt_content = ""
        for i, item in enumerate(transcript_list):
            start = item['start']
            end = start + item['duration']
            kurd_text = kurdish_texts[i] if i < len(kurdish_texts) else item['text']
            
            srt_content += f"{i + 1}\n"
            srt_content += f"{format_time(start)} --> {format_time(end)}\n"
            srt_content += f"{kurd_text}\n\n"
            
        file_path = f"{video_id}_kurdish.srt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
            
        with open(file_path, "rb") as f:
            await update.message.reply_document(document=f, caption="✅ ئەوەش فایلی ژێرنووسە بە کوردی!")
            
        os.remove(file_path)
        
    except Exception as e:
        await update.message.reply_text(f"❌ ببوورە، هەڵەیەک ڕوویدا: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
  

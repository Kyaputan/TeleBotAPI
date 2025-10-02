import logging
import os
import json
from datetime import datetime
import telebot
import glob

import config
from Lang.pipeline import process_image_pipeline, synthesize_all_summaries, llm_weather

logger = logging.getLogger(__name__)

if not config.TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Please set TELEGRAM_BOT_TOKEN in environment or .env")
bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN, parse_mode="HTML")




def _load_all_summaries():
    if not os.path.exists(config.SUMMARY_LOG):
        return []
    with open(config.SUMMARY_LOG, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

# ------------ config สำหรับข้อความและรายการคำสั่ง ------------
EXCLUDED_COMMANDS = ["/start", "/help", "/summary", "/clear" ,"/cls" ,"/sum" ,"/weather"]

USAGE_TEXT = (
    "คำสั่งที่ใช้ได้:\n"
    "• /start — เริ่มต้นการใช้งานบอท\n"
    "• /help — ดูวิธีใช้งานและคำสั่งทั้งหมด\n"
    "• /summary — สรุปรวมทุกไฟล์ที่เคยประมวลผล\n"
    "• /clear — ล้างไฟล์/บันทึกที่เคยประมวลผล\n\n"
    "หมายเหตุ: ส่ง ‘รูปภาพ’ เพื่อให้บอทวิเคราะห์และตอบสรุปกลับค่ะ 📷"
)

WELCOME_TEXT = (
    "สวัสดีค่ะ ยินดีต้อนรับ 🤖✨\n"
    "ส่งรูปมาได้เลย หนูจะวิเคราะห์ด้วย LLM แล้วส่งสรุปกลับให้ค่ะ\n\n"
    f"{USAGE_TEXT}"
)

#* ------------ /start ------------
@bot.message_handler(commands=["start"])
def handle_start(m):
    logger.info("Start command received", extra={"user_id": m.from_user.id})
    bot.reply_to(m, WELCOME_TEXT)

#* ------------ /help ------------
@bot.message_handler(commands=["help"])
def handle_help(m):
    logger.info("Help command received", extra={"user_id": m.from_user.id})
    bot.reply_to(m, USAGE_TEXT)

#* ------------ /summary ------------
@bot.message_handler(commands=["summary" , "sum"])
def handle_summary(m):
    logger.info("Summary command received")
    try:
        bot.send_message(m.chat.id, "<b>กำลังประมวลผล...</b>")
        summaries = _load_all_summaries()
        logger.info("Summaries requested", extra={"count": len(summaries)})
        combined = synthesize_all_summaries(summaries)
        bot.send_message(m.chat.id, f"<b>สรุปรวมทั้งหมด</b>\n{combined}")
    except Exception as e:
        bot.reply_to(m, f"มีข้อผิดพลาด: <code>{e}</code> ค่ะ")

#* ------------ ข้อความทั่วไป (ที่ไม่ใช่คำสั่ง) ------------
@bot.message_handler(func=lambda msg: bool(getattr(msg, "text", None)) and msg.text.strip() not in EXCLUDED_COMMANDS)
def handle_free_text(m):
    logger.info("Free text received", extra={"user_id": m.from_user.id, "text": m.text})
    try:
        bot.send_message(
            m.chat.id,
            "โปรดส่งข้อความที่กำหนดแล้วเท่านั้นค่ะ เช่น /summary /clear หรือส่ง ‘รูปภาพ’ เพื่อให้บอทวิเคราะห์ค่ะ\n\n"
            f"{USAGE_TEXT}"
        )
    except Exception as e:
        bot.reply_to(m, f"มีข้อผิดพลาด: <code>{e}</code> ค่ะ")
        

#* ------------ /clear ------------
@bot.message_handler(commands=["clear", "cls"])
def handle_clear(m):
    logger.info("Clear command received")
    try:
        bot.send_message(m.chat.id, "<b>กำลังล้างไฟล์...</b>")

        # 1) ลบไฟล์ใน uploads และ processed
        for path in glob.glob("uploads/*"):
            try:
                os.remove(path)
            except Exception as e:
                logger.warning("ลบไฟล์ไม่สำเร็จ", extra={"file": path, "error": str(e)})

        for path in glob.glob("processed/*"):
            try:
                os.remove(path)
            except Exception as e:
                logger.warning("ลบไฟล์ไม่สำเร็จ", extra={"file": path, "error": str(e)})

        # 2) ล้างไฟล์ log summaries
        if os.path.exists(config.SUMMARY_LOG):
            with open(config.SUMMARY_LOG, "w", encoding="utf-8") as f:
                f.write("")  # เขียนทับให้ว่างเปล่า

        bot.send_message(m.chat.id, "<b>ล้างไฟล์เรียบร้อยค่ะ ✅</b>")

    except Exception as e:
        bot.reply_to(m, f"มีข้อผิดพลาด: <code>{e}</code> ค่ะ")

#* ------------ photo ------------
@bot.message_handler(content_types=["photo"])
def handle_photo(m):
    logger.info("Photo received")
    try:
        photo = m.photo[-1]
        file_info = bot.get_file(photo.file_id)
        file_bytes = bot.download_file(file_info.file_path)

        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        in_path = os.path.join(config.UPLOAD_DIR, f"{m.chat.id}_{m.message_id}_{ts}.jpg")
        with open(in_path, "wb") as f:
            f.write(file_bytes)
        bot.reply_to(m,
        "รอสักครู่ค่ะ หนูกำลังวิเคราะห์รูป"
    )

        summary, out_path = process_image_pipeline(in_path)

        caption = (
            "<b>ผลวิเคราะห์</b>\n"
            f"{summary}\n\n"
            "<b>ไฟล์</b>: <code>" + os.path.basename(out_path) + "</code>"
        )
        with open(out_path, "rb") as f:
            bot.send_photo(m.chat.id, f, caption=caption)

    except Exception as e:
        logger.error("Photo processing failed", extra={"error": str(e)})
        bot.reply_to(m, f"โอ๊ะ มีข้อผิดพลาด: <code>{e}</code> ค่ะ")

#* ------------ /weather ------------
@bot.message_handler(commands=["weather"])
def handle_weather(m):
    logger.info("Weather command received")
    try:
        bot.send_message(m.chat.id, "<b>กำลังขอข้อมูล...</b>")
        weather = llm_weather("Bangkok")
        logger.info("Weather requested", extra={"weather": weather})
        bot.send_message(m.chat.id, f"<b>ข้อมูลอากาศ</b>\n{weather}")
    except Exception as e:
        bot.reply_to(m, f"มีข้อผิดพลาด: <code>{e}</code> ค่ะ")

def run_bot():
    logger.info("Bot is running")
    bot.infinity_polling(skip_pending=True, allowed_updates=["message"])

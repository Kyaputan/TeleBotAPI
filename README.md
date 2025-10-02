# TeleBotAPI — Telegram Bot วิเคราะห์รูปภาพด้วย LLM (ภาษาไทย)

บอท Telegram ที่วิเคราะห์รูปภาพและสรุปผลเป็นภาษาไทยโดยใช้ Vision LLM ผ่าน OpenRouter (โมเดล `x-ai/grok-4-fast:free`).
ยังรวมสรุปย้อนหลังของทุกรูปที่เคยประมวลผล และมีคำสั่งล้างข้อมูลได้ในตัว

## คุณสมบัติหลัก

- วิเคราะห์รูปภาพ: ส่งรูปให้บอท → ได้สรุปสั้น กระชับ พร้อมบันทึกลงไฟล์
- สรุปรวม: รวมสรุปจากทุกรูปที่ผ่านมา (`/summary`, `/sum`)
- ล้างข้อมูล: ลบไฟล์อัปโหลด/ประมวลผลและเคลียร์ไฟล์สรุป (`/clear`, `/cls`)
- คำสั่งช่วยเหลือ: `/start`, `/help`
- สภาพอากาศ (เดโม): `/weather` สร้างข้อความโดย LLM (ไม่ได้ดึงข้อมูลจริง)

> หมายเหตุ: มีตัวอย่างตัวช่วยดึงอากาศจริงใน `src/helper/wether.py` (Open‑Meteo + Nominatim)

## โครงสร้างโปรเจกต์

```
.
├─ src/
│  ├─ main.py                  # จุดเริ่มโปรแกรม: ตั้งค่า logging, SIGINT และรันบอท
│  ├─ config.py                # อ่านตัวแปรแวดล้อม, สร้างโฟลเดอร์, ตั้งค่า logging
│  ├─ bot/
│  │  └─ bot.py                # ตัวจัดการคำสั่ง/ข้อความของ Telegram
│  ├─ Lang/
│  │  └─ pipeline.py           # ขั้นตอน LLM สำหรับรูปภาพ/สรุปรวม/เดโมสภาพอากาศ
│  └─ helper/
│     └─ wether.py             # ยูทิลสำหรับสภาพอากาศจริง (Open‑Meteo/Nominatim)
├─ uploads/                    # เก็บไฟล์ที่ผู้ใช้ส่งมา (ถูกสร้างอัตโนมัติ)
├─ processed/                  # เก็บไฟล์ที่ประมวลผลแล้ว (ถูกสร้างอัตโนมัติ)
├─ logs/                       # ไฟล์ log (เช่น logs/bot.log)
└─ summaries.jsonl             # บันทึกสรุปแบบ JSON Lines
```

## การติดตั้ง

ข้อกำหนด: Python 3.13+ และ [uv](https://github.com/astral-sh/uv)

1) ติดตั้ง uv (เช่น `pip install uv` หรือดูคู่มือในลิงก์ข้างต้น)

2) ติดตั้ง dependencies ตาม `pyproject.toml`/`uv.lock`

```bash
uv sync
```

## การตั้งค่า .env

สร้างไฟล์ `.env` ที่รากโปรเจกต์ และกำหนดค่าต่อไปนี้

```
TELEGRAM_BOT_TOKEN=ใส่โทเค็นบอทจาก @BotFather
OPENROUTER_API_KEY=ใส่คีย์ OpenRouter ของคุณ
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

> หากไม่ตั้งค่า `OPENROUTER_BASE_URL` อาจเรียกใช้งาน LLM ไม่สำเร็จ ขึ้นกับค่าเริ่มต้นของไลบรารี

## วิธีรันบอท

รันด้วย uv จากรากโปรเจกต์ (ระบบจะใช้ env ที่ `uv sync` เตรียมไว้)

```bash
uv run src/main.py
```

หยุดบอทด้วย `Ctrl + C` (มีตัวดักสัญญาณเพื่อปิด polling อย่างสุภาพ)

## การใช้งานใน Telegram

- `/start` — แสดงข้อความต้อนรับและวิธีใช้งาน
- `/help` — แสดงรายการคำสั่ง
- ส่ง “รูปภาพ” — บอทจะวิเคราะห์รูปและตอบสรุป พร้อมบันทึกลง `summaries.jsonl`
- `/summary` หรือ `/sum` — สรุปรวมทุกรูปที่ผ่านมา โดยใช้ LLM สังเคราะห์เพิ่มเติม
- `/clear` หรือ `/cls` — ล้างไฟล์ใน `uploads/`, `processed/` และเคลียร์ไฟล์ `summaries.jsonl`
- `/weather` — LLM สร้างคำอธิบายสภาพอากาศ 

## ไฟล์ผลลัพธ์และ log

- `uploads/` — ไฟล์ต้นฉบับที่ผู้ใช้ส่งมา
- `processed/` — ไฟล์ที่ผ่านขั้นตอนประมวลผลแล้ว (คัดลอกจากต้นฉบับเพื่อเก็บเวอร์ชันผลลัพธ์)
- `logs/bot.log` — ไฟล์ log จากระบบ
- `summaries.jsonl` — เก็บบรรทัด JSON ต่อรูป เช่น

```json
{
  "timestamp_utc": "2025-01-01T12:34:56",
  "input_path": "uploads/123_456_20250101-123456.jpg",
  "output_path": "processed/123_456_20250101-123456_processed.jpg",
  "summary": "สรุปผลแบบย่อจาก LLM"
}
```

## หมายเหตุ/ข้อควรทราบ

- โปรเจกต์ใช้โมเดลผ่าน OpenRouter: ควรตรวจสอบเครดิต/โควตาในการใช้งาน
- การวิเคราะห์ภาพเป็นภาษาไทยถูกควบคุมด้วยพรอมป์ใน `Lang/pipeline.py` สามารถปรับแต่งให้ยาว/สั้นขึ้นหรือเปลี่ยนรูปแบบได้
- หากพบ `ModuleNotFoundError: No module named 'bot'` ให้รันจากใน `src` หรือกำหนด `PYTHONPATH=src` ตามตัวอย่างด้านบน

## ไลบรารีที่ใช้ (สำคัญ)

- `pytelegrambotapi` — ทำงานกับ Telegram Bot API
- `langchain`, `langchain-openai` — เรียกใช้โมเดลผ่าน OpenRouter (Vision LLM)
- `python-dotenv` — โหลดค่าจากไฟล์ `.env`
- `pillow` — จัดการรูปภาพพื้นฐาน (ถ้าจำเป็น)

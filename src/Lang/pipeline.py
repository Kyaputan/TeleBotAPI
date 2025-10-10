import json
import logging
import os
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from helper.helper import to_data_url
import config

logger = logging.getLogger(__name__)

def append_summary_log(item: dict) -> None:
    with open(config.SUMMARY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

def vlm() -> ChatOpenAI:
    return ChatOpenAI(
        model="google/gemini-2.0-flash-001",
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
        temperature=0.3,
    )

SYSTEM_PROMPT = (
    "คุณเป็นผู้ช่วยวิเคราะห์รูปภาพเป็นภาษาไทยแบบมืออาชีพ "
    "เป้าหมาย: สรุปสั้น กระชับ ชัด (2–3 ประโยค) "
    "จากนั้น bullet รายการวัตถุ/เอนทิตีสำคัญ และระบุ 'ข้อกังวลคุณภาพ' หากพบ\n"
    "ข้อกำหนดการเขียน: ภาษาไทย สุภาพ ไม่ฟุ้ง ใช้ถ้อยคำกะทัดรัด\n"
    "ห้ามแต่งเติมเกินข้อมูลที่เห็นจากภาพ"
)

def analyze_image_with_langchain(input_path: str) -> str:
    logger.info("Analyzing image", extra={"input_path": input_path})
    try:
        data_url = to_data_url(input_path)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=[
                {"type": "text",
                    "text": "ช่วยวิเคราะห์รูปนี้ให้หน่อยค่ะ"},
                {"type": "image_url",
                    "image_url": {"url": data_url}},
            ]),
    ]

        llm = vlm()
        resp = llm.invoke(messages)
        logger.info("Analysis complete")
        return (resp.content or "").strip()
    except Exception as e:
        logger.error("Analysis failed", extra={"error": str(e)})
        return ""

def process_image_pipeline(input_path: str):
    summary = analyze_image_with_langchain(input_path)

    base = os.path.basename(input_path)
    name, ext = os.path.splitext(base)
    out_path = os.path.join(config.PROCESSED_DIR, f"{name}_processed{ext or '.jpg'}")
    with open(input_path, "rb") as src, open(out_path, "wb") as dst:
        dst.write(src.read())

    log_item = {
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds"),
        "input_path": input_path,
        "output_path": out_path,
        "summary": summary,
    }
    append_summary_log(log_item)
    logger.info("Image processed")
    return summary, out_path

def synthesize_all_summaries(summaries: list[dict]) -> str:
    logger.info("Synthesizing all summaries", extra={"count": len(summaries)})
    if not summaries:
        return "ยังไม่มีไฟล์ที่ถูกประมวลผลค่ะ"

    joined = "\n\n".join(
        [f"- {os.path.basename(s['input_path'])}: {s['summary']}" for s in summaries]
    )
    messages = [
        SystemMessage(content=[
            {"type": "text",
                "text": (
                    "คุณคือผู้ช่วยที่สรุปข้อมูลภาพจำนวนมาก ให้ผลลัพธ์สั้น กระชับ เชิงปฏิบัติ "
                    f"นี่คือสรุปต่อไฟล์:\n\n{joined}\n\n"
                )},
        ]),
        HumanMessage(content=[
            {"type": "text",
                "text": (
                    "สังเคราะห์เป็นสรุปรวม: bullet ประเด็น, theme ให้สั้น กระชับ เชิงปฏิบัติ"
                )}
        ]),
    ]
    llm = vlm()
    resp = llm.invoke(messages)
    logger.info("Summary generated")
    return (resp.content or "").strip()

def llm_weather(weather: str) -> str:
    logger.info("Weather command received")
    messages = [
        SystemMessage(content=[
            {"type": "text",
                "text": (
                    "คุณคือผู้ช่วยที่สรุปข้อมูลอากาศ ให้ผลลัพธ์สั้น กระชับ เชิงปฏิบัติ "
                    f"นี่คือข้อมูลอากาศ:\n\n{weather}\n\n"
                )},
        ]),
        HumanMessage(content=[
            {"type": "text",
                "text": (
                    "คิดว่าสภาพอากาศจะเป็นอย่างไร ฝนจะตกไหม ลมแรงไหม"
                )}
        ]),
    ]
    llm = vlm()
    resp = llm.invoke(messages)
    logger.info("Weather generated")
    return (resp.content or "").strip()
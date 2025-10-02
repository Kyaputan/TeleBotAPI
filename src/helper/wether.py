import requests
from typing import Dict, Any, Optional
# ---------- พิกัดยอดนิยมในไทย (เติมเพิ่มได้) ----------
TH_PRESET_COORDS = {
    # province / city : (lat, lon)
    "bangkok": (13.7563, 100.5018),
    "bkk": (13.7563, 100.5018),
    "นนทบุรี": (13.8600, 100.5140),
    "ปทุมธานี": (14.0210, 100.5250),
    "สมุทรปราการ": (13.5991, 100.5996),
    "เชียงใหม่": (18.7883, 98.9853),
    "เชียงราย": (19.9105, 99.8406),
    "ลำปาง": (18.2888, 99.4928),
    "พิษณุโลก": (16.8283, 100.2729),
    "ขอนแก่น": (16.4419, 102.8350),
    "อุดรธานี": (17.4138, 102.7877),
    "อุบลราชธานี": (15.2384, 104.8487),
    "นครราชสีมา": (14.9799, 102.0977),
    "สุราษฎร์ธานี": (9.1382, 99.3215),
    "นครศรีธรรมราช": (8.4304, 99.9631),
    "ภูเก็ต": (7.8804, 98.3923),
    "กระบี่": (8.0863, 98.9063),
    "หาดใหญ่": (7.0086, 100.4747),
    "พัทยา": (12.9236, 100.8825),
    "ระยอง": (12.6810, 101.2810),
    "ชลบุรี": (13.3611, 100.9847),
    "อยุธยา": (14.3532, 100.5684),
    "สุโขทัย": (17.0060, 99.8200),
}

# ---------- แผนที่คำอธิบายสภาพอากาศแบบไทย ----------
WEATHER_CODE_TH = {
    0: "ท้องฟ้าแจ่มใส",
    1: "มีเมฆเล็กน้อย",
    2: "มีเมฆเป็นส่วนมาก",
    3: "เมฆมาก",
    45: "หมอก",
    48: "หมอกน้ำแข็ง",
    51: "ฝนปรอยเบา",
    53: "ฝนปรอยปานกลาง",
    55: "ฝนปรอยหนัก",
    56: "ฝนปรอย หนาวจัด",
    57: "ฝนปรอย หนักและหนาวจัด",
    61: "ฝนเบา",
    63: "ฝนปานกลาง",
    65: "ฝนหนัก",
    66: "ฝนหนาวจัด",
    67: "ฝนหนักและหนาวจัด",
    71: "หิมะเบา (แทบไม่มีในไทย)",
    73: "หิมะปานกลาง",
    75: "หิมะหนัก",
    77: "เม็ดน้ำแข็ง",
    80: "ฝนซู่เบา",
    81: "ฝนซู่ปานกลาง",
    82: "ฝนซู่หนัก",
    85: "หิมะซู่เบา",
    86: "หิมะซู่หนัก",
    95: "พายุฝนฟ้าคะนอง",
    96: "พายุฝนฟ้าคะนอง พร้อมลูกเห็บเล็ก",
    99: "พายุฝนฟ้าคะนอง พร้อมลูกเห็บใหญ่",
}


def _geocode_nominatim(place: str) -> Optional[tuple[float, float]]:
    """
    ค้นหาพิกัดจากชื่อสถานที่ด้วย Nominatim (OpenStreetMap)
    หมายเหตุ: API นี้ free-rate-limited; ควร cache ใน production
    """
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{place}, Thailand",
                "format": "jsonv2",
                "addressdetails": 0,
                "limit": 1,
            },
            headers={"User-Agent": "thai-weather-bot/1.0"}
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None

def get_weather(
    place: str = "Bangkok",
    hourly: bool = False,
) -> Dict[str, Any]:
    """
    ดึงสภาพอากาศประเทศไทยจาก Open-Meteo
    - place: ชื่อจังหวัด/เมืองไทย (ไทย/อังกฤษได้) เช่น 'เชียงใหม่', 'Bangkok'
    - hourly: ถ้า True จะรวม hourly temp ล่าสุด 24 ชั่วโมง

    Return:
      {
        "place": "...",
        "latitude": float,
        "longitude": float,
        "timezone": "Asia/Bangkok",
        "current": {
            "time": "YYYY-MM-DDTHH:MM",
            "weather_text_th": "...",
            "temperature_c": float,
            "humidity_%": int | None,
            "wind_speed_kmh": float | None,
            "rain_mm": float | None
        },
        "today": {
            "tmin_c": float,
            "tmax_c": float,
            "rain_mm": float
        },
        "hourly": [ ... ]  # เมื่อ hourly=True
      }
    """
    # 1) หาพิกัด
    key = place.strip().lower()
    coords = TH_PRESET_COORDS.get(key) or TH_PRESET_COORDS.get(place)  # เผื่อ key เป็นไทย
    if not coords:
        coords = _geocode_nominatim(place)
    if not coords:
        raise ValueError(f"หา location ไม่เจอ: {place}")

    lat, lon = coords

    # 2) เรียก Open-Meteo
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "Asia/Bangkok",
        "current": ["temperature_2m", "relative_humidity_2m", "rain", "weather_code", "wind_speed_10m"],
        "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum"],
    }
    if hourly:
        params["hourly"] = ["temperature_2m", "relative_humidity_2m", "rain"]
        params["past_days"] = 0
        params["forecast_days"] = 1

    resp = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=15)
    resp.raise_for_status()
    wx = resp.json()

    cur = wx.get("current", {})
    daily = wx.get("daily", {})

    code = cur.get("weather_code")
    text_th = WEATHER_CODE_TH.get(code, f"สภาพอากาศรหัส {code}")

    out: Dict[str, Any] = {
        "place": place,
        "latitude": lat,
        "longitude": lon,
        "timezone": wx.get("timezone", "Asia/Bangkok"),
        "current": {
            "time": cur.get("time"),
            "weather_text_th": text_th,
            "temperature_c": cur.get("temperature_2m"),
            "humidity_%": cur.get("relative_humidity_2m"),
            "wind_speed_kmh": cur.get("wind_speed_10m"),
            "rain_mm": cur.get("rain"),
        },
        "today": {
            "tmin_c": (daily.get("temperature_2m_min") or [None])[0],
            "tmax_c": (daily.get("temperature_2m_max") or [None])[0],
            "rain_mm": (daily.get("rain_sum") or [None])[0],
        }
    }

    if hourly and "hourly" in wx:
        out["hourly"] = [
            {
                "time": t,
                "temperature_c": temp,
                "humidity_%": (wx["hourly"].get("relative_humidity_2m") or [None])[i],
                "rain_mm": (wx["hourly"].get("rain") or [None])[i],
            }
            for i, (t, temp) in enumerate(zip(wx["hourly"]["time"], wx["hourly"]["temperature_2m"]))
        ]

    return out
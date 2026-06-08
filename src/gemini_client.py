import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Lấy API key từ file .env hoặc từ biến môi trường của hệ thống
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def get_embedding(text: str) -> list[float]:
    """
    Sinh vector embedding của văn bản sử dụng model text-embedding-004 của Gemini.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("⚠ CẢNH BÁO: Chưa cấu hình GEMINI_API_KEY thực, sử dụng mock embedding (768 chiều).")
        # Trả về một vector giả lập 768 chiều (độ dài default của text-embedding-004)
        return [0.01] * 768

    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "content": {
            "parts": [{"text": text}]
        }
    }

    response = requests.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    if "embedding" in data and "values" in data["embedding"]:
        return data["embedding"]["values"]
    else:
        raise ValueError(f"Phản hồi từ Gemini API không đúng định dạng embedding: {data}")


def generate_content(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.3,
    top_p: float = 0.9
) -> str:
    """
    Tạo câu trả lời từ Gemini 1.5 Flash sử dụng REST API.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("⚠ CẢNH BÁO: Chưa cấu hình GEMINI_API_KEY thực, sử dụng mock response.")
        return "[Mock Response] Đây là câu trả lời giả lập vì GEMINI_API_KEY chưa được thiết lập. Hãy thêm API key vào file .env để sử dụng Gemini 1.5 Flash."

    # Dùng gemini-1.5-flash làm mặc định cho độ trễ thấp và tối ưu chi phí
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": temperature,
            "topP": top_p
        }
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise ValueError(f"Không thể parse kết quả từ Gemini API: {data}") from e

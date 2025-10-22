import os
import aiohttp
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv


# بارگذاری متغیرهای محیطی (برای توسعه محلی)
load_dotenv()


# مقداردهی اولیه اپلیکیشن FastAPI
app = FastAPI()


# خواندن کلید API از متغیرهای محیطی
# در Hugging Face، این مقدار از بخش 'Repository secrets' خوانده می‌شود.
API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"


# مانت کردن پوشه 'static' برای ارائه فایل‌های HTML, CSS, JS
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    """
    ارائه فایل اصلی index.html به کاربر.
    """
    return FileResponse('static/index.html')


@app.post("/api/chat/completions")
async def proxy_api_call(request: Request):
    """
    این endpoint به عنوان یک پراکسی امن عمل می‌کند.
    درخواست JSON را از فرانت‌اند دریافت کرده، کلید API را به آن اضافه می‌کند
    و سپس به سرور OpenRouter ارسال می‌نماید.
    """
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on the server. The admin needs to set the OPENAI_API_KEY secret."
        )


    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body.")


    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }


    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=body, headers=headers) as response:
                response_json = await response.json()
                if not response.ok:
                    # ارسال خطای دریافتی از API اصلی به فرانت‌اند
                    raise HTTPException(status_code=response.status, detail=response_json)
                return response_json
        except aiohttp.ClientConnectorError as e:
            raise HTTPException(status_code=502, detail=f"Network error: Unable to connect to the external API. {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


# برای اجرای محلی: uvicorn app:app --reload --port 7860

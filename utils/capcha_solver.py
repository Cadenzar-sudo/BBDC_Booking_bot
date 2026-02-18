import os
import re
import time
import logging
import base64
import io
from PIL import Image, ImageOps
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

def ocr_base64(base64_img):
    # 1. CLEAN & COMPRESS IMAGE (Fixes the 45s upload lag)
    try:
        raw_data = base64_img.replace("data:image/png;base64,", "").strip()
        # raw_data = base64_img.replace("data:image/jpeg;base64,", "").strip()
        img = Image.open(io.BytesIO(base64.b64decode(raw_data)))
        
        # Resize if too large (CAPTCHAs don't need 4K)
        img.thumbnail((300, 100)) 
        img = img.convert("L") 
        img = ImageOps.autocontrast(img, cutoff=1)
        
        # Convert to JPEG (smaller than PNG for Base64)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        optimized_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        logging.error(f"Image optimization failed: {e}")
        optimized_base64 = raw_data

    # 2. ULTRA-FAST PROMPT (Reduces "Thinking" time)
    prompt = "CAPTCHA: Must be 5-chars, case-sensitive. Rule(only use when detect letter j): Hook+dot='j', Hook+no dot='J'. Format: [Reason] captcha:[5-chars]"

    for i in range(3):
        try:
            # 3. REQUEST WITH TIMEOUT & 2.0 FLASH
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    prompt,
                    {"inline_data": {"data": optimized_base64, "mime_type": "image/jpeg"}}
                ],
                config=types.GenerateContentConfig(
                    max_output_tokens=40,
                    temperature=0.1
                )
            )

            text = response.text.strip()
            logging.info(f"LLM Output: {text}")
            print(text)

            # 4. FLEXIBLE REGEX (Handles capcha:[ABCDE] or capcha:ABCDE)
            result = re.search(r'captcha:\[?([a-zA-Z0-9]{5})\]?', text)
            
            if result:
                return result.group(1), optimized_base64
            
            logging.warning(f"Attempt {i+1} failed to parse.")
            
        except Exception as e:
            logging.critical(f"API Error: {e}")
            time.sleep(1)

    return "", optimized_base64

# print("start")
# with open("test.txt","r") as f:
#     img = f.read()
# print(ocr_base64(img))
# print("end")
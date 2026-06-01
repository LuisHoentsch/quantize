import os
import io

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
from PIL import Image
import pillow_heif
from stylizer import apply_stylization

pillow_heif.register_heif_opener()

app = FastAPI(title="Image Stylization API")

@app.post("/api/stylize")
async def stylize_image(
    file: UploadFile = File(...),
    num_colors: int = Form(3),
    num_shades_per_color: int = Form(3),
    d: int = Form(15),
    sigma_color: float = Form(75.0),
    sigma_space: float = Form(75.0),
    passes: int = Form(5),
    ksize: int = Form(7),
    max_dim: int = Form(1000)
):
    # Check if the content type is supported
    supported_mime_types = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/tiff",
        "image/x-ms-bmp",
        "image/heic",
        "image/heif"
    ]
    if file.content_type not in supported_mime_types:
        return Response(
            content=f"Unsupported file format ({file.content_type}). Please provide a supported image.",
            status_code=400
        )

    # Read file contents into memory
    contents = await file.read()

    # Convert to cv2 image
    if file.content_type in ["image/heic", "image/heif"]:
        try:
            img_pil = Image.open(io.BytesIO(contents))
            if img_pil.mode in ("RGBA", "P"):
                img_pil = img_pil.convert("RGB")
            elif img_pil.mode != "RGB":
                img_pil = img_pil.convert("RGB")
            # Convert PIL RGB to cv2 BGR
            img_cv2 = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        except Exception as e:
            img_cv2 = None
    else:
        nparr = np.frombuffer(contents, np.uint8)
        img_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_cv2 is None:
        return Response(content="Invalid image data", status_code=400)

    # Apply stylization
    result_cv2 = apply_stylization(
        image=img_cv2,
        num_colors=num_colors,
        num_shades_per_color=num_shades_per_color,
        d=d,
        sigma_color=sigma_color,
        sigma_space=sigma_space,
        passes=passes,
        ksize=ksize,
        max_dim=max_dim
    )

    # Encode back to JPEG
    success, encoded_image = cv2.imencode('.jpg', result_cv2)
    if not success:
        return Response(content="Failed to encode image", status_code=500)

    return Response(content=encoded_image.tobytes(), media_type="image/jpeg")

# --- 2. Mount the Vue Static Files ---
# This tells FastAPI: "If a request starts with /assets, look in the dist/assets folder"
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

# This must go at the VERY BOTTOM of your code!
@app.get("/{catchall:path}")
async def serve_vue_app(catchall: str):
    # Check if a specific file is requested (like a favicon)
    file_path = f"frontend/dist/{catchall}"
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)

    # Otherwise, return the main Vue index.html
    return FileResponse("frontend/dist/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

import os

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
from stylizer import apply_stylization

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
    # Read file contents into memory
    contents = await file.read()

    # Convert directly to cv2 image
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

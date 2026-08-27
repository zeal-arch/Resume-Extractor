import os
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from src.parsers import extract_text, SUPPORTED_FORMATS
from src.extractors import extract_all

app = FastAPI(title="Resume Information Extraction System")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serve the main frontend HTML file."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/api/extract")
async def extract_resume_info(file: UploadFile = File(...)):
    """
    Accept a resume file (PDF or DOCX), extract structured data, return JSON.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Accepted: {', '.join(sorted(SUPPORTED_FORMATS))}",
        )

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        text, embedded_uris = extract_text(tmp_path)

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted. The file may be empty or scanned.",
            )

        result = extract_all(text, embedded_uris)
        result["_filename"] = file.filename
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error processing file: {exc}") from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

FROM python:3.11-slim

# System dependencies:
#  - poppler-utils: required by pdf2image to rasterize PDF pages for OCR
#  - tesseract-ocr: required by pytesseract to run OCR on scanned resumes
#  - build-essential/libpq-dev not needed (sqlite is file-based, scikit-learn wheels are prebuilt)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV UPLOAD_DIR=/data/uploaded_resumes
ENV DATABASE_URL=sqlite:////data/resume_screening.db

RUN mkdir -p /data/uploaded_resumes

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

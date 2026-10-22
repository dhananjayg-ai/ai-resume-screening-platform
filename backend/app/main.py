"""FastAPI application entrypoint: creates the app, wires up CORS, creates DB
tables on startup, includes all routers, and serves a branded HTML landing
page plus violet-themed API docs (instead of the stock FastAPI/Swagger look)."""
import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app import models
from app.routers import candidates, chatbot, interviews, jobs, matching, notifications, resumes

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Color tokens -- kept in sync with frontend/utils/styling.py so the backend
# (landing page + API docs) and the Streamlit frontend read as one product.
# ---------------------------------------------------------------------------
PRIMARY = "#6D28D9"
PRIMARY_DARK = "#4C1D95"
PRIMARY_LIGHT = "#A78BFA"
ACCENT_BG = "#EDE9FE"
PAGE_BG = "#F7F6FB"
TEXT_DARK = "#1E1B2E"
SUCCESS = "#15803D"
INFO = "#1D4ED8"

# Docs are re-mounted below with custom theming, so disable the stock ones.
app = FastAPI(
    title=settings.api_title,
    description=(
        "Backend API for the AI Resume Screening and Recruitment Platform: "
        "job postings, resume parsing & screening, NLP matching, an HR chatbot, "
        "interview scheduling, email notifications, duplicate detection, "
        "resume quality feedback, skill-gap recommendations, and multi-language support."
    ),
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

origins = (
    ["*"] if settings.cors_origins.strip() == "*" else [o.strip() for o in settings.cors_origins.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Branded landing page
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False, response_class=HTMLResponse)
def root(db: Session = Depends(get_db)):
    job_count = db.query(models.Job).count()
    candidate_count = db.query(models.Candidate).count()
    interview_count = db.query(models.InterviewSchedule).count()
    notification_count = db.query(models.NotificationLog).count()

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{settings.api_title}</title>
<style>
  :root {{
    --primary: {PRIMARY};
    --primary-dark: {PRIMARY_DARK};
    --primary-light: {PRIMARY_LIGHT};
    --accent-bg: {ACCENT_BG};
    --page-bg: {PAGE_BG};
    --text-dark: {TEXT_DARK};
    --success: {SUCCESS};
    --info: {INFO};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: linear-gradient(160deg, var(--page-bg) 0%, #FFFFFF 45%, var(--accent-bg) 100%);
    color: var(--text-dark);
    min-height: 100vh;
  }}
  .wrap {{ max-width: 920px; margin: 0 auto; padding: 2.5rem 1.5rem 3rem; }}
  .banner {{
    padding: 2rem 2.2rem;
    border-radius: 16px;
    background: linear-gradient(120deg, var(--primary-dark) 0%, var(--primary) 60%, var(--primary-light) 100%);
    color: #fff;
    box-shadow: 0 10px 30px rgba(76, 29, 149, 0.28);
    margin-bottom: 1.8rem;
  }}
  .banner h1 {{ margin: 0 0 0.4rem 0; font-size: 1.9rem; }}
  .banner p {{ margin: 0; color: #EDE9FE; font-size: 1.05rem; }}
  .status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(255,255,255,0.18);
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    font-weight: 600;
    font-size: 0.85rem;
    margin-top: 0.9rem;
  }}
  .dot {{ width: 9px; height: 9px; border-radius: 50%; background: #4ADE80; display: inline-block; }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 1rem;
    margin-bottom: 1.8rem;
  }}
  .card {{
    background: #fff;
    border-radius: 12px;
    border-left: 6px solid var(--primary);
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 10px rgba(30, 27, 46, 0.08);
  }}
  .card .label {{
    font-size: 0.78rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.03em; color: #6B7280;
  }}
  .card .value {{ font-size: 1.9rem; font-weight: 700; margin-top: 0.2rem; }}
  .links {{
    display: flex; gap: 0.9rem; flex-wrap: wrap; margin-bottom: 1.8rem;
  }}
  .links a {{
    display: inline-block;
    text-decoration: none;
    color: #fff;
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    padding: 0.65rem 1.3rem;
    border-radius: 8px;
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(76, 29, 149, 0.25);
  }}
  .links a.secondary {{
    background: #fff;
    color: var(--primary-dark);
    border: 1.5px solid var(--primary-light);
    box-shadow: none;
  }}
  .section-header {{
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.5rem 1rem; margin: 0 0 0.8rem 0;
    border-left: 4px solid var(--primary);
    background: var(--accent-bg);
    border-radius: 8px;
    font-weight: 700; font-size: 1.05rem;
  }}
  .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 0.7rem; }}
  .feature {{
    background: #fff; border-radius: 10px; padding: 0.8rem 1rem;
    box-shadow: 0 2px 8px rgba(30, 27, 46, 0.06); font-size: 0.92rem;
  }}
  footer {{ margin-top: 2rem; color: #6B7280; font-size: 0.85rem; text-align: center; }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="banner">
      <h1>{settings.api_title}</h1>
      <p>Backend API -- job postings, resume parsing &amp; screening, NLP matching, interview scheduling, and email notifications.</p>
      <div class="status-pill"><span class="dot"></span> API is running</div>
    </div>

    <div class="grid">
      <div class="card" style="border-left-color: {PRIMARY};">
        <div class="label">Jobs posted</div>
        <div class="value">{job_count}</div>
      </div>
      <div class="card" style="border-left-color: {INFO};">
        <div class="label">Candidates screened</div>
        <div class="value">{candidate_count}</div>
      </div>
      <div class="card" style="border-left-color: {SUCCESS};">
        <div class="label">Interviews scheduled</div>
        <div class="value">{interview_count}</div>
      </div>
      <div class="card" style="border-left-color: #BE185D;">
        <div class="label">Notifications sent</div>
        <div class="value">{notification_count}</div>
      </div>
    </div>

    <div class="links">
      <a href="/docs">Open API Docs (Swagger)</a>
      <a href="/redoc" class="secondary">Open ReDoc</a>
      <a href="/health" class="secondary">Health check</a>
    </div>

    <div class="section-header">Core capabilities</div>
    <div class="features">
      <div class="feature">Resume parsing (PDF/DOCX) with OCR fallback</div>
      <div class="feature">TF-IDF + skill-overlap candidate matching</div>
      <div class="feature">Duplicate resume detection</div>
      <div class="feature">Resume quality scoring &amp; feedback</div>
      <div class="feature">Skill-gap learning recommendations</div>
      <div class="feature">Interview scheduling</div>
      <div class="feature">Email notifications (STARTTLS / SSL)</div>
      <div class="feature">Multi-language resume support</div>
      <div class="feature">HR chatbot</div>
    </div>

    <footer>AI Resume Screening and Recruitment Platform -- v1.0.0</footer>
  </div>
</body>
</html>"""
    return HTMLResponse(html)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Violet-themed API docs (Swagger UI + ReDoc) -- a small <style> block is
# injected into the stock FastAPI-generated docs pages so they match the
# frontend's palette instead of the default white-and-green Swagger look.
# ---------------------------------------------------------------------------
_SWAGGER_THEME_CSS = f"""
<style>
  body {{ background: {PAGE_BG}; }}
  .swagger-ui .topbar {{
    background: linear-gradient(120deg, {PRIMARY_DARK} 0%, {PRIMARY} 100%);
  }}
  .swagger-ui .topbar .download-url-wrapper .select-label select {{
    border-color: {PRIMARY_LIGHT};
  }}
  .swagger-ui .info .title {{ color: {PRIMARY_DARK}; }}
  .swagger-ui .scheme-container {{ background: {ACCENT_BG}; box-shadow: none; }}
  .swagger-ui .btn.authorize {{
    color: {PRIMARY_DARK}; border-color: {PRIMARY};
  }}
  .swagger-ui .btn.authorize svg {{ fill: {PRIMARY}; }}
  .swagger-ui .opblock.opblock-get {{ background: rgba(29, 78, 216, 0.06); border-color: {INFO}; }}
  .swagger-ui .opblock.opblock-post {{ background: rgba(109, 40, 217, 0.06); border-color: {PRIMARY}; }}
  .swagger-ui .opblock.opblock-put {{ background: rgba(180, 83, 9, 0.06); border-color: #B45309; }}
  .swagger-ui .opblock.opblock-delete {{ background: rgba(185, 28, 28, 0.06); border-color: #B91C1C; }}
  .swagger-ui .opblock-tag {{ color: {TEXT_DARK}; border-bottom-color: {ACCENT_BG}; }}
  .swagger-ui .btn.execute {{
    background: {PRIMARY}; border-color: {PRIMARY};
  }}
  .swagger-ui select {{ border-color: {PRIMARY_LIGHT}; }}
</style>
"""

_REDOC_THEME_CSS = f"""
<style>
  body {{ background: {PAGE_BG}; }}
</style>
"""


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html():
    html_response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.api_title} -- API Docs",
        swagger_ui_parameters={"docExpansion": "list", "defaultModelsExpandDepth": -1},
    )
    body = html_response.body.decode("utf-8").replace("</head>", _SWAGGER_THEME_CSS + "</head>")
    return HTMLResponse(body)


@app.get("/redoc", include_in_schema=False)
def custom_redoc_html():
    html_response = get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{settings.api_title} -- ReDoc",
    )
    body = html_response.body.decode("utf-8").replace("</head>", _REDOC_THEME_CSS + "</head>")
    return HTMLResponse(body)


app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(candidates.router)
app.include_router(matching.router)
app.include_router(interviews.router)
app.include_router(notifications.router)
app.include_router(chatbot.router)

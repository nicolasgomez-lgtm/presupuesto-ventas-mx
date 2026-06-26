import json
import os
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Any
import threading

app = FastAPI()

BASE_DIR   = Path(__file__).parent
DATA_FILE  = BASE_DIR / "budget_data.json"
META_FILE  = BASE_DIR / "budget_meta.json"
LEVERS_FILE = BASE_DIR / "levers.json"
_lock = threading.Lock()

REFRESH_SQL = """
SELECT
  kitchen, brand, provider_new_name AS platform, city,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=0 THEN gmv ELSE 0 END)/3.0,0) AS avg0,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=1 THEN gmv ELSE 0 END)/3.0,0) AS avg1,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=2 THEN gmv ELSE 0 END)/3.0,0) AS avg2,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=3 THEN gmv ELSE 0 END)/3.0,0) AS avg3,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=4 THEN gmv ELSE 0 END)/3.0,0) AS avg4,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=5 THEN gmv ELSE 0 END)/3.0,0) AS avg5,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=6 THEN gmv ELSE 0 END)/3.0,0) AS avg6,
  ROUND(
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=0 THEN gmv ELSE 0 END)/3.0*4 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=1 THEN gmv ELSE 0 END)/3.0*4 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=2 THEN gmv ELSE 0 END)/3.0*4 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=3 THEN gmv ELSE 0 END)/3.0*5 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=4 THEN gmv ELSE 0 END)/3.0*5 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=5 THEN gmv ELSE 0 END)/3.0*5 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=6 THEN gmv ELSE 0 END)/3.0*4
  ,0) AS base_julio
FROM fdgy_views.orders_consolidado
WHERE order_state = 'Finalized'
  AND order_day >= CURRENT_DATE - 21
  AND order_day < CURRENT_DATE
  AND gmv > 0
  AND country = 'MEX'
GROUP BY kitchen, brand, provider_new_name, city
ORDER BY base_julio DESC
LIMIT 10000
"""

# ── Load budget data + metadata on startup ───────────────
with open(DATA_FILE) as f:
    BUDGET_DATA = json.load(f)

def load_meta() -> dict:
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text())
        except Exception:
            pass
    return {"updated_at": "2026-06-26T00:00:00+00:00", "row_count": len(BUDGET_DATA)}

# ── Lever persistence ────────────────────────────────────
def load_levers() -> list:
    if LEVERS_FILE.exists():
        try:
            return json.loads(LEVERS_FILE.read_text())
        except Exception:
            pass
    return []

def save_levers(levers: list):
    with _lock:
        LEVERS_FILE.write_text(json.dumps(levers, ensure_ascii=False))

# ── API routes ───────────────────────────────────────────
@app.get("/api/data")
def get_data():
    return JSONResponse(content=BUDGET_DATA)

@app.get("/api/meta")
def get_meta():
    return load_meta()

@app.get("/api/levers")
def get_levers():
    return {"levers": load_levers()}

class LeversPayload(BaseModel):
    levers: List[Any]

@app.put("/api/levers")
def put_levers(payload: LeversPayload):
    save_levers(payload.levers)
    return {"ok": True, "count": len(payload.levers)}

@app.post("/api/refresh")
def refresh_data():
    """Re-run the Redshift query and update the in-memory + on-disk snapshot."""
    global BUDGET_DATA

    host     = os.environ.get("REDSHIFT_HOST")
    port     = int(os.environ.get("REDSHIFT_PORT", 5439))
    database = os.environ.get("REDSHIFT_DATABASE")
    user     = os.environ.get("REDSHIFT_USER")
    password = os.environ.get("REDSHIFT_PASSWORD")

    if not all([host, database, user, password]):
        raise HTTPException(
            status_code=503,
            detail="Redshift credentials not configured. Set REDSHIFT_HOST, REDSHIFT_DATABASE, REDSHIFT_USER, REDSHIFT_PASSWORD env vars in Render."
        )

    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host, port=port, database=database,
            user=user, password=password,
            connect_timeout=60,
            options="-c statement_timeout=120000"
        )
        cur = conn.cursor()
        cur.execute(REFRESH_SQL)
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redshift error: {str(e)}")

    compact = [
        [r[0] or '', r[1] or '', r[2] or '', r[3] or '',
         float(r[4] or 0), float(r[5] or 0), float(r[6] or 0),
         float(r[7] or 0), float(r[8] or 0), float(r[9] or 0), float(r[10] or 0),
         float(r[11] or 0)]
        for r in rows
    ]

    with _lock:
        BUDGET_DATA = compact
        DATA_FILE.write_text(json.dumps(compact, ensure_ascii=False, separators=(',', ':')))
        meta = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "row_count": len(compact)
        }
        META_FILE.write_text(json.dumps(meta))

    return {"ok": True, "rows": len(compact), "updated_at": meta["updated_at"]}

# ── Static frontend ──────────────────────────────────────

@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/{full_path:path}")
def catch_all(full_path: str):
    return FileResponse(BASE_DIR / "index.html")

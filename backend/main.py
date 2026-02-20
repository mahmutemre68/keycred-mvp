import os
import shutil
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import Tenant, BankReceipt, Score
from services import RuleBasedScorer

# ---------------------------------------------------------------------------
# App & CORS
# ---------------------------------------------------------------------------
app = FastAPI(title="KeyCred MVP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

scorer = RuleBasedScorer()

# ---------------------------------------------------------------------------
# Startup: create tables & seed demo tenant
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    if not db.query(Tenant).filter(Tenant.id == 1).first():
        demo = Tenant(id=1, name="Demo Tenant", email="demo@keycred.io")
        db.add(demo)
        db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "KeyCred MVP API is running 🚀"}


@app.post("/api/upload-receipt/{tenant_id}")
async def upload_receipt(
    tenant_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run scorer
    result = scorer.score(file_path)

    # Persist receipt & score
    receipt = BankReceipt(tenant_id=tenant_id, file_path=file_path)
    db.add(receipt)
    db.flush()

    score = Score(
        tenant_id=tenant_id,
        receipt_id=receipt.id,
        keycred_score=result["keycred_score"],
        max_rent_limit=result["max_rent_limit"],
    )
    db.add(score)
    db.commit()
    db.refresh(score)

    return {
        "tenant_id": tenant_id,
        "receipt_id": receipt.id,
        "keycred_score": result["keycred_score"],
        "max_rent_limit": result["max_rent_limit"],
        "pages_parsed": result["pages_parsed"],
        "status": result["status"],
    }

# mcp_demo.py
import os

import sqlalchemy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

app = FastAPI(title="MCP Demo (leave create, fixed OTP)")

# NOTE: set this env var or edit the string below:
# Example SQLAlchemy Oracle URL (adjust host/port/service):
ORACLE_URL = os.getenv("ORACLE_URL", "oracle+oracledb://demo:demo123@oracledb19c-oracle-db.oracle19C.svc.cluster.local:1521/?service_name=orclpdb1")

engine = sqlalchemy.create_engine(ORACLE_URL, future=True)

# Fixed demo OTP
FIXED_OTP = "123456"

class LeavePayload(BaseModel):
    user_id: str
    start_date: str   # YYYY-MM-DD
    end_date: str     # YYYY-MM-DD
    leave_type: str
    reason: str = ""

class VerifyAndCreateRequest(BaseModel):
    otp: str
    payload: LeavePayload

@app.post("/mcp/verify_and_create_leave")
def verify_and_create_leave(req: VerifyAndCreateRequest):
    # Simple demo OTP check
    if req.otp != FIXED_OTP:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    payload = req.payload

    # Create a new leave request using sequence leave_req_seq for request_id
    insert_sql = text("""
        INSERT INTO leave_requests
          (request_id, user_id, start_date, end_date, leave_type, reason, status, created_at)
        VALUES (:rid, :uid, TO_DATE(:s, 'YYYY-MM-DD'), TO_DATE(:e, 'YYYY-MM-DD'), :t, :r, 'Pending', SYSTIMESTAMP)
    """)

    seq_sql = text("SELECT leave_req_seq.NEXTVAL AS seq FROM dual")

    with engine.begin() as conn:
        seq_row = conn.execute(seq_sql).fetchone()
        if not seq_row:
            raise HTTPException(status_code=500, detail="Failed to generate request id")
        rid = int(seq_row['seq'])
        conn.execute(insert_sql, {
            "rid": rid,
            "uid": payload.user_id,
            "s": payload.start_date,
            "e": payload.end_date,
            "t": payload.leave_type,
            "r": payload.reason
        })

    return {"status": "created", "request_id": rid}

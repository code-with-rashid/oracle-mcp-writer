# mcp_demo.py
import os

import sqlalchemy
from mcp.server.fastmcp import FastMCP
from sqlalchemy import text

mcp = FastMCP("Oracle MCP Writer")

# ORACLE_URL = os.getenv(
#     "ORACLE_URL",
#     "oracle+oracledb://demo:demo123@oracledb19c-oracle-db.oracle19C.svc.cluster.local:1521/?service_name=orclpdb1"
# )

ORACLE_URL = os.getenv(
    "ORACLE_URL",
    "oracle+oracledb://demo:demo123@localhost:59043/?service_name=orclpdb1"
)

engine = sqlalchemy.create_engine(ORACLE_URL, future=True)

FIXED_OTP = "123456"

# ----- Tool 1: Verify OTP -----
@mcp.tool()
def verify_otp(otp: str) -> dict:
    """
    Verifies the OTP without creating any leave request.
    Returns status only.
    """
    if otp == FIXED_OTP:
        return {"status": "verified"}
    else:
        return {"status": "failed", "error": "Invalid OTP"}

# ----- Tool 2: Create Leave Request -----
@mcp.tool()
def create_leave_request(user_id: str, start_date: str, end_date: str, leave_type: str, reason: str = "") -> dict:
    """
    Creates a leave request in Oracle database.
    Assumes OTP has been verified already.
    """
    insert_sql = text("""
        INSERT INTO leave_requests
          (request_id, user_id, start_date, end_date, leave_type, reason, status, created_at)
        VALUES (:rid, :uid, TO_DATE(:s, 'YYYY-MM-DD'), TO_DATE(:e, 'YYYY-MM-DD'), :t, :r, 'Pending', SYSTIMESTAMP)
    """)

    seq_sql = text("SELECT leave_req_seq.NEXTVAL AS seq FROM dual")

    try:
        with engine.begin() as conn:
            seq_row = conn.execute(seq_sql).fetchone()
            if not seq_row:
                return {"error": "Failed to generate request id", "status": "failed"}
            
            rid = int(seq_row[0])  # Changed from seq_row['seq'] to seq_row[0]
            conn.execute(insert_sql, {
                "rid": rid,
                "uid": user_id,
                "s": start_date,
                "e": end_date,
                "t": leave_type,
                "r": reason
            })

        return {"status": "created", "request_id": rid}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

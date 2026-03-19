from fastapi import APIRouter, HTTPException

from app.services.job_store import get_job

router = APIRouter()


@router.get("/status/{job_id}")
async def get_report_status(job_id: str):
    """
    Poll job status. When status == 'done', result_html contains the report.
    Statuses: pending → running → done | failed
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resp: dict = {
        "job_id": job_id,
        "status": job["status"],
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "specialty_name": job.get("specialty_name"),
        "provider_name": job.get("provider_name"),
    }

    if job["status"] == "done":
        resp["report_pdf_s3_url"] = job.get("report_pdf_s3_url", "")
    elif job["status"] == "failed":
        resp["error"] = job.get("error", "Unknown error")

    return resp

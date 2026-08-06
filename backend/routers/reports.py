from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database.session import get_db
from database.repository import ReportRepository
from reports.report_generator import ReportGenerator
from backend.schemas.reports import ReportResponse
from backend.security import get_current_user
from database.models import User

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=List[ReportResponse])
def get_all_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = ReportRepository(db)
    return repo.get_all()


@router.post("/generate", response_model=ReportResponse)
def generate_today_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    generator = ReportGenerator(db)
    report = generator.generate_daily_report()
    return report


@router.get("/{report_id}/download-csv")
def download_report_csv(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = ReportRepository(db)
    report = repo.get_by_id(report_id)
    if not report or not report.csv_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report CSV file not found"
        )
    return FileResponse(
        path=report.csv_file_path,
        filename=f"report_{report.id}.csv",
        media_type="text/csv"
    )

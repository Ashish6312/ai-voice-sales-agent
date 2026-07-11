from fastapi import APIRouter

from app.services.excel_service import ExcelService

router = APIRouter()

@router.get("/leads")
def get_all_leads():
    """
    Return all leads.
    """
    excel_service = ExcelService()
    return excel_service.get_all_leads()

@router.get("/leads/pending")
def get_pending_leads():
    """
    Return only the leads whose status is 'Pending'.
    """
    excel_service = ExcelService()
    return excel_service.get_pending_leads()

@router.get("/leads/{lead_id}")
def get_lead_by_id(lead_id: int):
    """
    Return one lead using its Lead ID.
    """
    excel_service = ExcelService()
    return excel_service.get_lead_by_id(lead_id)

#Serialization
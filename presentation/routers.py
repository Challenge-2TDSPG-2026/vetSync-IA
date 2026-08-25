from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from application.use_cases import ProcessPostCareIntentUseCase, ProcessPostCareIntentUseCaseError, ProcessSchedulingIntentUseCase, ProcessSchedulingIntentUseCaseError
from domain.models import ClinicalPostCarePlan, SchedulingIntent

router = APIRouter(prefix="/api/v1/assistant", tags=["Assistant"])

class IntentRequest(BaseModel):
    prompt: str

def get_use_case() -> ProcessPostCareIntentUseCase:
    try:
        return ProcessPostCareIntentUseCase()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse-intent", response_model=ClinicalPostCarePlan)
async def parse_intent(request: IntentRequest, use_case: ProcessPostCareIntentUseCase = Depends(get_use_case)):
    try:
        result = use_case.execute(request.prompt)
        return result
    except ProcessPostCareIntentUseCaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def get_scheduling_use_case() -> ProcessSchedulingIntentUseCase:
    try:
        return ProcessSchedulingIntentUseCase()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse-scheduling", response_model=SchedulingIntent)
async def parse_scheduling(request: IntentRequest, use_case: ProcessSchedulingIntentUseCase = Depends(get_scheduling_use_case)):
    try:
        result = use_case.execute(request.prompt)
        return result
    except ProcessSchedulingIntentUseCaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

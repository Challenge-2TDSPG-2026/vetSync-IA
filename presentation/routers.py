from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from application.use_cases import ProcessPostCareIntentUseCase, ProcessPostCareIntentUseCaseError, ProcessSchedulingIntentUseCase, ProcessSchedulingIntentUseCaseError
from domain.models import ClinicalPostCarePlan, SchedulingIntent
from application.ports import IAssistantGateway
from infrastructure.gemini_gateway import GeminiGateway

router = APIRouter(prefix="/api/v1/assistant", tags=["Assistant"])

class IntentRequest(BaseModel):
    prompt: str

def get_gateway() -> IAssistantGateway:
    try:
        return GeminiGateway()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inicializar IA: {str(e)}")

def get_use_case(gateway: IAssistantGateway = Depends(get_gateway)) -> ProcessPostCareIntentUseCase:
    try:
        return ProcessPostCareIntentUseCase(gateway=gateway)
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

def get_scheduling_use_case(gateway: IAssistantGateway = Depends(get_gateway)) -> ProcessSchedulingIntentUseCase:
    try:
        return ProcessSchedulingIntentUseCase(gateway=gateway)
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

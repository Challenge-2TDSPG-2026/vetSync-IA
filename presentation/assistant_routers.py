from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from application.use_cases import ProcessPostCareIntentUseCase, ProcessPostCareIntentUseCaseError, ProcessSchedulingIntentUseCase, ProcessSchedulingIntentUseCaseError, ProcessTriageIntentUseCase, ProcessTriageIntentUseCaseError, ProcessCheckinIntentUseCase, ProcessCheckinIntentUseCaseError
from domain.models.models import ClinicalPostCarePlan, SchedulingIntent, TriageResult, TriageInboundRequest, CheckinResult, CheckinResponseRequest
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

triage_router = APIRouter(tags=["Triage"])

def get_triage_use_case(gateway: IAssistantGateway = Depends(get_gateway)) -> ProcessTriageIntentUseCase:
    try:
        return ProcessTriageIntentUseCase(gateway=gateway)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@triage_router.post("/triage-inbound", response_model=TriageResult)
async def triage_inbound(request: TriageInboundRequest, use_case: ProcessTriageIntentUseCase = Depends(get_triage_use_case)):
    try:
        context = {
            "pet_id": request.pet_id,
            "tutor_id": request.tutor_id,
            "clinic_id": request.clinic_id,
            "conversation_id": request.conversation_id,
            "patient_species": request.patient_species,
            "patient_name": request.patient_name
        }
        # Remove empty contexts
        context = {k: v for k, v in context.items() if v is not None}
        
        if request.history:
            context["history"] = [msg.model_dump() for msg in request.history]
            
        result = use_case.execute(request.message, context)
        return result
    except ProcessTriageIntentUseCaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

checkin_router = APIRouter(tags=["Checkin"])

def get_checkin_use_case(gateway: IAssistantGateway = Depends(get_gateway)) -> ProcessCheckinIntentUseCase:
    try:
        return ProcessCheckinIntentUseCase(gateway=gateway)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@checkin_router.post("/parse-checkin-response", response_model=CheckinResult)
async def parse_checkin_response(request: CheckinResponseRequest, use_case: ProcessCheckinIntentUseCase = Depends(get_checkin_use_case)):
    try:
        context = {
            "pet_id": request.pet_id,
            "tutor_id": request.tutor_id,
            "clinic_id": request.clinic_id,
            "veterinarian_id": request.veterinarian_id,
            "surgery_id": request.surgery_id,
            "days_post_surgery": request.days_post_surgery,
            "conversation_id": request.conversation_id
        }
        # Remove empty contexts
        context = {k: v for k, v in context.items() if v is not None}
        
        if request.history:
            context["history"] = [msg.model_dump() for msg in request.history]
            
        result = use_case.execute(request.message, context)
        return result
    except ProcessCheckinIntentUseCaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

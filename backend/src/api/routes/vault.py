from fastapi import APIRouter
from src.core.vault.signing_service import signing_service, SignRequest, SignedResponse

router = APIRouter()

@router.post("/sign-instruction", response_model=SignedResponse)
async def sign_instruction(request: SignRequest):
    """
    Verifies a Human Approval JWT and signs the instruction with the Sovereign Vault Key.
    """
    return signing_service.sign_instruction(request)

from pydantic import BaseModel

class AuthStatus(BaseModel):
    authenticated: bool
    session_status: str # IDLE, STARTING, WAITING_FOR_USER, AUTHENTICATED, EXPIRED, ERROR

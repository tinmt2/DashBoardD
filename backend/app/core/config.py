from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./opsmonitor.db"
    
    LONG_CHAU_LOGIN_URL: str = "https://bapp.frt.vn/app/frt-gscmr-long-chau"
    LONG_CHAU_AUTH_DOMAIN: str = "bapp.frt.vn"
    LONG_CHAU_APP_BASE_URL: str = "https://bapp.frt.vn"
    
    
    VACCINE_LOGIN_URL: str = "https://ptt-public.frt.vn/app/frt-gscmr-vaccine"
    VACCINE_AUTH_DOMAIN: str = "ptt-public.frt.vn"
    VACCINE_APP_BASE_URL: str = "https://ptt-public.frt.vn"
    VACCINE_API_ENDPOINT: str = "https://ptt-public.frt.vn/api/v2/queries/query_datasource_plus_25bebdb08d3246899b15e196487b557b_2926f2eb5ca7476a971ae4d737df6e32"
    VACCINE_APP_ID: str = "app_fb5650a52754444cb87ee1e0c82b290b"

    class Config:
        env_file = ".env"

settings = Settings()

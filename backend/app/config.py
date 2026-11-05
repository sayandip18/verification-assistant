from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://bllro:bllro@localhost:5432/bllro"
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 480
    cookie_name: str = "bllro_session"
    cookie_secure: bool = False
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    blob_backend: str = "local"
    blob_local_dir: str = "blob-data"
    s3_endpoint: str = "http://127.0.0.1:9000"
    s3_access_key: str = "bllro"
    s3_secret_key: str = "bllrosecret"
    s3_bucket: str = "bllro-documents"
    s3_region: str = "us-east-1"

    seed_officer_email: str = "officer@bllro.local"
    seed_officer_password: str = "changeme"
    seed_officer_name: str = "Demo Inspector"
    seed_officer_employee_id: str = "BLLRO-001"

    tesseract_cmd: str = ""
    ocr_langs: str = "eng+ben"
    ocr_max_pages: int = 8
    ocr_pdf_scale: float = 2.0
    ocr_min_text_chars: int = 40
    ocr_max_bytes: int = 15 * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

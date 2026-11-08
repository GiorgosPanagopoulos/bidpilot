from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongo_db_name: str = Field("bidpilot", alias="MONGO_DB_NAME")
    chroma_path: str = Field("./chroma_data", alias="CHROMA_PATH")
    ted_api_base: str = Field("https://api.ted.europa.eu/v3", alias="TED_API_BASE")
    # ISO 3166 alpha-3 buyer country filter for TED; empty = all countries
    ted_buyer_country: str = Field("GRC", alias="TED_BUYER_COUNTRY")

    # matching weights
    weight_semantic: float = Field(0.6, alias="WEIGHT_SEMANTIC")
    weight_rule: float = Field(0.4, alias="WEIGHT_RULE")
    match_top_k: int = Field(20, alias="MATCH_TOP_K")
    budget_feasibility_factor: float = Field(2.0, alias="BUDGET_FEASIBILITY_FACTOR")

    # ingestion schedule (cron expression)
    ingest_cron: str = Field("0 6 * * *", alias="INGEST_CRON")

    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Drafting agent model; override via AGENT_MODEL env var.
    agent_model: str = Field("claude-sonnet-4-5", alias="AGENT_MODEL")

    # auth
    secret_key: str = Field(..., alias="SECRET_KEY", min_length=32)
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # comma-separated list of allowed browser origins
    cors_origins: str = Field("http://localhost:5173", alias="CORS_ORIGINS")

    # public demo account; empty DEMO_EMAIL disables POST /auth/demo
    demo_email: str = Field("", alias="DEMO_EMAIL")
    demo_daily_drafts: int = Field(2, alias="DEMO_DAILY_DRAFTS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

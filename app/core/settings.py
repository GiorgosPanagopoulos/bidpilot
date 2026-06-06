from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongo_db_name: str = Field("bidpilot", alias="MONGO_DB_NAME")
    chroma_path: str = Field("./chroma_data", alias="CHROMA_PATH")
    ted_api_base: str = Field("https://api.ted.europa.eu/v3", alias="TED_API_BASE")

    # matching weights
    weight_semantic: float = Field(0.6, alias="WEIGHT_SEMANTIC")
    weight_rule: float = Field(0.4, alias="WEIGHT_RULE")
    match_top_k: int = Field(20, alias="MATCH_TOP_K")
    budget_feasibility_factor: float = Field(2.0, alias="BUDGET_FEASIBILITY_FACTOR")

    # ingestion schedule (cron expression)
    ingest_cron: str = Field("0 6 * * *", alias="INGEST_CRON")

    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # drafting agent
    agent_model: str = Field("claude-sonnet-4-6", alias="AGENT_MODEL")


settings = Settings()

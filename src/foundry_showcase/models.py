"""Contracts for publishable catalog metadata, not executable AI workloads."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Audience = Literal["executive", "architect", "developer", "csa"]
Category = Literal[
    "models",
    "agents",
    "rag",
    "vision-documents",
    "voice",
    "media-generation",
    "fine-tuning",
    "evaluation-safety-observability",
    "enterprise-integrations",
]
NonEmptyText = Annotated[str, Field(min_length=1)]


class MetadataModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        str_strip_whitespace=True,
    )


class Capability(MetadataModel):
    id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]*$")]
    category: Category
    title: NonEmptyText
    summary: NonEmptyText
    audiences: Annotated[list[Audience], Field(min_length=1)]
    scenario: NonEmptyText
    business_value: NonEmptyText
    architecture_note: NonEmptyText
    learning_exercise: NonEmptyText
    evidence_to_collect: NonEmptyText
    guardrails: Annotated[list[NonEmptyText], Field(min_length=1)]
    synthetic_example: NonEmptyText
    tags: Annotated[list[NonEmptyText], Field(min_length=1)]
    deployment_status: Literal["not_deployed"]
    execution_enabled: Literal[False]
    source_verification: Literal["pending"]


class Catalog(MetadataModel):
    schema_version: Literal[1]
    title: NonEmptyText
    data_classification: Literal["synthetic"]
    content_notice: NonEmptyText
    source_verification: Literal["pending"]
    live_demos_enabled: Literal[False]
    capabilities: Annotated[list[Capability], Field(min_length=1)]

    @model_validator(mode="after")
    def require_unique_ids(self) -> Self:
        identifiers = [capability.id for capability in self.capabilities]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Capability identifiers must be unique.")
        return self


class Liveness(MetadataModel):
    status: Literal["ok"] = "ok"


class Readiness(MetadataModel):
    status: Literal["ready", "not_ready"]
    scope: Literal["local_catalog_only"] = "local_catalog_only"
    live_demos_enabled: Literal[False] = False
    detail: str | None = None


class PlannedConstraints(MetadataModel):
    enforcement: Literal["not_implemented"] = "not_implemented"
    visitor_access: Literal["approved_visitors_email_otp"] = (
        "approved_visitors_email_otp"
    )
    session_minutes: Literal[15] = 15
    sessions_per_visitor_per_day: Literal[3] = 3
    monthly_budget_target_usd: Literal[100] = 100


class FoundationStatus(MetadataModel):
    stage: Literal["local_foundation"] = "local_foundation"
    readiness_scope: Literal["local_catalog_only"] = "local_catalog_only"
    deployment_status: Literal["not_deployed"] = "not_deployed"
    live_demos_enabled: Literal[False] = False
    authentication_implemented: Literal[False] = False
    visitor_approval_implemented: Literal[False] = False
    session_accounting_implemented: Literal[False] = False
    cloud_security_state_implemented: Literal[False] = False
    live_sdk_execution_implemented: Literal[False] = False
    source_verification: Literal["pending"] = "pending"
    planned_constraints: PlannedConstraints = Field(default_factory=PlannedConstraints)

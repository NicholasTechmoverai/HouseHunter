from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, List, Union
import re

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}$"
)


class VerificationCodeRequest(BaseModel):
    identifier: str
    type: Literal["email", "phone", "2fa"]
    code: Optional[Union[str, List[str]]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # ---- NORMALIZE IDENTIFIER ----
    @field_validator("identifier", mode="before")
    @classmethod
    def clean_identifier(cls, v: str) -> str:
        return v.strip().lower()

    # ---- NORMALIZE CODE (string OR list) ----
    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v):
        if v is None:
            return None

        # Frontend sends ["5","2","3","4","5","4"]
        if isinstance(v, list):
            if not all(isinstance(d, str) and d.isdigit() for d in v):
                raise ValueError("Code must contain only digits")
            v = "".join(v)

        if not isinstance(v, str):
            raise ValueError("Invalid code format")

        v = v.strip()

        if len(v) != 6:
            raise ValueError("Code must be exactly 6 digits")

        if not v.isdigit():
            raise ValueError("Code must be numeric")

        return v

    # ---- CROSS-FIELD VALIDATION ----
    @model_validator(mode="after")
    def validate_identifier_by_type(self):
        if self.type == "email":
            if not EMAIL_REGEX.match(self.identifier):
                raise ValueError("Invalid email format")
        return self

    @property
    def cleaned(self) -> dict:
        return {
            "identifier": self.identifier,
            "type": self.type,
            "code": self.code,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }

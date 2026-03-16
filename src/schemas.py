import re
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    username: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9]+$",
        min_length=4,
        max_length=20,
        description="Только буквы и цифры, 4–20 символов"
    )
    email: EmailStr
    password: str = Field(...)
    confirm_password: str = Field(...)
    age: int = Field(..., ge=18, le=100, description="Возраст от 18 до 100 лет")

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")

        if not re.search(r"[0-9]", v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")

        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Пароль должен содержать хотя бы один спецсимвол (!@#$%^&*)")

        return v

    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Пароли не совпадают")
        return self
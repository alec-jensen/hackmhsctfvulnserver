"""Pydantic schemas for API responses."""
from pydantic import BaseModel
from typing import Optional


class UserInfo(BaseModel):
    password: str


class AdminResponse(BaseModel):
    flag: str


class SQLQueryResponse(BaseModel):
    columns: list[str]
    result: list[list[str]]


class ErrorResponse(BaseModel):
    detail: str

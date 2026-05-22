"""
Pydantic 数据模型
"""

from pydantic import BaseModel
from typing import Optional


class ItemCreate(BaseModel):
    name: str
    price: float
    purchase_date: str
    category: str = "其他"
    note: str = ""
    image_url: str = ""
    retirement_date: str = ""
    warranty_date: str = ""
    calc_method: str = "按时间"


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    purchase_date: Optional[str] = None
    category: Optional[str] = None
    note: Optional[str] = None
    image_url: Optional[str] = None
    retirement_date: Optional[str] = None
    warranty_date: Optional[str] = None
    calc_method: Optional[str] = None


class SubscriptionCreate(BaseModel):
    name: str
    start_date: str
    billing_cycle: str
    price_per_cycle: float
    auto_renew: bool = False


class SubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[str] = None
    billing_cycle: Optional[str] = None
    price_per_cycle: Optional[float] = None
    auto_renew: Optional[bool] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ChangeUsernameRequest(BaseModel):
    new_username: str

from pydantic import BaseModel
from typing import List, Optional

class ProductImageResponse(BaseModel):
    id: int
    image_url: str
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    category_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    price_per_unit: float
    quantity_available: float
    unit_type: str
    district: str

class ProductResponse(BaseModel):
    id: int
    farmer_id: int
    category_id: Optional[int]
    title: str
    description: Optional[str]
    price_per_unit: float
    quantity_available: float
    unit_type: str
    district: str
    is_active: bool
    images: List[ProductImageResponse] = []

    class Config:
        from_attributes = True
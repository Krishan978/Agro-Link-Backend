from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_db
from app.models import Product, ProductImage, User
from app.schemas import ProductCreate, ProductResponse
from app.auth import get_current_user, RoleChecker

router = APIRouter(prefix="/api/products", tags=["Products Pipeline"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(RoleChecker(["FARMER", "ADMIN"]))
):
    db_product = Product(
        farmer_id=current_user.id,
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
        price_per_unit=payload.price_per_unit,
        quantity_available=payload.quantity_available,
        unit_type=payload.unit_type,
        district=payload.district
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    district: Optional[str] = None, 
    db: AsyncSession = Depends(get_db)
):
    query = select(Product).where(Product.is_active == True).options(selectinload(Product.images))
    if district:
        query = query.where(Product.district == district)
        
    result = await db.execute(query)
    return result.scalars().all()
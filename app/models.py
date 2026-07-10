from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="FARMER")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, nullable=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price_per_unit = Column(Float, nullable=False)
    quantity_available = Column(Float, nullable=False)
    unit_type = Column(String, nullable=False)
    district = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    images = relationship("ProductImage", back_populates="product", lazy="selectin")

class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    image_url = Column(String, nullable=False)
    product = relationship("Product", back_populates="images")
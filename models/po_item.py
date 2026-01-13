from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship, declarative_base

# Creating a single Base to avoid "Multiple Classes Found" error
Base = declarative_base()

class StyleMaster(Base):
    __tablename__ = 'style_master'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ean = Column(String, unique=True, index=True)
    style_no = Column(String)
    buyer = Column(String)
    
    # Relationship back to PO items
    po_items = relationship("POItem", back_populates="style_master_ref")

class POItem(Base):
    __tablename__ = 'po_items'
    
    # Using STRING for ID to allow long PO numbers (e.g., 5002460652)
    id = Column(String, primary_key=True)
    po_number = Column(String)
    ean = Column(String, ForeignKey('style_master.ean', ondelete='SET NULL'), index=True)
    
    filename = Column(String)
    po_date = Column(String)
    style_no = Column(String) # For fallback if StyleMaster link fails
    buyer = Column(String)
    location = Column(String)
    delivery_date = Column(String)
    quantity = Column(Integer, default=0)
    
    # Operations Tracking
    status = Column(String, default='Pending')
    is_amended = Column(Boolean, default=False)
    ex_factory_date = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship back to StyleMaster
    style_master_ref = relationship("StyleMaster", back_populates="po_items")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

"""
Style Master Model - EAN to Style/Buyer mappings
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class StyleMaster(Base):
    """
    Style Master table - EAN to Style/Buyer mappings
    id is PRIMARY KEY, ean is UNIQUE (used for foreign key relationship)
    """
    __tablename__ = 'style_master'
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # Standard ID as PK
    ean = Column(String, unique=True, nullable=False, index=True)  # EAN is UNIQUE, used for FK
    style_no = Column(String)
    buyer = Column(String)
    
    # Relationship: One style_master can have many po_items
    po_items = relationship("POItem", back_populates="style_master_ref", foreign_keys="POItem.ean")
    
    def to_dict(self):
        return {
            'id': self.id,
            'ean': self.ean,
            'style_no': self.style_no,
            'buyer': self.buyer
        }
    
    def __repr__(self):
        return f'<StyleMaster {self.ean}>'



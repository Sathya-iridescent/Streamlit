"""
PO Item Model - Purchase Order Items
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from database import Base


class POItem(Base):
    """
    Purchase Order Items table
    Connected to style_master via EAN foreign key
    """
    __tablename__ = 'po_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key to style_master (EAN links to style_master.ean)
    ean = Column(String, ForeignKey('style_master.ean', ondelete='SET NULL'), nullable=True, index=True)
    
    # Relationship: Many po_items belong to one style_master
    style_master_ref = relationship("StyleMaster", back_populates="po_items", foreign_keys=[ean])
    
    # File & PO Information
    filename = Column(String)
    po_number = Column(String, index=True)
    po_date = Column(String)
    
    # Product Information (can be populated from style_master via JOIN)
    style_no = Column(String, index=True)  # Denormalized for performance
    ocn = Column(String)
    buyer = Column(String, index=True)  # Denormalized for performance
    description = Column(String)
    
    # Delivery Information
    delivery_date = Column(String, index=True)
    delivery_month = Column(String)
    location = Column(String)
    
    # Quantity Information
    caselot = Column(Integer)
    quantity = Column(Integer)
    no_of_boxes = Column(Integer)
    
    # Factory Information
    factory = Column(String)
    ex_factory_date = Column(String, index=True)
    factory_remarks = Column(String)
    
    # Dispatch Information
    dispatched_box = Column(Integer, default=0)
    dispatched_qty = Column(Integer, default=0)
    balance = Column(Integer, default=0)
    status = Column(String, default='Pending', index=True)
    dispatch_date = Column(String)
    transporter = Column(String)
    
    # GRN Information
    grn_date = Column(String)
    grn_status = Column(String)
    
    # Metadata
    is_revised = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Composite indexes for performance
    __table_args__ = (
        Index('idx_po_ean', 'po_number', 'ean'),
        Index('idx_status_exfactory', 'status', 'ex_factory_date'),
        Index('idx_po_number_ean', 'po_number', 'ean'),  # For duplicate prevention
    )

    parent_id = Column(Integer, nullable=True)
    is_manual = Column(Boolean, default=False)
    is_amended = Column(Boolean, default=False)
    child_seq = Column(Integer, default=0)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'filename': self.filename,
            'po_number': self.po_number,
            'po_date': self.po_date,
            'style_no': self.style_no,
            'ocn': self.ocn,
            'buyer': self.buyer,
            'description': self.description,
            'delivery_date': self.delivery_date,
            'delivery_month': self.delivery_month,
            'location': self.location,
            'caselot': self.caselot,
            'quantity': self.quantity,
            'no_of_boxes': self.no_of_boxes,
            'factory': self.factory,
            'ex_factory_date': self.ex_factory_date,
            'factory_remarks': self.factory_remarks or "",
            'dispatched_box': self.dispatched_box,
            'dispatched_qty': self.dispatched_qty,
            'balance': self.balance,
            'status': self.status,
            'dispatch_date': self.dispatch_date or "",
            'transporter': self.transporter,
            'grn_date': self.grn_date,
            'grn_status': self.grn_status,
            'is_revised': self.is_revised,
            'ean': self.ean,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            "is_amended": self.is_amended,
            "is_manual": self.is_manual,
            "status": self.status,
        }
    
    def __repr__(self):
        return f'<POItem {self.po_number}>'



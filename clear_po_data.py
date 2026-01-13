from database import get_db_session
from models.po_item import POItem

with get_db_session() as session:
    session.query(POItem).delete()
    session.commit()


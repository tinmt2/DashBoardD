import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.models.ticket import Ticket

db = SessionLocal()
t = db.query(Ticket).first()
if t:
    print(t.created_at)
else:
    print('No tickets')

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.database import Base, engine

print("Dropping all PostgreSQL tables...")
Base.metadata.drop_all(bind=engine)
print("Recreating tables with new schema...")
Base.metadata.create_all(bind=engine)
print("Done!")

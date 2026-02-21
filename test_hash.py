import sys
from passlib.context import CryptContext

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    print("Hashing 'test'")
    hash_val = pwd_context.hash("test")
    print("Hash success:", hash_val)
except Exception as e:
    import traceback
    traceback.print_exc()

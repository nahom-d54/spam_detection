from app.core.security import hash_password, verify_password

# long password > 72 bytes
long_password = "A" * 200

print("password len:", len(long_password))

h = hash_password(long_password)
print("hashed:", h)

ok = verify_password(long_password, h)
print("verify ok:", ok)

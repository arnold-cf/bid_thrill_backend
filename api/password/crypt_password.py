import bcrypt

def hash_password(password):
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed_password

def unhash_password(password, hashed_pass):
    return bcrypt.checkpw(password, hashed_pass)

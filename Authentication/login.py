import sqlite3
from flask_bcrypt import Bcrypt
from pathlib import Path


def check_login(username, password):
    bcrypt = Bcrypt()

    con = sqlite3.connect(Path('Authentication/users.sqlite'))
    cur = con.cursor()
    result = cur.execute(f"SELECT id, username, password FROM user WHERE username = '{username}' ").fetchone()
    con.close()

    if result and bcrypt.check_password_hash(result[2], password):
        return result
    return None
    
def get_user(id):
    con = sqlite3.connect(Path('Authentication/users.sqlite'))
    cur = con.cursor()
    result = cur.execute(f"SELECT id, username, password FROM user WHERE id = '{id}' ").fetchone()
    con.close()
    return result

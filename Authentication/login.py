import sqlite3
from flask_bcrypt import Bcrypt
from pathlib import Path


def connect_db():
    conn = sqlite3.connect(Path('Authentication/users.sqlite'))
    cursor = conn.cursor()
    return conn, cursor

def check_login(username, password):
    bcrypt = Bcrypt()
    conn, cursor = connect_db()
    result = cursor.execute(f"SELECT * FROM user \
                              WHERE username = '{username}';").fetchone()
    conn.close()
    if result and bcrypt.check_password_hash(result[2], password):
        return result
    return None
    
def get_user(id):
    conn, cursor = connect_db()
    result = cursor.execute(f"SELECT * FROM user \
                              WHERE id = '{id}';").fetchone()
    conn.close()
    return result

def add_user(username, password, name, location):
    conn, cursor = connect_db()
    bcrypt = Bcrypt()
    hashed_pw = bcrypt.generate_password_hash(password).decode('ascii')

    result = cursor.execute(f"SELECT COUNT(username) FROM user\
                             WHERE username = '{username}';").fetchone()
    if result[0] > 0:
        sql = f"UPDATE user SET password = '{hashed_pw}', name = '{name}', \
                location = '{location}', temp_pw = 1 \
                WHERE username = '{username}';"
    else:
        sql = f"INSERT INTO user (username, password, temp_pw, name, location) \
                VALUES ('{username}', '{hashed_pw}', 1, '{name}', '{location}');"
        
    cursor.execute(sql)
    conn.commit()
    conn.close()

def change_password(user_id, new_password):
    bcrypt = Bcrypt()
    hashed_pw = bcrypt.generate_password_hash(new_password).decode('ascii')
    sql = f"UPDATE user SET password = '{hashed_pw}', temp_pw = 0 \
            WHERE id = {user_id};"
    conn, cursor = connect_db()
    cursor.execute(sql)
    conn.commit()
    conn.close()


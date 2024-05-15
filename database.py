import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE = "sqlite:///./bank.db"
ENG = create_engine(DATABASE)

# These users are here just so the database is populated with something. This should not be seen as part of the vulnerabilities.
USERS = [
    {"username": "julio", "password":"123456", "first_name":"Julio", "last_name": "Araujo", "email":"julio@vbank.api", "balance":'9225.91', "account_number":'1001'},
    {"username": "thiago", "password":"mdr0g123!", "first_name":"Thiago", "last_name": "Araujo", "email":"thiago@vbank.api", "balance":'6377.34', "account_number":'1002'},
    {"username": "bido", "password":"b1d0wsg4uch0", "first_name":"Eduardo", "last_name": "Bido", "email":"bido@vbank.api", "balance":'3967.12', "account_number":'1004'},
    {"username": "pierre", "password":"l3m0tD3p@ss3", "first_name":"Pierre", "last_name": "Victorion", "email":"pierre@lemeilleurmail.fr", "balance":'122001.48', "account_number":'1005'},
    {"username": "john", "password":"myreallyLongpass.!", "first_name":"John", "last_name": "Smith", "email":"john@mymayl.us", "balance":'41011.59', "account_number":'1006'},
    {"username": "harold", "password":"letmein123.!", "first_name":"Harold", "last_name": "Robinson", "email":"harold@mymayl.us", "balance":'33022.38', "account_number":'1007'}
    ]

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENG)

def getDB():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def createDatabase():
    try:
        conn = sqlite3.connect(DATABASE.split("/")[-1])        
        cursor = conn.cursor()
        print("INFO:     Database created and/or initialized.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                balance NUMERIC,
                account_number INTEGER UNIQUE
            )
        ''')
        conn.commit()
        print("INFO:     Table 'users' created and/or loaded.")

    except sqlite3.Error as sqlite_error:
        print(f"Error: {sqlite_error}")
    
    try:
        print("INFO:     Users created and/or loaded.")
        for dict_object in USERS:
            values = []
            for value in dict_object.values():
                values.append(value)
            cursor.execute(f'''
                    INSERT INTO users (
                            username,
                            password,
                            first_name,
                            last_name,
                            email,
                            balance,
                            account_number
                            ) 
                    VALUES (
                            '{values[0]}',
                            '{values[1]}',
                            '{values[2]}',
                            '{values[3]}',
                            '{values[4]}',
                            {values[5]},
                            {values[6]});
            ''')
            conn.commit()

    except sqlite3.Error as sqlite_error:
        print(f"Error: {sqlite_error}")

    try:
        print("INFO:     Database created and/or initialized.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                orig_account_number INTEGER,
                dest_account_number INTEGER,
                amount NUMERIC(20, 2)
            )
        ''')

        conn.commit()
        print("INFO:     Table 'transactions' created and/or loaded.")
        
    except sqlite3.Error as sqlite_error:
        print(f"Error: {sqlite_error}")
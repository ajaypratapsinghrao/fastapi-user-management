from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import psycopg2

app = FastAPI()

# PostgreSQL connection parameters
db_params = {
    "dbname": "your_db_name",
    "user": "your_db_user",
    "password": "your_db_password",
    "host": "your_db_host",
    "port": "your_db_port"
}

def execute_query(query, values=None):
    connection = psycopg2.connect(**db_params)
    cursor = connection.cursor()
    cursor.execute(query, values)
    connection.commit()
    cursor.close()
    connection.close()

def fetch_query(query, values=None):
    connection = psycopg2.connect(**db_params)
    cursor = connection.cursor()
    cursor.execute(query, values)
    result = cursor.fetchall()
    connection.commit()
    cursor.close()
    connection.close()
    return result

def create_tables():
    create_users_table_query = """
    CREATE TABLE IF NOT EXISTS Users (
        user_id SERIAL PRIMARY KEY,
        first_name VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        password VARCHAR(100),
        phone VARCHAR(20) UNIQUE
    );
    """
    create_profile_table_query = """
    CREATE TABLE IF NOT EXISTS Profile (
        profile_id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES Users(user_id),
        profile_picture TEXT
    );
    """
    execute_query(create_users_table_query)
    execute_query(create_profile_table_query)

@app.post("/register")
async def register_user(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(...),
    profile_picture: UploadFile = File(...)
):
    try:
        create_tables()
        query = "INSERT INTO Users (first_name, email, password, phone) VALUES (%s, %s, %s, %s) RETURNING user_id;"
        values = (full_name, email, password, phone)
        user_id = fetch_query(query, values)[0][0]

        if profile_picture:
            profile_picture_data = profile_picture.file.read()
            query = "INSERT INTO Profile (user_id, profile_picture) VALUES (%s, %s);"
            values = (str(user_id), profile_picture_data)
            execute_query(query, values)

        return {"message": "User registered successfully"}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}")
async def get_user(user_id: int):
    try:
        query = "SELECT Users.first_name, Users.email, Users.phone, Profile.profile_picture FROM Users LEFT JOIN Profile ON Users.user_id = Profile.user_id WHERE Users.user_id = %s;"
        values = (user_id,)
        result = fetch_query(query, values)

        if not result:
            return HTTPException(status_code=404, detail="User not found")
        
        user_details = {
            "full_name": result[0][0],
            "email": result[0][1],
            "phone": result[0][2],
            "profile_picture": result[0][3]
        }
        return user_details
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

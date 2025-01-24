import os
import dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy import text, Table, Column, Integer, String, MetaData, Float
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import insert
from llama_index.core.utilities.sql_wrapper import SQLDatabase
# from llama_index import ServiceContext
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.openai import OpenAI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker
from faker import Faker
import random
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query_str: str

dotenv.load_dotenv()

HOST = 'localhost'
DBPASSWORD = 'password'
DBUSER = 'postgres'
DBNAME = 'postgres'
DB_PORT = '15438'

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_random_data():
    fake = Faker()

    id = random.randint(1, 1000000)
    name = fake.first_name()
    lastname = fake.last_name()
    height = np.round(random.uniform(140, 220), 2)  # assuming height is in meters
    weight = np.round(random.uniform(50, 100), 2)   # assuming weight is in kilos

    return {"id": id, "name": name, "lastname": lastname, "height": height, "weight": weight}

@app.get("/helloworld")
async def helloworld():
    return {"message": "Hello World"}

@app.get("/createTable")
async def createTable():
    conn_str = "postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(
        conn_str.format(
            user = DBUSER,
            host = HOST,
            port = DB_PORT,
            password = DBPASSWORD,
            database = DBNAME)
    )
    meta = MetaData()

    students = Table(
        'students', meta,
        Column('id', Integer, primary_key = True),
        Column('name', String),
        Column('lastname', String),
        Column('height', Float),
        Column('weight', Float)
    )
    meta.create_all(engine)

    json_compatible_item_data = jsonable_encoder({'message' : 'complete'})
    return JSONResponse(content=json_compatible_item_data)

@app.get("/removeTable")
async def removeTable():

    conn_str = "postgresql://{user}:{password}@{host}:{port}/{database}"

    engine = create_engine(
        conn_str.format(
            user = DBUSER,
            host = HOST,
            port = DB_PORT,
            password = DBPASSWORD,
            database = DBNAME)
    )
    Session = sessionmaker(bind=engine)

    # Create insertion SQL
    with Session() as session :
        session.execute(text("""DROP TABLE "students" """))
        session.commit()

    json_compatible_item_data = jsonable_encoder({'message' : 'complete'})
    return JSONResponse(content=json_compatible_item_data)

@app.get("/getInfo")
async def getInfo():

    conn_str = "postgresql://{user}:{password}@{host}:{port}/{database}"

    engine = create_engine(
        conn_str.format(
            user = DBUSER,
            host = HOST,
            port = DB_PORT,
            password = DBPASSWORD,
            database = DBNAME)
    )

    metadata = MetaData()
    metadata.reflect(bind=engine)
    result = {
        'attr' : {}
    }
    for table in metadata.tables:
        print("Table name: ", table)
        print("Table details: ")
        # retrieving table details
        result['table_name'] = table
        for column in metadata.tables[table].c:
            result['attr'][column.name] = {
                'name' : column.name,
                'type' : str(column.type)
            }
    json_compatible_item_data = jsonable_encoder(result)
    return JSONResponse(content=json_compatible_item_data)

@app.get("/addRandomData")
async def addRandomData():

    conn_str = "postgresql://{user}:{password}@{host}:{port}/{database}"
    data = []
    for i in range(10):
        data.append(generate_random_data())

    engine = create_engine(
        conn_str.format(
            user = DBUSER,
            host = HOST,
            port = DB_PORT,
            password = DBPASSWORD,
            database = DBNAME)
    )
    metadata = MetaData()
    metadata.reflect(bind=engine)
    students = Table('students', metadata)

    Session = sessionmaker(bind=engine)

    # Create insertion SQL
    stmt = (insert(students).values(data))
    with Session() as session :
        session.execute(stmt)
        session.commit()

    print("All records inserted.")
    json_compatible_item_data = jsonable_encoder(data)
    return JSONResponse(content=json_compatible_item_data)

def get_database_connection():
    """Create and return a database connection."""
    conn_str = "postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(
        conn_str.format(
            user=DBUSER,
            host=HOST,
            port=DB_PORT,
            password=DBPASSWORD,
            database=DBNAME
        )
    )
    return SQLDatabase(engine)

@app.get("/getAllData/{table}")
async def get_all_data(table: str):
    """Retrieve all data from the specified table."""
    try:
        # Basic SQL injection prevention
        allowed_tables = ['your_table1', 'your_table2']  # Add your actual table names
        if table not in allowed_tables:
            raise HTTPException(
                status_code=400,
                detail=f"Access to table '{table}' is not allowed"
            )
        
        sql_database = get_database_connection()
        query_result = sql_database.run_sql(f"SELECT * FROM {table}")
        
        if not query_result or len(query_result) < 2:
            return JSONResponse(content={"message": "No data found"})
        
        return JSONResponse(content=jsonable_encoder(query_result[1]))
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@app.get("/get_all_table/")
async def getAllData():

    conn_str = "postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(
        conn_str.format(
            user = DBUSER,
            host = HOST,
            port = DB_PORT,
            password = DBPASSWORD,
            database=DBNAME)
    )
    sql_database = SQLDatabase(engine)
    res = sql_database.run_sql("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
                               """)
    print(res[1])
    result = []
    # for i in res[1]['result'] :
    #     result.append({
    #         'id' : i[0],
    #         'name' : i[1],
    #         'lastname' : i[2],
    #         'height' : i[3],
    #         'weight' : i[4]
    #     })
    json_compatible_item_data = jsonable_encoder(res[1])
    return JSONResponse(content=json_compatible_item_data)


def query_databae(q_string):
    print(q_string)
    conn_str = "postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(
        conn_str.format(
            user = DBUSER,
            host = HOST,
            port = DB_PORT,
            password = DBPASSWORD,
            database=DBNAME)
    )
    sql_database = SQLDatabase(engine)
    res = sql_database.run_sql(f"{q_string}")
    return res[1]

# @app.get("/queryWithPrompt")
# async def queryWithPrompt(query_str : str = 'Write SQL in PostgresSQL format. ใช้เฉพาะข้อมูลที่มีอยู่ใน Database เท่านั้น. คำถาม คือ เคยเป็นกุ้งหรือไม่'):

#     llm = OpenAI(model="gpt-4o-mini",temperature=0, max_tokens=1000)

#     conn_str = "postgresql://{user}:{password}@{host}:{port}/{database}"
#     engine = create_engine(
#         conn_str.format(
#             user = DBUSER,
#             host = HOST,
#             port = DB_PORT,
#             password = DBPASSWORD,
#             database=DBNAME)
#     )
#     # service_context = ServiceContext.from_defaults(
#     #     llm=llm
#     # )
#     sql_database = SQLDatabase(engine)

#     query_engine = NLSQLTableQueryEngine(
#         sql_database=sql_database,
#         llm=llm,
#         sql_only=True


#     )

#     query_prompt = (query_str)
#     try :
#         response = query_engine.query(query_prompt)
#         print(response)
#         # result = response.response
#         # sql_query = response.metadata['sql_query'],
#         # query_result = query_databae(response.metadata['sql_query'])
#         result = {
#             "result": response.response,
#             "sql_query": response.metadata['sql_query'],
#             "query_result":query_databae(response.metadata['sql_query'])
#         }
#         json_compatible_item_data = jsonable_encoder(result)
#         return JSONResponse(content=json_compatible_item_data)


#     except :
#         result = {
#             "result": 'Bad Prompt',
#             "sql_query": None
#         }

#         json_compatible_item_data = jsonable_encoder(result)
#         return JSONResponse(content=json_compatible_item_data)


@app.post("/queryWithPrompt")
async def queryWithPrompt(request: QueryRequest):
    query_str = request.query_str
    try:
        llm = OpenAI(model="gpt-4o-mini", temperature=0, max_tokens=1000)

        conn_str = "postgresql://{user}:{password}@{host}:{port}/{database}"
        engine = create_engine(
            conn_str.format(
                user=DBUSER,
                host=HOST,
                port=DB_PORT,
                password=DBPASSWORD,
                database=DBNAME
            )
        )
        # ปรับ query string ให้จำกัดขอบเขตการตอบ
        restricted_query = f"""
You are a PostgreSQL query generator. You MUST follow these rules strictly:

Core Purpose

1. Generate SQL queries that ONLY retrieve data
2. Ignore any visualization or presentation requests
3. Focus on getting the correct data points for further processing

Query Response Guidelines

What to Include

1. Pure SELECT statements for data retrieval
2. Necessary JOIN operations to connect related data
3. Filtering conditions in WHERE clauses
4. Data aggregations when specifically requested
5. Proper column selection based on the data needs

What to Ignore

1. Requests for creating charts or graphs
2. Requests for formatting data tables
3. Requests for data visualization
4. Any CREATE TABLE statements, even for temporary results
5. Any presentation-related considerations


Primary Constraints
1. Generate ONLY SELECT statements
2. Do NOT generate any DDL statements (CREATE, ALTER, DROP, etc.)
3. Do NOT generate any DML statements (INSERT, UPDATE, DELETE, etc.)
4. Do NOT include any database modification commands
5. Avoid any statements that could potentially modify data

STRICT RULES:
1. Do NOT attempt to answer questions outside database
2. Do NOT make assumptions about data
3. Do NOT provide general information or explanations

Please generate SQL query with these requirements:
    1. Do not use aliases or abbreviations for table names
    2. Write full table names in the SELECT, FROM, JOIN, WHERE, GROUP BY and all other clauses
    3. Keep the query readable by using proper indentation and line breaks
    4. Include clear comments explaining the purpose of each major section
    5. Use clear and descriptive names for any calculated fields
    6. Make sure column references explicitly include their full table names

Column descriptions:

workingstatus: คือสถานะการทำงาน มี Working | LayOff | Resign
income: คือ รายได้
incomecode: คือ รหัสของประเภทรายได้
incomename คือ ชื่อของประเภทรายได้ 

Question: {query_str}

Tip:
1. PostgreSQL has AGE() function for time differences
2. Don't use WHERE MAX statements because it get the error and invalid postgrest syntax

Generate ONLY a PostgreSQL query , otherwise return the error message and explain why got the error

"""

        sql_database = SQLDatabase(engine)

        query_engine = NLSQLTableQueryEngine(
            sql_database=sql_database,
            llm=llm,
            sql_only=True
        )

        response = query_engine.query(restricted_query)
        print(response)
        # ตรวจสอบว่าคำตอบเป็น error message หรือไม่
        if "Cannot answer" in response.response:
            result = {
                "result": response.response,
                "sql_query": None,
                "query_result": None
            }
        else:
            result = {
                "result": response.response,
                "sql_query": response.metadata['sql_query'],
                "query_result": query_databae(response.metadata['sql_query'])
            }

        return JSONResponse(content=jsonable_encoder(result))

    except Exception as e:
        result = {
            "result": 'Bad Prompt or Error '+response.response,
            "sql_query": None,
            "error": str(e)
        }

        return JSONResponse(content=jsonable_encoder(result))
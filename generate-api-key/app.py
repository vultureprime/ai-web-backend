import boto3
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import module
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

client = boto3.client(
    'apigateway',
    region_name = 'ap-southeast-1')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class create_request(BaseModel):
    plan_name: str
    user: str

@app.get("/")
def root():
    result = {
        "message" : "hello world"
    }
    return JSONResponse(content=result, status_code=200)

# @app.get("/usage") #not complete
# def get_key_usage():
#     today_date = datetime.today().strftime('%Y-%m-%d')
#     module.get_plan_data_by_name()
#     response = client.get_usage(
#         usagePlanId='demo',
#         keyId='demo',
#         startDate=today_date,
#         endDate=today_date
#     )
#     usage = response['items']['demo'][-1]
#     result = {
#         "usage" : usage[0],
#         "remain" : usage[1]
#     }

#     return JSONResponse(content=result, status_code=200)
    
@app.get("/plan")
def get_plan():
    res = client.get_usage_plans()
    plan_name_list = []
    for i in res['items']:
        plan_name_list.append({
            "name":i['name']
        })
    return JSONResponse(content=plan_name_list, status_code=200)
    
@app.post("/create_key")
async def create_key(create_request :create_request ):
    res = module.check_user_exist_in_plan(create_request.user,create_request.plan_name)
    if res is True:
        raise HTTPException(status_code=409, detail="Key already exist")
    else:
        response = client.create_api_key(
            name=create_request.user,
            description='for use api',
            enabled=True,
            generateDistinctId=True
        )
        api_key = response['value']
        api_id = response['id']
        try:
            module.add_key_to_plan(api_id,create_request.plan_name)
            result = {
                "value" : api_key
            }
            return JSONResponse(content=result, status_code=200)
        except Exception as e:
            client.delete_api_key(
                apiKey=api_id
            )
            result = {
                "message" : "create failed"
            }
            return JSONResponse(content=result, status_code=500)
    


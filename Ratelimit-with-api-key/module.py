import boto3
import csv

client = boto3.client(
    'apigateway',
    region_name = 'ap-southeast-1')


# def save_data(api_key_information):
#     fieldnames = api_key_information[0].keys()
#     print(fieldnames)
#     with open('db.csv', 'w',newline='') as db:
#         csv_writer = csv.DictWriter(db, fieldnames=fieldnames)
#         csv_writer.writeheader()
#         csv_writer.writerows(api_key_information)
        
def get_plan_data_by_name(plan_name):
    try:
        res = client.get_usage_plans()
        for i in res['items']:
            if i['name'] == plan_name:
                return {
                    "id": i['id']
                }
    except Exception as e:
        print(e)
        
def add_key_to_plan(api_key_id,plan_name):
    plan_id = get_plan_data_by_name(plan_name)['id']
    response = client.create_usage_plan_key(
        usagePlanId=plan_id,
        keyId=api_key_id,
        keyType='API_KEY'
    )
    return response
    
def check_user_exist_in_plan(user,plan_name):
    try:
        res = get_plan_data_by_name(plan_name)
        plan_id = res['id']
        res = client.get_usage_plan_keys(
            usagePlanId = plan_id
        )
        if any(i['name'] == user for i in res['items']):
            return True
        else:
            return False
    except Exception as e:
        print(e)

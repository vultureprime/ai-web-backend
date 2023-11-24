import os 
import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from typing import List
import pydantic
import LocalTemplate 

dotenv.load_dotenv()

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class task_list(pydantic.BaseModel):
    role : str
    task : str

def remove_tag(text,tag_remove=['<question>','<role>','</question>','</role>','</sub-question>']):
    new_text = text.replace("\n",'').strip()
    for i in tag_remove : 
        new_text = new_text.replace(i,'')
    
    return new_text

def text_to_json(text, tag, tag_remove_group):
    text_list = []
    for i in text:
        raw = remove_tag(i,tag_remove=tag_remove_group)
        text_raw = raw.split(tag)
        step_text = text_raw[0].replace('\n','').strip()
        description_text = text_raw[1].replace('\n','').strip()
        text_list.append({'step': step_text,'description': description_text})

    return text_list

@app.post('/breakdown')
def breakdown_question(customer_need : str):
    model_256 = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0.3, max_tokens=256,openai_api_key = OPENAI_API_KEY)
    breakdown_chain = ChatPromptTemplate.from_template(LocalTemplate.get_manager()) | model_256
    result = breakdown_chain.invoke({"question": customer_need})
    arr = result.content.split('<question>')[1:]
    task_list = []
    for i in arr : 
        full_task = remove_tag(i,['<question>','<role>','</question>','</role>','</sub-question>']).strip()
        full_task_list = full_task.split('<sub-question>')
        role = full_task_list[0]
        task = full_task_list[1]
        task_list.append({'role':role,'task':task})

    json_compatible_item_data = jsonable_encoder(task_list)
    return JSONResponse(content=json_compatible_item_data)

@app.post('/build')
def build_task(task_list : List[task_list]):
    model_256 = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0.3, max_tokens=256,openai_api_key = OPENAI_API_KEY)
    frontend_chain = ChatPromptTemplate.from_template(LocalTemplate.get_frontend()) | model_256 
    frontend_result = frontend_chain.invoke({"task": task_list[0].task})
    
    backend_chain = ChatPromptTemplate.from_template(LocalTemplate.get_backend()) | model_256 
    backend_result = backend_chain.invoke({"task": task_list[1].task})

    designer_chain = ChatPromptTemplate.from_template(LocalTemplate.get_designer()) | model_256 
    designer_result = designer_chain.invoke({"task": task_list[2].task})
    
    frontend_text = frontend_result.content.split('<step>')[1:]
    frontend_json = text_to_json(frontend_text,'<description>',['<task>','</task>','<step>','</step>','</description>'])
    backend_text = backend_result.content.split('<step>')[1:]
    backend_json = text_to_json(backend_text,'<description>',['<task>','</task>','<step>','</step>','</description>'])
    designer_text = designer_result.content.split('<step>')[1:]
    designer_json = text_to_json(designer_text,'<description>',['<task>','</task>','<step>','</step>','</description>'])

    result = {
        'raw' : {
            "frontend_task": frontend_result.content, 
            "backend_task": frontend_result.content, 
            "designer_task": frontend_result.content
        },
        'json' : {
            "frontend_task": frontend_json, 
            "backend_task": backend_json, 
            "designer_task": designer_json
        }
    }


    json_compatible_item_data = jsonable_encoder(result)
    return JSONResponse(content=json_compatible_item_data)

@app.post('/conclude')
def build_conclusion(customer_need : str, frontend_task : str, backend_task : str, designer_task : str):
    model_512 = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0.3, max_tokens=512,openai_api_key = OPENAI_API_KEY)
    customer_chain = ChatPromptTemplate.from_template(LocalTemplate.get_conclusion()) | model_512
    customer_result = customer_chain.invoke({
        "customer_need" : customer_need,
        "frontend_task": frontend_task, 
        "backend_task": backend_task, 
        "designer_task": designer_task
    })

    customer_json = remove_tag(customer_result.content,['<conclude>','</conclude>','<text>','</text>'])
    result =  {
        'raw' : customer_result.content,
        'json' : {
            'customer_need' : customer_json
        }
    }
    json_compatible_item_data = jsonable_encoder(result)
    return JSONResponse(content=json_compatible_item_data)


@app.post('/query')
def query_with_chain(question : str):
    customer = question
    model_256 = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0.3, max_tokens=256,openai_api_key = OPENAI_API_KEY)
    model_512 = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0.3, max_tokens=512,openai_api_key = OPENAI_API_KEY)
    PO_Final_Chain = ChatPromptTemplate.from_template(LocalTemplate.get_manager()) | model_256
    result = PO_Final_Chain.invoke({"question": customer})
    # print(result.content)
    arr = result.content.split('<question>')[1:]
    task_list = []
    for i in arr : 
        full_task = i.replace('\n','').replace('</question>','').replace('<role>','').replace('</role>','').replace('</sub-question>','').strip()
        role = full_task.split('<sub-question>')[0].strip()
        task = full_task.split('<sub-question>')[1].strip()
        task_list.append({'role':role,'task':task})

    frontend_chain = ChatPromptTemplate.from_template(LocalTemplate.get_frontend()) | model_256 
    frontend_result = frontend_chain.invoke({"task": task_list[0]['task']})

    backend_chain = ChatPromptTemplate.from_template(LocalTemplate.get_backend()) | model_256 
    backend_result = backend_chain.invoke({"task": task_list[1]['task']})

    designer_chain = ChatPromptTemplate.from_template(LocalTemplate.get_designer()) | model_256 
    designer_result = designer_chain.invoke({"task": task_list[2]['task']})

    customer_chain = ChatPromptTemplate.from_template(LocalTemplate.get_conclusion()) | model_512
    customer_result = customer_chain.invoke({
        "customer_need" : customer,
        "frontend_task": frontend_result.content, 
        "backend_task": backend_result.content, 
        "designer_task": designer_result.content
    })

    customer_json = remove_tag(customer_result.content,['<conclude>','</conclude>','<text>','</text>'])
    result =  {
        'raw' : customer_result.content,
        'json' : {
            'customer_need' : customer_json
        }
    }

    json_compatible_item_data = jsonable_encoder(result)
    return JSONResponse(content=json_compatible_item_data)

@app.post('/queryWithoutChain')
def query_without_chain(question : str):
    model_512 = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0.3, max_tokens=512,openai_api_key = OPENAI_API_KEY)
    chain = ChatPromptTemplate.from_template('{question}') | model_512
    customer_result = chain.invoke({"question": question})
    
    result =  {
        'raw' : customer_result.content,
        'json' : {
            'customer_need' : customer_result.content
        }
    }

    json_compatible_item_data = jsonable_encoder(result)

    return JSONResponse(content=json_compatible_item_data)

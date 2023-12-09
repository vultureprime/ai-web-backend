import os
import openai
import dotenv
from llama_hub.file.unstructured.base import UnstructuredReader
from pathlib import Path
from llama_index import VectorStoreIndex, ServiceContext, StorageContext
from llama_index import load_index_from_storage
from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import SubQuestionQueryEngine
from llama_index.agent import OpenAIAgent
import nest_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dotenv.load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
nest_asyncio.apply()
agent = None
def read_data(years):
    loader = UnstructuredReader()
    doc_set = {}
    all_docs = []
    for year in years:
        year_docs = loader.load_data(
            file=Path(f"./data/UBER/UBER_{year}.html"), split_documents=False
        )
        # insert year metadata into each year
        for d in year_docs:
            d.metadata = {"year": year}
        doc_set[year] = year_docs
        all_docs.extend(year_docs)
    return doc_set

def store_data(years, doc_set,service_context):
    index_set = {}
    for year in years:
        storage_context = StorageContext.from_defaults()
        cur_index = VectorStoreIndex.from_documents(
            doc_set[year],
            service_context=service_context,
            storage_context=storage_context,
        )
        index_set[year] = cur_index
        storage_context.persist(persist_dir=f"./storage/{year}")
    return index_set

def load_data(years,service_context):
    index_set = {}
    for year in years:
        storage_context = StorageContext.from_defaults(
            persist_dir=f"./storage/{year}"
        )
        cur_index = load_index_from_storage(
            storage_context, service_context=service_context
        )
        index_set[year] = cur_index
    return index_set

def create_individual_query_tool(index_set,years):
    individual_query_engine_tools = [
        QueryEngineTool(
            query_engine=index_set[year].as_query_engine(),
            metadata=ToolMetadata(
                name=f"vector_index_{year}",
                description=f"useful for when you want to answer queries about the {year} SEC 10-K for Uber",
            ),
        )
        for year in years
    ]
    return individual_query_engine_tools

def create_synthesizer(individual_query_engine_tool,service_context):
    query_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=individual_query_engine_tool,
        service_context=service_context,
    )
    return query_engine

def create_sub_question_tool(query_engine):
    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="sub_question_query_engine",
            description="useful for when you want to answer queries that require analyzing multiple SEC 10-K documents for Uber",
        ),
    )
    return query_engine_tool

def agent_chat():
    chat_engine_tool = [
        QueryEngineTool(
            query_engine=OpenAIAgent.from_tools([]),
            metadata=ToolMetadata(
                name="gpt_agent", description="Agent that can answer the general question."
            ),
        ),
    ]
    return chat_engine_tool

def build_chat_engine(individual_query_engine_tools,query_engine_tool,gpt_agent):
    global agent 
    tools = gpt_agent + individual_query_engine_tools + [query_engine_tool]
    agent = OpenAIAgent.from_tools(tools, verbose=False)
    return agent

@app.post('/buildRAG')
def build_RAG():
    years = [2022, 2021, 2020, 2019]
    service_context = ServiceContext.from_defaults(chunk_size=512)
    doc_set = read_data(years)
    store_data(years,doc_set,service_context)
    # index_set = load_data(years,service_context)

    return JSONResponse({'status': 'success'})

@app.post('/chat')
def chat(query : str = 'What were some of the biggest risk factors in 2022 for Uber?'):
    global agent
    years = [2022, 2021, 2020, 2019]
    service_context = ServiceContext.from_defaults(chunk_size=512)
    index_set = load_data(years,service_context)
    individual_query_engine_tools = create_individual_query_tool(index_set,years)
    query_engine = create_synthesizer(individual_query_engine_tools,service_context)
    query_engine_tool = create_sub_question_tool(query_engine)
    gpt_agent = agent_chat()
    if(agent == None):
        print('agent is none')
        agent = build_chat_engine(individual_query_engine_tools,query_engine_tool,gpt_agent)
    
    answer = agent.chat(query)

    return JSONResponse({
        'answer': answer
    })

@app.post('/resetChat')
def resetChat():
    global agent
    agent.reset()
    return JSONResponse({
        'status' : 'complete'
    })

@app.post('/chatWithoutRAG')
def chatWithoutRAG(query : str = 'What were some of the biggest risk factors in 2022 for Uber?'):
    gpt_agent = agent_chat()
    agent = OpenAIAgent.from_tools(gpt_agent, verbose=False)
    answer = agent.chat(query)

    return JSONResponse({
        'answer': answer
    })
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi_health import health
from fastapi.middleware.cors import CORSMiddleware
from src.main import *
from src.QA_integration import *
from src.shared.common_fn import *
from src.shared.llm_graph_builder_exception import LLMGraphBuilderException
import uvicorn
import asyncio
import base64
from langserve import add_routes
from langchain_google_vertexai import ChatVertexAI
from src.api_response import create_api_response
from src.graphDB_dataAccess import graphDBdataAccess
from src.graph_query import get_graph_results,get_chunktext_results,visualize_schema
from src.chunkid_entities import get_entities_from_chunkids
from src.post_processing import create_vector_fulltext_indexes, create_entity_embedding, graph_schema_consolidation
from sse_starlette.sse import EventSourceResponse
from src.communities import create_communities
from src.neighbours import get_neighbour_nodes
import json
from typing import List, Optional
from google.oauth2.credentials import Credentials
import os
from src.logger import CustomLogger
from datetime import datetime, timezone
import time
import gc
from Secweb.XContentTypeOptions import XContentTypeOptions
from Secweb.XFrameOptions import XFrame
from fastapi.middleware.gzip import GZipMiddleware
from src.ragas_eval import *
from starlette.types import ASGIApp, Receive, Scope, Send
from langchain_neo4j import Neo4jGraph
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from dotenv import load_dotenv
# Task 6: Package Management API imports
from src.package_manager import PackageManager
from src.package_versioning import PackageVersionManager, ChangeType
from src.entities.document_package import PackageCategory, PackageStatus
load_dotenv(override=True)

logger = CustomLogger()
CHUNK_DIR = os.path.join(os.path.dirname(__file__), "chunks")
MERGED_DIR = os.path.join(os.path.dirname(__file__), "merged_files")

def sanitize_filename(filename):
   """
   Sanitize the user-provided filename to prevent directory traversal and remove unsafe characters.
   """
   # Remove path separators and collapse redundant separators
   filename = os.path.basename(filename)
   filename = os.path.normpath(filename)
   return filename

def validate_file_path(directory, filename):
   """
   Construct the full file path and ensure it is within the specified directory.
   """
   file_path = os.path.join(directory, filename)
   abs_directory = os.path.abspath(directory)
   abs_file_path = os.path.abspath(file_path)
   # Ensure the file path starts with the intended directory path
   if not abs_file_path.startswith(abs_directory):
       raise ValueError("Invalid file path")
   return abs_file_path

def healthy_condition():
    output = {"healthy": True}
    return output

def healthy():
    return True

def sick():
    return False
class CustomGZipMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        paths: List[str],
        minimum_size: int = 1000,
        compresslevel: int = 5
    ):
        self.app = app
        self.paths = paths
        self.minimum_size = minimum_size
        self.compresslevel = compresslevel
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
 
        path = scope["path"]
        should_compress = any(path.startswith(gzip_path) for gzip_path in self.paths)
        
        if not should_compress:
            return await self.app(scope, receive, send)
        
        gzip_middleware = GZipMiddleware(
            app=self.app,
            minimum_size=self.minimum_size,
            compresslevel=self.compresslevel
        )
        await gzip_middleware(scope, receive, send)
app = FastAPI()
app.add_middleware(XContentTypeOptions)
app.add_middleware(XFrame, Option={'X-Frame-Options': 'DENY'})
app.add_middleware(CustomGZipMiddleware, minimum_size=1000, compresslevel=5,paths=["/sources_list","/url/scan","/extract","/chat_bot","/chunk_entities","/get_neighbours","/graph_query","/schema","/populate_graph_schema","/get_unconnected_nodes_list","/get_duplicate_nodes","/fetch_chunktext","/schema_visualization"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

is_gemini_enabled = os.environ.get("GEMINI_ENABLED", "False").lower() in ("true", "1", "yes")
if is_gemini_enabled:
    add_routes(app,ChatVertexAI(), path="/vertexai")

app.add_api_route("/health", health([healthy_condition, healthy]))



@app.post("/url/scan")
async def create_source_knowledge_graph_url(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    source_url=Form(None),
    database=Form(None),
    aws_access_key_id=Form(None),
    aws_secret_access_key=Form(None),
    wiki_query=Form(None),
    model=Form(),
    gcs_bucket_name=Form(None),
    gcs_bucket_folder=Form(None),
    source_type=Form(None),
    gcs_project_id=Form(None),
    access_token=Form(None),
    email=Form(None)
    ):
    
    try:
        start = time.time()
        if source_url is not None:
            source = source_url
        else:
            source = wiki_query
            
        graph = create_graph_database_connection(uri, userName, password, database)
        if source_type == 's3 bucket' and aws_access_key_id and aws_secret_access_key:
            lst_file_name,success_count,failed_count = await asyncio.to_thread(create_source_node_graph_url_s3,graph, model, source_url, aws_access_key_id, aws_secret_access_key, source_type
            )
        elif source_type == 'gcs bucket':
            lst_file_name,success_count,failed_count = create_source_node_graph_url_gcs(graph, model, gcs_project_id, gcs_bucket_name, gcs_bucket_folder, source_type,Credentials(access_token)
            )
        elif source_type == 'web-url':
            lst_file_name,success_count,failed_count = await asyncio.to_thread(create_source_node_graph_web_url,graph, model, source_url, source_type
            )  
        elif source_type == 'youtube':
            lst_file_name,success_count,failed_count = await asyncio.to_thread(create_source_node_graph_url_youtube,graph, model, source_url, source_type
            )
        elif source_type == 'Wikipedia':
            lst_file_name,success_count,failed_count = await asyncio.to_thread(create_source_node_graph_url_wikipedia,graph, model, wiki_query, source_type
            )
        else:
            return create_api_response('Failed',message='source_type is other than accepted source')

        message = f"Source Node created successfully for source type: {source_type} and source: {source}"
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'url_scan','db_url':uri,'url_scanned_file':lst_file_name, 'source_url':source_url, 'wiki_query':wiki_query, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','userName':userName, 'database':database, 'aws_access_key_id':aws_access_key_id,
                            'model':model, 'gcs_bucket_name':gcs_bucket_name, 'gcs_bucket_folder':gcs_bucket_folder, 'source_type':source_type,
                            'gcs_project_id':gcs_project_id, 'logging_time': formatted_time(datetime.now(timezone.utc)),'email':email}
        logger.log_struct(json_obj, "INFO")
        result ={'elapsed_api_time' : f'{elapsed_time:.2f}'}
        return create_api_response("Success",message=message,success_count=success_count,failed_count=failed_count,file_name=lst_file_name,data=result)
    except LLMGraphBuilderException as e:
        error_message = str(e)
        message = f" Unable to create source node for source type: {source_type} and source: {source}"
        # Set the status "Success" becuase we are treating these error already handled by application as like custom errors.
        json_obj = {'error_message':error_message, 'status':'Success','db_url':uri, 'userName':userName, 'database':database,'success_count':1, 'source_type': source_type, 'source_url':source_url, 'wiki_query':wiki_query, 'logging_time': formatted_time(datetime.now(timezone.utc)),'email':email}
        logger.log_struct(json_obj, "INFO")
        logging.exception(f'File Failed in upload: {e}')
        return create_api_response('Failed',message=message + error_message[:80],error=error_message,file_source=source_type)
    except Exception as e:
        error_message = str(e)
        message = f" Unable to create source node for source type: {source_type} and source: {source}"
        json_obj = {'error_message':error_message, 'status':'Failed','db_url':uri, 'userName':userName, 'database':database,'failed_count':1, 'source_type': source_type, 'source_url':source_url, 'wiki_query':wiki_query, 'logging_time': formatted_time(datetime.now(timezone.utc)),'email':email}
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception Stack trace upload:{e}')
        return create_api_response('Failed',message=message + error_message[:80],error=error_message,file_source=source_type)
    finally:
        gc.collect()

@app.post("/extract")
async def extract_knowledge_graph_from_file(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    model=Form(),
    database=Form(None),
    source_url=Form(None),
    aws_access_key_id=Form(None),
    aws_secret_access_key=Form(None),
    wiki_query=Form(None),
    gcs_project_id=Form(None),
    gcs_bucket_name=Form(None),
    gcs_bucket_folder=Form(None),
    gcs_blob_filename=Form(None),
    source_type=Form(None),
    file_name=Form(None),
    allowedNodes=Form(None),
    allowedRelationship=Form(None),
    token_chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
    chunks_to_combine: Optional[int] = Form(None),
    language=Form(None),
    access_token=Form(None),
    retry_condition=Form(None),
    additional_instructions=Form(None),
    email=Form(None)
):
    """
    Calls 'extract_graph_from_file' in a new thread to create Neo4jGraph from a
    PDF file based on the model.

    Args:
          uri: URI of the graph to extract
          userName: Username to use for graph creation
          password: Password to use for graph creation
          file: File object containing the PDF file
          model: Type of model to use ('Diffbot'or'OpenAI GPT')

    Returns:
          Nodes and Relations created in Neo4j databse for the pdf file
    """
    try:
        start_time = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)   
        graphDb_data_Access = graphDBdataAccess(graph)
        if source_type == 'local file':
            file_name = sanitize_filename(file_name)
            merged_file_path = validate_file_path(MERGED_DIR, file_name)
            uri_latency, result = await extract_graph_from_file_local_file(uri, userName, password, database, model, merged_file_path, file_name, allowedNodes, allowedRelationship, token_chunk_size, chunk_overlap, chunks_to_combine, retry_condition, additional_instructions)

        elif source_type == 's3 bucket' and source_url:
            uri_latency, result = await extract_graph_from_file_s3(uri, userName, password, database, model, source_url, aws_access_key_id, aws_secret_access_key, file_name, allowedNodes, allowedRelationship, token_chunk_size, chunk_overlap, chunks_to_combine, retry_condition, additional_instructions)
        
        elif source_type == 'web-url':
            uri_latency, result = await extract_graph_from_web_page(uri, userName, password, database, model, source_url, file_name, allowedNodes, allowedRelationship, token_chunk_size, chunk_overlap, chunks_to_combine, retry_condition, additional_instructions)

        elif source_type == 'youtube' and source_url:
            uri_latency, result = await extract_graph_from_file_youtube(uri, userName, password, database, model, source_url, file_name, allowedNodes, allowedRelationship, token_chunk_size, chunk_overlap, chunks_to_combine, retry_condition, additional_instructions)

        elif source_type == 'Wikipedia' and wiki_query:
            uri_latency, result = await extract_graph_from_file_Wikipedia(uri, userName, password, database, model, wiki_query, language, file_name, allowedNodes, allowedRelationship, token_chunk_size, chunk_overlap, chunks_to_combine, retry_condition, additional_instructions)

        elif source_type == 'gcs bucket' and gcs_bucket_name:
            uri_latency, result = await extract_graph_from_file_gcs(uri, userName, password, database, model, gcs_project_id, gcs_bucket_name, gcs_bucket_folder, gcs_blob_filename, access_token, file_name, allowedNodes, allowedRelationship, token_chunk_size, chunk_overlap, chunks_to_combine, retry_condition, additional_instructions)
        else:
            return create_api_response('Failed',message='source_type is other than accepted source')
        extract_api_time = time.time() - start_time
        if result is not None:
            logging.info("Going for counting nodes and relationships in extract")
            count_node_time = time.time()
            graph = create_graph_database_connection(uri, userName, password, database)   
            graphDb_data_Access = graphDBdataAccess(graph)
            count_response = graphDb_data_Access.update_node_relationship_count(file_name)
            logging.info("Nodes and Relationship Counts updated")
            if count_response :
                result['chunkNodeCount'] = count_response[file_name].get('chunkNodeCount',"0")
                result['chunkRelCount'] =  count_response[file_name].get('chunkRelCount',"0")
                result['entityNodeCount']=  count_response[file_name].get('entityNodeCount',"0")
                result['entityEntityRelCount']=  count_response[file_name].get('entityEntityRelCount',"0")
                result['communityNodeCount']=  count_response[file_name].get('communityNodeCount',"0")
                result['communityRelCount']= count_response[file_name].get('communityRelCount',"0")
                result['nodeCount'] = count_response[file_name].get('nodeCount',"0")
                result['relationshipCount']  = count_response[file_name].get('relationshipCount',"0")
                logging.info(f"counting completed in {(time.time()-count_node_time):.2f}")
            result['db_url'] = uri
            result['api_name'] = 'extract'
            result['source_url'] = source_url
            result['wiki_query'] = wiki_query
            result['source_type'] = source_type
            result['logging_time'] = formatted_time(datetime.now(timezone.utc))
            result['elapsed_api_time'] = f'{extract_api_time:.2f}'
            result['userName'] = userName
            result['database'] = database
            result['aws_access_key_id'] = aws_access_key_id
            result['gcs_bucket_name'] = gcs_bucket_name
            result['gcs_bucket_folder'] = gcs_bucket_folder
            result['gcs_blob_filename'] = gcs_blob_filename
            result['gcs_project_id'] = gcs_project_id
            result['language'] = language
            result['retry_condition'] = retry_condition
            result['email'] = email
        logger.log_struct(result, "INFO")
        result.update(uri_latency)
        logging.info(f"extraction completed in {extract_api_time:.2f} seconds for file name {file_name}")
        return create_api_response('Success', data=result, file_source= source_type)
    except LLMGraphBuilderException as e:
        error_message = str(e)
        graph = create_graph_database_connection(uri, userName, password, database)   
        graphDb_data_Access = graphDBdataAccess(graph)
        graphDb_data_Access.update_exception_db(file_name,error_message, retry_condition)
        if source_type == 'local file':
            failed_file_process(uri,file_name, merged_file_path)
        node_detail = graphDb_data_Access.get_current_status_document_node(file_name)
        # Set the status "Completed" in logging becuase we are treating these error already handled by application as like custom errors.
        json_obj = {'api_name':'extract','message':error_message,'file_created_at':formatted_time(node_detail[0]['created_time']),'error_message':error_message, 'file_name': file_name,'status':'Completed',
                    'db_url':uri, 'userName':userName, 'database':database,'success_count':1, 'source_type': source_type, 'source_url':source_url, 'wiki_query':wiki_query, 'logging_time': formatted_time(datetime.now(timezone.utc)),'email':email,
                    'allowedNodes': allowedNodes, 'allowedRelationship': allowedRelationship}
        logger.log_struct(json_obj, "INFO")
        logging.exception(f'File Failed in extraction: {e}')
        return create_api_response("Failed", message = error_message, error=error_message, file_name=file_name)
    except Exception as e:
        message=f"Failed To Process File:{file_name} or LLM Unable To Parse Content "
        error_message = str(e)
        graph = create_graph_database_connection(uri, userName, password, database)   
        graphDb_data_Access = graphDBdataAccess(graph)
        graphDb_data_Access.update_exception_db(file_name,error_message, retry_condition)
        if source_type == 'local file':
            failed_file_process(uri,file_name, merged_file_path)
        node_detail = graphDb_data_Access.get_current_status_document_node(file_name)
        
        json_obj = {'api_name':'extract','message':message,'file_created_at':formatted_time(node_detail[0]['created_time']),'error_message':error_message, 'file_name': file_name,'status':'Failed',
                    'db_url':uri, 'userName':userName, 'database':database,'failed_count':1, 'source_type': source_type, 'source_url':source_url, 'wiki_query':wiki_query, 'logging_time': formatted_time(datetime.now(timezone.utc)),'email':email,
                    'allowedNodes': allowedNodes, 'allowedRelationship': allowedRelationship}
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'File Failed in extraction: {e}')
        return create_api_response('Failed', message=message + error_message[:100], error=error_message, file_name = file_name)
    finally:
        gc.collect()
            
@app.post("/sources_list")
async def get_source_list(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    email=Form(None)):
    """
    Calls 'get_source_list_from_graph' which returns list of sources which already exist in databse
    """
    try:
        start = time.time()
        result = await asyncio.to_thread(get_source_list_from_graph,uri,userName,password,database)
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'sources_list','db_url':uri, 'userName':userName, 'database':database, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response("Success",data=result, message=f"Total elapsed API time {elapsed_time:.2f}")
    except Exception as e:
        job_status = "Failed"
        message="Unable to fetch source list"
        error_message = str(e)
        logging.exception(f'Exception:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)

@app.post("/post_processing")
async def post_processing(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None), tasks=Form(None), email=Form(None)):
    try:
        graph = create_graph_database_connection(uri, userName, password, database)
        tasks = set(map(str.strip, json.loads(tasks)))
        api_name = 'post_processing'
        count_response = []
        start = time.time()
        if "materialize_text_chunk_similarities" in tasks:
            await asyncio.to_thread(update_graph, graph)
            api_name = 'post_processing/update_similarity_graph'
            logging.info(f'Updated KNN Graph')

        if "enable_hybrid_search_and_fulltext_search_in_bloom" in tasks:
            await asyncio.to_thread(create_vector_fulltext_indexes, uri=uri, username=userName, password=password, database=database)
            api_name = 'post_processing/enable_hybrid_search_and_fulltext_search_in_bloom'
            logging.info(f'Full Text index created')

        if os.environ.get('ENTITY_EMBEDDING','False').upper()=="TRUE" and "materialize_entity_similarities" in tasks:
            await asyncio.to_thread(create_entity_embedding, graph)
            api_name = 'post_processing/create_entity_embedding'
            logging.info(f'Entity Embeddings created')

        if "graph_schema_consolidation" in tasks :
            await asyncio.to_thread(graph_schema_consolidation, graph)
            api_name = 'post_processing/graph_schema_consolidation'
            logging.info(f'Updated nodes and relationship labels')
            
        if "enable_communities" in tasks:
            api_name = 'create_communities'
            await asyncio.to_thread(create_communities, uri, userName, password, database)  
            
            logging.info(f'created communities')
        graph = create_graph_database_connection(uri, userName, password, database)   
        graphDb_data_Access = graphDBdataAccess(graph)
        document_name = ""
        count_response = graphDb_data_Access.update_node_relationship_count(document_name)
        if count_response:
            count_response = [{"filename": filename, **counts} for filename, counts in count_response.items()]
            logging.info(f'Updated source node with community related counts')
        
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name': api_name, 'db_url': uri, 'userName':userName, 'database':database, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj)
        return create_api_response('Success', data=count_response, message='All tasks completed successfully')
    
    except Exception as e:
        job_status = "Failed"
        error_message = str(e)
        message = f"Unable to complete tasks"
        logging.exception(f'Exception in post_processing tasks: {error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    
    finally:
        gc.collect()
                
@app.post("/chat_bot")
async def chat_bot(uri=Form(None),model=Form(None),userName=Form(None), password=Form(None), database=Form(None),question=Form(None), document_names=Form(None),session_id=Form(None),mode=Form(None),email=Form(None)):
    logging.info(f"QA_RAG called at {datetime.now()}")
    qa_rag_start_time = time.time()
    try:
        if mode == "graph":
            graph = Neo4jGraph( url=uri,username=userName,password=password,database=database,sanitize = True, refresh_schema=True)
        else:
            graph = create_graph_database_connection(uri, userName, password, database)
        
        graph_DB_dataAccess = graphDBdataAccess(graph)
        write_access = graph_DB_dataAccess.check_account_access(database=database)
        result = await asyncio.to_thread(QA_RAG,graph=graph,model=model,question=question,document_names=document_names,session_id=session_id,mode=mode,write_access=write_access)

        total_call_time = time.time() - qa_rag_start_time
        logging.info(f"Total Response time is  {total_call_time:.2f} seconds")
        result["info"]["response_time"] = round(total_call_time, 2)
        
        json_obj = {'api_name':'chat_bot','db_url':uri, 'userName':userName, 'database':database, 'question':question,'document_names':document_names,
                             'session_id':session_id, 'mode':mode, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{total_call_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        
        return create_api_response('Success',data=result)
    except Exception as e:
        job_status = "Failed"
        message="Unable to get chat response"
        error_message = str(e)
        logging.exception(f'Exception in chat bot:{error_message}')
        return create_api_response(job_status, message=message, error=error_message,data=mode)
    finally:
        gc.collect()

@app.post("/chunk_entities")
async def chunk_entities(uri=Form(None),userName=Form(None), password=Form(None), database=Form(None), nodedetails=Form(None),entities=Form(),mode=Form(),email=Form(None)):
    try:
        start = time.time()
        result = await asyncio.to_thread(get_entities_from_chunkids,nodedetails=nodedetails,entities=entities,mode=mode,uri=uri, username=userName, password=password, database=database)
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'chunk_entities','db_url':uri, 'userName':userName, 'database':database, 'nodedetails':nodedetails,'entities':entities,
                            'mode':mode, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',data=result,message=f"Total elapsed API time {elapsed_time:.2f}")
    except Exception as e:
        job_status = "Failed"
        message="Unable to extract entities from chunk ids"
        error_message = str(e)
        logging.exception(f'Exception in chat bot:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()

@app.post("/get_neighbours")
async def get_neighbours(uri=Form(None),userName=Form(None), password=Form(None), database=Form(None), elementId=Form(None),email=Form(None)):
    try:
        start = time.time()
        result = await asyncio.to_thread(get_neighbour_nodes,uri=uri, username=userName, password=password,database=database, element_id=elementId)
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'get_neighbours', 'userName':userName, 'database':database,'db_url':uri, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',data=result,message=f"Total elapsed API time {elapsed_time:.2f}")
    except Exception as e:
        job_status = "Failed"
        message="Unable to extract neighbour nodes for given element ID"
        error_message = str(e)
        logging.exception(f'Exception in get neighbours :{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()

@app.post("/graph_query")
async def graph_query(
    uri: str = Form(None),
    database: str = Form(None),
    userName: str = Form(None),
    password: str = Form(None),
    document_names: str = Form(None),
    email=Form(None)
):
    try:
        start = time.time()
        result = await asyncio.to_thread(
            get_graph_results,
            uri=uri,
            username=userName,
            password=password,
            database=database,
            document_names=document_names
        )
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'graph_query','db_url':uri, 'userName':userName, 'database':database, 'document_names':document_names, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success', data=result,message=f"Total elapsed API time {elapsed_time:.2f}")
    except Exception as e:
        job_status = "Failed"
        message = "Unable to get graph query response"
        error_message = str(e)
        logging.exception(f'Exception in graph query: {error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()
    

@app.post("/clear_chat_bot")
async def clear_chat_bot(uri=Form(None),userName=Form(None), password=Form(None), database=Form(None), session_id=Form(None),email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        result = await asyncio.to_thread(clear_chat_history,graph=graph,session_id=session_id)
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'clear_chat_bot', 'db_url':uri, 'userName':userName, 'database':database, 'session_id':session_id, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',data=result)
    except Exception as e:
        job_status = "Failed"
        message="Unable to clear chat History"
        error_message = str(e)
        logging.exception(f'Exception in chat bot:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()
            
@app.post("/connect")
async def connect(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None),email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        result = await asyncio.to_thread(connection_check_and_get_vector_dimensions, graph, database)
        gcs_file_cache = os.environ.get('GCS_FILE_CACHE')
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'connect','db_url':uri, 'userName':userName, 'database':database, 'count':1, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        result['elapsed_api_time'] = f'{elapsed_time:.2f}'
        result['gcs_file_cache'] = gcs_file_cache
        return create_api_response('Success',data=result)
    except Exception as e:
        job_status = "Failed"
        message="Connection failed to connect Neo4j database"
        error_message = str(e)
        logging.exception(f'Connection failed to connect Neo4j database:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)

@app.post("/upload")
async def upload_large_file_into_chunks(file:UploadFile = File(...), chunkNumber=Form(None), totalChunks=Form(None), 
                                        originalname=Form(None), model=Form(None), uri=Form(None), userName=Form(None), 
                                        password=Form(None), database=Form(None),email=Form(None),
                                        categoryId=Form(None), categoryName=Form(None), productId=Form(None), 
                                        productName=Form(None), documentType=Form(None),
                                        expectedDocumentId=Form(None), preSelectedDocumentType=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        # Create package context if provided
        package_context = None
        if categoryId or productId:
            # Use pre-selected document type if provided, otherwise fall back to documentType
            final_document_type = preSelectedDocumentType or documentType or 'Other'
            
            package_context = {
                'categoryId': categoryId,
                'categoryName': categoryName,
                'productId': productId,
                'productName': productName,
                'documentType': final_document_type,
                'expectedDocumentId': expectedDocumentId  # Link to PackageDocument template
            }
        
        result = await asyncio.to_thread(upload_file, graph, model, file, chunkNumber, totalChunks, originalname, uri, CHUNK_DIR, MERGED_DIR, package_context)
        end = time.time()
        elapsed_time = end - start
        if int(chunkNumber) == int(totalChunks):
            json_obj = {'api_name':'upload','db_url':uri,'userName':userName, 'database':database, 'chunkNumber':chunkNumber,'totalChunks':totalChunks,
                                'original_file_name':originalname,'model':model, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
            logger.log_struct(json_obj, "INFO")
        if int(chunkNumber) == int(totalChunks):
            return create_api_response('Success',data=result, message='Source Node Created Successfully')
        else:
            return create_api_response('Success', message=result)
    except Exception as e:
        message="Unable to upload file in chunks"
        error_message = str(e)
        graph = create_graph_database_connection(uri, userName, password, database)   
        graphDb_data_Access = graphDBdataAccess(graph)
        graphDb_data_Access.update_exception_db(originalname,error_message)
        logging.info(message)
        logging.exception(f'Exception:{error_message}')
        return create_api_response('Failed', message=message + error_message[:100], error=error_message, file_name = originalname)
    finally:
        gc.collect()
            
@app.post("/schema")
async def get_structured_schema(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None),email=Form(None)):
    try:
        start = time.time()
        result = await asyncio.to_thread(get_labels_and_relationtypes, uri, userName, password, database)
        end = time.time()
        elapsed_time = end - start
        logging.info(f'Schema result from DB: {result}')
        json_obj = {'api_name':'schema','db_url':uri, 'userName':userName, 'database':database, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success', data=result,message=f"Total elapsed API time {elapsed_time:.2f}")
    except Exception as e:
        message="Unable to get the labels and relationtypes from neo4j database"
        error_message = str(e)
        logging.info(message)
        logging.exception(f'Exception:{error_message}')
        return create_api_response("Failed", message=message, error=error_message)
    finally:
        gc.collect()
            
def decode_password(pwd):
    sample_string_bytes = base64.b64decode(pwd)
    decoded_password = sample_string_bytes.decode("utf-8")
    return decoded_password

def encode_password(pwd):
    data_bytes = pwd.encode('ascii')
    encoded_pwd_bytes = base64.b64encode(data_bytes)
    return encoded_pwd_bytes

@app.get("/update_extract_status/{file_name}")
async def update_extract_status(request: Request, file_name: str, uri:str=None, userName:str=None, password:str=None, database:str=None):
    async def generate():
        status = ''
        
        if password is not None and password != "null":
            decoded_password = decode_password(password)
        else:
            decoded_password = None

        url = uri
        if url and " " in url:
            url= url.replace(" ","+")
            
        graph = create_graph_database_connection(url, userName, decoded_password, database)
        graphDb_data_Access = graphDBdataAccess(graph)
        while True:
            try:
                if await request.is_disconnected():
                    logging.info(" SSE Client disconnected")
                    break
                # get the current status of document node
                
                else:
                    result = graphDb_data_Access.get_current_status_document_node(file_name)
                    if len(result) > 0:
                        status = json.dumps({'fileName':file_name, 
                        'status':result[0]['Status'],
                        'processingTime':result[0]['processingTime'],
                        'nodeCount':result[0]['nodeCount'],
                        'relationshipCount':result[0]['relationshipCount'],
                        'model':result[0]['model'],
                        'total_chunks':result[0]['total_chunks'],
                        'fileSize':result[0]['fileSize'],
                        'processed_chunk':result[0]['processed_chunk'],
                        'fileSource':result[0]['fileSource'],
                        'chunkNodeCount' : result[0]['chunkNodeCount'],
                        'chunkRelCount' : result[0]['chunkRelCount'],
                        'entityNodeCount' : result[0]['entityNodeCount'],
                        'entityEntityRelCount' : result[0]['entityEntityRelCount'],
                        'communityNodeCount' : result[0]['communityNodeCount'],
                        'communityRelCount' : result[0]['communityRelCount']
                        })
                    yield status
            except asyncio.CancelledError:
                logging.info("SSE Connection cancelled")
    
    return EventSourceResponse(generate(),ping=60)

@app.post("/delete_document_and_entities")
async def delete_document_and_entities(uri=Form(None), 
                                       userName=Form(None), 
                                       password=Form(None), 
                                       database=Form(None), 
                                       filenames=Form(),
                                       source_types=Form(),
                                       deleteEntities=Form(),
                                       email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        graphDb_data_Access = graphDBdataAccess(graph)
        files_list_size = await asyncio.to_thread(graphDb_data_Access.delete_file_from_graph, filenames, source_types, deleteEntities, MERGED_DIR, uri)
        message = f"Deleted {files_list_size} documents with entities from database"
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'delete_document_and_entities','db_url':uri, 'userName':userName, 'database':database, 'filenames':filenames,'deleteEntities':deleteEntities,
                            'source_types':source_types, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',message=message)
    except Exception as e:
        job_status = "Failed"
        message=f"Unable to delete document {filenames}"
        error_message = str(e)
        logging.exception(f'{message}:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()

@app.get('/document_status/{file_name}')
async def get_document_status(file_name, url, userName, password, database):
    decoded_password = decode_password(password)
   
    try:
        if " " in url:
            uri= url.replace(" ","+")
        else:
            uri=url
        graph = create_graph_database_connection(uri, userName, decoded_password, database)
        graphDb_data_Access = graphDBdataAccess(graph)
        result = graphDb_data_Access.get_current_status_document_node(file_name)
        if len(result) > 0:
            status = {'fileName':file_name, 
                'status':result[0]['Status'],
                'processingTime':result[0]['processingTime'],
                'nodeCount':result[0]['nodeCount'],
                'relationshipCount':result[0]['relationshipCount'],
                'model':result[0]['model'],
                'total_chunks':result[0]['total_chunks'],
                'fileSize':result[0]['fileSize'],
                'processed_chunk':result[0]['processed_chunk'],
                'fileSource':result[0]['fileSource'],
                'chunkNodeCount' : result[0]['chunkNodeCount'],
                'chunkRelCount' : result[0]['chunkRelCount'],
                'entityNodeCount' : result[0]['entityNodeCount'],
                'entityEntityRelCount' : result[0]['entityEntityRelCount'],
                'communityNodeCount' : result[0]['communityNodeCount'],
                'communityRelCount' : result[0]['communityRelCount']
                }
        else:
            status = {'fileName':file_name, 'status':'Failed'}
        logging.info(f'Result of document status in refresh : {result}')
        return create_api_response('Success',message="",file_name=status)
    except Exception as e:
        message=f"Unable to get the document status"
        error_message = str(e)
        logging.exception(f'{message}:{error_message}')
        return create_api_response('Failed',message=message)
    
@app.post("/cancelled_job")
async def cancelled_job(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None), filenames=Form(None), source_types=Form(None),email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        result = manually_cancelled_job(graph,filenames, source_types, MERGED_DIR, uri)
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'cancelled_job','db_url':uri, 'userName':userName, 'database':database, 'filenames':filenames,
                            'source_types':source_types, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',message=result)
    except Exception as e:
        job_status = "Failed"
        message="Unable to cancelled the running job"
        error_message = str(e)
        logging.exception(f'Exception in cancelling the running job:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()

@app.post("/populate_graph_schema")
async def populate_graph_schema(input_text=Form(None), model=Form(None), is_schema_description_checked=Form(None),is_local_storage=Form(None),email=Form(None)):
    try:
        start = time.time()
        result = populate_graph_schema_from_text(input_text, model, is_schema_description_checked, is_local_storage)
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'populate_graph_schema', 'model':model, 'is_schema_description_checked':is_schema_description_checked, 'input_text':input_text, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',data=result)
    except Exception as e:
        job_status = "Failed"
        message="Unable to get the schema from text"
        error_message = str(e)
        logging.exception(f'Exception in getting the schema from text:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()
        
@app.post("/get_unconnected_nodes_list")
async def get_unconnected_nodes_list(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None),email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        graphDb_data_Access = graphDBdataAccess(graph)
        nodes_list, total_nodes = graphDb_data_Access.list_unconnected_nodes()
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'get_unconnected_nodes_list','db_url':uri, 'userName':userName, 'database':database, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',data=nodes_list,message=total_nodes)
    except Exception as e:
        job_status = "Failed"
        message="Unable to get the list of unconnected nodes"
        error_message = str(e)
        logging.exception(f'Exception in getting list of unconnected nodes:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()
        
@app.post("/delete_unconnected_nodes")
async def delete_orphan_nodes(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None),unconnected_entities_list=Form(),email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        graphDb_data_Access = graphDBdataAccess(graph)
        result = graphDb_data_Access.delete_unconnected_nodes(unconnected_entities_list)
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'delete_unconnected_nodes','db_url':uri, 'userName':userName, 'database':database,'unconnected_entities_list':unconnected_entities_list, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',data=result,message="Unconnected entities delete successfully")
    except Exception as e:
        job_status = "Failed"
        message="Unable to delete the unconnected nodes"
        error_message = str(e)
        logging.exception(f'Exception in delete the unconnected nodes:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()
        
@app.post("/get_duplicate_nodes")
async def get_duplicate_nodes(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None),email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        graphDb_data_Access = graphDBdataAccess(graph)
        nodes_list, total_nodes = graphDb_data_Access.get_duplicate_nodes_list()
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'get_duplicate_nodes','db_url':uri,'userName':userName, 'database':database, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',data=nodes_list, message=total_nodes)
    except Exception as e:
        job_status = "Failed"
        message="Unable to get the list of duplicate nodes"
        error_message = str(e)
        logging.exception(f'Exception in getting list of duplicate nodes:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()
        
@app.post("/merge_duplicate_nodes")
async def merge_duplicate_nodes(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None),duplicate_nodes_list=Form(),email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        graphDb_data_Access = graphDBdataAccess(graph)
        result = graphDb_data_Access.merge_duplicate_nodes(duplicate_nodes_list)
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'merge_duplicate_nodes','db_url':uri, 'userName':userName, 'database':database,
                            'duplicate_nodes_list':duplicate_nodes_list, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',data=result,message="Duplicate entities merged successfully")
    except Exception as e:
        job_status = "Failed"
        message="Unable to merge the duplicate nodes"
        error_message = str(e)
        logging.exception(f'Exception in merge the duplicate nodes:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()
        
@app.post("/drop_create_vector_index")
async def drop_create_vector_index(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None), isVectorIndexExist=Form(),email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        graphDb_data_Access = graphDBdataAccess(graph)
        result = graphDb_data_Access.drop_create_vector_index(isVectorIndexExist)
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'drop_create_vector_index', 'db_url':uri, 'userName':userName, 'database':database,
                            'isVectorIndexExist':isVectorIndexExist, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success',message=result)
    except Exception as e:
        job_status = "Failed"
        message="Unable to drop and re-create vector index with correct dimesion as per application configuration"
        error_message = str(e)
        logging.exception(f'Exception into drop and re-create vector index with correct dimesion as per application configuration:{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()
        
@app.post("/retry_processing")
async def retry_processing(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None), file_name=Form(), retry_condition=Form(), email=Form(None)):
    try:
        start = time.time()
        graph = create_graph_database_connection(uri, userName, password, database)
        chunks = execute_graph_query(graph,QUERY_TO_GET_CHUNKS,params={"filename":file_name})
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'retry_processing', 'db_url':uri, 'userName':userName, 'database':database, 'file_name':file_name,'retry_condition':retry_condition,
                            'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}','email':email}
        logger.log_struct(json_obj, "INFO")
        if chunks[0]['text'] is None or chunks[0]['text']=="" or not chunks :
            return create_api_response('Success',message=f"Chunks are not created for the file{file_name}. Please upload again the file to re-process.",data=chunks)
        else:
            await asyncio.to_thread(set_status_retry, graph,file_name,retry_condition)
            return create_api_response('Success',message=f"Status set to Ready to Reprocess for filename : {file_name}")
    except Exception as e:
        job_status = "Failed"
        message="Unable to set status to Retry"
        error_message = str(e)
        logging.exception(f'{error_message}')
        return create_api_response(job_status, message=message, error=error_message)
    finally:
        gc.collect()    

@app.post('/metric')
async def calculate_metric(question: str = Form(),
                           context: str = Form(),
                           answer: str = Form(),
                           model: str = Form(),
                           mode: str = Form()):
    try:
        start = time.time()
        context_list = [str(item).strip() for item in json.loads(context)] if context else []
        answer_list = [str(item).strip() for item in json.loads(answer)] if answer else []
        mode_list = [str(item).strip() for item in json.loads(mode)] if mode else []

        result = await asyncio.to_thread(
            get_ragas_metrics, question, context_list, answer_list, model
        )
        if result is None or "error" in result:
            return create_api_response(
                'Failed',
                message='Failed to calculate evaluation metrics.',
                error=result.get("error", "Ragas evaluation returned null")
            )
        data = {mode: {metric: result[metric][i] for metric in result} for i, mode in enumerate(mode_list)}
        end = time.time()
        elapsed_time = end - start
        json_obj = {'api_name':'metric', 'question':question, 'context':context, 'answer':answer, 'model':model,'mode':mode,
                            'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}'}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success', data=data)
    except Exception as e:
        logging.exception(f"Error while calculating evaluation metrics: {e}")
        return create_api_response(
            'Failed',
            message="Error while calculating evaluation metrics",
            error=str(e)
        )
    finally:
        gc.collect()
       

@app.post('/additional_metrics')
async def calculate_additional_metrics(question: str = Form(),
                                        context: str = Form(),
                                        answer: str = Form(),
                                        reference: str = Form(),
                                        model: str = Form(),
                                        mode: str = Form(),
):
   try:
       context_list = [str(item).strip() for item in json.loads(context)] if context else []
       answer_list = [str(item).strip() for item in json.loads(answer)] if answer else []
       mode_list = [str(item).strip() for item in json.loads(mode)] if mode else []
       result = await get_additional_metrics(question, context_list,answer_list, reference, model)
       if result is None or "error" in result:
           return create_api_response(
               'Failed',
               message='Failed to calculate evaluation metrics.',
               error=result.get("error", "Ragas evaluation returned null")
           )
       data = {mode: {metric: result[i][metric] for metric in result[i]} for i, mode in enumerate(mode_list)}
       return create_api_response('Success', data=data)
   except Exception as e:
       logging.exception(f"Error while calculating evaluation metrics: {e}")
       return create_api_response(
           'Failed',
           message="Error while calculating evaluation metrics",
           error=str(e)
       )
   finally:
       gc.collect()

@app.post("/fetch_chunktext")
async def fetch_chunktext(
   uri: str = Form(None),
   database: str = Form(None),
   userName: str = Form(None),
   password: str = Form(None),
   document_name: str = Form(),
   page_no: int = Form(1),
   email=Form(None)
):
   try:
       start = time.time()
       result = await asyncio.to_thread(
           get_chunktext_results,
           uri=uri,
           username=userName,
           password=password,
           database=database,
           document_name=document_name,
           page_no=page_no
       )
       end = time.time()
       elapsed_time = end - start
       json_obj = {
           'api_name': 'fetch_chunktext',
           'db_url': uri,
           'userName': userName,
           'database': database,
           'document_name': document_name,
           'page_no': page_no,
           'logging_time': formatted_time(datetime.now(timezone.utc)),
           'elapsed_api_time': f'{elapsed_time:.2f}',
           'email': email
       }
       logger.log_struct(json_obj, "INFO")
       return create_api_response('Success', data=result, message=f"Total elapsed API time {elapsed_time:.2f}")
   except Exception as e:
       job_status = "Failed"
       message = "Unable to get chunk text response"
       error_message = str(e)
       logging.exception(f'Exception in fetch_chunktext: {error_message}')
       return create_api_response(job_status, message=message, error=error_message)
   finally:
       gc.collect()


@app.post("/backend_connection_configuration")
async def backend_connection_configuration():
    try:
        start = time.time()
        uri = os.getenv('NEO4J_URI')
        username= os.getenv('NEO4J_USERNAME')
        database= os.getenv('NEO4J_DATABASE')
        password= os.getenv('NEO4J_PASSWORD')
        gcs_file_cache = os.environ.get('GCS_FILE_CACHE')
        if all([uri, username, database, password]):
            graph = Neo4jGraph()
            logging.info(f'login connection status of object: {graph}')
            if graph is not None:
                graph_connection = True        
                graphDb_data_Access = graphDBdataAccess(graph)
                result = graphDb_data_Access.connection_check_and_get_vector_dimensions(database)
                result['gcs_file_cache'] = gcs_file_cache
                result['uri'] = uri
                end = time.time()
                elapsed_time = end - start
                result['api_name'] = 'backend_connection_configuration'
                result['elapsed_api_time'] = f'{elapsed_time:.2f}'
                result['graph_connection'] = f'{graph_connection}',
                result['connection_from'] = 'backendAPI'
                logger.log_struct(result, "INFO")
                return create_api_response('Success',message=f"Backend connection successful",data=result)
        else:
            graph_connection = False
            return create_api_response('Success',message=f"Backend connection is not successful",data=graph_connection)
    except Exception as e:
        graph_connection = False
        job_status = "Failed"
        message="Unable to connect backend DB"
        error_message = str(e)
        logging.exception(f'{error_message}')
        return create_api_response(job_status, message=message, error=error_message.rstrip('.') + ', or fill from the login dialog.', data=graph_connection)
    finally:
        gc.collect()
    
@app.post("/schema_visualization")
async def get_schema_visualization(uri=Form(None), userName=Form(None), password=Form(None), database=Form(None)):
    try:
        start = time.time()
        result = await asyncio.to_thread(visualize_schema,
           uri=uri,
           userName=userName,
           password=password,
           database=database)
        if result:
            logging.info("Graph schema visualization query successful")
        end = time.time()
        elapsed_time = end - start
        logging.info(f'Schema result from DB: {result}')
        json_obj = {'api_name':'schema_visualization','db_url':uri, 'userName':userName, 'database':database, 'logging_time': formatted_time(datetime.now(timezone.utc)), 'elapsed_api_time':f'{elapsed_time:.2f}'}
        logger.log_struct(json_obj, "INFO")
        return create_api_response('Success', data=result,message=f"Total elapsed API time {elapsed_time:.2f}")
    except Exception as e:
        message="Unable to get schema visualization from neo4j database"
        error_message = str(e)
        logging.info(message)
        logging.exception(f'Exception:{error_message}')
        return create_api_response("Failed", message=message, error=error_message)
    finally:
        gc.collect()


# Task 6: Package Management API Endpoints

@app.post("/packages")
async def create_package(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    package_name=Form(...),
    tenant_id=Form(...),
    category=Form(...),
    template=Form(None),
    created_by=Form(None),
    documents=Form(None),
    relationships=Form(None),
    customizations=Form(None),
    products=Form(None)
):
    """Create a new document package"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Initialize package manager
        package_manager = PackageManager(graph_db)
        
        # Prepare package configuration
        package_config = {
            'package_name': package_name,
            'tenant_id': tenant_id,
            'category': category,
            'created_by': created_by or 'api_user'
        }
        
        # Add optional fields
        if template:
            package_config['template'] = template
            
        # Parse documents if provided
        if documents:
            try:
                package_config['documents'] = json.loads(documents)
            except json.JSONDecodeError:
                return create_api_response('Failed', message='Invalid documents JSON format')
        
        # Parse relationships if provided 
        if relationships:
            try:
                package_config['relationships'] = json.loads(relationships)
            except json.JSONDecodeError:
                return create_api_response('Failed', message='Invalid relationships JSON format')
                
        # Parse customizations if provided
        if customizations:
            try:
                package_config['customizations'] = json.loads(customizations)
            except json.JSONDecodeError:
                return create_api_response('Failed', message='Invalid customizations JSON format')
        
        # Parse products if provided (for 3-tier hierarchy)
        if products:
            try:
                package_config['products'] = json.loads(products)
            except json.JSONDecodeError:
                return create_api_response('Failed', message='Invalid products JSON format')
        
        # Create package
        package = package_manager.create_package(package_config)
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'create_package',
            'db_url': uri,
            'package_id': package.package_id,
            'package_name': package_name,
            'category': category,
            'tenant_id': tenant_id,
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        # Prepare response data
        response_data = {
            'package_id': package.package_id,
            'package_name': package.package_name,
            'category': package.category.value,
            'version': package.version,
            'status': package.status.value,
            'created_at': package.created_at.isoformat(),
            'document_count': len(package.documents),
            'relationship_count': len(package.relationships),
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Package '{package_name}' created successfully with ID: {package.package_id}"
        return create_api_response('Success', message=message, data=response_data)
        
    except ValueError as e:
        error_message = str(e)
        message = f"Invalid package configuration: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'create_package',
            'package_name': package_name,
            'category': category,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except LLMGraphBuilderException as e:
        error_message = str(e)
        message = f"Package creation failed: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'create_package',
            'package_name': package_name,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except Exception as e:
        error_message = str(e)
        message = f"Unexpected error during package creation: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'create_package',
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in create_package: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.get("/packages/{package_id}")
async def get_package(
    package_id: str,
    uri=Form(None),
    userName=Form(None), 
    password=Form(None),
    database=Form(None)
):
    """Retrieve a specific package by ID"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Initialize package manager
        package_manager = PackageManager(graph_db)
        
        # Load package
        package = package_manager.load_package(package_id)
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'get_package',
            'db_url': uri,
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        # Prepare response data
        response_data = {
            'package_id': package.package_id,
            'package_name': package.package_name,
            'tenant_id': package.tenant_id,
            'category': package.category.value,
            'version': package.version,
            'status': package.status.value,
            'created_by': package.created_by,
            'template_type': package.template_type,
            'created_at': package.created_at.isoformat(),
            'updated_at': package.updated_at.isoformat(),
            'template_mappings': package.template_mappings,
            'validation_rules': package.validation_rules,
            'documents': [
                {
                    'document_id': doc.document_id,
                    'document_type': doc.document_type,
                    'document_name': doc.document_name,
                    'expected_structure': doc.expected_structure,
                    'required_sections': doc.required_sections,
                    'optional_sections': doc.optional_sections,
                    'chunking_strategy': doc.chunking_strategy,
                    'entity_types': doc.entity_types,
                    'matrix_configuration': doc.matrix_configuration,
                    'validation_schema': doc.validation_schema,
                    'quality_thresholds': doc.quality_thresholds
                }
                for doc in package.documents
            ],
            'relationships': [
                {
                    'from_document': rel.from_document,
                    'to_document': rel.to_document,
                    'relationship_type': rel.relationship_type,
                    'metadata': rel.metadata
                }
                for rel in package.relationships
            ],
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Package '{package_id}' retrieved successfully"
        return create_api_response('Success', message=message, data=response_data)
        
    except ValueError as e:
        error_message = str(e)
        message = f"Package not found: {package_id}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'get_package',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to retrieve package: {package_id}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'get_package',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in get_package: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.get("/packages")
async def list_packages(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    tenant_id=Form(None),
    category=Form(None),
    status=Form(None)
):
    """List packages with optional filtering"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Initialize package manager
        package_manager = PackageManager(graph_db)
        
        # Parse filters
        category_filter = PackageCategory(category) if category else None
        status_filter = PackageStatus(status) if status else None
        
        # List packages
        packages = package_manager.list_packages(tenant_id, category_filter, status_filter)
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'list_packages',
            'db_url': uri,
            'tenant_id': tenant_id,
            'category': category,
            'status': status,
            'package_count': len(packages),
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        # Prepare response data
        response_data = {
            'packages': packages,
            'total_count': len(packages),
            'filters': {
                'tenant_id': tenant_id,
                'category': category,
                'status': status
            },
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Found {len(packages)} packages"
        return create_api_response('Success', message=message, data=response_data)
        
    except ValueError as e:
        error_message = str(e)
        message = f"Invalid filter parameters: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'list_packages',
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to list packages: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'list_packages',
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in list_packages: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.put("/packages/{package_id}")
async def update_package(
    package_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    package_name=Form(None),
    status=Form(None),
    documents=Form(None),
    relationships=Form(None),
    version_type=Form('PATCH')
):
    """Update an existing package"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Initialize package manager
        package_manager = PackageManager(graph_db)
        
        # Prepare updates
        updates = {}
        
        if package_name:
            updates['package_name'] = package_name
            
        if status:
            updates['status'] = status
            
        if documents:
            try:
                updates['documents'] = json.loads(documents)
            except json.JSONDecodeError:
                return create_api_response('Failed', message='Invalid documents JSON format')
        
        if relationships:
            try:
                updates['relationships'] = json.loads(relationships)
            except json.JSONDecodeError:
                return create_api_response('Failed', message='Invalid relationships JSON format')
                
        if version_type:
            updates['version_type'] = version_type
        
        # Update package
        package = package_manager.update_package(package_id, updates)
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'update_package',
            'db_url': uri,
            'package_id': package_id,
            'new_version': package.version,
            'version_type': version_type,
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        # Prepare response data
        response_data = {
            'package_id': package.package_id,
            'package_name': package.package_name,
            'version': package.version,
            'status': package.status.value,
            'updated_at': package.updated_at.isoformat(),
            'document_count': len(package.documents),
            'relationship_count': len(package.relationships),
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Package '{package_id}' updated successfully to version {package.version}"
        return create_api_response('Success', message=message, data=response_data)
        
    except ValueError as e:
        error_message = str(e)
        message = f"Package update failed: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'update_package',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to update package: {package_id}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'update_package',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in update_package: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.delete("/packages/{package_id}")
async def delete_package(
    package_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None)
):
    """Delete a package"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Initialize package manager
        package_manager = PackageManager(graph_db)
        
        # Delete package
        success = package_manager.delete_package(package_id)
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'delete_package',
            'db_url': uri,
            'package_id': package_id,
            'success': success,
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        response_data = {
            'package_id': package_id,
            'deleted': success,
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Package '{package_id}' deleted successfully" if success else f"Failed to delete package '{package_id}'"
        status = 'Success' if success else 'Failed'
        return create_api_response(status, message=message, data=response_data)
        
    except ValueError as e:
        error_message = str(e)
        message = f"Cannot delete package: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'delete_package',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to delete package: {package_id}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'delete_package',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in delete_package: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.post("/document-packages")
async def create_document_package(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    package_name=Form(...),
    package_description=Form(None),
    workspace_id=Form("default_workspace"),
    tenant_id=Form("default_tenant")
):
    """
    Create a DocumentPackage root node for package management.
    This is the root container that will hold categories and the entire package hierarchy.
    """
    start_time = time.time()
    logging.info(f"create_document_package called with package_name: {package_name}")
    
    try:
        # Initialize graph database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Generate unique package ID
        package_id = f"pkg_{int(time.time())}_{package_name.lower().replace(' ', '_')}"
        
        # Create package metadata
        package_metadata = {
            'package_id': package_id,
            'package_name': package_name,
            'description': package_description or f"Document package: {package_name}",
            'workspace_id': workspace_id,
            'tenant_id': tenant_id,
            'metadata': {
                'created_by': 'user',
                'creation_timestamp': datetime.now(timezone.utc).isoformat(),
                'version': '1.0'
            }
        }
        
        # Create DocumentPackage node in Neo4j immediately
        success = graph_db.create_document_package_node(package_metadata)
        
        if not success:
            raise Exception("Failed to create DocumentPackage node in database")
        
        elapsed_time = time.time() - start_time
        
        response_data = {
            'package_id': package_id,
            'package_name': package_name,
            'description': package_description,
            'workspace_id': workspace_id,
            'tenant_id': tenant_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'processing_time': f"{elapsed_time:.2f}s"
        }
        
        logging.info(f"DocumentPackage created successfully: {package_id} in {elapsed_time:.2f}s")
        return create_api_response(status="Success", message=f"DocumentPackage '{package_name}' created successfully with ID: {package_id}", data=response_data)
        
    except Exception as e:
        error_message = str(e)
        logging.error(f"Error creating DocumentPackage: {error_message}")
        
        elapsed_time = time.time() - start_time
        return create_api_response(
            status="Failed", 
            message=f"DocumentPackage creation failed: {error_message}",
            data={
                "package_name": package_name,
                "error": error_message,
                "processing_time": f"{elapsed_time:.2f}s"
            }
        )
    finally:
        gc.collect()


@app.post("/categories")
async def create_category(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    category_code=Form(...),
    category_name=Form(...),
    category_description=Form(None),
    package_id=Form(None),
    tenant_id=Form("default_tenant")
):
    """
    Create a new mortgage category with immediate Neo4j node creation.
    Implements the 4-tier hierarchy with instant graph node creation.
    """
    start_time = time.time()
    logging.info(f"create_category called with category_code: {category_code}, category_name: {category_name}")
    
    try:
        # Initialize graph database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Create category metadata
        category_metadata = {
            'category_code': category_code,
            'display_name': category_name,
            'description': category_description or f"{category_code} mortgage category",
            'tenant_id': tenant_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Create category node in Neo4j immediately
        success = graph_db.create_category_node(category_metadata)
        
        if not success:
            raise Exception("Failed to create category node in database")
        
        # Link category to DocumentPackage if package_id is provided
        linked_to_package = False
        if package_id:
            try:
                logging.info(f"Attempting to link category {category_code} to DocumentPackage {package_id}")
                linked_to_package = graph_db.link_category_to_package(package_id, category_code)
                if linked_to_package:
                    logging.info(f"SUCCESS: Category {category_code} linked to DocumentPackage {package_id}")
                else:
                    logging.warning(f"FAILED: Failed to link category {category_code} to DocumentPackage {package_id}")
            except Exception as link_error:
                logging.error(f"EXCEPTION: Failed to link category to package: {str(link_error)}")
        else:
            logging.warning(f"No package_id provided for category {category_code} - DocumentPackage link not created")
        
        elapsed_time = time.time() - start_time
        
        response_data = {
            'category_id': f"cat_{category_code}_{int(time.time())}",
            'category_code': category_code,
            'category_name': category_name,
            'description': category_description,
            'node_created': True,
            'linked_to_package': linked_to_package,
            'package_id': package_id if package_id else None,
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Category '{category_name}' created successfully with immediate node creation"
        return create_api_response('Success', message=message, data=response_data)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to create category: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'create_category',
            'category_code': category_code,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in create_category: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.post("/products")
async def create_product(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    product_name=Form(...),
    product_description=Form(None),
    category_code=Form(...),
    tenant_id=Form("default_tenant")
):
    """
    Create a new product with immediate Neo4j node creation.
    Implements the 4-tier hierarchy with instant graph node creation.
    """
    start_time = time.time()
    logging.info(f"create_product called with product_name: {product_name}, category_code: {category_code}")
    
    try:
        # Initialize graph database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Create product data
        product_data = {
            'product_id': f"prod_{product_name.lower().replace(' ', '_')}_{int(time.time())}",
            'product_name': product_name,
            'description': product_description or f"{product_name} product",
            'product_type': 'core',
            'key_features': [],
            'underwriting_highlights': [],
            'target_borrowers': [],
            'tier_level': 1,
            'processing_priority': 1,
            'tenant_id': tenant_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Create product node in Neo4j immediately
        success = graph_db.create_product_node(product_data, category_code)
        
        if not success:
            raise Exception("Failed to create product node in database")
        
        elapsed_time = time.time() - start_time
        
        response_data = {
            'product_id': product_data['product_id'],
            'product_name': product_name,
            'description': product_description,
            'category_code': category_code,
            'node_created': True,
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Product '{product_name}' created successfully with immediate node creation"
        return create_api_response('Success', message=message, data=response_data)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to create product: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'create_product',
            'product_name': product_name,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in create_product: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.post("/programs")
async def create_program(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    program_name=Form(...),
    program_code=Form(...),
    program_description=Form(None),
    product_id=Form(...),
    tenant_id=Form("default_tenant")
):
    """
    Create a new program with immediate Neo4j node creation.
    Implements the 4-tier hierarchy with instant graph node creation.
    """
    start_time = time.time()
    logging.info(f"create_program called with program_name: {program_name}, product_id: {product_id}")
    
    try:
        # Initialize graph database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Create program data
        program_data = {
            'program_id': f"prog_{program_code.lower()}_{int(time.time())}",
            'program_name': program_name,
            'program_code': program_code,
            'description': program_description or f"{program_name} program",
            'program_type': 'standard',
            'loan_limits': {'max_amount': 1000000, 'min_amount': 100000},
            'rate_adjustments': [],
            'feature_differences': [],
            'qualification_criteria': [],
            'processing_priority': 1,
            'tenant_id': tenant_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Create program node in Neo4j immediately
        success = graph_db.create_program_node(program_data, product_id)
        
        if not success:
            raise Exception("Failed to create program node in database")
        
        elapsed_time = time.time() - start_time
        
        response_data = {
            'program_id': program_data['program_id'],
            'program_name': program_name,
            'program_code': program_code,
            'description': program_description,
            'product_id': product_id,
            'node_created': True,
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Program '{program_name}' created successfully with immediate node creation"
        return create_api_response('Success', message=message, data=response_data)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to create program: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'create_program',
            'program_name': program_name,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in create_program: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.post("/documents/update-type")
async def update_document_type(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    file_name=Form(...),
    document_type=Form(...),
    category_id=Form(None),
    product_id=Form(None),
    category_name=Form(None),
    product_name=Form(None)
):
    """
    Update document type and package associations for an existing document.
    """
    start_time = time.time()
    logging.info(f"update_document_type called with file_name: {file_name}, document_type: {document_type}")
    
    try:
        # Initialize graph database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Create package metadata for the document
        package_metadata = {
            'document_type': document_type,
            'category_id': category_id,
            'product_id': product_id,
            'category_name': category_name,
            'product_name': product_name,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Update document node with package metadata
        success = graph_db.add_package_metadata_to_document(file_name, package_metadata)
        
        if not success:
            raise Exception("Failed to update document type in database")
        
        elapsed_time = time.time() - start_time
        
        response_data = {
            'file_name': file_name,
            'document_type': document_type,
            'category_id': category_id,
            'product_id': product_id,
            'updated': True,
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Document '{file_name}' type updated to '{document_type}' successfully"
        return create_api_response('Success', message=message, data=response_data)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to update document type: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'update_document_type',
            'file_name': file_name,
            'document_type': document_type,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in update_document_type: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.post("/package-documents")
async def create_package_document(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    product_id=Form(...),
    document_name=Form(...),
    document_type=Form(...),
    expected_structure=Form(None),
    validation_rules=Form(None),
    required_sections=Form(None),
    optional_sections=Form(None)
):
    """
    Create a PackageDocument node representing an expected document.
    This is part of the package template structure.
    """
    start_time = time.time()
    logging.info(f"create_package_document called for product: {product_id}, document: {document_name}")
    
    try:
        # Initialize graph database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Parse JSON fields if provided
        expected_structure_data = json.loads(expected_structure) if expected_structure else {}
        validation_rules_data = json.loads(validation_rules) if validation_rules else {}
        required_sections_list = json.loads(required_sections) if required_sections else []
        optional_sections_list = json.loads(optional_sections) if optional_sections else []
        
        # Create package document data
        package_document_data = {
            'document_id': f"pkgdoc_{product_id}_{document_type.lower()}_{int(time.time())}",
            'document_name': document_name,
            'document_type': document_type,
            'expected_structure': expected_structure_data,
            'validation_rules': validation_rules_data,
            'required_sections': required_sections_list,
            'optional_sections': optional_sections_list
        }
        
        # Create package document node in Neo4j
        success = graph_db.create_package_document_node(package_document_data, product_id)
        
        if not success:
            raise Exception("Failed to create package document node in database")
        
        elapsed_time = time.time() - start_time
        
        response_data = {
            'document_id': package_document_data['document_id'],
            'document_name': document_name,
            'document_type': document_type,
            'product_id': product_id,
            'node_created': True,
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Package document '{document_name}' created successfully"
        return create_api_response('Success', message=message, data=response_data)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to create package document: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'create_package_document',
            'document_name': document_name,
            'product_id': product_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in create_package_document: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.get("/products/{product_id}/expected-documents")
async def get_expected_documents(
    product_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None)
):
    """
    Get list of expected documents for a product with upload status.
    Used to power the document type slots interface.
    """
    start_time = time.time()
    logging.info(f"get_expected_documents called for product: {product_id}")
    
    try:
        # Initialize graph database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Get expected documents with upload status
        expected_documents = graph_db.get_expected_documents_for_product(product_id)
        
        # Calculate completion status
        total_expected = len(expected_documents)
        uploaded_count = sum(1 for doc in expected_documents if doc['upload_status'] != 'empty')
        completion_percentage = (uploaded_count / total_expected * 100) if total_expected > 0 else 0
        
        # Get product name for context
        product_info = graph_db.get_product_info(product_id)
        product_name = product_info.get('product_name', 'Unknown Product') if product_info else 'Unknown Product'
        
        elapsed_time = time.time() - start_time
        
        response_data = {
            'product_id': product_id,
            'product_name': product_name,
            'expected_documents': expected_documents,
            'completion_status': {
                'total_expected': total_expected,
                'uploaded_count': uploaded_count,
                'completion_percentage': round(completion_percentage, 1)
            },
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Found {total_expected} expected documents for product {product_name}"
        return create_api_response('Success', message=message, data=response_data)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to get expected documents for product: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'get_expected_documents',
            'product_id': product_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in get_expected_documents: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.post("/package-documents/link-upload")
async def link_document_upload(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    document_filename=Form(...),
    package_document_id=Form(...)
):
    """
    Link an uploaded Document to its corresponding PackageDocument.
    This connects the expected document to the actual uploaded file.
    """
    start_time = time.time()
    logging.info(f"link_document_upload called: {document_filename} -> {package_document_id}")
    
    try:
        # Initialize graph database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Link the uploaded document to package document
        success = graph_db.link_uploaded_document_to_package_document(
            document_filename, 
            package_document_id
        )
        
        if not success:
            raise Exception("Failed to link document to package document")
        
        elapsed_time = time.time() - start_time
        
        response_data = {
            'document_filename': document_filename,
            'package_document_id': package_document_id,
            'linked': True,
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Document '{document_filename}' linked to package document successfully"
        return create_api_response('Success', message=message, data=response_data)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to link document: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'link_document_upload',
            'document_filename': document_filename,
            'package_document_id': package_document_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in link_document_upload: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.get("/packages/{package_id}/completion-status")
async def get_package_completion(
    package_id: str,
    uri: str = None,
    userName: str = None,
    password: str = None,
    database: str = None
):
    """Get completion status of all documents in a package"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Get completion status
        status = graph_db.get_package_completion_status(package_id)
        
        elapsed_time = time.time() - start
        
        return create_api_response(
            'Success',
            message=f"Package completion status retrieved in {elapsed_time:.2f}s",
            data=status
        )
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to get package completion status: {error_message}"
        logging.exception(f'Exception in get_package_completion: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.get("/products/{product_id}/discovered-programs")
async def get_discovered_programs(
    product_id: str,
    uri: str = None,
    userName: str = None,
    password: str = None,
    database: str = None
):
    """Get all programs discovered during document processing for a product"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Get discovered programs
        programs = graph_db.get_discovered_programs_for_product(product_id)
        
        elapsed_time = time.time() - start
        
        return create_api_response(
            'Success',
            message=f"Retrieved {len(programs)} discovered programs in {elapsed_time:.2f}s",
            data=programs
        )
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to get discovered programs: {error_message}"
        logging.exception(f'Exception in get_discovered_programs: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.post("/packages/{package_id}/clone")
async def clone_package(
    package_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    new_name=Form(...),
    category=Form(None),
    created_by=Form(None),
    customizations=Form(None)
):
    """Clone an existing package"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Initialize package manager
        package_manager = PackageManager(graph_db)
        
        # Prepare modifications
        modifications = {}
        
        if category:
            modifications['category'] = category
            
        if created_by:
            modifications['created_by'] = created_by
            
        if customizations:
            try:
                modifications['customizations'] = json.loads(customizations)
            except json.JSONDecodeError:
                return create_api_response('Failed', message='Invalid customizations JSON format')
        
        # Clone package
        cloned_package = package_manager.clone_package(package_id, new_name, modifications)
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'clone_package',
            'db_url': uri,
            'source_package_id': package_id,
            'cloned_package_id': cloned_package.package_id,
            'new_name': new_name,
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        # Prepare response data
        response_data = {
            'source_package_id': package_id,
            'cloned_package_id': cloned_package.package_id,
            'package_name': cloned_package.package_name,
            'category': cloned_package.category.value,
            'version': cloned_package.version,
            'status': cloned_package.status.value,
            'created_at': cloned_package.created_at.isoformat(),
            'document_count': len(cloned_package.documents),
            'relationship_count': len(cloned_package.relationships),
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Package '{package_id}' cloned successfully as '{cloned_package.package_id}'"
        return create_api_response('Success', message=message, data=response_data)
        
    except ValueError as e:
        error_message = str(e)
        message = f"Package cloning failed: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'clone_package',
            'source_package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to clone package: {package_id}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'clone_package',
            'source_package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in clone_package: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.get("/packages/{package_id}/versions")
async def get_package_versions(
    package_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None)
):
    """Get version history for a package"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Initialize version manager
        version_manager = PackageVersionManager(graph_db)
        
        # Get version history
        history = version_manager.get_version_history(package_id)
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'get_package_versions',
            'db_url': uri,
            'package_id': package_id,
            'version_count': len(history),
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        # Prepare response data
        versions_data = [
            {
                'version': record.version,
                'change_type': record.change_type.value,
                'changes': record.changes,
                'created_at': record.created_at.isoformat(),
                'created_by': record.created_by,
                'metadata': record.metadata
            }
            for record in history
        ]
        
        response_data = {
            'package_id': package_id,
            'versions': versions_data,
            'total_versions': len(history),
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Found {len(history)} versions for package '{package_id}'"
        return create_api_response('Success', message=message, data=response_data)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to get version history for package: {package_id}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'get_package_versions',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in get_package_versions: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.post("/packages/{package_id}/rollback")
async def rollback_package(
    package_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    target_version=Form(...),
    created_by=Form(None)
):
    """Rollback package to a previous version"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Initialize version manager
        version_manager = PackageVersionManager(graph_db)
        
        # Perform rollback
        restored_package = version_manager.rollback_version(
            package_id, 
            target_version, 
            created_by or userName or 'api_user'
        )
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'rollback_package',
            'db_url': uri,
            'package_id': package_id,
            'target_version': target_version,
            'new_version': restored_package.version,
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        # Prepare response data
        response_data = {
            'package_id': package_id,
            'target_version': target_version,
            'new_version': restored_package.version,
            'package_name': restored_package.package_name,
            'status': restored_package.status.value,
            'updated_at': restored_package.updated_at.isoformat(),
            'document_count': len(restored_package.documents),
            'relationship_count': len(restored_package.relationships),
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Package '{package_id}' rolled back to version {target_version} (new version: {restored_package.version})"
        return create_api_response('Success', message=message, data=response_data)
        
    except ValueError as e:
        error_message = str(e)
        message = f"Rollback failed: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'rollback_package',
            'package_id': package_id,
            'target_version': target_version,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to rollback package: {package_id}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'rollback_package',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in rollback_package: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.get("/packages/{package_id}/diff")
async def diff_package_versions(
    package_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    from_version=Form(...),
    to_version=Form(...)
):
    """Compare two versions of a package"""
    try:
        start = time.time()
        
        # Create database connection
        graph = create_graph_database_connection(uri, userName, password, database)
        graph_db = graphDBdataAccess(graph)
        
        # Initialize version manager
        version_manager = PackageVersionManager(graph_db)
        
        # Get version diff
        diff = version_manager.diff_versions(package_id, from_version, to_version)
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'diff_package_versions',
            'db_url': uri,
            'package_id': package_id,
            'from_version': from_version,
            'to_version': to_version,
            'has_changes': diff.has_changes(),
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        # Prepare response data
        response_data = {
            'package_id': package_id,
            'from_version': from_version,
            'to_version': to_version,
            'has_changes': diff.has_changes(),
            'added_documents': diff.added_documents,
            'removed_documents': diff.removed_documents,
            'modified_documents': diff.modified_documents,
            'structural_changes': diff.structural_changes,
            'relationship_changes': diff.relationship_changes,
            'summary': {
                'documents_added': len(diff.added_documents),
                'documents_removed': len(diff.removed_documents),
                'documents_modified': len(diff.modified_documents),
                'structural_changes_count': len(diff.structural_changes),
                'relationship_changes_count': len(diff.relationship_changes)
            },
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        message = f"Version comparison complete for package '{package_id}' between {from_version} and {to_version}"
        return create_api_response('Success', message=message, data=response_data)
        
    except ValueError as e:
        error_message = str(e)
        message = f"Version comparison failed: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'diff_package_versions',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except Exception as e:
        error_message = str(e)
        message = f"Failed to compare package versions: {package_id}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'diff_package_versions',
            'package_id': package_id,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in diff_package_versions: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.post("/packages/validate")
async def validate_package_config(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    package_name=Form(...),
    tenant_id=Form(...),
    category=Form(...),
    documents=Form(None),
    relationships=Form(None)
):
    """Validate package configuration without creating"""
    try:
        start = time.time()
        
        # Prepare package configuration for validation
        package_config = {
            'package_name': package_name,
            'tenant_id': tenant_id,
            'category': category,
            'created_by': 'validation_user'
        }
        
        # Parse documents if provided
        if documents:
            try:
                package_config['documents'] = json.loads(documents)
            except json.JSONDecodeError:
                return create_api_response('Failed', message='Invalid documents JSON format')
        
        # Parse relationships if provided
        if relationships:
            try:
                package_config['relationships'] = json.loads(relationships)
            except json.JSONDecodeError:
                return create_api_response('Failed', message='Invalid relationships JSON format')
        
        # Create temporary package for validation (in memory only)
        from src.entities.document_package import DocumentPackage, validate_package
        import uuid
        
        # Generate temporary ID for validation
        category_enum = PackageCategory(category)
        temp_package_id = f"temp_{category_enum.value.lower()}_{uuid.uuid4().hex[:8]}"
        
        # Create temporary package
        temp_package = DocumentPackage(
            package_id=temp_package_id,
            package_name=package_name,
            tenant_id=tenant_id,
            category=category_enum,
            version="1.0.0",
            status=PackageStatus.DRAFT,
            created_by='validation_user'
        )
        
        # Add documents if provided
        if 'documents' in package_config:
            from src.entities.document_package import DocumentDefinition
            for doc_config in package_config['documents']:
                doc = DocumentDefinition(
                    document_id=doc_config.get('document_id', f"doc_{uuid.uuid4().hex[:8]}"),
                    document_type=doc_config['document_type'],
                    document_name=doc_config['document_name'],
                    expected_structure=doc_config.get('expected_structure', {}),
                    required_sections=doc_config.get('required_sections', []),
                    optional_sections=doc_config.get('optional_sections', []),
                    chunking_strategy=doc_config.get('chunking_strategy', 'hierarchical'),
                    entity_types=doc_config.get('entity_types', []),
                    matrix_configuration=doc_config.get('matrix_configuration'),
                    validation_schema=doc_config.get('validation_schema', {}),
                    quality_thresholds=doc_config.get('quality_thresholds', {})
                )
                temp_package.add_document(doc)
        
        # Add relationships if provided
        if 'relationships' in package_config:
            from src.entities.document_package import PackageRelationship
            for rel_config in package_config['relationships']:
                rel = PackageRelationship(
                    from_document=rel_config['from_document'],
                    to_document=rel_config['to_document'],
                    relationship_type=rel_config['relationship_type'],
                    metadata=rel_config.get('metadata', {})
                )
                temp_package.relationships.append(rel)
        
        # Validate package
        validation_errors = validate_package(temp_package)
        
        end = time.time()
        elapsed_time = end - start
        
        # Log API call
        json_obj = {
            'api_name': 'validate_package_config',
            'db_url': uri,
            'package_name': package_name,
            'category': category,
            'is_valid': len(validation_errors) == 0,
            'error_count': len(validation_errors),
            'logging_time': formatted_time(datetime.now(timezone.utc)),
            'elapsed_api_time': f'{elapsed_time:.2f}',
            'userName': userName,
            'database': database
        }
        logger.log_struct(json_obj, "INFO")
        
        # Prepare response data
        is_valid = len(validation_errors) == 0
        response_data = {
            'is_valid': is_valid,
            'validation_errors': validation_errors,
            'package_name': package_name,
            'category': category,
            'document_count': len(temp_package.documents),
            'relationship_count': len(temp_package.relationships),
            'elapsed_api_time': f'{elapsed_time:.2f}'
        }
        
        if is_valid:
            message = f"Package configuration is valid"
            status = 'Success'
        else:
            message = f"Package configuration has {len(validation_errors)} validation errors"
            status = 'Failed'
            
        return create_api_response(status, message=message, data=response_data)
        
    except ValueError as e:
        error_message = str(e)
        message = f"Validation failed: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'validate_package_config',
            'package_name': package_name,
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        return create_api_response('Failed', message=message, error=error_message)
        
    except Exception as e:
        error_message = str(e)
        message = f"Validation error: {error_message}"
        json_obj = {
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'validate_package_config',
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in validate_package_config: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


# Package Processing API Endpoints
@app.post("/packages/process")
async def process_package(
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None),
    package_id=Form(...),
    model=Form(...),
    apikey=Form(None),
    base_url=Form(None),
    is_vector_selected=Form(True),
    is_graph_update=Form(False),
    language=Form('en'),
    chat_mode=Form(False),
    node_labels=Form(None),
    relationship_labels=Form(None),
    additional_instructions=Form(None)
):
    """Process all documents in a package using hierarchical chunking with database-stored packages"""
    try:
        start = time.time()
        
        # Parse additional instructions to detect package mode
        package_context = {}
        if additional_instructions:
            try:
                package_context = json.loads(additional_instructions)
            except json.JSONDecodeError:
                package_context = {'package_mode': True, 'package_id': package_id}
        
        # Get package documents from database
        graph = create_graph_database_connection(uri, userName, password, database)
        gdb = graphDBdataAccess(graph)
        package_docs = gdb.get_package_documents(package_id)
        
        if not package_docs:
            return create_api_response('Failed', message=f'No documents found in package {package_id}')
        
        # Get package metadata from database
        package_metadata = {
            'package_id': package_id,
            'total_documents': len(package_docs),
            'document_types': list(set(doc.get('document_type', 'Other') for doc in package_docs))
        }
        
        logging.info(f"Retrieved {len(package_docs)} documents from database for package {package_id}")
        
        # Initialize processing status
        processing_status = {
            'packageId': package_id,
            'status': 'processing',
            'progress': 0,
            'processedDocuments': 0,
            'totalDocuments': len(package_docs),
            'currentDocument': None,
            'startTime': datetime.now(timezone.utc).isoformat(),
            'results': []
        }
        
        # Store processing status (in practice, would use Redis or database)
        # For now, using in-memory storage
        app.state.processing_status = getattr(app.state, 'processing_status', {})
        app.state.processing_status[package_id] = processing_status
        
        # Process documents with package-aware chunking
        results = []
        success_count = 0
        failure_count = 0
        
        for i, doc in enumerate(package_docs):
            try:
                # Update processing status
                processing_status['currentDocument'] = doc.get('name', f'Document {i+1}')
                processing_status['progress'] = int((i / len(package_docs)) * 100)
                
                # Enhanced instructions for package processing with full context
                doc_instructions = f"""
                PACKAGE PROCESSING MODE - DATABASE STORED DOCUMENTS:
                - Package ID: {package_id}
                - Document: {doc.get('name', 'Unknown')}
                - Document Type: {doc.get('document_type', 'Other')}
                - Document ID: {doc.get('id', 'Unknown')}
                - Processing Type: {doc.get('processing_type', 'package')}
                - File Source: {doc.get('file_source', 'local')}
                
                HIERARCHICAL PROCESSING REQUIREMENTS:
                - Use hierarchical chunking with navigation extraction
                - Preserve document structure and relationships within package context
                - Extract package-aware entities and relationships
                - Enable cross-document relationships within the same package
                - Consider document context within the complete package hierarchy
                
                PACKAGE CONTEXT AND CROSS-DOCUMENT RELATIONSHIPS:
                - Total documents in package: {len(package_docs)}
                - Document types in package: {package_metadata.get('document_types', [])}
                - Package metadata: {json.dumps(package_metadata, indent=2)}
                - Enable relationship extraction between documents in the same package
                - Consider relationships to other documents: {[d.get('name', 'Unknown') for d in package_docs if d.get('id') != doc.get('id')]}
                
                DOCUMENT SPECIFIC CONFIGURATION:
                - Expected structure: {json.dumps(doc.get('expected_structure', {}), indent=2)}
                - Required sections: {doc.get('required_sections', [])}
                - Optional sections: {doc.get('optional_sections', [])}
                - Entity types: {doc.get('entity_types', [])}
                - Quality thresholds: {doc.get('quality_thresholds', {})}
                
                CROSS-DOCUMENT INTELLIGENCE:
                - Look for references to other documents in the same package
                - Extract relationships between entities across documents
                - Identify shared concepts and terminology
                - Maintain package-level entity consistency
                
                {additional_instructions or ''}
                """
                
                # Call the main processing function with package context
                # For package processing, we'll use the local file processing function
                # assuming documents are stored locally or we have the content
                
                # Parse node and relationship labels
                allowedNodes = []
                allowedRelationship = []
                if node_labels:
                    try:
                        allowedNodes = json.loads(node_labels) if isinstance(node_labels, str) else node_labels
                    except:
                        allowedNodes = []
                        
                if relationship_labels:
                    try:
                        allowedRelationship = json.loads(relationship_labels) if isinstance(relationship_labels, str) else relationship_labels
                    except:
                        allowedRelationship = []
                
                # Enhanced file processing with better validation and error handling
                doc_name = doc.get('name', f'doc_{i}')
                doc_id = doc.get('id', '')
                doc_type = doc.get('document_type', 'Other')
                file_source = doc.get('file_source', 'local')
                
                # Multiple strategies to locate the file
                merged_file_path = None
                file_found = False
                
                if doc_name:
                    # Strategy 1: Check sanitized filename in merged directory
                    sanitized_name = sanitize_filename(doc_name)
                    potential_path = os.path.join(MERGED_DIR, sanitized_name)
                    if os.path.exists(potential_path):
                        merged_file_path = potential_path
                        file_found = True
                        logging.info(f"Found document file: {potential_path}")
                    else:
                        # Strategy 2: Check original filename
                        original_path = os.path.join(MERGED_DIR, doc_name)
                        if os.path.exists(original_path):
                            merged_file_path = original_path
                            file_found = True
                            logging.info(f"Found document file with original name: {original_path}")
                        else:
                            # Strategy 3: Check if file exists with document ID
                            id_based_path = os.path.join(MERGED_DIR, f"{doc_id}_{sanitized_name}")
                            if os.path.exists(id_based_path):
                                merged_file_path = id_based_path
                                file_found = True
                                logging.info(f"Found document file with ID prefix: {id_based_path}")
                
                if file_found and merged_file_path:
                    # Process the document using the existing file
                    logging.info(f"Processing document: {doc_name} (Type: {doc_type}) from {merged_file_path}")
                    
                    # Check if Document node already exists from upload
                    graph = create_graph_database_connection(uri, userName, password, database)
                    graphDb_data_Access = graphDBdataAccess(graph)
                    existing_doc_result = graphDb_data_Access.get_current_status_document_node(doc_name)
                    
                    if existing_doc_result and len(existing_doc_result) > 0:
                        # Document exists from upload - update it and link to product
                        logging.info(f"Document node already exists for {doc_name} - updating existing node")
                        
                        # Update the existing Document node status to Processing  
                        obj_source_node = sourceNode()
                        obj_source_node.file_name = doc_name
                        obj_source_node.status = "Processing"
                        obj_source_node.model = model
                        graphDb_data_Access.update_source_node(obj_source_node)
                        
                        # Link document to appropriate level (product or program) immediately
                        if doc.get('associated_to') == 'program' and doc.get('parent_id'):
                            # Document belongs to a program
                            program_id = doc.get('parent_id')
                            link_success = graphDb_data_Access.link_document_to_program(doc_name, program_id)
                            if link_success:
                                logging.info(f"Successfully linked document {doc_name} to program {program_id}")
                            else:
                                logging.warning(f"Failed to link document {doc_name} to program {program_id}")
                        elif product_id:
                            # Document belongs to a product
                            link_success = graphDb_data_Access.link_document_to_product(doc_name, product_id)
                            if link_success:
                                logging.info(f"Successfully linked document {doc_name} to product {product_id}")
                            else:
                                logging.warning(f"Failed to link document {doc_name} to product {product_id}")
                        
                        # Enhance doc_instructions with category, product, and program metadata
                        enhanced_instructions = doc_instructions
                        
                        # Get category metadata
                        category_metadata = graphDb_data_Access.get_category_metadata(category)
                        category_context = ""
                        if category_metadata:
                            category_context = f"""
CATEGORY CONTEXT:
- Category: {category_metadata.get('display_name', category)}
- Description: {category_metadata.get('description', '')}
- Key Characteristics: {', '.join(category_metadata.get('key_characteristics', []))}
- Regulatory Framework: {category_metadata.get('regulatory_framework', '')}
- Risk Profile: {category_metadata.get('risk_profile', '')}
"""
                        
                        # Get product metadata
                        product_metadata = graphDb_data_Access.get_product_metadata(product_id) if product_id else {}
                        product_context = ""
                        if product_metadata:
                            product_context = f"""
PRODUCT CONTEXT:
- Product: {product_metadata.get('product_name', '')}
- Description: {product_metadata.get('description', '')}
- Key Features: {', '.join(product_metadata.get('key_features', []))}
- Underwriting Highlights: {', '.join(product_metadata.get('underwriting_highlights', []))}
- Target Borrowers: {', '.join(product_metadata.get('target_borrowers', []))}
- Product Type: {product_metadata.get('product_type', '')}
"""
                        
                        # Get program metadata if document is program-specific
                        program_context = ""
                        if doc.get('associated_to') == 'program' and doc.get('parent_id'):
                            program_metadata = graphDb_data_Access.get_program_metadata(doc.get('parent_id'))
                            if program_metadata:
                                loan_limits = program_metadata.get('loan_limits', {})
                                loan_limits_str = ', '.join([f"{k}: {v}" for k, v in loan_limits.items()]) if loan_limits else "Standard limits"
                                
                                program_context = f"""
PROGRAM CONTEXT:
- Program: {program_metadata.get('program_name', '')} ({program_metadata.get('program_code', '')})
- Description: {program_metadata.get('description', '')}
- Program Type: {program_metadata.get('program_type', '')}
- Loan Limits: {loan_limits_str}
- Rate Adjustments: {', '.join(program_metadata.get('rate_adjustments', []))}
- Feature Differences: {', '.join(program_metadata.get('feature_differences', []))}
- Qualification Criteria: {', '.join(program_metadata.get('qualification_criteria', []))}
"""
                        
                        # Combine all instructions with enhanced context
                        if category_metadata or product_metadata or program_context:
                            enhanced_instructions = f"""
{doc_instructions}

MORTGAGE PROCESSING CONTEXT:
{category_context}
{product_context}
{program_context}

ENTITY EXTRACTION GUIDANCE:
- Focus on entities relevant to {category_metadata.get('display_name', category)} mortgage category
- Pay special attention to {product_metadata.get('product_name', '')} product-specific terms
- Consider regulatory requirements: {category_metadata.get('regulatory_framework', '')}
- Extract underwriting criteria related to: {', '.join(product_metadata.get('underwriting_highlights', []))}
{f"- This document is program-specific for {program_metadata.get('program_name', '')} - focus on program-level variations and pricing" if program_context else ""}
"""
                        
                        # Process the document with enhanced context
                        uri_latency, result = await extract_graph_from_file_local_file(
                            uri=uri,
                            userName=userName,
                            password=password,
                            database=database,
                            model=model,
                            merged_file_path=merged_file_path,
                            fileName=doc_name,
                            allowedNodes=allowedNodes,
                            allowedRelationship=allowedRelationship,
                            token_chunk_size=512,
                            chunk_overlap=100,
                            chunks_to_combine=1,
                            retry_condition=False,
                            additional_instructions=enhanced_instructions
                        )
                    else:
                        # No existing Document node - proceed with enhanced processing
                        # Get category and product metadata for enhanced instructions
                        category_metadata = graphDb_data_Access.get_category_metadata(category)
                        product_metadata = graphDb_data_Access.get_product_metadata(product_id) if product_id else {}
                        
                        enhanced_instructions = doc_instructions
                        if category_metadata or product_metadata:
                            category_context = f"""
CATEGORY CONTEXT:
- Category: {category_metadata.get('display_name', category)}
- Description: {category_metadata.get('description', '')}
- Key Characteristics: {', '.join(category_metadata.get('key_characteristics', []))}
- Regulatory Framework: {category_metadata.get('regulatory_framework', '')}
- Risk Profile: {category_metadata.get('risk_profile', '')}
""" if category_metadata else ""
                        
                            product_context = f"""
PRODUCT CONTEXT:
- Product: {product_metadata.get('product_name', '')}
- Description: {product_metadata.get('description', '')}
- Key Features: {', '.join(product_metadata.get('key_features', []))}
- Underwriting Highlights: {', '.join(product_metadata.get('underwriting_highlights', []))}
- Target Borrowers: {', '.join(product_metadata.get('target_borrowers', []))}
- Product Type: {product_metadata.get('product_type', '')}
""" if product_metadata else ""
                        
                            enhanced_instructions = f"""
{doc_instructions}

MORTGAGE PROCESSING CONTEXT:
{category_context}
{product_context}

ENTITY EXTRACTION GUIDANCE:
- Focus on entities relevant to {category_metadata.get('display_name', category)} mortgage category
- Pay special attention to {product_metadata.get('product_name', '')} product-specific terms
- Consider regulatory requirements: {category_metadata.get('regulatory_framework', '')}
- Extract underwriting criteria related to: {', '.join(product_metadata.get('underwriting_highlights', []))}
"""
                        
                        uri_latency, result = await extract_graph_from_file_local_file(
                            uri=uri,
                            userName=userName,
                            password=password,
                            database=database,
                            model=model,
                            merged_file_path=merged_file_path,
                            fileName=doc_name,
                            allowedNodes=allowedNodes,
                            allowedRelationship=allowedRelationship,
                            token_chunk_size=512,
                            chunk_overlap=100,
                            chunks_to_combine=1,
                            retry_condition=False,
                            additional_instructions=enhanced_instructions
                        )
                else:
                    # File not found - create a detailed failed result with suggestions
                    logging.warning(f"Document file not found: {doc_name} (ID: {doc_id}, Type: {doc_type})")
                    logging.warning(f"Checked paths: {[os.path.join(MERGED_DIR, sanitized_name), os.path.join(MERGED_DIR, doc_name)]}")
                    
                    result = {
                        'status': 'Failed',
                        'error': f'Document file not found: {doc_name}. Please upload the file first.',
                        'details': {
                            'document_id': doc_id,
                            'document_type': doc_type,
                            'file_source': file_source,
                            'checked_paths': [
                                os.path.join(MERGED_DIR, sanitize_filename(doc_name)),
                                os.path.join(MERGED_DIR, doc_name),
                                os.path.join(MERGED_DIR, f"{doc_id}_{sanitize_filename(doc_name)}")
                            ]
                        },
                        'nodeCount': 0,
                        'relationshipCount': 0,
                        'processingTime': 0
                    }
                    uri_latency = 0
                
                if result.get('status') == 'Success':
                    success_count += 1
                    results.append({
                        'fileId': doc.get('id', ''),
                        'fileName': doc.get('name', ''),
                        'documentType': doc.get('document_type', 'Other'),
                        'status': 'completed',
                        'nodesCount': result.get('nodeCount', 0),
                        'relationshipsCount': result.get('relationshipCount', 0),
                        'processingTime': result.get('processingTime', 0),
                        'fileSource': doc.get('file_source', 'local'),
                        'fileFound': file_found,
                        'filePath': merged_file_path,
                        'packageContext': {
                            'packageId': package_id,
                            'expectedStructure': doc.get('expected_structure', {}),
                            'entityTypes': doc.get('entity_types', []),
                            'qualityThresholds': doc.get('quality_thresholds', {})
                        }
                    })
                else:
                    failure_count += 1
                    results.append({
                        'fileId': doc.get('id', ''),
                        'fileName': doc.get('name', ''),
                        'documentType': doc.get('document_type', 'Other'),
                        'status': 'failed',
                        'nodesCount': 0,
                        'relationshipsCount': 0,
                        'processingTime': 0,
                        'errorMessage': result.get('error', 'Processing failed'),
                        'errorDetails': result.get('details', {}),
                        'fileSource': doc.get('file_source', 'local'),
                        'fileFound': file_found,
                        'filePath': merged_file_path,
                        'packageContext': {
                            'packageId': package_id,
                            'expectedStructure': doc.get('expected_structure', {}),
                            'entityTypes': doc.get('entity_types', []),
                            'qualityThresholds': doc.get('quality_thresholds', {})
                        }
                    })
                
            except Exception as e:
                failure_count += 1
                logging.error(f"Exception processing document {doc.get('name', 'Unknown')}: {str(e)}")
                results.append({
                    'fileId': doc.get('id', ''),
                    'fileName': doc.get('name', ''),
                    'documentType': doc.get('document_type', 'Other'),
                    'status': 'failed',
                    'nodesCount': 0,
                    'relationshipsCount': 0,
                    'processingTime': 0,
                    'errorMessage': f'Exception during processing: {str(e)}',
                    'errorDetails': {
                        'document_id': doc.get('id', ''),
                        'document_type': doc.get('document_type', 'Other'),
                        'file_source': doc.get('file_source', 'local'),
                        'exception_type': type(e).__name__
                    },
                    'fileSource': doc.get('file_source', 'local'),
                    'fileFound': False,
                    'filePath': None,
                    'packageContext': {
                        'packageId': package_id,
                        'expectedStructure': doc.get('expected_structure', {}),
                        'entityTypes': doc.get('entity_types', []),
                        'qualityThresholds': doc.get('quality_thresholds', {})
                    }
                })
            
            # Update processed count
            processing_status['processedDocuments'] = i + 1
        
        # Finalize processing status with enhanced metrics
        processing_status['status'] = 'completed'
        processing_status['endTime'] = datetime.now(timezone.utc).isoformat()
        processing_status['results'] = {
            'files': results,
            'successCount': success_count,
            'failureCount': failure_count,
            'totalNodes': sum(r.get('nodesCount', 0) for r in results),
            'totalRelationships': sum(r.get('relationshipsCount', 0) for r in results),
            'packageMetrics': {
                'totalProcessingTime': sum(r.get('processingTime', 0) for r in results),
                'averageProcessingTime': sum(r.get('processingTime', 0) for r in results) / len(results) if results else 0,
                'filesFound': sum(1 for r in results if r.get('fileFound', False)),
                'filesNotFound': sum(1 for r in results if not r.get('fileFound', False)),
                'documentTypeBreakdown': {
                    doc_type: {'count': len([r for r in results if r.get('documentType') == doc_type]),
                               'success': len([r for r in results if r.get('documentType') == doc_type and r.get('status') == 'completed']),
                               'failed': len([r for r in results if r.get('documentType') == doc_type and r.get('status') == 'failed'])}
                    for doc_type in set(r.get('documentType', 'Other') for r in results)
                },
                'crossDocumentContext': {
                    'packageId': package_id,
                    'totalDocuments': len(package_docs),
                    'documentTypes': package_metadata.get('document_types', []),
                    'crossDocumentRelationshipsEnabled': True
                }
            }
        }
        
        end = time.time()
        elapsed_time = end - start
        
        # Enhanced logging with package-level context
        json_obj = {
            'package_id': package_id,
            'total_documents': len(package_docs),
            'success_count': success_count,
            'failure_count': failure_count,
            'processing_time': elapsed_time,
            'total_nodes': sum(r.get('nodesCount', 0) for r in results),
            'total_relationships': sum(r.get('relationshipsCount', 0) for r in results),
            'files_found': sum(1 for r in results if r.get('fileFound', False)),
            'files_not_found': sum(1 for r in results if not r.get('fileFound', False)),
            'document_types': package_metadata.get('document_types', []),
            'status': 'Success',
            'api_name': 'process_package',
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "INFO")
        
        # Clean up any duplicate Document nodes that weren't properly linked
        try:
            graph = create_graph_database_connection(uri, userName, password, database)
            graphDb_data_Access = graphDBdataAccess(graph)
            cleanup_success = graphDb_data_Access.cleanup_duplicate_documents(package_id)
            if cleanup_success:
                logging.info(f"Successfully cleaned up duplicate documents for package: {package_id}")
            else:
                logging.warning(f"Failed to clean up duplicate documents for package: {package_id}")
        except Exception as cleanup_error:
            logging.error(f"Error during duplicate document cleanup: {str(cleanup_error)}")
        
        return create_api_response('Success', 
                                   data={
                                       'processing_id': package_id,
                                       'status': processing_status,
                                       'package_metadata': package_metadata
                                   },
                                   message=f'Package processing completed: {success_count} succeeded, {failure_count} failed')
        
    except Exception as e:
        error_message = str(e)
        message = f"Package processing error: {error_message}"
        json_obj = {
            'package_id': package_id,
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'process_package',
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in process_package: {e}')
        return create_api_response('Failed', message=message, error=error_message)
    finally:
        gc.collect()


@app.get("/packages/{package_id}/processing-status")
async def get_package_processing_status(
    package_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None)
):
    """Get processing status for a package"""
    try:
        # Get processing status from memory (in practice, would use Redis or database)
        processing_status = getattr(app.state, 'processing_status', {})
        
        if package_id not in processing_status:
            return create_api_response('Failed', message='Package processing status not found')
        
        status = processing_status[package_id]
        
        return create_api_response('Success', 
                                   data=status,
                                   message='Processing status retrieved')
        
    except Exception as e:
        error_message = str(e)
        message = f"Error getting processing status: {error_message}"
        json_obj = {
            'package_id': package_id,
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'get_package_processing_status',
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in get_package_processing_status: {e}')
        return create_api_response('Failed', message=message, error=error_message)


@app.get("/packages/{package_id}/results")
async def get_package_processing_results(
    package_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None)
):
    """Get processing results for a package"""
    try:
        # Get processing status from memory (in practice, would use Redis or database)
        processing_status = getattr(app.state, 'processing_status', {})
        
        if package_id not in processing_status:
            return create_api_response('Failed', message='Package processing results not found')
        
        status = processing_status[package_id]
        
        if status.get('status') != 'completed':
            return create_api_response('Failed', message='Package processing not completed')
        
        results = status.get('results', {})
        
        return create_api_response('Success', 
                                   data=results,
                                   message='Processing results retrieved')
        
    except Exception as e:
        error_message = str(e)
        message = f"Error getting processing results: {error_message}"
        json_obj = {
            'package_id': package_id,
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'get_package_processing_results',
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in get_package_processing_results: {e}')
        return create_api_response('Failed', message=message, error=error_message)


@app.post("/packages/{package_id}/cancel")
async def cancel_package_processing(
    package_id: str,
    uri=Form(None),
    userName=Form(None),
    password=Form(None),
    database=Form(None)
):
    """Cancel processing for a package"""
    try:
        # Get processing status from memory (in practice, would use Redis or database)
        processing_status = getattr(app.state, 'processing_status', {})
        
        if package_id not in processing_status:
            return create_api_response('Failed', message='Package processing not found')
        
        status = processing_status[package_id]
        
        if status.get('status') in ['completed', 'failed']:
            return create_api_response('Failed', message='Package processing already finished')
        
        # Cancel processing
        status['status'] = 'cancelled'
        status['endTime'] = datetime.now(timezone.utc).isoformat()
        
        return create_api_response('Success', 
                                   data=status,
                                   message='Package processing cancelled')
        
    except Exception as e:
        error_message = str(e)
        message = f"Error cancelling processing: {error_message}"
        json_obj = {
            'package_id': package_id,
            'error_message': error_message,
            'status': 'Failed',
            'api_name': 'cancel_package_processing',
            'logging_time': formatted_time(datetime.now(timezone.utc))
        }
        logger.log_struct(json_obj, "ERROR")
        logging.exception(f'Exception in cancel_package_processing: {e}')
        return create_api_response('Failed', message=message, error=error_message)


if __name__ == "__main__":
    uvicorn.run(app)
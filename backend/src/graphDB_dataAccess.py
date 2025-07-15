import logging
import os
import time
from neo4j.exceptions import TransientError
from langchain_neo4j import Neo4jGraph
from src.shared.common_fn import create_gcs_bucket_folder_name_hashed, delete_uploaded_local_file, load_embedding_model
from src.document_sources.gcs_bucket import delete_file_from_gcs
from src.shared.constants import BUCKET_UPLOAD,NODEREL_COUNT_QUERY_WITH_COMMUNITY, NODEREL_COUNT_QUERY_WITHOUT_COMMUNITY
from src.entities.source_node import sourceNode
from src.communities import MAX_COMMUNITY_LEVELS
import json
from dotenv import load_dotenv

load_dotenv()

class graphDBdataAccess:

    def __init__(self, graph: Neo4jGraph):
        self.graph = graph

    def update_exception_db(self, file_name, exp_msg, retry_condition=None):
        try:
            job_status = "Failed"
            result = self.get_current_status_document_node(file_name)
            if len(result) > 0:
                is_cancelled_status = result[0]['is_cancelled']
                if bool(is_cancelled_status) == True:
                    job_status = 'Cancelled'
            if retry_condition is not None: 
                retry_condition = None
                self.graph.query("""MERGE(d:Document {fileName :$fName}) SET d.status = $status, d.errorMessage = $error_msg, d.retry_condition = $retry_condition""",
                            {"fName":file_name, "status":job_status, "error_msg":exp_msg, "retry_condition":retry_condition},session_params={"database":self.graph._database})
            else :    
                self.graph.query("""MERGE(d:Document {fileName :$fName}) SET d.status = $status, d.errorMessage = $error_msg""",
                            {"fName":file_name, "status":job_status, "error_msg":exp_msg},session_params={"database":self.graph._database})
        except Exception as e:
            error_message = str(e)
            logging.error(f"Error in updating document node status as failed: {error_message}")
            raise Exception(error_message)
        
    def create_source_node(self, obj_source_node:sourceNode):
        try:
            job_status = "New"
            logging.info(f"creating source node if does not exist in database {self.graph._database}")
            
            # Add diagnostic logging for problematic files
            if obj_source_node.file_name and 'titanium' in obj_source_node.file_name.lower():
                logging.warning(f"🔍 DIAGNOSTIC: Creating Document node for problematic file {obj_source_node.file_name}")
                logging.warning(f"🔍 File properties: size={obj_source_node.file_size}, type={obj_source_node.file_type}")
            self.graph.query("""MERGE(d:Document {fileName :$fn}) SET d.fileSize = $fs, d.fileType = $ft ,
                            d.status = $st, d.url = $url, d.awsAccessKeyId = $awsacc_key_id, 
                            d.fileSource = $f_source, d.createdAt = $c_at, d.updatedAt = $u_at, 
                            d.processingTime = $pt, d.errorMessage = $e_message, d.nodeCount= $n_count, 
                            d.relationshipCount = $r_count, d.model= $model, d.gcsBucket=$gcs_bucket, 
                            d.gcsBucketFolder= $gcs_bucket_folder, d.language= $language,d.gcsProjectId= $gcs_project_id,
                            d.is_cancelled=False, d.total_chunks=0, d.processed_chunk=0,
                            d.access_token=$access_token,
                            d.chunkNodeCount=$chunkNodeCount,d.chunkRelCount=$chunkRelCount,
                            d.entityNodeCount=$entityNodeCount,d.entityEntityRelCount=$entityEntityRelCount,
                            d.communityNodeCount=$communityNodeCount,d.communityRelCount=$communityRelCount""",
                            {"fn":obj_source_node.file_name, "fs":obj_source_node.file_size, "ft":obj_source_node.file_type, "st":job_status, 
                            "url":obj_source_node.url,
                            "awsacc_key_id":obj_source_node.awsAccessKeyId, "f_source":obj_source_node.file_source, "c_at":obj_source_node.created_at,
                            "u_at":obj_source_node.created_at, "pt":0, "e_message":'', "n_count":0, "r_count":0, "model":obj_source_node.model,
                            "gcs_bucket": obj_source_node.gcsBucket, "gcs_bucket_folder": obj_source_node.gcsBucketFolder, 
                            "language":obj_source_node.language, "gcs_project_id":obj_source_node.gcsProjectId,
                            "access_token":obj_source_node.access_token,
                            "chunkNodeCount":obj_source_node.chunkNodeCount,
                            "chunkRelCount":obj_source_node.chunkRelCount,
                            "entityNodeCount":obj_source_node.entityNodeCount,
                            "entityEntityRelCount":obj_source_node.entityEntityRelCount,
                            "communityNodeCount":obj_source_node.communityNodeCount,
                            "communityRelCount":obj_source_node.communityRelCount
                            },session_params={"database":self.graph._database})
        except Exception as e:
            error_message = str(e)
            logging.info(f"error_message = {error_message}")
            self.update_exception_db(self, obj_source_node.file_name, error_message)
            raise Exception(error_message)
        
    def update_source_node(self, obj_source_node:sourceNode):
        try:

            params = {}
            if obj_source_node.file_name is not None and obj_source_node.file_name != '':
                params['fileName'] = obj_source_node.file_name

            if obj_source_node.status is not None and obj_source_node.status != '':
                params['status'] = obj_source_node.status

            if obj_source_node.created_at is not None:
                params['createdAt'] = obj_source_node.created_at

            if obj_source_node.updated_at is not None:
                params['updatedAt'] = obj_source_node.updated_at

            if obj_source_node.processing_time is not None and obj_source_node.processing_time != 0:
                params['processingTime'] = round(obj_source_node.processing_time.total_seconds(),2)

            if obj_source_node.node_count is not None :
                params['nodeCount'] = obj_source_node.node_count

            if obj_source_node.relationship_count is not None :
                params['relationshipCount'] = obj_source_node.relationship_count

            if obj_source_node.model is not None and obj_source_node.model != '':
                params['model'] = obj_source_node.model

            if obj_source_node.total_chunks is not None and obj_source_node.total_chunks != 0:
                params['total_chunks'] = obj_source_node.total_chunks

            if obj_source_node.is_cancelled is not None:
                params['is_cancelled'] = obj_source_node.is_cancelled

            if obj_source_node.processed_chunk is not None :
                params['processed_chunk'] = obj_source_node.processed_chunk
            
            if obj_source_node.retry_condition is not None :
                params['retry_condition'] = obj_source_node.retry_condition    

            param= {"props":params}
            
            logging.info(f'Base Param value 1 : {param}')
            query = "MERGE(d:Document {fileName :$props.fileName}) SET d += $props"
            logging.info("Update source node properties")
            self.graph.query(query,param,session_params={"database":self.graph._database})
        except Exception as e:
            error_message = str(e)
            self.update_exception_db(self,self.file_name,error_message)
            raise Exception(error_message)
    
    def get_source_list(self):
        """
        Args:
            uri: URI of the graph to extract
            db_name: db_name is database name to connect to graph db
            userName: Username to use for graph creation ( if None will use username from config file )
            password: Password to use for graph creation ( if None will use password from config file )
            file: File object containing the PDF file to be used
            model: Type of model to use ('Diffbot'or'OpenAI GPT')
        Returns:
        Returns a list of sources that are in the database by querying the graph and
        sorting the list by the last updated date. 
        """
        logging.info("Get existing files list from graph")
        query = "MATCH(d:Document) WHERE d.fileName IS NOT NULL RETURN d ORDER BY d.updatedAt DESC"
        result = self.graph.query(query,session_params={"database":self.graph._database})
        list_of_json_objects = [entry['d'] for entry in result]
        return list_of_json_objects
        
    def update_KNN_graph(self):
        """
        Update the graph node with SIMILAR relationship where embedding scrore match
        """
        index = self.graph.query("""show indexes yield * where type = 'VECTOR' and name = 'vector'""",session_params={"database":self.graph._database})
        # logging.info(f'show index vector: {index}')
        knn_min_score = os.environ.get('KNN_MIN_SCORE')
        if len(index) > 0:
            logging.info('update KNN graph')
            self.graph.query("""MATCH (c:Chunk)
                                    WHERE c.embedding IS NOT NULL AND count { (c)-[:SIMILAR]-() } < 5
                                    CALL db.index.vector.queryNodes('vector', 6, c.embedding) yield node, score
                                    WHERE node <> c and score >= $score MERGE (c)-[rel:SIMILAR]-(node) SET rel.score = score
                                """,
                                {"score":float(knn_min_score)}
                                ,session_params={"database":self.graph._database})
        else:
            logging.info("Vector index does not exist, So KNN graph not update")

    def check_account_access(self, database):
        try:
            query_dbms_componenet = "call dbms.components() yield edition"
            result_dbms_componenet = self.graph.query(query_dbms_componenet,session_params={"database":self.graph._database})

            if  result_dbms_componenet[0]["edition"] == "enterprise":
                query = """
                SHOW USER PRIVILEGES 
                YIELD * 
                WHERE graph = $database AND action IN ['read'] 
                RETURN COUNT(*) AS readAccessCount
                """
            
                logging.info(f"Checking access for database: {database}")

                result = self.graph.query(query, params={"database": database},session_params={"database":self.graph._database})
                read_access_count = result[0]["readAccessCount"] if result else 0

                logging.info(f"Read access count: {read_access_count}")

                if read_access_count > 0:
                    logging.info("The account has read access.")
                    return False
                else:
                    logging.info("The account has write access.")
                    return True
            else:
                #Community version have no roles to execute admin command, so assuming write access as TRUE
                logging.info("The account has write access.")
                return True

        except Exception as e:
            logging.error(f"Error checking account access: {e}")
            return False

    def check_gds_version(self):
        try:
            gds_procedure_count = """
            SHOW FUNCTIONS YIELD name WHERE name STARTS WITH 'gds.version' RETURN COUNT(*) AS totalGdsProcedures
            """
            result = self.graph.query(gds_procedure_count,session_params={"database":self.graph._database})
            total_gds_procedures = result[0]['totalGdsProcedures'] if result else 0

            if total_gds_procedures > 0:
                logging.info("GDS is available in the database.")
                return True
            else:
                logging.info("GDS is not available in the database.")
                return False
        except Exception as e:
            logging.error(f"An error occurred while checking GDS version: {e}")
            return False
            
    def connection_check_and_get_vector_dimensions(self,database):
        """
        Get the vector index dimension from database and application configuration and DB connection status
        
        Args:
            uri: URI of the graph to extract
            userName: Username to use for graph creation ( if None will use username from config file )
            password: Password to use for graph creation ( if None will use password from config file )
            db_name: db_name is database name to connect to graph db
        Returns:
        Returns a status of connection from NEO4j is success or failure
        """
        
        db_vector_dimension = self.graph.query("""SHOW INDEXES YIELD *
                                    WHERE type = 'VECTOR' AND name = 'vector'
                                    RETURN options.indexConfig['vector.dimensions'] AS vector_dimensions
                                """,session_params={"database":self.graph._database})
        
        result_chunks = self.graph.query("""match (c:Chunk) return size(c.embedding) as embeddingSize, count(*) as chunks, 
                                                    count(c.embedding) as hasEmbedding
                                """,session_params={"database":self.graph._database})
        
        embedding_model = os.getenv('EMBEDDING_MODEL')
        embeddings, application_dimension = load_embedding_model(embedding_model)
        logging.info(f'embedding model:{embeddings} and dimesion:{application_dimension}')

        gds_status = self.check_gds_version()
        write_access = self.check_account_access(database=database)
        
        if self.graph:
            if len(db_vector_dimension) > 0:
                return {'db_vector_dimension': db_vector_dimension[0]['vector_dimensions'], 'application_dimension':application_dimension, 'message':"Connection Successful","gds_status":gds_status,"write_access":write_access}
            else:
                if len(db_vector_dimension) == 0 and len(result_chunks) == 0:
                    logging.info("Chunks and vector index does not exists in database")
                    return {'db_vector_dimension': 0, 'application_dimension':application_dimension, 'message':"Connection Successful","chunks_exists":False,"gds_status":gds_status,"write_access":write_access}
                elif len(db_vector_dimension) == 0 and result_chunks[0]['hasEmbedding']==0 and result_chunks[0]['chunks'] > 0:
                    return {'db_vector_dimension': 0, 'application_dimension':application_dimension, 'message':"Connection Successful","chunks_exists":True,"gds_status":gds_status,"write_access":write_access}
                else:
                    return {'message':"Connection Successful","gds_status": gds_status,"write_access":write_access}

    def execute_query(self, query, param=None,max_retries=3, delay=2):
        retries = 0
        while retries < max_retries:
            try:
                return self.graph.query(query, param,session_params={"database":self.graph._database})
            except TransientError as e:
                if "DeadlockDetected" in str(e):
                    retries += 1
                    logging.info(f"Deadlock detected. Retrying {retries}/{max_retries} in {delay} seconds...")
                    time.sleep(delay)  # Wait before retrying
                else:
                    raise 
        logging.error("Failed to execute query after maximum retries due to persistent deadlocks.")
        raise RuntimeError("Query execution failed after multiple retries due to deadlock.")

    def get_current_status_document_node(self, file_name):
        query = """
                MATCH(d:Document {fileName : $file_name}) RETURN d.status AS Status , d.processingTime AS processingTime, 
                d.nodeCount AS nodeCount, d.model as model, d.relationshipCount as relationshipCount,
                d.total_chunks AS total_chunks , d.fileSize as fileSize, 
                d.is_cancelled as is_cancelled, d.processed_chunk as processed_chunk, d.fileSource as fileSource,
                d.chunkNodeCount AS chunkNodeCount,
                d.chunkRelCount AS chunkRelCount,
                d.entityNodeCount AS entityNodeCount,
                d.entityEntityRelCount AS entityEntityRelCount,
                d.communityNodeCount AS communityNodeCount,
                d.communityRelCount AS communityRelCount,
                d.createdAt AS created_time
                """
        param = {"file_name" : file_name}
        return self.execute_query(query, param)
    
    def delete_file_from_graph(self, filenames, source_types, deleteEntities:str, merged_dir:str, uri):
        
        filename_list= list(map(str.strip, json.loads(filenames)))
        source_types_list= list(map(str.strip, json.loads(source_types)))
        gcs_file_cache = os.environ.get('GCS_FILE_CACHE')
        
        for (file_name,source_type) in zip(filename_list, source_types_list):
            merged_file_path = os.path.join(merged_dir, file_name)
            if source_type == 'local file' and gcs_file_cache == 'True':
                folder_name = create_gcs_bucket_folder_name_hashed(uri, file_name)
                delete_file_from_gcs(BUCKET_UPLOAD,folder_name,file_name)
            else:
                logging.info(f'Deleted File Path: {merged_file_path} and Deleted File Name : {file_name}')
                delete_uploaded_local_file(merged_file_path,file_name)
                
        query_to_delete_document="""
            MATCH (d:Document)
            WHERE d.fileName IN $filename_list AND coalesce(d.fileSource, "None") IN $source_types_list
            WITH COLLECT(d) AS documents
            CALL (documents) {
            UNWIND documents AS d
            optional match (d)<-[:PART_OF]-(c:Chunk) 
            detach delete c, d
            } IN TRANSACTIONS OF 1 ROWS
            """
        query_to_delete_document_and_entities = """
            MATCH (d:Document)
            WHERE d.fileName IN $filename_list AND coalesce(d.fileSource, "None") IN $source_types_list
            WITH COLLECT(d) AS documents
            CALL (documents) {
            UNWIND documents AS d
            OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)
            OPTIONAL MATCH (c:Chunk)-[:HAS_ENTITY]->(e)
            WITH d, c, e, documents
            WHERE NOT EXISTS {
                MATCH (e)<-[:HAS_ENTITY]-(c2)-[:PART_OF]->(d2:Document)
                WHERE NOT d2 IN documents
                }
            WITH d, COLLECT(c) AS chunks, COLLECT(e) AS entities
            FOREACH (chunk IN chunks | DETACH DELETE chunk)
            FOREACH (entity IN entities | DETACH DELETE entity)
            DETACH DELETE d
            } IN TRANSACTIONS OF 1 ROWS
            """
        query_to_delete_communities = """
            MATCH (c:`__Community__`)
            WHERE c.level = 0 AND NOT EXISTS { ()-[:IN_COMMUNITY]->(c) }
            DETACH DELETE c
            WITH 1 AS dummy
            UNWIND range(1, $max_level)  AS level
            CALL (level) {
                MATCH (c:`__Community__`)
                WHERE c.level = level AND NOT EXISTS { ()-[:PARENT_COMMUNITY]->(c) }
                DETACH DELETE c
                }
        """   
        param = {"filename_list" : filename_list, "source_types_list": source_types_list}
        community_param = {"max_level":MAX_COMMUNITY_LEVELS}
        if deleteEntities == "true":
            result = self.execute_query(query_to_delete_document_and_entities, param)
            _ = self.execute_query(query_to_delete_communities,community_param)
            logging.info(f"Deleting {len(filename_list)} documents = '{filename_list}' from '{source_types_list}' from database")
        else :
            result = self.execute_query(query_to_delete_document, param)    
            logging.info(f"Deleting {len(filename_list)} documents = '{filename_list}' from '{source_types_list}' with their entities from database")
        return len(filename_list)
    
    def list_unconnected_nodes(self):
        query = """
        MATCH (e:!Chunk&!Document&!`__Community__`) 
        WHERE NOT exists { (e)--(:!Chunk&!Document&!`__Community__`) }
        OPTIONAL MATCH (doc:Document)<-[:PART_OF]-(c:Chunk)-[:HAS_ENTITY]->(e)
        RETURN 
        e {
            .*,
            embedding: null,
            elementId: elementId(e),
            labels: CASE 
            WHEN size(labels(e)) > 1 THEN 
                apoc.coll.removeAll(labels(e), ["__Entity__"])
            ELSE 
                ["Entity"]
            END
        } AS e, 
        collect(distinct doc.fileName) AS documents, 
        count(distinct c) AS chunkConnections
        ORDER BY e.id ASC
        LIMIT 100
        """
        query_total_nodes = """
        MATCH (e:!Chunk&!Document&!`__Community__`) 
        WHERE NOT exists { (e)--(:!Chunk&!Document&!`__Community__`) }
        RETURN count(*) as total
        """
        nodes_list = self.execute_query(query)
        total_nodes = self.execute_query(query_total_nodes)
        return nodes_list, total_nodes[0]
    
    def delete_unconnected_nodes(self,unconnected_entities_list):
        entities_list = list(map(str.strip, json.loads(unconnected_entities_list)))
        query = """
        MATCH (e) WHERE elementId(e) IN $elementIds
        DETACH DELETE e
        """
        param = {"elementIds":entities_list}
        return self.execute_query(query,param)
    
    def get_duplicate_nodes_list(self):
        score_value = float(os.environ.get('DUPLICATE_SCORE_VALUE'))
        text_distance = int(os.environ.get('DUPLICATE_TEXT_DISTANCE'))
        query_duplicate_nodes = """
                MATCH (n:!Chunk&!Session&!Document&!`__Community__`) with n 
                WHERE n.embedding is not null and n.id is not null // and size(toString(n.id)) > 3
                WITH n ORDER BY count {{ (n)--() }} DESC, size(toString(n.id)) DESC // updated
                WITH collect(n) as nodes
                UNWIND nodes as n
                WITH n, [other in nodes 
                // only one pair, same labels e.g. Person with Person
                WHERE elementId(n) < elementId(other) and labels(n) = labels(other)
                // at least embedding similarity of X
                AND 
                (
                // either contains each other as substrings or has a text edit distinct of less than 3
                (size(toString(other.id)) > 2 AND toLower(toString(n.id)) CONTAINS toLower(toString(other.id))) OR 
                (size(toString(n.id)) > 2 AND toLower(toString(other.id)) CONTAINS toLower(toString(n.id)))
                OR (size(toString(n.id))>5 AND apoc.text.distance(toLower(toString(n.id)), toLower(toString(other.id))) < $duplicate_text_distance)
                OR
                vector.similarity.cosine(other.embedding, n.embedding) > $duplicate_score_value
                )] as similar
                WHERE size(similar) > 0 
                // remove duplicate subsets
                with collect([n]+similar) as all
                CALL {{ with all
                    unwind all as nodes
                    with nodes, all
                    // skip current entry if it's smaller and a subset of any other entry
                    where none(other in all where other <> nodes and size(other) > size(nodes) and size(apoc.coll.subtract(nodes, other))=0)
                    return head(nodes) as n, tail(nodes) as similar
                }}
                OPTIONAL MATCH (doc:Document)<-[:PART_OF]-(c:Chunk)-[:HAS_ENTITY]->(n)
                {return_statement}
                """
        return_query_duplicate_nodes = """
                RETURN n {.*, embedding:null, elementId:elementId(n), labels:labels(n)} as e, 
                [s in similar | s {.id, .description, labels:labels(s), elementId: elementId(s)}] as similar,
                collect(distinct doc.fileName) as documents, count(distinct c) as chunkConnections
                ORDER BY e.id ASC
                LIMIT 100
                """
        total_duplicate_nodes = "RETURN COUNT(DISTINCT(n)) as total"
        
        param = {"duplicate_score_value": score_value, "duplicate_text_distance" : text_distance}
        
        nodes_list = self.execute_query(query_duplicate_nodes.format(return_statement=return_query_duplicate_nodes),param=param)
        total_nodes = self.execute_query(query_duplicate_nodes.format(return_statement=total_duplicate_nodes),param=param)
        return nodes_list, total_nodes[0]
    
    def merge_duplicate_nodes(self,duplicate_nodes_list):
        nodes_list = json.loads(duplicate_nodes_list)
        logging.info(f'Nodes list to merge {nodes_list}')
        query = """
        UNWIND $rows AS row
        CALL { with row
        MATCH (first) WHERE elementId(first) = row.firstElementId
        MATCH (rest) WHERE elementId(rest) IN row.similarElementIds
        WITH first, collect (rest) as rest
        WITH [first] + rest as nodes
        CALL apoc.refactor.mergeNodes(nodes, 
        {properties:"discard",mergeRels:true, produceSelfRel:false, preserveExistingSelfRels:false, singleElementAsArray:true}) 
        YIELD node
        RETURN size(nodes) as mergedCount
        }
        RETURN sum(mergedCount) as totalMerged
        """
        param = {"rows":nodes_list}
        return self.execute_query(query,param)
    
    def drop_create_vector_index(self, isVectorIndexExist):
        """
        drop and create the vector index when vector index dimesion are different.
        """
        embedding_model = os.getenv('EMBEDDING_MODEL')
        embeddings, dimension = load_embedding_model(embedding_model)
        
        if isVectorIndexExist == 'true':
            self.graph.query("""drop index vector""",session_params={"database":self.graph._database})
        
        self.graph.query("""CREATE VECTOR INDEX `vector` if not exists for (c:Chunk) on (c.embedding)
                            OPTIONS {indexConfig: {
                            `vector.dimensions`: $dimensions,
                            `vector.similarity_function`: 'cosine'
                            }}
                        """,
                        {
                            "dimensions" : dimension
                        },session_params={"database":self.graph._database}
                        )
        return "Drop and Re-Create vector index succesfully"


    def update_node_relationship_count(self,document_name):
        logging.info("updating node and relationship count")
        label_query = """CALL db.labels"""
        community_flag = {'label': '__Community__'} in self.execute_query(label_query)
        if (not document_name) and (community_flag):
            result = self.execute_query(NODEREL_COUNT_QUERY_WITH_COMMUNITY)
        elif (not document_name) and (not community_flag):
             return []
        else:
            param = {"document_name": document_name}
            result = self.execute_query(NODEREL_COUNT_QUERY_WITHOUT_COMMUNITY, param)
        response = {}
        if result:
            for record in result:
                filename = record.get("filename",None)
                chunkNodeCount = int(record.get("chunkNodeCount",0))
                chunkRelCount = int(record.get("chunkRelCount",0))
                entityNodeCount = int(record.get("entityNodeCount",0))
                entityEntityRelCount = int(record.get("entityEntityRelCount",0))
                if (not document_name) and (community_flag):
                    communityNodeCount = int(record.get("communityNodeCount",0))
                    communityRelCount = int(record.get("communityRelCount",0))
                else:
                    communityNodeCount = 0
                    communityRelCount = 0
                nodeCount = int(chunkNodeCount) + int(entityNodeCount) + int(communityNodeCount)
                relationshipCount = int(chunkRelCount) + int(entityEntityRelCount) + int(communityRelCount)
                update_query = """
                MATCH (d:Document {fileName: $filename})
                SET d.chunkNodeCount = $chunkNodeCount,
                    d.chunkRelCount = $chunkRelCount,
                    d.entityNodeCount = $entityNodeCount,
                    d.entityEntityRelCount = $entityEntityRelCount,
                    d.communityNodeCount = $communityNodeCount,
                    d.communityRelCount = $communityRelCount,
                    d.nodeCount = $nodeCount,
                    d.relationshipCount = $relationshipCount
                """
                self.execute_query(update_query,{
                    "filename": filename,
                    "chunkNodeCount": chunkNodeCount,
                    "chunkRelCount": chunkRelCount,
                    "entityNodeCount": entityNodeCount,
                    "entityEntityRelCount": entityEntityRelCount,
                    "communityNodeCount": communityNodeCount,
                    "communityRelCount": communityRelCount,
                    "nodeCount" : nodeCount,
                    "relationshipCount" : relationshipCount
                    })
                
                response[filename] = {"chunkNodeCount": chunkNodeCount,
                    "chunkRelCount": chunkRelCount,
                    "entityNodeCount": entityNodeCount,
                    "entityEntityRelCount": entityEntityRelCount,
                    "communityNodeCount": communityNodeCount,
                    "communityRelCount": communityRelCount,
                    "nodeCount" : nodeCount,
                    "relationshipCount" : relationshipCount
                    }

        return response
    
    def get_nodelabels_relationships(self):
        node_query = """
                    CALL db.labels() YIELD label
                    WITH label
                    WHERE NOT label IN ['Document', 'Chunk', '_Bloom_Perspective_', '__Community__', '__Entity__']
                    CALL apoc.cypher.run("MATCH (n:`" + label + "`) RETURN count(n) AS count",{}) YIELD value
                    WHERE value.count > 0
                    RETURN label order by label
                    """

        relation_query = """
                CALL db.relationshipTypes() yield relationshipType
                WHERE NOT relationshipType  IN ['PART_OF', 'NEXT_CHUNK', 'HAS_ENTITY', '_Bloom_Perspective_','FIRST_CHUNK','SIMILAR','IN_COMMUNITY','PARENT_COMMUNITY'] 
                return relationshipType order by relationshipType
                """
            
        try:
            node_result = self.execute_query(node_query)
            node_labels = [record["label"] for record in node_result]
            relationship_result = self.execute_query(relation_query)
            relationship_types = [record["relationshipType"] for record in relationship_result]
            return node_labels,relationship_types
        except Exception as e:
            print(f"Error in getting node labels/relationship types from db: {e}")
            return []

    def get_websource_url(self,file_name):
        logging.info("Checking if same title with different URL exist in db ")
        query = """
                MATCH(d:Document {fileName : $file_name}) WHERE d.fileSource = "web-url" 
                RETURN d.url AS url
                """
        param = {"file_name" : file_name}
        return self.execute_query(query, param)

    # Task 5: Package Database Schema Implementation
    # Package Management Methods
    
    def create_package_node(self, package_data: dict) -> bool:
        """Create a DocumentPackage node in Neo4j"""
        try:
            logging.info(f"Creating package node: {package_data.get('package_id', 'unknown')}")
            
            query = """
            CREATE (p:DocumentPackage {
                package_id: $package_id,
                package_name: $package_name,
                tenant_id: $tenant_id,
                category: $category,
                version: $version,
                status: $status,
                created_by: $created_by,
                template_type: $template_type,
                created_at: $created_at,
                updated_at: $updated_at,
                template_mappings: $template_mappings,
                validation_rules: $validation_rules
            })
            RETURN p.package_id as package_id
            """
            
            params = {
                "package_id": package_data.get("package_id"),
                "package_name": package_data.get("package_name"),
                "tenant_id": package_data.get("tenant_id"),
                "category": package_data.get("category"),
                "version": package_data.get("version"),
                "status": package_data.get("status"),
                "created_by": package_data.get("created_by"),
                "template_type": package_data.get("template_type", ""),
                "created_at": package_data.get("created_at").isoformat() if package_data.get("created_at") else None,
                "updated_at": package_data.get("updated_at").isoformat() if package_data.get("updated_at") else None,
                "template_mappings": json.dumps(package_data.get("template_mappings", {})),
                "validation_rules": json.dumps(package_data.get("validation_rules", {}))
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating package node: {str(e)}")
            raise Exception(f"Failed to create package node: {str(e)}")
    
    def get_package_node(self, package_id: str) -> dict:
        """Retrieve a DocumentPackage node from Neo4j"""
        try:
            logging.info(f"Retrieving package node: {package_id}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})
            RETURN p.package_id as package_id,
                   p.package_name as package_name,
                   p.tenant_id as tenant_id,
                   p.category as category,
                   p.version as version,
                   p.status as status,
                   p.created_by as created_by,
                   p.template_type as template_type,
                   p.created_at as created_at,
                   p.updated_at as updated_at,
                   p.template_mappings as template_mappings,
                   p.validation_rules as validation_rules
            """
            
            params = {"package_id": package_id}
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            
            if result:
                package_data = result[0]
                # Parse JSON fields
                package_data["template_mappings"] = json.loads(package_data.get("template_mappings", "{}"))
                package_data["validation_rules"] = json.loads(package_data.get("validation_rules", "{}"))
                return package_data
            
            return None
            
        except Exception as e:
            logging.error(f"Error retrieving package node: {str(e)}")
            raise Exception(f"Failed to retrieve package node: {str(e)}")
    
    def update_package_node(self, package_id: str, package_data: dict) -> bool:
        """Update a DocumentPackage node in Neo4j"""
        try:
            logging.info(f"Updating package node: {package_id}")
            
            # Build dynamic update query
            set_clauses = []
            params = {"package_id": package_id}
            
            for field, value in package_data.items():
                if field == "package_id":
                    continue  # Don't update the ID
                
                if field in ["created_at", "updated_at"] and value:
                    value = value.isoformat() if hasattr(value, 'isoformat') else value
                elif field in ["template_mappings", "validation_rules"]:
                    value = json.dumps(value)
                
                set_clauses.append(f"p.{field} = ${field}")
                params[field] = value
            
            if not set_clauses:
                return True  # Nothing to update
            
            query = f"""
            MATCH (p:DocumentPackage {{package_id: $package_id}})
            SET {', '.join(set_clauses)}
            RETURN p.package_id as package_id
            """
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error updating package node: {str(e)}")
            raise Exception(f"Failed to update package node: {str(e)}")
    
    def delete_package_node(self, package_id: str) -> bool:
        """Delete a DocumentPackage node and all related nodes"""
        try:
            logging.info(f"Deleting package node: {package_id}")
            
            # Delete package and all related nodes/relationships (including product tier)
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})
            OPTIONAL MATCH (p)-[:CONTAINS]->(prod:PackageProduct)
            OPTIONAL MATCH (prod)-[:CONTAINS]->(d:PackageDocument)
            OPTIONAL MATCH (p)-[:CONTAINS]->(d2:PackageDocument)
            OPTIONAL MATCH (p)-[:VERSION_OF]->(v:PackageVersion)
            OPTIONAL MATCH (v)-[:SNAPSHOT]->(s:PackageSnapshot)
            DETACH DELETE p, prod, d, d2, v, s
            RETURN count(p) as deleted_count
            """
            
            params = {"package_id": package_id}
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            
            return result[0]["deleted_count"] > 0 if result else False
            
        except Exception as e:
            logging.error(f"Error deleting package node: {str(e)}")
            raise Exception(f"Failed to delete package node: {str(e)}")
    
    def list_packages(self, tenant_id: str = None, category: str = None, status: str = None) -> list:
        """List packages with optional filtering"""
        try:
            logging.info("Listing packages with filters")
            
            where_clauses = []
            params = {}
            
            if tenant_id:
                where_clauses.append("p.tenant_id = $tenant_id")
                params["tenant_id"] = tenant_id
            
            if category:
                where_clauses.append("p.category = $category")
                params["category"] = category
            
            if status:
                where_clauses.append("p.status = $status")
                params["status"] = status
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            query = f"""
            MATCH (p:DocumentPackage)
            WHERE {where_clause}
            RETURN p.package_id as package_id,
                   p.package_name as package_name,
                   p.tenant_id as tenant_id,
                   p.category as category,
                   p.version as version,
                   p.status as status,
                   p.created_by as created_by,
                   p.created_at as created_at,
                   p.updated_at as updated_at
            ORDER BY p.updated_at DESC
            """
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return result if result else []
            
        except Exception as e:
            logging.error(f"Error listing packages: {str(e)}")
            raise Exception(f"Failed to list packages: {str(e)}")

    # Package Product Methods
    
    def create_package_product(self, package_id: str, product_data: dict) -> bool:
        """Create a PackageProduct node and link to package"""
        try:
            logging.info(f"Creating package product: {product_data.get('product_id', 'unknown')}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})
            CREATE (prod:PackageProduct {
                product_id: $product_id,
                product_name: $product_name,
                product_type: $product_type,
                tier_level: $tier_level,
                processing_priority: $processing_priority,
                dependencies: $dependencies,
                created_at: $created_at,
                updated_at: $updated_at,
                metadata: $metadata
            })
            CREATE (p)-[:CONTAINS]->(prod)
            RETURN prod.product_id as product_id
            """
            
            params = {
                "package_id": package_id,
                "product_id": product_data.get("product_id"),
                "product_name": product_data.get("product_name"),
                "product_type": product_data.get("product_type"),
                "tier_level": product_data.get("tier_level", 1),
                "processing_priority": product_data.get("processing_priority", 1),
                "dependencies": json.dumps(product_data.get("dependencies", [])),
                "created_at": product_data.get("created_at").isoformat() if product_data.get("created_at") else None,
                "updated_at": product_data.get("updated_at").isoformat() if product_data.get("updated_at") else None,
                "metadata": json.dumps(product_data.get("metadata", {}))
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating package product: {str(e)}")
            raise Exception(f"Failed to create package product: {str(e)}")
    
    def create_product_document(self, package_id: str, product_id: str, document_data: dict) -> bool:
        """Create a PackageDocument node and link to a specific product"""
        try:
            logging.info(f"Creating product document: {document_data.get('document_id', 'unknown')} for product: {product_id}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:CONTAINS]->(prod:PackageProduct {product_id: $product_id})
            CREATE (d:PackageDocument {
                document_id: $document_id,
                document_type: $document_type,
                document_name: $document_name,
                expected_structure: $expected_structure,
                required_sections: $required_sections,
                optional_sections: $optional_sections,
                chunking_strategy: $chunking_strategy,
                entity_types: $entity_types,
                matrix_configuration: $matrix_configuration,
                validation_schema: $validation_schema,
                quality_thresholds: $quality_thresholds
            })
            CREATE (prod)-[:CONTAINS]->(d)
            RETURN d.document_id as document_id
            """
            
            params = {
                "package_id": package_id,
                "product_id": product_id,
                "document_id": document_data.get("document_id"),
                "document_type": document_data.get("document_type"),
                "document_name": document_data.get("document_name"),
                "expected_structure": json.dumps(document_data.get("expected_structure", {})),
                "required_sections": json.dumps(document_data.get("required_sections", [])),
                "optional_sections": json.dumps(document_data.get("optional_sections", [])),
                "chunking_strategy": document_data.get("chunking_strategy", "hierarchical"),
                "entity_types": json.dumps(document_data.get("entity_types", [])),
                "matrix_configuration": json.dumps(document_data.get("matrix_configuration")) if document_data.get("matrix_configuration") else None,
                "validation_schema": json.dumps(document_data.get("validation_schema", {})),
                "quality_thresholds": json.dumps(document_data.get("quality_thresholds", {}))
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating product document: {str(e)}")
            raise Exception(f"Failed to create product document: {str(e)}")

    def get_package_products(self, package_id: str) -> list:
        """Get all products for a package"""
        try:
            logging.info(f"Retrieving package products: {package_id}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:CONTAINS]->(prod:PackageProduct)
            RETURN prod.product_id as product_id,
                   prod.product_name as product_name,
                   prod.product_type as product_type,
                   prod.tier_level as tier_level,
                   prod.processing_priority as processing_priority,
                   prod.dependencies as dependencies,
                   prod.created_at as created_at,
                   prod.updated_at as updated_at,
                   prod.metadata as metadata
            ORDER BY prod.processing_priority, prod.product_name
            """
            
            params = {"package_id": package_id}
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            
            # Parse JSON fields
            products = []
            for prod in result:
                processed_prod = {
                    'product_id': prod.get('product_id'),
                    'product_name': prod.get('product_name'),
                    'product_type': prod.get('product_type'),
                    'tier_level': prod.get('tier_level', 1),
                    'processing_priority': prod.get('processing_priority', 1),
                    'dependencies': json.loads(prod.get("dependencies", "[]")),
                    'created_at': prod.get('created_at'),
                    'updated_at': prod.get('updated_at'),
                    'metadata': json.loads(prod.get("metadata", "{}"))
                }
                products.append(processed_prod)
            
            return products
            
        except Exception as e:
            logging.error(f"Error retrieving package products: {str(e)}")
            raise Exception(f"Failed to retrieve package products: {str(e)}")

    # DocumentPackage, Category and Product Node Methods
    
    def create_document_package_node(self, package_metadata: dict) -> bool:
        """Create a DocumentPackage root node for package management"""
        try:
            logging.info(f"Creating DocumentPackage node: {package_metadata.get('package_name', 'Unknown')}")
            
            query = """
            CREATE (dp:DocumentPackage {
                package_id: $package_id,
                package_name: $package_name,
                description: $description,
                created_at: datetime(),
                updated_at: datetime(),
                status: 'ACTIVE',
                workspace_id: $workspace_id,
                tenant_id: $tenant_id,
                metadata: $metadata
            })
            RETURN dp.package_id as package_id
            """
            
            params = {
                "package_id": package_metadata.get("package_id"),
                "package_name": package_metadata.get("package_name"),
                "description": package_metadata.get("description", ""),
                "workspace_id": package_metadata.get("workspace_id", "default_workspace"),
                "tenant_id": package_metadata.get("tenant_id", "default_tenant"),
                "metadata": json.dumps(package_metadata.get("metadata", {}))
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating DocumentPackage node: {str(e)}")
            return False
    
    def link_category_to_package(self, package_id: str, category_code: str) -> bool:
        """Create CONTAINS_CATEGORY relationship between DocumentPackage and MortgageCategory"""
        try:
            logging.info(f"Linking category {category_code} to package {package_id}")
            
            # First check if both nodes exist
            check_query = """
            MATCH (dp:DocumentPackage {package_id: $package_id})
            MATCH (mc:MortgageCategory {category_code: $category_code})
            RETURN dp.package_id as package_found, mc.category_code as category_found
            """
            
            check_result = self.graph.query(check_query, {
                "package_id": package_id,
                "category_code": category_code
            }, session_params={"database": self.graph._database})
            
            if len(check_result) == 0:
                logging.error(f"Either DocumentPackage {package_id} or MortgageCategory {category_code} not found")
                return False
            
            logging.info(f"Found both nodes: DocumentPackage {package_id} and MortgageCategory {category_code}")
            
            # Create the relationship
            query = """
            MATCH (dp:DocumentPackage {package_id: $package_id})
            MATCH (mc:MortgageCategory {category_code: $category_code})
            MERGE (dp)-[:CONTAINS_CATEGORY]->(mc)
            RETURN COUNT(*) as linked
            """
            
            params = {
                "package_id": package_id,
                "category_code": category_code
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            success = len(result) > 0 and result[0].get('linked', 0) > 0
            
            if success:
                logging.info(f"Successfully created CONTAINS_CATEGORY relationship: {package_id} -> {category_code}")
            else:
                logging.error(f"Failed to create CONTAINS_CATEGORY relationship: {package_id} -> {category_code}")
            
            return success
            
        except Exception as e:
            logging.error(f"Error linking category to package: {str(e)}")
            return False
    
    def create_category_node(self, category_metadata: dict) -> bool:
        """Create a MortgageCategory node with rich metadata"""
        try:
            logging.info(f"Creating category node: {category_metadata.get('display_name', 'Unknown')}")
            
            query = """
            MERGE (c:MortgageCategory {category_code: $category_code})
            SET c.display_name = $display_name,
                c.description = $description,
                c.key_characteristics = $key_characteristics,
                c.regulatory_framework = $regulatory_framework,
                c.typical_products = $typical_products,
                c.risk_profile = $risk_profile,
                c.created_at = datetime(),
                c.updated_at = datetime()
            RETURN c.category_code as category_code
            """
            
            params = {
                "category_code": category_metadata.get("category_code"),
                "display_name": category_metadata.get("display_name"),
                "description": category_metadata.get("description"),
                "key_characteristics": category_metadata.get("key_characteristics", []),
                "regulatory_framework": category_metadata.get("regulatory_framework", ""),
                "typical_products": category_metadata.get("typical_products", []),
                "risk_profile": category_metadata.get("risk_profile", "")
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating category node: {str(e)}")
            return False
    
    def create_product_node(self, product_data: dict, category_code: str) -> bool:
        """Create a Product node with rich metadata and link to category"""
        try:
            logging.info(f"Creating product node: {product_data.get('product_name', 'Unknown')}")
            
            query = """
            MATCH (c:MortgageCategory {category_code: $category_code})
            MERGE (p:Product {product_id: $product_id})
            SET p.product_name = $product_name,
                p.product_type = $product_type,
                p.description = $description,
                p.key_features = $key_features,
                p.underwriting_highlights = $underwriting_highlights,
                p.target_borrowers = $target_borrowers,
                p.tier_level = $tier_level,
                p.processing_priority = $processing_priority,
                p.created_at = datetime(),
                p.updated_at = datetime()
            MERGE (c)-[:CONTAINS]->(p)
            RETURN p.product_id as product_id
            """
            
            params = {
                "category_code": category_code,
                "product_id": product_data.get("product_id"),
                "product_name": product_data.get("product_name"),
                "product_type": product_data.get("product_type"),
                "description": product_data.get("description", ""),
                "key_features": product_data.get("key_features", []),
                "underwriting_highlights": product_data.get("underwriting_highlights", []),
                "target_borrowers": product_data.get("target_borrowers", []),
                "tier_level": product_data.get("tier_level", 1),
                "processing_priority": product_data.get("processing_priority", 1)
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating product node: {str(e)}")
            return False
    
    def link_document_to_product(self, document_filename: str, product_id: str) -> bool:
        """Link an existing Document node to a Product node"""
        try:
            logging.info(f"Linking document {document_filename} to product {product_id}")
            
            query = """
            MATCH (d:Document {fileName: $document_filename})
            MATCH (p:Product {product_id: $product_id})
            MERGE (p)-[:CONTAINS]->(d)
            RETURN d.fileName as document_name, p.product_id as product_id
            """
            
            params = {
                "document_filename": document_filename,
                "product_id": product_id
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error linking document to product: {str(e)}")
            return False
    
    def get_category_metadata(self, category_code: str) -> dict:
        """Retrieve category metadata for LLM processing"""
        try:
            query = """
            MATCH (c:MortgageCategory {category_code: $category_code})
            RETURN c.display_name as display_name,
                   c.description as description,
                   c.key_characteristics as key_characteristics,
                   c.regulatory_framework as regulatory_framework,
                   c.typical_products as typical_products,
                   c.risk_profile as risk_profile
            """
            
            result = self.execute_query(query, {"category_code": category_code})
            if result:
                return result[0]
            return {}
            
        except Exception as e:
            logging.error(f"Error retrieving category metadata: {str(e)}")
            return {}
    
    def get_product_metadata(self, product_id: str) -> dict:
        """Retrieve product metadata for LLM processing"""
        try:
            query = """
            MATCH (p:Product {product_id: $product_id})
            OPTIONAL MATCH (c:MortgageCategory)-[:CONTAINS]->(p)
            RETURN p.product_name as product_name,
                   p.description as description,
                   p.key_features as key_features,
                   p.underwriting_highlights as underwriting_highlights,
                   p.target_borrowers as target_borrowers,
                   p.product_type as product_type,
                   c.category_code as category_code,
                   c.display_name as category_display_name
            """
            
            result = self.execute_query(query, {"product_id": product_id})
            if result:
                return result[0]
            return {}
            
        except Exception as e:
            logging.error(f"Error retrieving product metadata: {str(e)}")
            return {}
    
    def add_package_metadata_to_document(self, file_name: str, package_metadata: dict) -> bool:
        """Add package context metadata to an existing Document node and create relationships"""
        try:
            # First, update the document metadata
            query = """
            MATCH (d:Document {fileName: $file_name})
            SET d.categoryId = $category_id,
                d.categoryName = $category_name,
                d.productId = $product_id,
                d.productName = $product_name,
                d.documentType = $document_type,
                d.expected_document_id = $expected_document_id,
                d.package_upload = true,
                d.created_via_package = true,
                d.updated_at = datetime()
            RETURN d.fileName as fileName
            """
            
            result = self.graph.query(query, {
                'file_name': file_name,
                'category_id': package_metadata.get('category_id'),
                'category_name': package_metadata.get('category_name'),
                'product_id': package_metadata.get('product_id'),
                'product_name': package_metadata.get('product_name'),
                'document_type': package_metadata.get('document_type'),
                'expected_document_id': package_metadata.get('expectedDocumentId')
            }, session_params={"database": self.graph._database})
            
            if len(result) == 0:
                logging.warning(f"Document {file_name} not found for metadata update")
                return False
            
            # Create relationships if category_id and product_id are provided
            if package_metadata.get('category_id') and package_metadata.get('product_id'):
                # Create relationship from Product to Document
                relationship_query = """
                MATCH (d:Document {fileName: $file_name})
                MATCH (p:Product {product_id: $product_id})
                MERGE (p)-[:CONTAINS_DOCUMENT]->(d)
                
                // Also create relationship from Category to Document for direct access
                WITH d, p
                MATCH (c:MortgageCategory)
                WHERE c.category_code = $category_code OR c.id = $category_id
                MERGE (c)-[:ASSOCIATED_DOCUMENT]->(d)
                
                RETURN d.fileName as fileName, p.product_id as product_id, c.category_code as category_code
                """
                
                # Extract category_code from category_id if it follows the pattern cat_CODE_timestamp
                category_id = package_metadata.get('category_id')
                category_code = category_id
                if category_id and category_id.startswith('cat_'):
                    parts = category_id.split('_')
                    if len(parts) >= 2:
                        category_code = parts[1]  # Extract 'NQM' from 'cat_NQM_1752608865'
                
                rel_result = self.graph.query(relationship_query, {
                    'file_name': file_name,
                    'product_id': package_metadata.get('product_id'),
                    'category_id': category_id,
                    'category_code': category_code
                }, session_params={"database": self.graph._database})
                
                if len(rel_result) > 0:
                    logging.info(f"Created relationships for document {file_name} to product {package_metadata.get('product_id')} and category {package_metadata.get('category_id')}")
                else:
                    logging.warning(f"Failed to create relationships for document {file_name}")
                
                # Note: Content nodes (Guidelines/Matrix) will be created during processing,
                # not during document type assignment. This maintains the two-structure separation.
                
                # Link Document to corresponding PackageDocument
                package_doc_result = self._link_document_to_package_document(
                    file_name, 
                    package_metadata.get('document_type'), 
                    package_metadata.get('product_id')
                )
                
                if package_doc_result:
                    logging.info(f"Linked Document {file_name} to PackageDocument")
                else:
                    logging.warning(f"Failed to link Document {file_name} to PackageDocument")
            
            return True
            
        except Exception as e:
            logging.error(f"Error adding package metadata to document {file_name}: {str(e)}")
            return False

    def get_document_package_info(self, file_name: str) -> dict:
        """Retrieve package metadata for a document to determine if enhanced processing should be used"""
        try:
            query = """
            MATCH (d:Document {fileName: $file_name})
            RETURN d.created_via_package as created_via_package,
                   d.package_upload as package_upload,
                   d.category_id as category_id,
                   d.category_name as category_name,
                   d.product_id as product_id,
                   d.product_name as product_name,
                   d.document_type as document_type
            """
            
            result = self.graph.query(query, {'file_name': file_name}, session_params={"database": self.graph._database})
            
            if result:
                record = result[0] if result else None
                
                if record:
                    return {
                        'created_via_package': record.get('created_via_package', False),
                        'package_upload': record.get('package_upload', False),
                        'category_id': record.get('category_id'),
                        'category_name': record.get('category_name'),
                        'product_id': record.get('product_id'),
                        'product_name': record.get('product_name'),
                        'document_type': record.get('document_type')
                    }
            
            return {}
                    
        except Exception as e:
            logging.error(f"Error retrieving package info for document {file_name}: {str(e)}")
            return {}

    def get_expected_documents_for_product(self, product_id: str) -> list:
        """
        Get all expected documents for a product with their upload status.
        Returns list of PackageDocument nodes with associated uploaded Document nodes.
        """
        try:
            query = """
            MATCH (prod:Product {product_id: $product_id})-[:EXPECTS_DOCUMENT]->(pd:PackageDocument)
            
            // Get uploaded document if it exists
            OPTIONAL MATCH (pd)-[:HAS_UPLOADED]->(d:Document)
            
            RETURN pd.document_id as document_id,
                   pd.document_type as document_type,
                   pd.document_name as document_name,
                   pd.expected_structure as expected_structure,
                   pd.validation_rules as validation_rules,
                   pd.required_sections as required_sections,
                   pd.optional_sections as optional_sections,
                   pd.has_upload as has_upload,
                   pd.processing_status as processing_status,
                   
                   // Document details if uploaded
                   d.fileName as uploaded_filename,
                   d.fileSize as uploaded_file_size,
                   d.createdAt as upload_date,
                   d.status as document_processing_status
                   
            ORDER BY pd.document_type, pd.document_name
            """
            
            result = self.graph.query(query, {'product_id': product_id}, session_params={"database": self.graph._database})
            
            expected_documents = []
            for record in result:
                doc_data = {
                    'id': record.get('document_id'),
                    'document_type': record.get('document_type'),
                    'document_name': record.get('document_name'),
                    'is_required': True,  # For now, all PackageDocuments are required
                    'upload_status': 'uploaded' if record.get('has_upload') else 'empty',
                    'uploaded_file': None,
                    'validation_rules': self._get_validation_rules_for_document_type(record.get('document_type')),
                    'expected_structure': json.loads(record.get('expected_structure') or '{}'),
                    'required_sections': record.get('required_sections', []),
                    'optional_sections': record.get('optional_sections', []),
                    'processing_status': record.get('processing_status', 'PENDING')
                }
                
                # Add uploaded file details if available
                if record.get('uploaded_filename'):
                    doc_data['uploaded_file'] = {
                        'fileName': record.get('uploaded_filename'),
                        'fileSize': record.get('uploaded_file_size'),
                        'uploadDate': record.get('upload_date'),
                        'processingStatus': record.get('document_processing_status', 'New')
                    }
                    
                    # Update upload status based on processing status
                    if record.get('document_processing_status') == 'Processing':
                        doc_data['upload_status'] = 'processing'
                    elif record.get('document_processing_status') in ['Completed', 'Failed']:
                        doc_data['upload_status'] = 'uploaded'
                
                expected_documents.append(doc_data)
            
            return expected_documents
            
        except Exception as e:
            logging.error(f"Error getting expected documents for product {product_id}: {str(e)}")
            return []

    def _get_validation_rules_for_document_type(self, document_type: str) -> dict:
        """Get validation rules based on document type"""
        
        validation_rules = {
            'Guidelines': {
                'accepted_types': ['.pdf', '.docx'],
                'accepted_mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
                'max_file_size': 50 * 1024 * 1024,  # 50MB
                'content_validation': 'guidelines_structure',
                'description': 'Underwriting guidelines and policy documents'
            },
            'Matrix': {
                'accepted_types': ['.pdf', '.xlsx', '.xls', '.csv'],
                'accepted_mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'text/csv'],
                'max_file_size': 25 * 1024 * 1024,  # 25MB
                'content_validation': 'matrix_structure',
                'description': 'Rate matrices and pricing tables'
            },
            'Supporting': {
                'accepted_types': ['.pdf', '.docx', '.xlsx', '.xls'],
                'accepted_mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'],
                'max_file_size': 30 * 1024 * 1024,  # 30MB
                'content_validation': 'supporting_document',
                'description': 'Supporting documentation and supplements'
            },
            'Other': {
                'accepted_types': ['.pdf', '.docx', '.xlsx', '.xls', '.txt', '.csv'],
                'accepted_mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'text/plain', 'text/csv'],
                'max_file_size': 100 * 1024 * 1024,  # 100MB
                'content_validation': 'none',
                'description': 'Other documents and miscellaneous files'
            }
        }
        
        return validation_rules.get(document_type, validation_rules['Other'])

    def get_product_info(self, product_id: str) -> dict:
        """Get basic product information"""
        try:
            query = """
            MATCH (p:Product {product_id: $product_id})
            RETURN p.product_name as product_name,
                   p.description as description,
                   p.category_code as category_code
            """
            
            result = self.graph.query(query, {'product_id': product_id}, session_params={"database": self.graph._database})
            
            if result:
                record = result[0] if result else None
                
                if record:
                    return {
                        'product_name': record.get('product_name'),
                        'description': record.get('description'),
                        'category_code': record.get('category_code')
                    }
            
            return {}
                    
        except Exception as e:
            logging.error(f"Error getting product info for {product_id}: {str(e)}")
            return {}

    def _link_document_to_package_document(self, file_name: str, document_type: str, product_id: str) -> bool:
        """Link an uploaded Document to its corresponding PackageDocument"""
        try:
            # First, remove any existing PackageDocument -> Document relationships for this document
            # This prevents duplicate relationships when document type is changed
            cleanup_query = """
            MATCH (d:Document {fileName: $file_name})
            MATCH (pd:PackageDocument)-[r:HAS_UPLOADED]->(d)
            DELETE r
            SET pd.has_upload = false,
                pd.uploaded_file = null,
                pd.upload_date = null,
                pd.processing_status = 'PENDING'
            RETURN COUNT(r) as removed_relationships
            """
            
            cleanup_result = self.graph.query(cleanup_query, {
                'file_name': file_name
            }, session_params={"database": self.graph._database})
            
            removed_count = cleanup_result[0].get('removed_relationships', 0) if cleanup_result else 0
            if removed_count > 0:
                logging.info(f"Removed {removed_count} existing PackageDocument relationships for {file_name}")
            
            # Now find the PackageDocument with matching document_type and product_id
            # and create HAS_UPLOADED relationship (PackageDocument -> Document)
            query = """
            MATCH (d:Document {fileName: $file_name})
            MATCH (prod:Product {product_id: $product_id})-[:EXPECTS_DOCUMENT]->(pd:PackageDocument {document_type: $document_type})
            
            // Create relationship from PackageDocument to Document (PackageDocument HAS_UPLOADED Document)
            MERGE (pd)-[:HAS_UPLOADED]->(d)
            
            // Update PackageDocument status
            SET pd.has_upload = true,
                pd.uploaded_file = $file_name,
                pd.upload_date = datetime(),
                pd.processing_status = 'UPLOADED'
            
            RETURN pd.document_id as package_document_id, d.fileName as document_name
            """
            
            params = {
                'file_name': file_name,
                'document_type': document_type,
                'product_id': product_id
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            
            if len(result) > 0:
                logging.info(f"Successfully linked Document {file_name} to PackageDocument {result[0].get('package_document_id')}")
                return True
            else:
                # Add debugging query to see what PackageDocuments exist for this product
                debug_query = """
                MATCH (prod:Product {product_id: $product_id})-[:EXPECTS_DOCUMENT]->(pd:PackageDocument)
                RETURN pd.document_type as existing_types, pd.document_name as existing_names, pd.document_id as existing_ids
                """
                debug_result = self.graph.query(debug_query, {'product_id': product_id}, session_params={"database": self.graph._database})
                logging.warning(f"No matching PackageDocument found for {file_name} with type '{document_type}' and product {product_id}")
                logging.warning(f"Available PackageDocuments for product {product_id}: {debug_result}")
                return False
                
        except Exception as e:
            logging.error(f"Error linking Document to PackageDocument: {str(e)}")
            return False

    def create_knowledge_structure_nodes(self, file_name: str, package_metadata: dict) -> bool:
        """Create knowledge extraction versions of DocumentPackage, MortgageCategory and Product nodes"""
        try:
            category_id = package_metadata.get('category_id')
            product_id = package_metadata.get('product_id')
            
            if not category_id or not product_id:
                logging.warning(f"Missing category_id or product_id for knowledge structure creation")
                return False
            
            # First, find the original DocumentPackage and create knowledge version
            package_query = """
            // Find the package management DocumentPackage that contains this category
            MATCH (pkg_dp:DocumentPackage)-[:CONTAINS_CATEGORY]->(pkg_cat:MortgageCategory {category_code: $category_id})
            
            // Create or update knowledge structure DocumentPackage
            MERGE (know_dp:DocumentPackage {package_id: pkg_dp.package_id, knowledge_extracted: true})
            SET know_dp.package_name = pkg_dp.package_name,
                know_dp.description = pkg_dp.description,
                know_dp.workspace_id = pkg_dp.workspace_id,
                know_dp.tenant_id = pkg_dp.tenant_id,
                know_dp.knowledge_extracted = true,
                know_dp.last_processed = datetime()
            
            RETURN know_dp.package_id as package_id
            """
            
            pkg_result = self.graph.query(package_query, {
                'category_id': category_id
            }, session_params={"database": self.graph._database})
            
            if len(pkg_result) == 0:
                logging.warning(f"Could not find DocumentPackage for category {category_id}")
                return False
            
            package_id = pkg_result[0].get('package_id')
            
            # Create knowledge structure MortgageCategory and link to knowledge DocumentPackage
            category_query = """
            // Find the package management category and knowledge DocumentPackage
            MATCH (pkg_cat:MortgageCategory {category_code: $category_id})
            MATCH (know_dp:DocumentPackage {package_id: $package_id, knowledge_extracted: true})
            
            // Create or update knowledge structure category
            MERGE (know_cat:MortgageCategory {category_code: $category_id, knowledge_extracted: true})
            SET know_cat.display_name = pkg_cat.display_name,
                know_cat.description = pkg_cat.description,
                know_cat.key_characteristics = pkg_cat.key_characteristics,
                know_cat.regulatory_framework = pkg_cat.regulatory_framework,
                know_cat.typical_products = pkg_cat.typical_products,
                know_cat.risk_profile = pkg_cat.risk_profile,
                know_cat.knowledge_extracted = true,
                know_cat.last_processed = datetime()
            
            // Create relationship in knowledge structure
            MERGE (know_dp)-[:CONTAINS_CATEGORY]->(know_cat)
            
            RETURN know_cat.category_code as category_code
            """
            
            cat_result = self.graph.query(category_query, {
                'category_id': category_id,
                'package_id': package_id
            }, session_params={"database": self.graph._database})
            
            # Create knowledge structure Product if it doesn't exist  
            product_query = """
            // Find the package management product
            MATCH (pkg_prod:Product {product_id: $product_id})
            
            // Find or create knowledge structure category
            MATCH (know_cat:MortgageCategory {category_code: $category_id, knowledge_extracted: true})
            
            // Create or update knowledge structure product
            MERGE (know_prod:Product {product_id: $product_id, knowledge_extracted: true})
            SET know_prod.product_name = pkg_prod.product_name,
                know_prod.product_type = pkg_prod.product_type,
                know_prod.description = pkg_prod.description,
                know_prod.loan_characteristics = pkg_prod.loan_characteristics,
                know_prod.eligible_borrowers = pkg_prod.eligible_borrowers,
                know_prod.underwriting_approach = pkg_prod.underwriting_approach,
                know_prod.knowledge_extracted = true,
                know_prod.last_processed = datetime()
            
            // Create relationship in knowledge structure
            MERGE (know_cat)-[:CONTAINS]->(know_prod)
            
            RETURN know_prod.product_id as product_id
            """
            
            prod_result = self.graph.query(product_query, {
                'product_id': product_id,
                'category_id': category_id
            }, session_params={"database": self.graph._database})
            
            # Link the Document to the knowledge structure
            doc_link_query = """
            MATCH (d:Document {fileName: $file_name})
            MATCH (know_prod:Product {product_id: $product_id, knowledge_extracted: true})
            
            // Create relationship from knowledge structure to document
            MERGE (know_prod)-[:EXTRACTED_FROM_DOCUMENT]->(d)
            
            RETURN d.fileName as document_name
            """
            
            doc_result = self.graph.query(doc_link_query, {
                'file_name': file_name,
                'product_id': product_id
            }, session_params={"database": self.graph._database})
            
            if len(pkg_result) > 0 and len(cat_result) > 0 and len(prod_result) > 0 and len(doc_result) > 0:
                logging.info(f"Successfully created complete knowledge structure for {file_name}")
                logging.info(f"Knowledge structure: DocumentPackage -> MortgageCategory -> Product -> Document")
                return True
            else:
                logging.warning(f"Failed to create complete knowledge structure for {file_name}")
                logging.warning(f"Results: pkg={len(pkg_result)}, cat={len(cat_result)}, prod={len(prod_result)}, doc={len(doc_result)}")
                return False
                
        except Exception as e:
            logging.error(f"Error creating knowledge structure nodes: {str(e)}")
            return False

    def create_program_node(self, program_data: dict, product_id: str) -> bool:
        """Create a Program node with rich metadata and link to product"""
        try:
            logging.info(f"Creating program node: {program_data.get('program_name', 'Unknown')}")
            
            query = """
            MATCH (p:Product {product_id: $product_id})
            MERGE (prog:Program {program_id: $program_id})
            SET prog.program_name = $program_name,
                prog.program_code = $program_code,
                prog.description = $description,
                prog.program_type = $program_type,
                prog.loan_limits = $loan_limits,
                prog.rate_adjustments = $rate_adjustments,
                prog.feature_differences = $feature_differences,
                prog.qualification_criteria = $qualification_criteria,
                prog.processing_priority = $processing_priority,
                prog.created_at = datetime(),
                prog.updated_at = datetime()
            MERGE (p)-[:CONTAINS]->(prog)
            RETURN prog.program_id as program_id
            """
            
            # Convert complex fields to JSON strings
            params = {
                "product_id": product_id,
                "program_id": program_data.get("program_id"),
                "program_name": program_data.get("program_name"),
                "program_code": program_data.get("program_code"),
                "description": program_data.get("description", ""),
                "program_type": program_data.get("program_type", "standard"),
                "loan_limits": json.dumps(program_data.get("loan_limits", {})),
                "rate_adjustments": program_data.get("rate_adjustments", []),
                "feature_differences": program_data.get("feature_differences", []),
                "qualification_criteria": program_data.get("qualification_criteria", []),
                "processing_priority": program_data.get("processing_priority", 1)
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating program node: {str(e)}")
            return False
    
    def link_document_to_program(self, document_filename: str, program_id: str) -> bool:
        """Link an existing Document node to a Program node"""
        try:
            logging.info(f"Linking document {document_filename} to program {program_id}")
            
            query = """
            MATCH (d:Document {fileName: $document_filename})
            MATCH (prog:Program {program_id: $program_id})
            MERGE (prog)-[:CONTAINS]->(d)
            RETURN d.fileName as document_name, prog.program_id as program_id
            """
            
            params = {
                "document_filename": document_filename,
                "program_id": program_id
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error linking document to program: {str(e)}")
            return False
    
    def get_program_metadata(self, program_id: str) -> dict:
        """Retrieve program metadata for LLM processing"""
        try:
            query = """
            MATCH (prog:Program {program_id: $program_id})
            OPTIONAL MATCH (p:Product)-[:CONTAINS]->(prog)
            OPTIONAL MATCH (c:MortgageCategory)-[:CONTAINS]->(p)
            RETURN prog.program_name as program_name,
                   prog.program_code as program_code,
                   prog.description as description,
                   prog.program_type as program_type,
                   prog.loan_limits as loan_limits,
                   prog.rate_adjustments as rate_adjustments,
                   prog.feature_differences as feature_differences,
                   prog.qualification_criteria as qualification_criteria,
                   p.product_id as product_id,
                   p.product_name as product_name,
                   c.category_code as category_code,
                   c.display_name as category_display_name
            """
            
            result = self.graph.query(query, {"program_id": program_id}, session_params={"database": self.graph._database})
            if result:
                # Parse JSON fields back to objects
                metadata = result[0]
                if metadata.get('loan_limits'):
                    try:
                        metadata['loan_limits'] = json.loads(metadata['loan_limits'])
                    except json.JSONDecodeError:
                        metadata['loan_limits'] = {}
                return metadata
            return {}
            
        except Exception as e:
            logging.error(f"Error retrieving program metadata: {str(e)}")
            return {}
    
    # Package Document Methods
    
    def cleanup_duplicate_documents(self, package_id: str) -> bool:
        """Clean up duplicate Document nodes for PackageDocument relationships"""
        try:
            logging.info(f"Cleaning up duplicate documents for package: {package_id}")
            
            # Find PackageDocument nodes that have corresponding Document nodes
            # and merge duplicate information
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})
            MATCH (p)-[:CONTAINS*1..2]->(pd:PackageDocument)
            OPTIONAL MATCH (pd)-[:REPRESENTS]->(doc:Document {fileName: pd.document_name})
            WHERE doc IS NULL
            WITH pd
            OPTIONAL MATCH (duplicate_doc:Document {fileName: pd.document_name})
            WHERE duplicate_doc IS NOT NULL
            CREATE (pd)-[:REPRESENTS]->(duplicate_doc)
            RETURN count(pd) as linked_count
            """
            
            result = self.execute_query(query, {"package_id": package_id})
            linked_count = result[0]['linked_count'] if result else 0
            
            logging.info(f"Linked {linked_count} PackageDocument nodes to existing Document nodes")
            return True
            
        except Exception as e:
            logging.error(f"Error cleaning up duplicate documents: {str(e)}")
            return False
    
    def create_package_document(self, package_id: str, document_data: dict, product_id: str = None) -> bool:
        """Create a PackageDocument node and link to product or package, while linking to existing Document node"""
        try:
            logging.info(f"Creating package document: {document_data.get('document_id', 'unknown')}")
            
            if product_id:
                # New 3-tier hierarchy: link to product and existing Document node
                query = """
                MATCH (p:DocumentPackage {package_id: $package_id})-[:CONTAINS]->(prod:PackageProduct {product_id: $product_id})
                CREATE (d:PackageDocument {
                    document_id: $document_id,
                    document_type: $document_type,
                    document_name: $document_name,
                    expected_structure: $expected_structure,
                    required_sections: $required_sections,
                    optional_sections: $optional_sections,
                    chunking_strategy: $chunking_strategy,
                    entity_types: $entity_types,
                    matrix_configuration: $matrix_configuration,
                    validation_schema: $validation_schema,
                    quality_thresholds: $quality_thresholds
                })
                CREATE (prod)-[:CONTAINS]->(d)
                // Link to existing Document node if it exists
                WITH d
                OPTIONAL MATCH (doc:Document {fileName: $document_name})
                FOREACH (existing_doc IN CASE WHEN doc IS NOT NULL THEN [doc] ELSE [] END |
                    CREATE (d)-[:REPRESENTS]->(existing_doc)
                )
                RETURN d.document_id as document_id
                """
                params = {
                    "package_id": package_id,
                    "product_id": product_id,
                    "document_id": document_data.get("document_id"),
                    "document_type": document_data.get("document_type"),
                    "document_name": document_data.get("document_name"),
                    "expected_structure": json.dumps(document_data.get("expected_structure", {})),
                    "required_sections": json.dumps(document_data.get("required_sections", [])),
                    "optional_sections": json.dumps(document_data.get("optional_sections", [])),
                    "chunking_strategy": document_data.get("chunking_strategy", "hierarchical"),
                    "entity_types": json.dumps(document_data.get("entity_types", [])),
                    "matrix_configuration": json.dumps(document_data.get("matrix_configuration")) if document_data.get("matrix_configuration") else None,
                    "validation_schema": json.dumps(document_data.get("validation_schema", {})),
                    "quality_thresholds": json.dumps(document_data.get("quality_thresholds", {}))
                }
            else:
                # Backwards compatibility: link directly to package and existing Document node
                query = """
                MATCH (p:DocumentPackage {package_id: $package_id})
                CREATE (d:PackageDocument {
                    document_id: $document_id,
                    document_type: $document_type,
                    document_name: $document_name,
                    expected_structure: $expected_structure,
                    required_sections: $required_sections,
                    optional_sections: $optional_sections,
                    chunking_strategy: $chunking_strategy,
                    entity_types: $entity_types,
                    matrix_configuration: $matrix_configuration,
                    validation_schema: $validation_schema,
                    quality_thresholds: $quality_thresholds
                })
                CREATE (p)-[:CONTAINS]->(d)
                // Link to existing Document node if it exists
                WITH d
                OPTIONAL MATCH (doc:Document {fileName: $document_name})
                FOREACH (existing_doc IN CASE WHEN doc IS NOT NULL THEN [doc] ELSE [] END |
                    CREATE (d)-[:REPRESENTS]->(existing_doc)
                )
                RETURN d.document_id as document_id
                """
                params = {
                    "package_id": package_id,
                    "document_id": document_data.get("document_id"),
                    "document_type": document_data.get("document_type"),
                    "document_name": document_data.get("document_name"),
                    "expected_structure": json.dumps(document_data.get("expected_structure", {})),
                    "required_sections": json.dumps(document_data.get("required_sections", [])),
                    "optional_sections": json.dumps(document_data.get("optional_sections", [])),
                    "chunking_strategy": document_data.get("chunking_strategy", "hierarchical"),
                    "entity_types": json.dumps(document_data.get("entity_types", [])),
                    "matrix_configuration": json.dumps(document_data.get("matrix_configuration")) if document_data.get("matrix_configuration") else None,
                    "validation_schema": json.dumps(document_data.get("validation_schema", {})),
                    "quality_thresholds": json.dumps(document_data.get("quality_thresholds", {}))
                }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating package document: {str(e)}")
            raise Exception(f"Failed to create package document: {str(e)}")
    
    def get_package_documents(self, package_id: str) -> list:
        """Get all documents for a package with file information - supports 3-tier hierarchy"""
        try:
            logging.info(f"Retrieving package documents: {package_id}")
            
            # Try 3-tier hierarchy first: Package -> Product -> Document
            query_3tier = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:CONTAINS]->(prod:PackageProduct)-[:CONTAINS]->(d:PackageDocument)
            RETURN d.document_id as document_id,
                   d.document_type as document_type,
                   d.document_name as document_name,
                   d.expected_structure as expected_structure,
                   d.required_sections as required_sections,
                   d.optional_sections as optional_sections,
                   d.chunking_strategy as chunking_strategy,
                   d.entity_types as entity_types,
                   d.matrix_configuration as matrix_configuration,
                   d.validation_schema as validation_schema,
                   d.quality_thresholds as quality_thresholds,
                   d.file_size as file_size,
                   d.file_source as file_source,
                   d.processing_type as processing_type,
                   d.status as status,
                   d.created_at as created_at,
                   d.updated_at as updated_at,
                   prod.product_id as product_id,
                   prod.product_name as product_name,
                   prod.product_type as product_type,
                   prod.tier_level as tier_level,
                   prod.processing_priority as processing_priority
            ORDER BY prod.processing_priority, prod.product_name, d.document_type, d.document_name
            """
            
            # Fallback to 2-tier hierarchy: Package -> Document (backwards compatibility)
            query_2tier = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:CONTAINS]->(d:PackageDocument)
            WHERE NOT EXISTS((p)-[:CONTAINS]->(:PackageProduct)-[:CONTAINS]->(d))
            RETURN d.document_id as document_id,
                   d.document_type as document_type,
                   d.document_name as document_name,
                   d.expected_structure as expected_structure,
                   d.required_sections as required_sections,
                   d.optional_sections as optional_sections,
                   d.chunking_strategy as chunking_strategy,
                   d.entity_types as entity_types,
                   d.matrix_configuration as matrix_configuration,
                   d.validation_schema as validation_schema,
                   d.quality_thresholds as quality_thresholds,
                   d.file_size as file_size,
                   d.file_source as file_source,
                   d.processing_type as processing_type,
                   d.status as status,
                   d.created_at as created_at,
                   d.updated_at as updated_at,
                   null as product_id,
                   null as product_name,
                   null as product_type,
                   null as tier_level,
                   null as processing_priority
            ORDER BY d.document_type, d.document_name
            """
            
            params = {"package_id": package_id}
            
            # Execute 3-tier query first
            result_3tier = self.execute_query(query_3tier, params)
            
            # Execute 2-tier query for backwards compatibility
            result_2tier = self.execute_query(query_2tier, params)
            
            # Combine results
            result = result_3tier + result_2tier
            
            # Parse JSON fields and format for processing
            documents = []
            for doc in result:
                processed_doc = {
                    'id': doc.get('document_id'),
                    'name': doc.get('document_name'),
                    'document_type': doc.get('document_type', 'Other'),
                    'package_id': package_id,
                    'package_name': f'Package {package_id}',
                    'processing_type': doc.get('processing_type', 'package'),
                    'file_source': doc.get('file_source', 'local'),
                    'size': doc.get('file_size', 0),
                    'status': doc.get('status', 'pending'),
                    'created_at': doc.get('created_at'),
                    'updated_at': doc.get('updated_at'),
                    'expected_structure': json.loads(doc.get("expected_structure", "{}")),
                    'required_sections': json.loads(doc.get("required_sections", "[]")),
                    'optional_sections': json.loads(doc.get("optional_sections", "[]")),
                    'entity_types': json.loads(doc.get("entity_types", "[]")),
                    'matrix_configuration': json.loads(doc.get("matrix_configuration")) if doc.get("matrix_configuration") else None,
                    'validation_schema': json.loads(doc.get("validation_schema", "{}")),
                    'quality_thresholds': json.loads(doc.get("quality_thresholds", "{}")),
                    # Product-tier information
                    'product_id': doc.get('product_id'),
                    'product_name': doc.get('product_name'),
                    'product_type': doc.get('product_type'),
                    'tier_level': doc.get('tier_level'),
                    'processing_priority': doc.get('processing_priority')
                }
                documents.append(processed_doc)
            
            return documents
            
        except Exception as e:
            logging.error(f"Error retrieving package documents: {str(e)}")
            raise Exception(f"Failed to retrieve package documents: {str(e)}")

    # Package Relationship Methods
    
    def create_package_relationship(self, package_id: str, relationship_data: dict) -> bool:
        """Create a relationship between package documents"""
        try:
            logging.info(f"Creating package relationship: {relationship_data.get('from_document', 'unknown')} -> {relationship_data.get('to_document', 'unknown')}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:CONTAINS]->(from_doc:PackageDocument {document_id: $from_document})
            MATCH (p)-[:CONTAINS]->(to_doc:PackageDocument {document_id: $to_document})
            CREATE (from_doc)-[r:RELATIONSHIP {
                relationship_type: $relationship_type,
                metadata: $metadata
            }]->(to_doc)
            RETURN r
            """
            
            params = {
                "package_id": package_id,
                "from_document": relationship_data.get("from_document"),
                "to_document": relationship_data.get("to_document"),
                "relationship_type": relationship_data.get("relationship_type"),
                "metadata": json.dumps(relationship_data.get("metadata", {}))
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating package relationship: {str(e)}")
            raise Exception(f"Failed to create package relationship: {str(e)}")
    
    def get_package_relationships(self, package_id: str) -> list:
        """Get all relationships for a package"""
        try:
            logging.info(f"Retrieving package relationships: {package_id}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:CONTAINS]->(from_doc:PackageDocument)
            MATCH (from_doc)-[r:RELATIONSHIP]->(to_doc:PackageDocument)
            MATCH (p)-[:CONTAINS]->(to_doc)
            RETURN from_doc.document_id as from_document,
                   to_doc.document_id as to_document,
                   r.relationship_type as relationship_type,
                   r.metadata as metadata
            """
            
            params = {"package_id": package_id}
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            
            # Parse JSON metadata
            relationships = []
            for rel in result:
                rel["metadata"] = json.loads(rel.get("metadata", "{}"))
                relationships.append(rel)
            
            return relationships
            
        except Exception as e:
            logging.error(f"Error retrieving package relationships: {str(e)}")
            raise Exception(f"Failed to retrieve package relationships: {str(e)}")

    # Package Version Methods
    
    def create_version_record(self, package_id: str, version_data: dict) -> bool:
        """Create a version record for a package"""
        try:
            logging.info(f"Creating version record: {version_data.get('version', 'unknown')}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})
            CREATE (v:PackageVersion {
                version: $version,
                change_type: $change_type,
                changes: $changes,
                created_at: $created_at,
                created_by: $created_by,
                metadata: $metadata
            })
            CREATE (p)-[:VERSION_OF]->(v)
            RETURN v.version as version
            """
            
            params = {
                "package_id": package_id,
                "version": version_data.get("version"),
                "change_type": version_data.get("change_type"),
                "changes": json.dumps(version_data.get("changes", [])),
                "created_at": version_data.get("created_at").isoformat() if version_data.get("created_at") else None,
                "created_by": version_data.get("created_by"),
                "metadata": json.dumps(version_data.get("metadata", {}))
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating version record: {str(e)}")
            raise Exception(f"Failed to create version record: {str(e)}")
    
    def get_version_history(self, package_id: str) -> list:
        """Get version history for a package"""
        try:
            logging.info(f"Retrieving version history: {package_id}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:VERSION_OF]->(v:PackageVersion)
            RETURN v.version as version,
                   v.change_type as change_type,
                   v.changes as changes,
                   v.created_at as created_at,
                   v.created_by as created_by,
                   v.metadata as metadata
            ORDER BY v.created_at DESC
            """
            
            params = {"package_id": package_id}
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            
            # Parse JSON fields
            versions = []
            for version in result:
                version["changes"] = json.loads(version.get("changes", "[]"))
                version["metadata"] = json.loads(version.get("metadata", "{}"))
                versions.append(version)
            
            return versions
            
        except Exception as e:
            logging.error(f"Error retrieving version history: {str(e)}")
            raise Exception(f"Failed to retrieve version history: {str(e)}")

    # Package Snapshot Methods
    
    def create_package_snapshot(self, package_id: str, version: str, snapshot_data: dict) -> bool:
        """Create a package snapshot for rollback"""
        try:
            logging.info(f"Creating package snapshot: {package_id} v{version}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:VERSION_OF]->(v:PackageVersion {version: $version})
            CREATE (s:PackageSnapshot {
                package_id: $package_id,
                version: $version,
                snapshot_data: $snapshot_data,
                created_at: $created_at
            })
            CREATE (v)-[:SNAPSHOT]->(s)
            RETURN s
            """
            
            params = {
                "package_id": package_id,
                "version": version,
                "snapshot_data": json.dumps(snapshot_data),
                "created_at": snapshot_data.get("snapshot_created")
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating package snapshot: {str(e)}")
            raise Exception(f"Failed to create package snapshot: {str(e)}")
    
    def get_package_snapshot(self, package_id: str, version: str) -> dict:
        """Get package snapshot for a specific version"""
        try:
            logging.info(f"Retrieving package snapshot: {package_id} v{version}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:VERSION_OF]->(v:PackageVersion {version: $version})-[:SNAPSHOT]->(s:PackageSnapshot)
            RETURN s.snapshot_data as snapshot_data,
                   s.created_at as created_at
            """
            
            params = {"package_id": package_id, "version": version}
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            
            if result:
                snapshot = result[0]
                snapshot["snapshot_data"] = json.loads(snapshot.get("snapshot_data", "{}"))
                return snapshot["snapshot_data"]
            
            return None
            
        except Exception as e:
            logging.error(f"Error retrieving package snapshot: {str(e)}")
            raise Exception(f"Failed to retrieve package snapshot: {str(e)}")

    # Package Schema Validation and Migration
    
    def validate_package_schema(self) -> dict:
        """Validate package schema in database"""
        try:
            logging.info("Validating package schema")
            
            validation_results = {
                "valid": True,
                "issues": [],
                "recommendations": []
            }
            
            # Check for required indexes
            index_query = "SHOW INDEXES"
            indexes = self.execute_query(index_query)
            
            required_indexes = [
                "DocumentPackage.package_id",
                "DocumentPackage.tenant_id",
                "PackageDocument.document_id",
                "PackageVersion.version"
            ]
            
            existing_indexes = [idx.get("labelsOrTypes", []) for idx in indexes]
            
            for required_index in required_indexes:
                if not any(required_index in str(idx) for idx in existing_indexes):
                    validation_results["issues"].append(f"Missing index: {required_index}")
                    validation_results["recommendations"].append(f"CREATE INDEX FOR (n:{required_index.split('.')[0]}) ON (n.{required_index.split('.')[1]})")
            
            # Check for constraint violations
            constraint_query = "SHOW CONSTRAINTS"
            constraints = self.execute_query(constraint_query)
            
            if not any("DocumentPackage" in str(c) and "package_id" in str(c) for c in constraints):
                validation_results["issues"].append("Missing uniqueness constraint on DocumentPackage.package_id")
                validation_results["recommendations"].append("CREATE CONSTRAINT package_id_unique FOR (p:DocumentPackage) REQUIRE p.package_id IS UNIQUE")
            
            validation_results["valid"] = len(validation_results["issues"]) == 0
            
            return validation_results
            
        except Exception as e:
            logging.error(f"Error validating package schema: {str(e)}")
            return {
                "valid": False,
                "issues": [f"Schema validation failed: {str(e)}"],
                "recommendations": []
            }
    
    def migrate_package_schema(self) -> bool:
        """Create package schema indexes and constraints"""
        try:
            logging.info("Migrating package schema")
            
            # Create indexes for performance
            index_queries = [
                "CREATE INDEX package_id_index IF NOT EXISTS FOR (p:DocumentPackage) ON (p.package_id)",
                "CREATE INDEX package_tenant_index IF NOT EXISTS FOR (p:DocumentPackage) ON (p.tenant_id)",
                "CREATE INDEX package_category_index IF NOT EXISTS FOR (p:DocumentPackage) ON (p.category)",
                "CREATE INDEX package_status_index IF NOT EXISTS FOR (p:DocumentPackage) ON (p.status)",
                "CREATE INDEX product_id_index IF NOT EXISTS FOR (prod:PackageProduct) ON (prod.product_id)",
                "CREATE INDEX product_type_index IF NOT EXISTS FOR (prod:PackageProduct) ON (prod.product_type)",
                "CREATE INDEX product_priority_index IF NOT EXISTS FOR (prod:PackageProduct) ON (prod.processing_priority)",
                "CREATE INDEX document_id_index IF NOT EXISTS FOR (d:PackageDocument) ON (d.document_id)",
                "CREATE INDEX version_index IF NOT EXISTS FOR (v:PackageVersion) ON (v.version)"
            ]
            
            # Create constraints for data integrity
            constraint_queries = [
                "CREATE CONSTRAINT package_id_unique IF NOT EXISTS FOR (p:DocumentPackage) REQUIRE p.package_id IS UNIQUE",
                "CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (prod:PackageProduct) REQUIRE prod.product_id IS UNIQUE",
                "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:PackageDocument) REQUIRE d.document_id IS UNIQUE"
            ]
            
            # Execute index creation
            for query in index_queries:
                try:
                    self.execute_query(query)
                    logging.info(f"Created index: {query}")
                except Exception as e:
                    logging.warning(f"Index creation failed (may already exist): {str(e)}")
            
            # Execute constraint creation
            for query in constraint_queries:
                try:
                    self.execute_query(query)
                    logging.info(f"Created constraint: {query}")
                except Exception as e:
                    logging.warning(f"Constraint creation failed (may already exist): {str(e)}")
            
            logging.info("Package schema migration completed")
            return True
            
        except Exception as e:
            logging.error(f"Error migrating package schema: {str(e)}")
            raise Exception(f"Failed to migrate package schema: {str(e)}")

    # Utility Methods for Package Integration
    
    def package_exists(self, package_id: str) -> bool:
        """Check if a package exists"""
        try:
            query = "MATCH (p:DocumentPackage {package_id: $package_id}) RETURN count(p) as count"
            result = self.execute_query(query, {"package_id": package_id})
            return result[0]["count"] > 0 if result else False
        except Exception as e:
            logging.error(f"Error checking package existence: {str(e)}")
            return False
    
    def get_package_statistics(self, package_id: str = None) -> dict:
        """Get package statistics"""
        try:
            if package_id:
                query = """
                MATCH (p:DocumentPackage {package_id: $package_id})
                OPTIONAL MATCH (p)-[:CONTAINS]->(d:PackageDocument)
                OPTIONAL MATCH (p)-[:VERSION_OF]->(v:PackageVersion)
                RETURN p.package_id as package_id,
                       count(DISTINCT d) as document_count,
                       count(DISTINCT v) as version_count
                """
                params = {"package_id": package_id}
            else:
                query = """
                MATCH (p:DocumentPackage)
                OPTIONAL MATCH (p)-[:CONTAINS]->(d:PackageDocument)
                OPTIONAL MATCH (p)-[:VERSION_OF]->(v:PackageVersion)
                RETURN count(DISTINCT p) as total_packages,
                       count(DISTINCT d) as total_documents,
                       count(DISTINCT v) as total_versions
                """
                params = {}
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return result[0] if result else {}
            
        except Exception as e:
            logging.error(f"Error getting package statistics: {str(e)}")
            return {}

    def cleanup_orphaned_package_data(self) -> dict:
        """Clean up orphaned package data"""
        try:
            logging.info("Cleaning up orphaned package data")
            
            cleanup_stats = {
                "orphaned_documents": 0,
                "orphaned_products": 0,
                "orphaned_versions": 0,
                "orphaned_snapshots": 0
            }
            
            # Clean up orphaned documents (not connected to package or product)
            orphaned_docs_query = """
            MATCH (d:PackageDocument)
            WHERE NOT EXISTS((p:DocumentPackage)-[:CONTAINS]->(d)) 
            AND NOT EXISTS((prod:PackageProduct)-[:CONTAINS]->(d))
            DETACH DELETE d
            RETURN count(d) as count
            """
            result = self.execute_query(orphaned_docs_query)
            cleanup_stats["orphaned_documents"] = result[0]["count"] if result else 0
            
            # Clean up orphaned products
            orphaned_products_query = """
            MATCH (prod:PackageProduct)
            WHERE NOT EXISTS((p:DocumentPackage)-[:CONTAINS]->(prod))
            DETACH DELETE prod
            RETURN count(prod) as count
            """
            result = self.execute_query(orphaned_products_query)
            cleanup_stats["orphaned_products"] = result[0]["count"] if result else 0
            
            # Clean up orphaned versions
            orphaned_versions_query = """
            MATCH (v:PackageVersion)
            WHERE NOT EXISTS((p:DocumentPackage)-[:VERSION_OF]->(v))
            DETACH DELETE v
            RETURN count(v) as count
            """
            result = self.execute_query(orphaned_versions_query)
            cleanup_stats["orphaned_versions"] = result[0]["count"] if result else 0
            
            # Clean up orphaned snapshots
            orphaned_snapshots_query = """
            MATCH (s:PackageSnapshot)
            WHERE NOT EXISTS((v:PackageVersion)-[:SNAPSHOT]->(s))
            DETACH DELETE s
            RETURN count(s) as count
            """
            result = self.graph.query(orphaned_snapshots_query, {}, session_params={"database": self.graph._database})
            cleanup_stats["orphaned_snapshots"] = result[0]["count"] if result else 0
            
            logging.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logging.error(f"Error cleaning up orphaned package data: {str(e)}")
            raise Exception(f"Failed to cleanup orphaned package data: {str(e)}")
    
    # Two-Structure Architecture Methods
    
    def create_package_document_node(self, package_document_data: dict, product_id: str) -> bool:
        """Create a PackageDocument node representing an expected document in the package"""
        try:
            logging.info(f"Creating package document node: {package_document_data.get('document_name', 'Unknown')}")
            
            query = """
            MATCH (p:Product {product_id: $product_id})
            MERGE (pd:PackageDocument {document_id: $document_id})
            SET pd.document_name = $document_name,
                pd.document_type = $document_type,
                pd.expected_structure = $expected_structure,
                pd.validation_rules = $validation_rules,
                pd.required_sections = $required_sections,
                pd.optional_sections = $optional_sections,
                pd.created_at = datetime(),
                pd.updated_at = datetime(),
                pd.has_upload = false,
                pd.processing_status = 'PENDING'
            MERGE (p)-[:EXPECTS_DOCUMENT]->(pd)
            RETURN pd.document_id as document_id
            """
            
            params = {
                "product_id": product_id,
                "document_id": package_document_data.get("document_id"),
                "document_name": package_document_data.get("document_name"),
                "document_type": package_document_data.get("document_type"),
                "expected_structure": json.dumps(package_document_data.get("expected_structure", {})),
                "validation_rules": json.dumps(package_document_data.get("validation_rules", {})),
                "required_sections": package_document_data.get("required_sections", []),
                "optional_sections": package_document_data.get("optional_sections", [])
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating package document node: {str(e)}")
            return False
    
    def link_uploaded_document_to_package_document(self, document_filename: str, package_document_id: str) -> bool:
        """Link an uploaded Document to its corresponding PackageDocument"""
        try:
            logging.info(f"🔗 Linking uploaded document {document_filename} to package document {package_document_id}")
            
            # First check if both nodes exist
            check_query = """
            OPTIONAL MATCH (pd:PackageDocument {document_id: $package_document_id})
            OPTIONAL MATCH (d:Document {fileName: $document_filename})
            RETURN pd.document_id as package_found, d.fileName as document_found
            """
            
            check_result = self.graph.query(check_query, {
                "package_document_id": package_document_id,
                "document_filename": document_filename
            }, session_params={"database": self.graph._database})
            
            if check_result:
                check_record = check_result[0]
                if not check_record.get('package_found'):
                    logging.error(f"❌ PackageDocument {package_document_id} not found in database")
                    return False
                if not check_record.get('document_found'):
                    logging.error(f"❌ Document {document_filename} not found in database")
                    return False
                logging.info(f"✅ Both nodes exist: PackageDocument {package_document_id} and Document {document_filename}")
            
            # Create the relationship
            query = """
            MATCH (pd:PackageDocument {document_id: $package_document_id})
            MATCH (d:Document {fileName: $document_filename})
            MERGE (pd)-[:HAS_UPLOADED]->(d)
            SET pd.has_upload = true,
                pd.uploaded_at = datetime(),
                d.package_document_id = $package_document_id
            RETURN pd.document_id as package_document_id
            """
            
            params = {
                "package_document_id": package_document_id,
                "document_filename": document_filename
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            success = len(result) > 0
            
            if success:
                logging.info(f"✅ Successfully created HAS_UPLOADED relationship")
            else:
                logging.error(f"❌ Failed to create HAS_UPLOADED relationship")
                
            return success
            
        except Exception as e:
            logging.error(f"Error linking uploaded document to package document: {str(e)}")
            return False
    
    def create_discovered_program_node(self, program_data: dict, product_id: str, discovered_from: str) -> bool:
        """Create a Program node discovered during document processing"""
        try:
            logging.info(f"Creating discovered program node: {program_data.get('program_name', 'Unknown')}")
            
            query = """
            MATCH (p:Product {product_id: $product_id})
            MERGE (prog:Program {program_id: $program_id})
            SET prog.program_name = $program_name,
                prog.program_code = $program_code,
                prog.description = $description,
                prog.discovered_from = $discovered_from,
                prog.discovered_at = datetime(),
                prog.loan_limits = $loan_limits,
                prog.rate_adjustments = $rate_adjustments,
                prog.feature_differences = $feature_differences,
                prog.qualification_criteria = $qualification_criteria,
                prog.created_at = datetime(),
                prog.updated_at = datetime()
            MERGE (p)-[:HAS_PROGRAM]->(prog)
            RETURN prog.program_id as program_id
            """
            
            params = {
                "product_id": product_id,
                "program_id": program_data.get("program_id"),
                "program_name": program_data.get("program_name"),
                "program_code": program_data.get("program_code"),
                "description": program_data.get("description", ""),
                "discovered_from": discovered_from,
                "loan_limits": json.dumps(program_data.get("loan_limits", {})),
                "rate_adjustments": program_data.get("rate_adjustments", []),
                "feature_differences": program_data.get("feature_differences", []),
                "qualification_criteria": program_data.get("qualification_criteria", [])
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating discovered program node: {str(e)}")
            return False
    
    def create_processed_guidelines_node(self, document_id: str, guidelines_data: dict) -> bool:
        """Create a Guidelines node from processed document content"""
        try:
            logging.info(f"Creating processed guidelines node from document: {document_id}")
            
            query = """
            MATCH (d:Document {fileName: $document_id})
            MERGE (g:Guidelines {guidelines_id: $guidelines_id})
            SET g.content = $content,
                g.sections = $sections,
                g.discovered_programs = $discovered_programs,
                g.eligibility_criteria = $eligibility_criteria,
                g.documentation_requirements = $documentation_requirements,
                g.processing_rules = $processing_rules,
                g.source_document = $document_id,
                g.processed_at = datetime()
            MERGE (d)-[:PROCESSED_INTO]->(g)
            RETURN g.guidelines_id as guidelines_id
            """
            
            params = {
                "document_id": document_id,
                "guidelines_id": f"guidelines_{document_id}_{int(time.time())}",
                "content": guidelines_data.get("content", ""),
                "sections": guidelines_data.get("sections", []),
                "discovered_programs": guidelines_data.get("discovered_programs", []),
                "eligibility_criteria": json.dumps(guidelines_data.get("eligibility_criteria", {})),
                "documentation_requirements": json.dumps(guidelines_data.get("documentation_requirements", {})),
                "processing_rules": json.dumps(guidelines_data.get("processing_rules", {}))
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating processed guidelines node: {str(e)}")
            return False
    
    def create_processed_matrix_node(self, document_id: str, matrix_data: dict, program_id: str = None) -> bool:
        """Create a Matrix node from processed document content"""
        try:
            logging.info(f"Creating processed matrix node from document: {document_id}")
            
            query = """
            MATCH (d:Document {fileName: $document_id})
            MERGE (m:Matrix {matrix_id: $matrix_id})
            SET m.content = $content,
                m.dimensions = $dimensions,
                m.cells = $cells,
                m.ranges = $ranges,
                m.matrix_type = $matrix_type,
                m.source_document = $document_id,
                m.processed_at = datetime()
            MERGE (d)-[:PROCESSED_INTO]->(m)
            """
            
            # If program_id provided, link to program
            if program_id:
                query += """
                WITH m
                MATCH (prog:Program {program_id: $program_id})
                MERGE (prog)-[:USES_MATRIX]->(m)
                """
            
            query += " RETURN m.matrix_id as matrix_id"
            
            params = {
                "document_id": document_id,
                "matrix_id": f"matrix_{document_id}_{int(time.time())}",
                "content": matrix_data.get("content", ""),
                "dimensions": matrix_data.get("dimensions", []),
                "cells": json.dumps(matrix_data.get("cells", [])),
                "ranges": json.dumps(matrix_data.get("ranges", {})),
                "matrix_type": matrix_data.get("matrix_type", "unknown")
            }
            
            if program_id:
                params["program_id"] = program_id
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating processed matrix node: {str(e)}")
            return False
    
    def update_package_document_processing_status(self, package_document_id: str, status: str) -> bool:
        """Update the processing status of a PackageDocument"""
        try:
            query = """
            MATCH (pd:PackageDocument {document_id: $package_document_id})
            SET pd.processing_status = $status,
                pd.processing_updated_at = datetime()
            RETURN pd.document_id as document_id
            """
            
            params = {
                "package_document_id": package_document_id,
                "status": status  # PENDING, PROCESSING, COMPLETED, FAILED
            }
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error updating package document processing status: {str(e)}")
            return False
    
    def get_package_completion_status(self, package_id: str) -> dict:
        """Get completion status of all documents in a package"""
        try:
            query = """
            MATCH (pkg:DocumentPackage {package_id: $package_id})-[:CONTAINS_CATEGORY]->(cat:MortgageCategory)
            MATCH (cat)-[:CONTAINS_PRODUCT]->(prod:Product)
            MATCH (prod)-[:EXPECTS_DOCUMENT]->(pd:PackageDocument)
            OPTIONAL MATCH (pd)-[:HAS_UPLOADED]->(doc:Document)
            RETURN cat.category_code as category,
                   prod.product_name as product,
                   pd.document_type as document_type,
                   pd.document_name as document_name,
                   pd.has_upload as has_upload,
                   pd.processing_status as processing_status,
                   doc.fileName as uploaded_file,
                   doc.status as document_status
            ORDER BY cat.category_code, prod.product_name, pd.document_type
            """
            
            params = {"package_id": package_id}
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            
            # Summarize results
            total_expected = len(result)
            uploaded = sum(1 for r in result if r.get("has_upload", False))
            processed = sum(1 for r in result if r.get("processing_status") == "COMPLETED")
            
            return {
                "package_id": package_id,
                "total_expected_documents": total_expected,
                "uploaded_documents": uploaded,
                "processed_documents": processed,
                "completion_percentage": (processed / total_expected * 100) if total_expected > 0 else 0,
                "details": result
            }
            
        except Exception as e:
            logging.error(f"Error getting package completion status: {str(e)}")
            return {
                "package_id": package_id,
                "error": str(e),
                "total_expected_documents": 0,
                "uploaded_documents": 0,
                "processed_documents": 0,
                "completion_percentage": 0,
                "details": []
            }
    
    def get_discovered_programs_for_product(self, product_id: str) -> list:
        """Get all programs discovered during processing for a product"""
        try:
            query = """
            MATCH (p:Product {product_id: $product_id})-[:HAS_PROGRAM]->(prog:Program)
            WHERE prog.discovered_from IS NOT NULL
            OPTIONAL MATCH (prog)-[:USES_MATRIX]->(m:Matrix)
            RETURN prog.program_id as program_id,
                   prog.program_name as program_name,
                   prog.program_code as program_code,
                   prog.discovered_from as discovered_from,
                   prog.discovered_at as discovered_at,
                   collect(m.matrix_id) as associated_matrices
            ORDER BY prog.program_name
            """
            
            params = {"product_id": product_id}
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return result
            
        except Exception as e:
            logging.error(f"Error getting discovered programs: {str(e)}")
            return []
    
    def _create_content_type_relationships(self, file_name: str, document_type: str, product_id: str) -> bool:
        """Create or update content-type-specific relationships and nodes"""
        try:
            if document_type == 'Guidelines':
                # Create or find Guidelines content node and link to Document
                query = """
                MATCH (d:Document {fileName: $file_name})
                MATCH (p:Product {product_id: $product_id})
                
                // Create Guidelines content node if it doesn't exist
                MERGE (g:Guidelines {
                    source_document: $file_name,
                    product_id: $product_id
                })
                ON CREATE SET 
                    g.guidelines_id = $guidelines_id,
                    g.content = '',
                    g.sections = [],
                    g.discovered_programs = [],
                    g.created_at = datetime(),
                    g.processing_status = 'PENDING'
                
                // Create relationships
                MERGE (d)-[:PROCESSED_INTO]->(g)
                MERGE (p)-[:HAS_GUIDELINES]->(g)
                
                RETURN g.guidelines_id as guidelines_id
                """
                
                params = {
                    'file_name': file_name,
                    'product_id': product_id,
                    'guidelines_id': f"guidelines_{product_id}_{int(time.time())}"
                }
                
            elif document_type == 'Matrix':
                # Create or find Matrix content node and link to Document
                query = """
                MATCH (d:Document {fileName: $file_name})
                MATCH (p:Product {product_id: $product_id})
                
                // Create Matrix content node if it doesn't exist
                MERGE (m:Matrix {
                    source_document: $file_name,
                    product_id: $product_id
                })
                ON CREATE SET 
                    m.matrix_id = $matrix_id,
                    m.content = '',
                    m.dimensions = [],
                    m.cells = [],
                    m.matrix_type = 'pricing',
                    m.created_at = datetime(),
                    m.processing_status = 'PENDING'
                
                // Create relationships
                MERGE (d)-[:PROCESSED_INTO]->(m)
                MERGE (p)-[:HAS_MATRIX]->(m)
                
                RETURN m.matrix_id as matrix_id
                """
                
                params = {
                    'file_name': file_name,
                    'product_id': product_id,
                    'matrix_id': f"matrix_{product_id}_{int(time.time())}"
                }
            
            else:
                return False
            
            result = self.graph.query(query, params, session_params={"database": self.graph._database})
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating content type relationships: {str(e)}")
            return False
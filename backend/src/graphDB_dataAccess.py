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
            
            result = self.execute_query(query, params)
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
            result = self.execute_query(query, params)
            
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
            
            result = self.execute_query(query, params)
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error updating package node: {str(e)}")
            raise Exception(f"Failed to update package node: {str(e)}")
    
    def delete_package_node(self, package_id: str) -> bool:
        """Delete a DocumentPackage node and all related nodes"""
        try:
            logging.info(f"Deleting package node: {package_id}")
            
            # Delete package and all related nodes/relationships
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})
            OPTIONAL MATCH (p)-[:CONTAINS]->(d:PackageDocument)
            OPTIONAL MATCH (p)-[:VERSION_OF]->(v:PackageVersion)
            OPTIONAL MATCH (v)-[:SNAPSHOT]->(s:PackageSnapshot)
            DETACH DELETE p, d, v, s
            RETURN count(p) as deleted_count
            """
            
            params = {"package_id": package_id}
            result = self.execute_query(query, params)
            
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
            
            result = self.execute_query(query, params)
            return result if result else []
            
        except Exception as e:
            logging.error(f"Error listing packages: {str(e)}")
            raise Exception(f"Failed to list packages: {str(e)}")

    # Package Document Methods
    
    def create_package_document(self, package_id: str, document_data: dict) -> bool:
        """Create a PackageDocument node and link to package"""
        try:
            logging.info(f"Creating package document: {document_data.get('document_id', 'unknown')}")
            
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
            
            result = self.execute_query(query, params)
            return len(result) > 0
            
        except Exception as e:
            logging.error(f"Error creating package document: {str(e)}")
            raise Exception(f"Failed to create package document: {str(e)}")
    
    def get_package_documents(self, package_id: str) -> list:
        """Get all documents for a package"""
        try:
            logging.info(f"Retrieving package documents: {package_id}")
            
            query = """
            MATCH (p:DocumentPackage {package_id: $package_id})-[:CONTAINS]->(d:PackageDocument)
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
                   d.quality_thresholds as quality_thresholds
            ORDER BY d.document_type, d.document_name
            """
            
            params = {"package_id": package_id}
            result = self.execute_query(query, params)
            
            # Parse JSON fields
            documents = []
            for doc in result:
                doc["expected_structure"] = json.loads(doc.get("expected_structure", "{}"))
                doc["required_sections"] = json.loads(doc.get("required_sections", "[]"))
                doc["optional_sections"] = json.loads(doc.get("optional_sections", "[]"))
                doc["entity_types"] = json.loads(doc.get("entity_types", "[]"))
                doc["matrix_configuration"] = json.loads(doc.get("matrix_configuration")) if doc.get("matrix_configuration") else None
                doc["validation_schema"] = json.loads(doc.get("validation_schema", "{}"))
                doc["quality_thresholds"] = json.loads(doc.get("quality_thresholds", "{}"))
                documents.append(doc)
            
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
            
            result = self.execute_query(query, params)
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
            result = self.execute_query(query, params)
            
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
            
            result = self.execute_query(query, params)
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
            result = self.execute_query(query, params)
            
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
            
            result = self.execute_query(query, params)
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
            result = self.execute_query(query, params)
            
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
                "CREATE INDEX document_id_index IF NOT EXISTS FOR (d:PackageDocument) ON (d.document_id)",
                "CREATE INDEX version_index IF NOT EXISTS FOR (v:PackageVersion) ON (v.version)"
            ]
            
            # Create constraints for data integrity
            constraint_queries = [
                "CREATE CONSTRAINT package_id_unique IF NOT EXISTS FOR (p:DocumentPackage) REQUIRE p.package_id IS UNIQUE",
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
            
            result = self.execute_query(query, params)
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
                "orphaned_versions": 0,
                "orphaned_snapshots": 0
            }
            
            # Clean up orphaned documents
            orphaned_docs_query = """
            MATCH (d:PackageDocument)
            WHERE NOT EXISTS((p:DocumentPackage)-[:CONTAINS]->(d))
            DETACH DELETE d
            RETURN count(d) as count
            """
            result = self.execute_query(orphaned_docs_query)
            cleanup_stats["orphaned_documents"] = result[0]["count"] if result else 0
            
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
            result = self.execute_query(orphaned_snapshots_query)
            cleanup_stats["orphaned_snapshots"] = result[0]["count"] if result else 0
            
            logging.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logging.error(f"Error cleaning up orphaned package data: {str(e)}")
            raise Exception(f"Failed to cleanup orphaned package data: {str(e)}")
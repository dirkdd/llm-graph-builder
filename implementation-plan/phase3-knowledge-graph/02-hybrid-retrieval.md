# Phase 3.2: Hybrid Retrieval System

## Overview
The Hybrid Retrieval System implements sophisticated multi-modal information retrieval that leverages the multi-layer knowledge graph schema. This system combines vector similarity search, graph traversal, decision path following, and semantic reasoning to provide contextually relevant and comprehensive responses to complex mortgage domain queries.

## Core Retrieval Paradigms

### Multi-Modal Retrieval Strategy
The system employs five complementary retrieval modes that can be used individually or in combination:

1. **Vector Similarity Retrieval**: Semantic embedding-based search
2. **Graph Traversal Retrieval**: Structure-aware navigation
3. **Decision Path Retrieval**: Logic-following query resolution
4. **Matrix Intersection Retrieval**: Qualification-based lookup
5. **Hybrid Reasoning Retrieval**: Combined multi-modal approach

Each mode leverages different aspects of the knowledge graph and can be weighted based on query characteristics and user context.

## System Architecture

### 1. Query Analysis and Routing

#### Query Classifier (`query_classifier.py`)

```python
class QueryClassifier:
    """Analyzes incoming queries and determines optimal retrieval strategy"""
    
    def __init__(self, llm_model: str = "claude-sonnet-4"):
        self.llm = get_llm(llm_model)
        self.query_patterns = self._load_query_patterns()
        self.retrieval_strategy_selector = RetrievalStrategySelector()
        
    def classify_query(self, query: str, context: QueryContext) -> QueryClassification:
        """Classify query and determine retrieval strategy"""
        
        # Extract query features
        features = self.extract_query_features(query)
        
        # Identify query intent
        intent = self.identify_query_intent(query, features)
        
        # Determine domain focus
        domain_focus = self.identify_domain_focus(query, features)
        
        # Analyze complexity
        complexity = self.analyze_query_complexity(query, features)
        
        # Select retrieval modes
        retrieval_modes = self.select_retrieval_modes(intent, domain_focus, complexity)
        
        # Determine mode weights
        mode_weights = self.calculate_mode_weights(query, intent, complexity)
        
        return QueryClassification(
            query=query,
            intent=intent,
            domain_focus=domain_focus,
            complexity_score=complexity,
            retrieval_modes=retrieval_modes,
            mode_weights=mode_weights,
            expected_response_type=self.determine_response_type(intent),
            context_requirements=self.identify_context_requirements(query, intent)
        )
    
    def extract_query_features(self, query: str) -> QueryFeatures:
        """Extract linguistic and semantic features from query"""
        return QueryFeatures(
            # Linguistic features
            word_count=len(query.split()),
            has_question_words=bool(re.search(r'\b(what|who|when|where|why|how)\b', query.lower())),
            has_comparison=bool(re.search(r'\b(vs|versus|compared|difference|better)\b', query.lower())),
            has_negation=bool(re.search(r'\b(not|no|never|without)\b', query.lower())),
            
            # Domain features
            mentions_loan_programs=bool(re.search(r'\b(nqm|rtl|sbc|conventional|jumbo)\b', query.lower())),
            mentions_borrower_criteria=bool(re.search(r'\b(fico|credit|income|dti|ltv)\b', query.lower())),
            mentions_property=bool(re.search(r'\b(property|home|house|condo|sfr)\b', query.lower())),
            mentions_documentation=bool(re.search(r'\b(docs|documentation|required|provide)\b', query.lower())),
            
            # Complexity indicators
            mentions_exceptions=bool(re.search(r'\b(except|unless|however|but|override)\b', query.lower())),
            mentions_scenarios=bool(re.search(r'\b(if|when|scenario|case|situation)\b', query.lower())),
            mentions_calculations=bool(re.search(r'\b(calculate|compute|rate|payment|amount)\b', query.lower())),
            
            # Entity mentions
            entity_mentions=self.extract_entity_mentions(query),
            numeric_mentions=self.extract_numeric_mentions(query)
        )
    
    def identify_query_intent(self, query: str, features: QueryFeatures) -> QueryIntent:
        """Identify the primary intent of the query"""
        
        intent_patterns = {
            'QUALIFICATION_CHECK': [
                r'qualify|eligible|approve|accept',
                r'can.*borrow|able.*get.*loan',
                r'meet.*requirements|satisfy.*criteria'
            ],
            'DOCUMENTATION_INQUIRY': [
                r'documents.*required|need.*provide|what.*submit',
                r'documentation|paperwork|files.*needed'
            ],
            'POLICY_LOOKUP': [
                r'policy|guideline|rule|requirement',
                r'what.*policy|according.*guidelines'
            ],
            'CALCULATION_REQUEST': [
                r'calculate|compute|determine.*amount',
                r'what.*rate|payment.*amount|monthly.*payment'
            ],
            'COMPARISON_ANALYSIS': [
                r'difference.*between|compare|versus|vs',
                r'better.*option|which.*program'
            ],
            'EXCEPTION_INQUIRY': [
                r'exception|override|waiver|special.*case',
                r'manual.*review|underwriter.*decision'
            ],
            'PROCESS_NAVIGATION': [
                r'next.*step|what.*happens|process|workflow',
                r'how.*long|timeline|when.*complete'
            ]
        }
        
        for intent, patterns in intent_patterns.items():
            if any(re.search(pattern, query.lower()) for pattern in patterns):
                return QueryIntent(
                    primary_intent=intent,
                    confidence=self.calculate_intent_confidence(query, intent, patterns),
                    supporting_evidence=self.extract_intent_evidence(query, patterns)
                )
        
        # Default to policy lookup if no specific intent detected
        return QueryIntent(
            primary_intent='POLICY_LOOKUP',
            confidence=0.6,
            supporting_evidence=['Default classification']
        )
    
    def select_retrieval_modes(self, intent: QueryIntent, domain_focus: DomainFocus, 
                              complexity: float) -> List[RetrievalMode]:
        """Select appropriate retrieval modes based on query characteristics"""
        
        modes = []
        
        # Intent-based mode selection
        if intent.primary_intent == 'QUALIFICATION_CHECK':
            modes.extend(['DECISION_PATH', 'MATRIX_INTERSECTION', 'VECTOR_SIMILARITY'])
        elif intent.primary_intent == 'DOCUMENTATION_INQUIRY':
            modes.extend(['VECTOR_SIMILARITY', 'GRAPH_TRAVERSAL'])
        elif intent.primary_intent == 'POLICY_LOOKUP':
            modes.extend(['VECTOR_SIMILARITY', 'GRAPH_TRAVERSAL', 'DECISION_PATH'])
        elif intent.primary_intent == 'CALCULATION_REQUEST':
            modes.extend(['MATRIX_INTERSECTION', 'VECTOR_SIMILARITY'])
        elif intent.primary_intent == 'COMPARISON_ANALYSIS':
            modes.extend(['HYBRID_REASONING', 'VECTOR_SIMILARITY', 'GRAPH_TRAVERSAL'])
        elif intent.primary_intent == 'EXCEPTION_INQUIRY':
            modes.extend(['DECISION_PATH', 'GRAPH_TRAVERSAL', 'HYBRID_REASONING'])
        
        # Complexity-based adjustments
        if complexity > 0.7:
            if 'HYBRID_REASONING' not in modes:
                modes.append('HYBRID_REASONING')
        
        # Domain-specific adjustments
        if domain_focus.has_matrix_focus:
            if 'MATRIX_INTERSECTION' not in modes:
                modes.insert(0, 'MATRIX_INTERSECTION')
        
        return modes[:4]  # Limit to top 4 modes for performance
```

### 2. Vector Similarity Retrieval Engine

#### Enhanced Vector Search (`vector_retrieval.py`)

```python
class EnhancedVectorRetrieval:
    """Advanced vector similarity search with context awareness"""
    
    def __init__(self, neo4j_driver, embedding_model: str = "text-embedding-3-large"):
        self.driver = neo4j_driver
        self.embedding_model = embedding_model
        self.context_enhancer = ContextEnhancer()
        self.result_ranker = ResultRanker()
        
    def retrieve_similar_chunks(self, query: str, query_classification: QueryClassification, 
                               top_k: int = 20) -> List[RetrievalResult]:
        """Retrieve semantically similar chunks with context enhancement"""
        
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query, query_classification)
        
        # Perform vector similarity search
        similar_chunks = self.vector_search(query_embedding, top_k * 2)  # Over-retrieve for filtering
        
        # Apply domain-specific filtering
        filtered_chunks = self.apply_domain_filters(similar_chunks, query_classification)
        
        # Enhance with navigation context
        enhanced_results = self.enhance_with_navigation_context(filtered_chunks)
        
        # Re-rank based on multiple factors
        ranked_results = self.result_ranker.rank_results(
            enhanced_results, 
            query_classification,
            ranking_factors=['similarity_score', 'navigation_relevance', 'entity_overlap', 'decision_relevance']
        )
        
        return ranked_results[:top_k]
    
    def generate_query_embedding(self, query: str, classification: QueryClassification) -> List[float]:
        """Generate context-enhanced query embedding"""
        
        # Basic query embedding
        base_embedding = self.get_embedding(query)
        
        # Intent-specific enhancement
        if classification.intent.primary_intent in ['QUALIFICATION_CHECK', 'CALCULATION_REQUEST']:
            # Enhance with mortgage domain context
            domain_context = "mortgage loan qualification underwriting criteria requirements"
            enhanced_query = f"{query} {domain_context}"
            enhanced_embedding = self.get_embedding(enhanced_query)
            
            # Weighted combination
            base_embedding = self.combine_embeddings(base_embedding, enhanced_embedding, weights=[0.8, 0.2])
        
        return base_embedding
    
    def vector_search(self, query_embedding: List[float], top_k: int) -> List[ChunkResult]:
        """Perform vector similarity search in Neo4j"""
        
        query = """
        CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $query_embedding) 
        YIELD node as chunk, score
        
        // Get navigation context
        MATCH (chunk:HierarchicalChunk)-[:BELONGS_TO]->(nav:NavigationNode)
        OPTIONAL MATCH (nav)-[:PART_OF_PACKAGE]->(pkg:DocumentPackage)
        OPTIONAL MATCH (chunk)-[:MENTIONS]->(entity:Entity)
        
        // Get decision context if applicable
        OPTIONAL MATCH (nav)-[:HAS_DECISION_TREE]->(dt:DecisionTree)
        OPTIONAL MATCH (dt)-[:CONTAINS_NODE]->(decision:DecisionNode)
        
        RETURN chunk, score, nav, pkg, 
               collect(DISTINCT entity) as entities,
               collect(DISTINCT decision) as decision_nodes
        ORDER BY score DESC
        LIMIT $top_k
        """
        
        with self.driver.session() as session:
            result = session.run(query, {
                'query_embedding': query_embedding,
                'top_k': top_k
            })
            
            chunks = []
            for record in result:
                chunk_result = ChunkResult(
                    chunk=record['chunk'],
                    similarity_score=record['score'],
                    navigation_node=record['nav'],
                    package=record['pkg'],
                    entities=record['entities'],
                    decision_nodes=record['decision_nodes']
                )
                chunks.append(chunk_result)
            
            return chunks
    
    def enhance_with_navigation_context(self, chunk_results: List[ChunkResult]) -> List[EnhancedChunkResult]:
        """Enhance results with navigation hierarchy context"""
        
        enhanced_results = []
        
        for chunk_result in chunk_results:
            # Get hierarchical context
            navigation_context = self.get_navigation_context(chunk_result.navigation_node)
            
            # Get sibling chunks for context
            sibling_chunks = self.get_sibling_chunks(chunk_result.chunk)
            
            # Get parent/child relationships
            hierarchical_relationships = self.get_hierarchical_relationships(chunk_result.navigation_node)
            
            enhanced_result = EnhancedChunkResult(
                chunk_result=chunk_result,
                navigation_context=navigation_context,
                sibling_chunks=sibling_chunks,
                hierarchical_relationships=hierarchical_relationships,
                context_relevance_score=self.calculate_context_relevance(chunk_result, navigation_context)
            )
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
```

### 3. Graph Traversal Retrieval Engine

#### Intelligent Graph Navigation (`graph_traversal.py`)

```python
class GraphTraversalRetrieval:
    """Structure-aware graph traversal for contextual information retrieval"""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.path_analyzer = PathAnalyzer()
        self.relevance_scorer = RelevanceScorer()
        
    def traverse_for_context(self, query: str, classification: QueryClassification,
                           starting_nodes: List[str] = None) -> List[TraversalResult]:
        """Perform intelligent graph traversal to find relevant context"""
        
        if not starting_nodes:
            starting_nodes = self.identify_starting_nodes(query, classification)
        
        traversal_results = []
        
        for start_node in starting_nodes:
            # Define traversal strategy based on query intent
            strategy = self.define_traversal_strategy(classification)
            
            # Execute traversal
            paths = self.execute_traversal(start_node, strategy)
            
            # Analyze paths for relevance
            analyzed_paths = self.path_analyzer.analyze_paths(paths, query, classification)
            
            # Convert to results
            for path in analyzed_paths:
                result = TraversalResult(
                    start_node_id=start_node,
                    path=path,
                    end_nodes=path.end_nodes,
                    relevance_score=path.relevance_score,
                    context_information=self.extract_context_information(path)
                )
                traversal_results.append(result)
        
        # Rank and filter results
        ranked_results = self.relevance_scorer.rank_traversal_results(
            traversal_results, 
            query, 
            classification
        )
        
        return ranked_results
    
    def define_traversal_strategy(self, classification: QueryClassification) -> TraversalStrategy:
        """Define graph traversal strategy based on query characteristics"""
        
        intent = classification.intent.primary_intent
        
        if intent == 'QUALIFICATION_CHECK':
            return TraversalStrategy(
                relationship_types=['HAS_DECISION_TREE', 'CONTAINS_NODE', 'LEADS_TO', 'RESULTS_IN'],
                max_depth=5,
                direction='OUTGOING',
                node_filters=['DecisionNode', 'DecisionOutcome'],
                path_constraints=['must_include_leaf_node'],
                weight_factors={'decision_relevance': 0.6, 'proximity': 0.4}
            )
        
        elif intent == 'DOCUMENTATION_INQUIRY':
            return TraversalStrategy(
                relationship_types=['CONTAINS_ENTITY', 'RELATED_TO', 'REFERENCES'],
                max_depth=3,
                direction='BOTH',
                node_filters=['Entity'],
                entity_type_filters=['REQUIREMENT', 'DOCUMENT_TYPE'],
                weight_factors={'entity_relevance': 0.7, 'proximity': 0.3}
            )
        
        elif intent == 'POLICY_LOOKUP':
            return TraversalStrategy(
                relationship_types=['PARENT_OF', 'CHILD_OF', 'REFERENCES', 'IMPLEMENTS'],
                max_depth=4,
                direction='BOTH',
                node_filters=['NavigationNode', 'BusinessPolicy'],
                path_constraints=['maintain_hierarchy'],
                weight_factors={'hierarchical_relevance': 0.5, 'content_relevance': 0.5}
            )
        
        elif intent == 'COMPARISON_ANALYSIS':
            return TraversalStrategy(
                relationship_types=['SAME_AS', 'SIMILAR_TO', 'COMPETES_WITH', 'ALTERNATIVE_TO'],
                max_depth=3,
                direction='BOTH',
                node_filters=['Entity', 'NavigationNode', 'MatrixCell'],
                weight_factors={'similarity': 0.6, 'completeness': 0.4}
            )
        
        else:  # Default strategy
            return TraversalStrategy(
                relationship_types=['CONTAINS', 'REFERENCES', 'RELATED_TO'],
                max_depth=3,
                direction='BOTH',
                weight_factors={'proximity': 0.5, 'relevance': 0.5}
            )
    
    def execute_traversal(self, start_node_id: str, strategy: TraversalStrategy) -> List[GraphPath]:
        """Execute graph traversal according to strategy"""
        
        # Build Cypher query based on strategy
        cypher_query = self.build_traversal_query(start_node_id, strategy)
        
        with self.driver.session() as session:
            result = session.run(cypher_query)
            
            paths = []
            for record in result:
                path = GraphPath(
                    nodes=record['path_nodes'],
                    relationships=record['path_relationships'],
                    length=record['path_length'],
                    end_node=record['end_node'],
                    traversal_score=record.get('traversal_score', 0.0)
                )
                paths.append(path)
            
            return paths
    
    def build_traversal_query(self, start_node_id: str, strategy: TraversalStrategy) -> str:
        """Build Cypher query for graph traversal"""
        
        # Base traversal pattern
        relationship_pattern = '|'.join(strategy.relationship_types)
        direction_pattern = '-' if strategy.direction == 'BOTH' else '->' if strategy.direction == 'OUTGOING' else '<-'
        
        node_filter = ''
        if strategy.node_filters:
            node_filter = f"WHERE any(label IN labels(n) WHERE label IN {strategy.node_filters})"
        
        query = f"""
        MATCH path = (start {{enhanced_node_id: $start_node_id}})
                     {direction_pattern}[r:{relationship_pattern}*1..{strategy.max_depth}]
                     {direction_pattern}(n)
        {node_filter}
        
        WITH path, nodes(path) as path_nodes, relationships(path) as path_relationships,
             length(path) as path_length, n as end_node
        
        // Calculate traversal score based on strategy
        WITH path, path_nodes, path_relationships, path_length, end_node,
             {self.build_scoring_expression(strategy)} as traversal_score
        
        WHERE traversal_score > 0.3  // Minimum relevance threshold
        
        RETURN path_nodes, path_relationships, path_length, end_node, traversal_score
        ORDER BY traversal_score DESC
        LIMIT 50
        """
        
        return query
    
    def build_scoring_expression(self, strategy: TraversalStrategy) -> str:
        """Build Cypher expression for scoring paths"""
        
        scoring_components = []
        
        # Proximity score (shorter paths generally better)
        scoring_components.append(f"(1.0 / (path_length + 1)) * {strategy.weight_factors.get('proximity', 0.3)}")
        
        # Decision relevance (if applicable)
        if 'decision_relevance' in strategy.weight_factors:
            scoring_components.append(
                f"CASE WHEN any(node IN path_nodes WHERE 'DecisionNode' IN labels(node)) "
                f"THEN {strategy.weight_factors['decision_relevance']} ELSE 0 END"
            )
        
        # Entity relevance (if applicable)
        if 'entity_relevance' in strategy.weight_factors:
            scoring_components.append(
                f"CASE WHEN any(node IN path_nodes WHERE 'Entity' IN labels(node)) "
                f"THEN {strategy.weight_factors['entity_relevance']} ELSE 0 END"
            )
        
        # Hierarchical relevance (if applicable)
        if 'hierarchical_relevance' in strategy.weight_factors:
            scoring_components.append(
                f"CASE WHEN any(rel IN path_relationships WHERE type(rel) IN ['PARENT_OF', 'CHILD_OF']) "
                f"THEN {strategy.weight_factors['hierarchical_relevance']} ELSE 0 END"
            )
        
        return " + ".join(scoring_components) if scoring_components else "1.0"
```

### 4. Decision Path Retrieval Engine

#### Decision Logic Follower (`decision_path_retrieval.py`)

```python
class DecisionPathRetrieval:
    """Follows decision trees and logic paths to provide qualification answers"""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.decision_evaluator = DecisionEvaluator()
        self.path_optimizer = PathOptimizer()
        
    def evaluate_qualification_query(self, query: str, borrower_params: Dict[str, Any],
                                   classification: QueryClassification) -> DecisionPathResult:
        """Evaluate qualification query by following decision paths"""
        
        # Extract decision criteria from query
        criteria = self.extract_decision_criteria(query, borrower_params)
        
        # Find relevant decision trees
        relevant_trees = self.find_relevant_decision_trees(query, classification)
        
        # Evaluate each tree
        evaluation_results = []
        for tree in relevant_trees:
            result = self.evaluate_decision_tree(tree, criteria)
            evaluation_results.append(result)
        
        # Combine results
        combined_result = self.combine_decision_results(evaluation_results)
        
        # Generate explanation
        explanation = self.generate_decision_explanation(combined_result)
        
        return DecisionPathResult(
            query=query,
            criteria=criteria,
            decision_trees_evaluated=relevant_trees,
            individual_results=evaluation_results,
            combined_result=combined_result,
            explanation=explanation,
            confidence_score=combined_result.confidence
        )
    
    def find_relevant_decision_trees(self, query: str, classification: QueryClassification) -> List[DecisionTree]:
        """Find decision trees relevant to the query"""
        
        query_embedding = self.get_embedding(query)
        
        cypher_query = """
        // Find decision trees with semantic similarity to query
        MATCH (dt:DecisionTree)-[:IMPLEMENTS]->(bp:BusinessPolicy)
        OPTIONAL MATCH (dt)-[:ROOT_OF_TREE]->(root:DecisionNode)
        OPTIONAL MATCH (dt)-[:CONTAINS_NODE]->(node:DecisionNode)
        
        // Calculate relevance based on multiple factors
        WITH dt, bp, root, collect(node) as all_nodes,
             gds.similarity.cosine(dt.summary_embedding, $query_embedding) as semantic_similarity,
             
             // Intent-based relevance
             CASE 
                WHEN $intent = 'QUALIFICATION_CHECK' AND dt.decision_domain = 'BORROWER_ELIGIBILITY' 
                THEN 1.0
                WHEN $intent = 'QUALIFICATION_CHECK' AND dt.decision_domain IN ['PROPERTY_ELIGIBILITY', 'LOAN_ELIGIBILITY'] 
                THEN 0.8
                WHEN $intent = 'DOCUMENTATION_INQUIRY' AND dt.decision_domain = 'DOCUMENTATION_REQUIREMENTS' 
                THEN 1.0
                ELSE 0.5 
             END as intent_relevance,
             
             // Completeness score
             dt.completeness_verified as completeness
        
        WHERE semantic_similarity > 0.7 OR intent_relevance > 0.8
        
        WITH dt, bp, root, all_nodes,
             (semantic_similarity * 0.4 + intent_relevance * 0.4 + 
              CASE WHEN completeness THEN 0.2 ELSE 0 END) as total_relevance
        
        ORDER BY total_relevance DESC
        LIMIT 5
        
        RETURN dt, bp, root, all_nodes, total_relevance
        """
        
        with self.driver.session() as session:
            result = session.run(cypher_query, {
                'query_embedding': query_embedding,
                'intent': classification.intent.primary_intent
            })
            
            trees = []
            for record in result:
                tree = DecisionTree(
                    tree_data=record['dt'],
                    business_policy=record['bp'],
                    root_node=record['root'],
                    all_nodes=record['all_nodes'],
                    relevance_score=record['total_relevance']
                )
                trees.append(tree)
            
            return trees
    
    def evaluate_decision_tree(self, tree: DecisionTree, criteria: Dict[str, Any]) -> TreeEvaluationResult:
        """Evaluate a specific decision tree with given criteria"""
        
        # Start from root node
        current_node = tree.root_node
        evaluation_path = [current_node]
        
        while current_node.decision_type != 'LEAF':
            # Evaluate current node condition
            evaluation_result = self.decision_evaluator.evaluate_node(current_node, criteria)
            
            # Determine next node based on evaluation
            if evaluation_result.result == True:
                next_node = self.get_true_path_node(current_node)
            elif evaluation_result.result == False:
                next_node = self.get_false_path_node(current_node)
            else:
                # Handle exception or missing data
                next_node = self.get_exception_path_node(current_node)
            
            if not next_node:
                # Dead end - shouldn't happen in well-formed trees
                break
            
            current_node = next_node
            evaluation_path.append(current_node)
        
        # Extract final outcome
        final_outcome = current_node.default_outcome if hasattr(current_node, 'default_outcome') else None
        
        return TreeEvaluationResult(
            tree=tree,
            evaluation_path=evaluation_path,
            final_outcome=final_outcome,
            criteria_used=criteria,
            missing_criteria=self.identify_missing_criteria(evaluation_path, criteria),
            confidence=self.calculate_evaluation_confidence(evaluation_path, criteria)
        )
    
    def generate_decision_explanation(self, combined_result: CombinedDecisionResult) -> DecisionExplanation:
        """Generate human-readable explanation of decision process"""
        
        explanation_parts = []
        
        # Overall outcome
        explanation_parts.append(f"Based on the provided criteria, the loan application would be: {combined_result.final_decision}")
        
        # Key decision factors
        key_factors = self.extract_key_factors(combined_result)
        if key_factors:
            explanation_parts.append("Key factors in this decision:")
            for factor in key_factors:
                explanation_parts.append(f"  • {factor.description} ({factor.impact})")
        
        # Decision path summary
        for tree_result in combined_result.individual_results:
            if tree_result.final_outcome:
                explanation_parts.append(
                    f"The {tree_result.tree.tree_name} resulted in: {tree_result.final_outcome.action}"
                )
                
                # Include decision steps
                for i, node in enumerate(tree_result.evaluation_path[:-1]):  # Exclude final outcome
                    next_node = tree_result.evaluation_path[i + 1]
                    explanation_parts.append(
                        f"  Step {i + 1}: {node.decision_name} → {self.get_path_description(node, next_node)}"
                    )
        
        # Missing information or exceptions
        missing_criteria = combined_result.missing_criteria
        if missing_criteria:
            explanation_parts.append("Additional information needed for complete evaluation:")
            for criterion in missing_criteria:
                explanation_parts.append(f"  • {criterion}")
        
        # Alternative outcomes
        alternatives = self.identify_alternative_outcomes(combined_result)
        if alternatives:
            explanation_parts.append("Alternative outcomes possible with different criteria:")
            for alternative in alternatives:
                explanation_parts.append(f"  • {alternative.description}")
        
        return DecisionExplanation(
            full_text="\n".join(explanation_parts),
            structured_steps=self.create_structured_steps(combined_result),
            key_factors=key_factors,
            confidence_level=combined_result.confidence,
            alternative_scenarios=alternatives
        )
```

### 5. Matrix Intersection Retrieval Engine

#### Qualification Matrix Lookup (`matrix_intersection_retrieval.py`)

```python
class MatrixIntersectionRetrieval:
    """Performs precise lookups in qualification and pricing matrices"""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.range_matcher = RangeMatcher()
        self.matrix_navigator = MatrixNavigator()
        
    def lookup_qualification_criteria(self, query: str, borrower_params: Dict[str, Any],
                                    classification: QueryClassification) -> MatrixLookupResult:
        """Perform matrix lookup for qualification criteria"""
        
        # Identify relevant matrices
        relevant_matrices = self.find_relevant_matrices(query, classification)
        
        # Extract lookup parameters from query and borrower data
        lookup_params = self.extract_lookup_parameters(query, borrower_params)
        
        # Perform lookups in each matrix
        lookup_results = []
        for matrix in relevant_matrices:
            result = self.perform_matrix_lookup(matrix, lookup_params)
            lookup_results.append(result)
        
        # Combine and rank results
        combined_result = self.combine_matrix_results(lookup_results)
        
        # Get related guideline context
        guideline_context = self.get_guideline_context_for_results(combined_result)
        
        return MatrixLookupResult(
            query=query,
            lookup_parameters=lookup_params,
            matrices_consulted=relevant_matrices,
            individual_lookups=lookup_results,
            combined_result=combined_result,
            guideline_context=guideline_context,
            confidence_score=self.calculate_lookup_confidence(lookup_results)
        )
    
    def find_relevant_matrices(self, query: str, classification: QueryClassification) -> List[MatrixDocument]:
        """Find matrices relevant to the qualification query"""
        
        query_tokens = self.extract_query_tokens(query)
        intent = classification.intent.primary_intent
        
        cypher_query = """
        MATCH (matrix:MatrixDocument)
        WHERE matrix.matrix_classification.primary_type IN ['MULTI_DIMENSIONAL_DECISION', 'RISK_BASED_SEGMENTATION']
        
        // Calculate relevance based on query intent and content
        WITH matrix,
             // Intent-based scoring
             CASE 
                WHEN $intent = 'QUALIFICATION_CHECK' AND 
                     any(dim IN matrix.dimensions WHERE dim IN ['fico_score', 'ltv_ratio', 'dti_ratio'])
                THEN 1.0
                WHEN $intent = 'CALCULATION_REQUEST' AND 
                     'pricing' IN tolower(matrix.matrix_name)
                THEN 1.0
                ELSE 0.5
             END as intent_score,
             
             // Token overlap scoring
             size([token IN $query_tokens WHERE token IN matrix.search_tokens]) * 1.0 / size($query_tokens) as token_overlap,
             
             // Matrix quality scoring
             matrix.range_coverage.overall as coverage_score
        
        WITH matrix, (intent_score * 0.5 + token_overlap * 0.3 + coverage_score * 0.2) as relevance_score
        
        WHERE relevance_score > 0.4
        ORDER BY relevance_score DESC
        LIMIT 3
        
        RETURN matrix, relevance_score
        """
        
        with self.driver.session() as session:
            result = session.run(cypher_query, {
                'intent': intent,
                'query_tokens': query_tokens
            })
            
            matrices = []
            for record in result:
                matrix = MatrixDocument(
                    matrix_data=record['matrix'],
                    relevance_score=record['relevance_score']
                )
                matrices.append(matrix)
            
            return matrices
    
    def perform_matrix_lookup(self, matrix: MatrixDocument, lookup_params: Dict[str, Any]) -> SingleMatrixLookupResult:
        """Perform lookup in a specific matrix"""
        
        # Find applicable cells based on parameter ranges
        applicable_cells = self.find_applicable_cells(matrix, lookup_params)
        
        # Handle exact matches and range overlaps
        exact_matches = []
        range_matches = []
        
        for cell in applicable_cells:
            match_type = self.determine_match_type(cell, lookup_params)
            
            if match_type == 'EXACT':
                exact_matches.append(cell)
            elif match_type == 'RANGE_OVERLAP':
                range_matches.append(cell)
        
        # Prioritize exact matches
        primary_results = exact_matches if exact_matches else range_matches
        
        # Get cell values and associated guidelines
        enriched_results = []
        for cell in primary_results:
            enriched_cell = self.enrich_cell_with_context(cell, matrix)
            enriched_results.append(enriched_cell)
        
        return SingleMatrixLookupResult(
            matrix=matrix,
            lookup_params=lookup_params,
            exact_matches=exact_matches,
            range_matches=range_matches,
            primary_results=enriched_results,
            match_confidence=self.calculate_match_confidence(primary_results, lookup_params)
        )
    
    def find_applicable_cells(self, matrix: MatrixDocument, lookup_params: Dict[str, Any]) -> List[MatrixCell]:
        """Find matrix cells that match the lookup parameters"""
        
        param_conditions = []
        cypher_params = {'matrix_id': matrix.matrix_id}
        
        # Build parameter-specific conditions
        for param_name, param_value in lookup_params.items():
            if param_name == 'fico_score' and param_value is not None:
                param_conditions.append(
                    """
                    any(range IN cell.ranges 
                        WHERE range.dimension = 'fico_score' 
                        AND $fico_score >= range.min_value 
                        AND $fico_score <= range.max_value)
                    """
                )
                cypher_params['fico_score'] = param_value
            
            elif param_name == 'ltv_ratio' and param_value is not None:
                param_conditions.append(
                    """
                    any(range IN cell.ranges 
                        WHERE range.dimension = 'ltv_ratio' 
                        AND $ltv_ratio >= range.min_value 
                        AND $ltv_ratio <= range.max_value)
                    """
                )
                cypher_params['ltv_ratio'] = param_value
            
            elif param_name == 'dti_ratio' and param_value is not None:
                param_conditions.append(
                    """
                    any(range IN cell.ranges 
                        WHERE range.dimension = 'dti_ratio' 
                        AND $dti_ratio >= range.min_value 
                        AND $dti_ratio <= range.max_value)
                    """
                )
                cypher_params['dti_ratio'] = param_value
            
            elif param_name == 'property_type' and param_value is not None:
                param_conditions.append("$property_type IN cell.property_types")
                cypher_params['property_type'] = param_value
        
        # Build the complete query
        where_clause = " AND ".join(param_conditions) if param_conditions else "true"
        
        cypher_query = f"""
        MATCH (matrix:MatrixDocument {{matrix_id: $matrix_id}})-[:CONTAINS_CELL]->(cell:MatrixCell)
        WHERE {where_clause}
        
        // Get associated guidelines context
        OPTIONAL MATCH (cell)-[:REFERENCES]->(nav:NavigationNode)
        OPTIONAL MATCH (cell)-[:ELABORATED_BY]->(chunk:HierarchicalChunk)
        
        RETURN cell, 
               collect(DISTINCT nav) as related_navigation,
               collect(DISTINCT chunk) as related_chunks
        ORDER BY cell.row_index, cell.column_index
        """
        
        with self.driver.session() as session:
            result = session.run(cypher_query, cypher_params)
            
            cells = []
            for record in result:
                cell = MatrixCell(
                    cell_data=record['cell'],
                    related_navigation=record['related_navigation'],
                    related_chunks=record['related_chunks']
                )
                cells.append(cell)
            
            return cells
```

### 6. Hybrid Reasoning Engine

#### Multi-Modal Intelligence Combiner (`hybrid_reasoning.py`)

```python
class HybridReasoningEngine:
    """Combines multiple retrieval modes with intelligent reasoning"""
    
    def __init__(self, neo4j_driver, llm_model: str = "claude-sonnet-4"):
        self.driver = neo4j_driver
        self.llm = get_llm(llm_model)
        self.vector_retrieval = EnhancedVectorRetrieval(neo4j_driver)
        self.graph_traversal = GraphTraversalRetrieval(neo4j_driver)
        self.decision_path = DecisionPathRetrieval(neo4j_driver)
        self.matrix_lookup = MatrixIntersectionRetrieval(neo4j_driver)
        self.result_synthesizer = ResultSynthesizer()
        
    def process_complex_query(self, query: str, context: QueryContext,
                            classification: QueryClassification) -> HybridReasoningResult:
        """Process complex query using multiple retrieval modes"""
        
        # Execute retrieval modes in parallel based on classification
        retrieval_tasks = self.prepare_retrieval_tasks(query, context, classification)
        
        # Execute tasks
        mode_results = {}
        for mode, task in retrieval_tasks.items():
            try:
                mode_results[mode] = task.execute()
            except Exception as e:
                self.logger.warning(f"Retrieval mode {mode} failed: {e}")
                mode_results[mode] = None
        
        # Synthesize results using LLM reasoning
        synthesized_result = self.synthesize_multi_modal_results(
            query, mode_results, classification
        )
        
        # Validate and enhance with additional context
        validated_result = self.validate_and_enhance_result(
            synthesized_result, query, context
        )
        
        # Generate confidence assessment
        confidence_assessment = self.assess_result_confidence(
            validated_result, mode_results
        )
        
        return HybridReasoningResult(
            query=query,
            classification=classification,
            mode_results=mode_results,
            synthesized_result=validated_result,
            confidence_assessment=confidence_assessment,
            retrieval_modes_used=list(mode_results.keys()),
            processing_metadata=self.generate_processing_metadata(mode_results)
        )
    
    def synthesize_multi_modal_results(self, query: str, mode_results: Dict[str, Any],
                                     classification: QueryClassification) -> SynthesizedResult:
        """Use LLM to synthesize results from multiple retrieval modes"""
        
        # Prepare synthesis prompt
        synthesis_prompt = self.build_synthesis_prompt(query, mode_results, classification)
        
        # Execute LLM synthesis
        synthesis_response = self.llm.generate_response(synthesis_prompt)
        
        # Parse structured response
        synthesized_result = self.parse_synthesis_response(synthesis_response)
        
        # Cross-validate against original sources
        validated_result = self.cross_validate_synthesis(synthesized_result, mode_results)
        
        return validated_result
    
    def build_synthesis_prompt(self, query: str, mode_results: Dict[str, Any],
                             classification: QueryClassification) -> str:
        """Build comprehensive synthesis prompt for LLM"""
        
        prompt_parts = [
            "You are a mortgage lending expert analyzing information from multiple sources to answer a complex query.",
            f"Query: {query}",
            f"Query Intent: {classification.intent.primary_intent}",
            "",
            "Information Sources:"
        ]
        
        # Add vector similarity results
        if mode_results.get('VECTOR_SIMILARITY'):
            vector_results = mode_results['VECTOR_SIMILARITY']
            prompt_parts.append("## Semantic Search Results")
            for i, result in enumerate(vector_results[:5]):
                prompt_parts.append(f"{i+1}. {result.chunk.content[:500]}...")
                prompt_parts.append(f"   Source: {result.navigation_node.title}")
                prompt_parts.append(f"   Confidence: {result.similarity_score:.2f}")
            prompt_parts.append("")
        
        # Add graph traversal results
        if mode_results.get('GRAPH_TRAVERSAL'):
            graph_results = mode_results['GRAPH_TRAVERSAL']
            prompt_parts.append("## Structural Navigation Results")
            for i, result in enumerate(graph_results[:3]):
                prompt_parts.append(f"{i+1}. Path: {' → '.join([n.title for n in result.path.nodes])}")
                prompt_parts.append(f"   Context: {result.context_information}")
                prompt_parts.append(f"   Relevance: {result.relevance_score:.2f}")
            prompt_parts.append("")
        
        # Add decision path results
        if mode_results.get('DECISION_PATH'):
            decision_results = mode_results['DECISION_PATH']
            prompt_parts.append("## Decision Logic Analysis")
            if decision_results.combined_result:
                prompt_parts.append(f"Decision Outcome: {decision_results.combined_result.final_decision}")
                prompt_parts.append(f"Decision Path: {decision_results.explanation.structured_steps}")
                prompt_parts.append(f"Confidence: {decision_results.confidence_score:.2f}")
            prompt_parts.append("")
        
        # Add matrix lookup results
        if mode_results.get('MATRIX_INTERSECTION'):
            matrix_results = mode_results['MATRIX_INTERSECTION']
            prompt_parts.append("## Matrix Qualification Results")
            if matrix_results.combined_result:
                prompt_parts.append(f"Matrix Outcomes: {matrix_results.combined_result}")
                prompt_parts.append(f"Lookup Confidence: {matrix_results.confidence_score:.2f}")
            prompt_parts.append("")
        
        # Add synthesis instructions
        prompt_parts.extend([
            "## Synthesis Instructions",
            "1. Analyze all information sources for consistency and relevance",
            "2. Identify any conflicts or contradictions between sources",
            "3. Synthesize a comprehensive, accurate answer to the query",
            "4. Cite specific sources for key claims",
            "5. Note any limitations or missing information",
            "6. Provide confidence assessment for your answer",
            "",
            "## Response Format",
            "Provide your response in the following JSON structure:",
            "{",
            '  "answer": "Comprehensive answer to the query",',
            '  "key_points": ["Point 1", "Point 2", "Point 3"],',
            '  "source_citations": [{"claim": "Specific claim", "source": "Source reference"}],',
            '  "conflicts_identified": ["Any conflicts between sources"],',
            '  "confidence_level": 0.95,',
            '  "limitations": ["Any limitations or missing info"],',
            '  "additional_context": "Any relevant additional context"',
            "}"
        ])
        
        return "\n".join(prompt_parts)
    
    def validate_and_enhance_result(self, synthesized_result: SynthesizedResult,
                                  query: str, context: QueryContext) -> ValidatedResult:
        """Validate synthesis result and enhance with additional context"""
        
        # Fact-check key claims against knowledge base
        fact_check_results = self.fact_check_claims(synthesized_result.key_points)
        
        # Check for completeness
        completeness_assessment = self.assess_completeness(synthesized_result, query)
        
        # Add relevant context that might have been missed
        additional_context = self.find_additional_context(synthesized_result, query)
        
        # Generate final validation
        validation_result = ValidationResult(
            original_synthesis=synthesized_result,
            fact_check_results=fact_check_results,
            completeness_score=completeness_assessment.score,
            additional_context=additional_context,
            validation_confidence=self.calculate_validation_confidence(
                fact_check_results, completeness_assessment
            )
        )
        
        return ValidatedResult(
            synthesized_result=synthesized_result,
            validation=validation_result,
            enhanced_answer=self.enhance_answer_with_validation(
                synthesized_result, validation_result
            )
        )
```

## Query Processing Pipeline

### Orchestration Engine (`query_orchestrator.py`)

```python
class QueryOrchestrator:
    """Orchestrates the complete hybrid retrieval pipeline"""
    
    def __init__(self, neo4j_driver, config: HybridRetrievalConfig):
        self.driver = neo4j_driver
        self.config = config
        self.query_classifier = QueryClassifier()
        self.hybrid_reasoning = HybridReasoningEngine(neo4j_driver)
        self.performance_monitor = PerformanceMonitor()
        
    async def process_query(self, query: str, context: QueryContext = None) -> QueryResponse:
        """Process query through complete hybrid retrieval pipeline"""
        
        start_time = time.time()
        
        try:
            # 1. Query classification
            classification = self.query_classifier.classify_query(query, context)
            
            # 2. Determine processing strategy
            strategy = self.determine_processing_strategy(classification)
            
            # 3. Execute hybrid retrieval
            if strategy == 'SIMPLE_VECTOR':
                result = await self.execute_simple_vector_search(query, classification)
            elif strategy == 'GRAPH_NAVIGATION':
                result = await self.execute_graph_navigation(query, classification)
            elif strategy == 'DECISION_EVALUATION':
                result = await self.execute_decision_evaluation(query, classification, context)
            elif strategy == 'MATRIX_LOOKUP':
                result = await self.execute_matrix_lookup(query, classification, context)
            else:  # HYBRID_REASONING
                result = await self.execute_hybrid_reasoning(query, classification, context)
            
            # 4. Post-process and format result
            formatted_result = self.format_final_result(result, classification)
            
            # 5. Record performance metrics
            processing_time = time.time() - start_time
            self.performance_monitor.record_query_performance(
                query, classification, strategy, processing_time, formatted_result.confidence
            )
            
            return QueryResponse(
                query=query,
                classification=classification,
                strategy_used=strategy,
                result=formatted_result,
                processing_time=processing_time,
                confidence=formatted_result.confidence
            )
            
        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            return self.generate_error_response(query, str(e))
    
    def determine_processing_strategy(self, classification: QueryClassification) -> str:
        """Determine optimal processing strategy based on query classification"""
        
        intent = classification.intent.primary_intent
        complexity = classification.complexity_score
        
        # Simple queries can use vector search
        if complexity < 0.3 and intent in ['DOCUMENTATION_INQUIRY', 'POLICY_LOOKUP']:
            return 'SIMPLE_VECTOR'
        
        # Navigation-focused queries
        elif intent == 'PROCESS_NAVIGATION' or complexity < 0.5:
            return 'GRAPH_NAVIGATION'
        
        # Decision evaluation queries
        elif intent == 'QUALIFICATION_CHECK' and classification.has_borrower_params:
            return 'DECISION_EVALUATION'
        
        # Matrix calculation queries
        elif intent == 'CALCULATION_REQUEST' and classification.has_numeric_params:
            return 'MATRIX_LOOKUP'
        
        # Complex queries need hybrid reasoning
        else:
            return 'HYBRID_REASONING'
```

## Performance Optimization

### Caching and Optimization Strategies

```python
class PerformanceOptimizer:
    """Optimizes retrieval performance through caching and intelligent routing"""
    
    def __init__(self, redis_client, neo4j_driver):
        self.redis = redis_client
        self.driver = neo4j_driver
        self.query_cache = QueryCache(redis_client)
        self.embedding_cache = EmbeddingCache(redis_client)
        self.result_cache = ResultCache(redis_client)
        
    def optimize_vector_search(self, query_embedding: List[float], 
                              top_k: int) -> List[ChunkResult]:
        """Optimize vector search with pre-computed similarities"""
        
        # Check for cached similar queries
        cache_key = self.generate_embedding_cache_key(query_embedding)
        cached_results = self.embedding_cache.get(cache_key)
        
        if cached_results:
            return cached_results[:top_k]
        
        # Perform search with optimized parameters
        results = self.execute_optimized_vector_search(query_embedding, top_k * 2)
        
        # Cache results for future use
        self.embedding_cache.set(cache_key, results, ttl=3600)  # 1 hour TTL
        
        return results[:top_k]
    
    def optimize_graph_traversal(self, start_nodes: List[str], 
                                strategy: TraversalStrategy) -> List[GraphPath]:
        """Optimize graph traversal with path caching"""
        
        # Check for cached traversal paths
        cache_key = self.generate_traversal_cache_key(start_nodes, strategy)
        cached_paths = self.result_cache.get(cache_key)
        
        if cached_paths:
            return cached_paths
        
        # Execute traversal with batched queries
        paths = self.execute_batched_traversal(start_nodes, strategy)
        
        # Cache paths
        self.result_cache.set(cache_key, paths, ttl=1800)  # 30 minutes TTL
        
        return paths
```

## Success Metrics and Monitoring

### Performance Monitoring

```python
class RetrievalMetricsCollector:
    """Collects and analyzes retrieval performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'query_volume': Counter(),
            'strategy_usage': Counter(),
            'response_times': defaultdict(list),
            'confidence_scores': defaultdict(list),
            'user_satisfaction': defaultdict(list)
        }
    
    def record_query_performance(self, query: str, classification: QueryClassification,
                               strategy: str, response_time: float, confidence: float):
        """Record performance metrics for a query"""
        
        self.metrics['query_volume'][classification.intent.primary_intent] += 1
        self.metrics['strategy_usage'][strategy] += 1
        self.metrics['response_times'][strategy].append(response_time)
        self.metrics['confidence_scores'][strategy].append(confidence)
    
    def generate_performance_report(self) -> PerformanceReport:
        """Generate comprehensive performance report"""
        
        return PerformanceReport(
            total_queries=sum(self.metrics['query_volume'].values()),
            average_response_time=self.calculate_average_response_time(),
            strategy_effectiveness=self.calculate_strategy_effectiveness(),
            confidence_distribution=self.analyze_confidence_distribution(),
            recommendations=self.generate_optimization_recommendations()
        )
```

## Integration and Testing

The Hybrid Retrieval System integrates seamlessly with the existing LLM Graph Builder architecture while providing significant enhancements in query processing capability and accuracy. The system is designed for incremental deployment and continuous optimization based on real-world usage patterns.

## Next Steps

After Phase 3.2 completion, the system will be ready for Phase 3.5 frontend integration, which will provide sophisticated user interfaces for:
- Multi-modal query composition
- Retrieval strategy visualization  
- Confidence assessment displays
- Interactive result exploration
- Performance monitoring dashboards

The hybrid retrieval system forms the core intelligence layer for advanced mortgage document analysis and provides the foundation for sophisticated AI-powered lending assistance capabilities.
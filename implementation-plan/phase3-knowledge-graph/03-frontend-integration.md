# Phase 3.5: Frontend Integration for Enhanced Knowledge Graph

## Overview
This phase implements sophisticated frontend components that leverage the multi-layer knowledge graph schema and hybrid retrieval system. The frontend provides intuitive interfaces for complex query composition, multi-modal retrieval visualization, and interactive exploration of the enhanced knowledge graph while maintaining seamless integration with existing UI patterns.

## Frontend Architecture Integration

### Leveraging Advanced Graph Capabilities
- **Multi-Layer Visualization**: Extend existing graph components for layer-aware display
- **Hybrid Query Interface**: Build on existing search patterns for multi-modal queries
- **Intelligent Navigation**: Enhance existing navigation components with structure awareness
- **Performance Monitoring**: Integrate with existing analytics patterns
- **Contextual Intelligence**: Provide smart suggestions and contextual assistance

## Core Frontend Components

### 1. Advanced Query Composer

#### HybridQueryInterface Component (`frontend/src/components/Query/HybridQueryInterface.tsx`)

```typescript
interface HybridQueryInterfaceProps {
  onQuerySubmit: (query: QueryRequest) => void;
  onModeChange?: (modes: RetrievalMode[]) => void;
  currentPackage?: DocumentPackage;
}

const HybridQueryInterface: React.FC<HybridQueryInterfaceProps> = ({ 
  onQuerySubmit, 
  onModeChange, 
  currentPackage 
}) => {
  const [query, setQuery] = useState('');
  const [selectedModes, setSelectedModes] = useState<RetrievalMode[]>(['VECTOR_SIMILARITY']);
  const [queryClassification, setQueryClassification] = useState<QueryClassification | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [contextParams, setContextParams] = useState<QueryContextParams>({});
  
  // Auto-analyze query as user types (debounced)
  const debouncedAnalyzeQuery = useCallback(
    debounce(async (queryText: string) => {
      if (queryText.length > 10) {
        setIsAnalyzing(true);
        try {
          const classification = await analyzeQueryIntent(queryText, contextParams);
          setQueryClassification(classification);
          
          // Auto-suggest retrieval modes
          const suggestedModes = classification.suggested_retrieval_modes;
          setSelectedModes(suggestedModes);
          onModeChange?.(suggestedModes);
        } catch (error) {
          console.warn('Query analysis failed:', error);
        } finally {
          setIsAnalyzing(false);
        }
      }
    }, 800),
    [contextParams, onModeChange]
  );
  
  useEffect(() => {
    debouncedAnalyzeQuery(query);
  }, [query, debouncedAnalyzeQuery]);
  
  const handleSubmit = () => {
    const queryRequest: QueryRequest = {
      query,
      retrieval_modes: selectedModes,
      context_params: contextParams,
      package_context: currentPackage?.package_id,
      classification: queryClassification
    };
    
    onQuerySubmit(queryRequest);
  };
  
  return (
    <Box>
      {/* Main Query Input */}
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Box display="flex" alignItems="center" gap={2}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Ask about mortgage guidelines, qualifications, or policies..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            multiline
            rows={2}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  {isAnalyzing && <CircularProgress size={20} />}
                  <IconButton onClick={handleSubmit} disabled={!query.trim()}>
                    <SendIcon />
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
        </Box>
        
        {/* Query Intelligence Panel */}
        {queryClassification && (
          <Collapse in={!!queryClassification}>
            <Box mt={2} p={2} bgcolor="grey.50" borderRadius={1}>
              <Typography variant="subtitle2" gutterBottom>
                Query Analysis
              </Typography>
              <Box display="flex" gap={1} mb={1}>
                <Chip 
                  label={queryClassification.intent.primary_intent}
                  color="primary"
                  size="small"
                />
                <Chip 
                  label={`Complexity: ${(queryClassification.complexity_score * 100).toFixed(0)}%`}
                  color={queryClassification.complexity_score > 0.7 ? 'error' : 
                         queryClassification.complexity_score > 0.4 ? 'warning' : 'success'}
                  size="small"
                />
                <Chip 
                  label={`Confidence: ${(queryClassification.intent.confidence * 100).toFixed(0)}%`}
                  size="small"
                />
              </Box>
              
              {queryClassification.suggested_parameters.length > 0 && (
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    Suggested context parameters:
                  </Typography>
                  <Box display="flex" gap={0.5} mt={0.5}>
                    {queryClassification.suggested_parameters.map(param => (
                      <Chip 
                        key={param}
                        label={param}
                        variant="outlined"
                        size="small"
                        onClick={() => handleAddContextParam(param)}
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Box>
          </Collapse>
        )}
      </Paper>
      
      {/* Retrieval Mode Selection */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Search Strategy
        </Typography>
        <RetrievalModeSelector 
          selectedModes={selectedModes}
          onModeChange={setSelectedModes}
          queryClassification={queryClassification}
        />
      </Paper>
      
      {/* Context Parameters */}
      <ContextParameterPanel 
        params={contextParams}
        onChange={setContextParams}
        suggestions={queryClassification?.suggested_parameters || []}
      />
      
      {/* Quick Suggestions */}
      <QuerySuggestions 
        currentQuery={query}
        packageContext={currentPackage}
        onSuggestionClick={(suggestion) => setQuery(suggestion)}
      />
    </Box>
  );
};
```

#### RetrievalModeSelector Component (`frontend/src/components/Query/RetrievalModeSelector.tsx`)

```typescript
interface RetrievalModeSelectorProps {
  selectedModes: RetrievalMode[];
  onModeChange: (modes: RetrievalMode[]) => void;
  queryClassification?: QueryClassification;
}

const RetrievalModeSelector: React.FC<RetrievalModeSelectorProps> = ({ 
  selectedModes, 
  onModeChange, 
  queryClassification 
}) => {
  const [advancedMode, setAdvancedMode] = useState(false);
  
  const retrievalModes: RetrievalModeConfig[] = [
    {
      mode: 'VECTOR_SIMILARITY',
      name: 'Semantic Search',
      description: 'Find content based on meaning and context',
      icon: <SearchIcon />,
      recommended: true,
      estimatedTime: '< 1s'
    },
    {
      mode: 'GRAPH_TRAVERSAL',
      name: 'Structure Navigation',
      description: 'Follow document hierarchy and relationships',
      icon: <AccountTreeIcon />,
      recommended: queryClassification?.intent.primary_intent === 'PROCESS_NAVIGATION',
      estimatedTime: '1-2s'
    },
    {
      mode: 'DECISION_PATH',
      name: 'Decision Logic',
      description: 'Follow qualification decision trees',
      icon: <DeviceHubIcon />,
      recommended: queryClassification?.intent.primary_intent === 'QUALIFICATION_CHECK',
      estimatedTime: '2-3s'
    },
    {
      mode: 'MATRIX_INTERSECTION',
      name: 'Matrix Lookup',
      description: 'Query qualification and pricing matrices',
      icon: <GridViewIcon />,
      recommended: queryClassification?.intent.primary_intent === 'CALCULATION_REQUEST',
      estimatedTime: '1s'
    },
    {
      mode: 'HYBRID_REASONING',
      name: 'AI Reasoning',
      description: 'Combine all methods with intelligent analysis',
      icon: <PsychologyIcon />,
      recommended: queryClassification?.complexity_score > 0.7,
      estimatedTime: '3-5s',
      advanced: true
    }
  ];
  
  const handleModeToggle = (mode: RetrievalMode) => {
    const newModes = selectedModes.includes(mode)
      ? selectedModes.filter(m => m !== mode)
      : [...selectedModes, mode];
    
    onModeChange(newModes);
  };
  
  const getRecommendedModes = () => {
    return retrievalModes
      .filter(config => config.recommended)
      .map(config => config.mode);
  };
  
  const handleUseRecommended = () => {
    onModeChange(getRecommendedModes());
  };
  
  return (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
        <FormControlLabel
          control={
            <Switch
              checked={advancedMode}
              onChange={(e) => setAdvancedMode(e.target.checked)}
            />
          }
          label="Advanced Mode"
        />
        <Button 
          size="small" 
          onClick={handleUseRecommended}
          disabled={!queryClassification}
        >
          Use Recommended
        </Button>
      </Box>
      
      <Grid container spacing={2}>
        {retrievalModes
          .filter(config => advancedMode || !config.advanced)
          .map(config => (
            <Grid item xs={12} sm={6} md={4} key={config.mode}>
              <Card 
                variant={selectedModes.includes(config.mode) ? "elevation" : "outlined"}
                sx={{ 
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  border: selectedModes.includes(config.mode) ? 2 : 1,
                  borderColor: selectedModes.includes(config.mode) ? 'primary.main' : 'divider',
                  '&:hover': { elevation: 4 }
                }}
                onClick={() => handleModeToggle(config.mode)}
              >
                <CardContent sx={{ p: 2 }}>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    {config.icon}
                    <Typography variant="subtitle2">
                      {config.name}
                    </Typography>
                    {config.recommended && (
                      <Chip label="Recommended" color="success" size="small" />
                    )}
                  </Box>
                  
                  <Typography variant="body2" color="textSecondary" mb={1}>
                    {config.description}
                  </Typography>
                  
                  <Box display="flex" justifyContent="between" alignItems="center">
                    <Typography variant="caption" color="textSecondary">
                      ~{config.estimatedTime}
                    </Typography>
                    <Checkbox 
                      checked={selectedModes.includes(config.mode)}
                      size="small"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
      </Grid>
      
      {selectedModes.length > 1 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            Using multiple retrieval modes will provide more comprehensive results but may take longer.
            Estimated total time: {calculateEstimatedTime(selectedModes)}
          </Typography>
        </Alert>
      )}
    </Box>
  );
};
```

### 2. Multi-Modal Result Visualization

#### HybridResultsViewer Component (`frontend/src/components/Results/HybridResultsViewer.tsx`)

```typescript
interface HybridResultsViewerProps {
  queryRequest: QueryRequest;
  queryResult: HybridQueryResult;
  onResultSelect?: (result: any) => void;
  onFollowUp?: (query: string) => void;
}

const HybridResultsViewer: React.FC<HybridResultsViewerProps> = ({ 
  queryRequest, 
  queryResult, 
  onResultSelect, 
  onFollowUp 
}) => {
  const [selectedTab, setSelectedTab] = useState('synthesis');
  const [selectedModeResult, setSelectedModeResult] = useState<string | null>(null);
  const [showConfidenceDetails, setShowConfidenceDetails] = useState(false);
  
  const getModeResultsAvailable = () => {
    return Object.keys(queryResult.mode_results).filter(mode => 
      queryResult.mode_results[mode] && queryResult.mode_results[mode].length > 0
    );
  };
  
  return (
    <Box>
      {/* Query Summary Header */}
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Box display="flex" justifyContent="between" alignItems="center">
          <Box>
            <Typography variant="h6" gutterBottom>
              Query Results
            </Typography>
            <Typography variant="body2" color="textSecondary">
              "{queryRequest.query}"
            </Typography>
          </Box>
          
          <Box display="flex" alignItems="center" gap={2}>
            <ConfidenceIndicator 
              confidence={queryResult.confidence_assessment.overall_confidence}
              onClick={() => setShowConfidenceDetails(true)}
            />
            <Chip 
              label={`${queryResult.processing_metadata.total_processing_time.toFixed(1)}s`}
              size="small"
              icon={<TimerIcon />}
            />
          </Box>
        </Box>
        
        {/* Mode Usage Summary */}
        <Box display="flex" gap={1} mt={2}>
          {queryResult.retrieval_modes_used.map(mode => (
            <Chip 
              key={mode}
              label={getModeDisplayName(mode)}
              size="small"
              color={queryResult.mode_results[mode] ? 'primary' : 'default'}
              variant={queryResult.mode_results[mode] ? 'filled' : 'outlined'}
            />
          ))}
        </Box>
      </Paper>
      
      {/* Main Results Tabs */}
      <Paper elevation={1}>
        <Tabs 
          value={selectedTab} 
          onChange={(_, newTab) => setSelectedTab(newTab)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="AI Synthesis" value="synthesis" />
          <Tab label="Source Analysis" value="sources" />
          <Tab label="Mode Breakdown" value="modes" />
          <Tab label="Confidence Details" value="confidence" />
        </Tabs>
        
        <Box sx={{ p: 2 }}>
          {/* AI Synthesis Tab */}
          {selectedTab === 'synthesis' && (
            <SynthesisResultPanel 
              synthesizedResult={queryResult.synthesized_result}
              onFollowUp={onFollowUp}
              onSourceClick={onResultSelect}
            />
          )}
          
          {/* Source Analysis Tab */}
          {selectedTab === 'sources' && (
            <SourceAnalysisPanel 
              modeResults={queryResult.mode_results}
              onSourceSelect={onResultSelect}
            />
          )}
          
          {/* Mode Breakdown Tab */}
          {selectedTab === 'modes' && (
            <ModeBreakdownPanel 
              modeResults={queryResult.mode_results}
              processingMetadata={queryResult.processing_metadata}
              onModeSelect={setSelectedModeResult}
            />
          )}
          
          {/* Confidence Details Tab */}
          {selectedTab === 'confidence' && (
            <ConfidenceAnalysisPanel 
              confidenceAssessment={queryResult.confidence_assessment}
              validationResult={queryResult.validation_result}
            />
          )}
        </Box>
      </Paper>
      
      {/* Follow-up Suggestions */}
      <FollowUpSuggestions 
        queryResult={queryResult}
        onSuggestionClick={onFollowUp}
      />
      
      {/* Confidence Details Modal */}
      <ConfidenceDetailsModal 
        isOpen={showConfidenceDetails}
        onClose={() => setShowConfidenceDetails(false)}
        confidenceAssessment={queryResult.confidence_assessment}
      />
    </Box>
  );
};
```

#### SynthesisResultPanel Component (`frontend/src/components/Results/SynthesisResultPanel.tsx`)

```typescript
interface SynthesisResultPanelProps {
  synthesizedResult: SynthesizedResult;
  onFollowUp?: (query: string) => void;
  onSourceClick?: (source: any) => void;
}

const SynthesisResultPanel: React.FC<SynthesisResultPanelProps> = ({ 
  synthesizedResult, 
  onFollowUp, 
  onSourceClick 
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['answer']));
  
  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };
  
  return (
    <Box>
      {/* Main Answer */}
      <Box mb={3}>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <AutoAwesomeIcon color="primary" />
          <Typography variant="h6">AI Analysis</Typography>
          <Chip 
            label={`${(synthesizedResult.confidence_level * 100).toFixed(0)}% confident`}
            size="small"
            color={synthesizedResult.confidence_level > 0.8 ? 'success' : 
                   synthesizedResult.confidence_level > 0.6 ? 'warning' : 'error'}
          />
        </Box>
        
        <Paper variant="outlined" sx={{ p: 3, bgcolor: 'grey.50' }}>
          <Typography variant="body1" sx={{ lineHeight: 1.7 }}>
            {synthesizedResult.answer}
          </Typography>
        </Paper>
      </Box>
      
      {/* Key Points */}
      {synthesizedResult.key_points && synthesizedResult.key_points.length > 0 && (
        <Accordion 
          expanded={expandedSections.has('key_points')}
          onChange={() => toggleSection('key_points')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1">Key Points</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List>
              {synthesizedResult.key_points.map((point, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <FiberManualRecordIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={point} />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}
      
      {/* Source Citations */}
      {synthesizedResult.source_citations && synthesizedResult.source_citations.length > 0 && (
        <Accordion 
          expanded={expandedSections.has('citations')}
          onChange={() => toggleSection('citations')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1">
              Sources ({synthesizedResult.source_citations.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List>
              {synthesizedResult.source_citations.map((citation, index) => (
                <ListItem 
                  key={index}
                  button
                  onClick={() => onSourceClick?.(citation.source)}
                >
                  <ListItemIcon>
                    <LinkIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary={citation.claim}
                    secondary={citation.source}
                  />
                  <ListItemSecondaryAction>
                    <IconButton size="small">
                      <OpenInNewIcon fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}
      
      {/* Conflicts Identified */}
      {synthesizedResult.conflicts_identified && synthesizedResult.conflicts_identified.length > 0 && (
        <Accordion 
          expanded={expandedSections.has('conflicts')}
          onChange={() => toggleSection('conflicts')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <WarningIcon color="warning" />
              <Typography variant="subtitle1">
                Conflicts Detected ({synthesizedResult.conflicts_identified.length})
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <AlertTitle>Information Conflicts</AlertTitle>
              The AI detected some conflicting information in the sources. Review carefully.
            </Alert>
            <List>
              {synthesizedResult.conflicts_identified.map((conflict, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <ReportProblemIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText primary={conflict} />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}
      
      {/* Limitations */}
      {synthesizedResult.limitations && synthesizedResult.limitations.length > 0 && (
        <Accordion 
          expanded={expandedSections.has('limitations')}
          onChange={() => toggleSection('limitations')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1">Limitations & Caveats</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List>
              {synthesizedResult.limitations.map((limitation, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <InfoIcon color="info" />
                  </ListItemIcon>
                  <ListItemText primary={limitation} />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}
      
      {/* Additional Context */}
      {synthesizedResult.additional_context && (
        <Box mt={2}>
          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
            <Typography variant="subtitle2" gutterBottom>
              Additional Context
            </Typography>
            <Typography variant="body2">
              {synthesizedResult.additional_context}
            </Typography>
          </Paper>
        </Box>
      )}
    </Box>
  );
};
```

### 3. Enhanced Graph Visualization

#### MultiLayerGraphVisualization Component (`frontend/src/components/Graph/MultiLayerGraphVisualization.tsx`)

```typescript
interface MultiLayerGraphVisualizationProps {
  graphData: MultiLayerGraphData;
  selectedLayers: GraphLayer[];
  onLayerToggle: (layer: GraphLayer) => void;
  onNodeSelect?: (node: GraphNode) => void;
  onRelationshipSelect?: (relationship: GraphRelationship) => void;
  queryResult?: HybridQueryResult;
}

const MultiLayerGraphVisualization: React.FC<MultiLayerGraphVisualizationProps> = ({ 
  graphData, 
  selectedLayers, 
  onLayerToggle, 
  onNodeSelect, 
  onRelationshipSelect,
  queryResult 
}) => {
  const graphRef = useRef<any>(null);
  const [layoutMode, setLayoutMode] = useState<'hierarchical' | 'force' | 'circular'>('force');
  const [filterMode, setFilterMode] = useState<'all' | 'relevant' | 'path'>('relevant');
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [showMetadata, setShowMetadata] = useState(false);
  
  // Filter graph data based on selected layers and query relevance
  const filteredGraphData = useMemo(() => {
    return filterGraphDataByLayers(graphData, selectedLayers, queryResult, filterMode);
  }, [graphData, selectedLayers, queryResult, filterMode]);
  
  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node.id);
    onNodeSelect?.(node);
  };
  
  const handleRelationshipClick = (relationship: GraphRelationship) => {
    onRelationshipSelect?.(relationship);
  };
  
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Controls */}
      <Paper elevation={1} sx={{ p: 2, mb: 1 }}>
        <Box display="flex" justifyContent="between" alignItems="center">
          {/* Layer Controls */}
          <Box display="flex" gap={1} alignItems="center">
            <Typography variant="subtitle2">Layers:</Typography>
            <LayerToggleGroup 
              layers={Object.keys(graphData.layers)}
              selectedLayers={selectedLayers}
              onLayerToggle={onLayerToggle}
            />
          </Box>
          
          {/* View Controls */}
          <Box display="flex" gap={1} alignItems="center">
            <ToggleButtonGroup
              value={layoutMode}
              exclusive
              onChange={(_, value) => value && setLayoutMode(value)}
              size="small"
            >
              <ToggleButton value="hierarchical">Hierarchy</ToggleButton>
              <ToggleButton value="force">Force</ToggleButton>
              <ToggleButton value="circular">Circular</ToggleButton>
            </ToggleButtonGroup>
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <Select
                value={filterMode}
                onChange={(e) => setFilterMode(e.target.value as any)}
              >
                <MenuItem value="all">All Nodes</MenuItem>
                <MenuItem value="relevant">Query Relevant</MenuItem>
                <MenuItem value="path">Query Paths</MenuItem>
              </Select>
            </FormControl>
            
            <IconButton 
              onClick={() => setShowMetadata(!showMetadata)}
              color={showMetadata ? 'primary' : 'default'}
            >
              <InfoIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>
      
      {/* Graph Visualization */}
      <Box sx={{ flex: 1, position: 'relative' }}>
        <EnhancedGraphVisualization
          ref={graphRef}
          nodes={filteredGraphData.nodes}
          relationships={filteredGraphData.relationships}
          layout={layoutMode}
          onNodeClick={handleNodeClick}
          onRelationshipClick={handleRelationshipClick}
          selectedNodeId={selectedNode}
          nodeColorScheme={getLayerColorScheme(selectedLayers)}
          relationshipColorScheme={getRelationshipColorScheme()}
          highlightedElements={queryResult ? getQueryRelevantElements(queryResult) : undefined}
          showLabels={true}
          interactive={true}
          clustering={layoutMode === 'force'}
        />
        
        {/* Graph Statistics Overlay */}
        {showMetadata && (
          <Paper 
            sx={{ 
              position: 'absolute', 
              top: 10, 
              left: 10, 
              p: 2, 
              minWidth: 200,
              backgroundColor: 'rgba(255,255,255,0.95)'
            }}
          >
            <Typography variant="subtitle2" gutterBottom>Graph Statistics</Typography>
            <Box>
              <Typography variant="caption" display="block">
                Nodes: {filteredGraphData.nodes.length}
              </Typography>
              <Typography variant="caption" display="block">
                Relationships: {filteredGraphData.relationships.length}
              </Typography>
              <Typography variant="caption" display="block">
                Layers: {selectedLayers.length}/{Object.keys(graphData.layers).length}
              </Typography>
              {queryResult && (
                <Typography variant="caption" display="block">
                  Query Relevance: {getQueryRelevanceScore(filteredGraphData, queryResult).toFixed(2)}
                </Typography>
              )}
            </Box>
          </Paper>
        )}
        
        {/* Legend */}
        <MultiLayerGraphLegend 
          layers={selectedLayers}
          colorScheme={getLayerColorScheme(selectedLayers)}
          position="bottom-right"
        />
      </Box>
    </Box>
  );
};
```

#### LayerToggleGroup Component (`frontend/src/components/Graph/LayerToggleGroup.tsx`)

```typescript
interface LayerToggleGroupProps {
  layers: string[];
  selectedLayers: GraphLayer[];
  onLayerToggle: (layer: GraphLayer) => void;
}

const LayerToggleGroup: React.FC<LayerToggleGroupProps> = ({ 
  layers, 
  selectedLayers, 
  onLayerToggle 
}) => {
  const layerConfigs: Record<string, LayerConfig> = {
    DOCUMENT: {
      name: 'Documents',
      icon: <DescriptionIcon />,
      color: '#1976d2',
      description: 'Document packages and individual files'
    },
    STRUCTURE: {
      name: 'Structure',
      icon: <AccountTreeIcon />,
      color: '#388e3c',
      description: 'Navigation hierarchy and document structure'
    },
    ENTITY: {
      name: 'Entities',
      icon: <LabelIcon />,
      color: '#f57c00',
      description: 'Extracted entities and concepts'
    },
    DECISION: {
      name: 'Decisions',
      icon: <DeviceHubIcon />,
      color: '#7b1fa2',
      description: 'Decision trees and logic flows'
    },
    BUSINESS: {
      name: 'Business',
      icon: <BusinessIcon />,
      color: '#d32f2f',
      description: 'Business policies and rules'
    }
  };
  
  return (
    <Box display="flex" gap={0.5}>
      {layers.map(layer => {
        const config = layerConfigs[layer];
        const isSelected = selectedLayers.includes(layer as GraphLayer);
        
        return (
          <Tooltip key={layer} title={config.description} arrow>
            <Chip
              icon={config.icon}
              label={config.name}
              onClick={() => onLayerToggle(layer as GraphLayer)}
              color={isSelected ? 'primary' : 'default'}
              variant={isSelected ? 'filled' : 'outlined'}
              size="small"
              sx={{
                '& .MuiChip-icon': {
                  color: isSelected ? 'white' : config.color
                }
              }}
            />
          </Tooltip>
        );
      })}
    </Box>
  );
};
```

### 4. Intelligent Navigation Assistant

#### NavigationAssistant Component (`frontend/src/components/Navigation/NavigationAssistant.tsx`)

```typescript
interface NavigationAssistantProps {
  currentContext: NavigationContext;
  onNavigate: (destination: NavigationDestination) => void;
  onSuggestedQuery: (query: string) => void;
}

const NavigationAssistant: React.FC<NavigationAssistantProps> = ({ 
  currentContext, 
  onNavigate, 
  onSuggestedQuery 
}) => {
  const [suggestions, setSuggestions] = useState<NavigationSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [assistantMode, setAssistantMode] = useState<'explore' | 'search' | 'analyze'>('explore');
  
  // Generate contextual suggestions based on current location
  useEffect(() => {
    if (currentContext.node_id) {
      generateContextualSuggestions(currentContext);
    }
  }, [currentContext]);
  
  const generateContextualSuggestions = async (context: NavigationContext) => {
    setIsLoading(true);
    try {
      const response = await getNavigationSuggestions(context, assistantMode);
      setSuggestions(response.suggestions);
    } catch (error) {
      console.error('Failed to generate suggestions:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
        <Typography variant="h6">
          <AssistantIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Navigation Assistant
        </Typography>
        
        <ToggleButtonGroup
          value={assistantMode}
          exclusive
          onChange={(_, value) => value && setAssistantMode(value)}
          size="small"
        >
          <ToggleButton value="explore">Explore</ToggleButton>
          <ToggleButton value="search">Search</ToggleButton>
          <ToggleButton value="analyze">Analyze</ToggleButton>
        </ToggleButtonGroup>
      </Box>
      
      {/* Current Context Display */}
      <Box mb={2}>
        <CurrentContextDisplay context={currentContext} />
      </Box>
      
      {/* Mode-Specific Content */}
      {assistantMode === 'explore' && (
        <ExplorationSuggestions 
          suggestions={suggestions.filter(s => s.type === 'EXPLORATION')}
          onNavigate={onNavigate}
          isLoading={isLoading}
        />
      )}
      
      {assistantMode === 'search' && (
        <SearchSuggestions 
          suggestions={suggestions.filter(s => s.type === 'SEARCH')}
          onSuggestedQuery={onSuggestedQuery}
          currentContext={currentContext}
        />
      )}
      
      {assistantMode === 'analyze' && (
        <AnalysisSuggestions 
          suggestions={suggestions.filter(s => s.type === 'ANALYSIS')}
          onNavigate={onNavigate}
          onSuggestedQuery={onSuggestedQuery}
        />
      )}
      
      {/* Quick Actions */}
      <Box mt={2}>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="subtitle2" gutterBottom>Quick Actions</Typography>
        <Box display="flex" gap={1} flexWrap="wrap">
          <Button 
            size="small" 
            startIcon={<HomeIcon />}
            onClick={() => onNavigate({ type: 'HOME' })}
          >
            Home
          </Button>
          <Button 
            size="small" 
            startIcon={<HistoryIcon />}
            onClick={() => onNavigate({ type: 'HISTORY' })}
          >
            Recent
          </Button>
          <Button 
            size="small" 
            startIcon={<BookmarkIcon />}
            onClick={() => onNavigate({ type: 'BOOKMARKS' })}
          >
            Bookmarks
          </Button>
          <Button 
            size="small" 
            startIcon={<TrendingUpIcon />}
            onClick={() => onNavigate({ type: 'TRENDING' })}
          >
            Trending
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};
```

### 5. Performance Analytics Dashboard

#### QueryPerformanceDashboard Component (`frontend/src/components/Analytics/QueryPerformanceDashboard.tsx`)

```typescript
interface QueryPerformanceDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

const QueryPerformanceDashboard: React.FC<QueryPerformanceDashboardProps> = ({ 
  isOpen, 
  onClose 
}) => {
  const [performanceData, setPerformanceData] = useState<PerformanceMetrics | null>(null);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [selectedMetric, setSelectedMetric] = useState<'response_time' | 'confidence' | 'satisfaction'>('response_time');
  
  useEffect(() => {
    if (isOpen) {
      loadPerformanceData(timeRange);
    }
  }, [isOpen, timeRange]);
  
  const loadPerformanceData = async (range: string) => {
    try {
      const data = await getQueryPerformanceMetrics(range);
      setPerformanceData(data);
    } catch (error) {
      console.error('Failed to load performance data:', error);
    }
  };
  
  return (
    <CustomModal isOpen={isOpen} onClose={onClose} size="fullscreen">
      <Box sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
          <Typography variant="h5">Query Performance Analytics</Typography>
          
          <Box display="flex" gap={2} alignItems="center">
            <FormControl size="small">
              <Select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as any)}
              >
                <MenuItem value="1h">Last Hour</MenuItem>
                <MenuItem value="24h">Last 24 Hours</MenuItem>
                <MenuItem value="7d">Last 7 Days</MenuItem>
                <MenuItem value="30d">Last 30 Days</MenuItem>
              </Select>
            </FormControl>
            
            <IconButton onClick={() => loadPerformanceData(timeRange)}>
              <RefreshIcon />
            </IconButton>
            
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
        
        {performanceData ? (
          <Grid container spacing={3} sx={{ flex: 1 }}>
            {/* Overview Cards */}
            <Grid item xs={12}>
              <Grid container spacing={2}>
                <Grid item xs={3}>
                  <MetricCard 
                    title="Total Queries"
                    value={performanceData.total_queries}
                    trend={performanceData.query_volume_trend}
                    icon={<QueryStatsIcon />}
                  />
                </Grid>
                <Grid item xs={3}>
                  <MetricCard 
                    title="Avg Response Time"
                    value={`${performanceData.avg_response_time.toFixed(1)}s`}
                    trend={performanceData.response_time_trend}
                    icon={<SpeedIcon />}
                  />
                </Grid>
                <Grid item xs={3}>
                  <MetricCard 
                    title="Avg Confidence"
                    value={`${(performanceData.avg_confidence * 100).toFixed(0)}%`}
                    trend={performanceData.confidence_trend}
                    icon={<VerifiedIcon />}
                  />
                </Grid>
                <Grid item xs={3}>
                  <MetricCard 
                    title="User Satisfaction"
                    value={`${(performanceData.user_satisfaction * 100).toFixed(0)}%`}
                    trend={performanceData.satisfaction_trend}
                    icon={<ThumbUpIcon />}
                  />
                </Grid>
              </Grid>
            </Grid>
            
            {/* Performance Charts */}
            <Grid item xs={8}>
              <Paper sx={{ p: 2, height: '400px' }}>
                <Typography variant="h6" gutterBottom>
                  Performance Over Time
                </Typography>
                <PerformanceTimeSeriesChart 
                  data={performanceData.time_series}
                  selectedMetric={selectedMetric}
                  onMetricChange={setSelectedMetric}
                />
              </Paper>
            </Grid>
            
            <Grid item xs={4}>
              <Paper sx={{ p: 2, height: '400px' }}>
                <Typography variant="h6" gutterBottom>
                  Retrieval Mode Usage
                </Typography>
                <RetrievalModeChart 
                  data={performanceData.mode_usage}
                />
              </Paper>
            </Grid>
            
            {/* Query Intent Analysis */}
            <Grid item xs={6}>
              <Paper sx={{ p: 2, height: '300px' }}>
                <Typography variant="h6" gutterBottom>
                  Query Intent Distribution
                </Typography>
                <QueryIntentChart 
                  data={performanceData.intent_distribution}
                />
              </Paper>
            </Grid>
            
            {/* Top Performing Queries */}
            <Grid item xs={6}>
              <Paper sx={{ p: 2, height: '300px' }}>
                <Typography variant="h6" gutterBottom>
                  Top Performing Queries
                </Typography>
                <TopQueriesTable 
                  queries={performanceData.top_queries}
                />
              </Paper>
            </Grid>
          </Grid>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" sx={{ flex: 1 }}>
            <CircularProgress />
          </Box>
        )}
      </Box>
    </CustomModal>
  );
};
```

## API Integration Services

### Enhanced Query Service (`frontend/src/services/HybridQueryAPI.ts`)

```typescript
export interface QueryRequest {
  query: string;
  retrieval_modes: RetrievalMode[];
  context_params: QueryContextParams;
  package_context?: string;
  classification?: QueryClassification;
}

export interface HybridQueryResult {
  query_id: string;
  request: QueryRequest;
  classification: QueryClassification;
  mode_results: Record<string, any>;
  synthesized_result: SynthesizedResult;
  confidence_assessment: ConfidenceAssessment;
  validation_result: ValidationResult;
  retrieval_modes_used: RetrievalMode[];
  processing_metadata: ProcessingMetadata;
}

export const submitHybridQuery = async (queryRequest: QueryRequest): Promise<ServerResponse> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const formData = new FormData();
  formData.append('query', queryRequest.query);
  formData.append('retrieval_modes', JSON.stringify(queryRequest.retrieval_modes));
  formData.append('context_params', JSON.stringify(queryRequest.context_params));
  
  if (queryRequest.package_context) {
    formData.append('package_context', queryRequest.package_context);
  }
  
  if (queryRequest.classification) {
    formData.append('classification', JSON.stringify(queryRequest.classification));
  }
  
  appendUserCredentials(formData, userCredentials);
  
  const response = await fetch(`${apiUrl}/query/hybrid`, {
    method: 'POST',
    body: formData,
  });
  
  return response.json();
};

export const analyzeQueryIntent = async (
  query: string, 
  context: QueryContextParams
): Promise<QueryClassification> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const formData = new FormData();
  formData.append('query', query);
  formData.append('context', JSON.stringify(context));
  
  appendUserCredentials(formData, userCredentials);
  
  const response = await fetch(`${apiUrl}/query/analyze`, {
    method: 'POST',
    body: formData,
  });
  
  const result = await response.json();
  return result.data;
};

export const getNavigationSuggestions = async (
  context: NavigationContext, 
  mode: string
): Promise<{ suggestions: NavigationSuggestion[] }> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const params = new URLSearchParams();
  params.append('context', JSON.stringify(context));
  params.append('mode', mode);
  appendUserCredentialsToParams(params, userCredentials);
  
  const response = await fetch(`${apiUrl}/navigation/suggestions?${params}`, {
    method: 'GET',
  });
  
  const result = await response.json();
  return result.data;
};

export const getQueryPerformanceMetrics = async (timeRange: string): Promise<PerformanceMetrics> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const params = new URLSearchParams();
  params.append('time_range', timeRange);
  appendUserCredentialsToParams(params, userCredentials);
  
  const response = await fetch(`${apiUrl}/analytics/query-performance?${params}`, {
    method: 'GET',
  });
  
  const result = await response.json();
  return result.data;
};
```

## State Management Integration

### Query Context Provider (`frontend/src/context/QueryContext.tsx`)

```typescript
interface QueryContextType {
  currentQuery: QueryRequest | null;
  queryResult: HybridQueryResult | null;
  queryHistory: QueryHistoryItem[];
  isProcessing: boolean;
  error: string | null;
  
  submitQuery: (request: QueryRequest) => Promise<HybridQueryResult>;
  clearResult: () => void;
  retryQuery: () => Promise<void>;
  saveToHistory: (query: QueryRequest, result: HybridQueryResult) => void;
  getQueryFromHistory: (queryId: string) => QueryHistoryItem | null;
}

export const QueryContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentQuery, setCurrentQuery] = useState<QueryRequest | null>(null);
  const [queryResult, setQueryResult] = useState<HybridQueryResult | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const submitQuery = async (request: QueryRequest): Promise<HybridQueryResult> => {
    setIsProcessing(true);
    setError(null);
    setCurrentQuery(request);
    
    try {
      const response = await submitHybridQuery(request);
      if (response.status === 'success') {
        const result = response.data;
        setQueryResult(result);
        saveToHistory(request, result);
        return result;
      } else {
        throw new Error(response.error || 'Query failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Query processing failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsProcessing(false);
    }
  };
  
  const clearResult = () => {
    setQueryResult(null);
    setCurrentQuery(null);
    setError(null);
  };
  
  const retryQuery = async () => {
    if (currentQuery) {
      await submitQuery(currentQuery);
    }
  };
  
  const saveToHistory = (query: QueryRequest, result: HybridQueryResult) => {
    const historyItem: QueryHistoryItem = {
      id: result.query_id,
      query: query.query,
      timestamp: new Date(),
      retrieval_modes: query.retrieval_modes,
      confidence: result.confidence_assessment.overall_confidence,
      processing_time: result.processing_metadata.total_processing_time
    };
    
    setQueryHistory(prev => [historyItem, ...prev.slice(0, 49)]); // Keep last 50 queries
  };
  
  const getQueryFromHistory = (queryId: string): QueryHistoryItem | null => {
    return queryHistory.find(item => item.id === queryId) || null;
  };
  
  const value: QueryContextType = {
    currentQuery,
    queryResult,
    queryHistory,
    isProcessing,
    error,
    submitQuery,
    clearResult,
    retryQuery,
    saveToHistory,
    getQueryFromHistory
  };
  
  return (
    <QueryContext.Provider value={value}>
      {children}
    </QueryContext.Provider>
  );
};
```

## Integration with Existing Components

### 1. Enhanced Chatbot Integration

```typescript
// In frontend/src/components/ChatBot/Chatbot.tsx
const EnhancedChatbot: React.FC = () => {
  const { submitQuery, queryResult, isProcessing } = useContext(QueryContext);
  const [showHybridInterface, setShowHybridInterface] = useState(false);
  
  const handleAdvancedQuery = async (queryRequest: QueryRequest) => {
    try {
      const result = await submitQuery(queryRequest);
      // Display result in chat interface
      addMessageToChat({
        type: 'hybrid_result',
        content: result.synthesized_result.answer,
        confidence: result.confidence_assessment.overall_confidence,
        sources: result.synthesized_result.source_citations
      });
    } catch (error) {
      addMessageToChat({
        type: 'error',
        content: 'Failed to process advanced query'
      });
    }
  };
  
  return (
    <Box>
      {/* Existing chatbot interface */}
      <StandardChatInterface />
      
      {/* Advanced query toggle */}
      <Box mt={1}>
        <Button 
          size="small" 
          startIcon={<PsychologyIcon />}
          onClick={() => setShowHybridInterface(!showHybridInterface)}
        >
          Advanced Query
        </Button>
      </Box>
      
      {/* Hybrid query interface */}
      <Collapse in={showHybridInterface}>
        <Box mt={2}>
          <HybridQueryInterface 
            onQuerySubmit={handleAdvancedQuery}
            currentPackage={getCurrentPackage()}
          />
        </Box>
      </Collapse>
    </Box>
  );
};
```

### 2. Graph View Enhancement

```typescript
// In frontend/src/components/Graph/GraphViewModal.tsx
const EnhancedGraphViewModal: React.FC = ({ isOpen, onClose }) => {
  const [selectedLayers, setSelectedLayers] = useState<GraphLayer[]>(['ENTITY', 'STRUCTURE']);
  const [graphData, setGraphData] = useState<MultiLayerGraphData | null>(null);
  const { queryResult } = useContext(QueryContext);
  
  useEffect(() => {
    if (isOpen) {
      loadMultiLayerGraphData();
    }
  }, [isOpen]);
  
  const handleLayerToggle = (layer: GraphLayer) => {
    setSelectedLayers(prev => 
      prev.includes(layer) 
        ? prev.filter(l => l !== layer)
        : [...prev, layer]
    );
  };
  
  return (
    <CustomModal isOpen={isOpen} onClose={onClose} size="fullscreen">
      <MultiLayerGraphVisualization 
        graphData={graphData}
        selectedLayers={selectedLayers}
        onLayerToggle={handleLayerToggle}
        queryResult={queryResult}
      />
    </CustomModal>
  );
};
```

## Type System Extensions

### Advanced Query Types (`frontend/src/types.ts`)

```typescript
// Add to existing types.ts file

export type RetrievalMode = 
  | 'VECTOR_SIMILARITY' 
  | 'GRAPH_TRAVERSAL' 
  | 'DECISION_PATH' 
  | 'MATRIX_INTERSECTION' 
  | 'HYBRID_REASONING';

export type GraphLayer = 
  | 'DOCUMENT' 
  | 'STRUCTURE' 
  | 'ENTITY' 
  | 'DECISION' 
  | 'BUSINESS';

export interface QueryClassification {
  intent: {
    primary_intent: string;
    confidence: number;
    supporting_evidence: string[];
  };
  domain_focus: {
    has_matrix_focus: boolean;
    has_decision_focus: boolean;
    has_documentation_focus: boolean;
  };
  complexity_score: number;
  suggested_retrieval_modes: RetrievalMode[];
  suggested_parameters: string[];
  expected_response_type: string;
}

export interface SynthesizedResult {
  answer: string;
  key_points: string[];
  source_citations: {
    claim: string;
    source: string;
  }[];
  conflicts_identified: string[];
  confidence_level: number;
  limitations: string[];
  additional_context: string;
}

export interface ConfidenceAssessment {
  overall_confidence: number;
  mode_confidences: Record<string, number>;
  synthesis_confidence: number;
  validation_confidence: number;
  factors_affecting_confidence: string[];
}

export interface ProcessingMetadata {
  total_processing_time: number;
  mode_processing_times: Record<string, number>;
  nodes_processed: number;
  relationships_traversed: number;
  cache_hit_rate: number;
}

export interface NavigationSuggestion {
  type: 'EXPLORATION' | 'SEARCH' | 'ANALYSIS';
  title: string;
  description: string;
  destination?: NavigationDestination;
  query?: string;
  confidence: number;
}

export interface MultiLayerGraphData {
  layers: Record<GraphLayer, {
    nodes: GraphNode[];
    relationships: GraphRelationship[];
  }>;
  cross_layer_relationships: GraphRelationship[];
  metadata: {
    total_nodes: number;
    total_relationships: number;
    layer_sizes: Record<GraphLayer, number>;
  };
}
```

## Testing Strategy

### Component Testing
```typescript
// __tests__/HybridQueryInterface.test.tsx
describe('HybridQueryInterface', () => {
  it('auto-analyzes query and suggests modes', async () => {
    const mockAnalysis = {
      intent: { primary_intent: 'QUALIFICATION_CHECK' },
      suggested_retrieval_modes: ['DECISION_PATH', 'MATRIX_INTERSECTION']
    };
    
    mockAnalyzeQueryIntent.mockResolvedValue(mockAnalysis);
    
    render(<HybridQueryInterface onQuerySubmit={jest.fn()} />);
    
    const queryInput = screen.getByPlaceholderText(/ask about mortgage/i);
    fireEvent.change(queryInput, { target: { value: 'Can a borrower with 620 FICO qualify?' } });
    
    await waitFor(() => {
      expect(screen.getByText('QUALIFICATION_CHECK')).toBeInTheDocument();
      expect(screen.getByText('Decision Logic')).toBeInTheDocument();
    });
  });
});
```

### Integration Testing
```typescript
// __tests__/HybridQueryFlow.test.tsx
describe('Hybrid Query Flow', () => {
  it('processes query through multiple modes and synthesizes result', async () => {
    // Test complete flow from query input to result display
  });
});
```

## Migration Strategy

### Phase 3.5 Implementation Steps

1. **Week 6.5**: Create hybrid query interface and result visualization components
2. **Week 6.75**: Implement multi-layer graph visualization and navigation assistant
3. **Week 6.9**: Add performance analytics dashboard and API integrations
4. **Week 6.95**: Integrate with existing components and test complete flow
5. **Week 7.0**: Deploy and validate with Phase 3 backend systems

### Backward Compatibility
- All existing query and chat functionality remains unchanged
- Hybrid features are additive and opt-in
- Existing graph visualization works alongside new multi-layer view
- No breaking changes to current user workflows

## Success Metrics

### User Experience Metrics
- Query complexity handling improvement > 80%
- Multi-modal query satisfaction > 4.5/5
- Navigation efficiency improvement > 60%
- Advanced feature adoption > 40%

### Technical Metrics
- Query processing visualization accuracy > 95%
- Graph layer performance with 10K+ nodes
- Real-time analytics update < 2 seconds
- Zero regression in existing functionality

## Next Steps
After Phase 3.5 completion:
1. Gather user feedback on advanced query capabilities
2. Optimize performance for large-scale graph visualization
3. Prepare for Phase 4 production features and AI enhancements
4. Plan advanced analytics and reporting capabilities
# Phase 2.5: Frontend Integration for Matrix Processing

## Overview
This phase implements sophisticated frontend components for matrix visualization, classification, and guidelines-matrix relationship management. Building on the existing graph visualization patterns, this frontend integration provides intuitive interfaces for complex matrix analysis while maintaining the established design system.

## Frontend Architecture Integration

### Leveraging Existing Patterns
- **Graph Visualization**: Extend existing Neo4j graph components for matrix relationships
- **Modal System**: Use CustomModal patterns for matrix analysis dialogs
- **Property Panels**: Enhance existing GraphPropertiesPanel for matrix metadata
- **Legend System**: Extend LegendsChip for matrix classification indicators
- **Responsive Design**: Maintain drawer layout compatibility

## Core Frontend Components

### 1. Matrix Classification Viewer

#### MatrixClassificationPanel Component (`frontend/src/components/Matrix/MatrixClassificationPanel.tsx`)

```typescript
interface MatrixClassificationPanelProps {
  matrixId: string;
  classification: MatrixClassification;
  onReclassify?: () => void;
}

const MatrixClassificationPanel: React.FC<MatrixClassificationPanelProps> = ({ 
  matrixId, 
  classification, 
  onReclassify 
}) => {
  const [expandedTypes, setExpandedTypes] = useState<string[]>([]);
  
  const handleTypeExpand = (type: string) => {
    setExpandedTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };
  
  return (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
        <Typography variant="h6">Matrix Classification</Typography>
        <Box display="flex" gap={1}>
          <Chip 
            label={`Complexity: ${(classification.complexity_score * 100).toFixed(0)}%`}
            color={classification.complexity_score > 0.7 ? 'error' : 
                   classification.complexity_score > 0.4 ? 'warning' : 'success'}
            size="small"
          />
          <Button size="small" onClick={onReclassify}>Reclassify</Button>
        </Box>
      </Box>
      
      {/* Primary Type Display */}
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2}>
            <MatrixTypeIcon type={classification.primary_type} size="large" />
            <Box>
              <Typography variant="h6">{classification.primary_type}</Typography>
              <Typography variant="body2" color="textSecondary">
                Primary Type (Confidence: {(classification.detected_types[classification.primary_type] * 100).toFixed(1)}%)
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
      
      {/* Multi-Type Detection */}
      {Object.keys(classification.detected_types).length > 1 && (
        <Box mb={2}>
          <Typography variant="subtitle1" mb={1}>Additional Detected Types</Typography>
          {Object.entries(classification.detected_types)
            .filter(([type]) => type !== classification.primary_type)
            .map(([type, confidence]) => (
              <Box key={type} mb={1}>
                <Box display="flex" justifyContent="between" alignItems="center">
                  <Box display="flex" alignItems="center" gap={1}>
                    <MatrixTypeIcon type={type} size="small" />
                    <Typography variant="body2">{type}</Typography>
                  </Box>
                  <Typography variant="caption">
                    {(confidence * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={confidence * 100} 
                  sx={{ height: 4, borderRadius: 2 }}
                />
              </Box>
            ))}
        </Box>
      )}
      
      {/* Processing Strategy */}
      <Alert severity="info" sx={{ mb: 2 }}>
        <AlertTitle>Processing Strategy</AlertTitle>
        <Typography variant="body2">
          {getProcessingStrategyDescription(classification.processing_strategy)}
        </Typography>
      </Alert>
      
      {/* Dimensions */}
      <Box>
        <Typography variant="subtitle1" mb={1}>Matrix Dimensions</Typography>
        <Box display="flex" flexWrap="wrap" gap={1}>
          {classification.dimensions.map(dimension => (
            <Chip 
              key={dimension}
              label={dimension}
              variant="outlined"
              size="small"
            />
          ))}
        </Box>
      </Box>
    </Box>
  );
};
```

#### MatrixVisualizationModal Component (`frontend/src/components/Matrix/MatrixVisualizationModal.tsx`)

```typescript
interface MatrixVisualizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  matrixData: ProcessedMatrix;
  classification: MatrixClassification;
  guidelineMappings: MatrixGuidelineMapping;
}

const MatrixVisualizationModal: React.FC<MatrixVisualizationModalProps> = ({ 
  isOpen, 
  onClose, 
  matrixData, 
  classification,
  guidelineMappings 
}) => {
  const [viewMode, setViewMode] = useState<'table' | 'heatmap' | 'relationships'>('table');
  const [selectedCell, setSelectedCell] = useState<MatrixCell | null>(null);
  
  return (
    <CustomModal isOpen={isOpen} onClose={onClose} size="fullscreen">
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box p={2} borderBottom={1} borderColor="divider">
          <Box display="flex" justifyContent="between" alignItems="center">
            <Typography variant="h5">Matrix Analysis</Typography>
            <Box display="flex" gap={1} alignItems="center">
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(_, value) => value && setViewMode(value)}
                size="small"
              >
                <ToggleButton value="table">Table View</ToggleButton>
                <ToggleButton value="heatmap">Heat Map</ToggleButton>
                <ToggleButton value="relationships">Relationships</ToggleButton>
              </ToggleButtonGroup>
              <IconButton onClick={onClose}>
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </Box>
        
        {/* Content */}
        <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Main Visualization Area */}
          <Box sx={{ flex: 1, p: 2, overflow: 'auto' }}>
            {viewMode === 'table' && (
              <MatrixTableView 
                matrixData={matrixData}
                onCellSelect={setSelectedCell}
                selectedCell={selectedCell}
                showMappings={true}
              />
            )}
            {viewMode === 'heatmap' && (
              <MatrixHeatmapView 
                matrixData={matrixData}
                classification={classification}
                onCellSelect={setSelectedCell}
              />
            )}
            {viewMode === 'relationships' && (
              <MatrixRelationshipGraph 
                matrixData={matrixData}
                guidelineMappings={guidelineMappings}
                onElementSelect={setSelectedCell}
              />
            )}
          </Box>
          
          {/* Side Panel */}
          <Box sx={{ width: 400, borderLeft: 1, borderColor: 'divider', p: 2 }}>
            <MatrixDetailsPanel 
              classification={classification}
              selectedCell={selectedCell}
              guidelineMappings={guidelineMappings}
            />
          </Box>
        </Box>
      </Box>
    </CustomModal>
  );
};
```

### 2. Matrix-Guidelines Relationship Viewer

#### MatrixGuidelineConnector Component (`frontend/src/components/Matrix/MatrixGuidelineConnector.tsx`)

```typescript
interface MatrixGuidelineConnectorProps {
  mappings: MatrixGuidelineMapping;
  onMappingSelect?: (mapping: CellMapping | DimensionMapping) => void;
  showConflicts?: boolean;
}

const MatrixGuidelineConnector: React.FC<MatrixGuidelineConnectorProps> = ({ 
  mappings, 
  onMappingSelect, 
  showConflicts = true 
}) => {
  const [selectedMappingType, setSelectedMappingType] = useState<'dimensions' | 'cells' | 'outcomes'>('dimensions');
  const [filterLevel, setFilterLevel] = useState<'all' | 'high' | 'medium'>('high');
  
  const getFilteredMappings = () => {
    const confidenceThreshold = filterLevel === 'high' ? 0.8 : filterLevel === 'medium' ? 0.6 : 0;
    
    switch (selectedMappingType) {
      case 'dimensions':
        return mappings.dimension_mappings.filter(m => m.confidence >= confidenceThreshold);
      case 'cells':
        return mappings.cell_mappings.filter(m => m.confidence >= confidenceThreshold);
      case 'outcomes':
        return mappings.outcome_mappings.filter(m => m.confidence >= confidenceThreshold);
      default:
        return [];
    }
  };
  
  return (
    <Box>
      {/* Controls */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
        <ToggleButtonGroup
          value={selectedMappingType}
          exclusive
          onChange={(_, value) => value && setSelectedMappingType(value)}
          size="small"
        >
          <ToggleButton value="dimensions">Dimensions</ToggleButton>
          <ToggleButton value="cells">Cells</ToggleButton>
          <ToggleButton value="outcomes">Outcomes</ToggleButton>
        </ToggleButtonGroup>
        
        <FormControl size="small">
          <Select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value as any)}
          >
            <MenuItem value="all">All Confidence</MenuItem>
            <MenuItem value="medium">Medium+ (60%)</MenuItem>
            <MenuItem value="high">High (80%)</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {/* Conflicts Alert */}
      {showConflicts && mappings.conflicts.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <AlertTitle>Detected Conflicts ({mappings.conflicts.length})</AlertTitle>
          <Typography variant="body2">
            Found inconsistencies between matrix and guidelines. 
            <Button size="small" sx={{ ml: 1 }}>View Details</Button>
          </Typography>
        </Alert>
      )}
      
      {/* Mappings List */}
      <List>
        {getFilteredMappings().map((mapping, index) => (
          <ListItem 
            key={index}
            button
            onClick={() => onMappingSelect?.(mapping)}
            sx={{ 
              border: 1, 
              borderColor: 'divider', 
              borderRadius: 1, 
              mb: 1,
              '&:hover': { borderColor: 'primary.main' }
            }}
          >
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: getConfidenceColor(mapping.confidence) }}>
                {(mapping.confidence * 100).toFixed(0)}%
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={
                <Box display="flex" alignItems="center" gap={1}>
                  <MappingTypeIcon type={mapping.relationship_type} />
                  <Typography variant="body1">
                    {getMappingTitle(mapping)}
                  </Typography>
                </Box>
              }
              secondary={
                <Box>
                  <Typography variant="caption" display="block">
                    Matrix: {getMappingSourceDescription(mapping)}
                  </Typography>
                  <Typography variant="caption" display="block">
                    Guidelines: {getMappingTargetDescription(mapping)}
                  </Typography>
                </Box>
              }
            />
            <ListItemSecondaryAction>
              <Chip 
                label={mapping.relationship_type}
                size="small"
                color={getRelationshipColor(mapping.relationship_type)}
              />
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>
      
      {getFilteredMappings().length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography variant="body2" color="textSecondary">
            No mappings found for the selected criteria
          </Typography>
        </Box>
      )}
    </Box>
  );
};
```

### 3. Enhanced Matrix Table View

#### MatrixTableView Component (`frontend/src/components/Matrix/MatrixTableView.tsx`)

```typescript
interface MatrixTableViewProps {
  matrixData: ProcessedMatrix;
  onCellSelect?: (cell: MatrixCell) => void;
  selectedCell?: MatrixCell | null;
  showMappings?: boolean;
}

const MatrixTableView: React.FC<MatrixTableViewProps> = ({ 
  matrixData, 
  onCellSelect, 
  selectedCell,
  showMappings = false 
}) => {
  const [hoveredCell, setHoveredCell] = useState<MatrixCell | null>(null);
  
  const getCellStyle = (cell: MatrixCell): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      position: 'relative',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      border: '1px solid #e0e0e0',
      padding: '8px',
      textAlign: 'center',
      minHeight: '60px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    };
    
    if (selectedCell?.cell_id === cell.cell_id) {
      return {
        ...baseStyle,
        backgroundColor: '#1976d2',
        color: 'white',
        boxShadow: '0 0 8px rgba(25, 118, 210, 0.5)'
      };
    }
    
    if (hoveredCell?.cell_id === cell.cell_id) {
      return {
        ...baseStyle,
        backgroundColor: '#f5f5f5',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      };
    }
    
    // Color based on cell type
    const typeColors = {
      'DECISION': '#e3f2fd',
      'THRESHOLD': '#f3e5f5',
      'RATE': '#e8f5e8',
      'RULE': '#fff3e0'
    };
    
    return {
      ...baseStyle,
      backgroundColor: typeColors[cell.cell_type] || '#ffffff'
    };
  };
  
  const getCellContent = (cell: MatrixCell) => {
    return (
      <Box sx={{ width: '100%' }}>
        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
          {cell.value}
        </Typography>
        
        {/* Mapping Indicators */}
        {showMappings && cell.guideline_mappings && (
          <Box display="flex" justifyContent="center" mt={0.5}>
            {cell.guideline_mappings.map((mapping, idx) => (
              <Tooltip 
                key={idx} 
                title={`Mapped to: ${mapping.guideline_section}`}
                arrow
              >
                <Box
                  sx={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    backgroundColor: getConfidenceColor(mapping.confidence),
                    mx: 0.25
                  }}
                />
              </Tooltip>
            ))}
          </Box>
        )}
        
        {/* Range Indicators */}
        {cell.ranges && cell.ranges.length > 0 && (
          <Box mt={0.5}>
            <Chip 
              label="Range"
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.6rem', height: '16px' }}
            />
          </Box>
        )}
      </Box>
    );
  };
  
  if (!matrixData.table_data) {
    return (
      <Box textAlign="center" py={4}>
        <Typography color="textSecondary">
          Matrix table data not available
        </Typography>
      </Box>
    );
  }
  
  return (
    <Box>
      {/* Matrix Metadata */}
      <Box mb={2}>
        <Typography variant="h6">{matrixData.matrix_name}</Typography>
        <Box display="flex" gap={1} mt={1}>
          <Chip label={`${matrixData.dimensions.length} Dimensions`} size="small" />
          <Chip label={`${matrixData.cells.length} Cells`} size="small" />
          <Chip label={matrixData.primary_type} color="primary" size="small" />
        </Box>
      </Box>
      
      {/* Table */}
      <TableContainer component={Paper} variant="outlined">
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>
                {/* Row dimension label */}
              </TableCell>
              {matrixData.table_data.columns.map((col, index) => (
                <TableCell 
                  key={index}
                  align="center"
                  sx={{ 
                    fontWeight: 'bold', 
                    backgroundColor: '#f5f5f5',
                    minWidth: '120px'
                  }}
                >
                  {col}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {matrixData.table_data.rows.map((row, rowIndex) => (
              <TableRow key={rowIndex}>
                <TableCell 
                  sx={{ 
                    fontWeight: 'bold', 
                    backgroundColor: '#f9f9f9',
                    position: 'sticky',
                    left: 0,
                    zIndex: 1
                  }}
                >
                  {row.label}
                </TableCell>
                {row.cells.map((cell, cellIndex) => (
                  <TableCell 
                    key={cellIndex}
                    sx={getCellStyle(cell)}
                    onClick={() => onCellSelect?.(cell)}
                    onMouseEnter={() => setHoveredCell(cell)}
                    onMouseLeave={() => setHoveredCell(null)}
                  >
                    {getCellContent(cell)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Legend */}
      <Box mt={2}>
        <Typography variant="caption" color="textSecondary" mb={1} display="block">
          Cell Types:
        </Typography>
        <Box display="flex" gap={1} flexWrap="wrap">
          {Object.entries({
            'DECISION': '#e3f2fd',
            'THRESHOLD': '#f3e5f5', 
            'RATE': '#e8f5e8',
            'RULE': '#fff3e0'
          }).map(([type, color]) => (
            <Box key={type} display="flex" alignItems="center" gap={0.5}>
              <Box 
                sx={{ 
                  width: 12, 
                  height: 12, 
                  backgroundColor: color,
                  border: '1px solid #ccc'
                }} 
              />
              <Typography variant="caption">{type}</Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
};
```

### 4. Matrix Range Visualization

#### RangeVisualizationPanel Component (`frontend/src/components/Matrix/RangeVisualizationPanel.tsx`)

```typescript
interface RangeVisualizationPanelProps {
  ranges: RangeStructure;
  matrixData: ProcessedMatrix;
  onRangeSelect?: (range: Range) => void;
}

const RangeVisualizationPanel: React.FC<RangeVisualizationPanelProps> = ({ 
  ranges, 
  matrixData, 
  onRangeSelect 
}) => {
  const [selectedDimension, setSelectedDimension] = useState<string>('');
  const [viewMode, setViewMode] = useState<'list' | 'chart'>('list');
  
  useEffect(() => {
    if (!selectedDimension && Object.keys(ranges.dimensions).length > 0) {
      setSelectedDimension(Object.keys(ranges.dimensions)[0]);
    }
  }, [ranges.dimensions, selectedDimension]);
  
  const dimensionRanges = selectedDimension ? ranges.dimensions[selectedDimension] : [];
  
  return (
    <Box>
      {/* Controls */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Dimension</InputLabel>
          <Select
            value={selectedDimension}
            onChange={(e) => setSelectedDimension(e.target.value)}
            label="Dimension"
          >
            {Object.keys(ranges.dimensions).map(dim => (
              <MenuItem key={dim} value={dim}>
                {dim} ({ranges.dimensions[dim].length} ranges)
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(_, value) => value && setViewMode(value)}
          size="small"
        >
          <ToggleButton value="list">List</ToggleButton>
          <ToggleButton value="chart">Chart</ToggleButton>
        </ToggleButtonGroup>
      </Box>
      
      {/* Range Coverage Summary */}
      {selectedDimension && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            {selectedDimension}: {dimensionRanges.length} ranges covering{' '}
            {calculateCoveragePercentage(dimensionRanges).toFixed(1)}% of expected domain
          </Typography>
        </Alert>
      )}
      
      {/* Content */}
      {viewMode === 'list' ? (
        <RangeListView 
          ranges={dimensionRanges}
          dimension={selectedDimension}
          onRangeSelect={onRangeSelect}
        />
      ) : (
        <RangeChartView 
          ranges={dimensionRanges}
          dimension={selectedDimension}
          onRangeSelect={onRangeSelect}
        />
      )}
      
      {/* Coverage Gaps */}
      {ranges.gaps && ranges.gaps[selectedDimension] && (
        <Box mt={2}>
          <Alert severity="warning">
            <AlertTitle>Coverage Gaps Detected</AlertTitle>
            <Typography variant="body2">
              {ranges.gaps[selectedDimension].length} gaps found in {selectedDimension} coverage
            </Typography>
            <Box mt={1}>
              {ranges.gaps[selectedDimension].map((gap, index) => (
                <Chip 
                  key={index}
                  label={`${gap.start} - ${gap.end}`}
                  size="small"
                  color="warning"
                  variant="outlined"
                  sx={{ mr: 0.5, mb: 0.5 }}
                />
              ))}
            </Box>
          </Alert>
        </Box>
      )}
    </Box>
  );
};
```

## Graph Integration Components

### 5. Matrix-Guidelines Relationship Graph

#### MatrixRelationshipGraph Component (`frontend/src/components/Matrix/MatrixRelationshipGraph.tsx`)

```typescript
interface MatrixRelationshipGraphProps {
  matrixData: ProcessedMatrix;
  guidelineMappings: MatrixGuidelineMapping;
  onElementSelect?: (element: any) => void;
}

const MatrixRelationshipGraph: React.FC<MatrixRelationshipGraphProps> = ({ 
  matrixData, 
  guidelineMappings, 
  onElementSelect 
}) => {
  const graphRef = useRef<any>(null);
  const [graphData, setGraphData] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  
  useEffect(() => {
    // Transform matrix and guideline data into graph format
    const nodes = [
      // Matrix node
      {
        id: matrixData.matrix_id,
        label: matrixData.matrix_name,
        type: 'matrix',
        properties: {
          primary_type: matrixData.primary_type,
          complexity: matrixData.complexity_score,
          dimensions: matrixData.dimensions.length
        }
      },
      // Matrix cells as nodes
      ...matrixData.cells.map(cell => ({
        id: cell.cell_id,
        label: cell.value,
        type: 'matrix_cell',
        properties: {
          cell_type: cell.cell_type,
          coordinates: cell.coordinates
        }
      })),
      // Guideline nodes from mappings
      ...extractGuidelineNodes(guidelineMappings)
    ];
    
    const relationships = [
      // Matrix contains cells
      ...matrixData.cells.map(cell => ({
        id: `contains_${cell.cell_id}`,
        startNodeId: matrixData.matrix_id,
        endNodeId: cell.cell_id,
        type: 'CONTAINS_CELL'
      })),
      // Cell to guideline mappings
      ...extractMappingRelationships(guidelineMappings)
    ];
    
    setGraphData({ nodes, relationships });
  }, [matrixData, guidelineMappings]);
  
  const handleNodeClick = (node: any) => {
    setSelectedNode(node.id);
    onElementSelect?.(node);
  };
  
  if (!graphData) {
    return <CircularProgress />;
  }
  
  return (
    <Box sx={{ height: '100%', width: '100%', position: 'relative' }}>
      {/* Graph Controls */}
      <Box 
        sx={{ 
          position: 'absolute', 
          top: 10, 
          right: 10, 
          zIndex: 1000,
          display: 'flex',
          gap: 1
        }}
      >
        <Button size="small" onClick={() => graphRef.current?.fitToScreen()}>
          Fit to Screen
        </Button>
        <Button size="small" onClick={() => graphRef.current?.centerGraph()}>
          Center
        </Button>
      </Box>
      
      {/* Neo4j Graph Visualization */}
      <GraphVisualization
        ref={graphRef}
        nodes={graphData.nodes}
        relationships={graphData.relationships}
        onNodeClick={handleNodeClick}
        selectedNodeId={selectedNode}
        nodeColorScheme={{
          matrix: '#1976d2',
          matrix_cell: '#42a5f5',
          guideline_node: '#66bb6a',
          guideline_chunk: '#81c784'
        }}
        relationshipColorScheme={{
          CONTAINS_CELL: '#757575',
          REFERENCES: '#ff9800',
          ELABORATED_BY: '#9c27b0',
          CONFLICTS_WITH: '#f44336'
        }}
        layout="force"
        interactive={true}
      />
      
      {/* Legend */}
      <Box 
        sx={{ 
          position: 'absolute', 
          bottom: 10, 
          left: 10,
          backgroundColor: 'rgba(255,255,255,0.9)',
          p: 1,
          borderRadius: 1,
          border: '1px solid #ccc'
        }}
      >
        <Typography variant="caption" fontWeight="bold" mb={1} display="block">
          Legend
        </Typography>
        <Box display="flex" flexDirection="column" gap={0.5}>
          {[
            { type: 'Matrix', color: '#1976d2' },
            { type: 'Matrix Cell', color: '#42a5f5' },
            { type: 'Guideline Node', color: '#66bb6a' },
            { type: 'Guideline Chunk', color: '#81c784' }
          ].map(({ type, color }) => (
            <Box key={type} display="flex" alignItems="center" gap={0.5}>
              <Box 
                sx={{ 
                  width: 12, 
                  height: 12, 
                  backgroundColor: color,
                  borderRadius: '50%'
                }} 
              />
              <Typography variant="caption">{type}</Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
};
```

## API Integration Services

### Matrix Analysis Service (`frontend/src/services/MatrixAPI.ts`)

```typescript
export interface MatrixClassification {
  primary_type: string;
  detected_types: Record<string, number>;
  weights: Record<string, number>;
  processing_strategy: string;
  complexity_score: number;
  dimensions: string[];
  confidence_threshold: number;
  metadata: Record<string, any>;
}

export interface ProcessedMatrix {
  matrix_id: string;
  document_id: string;
  matrix_name: string;
  primary_type: string;
  detected_types: string[];
  complexity_score: number;
  dimensions: MatrixDimension[];
  cells: MatrixCell[];
  table_data?: MatrixTableData;
  ranges?: RangeStructure;
}

export const getMatrixClassification = async (documentId: string): Promise<ServerResponse> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const params = new URLSearchParams();
  params.append('document_id', documentId);
  appendUserCredentialsToParams(params, userCredentials);
  
  const response = await fetch(`${apiUrl}/matrix/classification?${params}`, {
    method: 'GET',
  });
  
  return response.json();
};

export const getMatrixGuidelineMappings = async (
  matrixId: string, 
  guidelinesId: string
): Promise<ServerResponse> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const formData = new FormData();
  formData.append('matrix_id', matrixId);
  formData.append('guidelines_id', guidelinesId);
  appendUserCredentials(formData, userCredentials);
  
  const response = await fetch(`${apiUrl}/matrix/guideline-mappings`, {
    method: 'POST',
    body: formData,
  });
  
  return response.json();
};

export const reclassifyMatrix = async (
  matrixId: string, 
  options: ReclassificationOptions
): Promise<ServerResponse> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const formData = new FormData();
  formData.append('matrix_id', matrixId);
  formData.append('options', JSON.stringify(options));
  appendUserCredentials(formData, userCredentials);
  
  const response = await fetch(`${apiUrl}/matrix/reclassify`, {
    method: 'POST',
    body: formData,
  });
  
  return response.json();
};

export const validateMatrixRanges = async (matrixId: string): Promise<ServerResponse> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const params = new URLSearchParams();
  params.append('matrix_id', matrixId);
  appendUserCredentialsToParams(params, userCredentials);
  
  const response = await fetch(`${apiUrl}/matrix/validate-ranges?${params}`, {
    method: 'GET',
  });
  
  return response.json();
};
```

## Integration with Existing Components

### 1. Enhanced FileTable Integration

```typescript
// In frontend/src/components/FileTable.tsx
const MatrixAnalysisButton: React.FC<{ file: UserFile }> = ({ file }) => {
  const [showMatrixModal, setShowMatrixModal] = useState(false);
  const [matrixData, setMatrixData] = useState<ProcessedMatrix | null>(null);
  
  const handleAnalyzeMatrix = async () => {
    const response = await getMatrixClassification(file.id);
    if (response.status === 'success') {
      setMatrixData(response.data);
      setShowMatrixModal(true);
    }
  };
  
  if (file.type !== 'matrix') return null;
  
  return (
    <>
      <IconButtonToolTip
        title="Analyze Matrix"
        onClick={handleAnalyzeMatrix}
        size="small"
      >
        <GridViewIcon />
      </IconButtonToolTip>
      
      {matrixData && (
        <MatrixVisualizationModal
          isOpen={showMatrixModal}
          onClose={() => setShowMatrixModal(false)}
          matrixData={matrixData}
          classification={matrixData.classification}
          guidelineMappings={matrixData.guideline_mappings}
        />
      )}
    </>
  );
};
```

### 2. Graph Enhancement for Matrix Relationships

```typescript
// In frontend/src/components/Graph/GraphViewButton.tsx
const MatrixRelationshipToggle: React.FC = () => {
  const [showMatrixRelationships, setShowMatrixRelationships] = useState(true);
  
  return (
    <FormControlLabel
      control={
        <Checkbox
          checked={showMatrixRelationships}
          onChange={(e) => setShowMatrixRelationships(e.target.checked)}
          size="small"
        />
      }
      label="Matrix-Guidelines Relationships"
    />
  );
};
```

## State Management Integration

### Matrix Context Provider (`frontend/src/context/MatrixContext.tsx`)

```typescript
interface MatrixContextType {
  matrices: ProcessedMatrix[];
  selectedMatrix: ProcessedMatrix | null;
  isAnalyzing: boolean;
  error: string | null;
  analyzeMatrix: (documentId: string) => Promise<ProcessedMatrix>;
  selectMatrix: (matrixId: string) => void;
  getMappings: (matrixId: string, guidelinesId: string) => Promise<MatrixGuidelineMapping>;
  reclassify: (matrixId: string, options: ReclassificationOptions) => Promise<void>;
}

export const MatrixContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [matrices, setMatrices] = useState<ProcessedMatrix[]>([]);
  const [selectedMatrix, setSelectedMatrix] = useState<ProcessedMatrix | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const analyzeMatrix = async (documentId: string): Promise<ProcessedMatrix> => {
    setIsAnalyzing(true);
    setError(null);
    
    try {
      const response = await getMatrixClassification(documentId);
      if (response.status === 'success') {
        const matrixData = response.data;
        setMatrices(prev => [...prev.filter(m => m.document_id !== documentId), matrixData]);
        return matrixData;
      } else {
        throw new Error(response.error || 'Analysis failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      throw err;
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  const selectMatrix = (matrixId: string) => {
    const matrix = matrices.find(m => m.matrix_id === matrixId);
    setSelectedMatrix(matrix || null);
  };
  
  const getMappings = async (matrixId: string, guidelinesId: string): Promise<MatrixGuidelineMapping> => {
    const response = await getMatrixGuidelineMappings(matrixId, guidelinesId);
    if (response.status === 'success') {
      return response.data;
    }
    throw new Error(response.error || 'Failed to get mappings');
  };
  
  const reclassify = async (matrixId: string, options: ReclassificationOptions) => {
    const response = await reclassifyMatrix(matrixId, options);
    if (response.status === 'success') {
      // Update the matrix in state
      const updatedMatrix = response.data;
      setMatrices(prev => prev.map(m => m.matrix_id === matrixId ? updatedMatrix : m));
      if (selectedMatrix?.matrix_id === matrixId) {
        setSelectedMatrix(updatedMatrix);
      }
    } else {
      throw new Error(response.error || 'Reclassification failed');
    }
  };
  
  const value: MatrixContextType = {
    matrices,
    selectedMatrix,
    isAnalyzing,
    error,
    analyzeMatrix,
    selectMatrix,
    getMappings,
    reclassify
  };
  
  return (
    <MatrixContext.Provider value={value}>
      {children}
    </MatrixContext.Provider>
  );
};
```

## Type System Extensions

### Matrix Types (`frontend/src/types.ts`)

```typescript
// Add to existing types.ts file

export interface MatrixDimension {
  name: string;
  type: 'FICO_SCORE' | 'LTV_RATIO' | 'DTI_RATIO' | 'PROPERTY_TYPE' | 'LOAN_AMOUNT';
  ranges: Range[];
  axis: 'row' | 'column' | 'filter';
}

export interface MatrixCell {
  cell_id: string;
  matrix_id: string;
  row_index: string | number;
  column_index: string | number;
  value: any;
  cell_type: 'DECISION' | 'THRESHOLD' | 'RATE' | 'RULE';
  coordinates: Record<string, any>;
  ranges?: Range[];
  guideline_mappings?: CellMapping[];
}

export interface Range {
  range_id: string;
  dimension: string;
  min_value: number;
  max_value: number;
  inclusive_min: boolean;
  inclusive_max: boolean;
  format?: 'percentage' | 'currency' | 'number';
}

export interface MatrixGuidelineMapping {
  dimension_mappings: DimensionMapping[];
  cell_mappings: CellMapping[];
  outcome_mappings: OutcomeMapping[];
  conflicts: Conflict[];
}

export interface CellMapping {
  cell: MatrixCell;
  guideline_chunk: NavigationNode;
  relationship_type: 'REFERENCES' | 'ELABORATED_BY' | 'CONTRADICTS';
  confidence: number;
  context: Record<string, any>;
}

export interface Conflict {
  conflict_type: 'THRESHOLD_MISMATCH' | 'MISSING_COVERAGE' | 'LOGICAL_CONFLICT';
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  matrix_element: MatrixCell | MatrixDimension;
  guideline_element: NavigationNode | Entity;
  description: string;
  resolution_suggestions: string[];
}
```

## Testing Strategy

### Component Testing
```typescript
// __tests__/MatrixClassificationPanel.test.tsx
describe('MatrixClassificationPanel', () => {
  it('displays primary classification with confidence', () => {
    const mockClassification = {
      primary_type: 'MULTI_DIMENSIONAL_DECISION',
      detected_types: { 'MULTI_DIMENSIONAL_DECISION': 0.92 },
      complexity_score: 0.75
    };
    
    render(<MatrixClassificationPanel classification={mockClassification} />);
    
    expect(screen.getByText('MULTI_DIMENSIONAL_DECISION')).toBeInTheDocument();
    expect(screen.getByText('92.0%')).toBeInTheDocument();
  });
});
```

### Integration Testing
```typescript
// __tests__/MatrixGuidelineFlow.test.tsx
describe('Matrix-Guideline Integration Flow', () => {
  it('maps matrix cells to guideline sections correctly', async () => {
    // Test complete flow from matrix analysis to guideline mapping
  });
});
```

## Migration Strategy

### Phase 2.5 Implementation Steps

1. **Week 4.5**: Create matrix classification and visualization components
2. **Week 4.75**: Implement matrix-guideline relationship viewer
3. **Week 4.9**: Integrate with existing graph and table components
4. **Week 4.95**: Add API services and context providers
5. **Week 5.0**: Deploy and validate with Phase 2 backend APIs

### Backward Compatibility
- Matrix visualization is additive to existing file processing
- No changes to existing graph or table functionality
- Matrix analysis is opt-in through file type detection
- Existing workflows remain unchanged

## Success Metrics

### User Experience Metrics
- Matrix classification accuracy perception > 90%
- Guideline mapping utility rating > 4.0/5
- Navigation between matrix and guidelines < 3 clicks
- Conflict identification usefulness > 85%

### Technical Metrics
- Matrix visualization load time < 2 seconds
- Relationship graph performance for 100+ nodes
- Zero regression in existing components
- API response handling reliability > 99%

## Next Steps
After Phase 2.5 completion:
1. Gather user feedback on matrix visualization effectiveness
2. Optimize performance for large matrices (1000+ cells)
3. Prepare for Phase 3.5 enhanced knowledge graph integration
4. Plan advanced analytics and reporting features
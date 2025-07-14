# Phase 1.5: Frontend Integration for Document Packages

## Overview
This phase implements frontend components to support the document package system introduced in Phase 1, maintaining seamless integration with the existing UI patterns and design system. The frontend will enable users to create, manage, and apply document packages while preserving the current user experience.

## Frontend Architecture Integration

### Maintaining Current UI Patterns
The implementation leverages existing components and patterns:
- **Neo4j NDL Components**: Continue using established design system
- **Context-based State Management**: Extend existing context providers
- **Modal/Dialog System**: Use existing `CustomModal` HOC pattern
- **API Service Pattern**: Follow established FormData API patterns
- **Responsive Design**: Maintain drawer/layout system for different screen sizes

## Core Frontend Components

### 1. Package Management Interface

#### PackageManager Component (`frontend/src/components/PackageManager/`)

```typescript
interface PackageManagerProps {
  isOpen: boolean;
  onClose: () => void;
  onPackageSelected: (packageId: string) => void;
}

const PackageManager: React.FC<PackageManagerProps> = ({ isOpen, onClose, onPackageSelected }) => {
  const { userCredentials } = useContext(UserCredentialsContext);
  const [packages, setPackages] = useState<DocumentPackage[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  
  return (
    <CustomModal isOpen={isOpen} onClose={onClose} size="large">
      <Box p={3}>
        <Typography variant="h6">Document Package Manager</Typography>
        
        {/* Category Filter */}
        <Box mb={2}>
          <MUISelect
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            displayEmpty
            fullWidth
          >
            <MenuItem value="">All Categories</MenuItem>
            <MenuItem value="NQM">Non-QM</MenuItem>
            <MenuItem value="RTL">Rental</MenuItem>
            <MenuItem value="SBC">Small Balance Commercial</MenuItem>
            <MenuItem value="CONV">Conventional</MenuItem>
          </MUISelect>
        </Box>
        
        {/* Package List */}
        <PackageList 
          packages={packages}
          onSelect={onPackageSelected}
          onEdit={handleEditPackage}
          onClone={handleClonePackage}
        />
        
        {/* Action Buttons */}
        <Box display="flex" gap={2} mt={3}>
          <Button variant="contained" onClick={handleCreateNew}>
            Create New Package
          </Button>
          <Button variant="outlined" onClick={handleImportTemplate}>
            Import Template
          </Button>
        </Box>
      </Box>
    </CustomModal>
  );
};
```

#### PackageCreator Component (`frontend/src/components/PackageManager/PackageCreator.tsx`)

```typescript
interface PackageCreatorProps {
  isOpen: boolean;
  onClose: () => void;
  templateType?: string;
  onPackageCreated: (packageData: DocumentPackage) => void;
}

const PackageCreator: React.FC<PackageCreatorProps> = ({ 
  isOpen, 
  onClose, 
  templateType, 
  onPackageCreated 
}) => {
  const [formData, setFormData] = useState<PackageFormData>({
    package_name: '',
    category: templateType || '',
    template: '',
    customizations: {}
  });
  
  const handleSubmit = async () => {
    try {
      const response = await createDocumentPackage(formData);
      if (response.status === 'success') {
        onPackageCreated(response.data);
        onClose();
        showSuccessToast('Package created successfully');
      }
    } catch (error) {
      showErrorToast('Failed to create package');
    }
  };
  
  return (
    <CustomModal isOpen={isOpen} onClose={onClose}>
      <Box component="form" onSubmit={handleSubmit} p={3}>
        <Typography variant="h6" mb={2}>Create New Document Package</Typography>
        
        {/* Package Name */}
        <TextField
          fullWidth
          label="Package Name"
          value={formData.package_name}
          onChange={(e) => setFormData({...formData, package_name: e.target.value})}
          margin="normal"
          required
        />
        
        {/* Category Selection */}
        <FormControl fullWidth margin="normal">
          <InputLabel>Category</InputLabel>
          <MUISelect
            value={formData.category}
            onChange={(e) => setFormData({...formData, category: e.target.value})}
            required
          >
            <MenuItem value="NQM">Non-QM</MenuItem>
            <MenuItem value="RTL">Rental</MenuItem>
            <MenuItem value="SBC">Small Balance Commercial</MenuItem>
            <MenuItem value="CONV">Conventional</MenuItem>
          </MUISelect>
        </FormControl>
        
        {/* Template Selection */}
        <TemplateSelector 
          category={formData.category}
          onTemplateSelected={(template) => setFormData({...formData, template})}
        />
        
        {/* Customization Options */}
        <CustomizationPanel 
          template={formData.template}
          customizations={formData.customizations}
          onChange={(customizations) => setFormData({...formData, customizations})}
        />
        
        <Box display="flex" gap={2} mt={3} justifyContent="flex-end">
          <Button variant="outlined" onClick={onClose}>Cancel</Button>
          <Button variant="contained" type="submit">Create Package</Button>
        </Box>
      </Box>
    </CustomModal>
  );
};
```

### 2. Enhanced Upload Flow Integration

#### Enhanced DropZone Component (`frontend/src/components/DataSources/Local/EnhancedDropZone.tsx`)

```typescript
interface EnhancedDropZoneProps extends DropZoneProps {
  packageId?: string;
  enablePackageSelection?: boolean;
}

const EnhancedDropZone: React.FC<EnhancedDropZoneProps> = ({ 
  packageId, 
  enablePackageSelection = true,
  ...props 
}) => {
  const [selectedPackage, setSelectedPackage] = useState<string | null>(packageId || null);
  const [showPackageManager, setShowPackageManager] = useState(false);
  const [uploadMode, setUploadMode] = useState<'standard' | 'package'>('standard');
  
  const handleFilesDropped = (files: File[]) => {
    if (uploadMode === 'package' && selectedPackage) {
      // Use package-based upload
      handlePackageUpload(files, selectedPackage);
    } else {
      // Use standard upload
      props.onFilesDropped?.(files);
    }
  };
  
  return (
    <Box>
      {/* Upload Mode Toggle */}
      <Box mb={2}>
        <ToggleButtonGroup
          value={uploadMode}
          exclusive
          onChange={(_, value) => value && setUploadMode(value)}
          size="small"
        >
          <ToggleButton value="standard">Standard Upload</ToggleButton>
          <ToggleButton value="package">Package-Based Upload</ToggleButton>
        </ToggleButtonGroup>
      </Box>
      
      {/* Package Selection (when in package mode) */}
      {uploadMode === 'package' && (
        <Box mb={2}>
          <Box display="flex" gap={2} alignItems="center">
            <Chip 
              label={selectedPackage ? `Package: ${selectedPackage}` : 'No Package Selected'}
              color={selectedPackage ? 'primary' : 'default'}
              variant={selectedPackage ? 'filled' : 'outlined'}
            />
            <Button 
              size="small" 
              onClick={() => setShowPackageManager(true)}
            >
              {selectedPackage ? 'Change' : 'Select'} Package
            </Button>
          </Box>
        </Box>
      )}
      
      {/* Enhanced DropZone with package context */}
      <DropZone 
        {...props}
        onFilesDropped={handleFilesDropped}
        additionalInfo={selectedPackage ? 
          `Files will be processed using the ${selectedPackage} package structure` : 
          undefined
        }
      />
      
      {/* Package Manager Modal */}
      <PackageManager 
        isOpen={showPackageManager}
        onClose={() => setShowPackageManager(false)}
        onPackageSelected={(id) => {
          setSelectedPackage(id);
          setShowPackageManager(false);
        }}
      />
    </Box>
  );
};
```

### 3. Package-Aware File Processing Display

#### PackageProcessingStatus Component (`frontend/src/components/FileTable/PackageProcessingStatus.tsx`)

```typescript
interface PackageProcessingStatusProps {
  file: UserFile;
  packageInfo?: DocumentPackage;
}

const PackageProcessingStatus: React.FC<PackageProcessingStatusProps> = ({ 
  file, 
  packageInfo 
}) => {
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);
  const [currentStep, setCurrentStep] = useState<string>('');
  
  useEffect(() => {
    if (packageInfo && file.status === 'Processing') {
      // Subscribe to package-specific processing updates
      const unsubscribe = subscribeToPackageProcessing(file.id, packageInfo.package_id, (steps) => {
        setProcessingSteps(steps);
        setCurrentStep(steps.find(s => s.status === 'in_progress')?.name || '');
      });
      
      return unsubscribe;
    }
  }, [file.id, packageInfo, file.status]);
  
  if (!packageInfo) {
    // Render standard processing status
    return <StandardProcessingStatus file={file} />;
  }
  
  return (
    <Box>
      <Box display="flex" alignItems="center" gap={1} mb={1}>
        <Chip size="small" label={packageInfo.category} color="primary" />
        <Typography variant="caption" color="textSecondary">
          Package: {packageInfo.package_name}
        </Typography>
      </Box>
      
      {/* Package-specific processing steps */}
      <List dense>
        {processingSteps.map((step, index) => (
          <ListItem key={index} sx={{ py: 0 }}>
            <ListItemIcon sx={{ minWidth: 32 }}>
              {step.status === 'completed' && <CheckCircleIcon color="success" fontSize="small" />}
              {step.status === 'in_progress' && <CircularProgress size={16} />}
              {step.status === 'pending' && <RadioButtonUncheckedIcon color="disabled" fontSize="small" />}
            </ListItemIcon>
            <ListItemText 
              primary={step.name}
              secondary={step.description}
              primaryTypographyProps={{ variant: 'caption' }}
              secondaryTypographyProps={{ variant: 'caption' }}
            />
          </ListItem>
        ))}
      </List>
      
      {/* Hierarchical Processing Progress */}
      {currentStep === 'hierarchical_chunking' && (
        <HierarchicalChunkingProgress fileId={file.id} />
      )}
      
      {/* Navigation Extraction Progress */}
      {currentStep === 'navigation_extraction' && (
        <NavigationExtractionProgress fileId={file.id} />
      )}
    </Box>
  );
};
```

### 4. Navigation Structure Viewer

#### NavigationTreeViewer Component (`frontend/src/components/Navigation/NavigationTreeViewer.tsx`)

```typescript
interface NavigationTreeViewerProps {
  fileId: string;
  navigationData: NavigationTree;
  onNodeSelect?: (nodeId: string) => void;
}

const NavigationTreeViewer: React.FC<NavigationTreeViewerProps> = ({ 
  fileId, 
  navigationData, 
  onNodeSelect 
}) => {
  const [expandedNodes, setExpandedNodes] = useState<string[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  
  const handleNodeToggle = (nodeIds: string[]) => {
    setExpandedNodes(nodeIds);
  };
  
  const handleNodeSelect = (nodeId: string) => {
    setSelectedNode(nodeId);
    onNodeSelect?.(nodeId);
  };
  
  const renderTreeNode = (node: NavigationNode): React.ReactNode => {
    return (
      <TreeItem
        key={node.enhanced_node_id}
        nodeId={node.enhanced_node_id}
        label={
          <Box display="flex" alignItems="center" gap={1}>
            <NavigationNodeIcon nodeType={node.node_type} />
            <Typography variant="body2">{node.title}</Typography>
            {node.requires_complete_tree && (
              <Chip size="small" label="Decision Tree" color="warning" />
            )}
          </Box>
        }
      >
        {node.children.map(child => renderTreeNode(child))}
      </TreeItem>
    );
  };
  
  return (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
        <Typography variant="h6">Document Navigation</Typography>
        <Box display="flex" gap={1}>
          <Button size="small" onClick={() => setExpandedNodes([])}>
            Collapse All
          </Button>
          <Button size="small" onClick={() => setExpandedNodes(getAllNodeIds(navigationData))}>
            Expand All
          </Button>
        </Box>
      </Box>
      
      <TreeView
        expanded={expandedNodes}
        selected={selectedNode}
        onNodeToggle={(_, nodeIds) => handleNodeToggle(nodeIds)}
        onNodeSelect={(_, nodeId) => handleNodeSelect(nodeId)}
        defaultCollapseIcon={<ExpandMoreIcon />}
        defaultExpandIcon={<ChevronRightIcon />}
      >
        {navigationData.nodes.map(rootNode => renderTreeNode(rootNode))}
      </TreeView>
      
      {/* Decision Tree Visualization */}
      {selectedNode && (
        <DecisionTreePreview 
          nodeId={selectedNode}
          navigationData={navigationData}
        />
      )}
    </Box>
  );
};
```

## API Integration Services

### Package Management Service (`frontend/src/services/PackageAPI.ts`)

```typescript
export interface DocumentPackage {
  package_id: string;
  package_name: string;
  tenant_id: string;
  category: string;
  version: string;
  status: string;
  created_at: string;
  template_type: string;
}

export interface PackageFormData {
  package_name: string;
  category: string;
  template: string;
  customizations: Record<string, any>;
}

export const createDocumentPackage = async (packageData: PackageFormData): Promise<ServerResponse> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const formData = new FormData();
  formData.append('package_name', packageData.package_name);
  formData.append('category', packageData.category);
  formData.append('template', packageData.template);
  formData.append('customizations', JSON.stringify(packageData.customizations));
  
  appendUserCredentials(formData, userCredentials);
  
  const response = await fetch(`${apiUrl}/packages`, {
    method: 'POST',
    body: formData,
  });
  
  return response.json();
};

export const getDocumentPackages = async (category?: string): Promise<ServerResponse> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  appendUserCredentialsToParams(params, userCredentials);
  
  const response = await fetch(`${apiUrl}/packages?${params}`, {
    method: 'GET',
  });
  
  return response.json();
};

export const applyPackageToFiles = async (
  packageId: string, 
  fileIds: string[], 
  options: { update_in_place?: boolean; preserve_custom_sections?: boolean } = {}
): Promise<ServerResponse> => {
  const { apiUrl, userCredentials } = getApiConfig();
  
  const formData = new FormData();
  formData.append('document_ids', JSON.stringify(fileIds));
  formData.append('options', JSON.stringify(options));
  
  appendUserCredentials(formData, userCredentials);
  
  const response = await fetch(`${apiUrl}/packages/${packageId}/apply`, {
    method: 'POST',
    body: formData,
  });
  
  return response.json();
};
```

## State Management Integration

### Package Context Provider (`frontend/src/context/PackageContext.tsx`)

```typescript
interface PackageContextType {
  packages: DocumentPackage[];
  selectedPackage: DocumentPackage | null;
  isLoading: boolean;
  error: string | null;
  loadPackages: (category?: string) => Promise<void>;
  selectPackage: (packageId: string) => void;
  createPackage: (packageData: PackageFormData) => Promise<DocumentPackage>;
  applyPackage: (packageId: string, fileIds: string[]) => Promise<void>;
}

export const PackageContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [packages, setPackages] = useState<DocumentPackage[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<DocumentPackage | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const loadPackages = async (category?: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await getDocumentPackages(category);
      if (response.status === 'success') {
        setPackages(response.data);
      } else {
        setError(response.error || 'Failed to load packages');
      }
    } catch (err) {
      setError('Network error loading packages');
    } finally {
      setIsLoading(false);
    }
  };
  
  const selectPackage = (packageId: string) => {
    const pkg = packages.find(p => p.package_id === packageId);
    setSelectedPackage(pkg || null);
  };
  
  const createPackage = async (packageData: PackageFormData): Promise<DocumentPackage> => {
    const response = await createDocumentPackage(packageData);
    if (response.status === 'success') {
      const newPackage = response.data;
      setPackages(prev => [...prev, newPackage]);
      return newPackage;
    }
    throw new Error(response.error || 'Failed to create package');
  };
  
  const applyPackage = async (packageId: string, fileIds: string[]) => {
    const response = await applyPackageToFiles(packageId, fileIds);
    if (response.status !== 'success') {
      throw new Error(response.error || 'Failed to apply package');
    }
  };
  
  const value: PackageContextType = {
    packages,
    selectedPackage,
    isLoading,
    error,
    loadPackages,
    selectPackage,
    createPackage,
    applyPackage
  };
  
  return (
    <PackageContext.Provider value={value}>
      {children}
    </PackageContext.Provider>
  );
};
```

## UI Component Integration Points

### 1. Header Integration
Add package management button to existing header:

```typescript
// In frontend/src/components/Layout/Header.tsx
const [showPackageManager, setShowPackageManager] = useState(false);

// Add button next to existing actions
<IconButtonToolTip
  title="Manage Document Packages"
  onClick={() => setShowPackageManager(true)}
  size="medium"
>
  <FolderSpecialIcon />
</IconButtonToolTip>
```

### 2. Home.tsx Integration
Integrate package selection into main workflow:

```typescript
// In frontend/src/Home.tsx
const { selectedPackage } = useContext(PackageContext);

// Pass package context to relevant components
<EnhancedDropZone 
  packageId={selectedPackage?.package_id}
  enablePackageSelection={true}
  // ... other props
/>
```

### 3. FileTable Enhancement
Show package information in file table:

```typescript
// Enhance UserFile interface in types.ts
interface UserFile {
  // ... existing properties
  package_id?: string;
  package_name?: string;
  processing_metadata?: {
    navigation_extracted?: boolean;
    hierarchical_chunks_created?: boolean;
    decision_trees_complete?: boolean;
  };
}
```

## Type System Extensions

### New Types (`frontend/src/types.ts`)

```typescript
// Add to existing types.ts file

export interface DocumentPackage {
  package_id: string;
  package_name: string;
  tenant_id: string;
  category: 'NQM' | 'RTL' | 'SBC' | 'CONV';
  version: string;
  status: 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
  created_at: string;
  updated_at: string;
  created_by: string;
  template_type: string;
  documents: DocumentDefinition[];
  relationships: PackageRelationship[];
}

export interface NavigationNode {
  enhanced_node_id: string;
  node_type: 'CHAPTER' | 'SECTION' | 'SUBSECTION' | 'DECISION_FLOW_SECTION';
  title: string;
  depth_level: number;
  chapter_number?: number;
  section_number?: string;
  children: NavigationNode[];
  requires_complete_tree: boolean;
}

export interface NavigationTree {
  nodes: NavigationNode[];
  decision_trees: DecisionTree[];
  metadata: NavigationMetadata;
}

export interface ProcessingStep {
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
  details?: Record<string, any>;
}
```

## Testing Strategy

### Component Testing
```typescript
// __tests__/PackageManager.test.tsx
describe('PackageManager', () => {
  it('loads packages on mount', async () => {
    const mockPackages = [
      { package_id: 'pkg1', package_name: 'Test Package', category: 'NQM' }
    ];
    
    mockGetDocumentPackages.mockResolvedValue({
      status: 'success',
      data: mockPackages
    });
    
    render(<PackageManager isOpen={true} onClose={jest.fn()} onPackageSelected={jest.fn()} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Package')).toBeInTheDocument();
    });
  });
});
```

### Integration Testing
```typescript
// __tests__/PackageUploadFlow.test.tsx
describe('Package Upload Flow', () => {
  it('applies package structure during upload', async () => {
    // Test complete flow from package selection to upload completion
  });
});
```

## Migration Strategy

### Phase 1.5 Implementation Steps

1. **Week 2.5**: Create new components (PackageManager, PackageCreator)
2. **Week 2.75**: Integrate with existing DropZone and FileTable
3. **Week 2.9**: Add API services and context providers
4. **Week 2.95**: Update type definitions and test integration
5. **Week 3.0**: Deploy and validate with backend Phase 1 APIs

### Backward Compatibility
- All existing upload flows continue to work unchanged
- Package-based upload is opt-in through UI toggle
- Standard processing remains default behavior
- Existing file table and graph components unchanged

## Success Metrics

### User Experience Metrics
- Package creation time < 30 seconds
- Upload flow with packages feels natural and intuitive
- No breaking changes to existing workflows
- 95% compatibility with existing UI patterns

### Technical Metrics
- Component reusability > 80%
- API response times < 500ms
- Zero regression in existing functionality
- TypeScript coverage > 95%

## Next Steps
After Phase 1.5 completion:
1. Gather user feedback on package management UX
2. Optimize performance based on usage patterns
3. Prepare for Phase 2.5 matrix visualization components
4. Plan enhanced graph visualization for hierarchical navigation
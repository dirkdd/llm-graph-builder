import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  Chip,
  Button,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Chat as ChatIcon,
  Visibility as VisibilityIcon,
  Analytics as AnalyticsIcon,
  AccountTree as AccountTreeIcon
} from '@mui/icons-material';
import { CustomFile, DocumentPackage, ChatPackageContext } from '../../types';
import { NavigationViewer } from '../Navigation/NavigationViewer';

export interface PackageResultsViewerProps {
  packageId: string;
  processingResult: PackageProcessingResult;
  navigationData?: NavigationData[];
  onStartChat?: (packageContext: ChatPackageContext) => void;
  onViewGraph?: (packageId: string) => void;
  className?: string;
}

export interface PackageProcessingResult {
  packageId: string;
  packageName: string;
  totalFiles: number;
  processedFiles: number;
  successCount: number;
  failureCount: number;
  processingTime: number;
  totalNodes: number;
  totalRelationships: number;
  results: FileProcessingResult[];
  documentTypes: DocumentTypeStats[];
  categories: CategoryStats[];
}

export interface FileProcessingResult {
  fileId: string;
  fileName: string;
  documentType: string;
  status: 'completed' | 'failed';
  nodesCount: number;
  relationshipsCount: number;
  processingTime: number;
  extractedEntities?: string[];
  extractedRelationships?: string[];
  navigationPath?: string;
  errorMessage?: string;
}

export interface DocumentTypeStats {
  type: 'Guidelines' | 'Matrix' | 'Supporting' | 'Other';
  count: number;
  nodesCount: number;
  relationshipsCount: number;
  completedCount: number;
  failedCount: number;
}

export interface CategoryStats {
  categoryName: string;
  categoryType: string;
  filesCount: number;
  nodesCount: number;
  relationshipsCount: number;
  completedFiles: number;
  products: ProductStats[];
}

export interface ProductStats {
  productName: string;
  filesCount: number;
  nodesCount: number;
  relationshipsCount: number;
  completedFiles: number;
}

export interface NavigationData {
  id: string;
  title: string;
  level: number;
  path: string;
  children?: NavigationData[];
  documentType?: string;
  content?: string;
}

// Remove duplicate interface - using ChatPackageContext from types.ts

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`package-results-tabpanel-${index}`}
      aria-labelledby={`package-results-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 0 }}>{children}</Box>}
    </div>
  );
};

export const PackageResultsViewer: React.FC<PackageResultsViewerProps> = ({
  packageId,
  processingResult,
  navigationData = [],
  onStartChat,
  onViewGraph,
  className
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>('overview');

  // Create package context for chat integration
  const packageContext: ChatPackageContext = useMemo(() => ({
    packageId: processingResult.packageId,
    packageName: processingResult.packageName,
    documentTypes: processingResult.documentTypes.map(dt => dt.type),
    totalNodes: processingResult.totalNodes,
    totalRelationships: processingResult.totalRelationships,
    categories: processingResult.categories.map(cat => cat.categoryName),
    products: processingResult.categories.flatMap(cat => cat.products.map(prod => prod.productName))
  }), [processingResult]);

  // Handle tab changes
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Handle accordion expansion
  const handleAccordionChange = (panel: string) => (
    event: React.SyntheticEvent,
    isExpanded: boolean
  ) => {
    setExpandedAccordion(isExpanded ? panel : false);
  };

  // Handle chat start
  const handleStartChat = () => {
    if (onStartChat) {
      onStartChat(packageContext);
    }
  };

  // Handle graph view
  const handleViewGraph = () => {
    if (onViewGraph) {
      onViewGraph(packageId);
    }
  };

  // Calculate success rate
  const successRate = processingResult.totalFiles > 0 
    ? Math.round((processingResult.successCount / processingResult.totalFiles) * 100) 
    : 0;

  return (
    <Box className={className}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            <Typography variant="h5" gutterBottom>
              Package Processing Results
            </Typography>
            <Typography variant="h6" color="primary" gutterBottom>
              {processingResult.packageName}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Package ID: {packageId}
            </Typography>
          </Box>
          
          <Box display="flex" gap={1}>
            <Button
              variant="contained"
              startIcon={<ChatIcon />}
              onClick={handleStartChat}
              disabled={processingResult.successCount === 0}
            >
              Start Chat
            </Button>
            <Button
              variant="outlined"
              startIcon={<VisibilityIcon />}
              onClick={handleViewGraph}
              disabled={processingResult.successCount === 0}
            >
              View Graph
            </Button>
          </Box>
        </Box>

        {/* Status Alert */}
        <Alert 
          severity={processingResult.failureCount > 0 ? 'warning' : 'success'}
          sx={{ mb: 2 }}
        >
          <Typography variant="body2">
            <strong>Processing Complete:</strong> {processingResult.successCount} of {processingResult.totalFiles} files processed successfully
            ({successRate}% success rate)
          </Typography>
        </Alert>

        {/* Quick Stats */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="primary">
                  {processingResult.totalNodes.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Nodes
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="secondary">
                  {processingResult.totalRelationships.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Relationships
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="success.main">
                  {processingResult.successCount}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Files Processed
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="text.secondary">
                  {Math.round(processingResult.processingTime)}s
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Time
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={activeTab} onChange={handleTabChange} variant="fullWidth">
          <Tab 
            label="Overview" 
            icon={<AnalyticsIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="File Details" 
            icon={<ExpandMoreIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Navigation" 
            icon={<AccountTreeIcon />} 
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={activeTab} index={0}>
        {/* Overview Tab */}
        <Box>
          {/* Document Types Breakdown */}
          <Accordion 
            expanded={expandedAccordion === 'documentTypes'} 
            onChange={handleAccordionChange('documentTypes')}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Document Types</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {processingResult.documentTypes.map((docType) => (
                  <Grid item xs={12} sm={6} md={3} key={docType.type}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="h6">{docType.type}</Typography>
                          <Chip 
                            label={`${docType.completedCount}/${docType.count}`} 
                            color={docType.completedCount === docType.count ? 'success' : 'warning'}
                            size="small"
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          Nodes: {docType.nodesCount.toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Relationships: {docType.relationshipsCount.toLocaleString()}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* Categories Breakdown */}
          <Accordion 
            expanded={expandedAccordion === 'categories'} 
            onChange={handleAccordionChange('categories')}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Categories & Products</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {processingResult.categories.map((category) => (
                <Box key={category.categoryName} mb={3}>
                  <Typography variant="h6" gutterBottom>
                    {category.categoryName} ({category.categoryType})
                  </Typography>
                  <Box display="flex" gap={2} mb={2}>
                    <Chip label={`${category.completedFiles}/${category.filesCount} files`} />
                    <Chip label={`${category.nodesCount} nodes`} variant="outlined" />
                    <Chip label={`${category.relationshipsCount} relationships`} variant="outlined" />
                  </Box>
                  <List>
                    {category.products.map((product) => (
                      <ListItem key={product.productName} divider>
                        <ListItemText
                          primary={product.productName}
                          secondary={`${product.completedFiles}/${product.filesCount} files • ${product.nodesCount} nodes • ${product.relationshipsCount} relationships`}
                        />
                        <Chip 
                          label={product.completedFiles === product.filesCount ? 'Complete' : 'Partial'}
                          color={product.completedFiles === product.filesCount ? 'success' : 'warning'}
                          size="small"
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              ))}
            </AccordionDetails>
          </Accordion>
        </Box>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        {/* File Details Tab */}
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            File Processing Details
          </Typography>
          <List>
            {processingResult.results.map((result) => (
              <ListItem key={result.fileId} divider>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body1">{result.fileName}</Typography>
                      <Chip 
                        label={result.documentType} 
                        size="small" 
                        variant="outlined"
                      />
                      <Chip 
                        label={result.status} 
                        size="small" 
                        color={result.status === 'completed' ? 'success' : 'error'}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      {result.status === 'completed' ? (
                        <>
                          <Typography variant="body2" color="text.secondary">
                            Nodes: {result.nodesCount} • Relationships: {result.relationshipsCount} • Time: {result.processingTime}s
                          </Typography>
                          {result.navigationPath && (
                            <Typography variant="body2" color="primary">
                              Navigation: {result.navigationPath}
                            </Typography>
                          )}
                        </>
                      ) : (
                        <Typography variant="body2" color="error">
                          Error: {result.errorMessage}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        {/* Navigation Tab */}
        <Paper sx={{ p: 2 }}>
          {navigationData.length > 0 ? (
            <NavigationViewer 
              navigationData={navigationData}
              packageContext={packageContext}
            />
          ) : (
            <Alert severity="info">
              <Typography variant="body2">
                Navigation data will be available after processing documents with hierarchical chunking enabled.
              </Typography>
            </Alert>
          )}
        </Paper>
      </TabPanel>

      {/* Package Context for Chat */}
      {processingResult.successCount > 0 && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            Chat Integration Ready
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            This package is ready for intelligent querying with package-aware context.
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            {packageContext.categories.map(category => (
              <Chip key={category} label={category} size="small" />
            ))}
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default PackageResultsViewer;
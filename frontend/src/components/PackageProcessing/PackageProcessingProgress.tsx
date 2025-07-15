import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { CustomFile } from '../../types';

export interface PackageProcessingProgressProps {
  packageId: string;
  documents: CustomFile[];
  onComplete?: (results: PackageProcessingResult) => void;
  onRetry?: (fileId: string) => void;
  className?: string;
}

export interface PackageProcessingResult {
  packageId: string;
  totalFiles: number;
  processedFiles: number;
  successCount: number;
  failureCount: number;
  processingTime: number;
  results: FileProcessingResult[];
}

export interface FileProcessingResult {
  fileId: string;
  fileName: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  startTime?: number;
  endTime?: number;
  processingTime?: number;
  nodesCount?: number;
  relationshipsCount?: number;
  errorMessage?: string;
  documentType?: string;
}

export const PackageProcessingProgress: React.FC<PackageProcessingProgressProps> = ({
  packageId,
  documents,
  onComplete,
  onRetry,
  className
}) => {
  const [processingResults, setProcessingResults] = useState<FileProcessingResult[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>(false);

  // Initialize processing results from documents
  useEffect(() => {
    const initialResults: FileProcessingResult[] = documents.map(doc => ({
      fileId: doc.id,
      fileName: doc.name,
      status: doc.status === 'Processing' ? 'processing' : 
              doc.status === 'Completed' ? 'completed' :
              doc.status === 'Failed' ? 'failed' : 'pending',
      nodesCount: doc.nodesCount,
      relationshipsCount: doc.relationshipsCount,
      errorMessage: doc.errorMessage,
      documentType: doc.document_type
    }));
    setProcessingResults(initialResults);
  }, [documents]);

  // Check if processing is active
  useEffect(() => {
    const processing = processingResults.some(result => result.status === 'processing');
    setIsProcessing(processing);
  }, [processingResults]);

  // Calculate progress statistics
  const totalFiles = documents.length;
  const completedFiles = processingResults.filter(r => r.status === 'completed').length;
  const failedFiles = processingResults.filter(r => r.status === 'failed').length;
  const processingFiles = processingResults.filter(r => r.status === 'processing').length;
  const pendingFiles = processingResults.filter(r => r.status === 'pending').length;
  
  const progress = totalFiles > 0 ? ((completedFiles + failedFiles) / totalFiles) * 100 : 0;

  // Get status color for chips
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'processing': return 'primary';
      case 'pending': return 'default';
      default: return 'default';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon color="success" />;
      case 'failed': return <ErrorIcon color="error" />;
      case 'processing': return <PlayArrowIcon color="primary" />;
      case 'pending': return <InfoIcon color="disabled" />;
      default: return <InfoIcon color="disabled" />;
    }
  };

  // Handle accordion expansion
  const handleAccordionChange = (panel: string) => (
    event: React.SyntheticEvent,
    isExpanded: boolean
  ) => {
    setExpandedAccordion(isExpanded ? panel : false);
  };

  // Handle retry for failed files
  const handleRetry = (fileId: string) => {
    if (onRetry) {
      onRetry(fileId);
    }
  };

  return (
    <Box className={className}>
      <Paper sx={{ p: 3 }}>
        {/* Header */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Package Processing Progress
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Package ID: {packageId}
          </Typography>
        </Box>

        {/* Overall Progress */}
        <Box mb={3}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body1">
              Overall Progress: {completedFiles + failedFiles} / {totalFiles} files
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {Math.round(progress)}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Status Summary */}
        <Box display="flex" gap={1} mb={3} flexWrap="wrap">
          {completedFiles > 0 && (
            <Chip 
              label={`${completedFiles} Completed`} 
              color="success" 
              size="small" 
              icon={<CheckCircleIcon />}
            />
          )}
          {failedFiles > 0 && (
            <Chip 
              label={`${failedFiles} Failed`} 
              color="error" 
              size="small" 
              icon={<ErrorIcon />}
            />
          )}
          {processingFiles > 0 && (
            <Chip 
              label={`${processingFiles} Processing`} 
              color="primary" 
              size="small" 
              icon={<PlayArrowIcon />}
            />
          )}
          {pendingFiles > 0 && (
            <Chip 
              label={`${pendingFiles} Pending`} 
              color="default" 
              size="small" 
              icon={<InfoIcon />}
            />
          )}
        </Box>

        {/* Processing Status Alert */}
        {isProcessing && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Processing in progress...</strong><br />
              Files are being processed with package-aware hierarchical chunking and enhanced entity extraction.
            </Typography>
          </Alert>
        )}

        {/* Completion Alert */}
        {!isProcessing && (completedFiles > 0 || failedFiles > 0) && (
          <Alert 
            severity={failedFiles > 0 ? 'warning' : 'success'} 
            sx={{ mb: 3 }}
          >
            <Typography variant="body2">
              <strong>Processing {failedFiles > 0 ? 'completed with errors' : 'completed successfully'}!</strong><br />
              {completedFiles} files processed successfully
              {failedFiles > 0 && `, ${failedFiles} files failed`}
            </Typography>
          </Alert>
        )}

        {/* Detailed File Results */}
        <Accordion 
          expanded={expandedAccordion === 'fileDetails'} 
          onChange={handleAccordionChange('fileDetails')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">File Processing Details</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List>
              {processingResults.map((result) => (
                <ListItem 
                  key={result.fileId}
                  sx={{ 
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    '&:last-child': { mb: 0 }
                  }}
                >
                  <ListItemIcon>
                    {getStatusIcon(result.status)}
                  </ListItemIcon>
                  
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body1" component="span">
                          {result.fileName}
                        </Typography>
                        <Chip 
                          label={result.status} 
                          size="small" 
                          color={getStatusColor(result.status) as any}
                        />
                        {result.documentType && (
                          <Chip 
                            label={result.documentType} 
                            size="small" 
                            variant="outlined"
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box>
                        {result.status === 'completed' && (
                          <Typography variant="body2" color="text.secondary">
                            Nodes: {result.nodesCount || 0} • Relationships: {result.relationshipsCount || 0}
                            {result.processingTime && ` • Time: ${result.processingTime}s`}
                          </Typography>
                        )}
                        {result.status === 'failed' && result.errorMessage && (
                          <Typography variant="body2" color="error">
                            Error: {result.errorMessage}
                          </Typography>
                        )}
                        {result.status === 'processing' && (
                          <Typography variant="body2" color="primary">
                            Processing with package-aware extraction...
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  
                  {result.status === 'failed' && onRetry && (
                    <IconButton 
                      onClick={() => handleRetry(result.fileId)}
                      size="small"
                      color="primary"
                    >
                      <RefreshIcon />
                    </IconButton>
                  )}
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>

        {/* Processing Metrics */}
        {(completedFiles > 0 || failedFiles > 0) && (
          <Accordion 
            expanded={expandedAccordion === 'metrics'} 
            onChange={handleAccordionChange('metrics')}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Processing Metrics</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box display="flex" flexWrap="wrap" gap={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary">Total Files</Typography>
                  <Typography variant="h6">{totalFiles}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Success Rate</Typography>
                  <Typography variant="h6" color="success.main">
                    {totalFiles > 0 ? Math.round((completedFiles / totalFiles) * 100) : 0}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Total Nodes</Typography>
                  <Typography variant="h6">
                    {processingResults.reduce((sum, r) => sum + (r.nodesCount || 0), 0)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Total Relationships</Typography>
                  <Typography variant="h6">
                    {processingResults.reduce((sum, r) => sum + (r.relationshipsCount || 0), 0)}
                  </Typography>
                </Box>
              </Box>
            </AccordionDetails>
          </Accordion>
        )}
      </Paper>
    </Box>
  );
};

export default PackageProcessingProgress;
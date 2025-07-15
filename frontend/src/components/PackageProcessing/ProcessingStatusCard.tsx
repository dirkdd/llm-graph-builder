import React from 'react';
import { Typography, Button } from '@neo4j-ndl/react';
import {
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RefreshIcon from '@mui/icons-material/Refresh';
import { PackageProcessingStatus, PackageFile } from '../../types';

interface ProcessingStatusCardProps {
  packageId: string;
  packageName: string;
  status: PackageProcessingStatus;
  files: PackageFile[];
  onRefresh?: () => void;
  onRetryFailed?: (fileId: string) => void;
  onViewResults?: (fileId: string) => void;
}

export const ProcessingStatusCard: React.FC<ProcessingStatusCardProps> = ({
  packageId,
  packageName,
  status,
  files,
  onRefresh,
  onRetryFailed,
  onViewResults
}) => {
  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'info' => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'processing': return 'info';
      case 'pending': return 'warning';
      default: return 'info';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'processing':
        return <PlayArrowIcon color="info" />;
      case 'pending':
        return <HourglassEmptyIcon color="warning" />;
      default:
        return <HourglassEmptyIcon />;
    }
  };

  const getOverallProgress = () => {
    const totalFiles = files.length;
    const completedFiles = files.filter(f => f.processing_status === 'completed').length;
    return totalFiles > 0 ? (completedFiles / totalFiles) * 100 : 0;
  };

  const getStatusCounts = () => {
    return files.reduce((acc, file) => {
      acc[file.processing_status] = (acc[file.processing_status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  };

  const statusCounts = getStatusCounts();
  const overallProgress = getOverallProgress();

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Package: {packageName}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
              <Chip 
                size="small" 
                label={status.overall_status.replace('_', ' ').toUpperCase()}
                color={getStatusColor(status.overall_status)}
              />
              <Chip 
                size="small" 
                label={`${files.length} files`}
                variant="outlined"
              />
            </Box>
          </Box>
          <Button 
            size="small" 
            onClick={onRefresh}
            fill="outlined"
            startIcon={<RefreshIcon />}
          >
            Refresh
          </Button>
        </Box>

        {/* Overall Progress */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body-medium">Overall Progress</Typography>
            <Typography variant="body-medium">{Math.round(overallProgress)}%</Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={overallProgress}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Status Summary */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          {Object.entries(statusCounts).map(([status, count]) => (
            <Chip
              key={status}
              size="small"
              label={`${status}: ${count}`}
              color={getStatusColor(status)}
              variant="outlined"
            />
          ))}
        </Box>

        {/* Processing Steps */}
        {status.processing_steps && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subheading-medium" gutterBottom>
              Processing Pipeline
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {status.processing_steps.map((step, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Chip
                    size="small"
                    label={step.name}
                    color={step.completed ? 'success' : step.active ? 'info' : 'default'}
                    variant={step.active ? 'filled' : 'outlined'}
                  />
                  {index < status.processing_steps.length - 1 && (
                    <Typography variant="body-small">→</Typography>
                  )}
                </Box>
              ))}
            </Box>
          </Box>
        )}

        {/* Error Summary */}
        {status.errors && status.errors.length > 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body-medium" gutterBottom>
              Processing Errors ({status.errors.length})
            </Typography>
            <List dense>
              {status.errors.slice(0, 3).map((error, index) => (
                <ListItem key={index} sx={{ py: 0 }}>
                  <ListItemText 
                    primary={error.message}
                    secondary={error.file_name && `File: ${error.file_name}`}
                  />
                </ListItem>
              ))}
              {status.errors.length > 3 && (
                <Typography variant="body-small">
                  ... and {status.errors.length - 3} more errors
                </Typography>
              )}
            </List>
          </Alert>
        )}

        {/* File Details */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subheading-medium">
              File Processing Details ({files.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {files.map((file) => (
                <ListItem 
                  key={file.id}
                  sx={{ 
                    borderBottom: '1px solid', 
                    borderColor: 'divider',
                    '&:last-child': { borderBottom: 'none' }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {getStatusIcon(file.processing_status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body-medium">{file.name}</Typography>
                        <Chip
                          size="small"
                          label={file.processing_status}
                          color={getStatusColor(file.processing_status)}
                          sx={{ fontSize: '0.7rem', height: 18 }}
                        />
                      </Box>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        {file.processing_time && (
                          <Typography variant="body-small">
                            {file.processing_time}s
                          </Typography>
                        )}
                        {file.entity_count && (
                          <Typography variant="body-small">
                            {file.entity_count} entities
                          </Typography>
                        )}
                        {file.relationship_count && (
                          <Typography variant="body-small">
                            {file.relationship_count} relationships
                          </Typography>
                        )}
                        {file.processing_status === 'completed' && onViewResults && (
                          <Button 
                            size="small" 
                            onClick={() => onViewResults(file.id)}
                          >
                            View Results
                          </Button>
                        )}
                        {file.processing_status === 'failed' && onRetryFailed && (
                          <Button 
                            size="small" 
                            onClick={() => onRetryFailed(file.id)}
                            fill="outlined"
                          >
                            Retry
                          </Button>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>

        {/* Package Metadata */}
        {status.package_metadata && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="subheading-medium" gutterBottom>
              Package Metadata
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              {status.package_metadata.total_entities && (
                <Chip 
                  size="small" 
                  label={`${status.package_metadata.total_entities} total entities`}
                  variant="outlined"
                />
              )}
              {status.package_metadata.total_relationships && (
                <Chip 
                  size="small" 
                  label={`${status.package_metadata.total_relationships} total relationships`}
                  variant="outlined"
                />
              )}
              {status.package_metadata.decision_trees_extracted && (
                <Chip 
                  size="small" 
                  label={`${status.package_metadata.decision_trees_extracted} decision trees`}
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
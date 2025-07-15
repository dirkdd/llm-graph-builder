import React from 'react';
import { Typography } from '@neo4j-ndl/react';
import {
  Box,
  Chip,
  LinearProgress,
  Tooltip,
  CircularProgress
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

interface ProcessingIndicatorProps {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  fileName?: string;
  entityCount?: number;
  relationshipCount?: number;
  processingTime?: number;
  error?: string;
  compact?: boolean;
  showDetails?: boolean;
}

export const ProcessingIndicator: React.FC<ProcessingIndicatorProps> = ({
  status,
  progress,
  fileName,
  entityCount,
  relationshipCount,
  processingTime,
  error,
  compact = false,
  showDetails = true
}) => {
  const getStatusColor = (): 'success' | 'error' | 'warning' | 'info' => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'processing': return 'info';
      case 'pending': return 'warning';
      default: return 'info';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon fontSize="small" color="success" />;
      case 'failed':
        return <ErrorIcon fontSize="small" color="error" />;
      case 'processing':
        return compact ? 
          <CircularProgress size={16} /> : 
          <PlayArrowIcon fontSize="small" color="info" />;
      case 'pending':
        return <HourglassEmptyIcon fontSize="small" color="warning" />;
      default:
        return <HourglassEmptyIcon fontSize="small" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'completed': return 'Completed';
      case 'failed': return 'Failed';
      case 'processing': return 'Processing...';
      case 'pending': return 'Pending';
      default: return 'Unknown';
    }
  };

  const getProgressText = () => {
    if (progress !== undefined) {
      return `${Math.round(progress)}%`;
    }
    return null;
  };

  if (compact) {
    return (
      <Tooltip 
        title={
          <Box>
            <Typography variant="body-small">{getStatusText()}</Typography>
            {fileName && <Typography variant="body-small">File: {fileName}</Typography>}
            {error && <Typography variant="body-small" color="error">Error: {error}</Typography>}
          </Box>
        }
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {getStatusIcon()}
          <Chip
            size="small"
            label={getStatusText()}
            color={getStatusColor()}
            sx={{ fontSize: '0.7rem', height: 20 }}
          />
          {progress !== undefined && status === 'processing' && (
            <Typography variant="body-small">
              {getProgressText()}
            </Typography>
          )}
        </Box>
      </Tooltip>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Status Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        {getStatusIcon()}
        <Typography variant="body-medium" sx={{ flexGrow: 1 }}>
          {getStatusText()}
          {fileName && ` - ${fileName}`}
        </Typography>
        <Chip
          size="small"
          label={getStatusText()}
          color={getStatusColor()}
        />
      </Box>

      {/* Progress Bar */}
      {status === 'processing' && progress !== undefined && (
        <Box sx={{ mb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body-small">Processing Progress</Typography>
            <Typography variant="body-small">{getProgressText()}</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{ height: 6, borderRadius: 3 }}
          />
        </Box>
      )}

      {/* Processing Details */}
      {showDetails && (status === 'completed' || status === 'processing') && (
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
          {entityCount !== undefined && (
            <Chip
              size="small"
              label={`${entityCount} entities`}
              variant="outlined"
              sx={{ fontSize: '0.7rem', height: 18 }}
            />
          )}
          {relationshipCount !== undefined && (
            <Chip
              size="small"
              label={`${relationshipCount} relationships`}
              variant="outlined"
              sx={{ fontSize: '0.7rem', height: 18 }}
            />
          )}
          {processingTime !== undefined && (
            <Chip
              size="small"
              label={`${processingTime}s`}
              variant="outlined"
              sx={{ fontSize: '0.7rem', height: 18 }}
            />
          )}
        </Box>
      )}

      {/* Error Display */}
      {status === 'failed' && error && (
        <Box sx={{ 
          p: 1, 
          bgcolor: 'error.light', 
          borderRadius: 1, 
          mt: 1,
          border: '1px solid',
          borderColor: 'error.main'
        }}>
          <Typography variant="body-small" color="error.dark">
            <strong>Error:</strong> {error}
          </Typography>
        </Box>
      )}

      {/* Pending Information */}
      {status === 'pending' && (
        <Typography variant="body-small" color="text.secondary">
          Waiting to begin processing...
        </Typography>
      )}
    </Box>
  );
};
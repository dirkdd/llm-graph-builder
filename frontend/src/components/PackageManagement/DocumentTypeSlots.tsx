import React, { useState, useCallback, useRef } from 'react';
import {
  Button
} from '@neo4j-ndl/react';
import {
  Box,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  Grid,
  Snackbar,
  CircularProgress,
  Tooltip,
  IconButton,
  Collapse,
  Typography,
  Fade,
  Grow,
  useTheme,
  useMediaQuery,
  Skeleton
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Description as DocumentIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { DocumentSlotSkeleton } from './DocumentSlotSkeleton';

export interface ExpectedDocument {
  id: string;
  document_type: string;
  document_name: string;
  is_required: boolean;
  upload_status: 'empty' | 'uploaded' | 'processing' | 'failed';
  uploaded_file?: {
    fileName: string;
    fileSize: number;
    uploadDate: string;
    processingStatus: string;
  };
  validation_rules: {
    accepted_types: string[];
    accepted_mime_types: string[];
    max_file_size: number;
    description: string;
  };
  error_message?: string;
  retry_count?: number;
  // Program-level association for matrices
  level?: 'product' | 'program';
  programCode?: string;
  programName?: string;
}

export interface ValidationError {
  type: 'file_size' | 'file_type' | 'file_format' | 'network' | 'server' | 'unknown';
  message: string;
  details?: string;
  suggestions?: string[];
}

export interface UploadError {
  documentId: string;
  file: File;
  error: ValidationError;
  timestamp: Date;
  retryCount: number;
}

interface DocumentTypeSlotsProps {
  expectedDocuments: ExpectedDocument[];
  onFileUpload: (file: File, expectedDocumentId: string, documentType: string) => void;
  uploadProgress: Record<string, number>;
  disabled?: boolean;
  className?: string;
  onError?: (error: UploadError) => void;
  onRetry?: (documentId: string, file: File) => void;
  loading?: boolean;
  maxRetries?: number;
  onUploadStart?: (documentId: string, file: File) => void;
}

export const DocumentTypeSlots: React.FC<DocumentTypeSlotsProps> = ({
  expectedDocuments,
  onFileUpload,
  uploadProgress,
  disabled = false,
  className,
  onError,
  onRetry,
  loading = false,
  maxRetries = 3,
  onUploadStart
}) => {
  const [activeSlotId, setActiveSlotId] = useState<string | null>(null);
  const [uploadErrors, setUploadErrors] = useState<Record<string, UploadError>>({});
  const [showErrorDetails, setShowErrorDetails] = useState<Record<string, boolean>>({});
  const [retryingDocuments, setRetryingDocuments] = useState<Set<string>>(new Set());

  const getStatusIcon = (uploadStatus: string) => {
    switch (uploadStatus) {
      case 'uploaded':
        return <CheckCircleIcon sx={{ color: 'success.main', width: 20, height: 20 }} />;
      case 'processing':
        return <PlayArrowIcon sx={{ color: 'warning.main', width: 20, height: 20 }} />;
      case 'failed':
        return <ErrorIcon sx={{ color: 'error.main', width: 20, height: 20 }} />;
      default:
        return <WarningIcon sx={{ color: 'text.secondary', width: 20, height: 20 }} />;
    }
  };

  const getStatusColor = (uploadStatus: string, isRequired: boolean) => {
    switch (uploadStatus) {
      case 'uploaded':
        return 'success.main';
      case 'processing':
        return 'warning.main';
      case 'failed':
        return 'error.main';
      case 'empty':
        return isRequired ? 'error.light' : 'text.secondary';
      default:
        return 'text.secondary';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Enhanced file validation with detailed error reporting
  const validateFile = useCallback((file: File, document: ExpectedDocument): ValidationError | null => {
    const { validation_rules } = document;
    
    // File size validation
    if (file.size > validation_rules.max_file_size) {
      return {
        type: 'file_size',
        message: `File size exceeds limit`,
        details: `File size: ${formatFileSize(file.size)}. Maximum allowed: ${formatFileSize(validation_rules.max_file_size)}`,
        suggestions: [
          'Compress your file using a file compression tool',
          'Split large documents into smaller sections',
          'Save the file in a more efficient format (e.g., PDF instead of Word)',
          'Remove unnecessary images or content from the document'
        ]
      };
    }

    // File type validation
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!validation_rules.accepted_types.includes(fileExtension)) {
      return {
        type: 'file_type',
        message: `File type not supported`,
        details: `File type: ${fileExtension}. Accepted types: ${validation_rules.accepted_types.join(', ')}`,
        suggestions: [
          `Convert your file to one of these formats: ${validation_rules.accepted_types.join(', ')}`,
          'Use "Save As" in your application to change the file format',
          'Check if you have the correct document for this slot'
        ]
      };
    }

    // MIME type validation
    if (validation_rules.accepted_mime_types.length > 0 && 
        !validation_rules.accepted_mime_types.includes(file.type)) {
      return {
        type: 'file_format',
        message: `File format not recognized`,
        details: `MIME type: ${file.type}. Expected: ${validation_rules.accepted_mime_types.join(', ')}`,
        suggestions: [
          'Ensure the file is not corrupted',
          'Try saving the file again from the original application',
          'Contact support if the file appears to be in the correct format'
        ]
      };
    }

    return null;
  }, []);

  // Handle upload errors with retry logic
  const handleUploadError = useCallback((documentId: string, file: File, error: ValidationError) => {
    const existingError = uploadErrors[documentId];
    const retryCount = existingError ? existingError.retryCount + 1 : 0;
    
    const uploadError: UploadError = {
      documentId,
      file,
      error,
      timestamp: new Date(),
      retryCount
    };

    setUploadErrors(prev => ({
      ...prev,
      [documentId]: uploadError
    }));

    // Call error callback if provided
    if (onError) {
      onError(uploadError);
    }

    // Auto-retry for network/server errors (but not validation errors)
    if (error.type === 'network' || error.type === 'server') {
      if (retryCount < maxRetries) {
        setTimeout(() => {
          handleRetry(documentId, file);
        }, Math.pow(2, retryCount) * 1000); // Exponential backoff
      }
    }
  }, [uploadErrors, onError, maxRetries]);

  // Handle retry attempts
  const handleRetry = useCallback((documentId: string, file: File) => {
    setRetryingDocuments(prev => new Set(prev).add(documentId));
    
    // Clear previous errors
    setUploadErrors(prev => {
      const updated = { ...prev };
      delete updated[documentId];
      return updated;
    });

    // Call retry callback if provided, otherwise use regular upload
    if (onRetry) {
      onRetry(documentId, file);
    } else {
      const document = expectedDocuments.find(d => d.id === documentId);
      if (document) {
        onFileUpload(file, documentId, document.document_type);
      }
    }

    // Remove from retrying set after a delay
    setTimeout(() => {
      setRetryingDocuments(prev => {
        const updated = new Set(prev);
        updated.delete(documentId);
        return updated;
      });
    }, 2000);
  }, [onRetry, onFileUpload, expectedDocuments]);

  // Clear error for a document
  const clearError = useCallback((documentId: string) => {
    setUploadErrors(prev => {
      const updated = { ...prev };
      delete updated[documentId];
      return updated;
    });
    setShowErrorDetails(prev => ({
      ...prev,
      [documentId]: false
    }));
  }, []);

  // Toggle error details visibility
  const toggleErrorDetails = useCallback((documentId: string) => {
    setShowErrorDetails(prev => ({
      ...prev,
      [documentId]: !prev[documentId]
    }));
  }, []);

  const DocumentSlot: React.FC<{ document: ExpectedDocument }> = ({ document }) => {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    const fileInputRef = useRef<HTMLInputElement>(null);
    
    const isUploading = uploadProgress[document.id] !== undefined;
    const uploadPercentage = uploadProgress[document.id] || 0;
    const canUpload = !disabled && document.upload_status !== 'processing' && !retryingDocuments.has(document.id);
    const isDragActive = activeSlotId === document.id;
    const hasError = uploadErrors[document.id];
    const isRetrying = retryingDocuments.has(document.id);
    
    // Accessibility helpers
    const slotId = `document-slot-${document.id}`;
    const errorId = `error-${document.id}`;
    const descriptionId = `description-${document.id}`;
    
    const getAccessibilityLabel = () => {
      let label = `Upload ${document.document_type} document: ${document.document_name}`;
      if (document.is_required) label += ', required';
      
      switch (document.upload_status) {
        case 'uploaded':
          label += ', already uploaded';
          break;
        case 'processing':
          label += ', currently processing';
          break;
        case 'failed':
          label += ', upload failed';
          break;
        default:
          label += ', ready for upload';
      }
      
      if (hasError) {
        label += `, error: ${hasError.error.message}`;
      }
      
      return label;
    };
    
    const handleKeyDown = (event: React.KeyboardEvent) => {
      if ((event.key === 'Enter' || event.key === ' ') && canUpload) {
        event.preventDefault();
        fileInputRef.current?.click();
      }
    };

    const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
      setActiveSlotId(null);
      
      // Handle rejected files first
      if (rejectedFiles.length > 0) {
        const rejectedFile = rejectedFiles[0];
        let error: ValidationError;
        
        if (rejectedFile.errors.some((e: any) => e.code === 'file-too-large')) {
          error = {
            type: 'file_size',
            message: 'File size exceeds limit',
            details: `Maximum allowed: ${formatFileSize(document.validation_rules.max_file_size)}`,
            suggestions: ['Compress your file or split it into smaller parts']
          };
        } else if (rejectedFile.errors.some((e: any) => e.code === 'file-invalid-type')) {
          error = {
            type: 'file_type',
            message: 'File type not supported',
            details: `Accepted types: ${document.validation_rules.accepted_types.join(', ')}`,
            suggestions: ['Convert your file to a supported format']
          };
        } else {
          error = {
            type: 'unknown',
            message: 'File rejected',
            details: rejectedFile.errors.map((e: any) => e.message).join(', '),
            suggestions: ['Check the file and try again']
          };
        }
        
        handleUploadError(document.id, rejectedFile.file, error);
        return;
      }

      // Handle accepted files
      if (acceptedFiles.length > 0 && canUpload) {
        const file = acceptedFiles[0];
        
        // Clear any previous errors
        clearError(document.id);
        
        // Perform additional validation
        const validationError = validateFile(file, document);
        if (validationError) {
          handleUploadError(document.id, file, validationError);
          return;
        }

        // File is valid, proceed with upload
        try {
          // Notify parent component about upload start for optimistic UI update
          if (onUploadStart) {
            onUploadStart(document.id, file);
          }
          
          onFileUpload(file, document.id, document.document_type);
        } catch (error) {
          const uploadError: ValidationError = {
            type: 'unknown',
            message: 'Upload failed',
            details: error instanceof Error ? error.message : 'Unknown error occurred',
            suggestions: ['Try uploading again', 'Check your internet connection']
          };
          handleUploadError(document.id, file, uploadError);
        }
      }
    }, [document, canUpload, onFileUpload, clearError, validateFile, handleUploadError]);

    const { getRootProps, getInputProps, isDragAccept, isDragReject } = useDropzone({
      onDrop,
      onDragEnter: () => setActiveSlotId(document.id),
      onDragLeave: () => setActiveSlotId(null),
      accept: document.validation_rules.accepted_mime_types.reduce((acc, mime) => {
        acc[mime] = document.validation_rules.accepted_types;
        return acc;
      }, {} as Record<string, string[]>),
      disabled: !canUpload,
      multiple: false,
      maxSize: document.validation_rules.max_file_size
    });

    return (
      <Grow in={true} timeout={300}>
        <Paper
          {...getRootProps()}
          component="div"
          role="button"
          tabIndex={canUpload ? 0 : -1}
          id={slotId}
          aria-label={getAccessibilityLabel()}
          aria-describedby={`${descriptionId} ${hasError ? errorId : ''}`}
          aria-disabled={!canUpload}
          aria-invalid={hasError ? 'true' : 'false'}
          onKeyDown={handleKeyDown}
          sx={{
            p: isMobile ? 1.5 : 2,
            border: '2px dashed',
            borderColor: hasError
              ? 'error.main'
              : isDragActive 
                ? 'primary.main' 
                : isDragAccept
                  ? 'success.main'
                  : isDragReject
                    ? 'error.main'
                    : getStatusColor(document.upload_status, document.is_required),
            borderRadius: 2,
            cursor: canUpload ? 'pointer' : 'not-allowed',
            bgcolor: hasError
              ? 'rgba(255, 0, 0, 0.05)'
              : isDragActive 
                ? 'rgba(var(--theme-palette-primary-bg-strong), 0.08)' 
                : 'background.paper',
            opacity: canUpload ? 1 : 0.7,
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            height: hasError ? (isMobile ? '280px' : '250px') : (isMobile ? '180px' : '200px'), // Fixed height instead of minHeight
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            position: 'relative',
            transform: isDragActive ? 'scale(1.02)' : 'scale(1)',
            boxShadow: isDragActive ? theme.shadows[4] : theme.shadows[1],
            '&:hover': canUpload ? {
              borderColor: hasError ? 'error.main' : 'primary.main',
              bgcolor: hasError ? 'rgba(255, 0, 0, 0.08)' : 'rgba(var(--theme-palette-primary-bg-strong), 0.04)',
              transform: 'scale(1.01)',
              boxShadow: theme.shadows[2]
            } : {},
            '&:focus': {
              outline: `2px solid ${theme.palette.primary.main}`,
              outlineOffset: '2px'
            },
            '&:focus:not(:focus-visible)': {
              outline: 'none'
            }
          }}
        >
          <input 
            {...getInputProps()} 
            ref={fileInputRef}
            disabled={!canUpload}
            aria-hidden="true"
          />
        
        {/* Upload Progress */}
        {isUploading && (
          <Fade in={isUploading}>
            <Box sx={{ position: 'absolute', top: 8, left: 8, right: 8 }}>
              <LinearProgress 
                variant="determinate" 
                value={uploadPercentage}
                sx={{
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: 'rgba(0, 0, 0, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 3,
                    transition: 'transform 0.4s ease'
                  }
                }}
              />
              <Typography 
                variant="caption" 
                color="text.secondary" 
                sx={{ 
                  mt: 0.5, 
                  display: 'block', 
                  textAlign: 'center',
                  fontWeight: 500
                }}
                role="status"
                aria-live="polite"
              >
                Uploading... {uploadPercentage}%
              </Typography>
            </Box>
          </Fade>
        )}

        {/* Retry Progress */}
        {isRetrying && (
          <Fade in={isRetrying}>
            <Box sx={{ position: 'absolute', top: 8, left: 8, right: 8 }}>
              <LinearProgress 
                color="warning"
                sx={{
                  height: 6,
                  borderRadius: 3,
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 3
                  }
                }}
              />
              <Typography 
                variant="caption" 
                color="warning.main" 
                sx={{ 
                  mt: 0.5, 
                  display: 'block', 
                  textAlign: 'center',
                  fontWeight: 500
                }}
                role="status"
                aria-live="polite"
              >
                Retrying upload...
              </Typography>
            </Box>
          </Fade>
        )}

        {/* Required Badge - Only show if required and not uploaded */}
        {document.is_required && document.upload_status !== 'uploaded' && (
          <Chip
            label="Required"
            size="small"
            color="error"
            variant="outlined"
            sx={{ 
              position: 'absolute', 
              top: 8, 
              left: '50%',
              transform: 'translateX(-50%)', // Center horizontally
              zIndex: 1
            }}
          />
        )}

        {/* Status Icon */}
        <Box sx={{ mb: 1 }}>
          {getStatusIcon(document.upload_status)}
        </Box>

        {/* Document Type */}
        <Typography 
          variant="h6" 
          color="text.primary" 
          sx={{ 
            mb: 0.5, 
            fontWeight: 600, 
            textAlign: 'center',
            fontSize: isMobile ? '1rem' : '1.25rem'
          }}
          component="h3"
        >
          {document.document_type}
        </Typography>
        
        {/* Document Name */}
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ 
            mb: 1, 
            textAlign: 'center',
            fontSize: isMobile ? '0.75rem' : '0.875rem'
          }}
          id={descriptionId}
        >
          {document.document_name}
        </Typography>

        {/* Upload Status */}
        {document.upload_status === 'empty' ? (
          <Box sx={{ textAlign: 'center' }}>
            <CloudUploadIcon sx={{ color: 'text.secondary', mb: 1, width: 24, height: 24 }} />
            <Typography variant="body2" color="text.secondary">
              Drop file here or click to browse
            </Typography>
          </Box>
        ) : (
          <Box sx={{ textAlign: 'center' }}>
            <DocumentIcon sx={{ color: 'primary.main', mb: 1, width: 24, height: 24 }} />
            <Typography variant="body2" color="text.primary" sx={{ fontWeight: 500 }}>
              {document.uploaded_file?.fileName}
            </Typography>
            {document.uploaded_file && (
              <Typography variant="caption" color="text.secondary">
                {formatFileSize(document.uploaded_file.fileSize)} • {new Date(document.uploaded_file.uploadDate).toLocaleDateString()}
              </Typography>
            )}
          </Box>
        )}

        {/* Accepted File Types */}
        {document.upload_status === 'empty' && !hasError && (
          <Box sx={{ mt: 1 }}>
            <Box display="flex" flexWrap="wrap" gap={0.5} justifyContent="center">
              {document.validation_rules.accepted_types.slice(0, 3).map((type) => (
                <Chip key={type} label={type.toUpperCase()} size="small" variant="outlined" />
              ))}
              {document.validation_rules.accepted_types.length > 3 && (
                <Chip label={`+${document.validation_rules.accepted_types.length - 3}`} size="small" variant="outlined" />
              )}
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block', textAlign: 'center' }}>
              Max: {formatFileSize(document.validation_rules.max_file_size)}
            </Typography>
          </Box>
        )}

        {/* Error Display */}
        {hasError && (
          <Fade in={true}>
            <Box sx={{ position: 'absolute', bottom: 8, left: 8, right: 8 }}>
              <Alert 
                severity="error" 
                id={errorId}
                role="alert"
                aria-live="assertive"
                sx={{ 
                  mb: 1,
                  '& .MuiAlert-message': { 
                    width: '100%',
                    fontSize: isMobile ? '0.7rem' : '0.75rem'
                  }
                }}
                action={
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="Show error details">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleErrorDetails(document.id);
                        }}
                        sx={{ color: 'error.main' }}
                        aria-label="Show error details"
                        aria-expanded={showErrorDetails[document.id]}
                        aria-controls={`error-details-${document.id}`}
                      >
                        {showErrorDetails[document.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </Tooltip>
                    {hasError.retryCount < maxRetries && (
                      <Tooltip title="Retry upload">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRetry(document.id, hasError.file);
                          }}
                          sx={{ color: 'error.main' }}
                          aria-label="Retry upload"
                        >
                          <RefreshIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Clear error">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          clearError(document.id);
                        }}
                        sx={{ color: 'error.main' }}
                        aria-label="Clear error"
                      >
                        <CloseIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                }
              >
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {hasError.error.message}
              </Typography>
              {hasError.error.details && (
                <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                  {hasError.error.details}
                </Typography>
              )}
            </Alert>

            {/* Error Details */}
            <Collapse in={showErrorDetails[document.id]} timeout={300}>
              <Box 
                sx={{ bgcolor: 'error.lighter', p: 1, borderRadius: 1, mt: 1 }}
                id={`error-details-${document.id}`}
                role="region"
                aria-label="Error details and suggestions"
              >
                <Typography 
                  variant="caption" 
                  sx={{ 
                    fontWeight: 600, 
                    display: 'block', 
                    mb: 0.5,
                    fontSize: isMobile ? '0.65rem' : '0.75rem'
                  }}
                >
                  Suggestions:
                </Typography>
                {hasError.error.suggestions?.map((suggestion, index) => (
                  <Typography 
                    key={index} 
                    variant="caption" 
                    sx={{ 
                      display: 'block', 
                      ml: 1,
                      fontSize: isMobile ? '0.6rem' : '0.7rem'
                    }}
                  >
                    • {suggestion}
                  </Typography>
                ))}
                <Typography 
                  variant="caption" 
                  sx={{ 
                    display: 'block', 
                    mt: 1, 
                    opacity: 0.7,
                    fontSize: isMobile ? '0.6rem' : '0.7rem'
                  }}
                >
                  Retry count: {hasError.retryCount}/{maxRetries}
                </Typography>
              </Box>
            </Collapse>
            </Box>
          </Fade>
        )}
        </Paper>
      </Grow>
    );
  };

  if (expectedDocuments.length === 0) {
    return (
      <Box className={className}>
        <Alert severity="info">
          No expected documents defined for this product. Documents will be uploaded with standard processing.
        </Alert>
      </Box>
    );
  }

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Show skeleton loading state
  if (loading) {
    return <DocumentSlotSkeleton count={3} className={className} />;
  }

  return (
    <Box 
      className={className}
      sx={{ 
        width: '100%',
        maxWidth: '100%',
        boxSizing: 'border-box'
      }}
    >
      {/* Header */}
      <Fade in={true} timeout={500}>
        <Box sx={{ mb: 3 }}>
          <Typography 
            variant={isMobile ? "h6" : "h5"} 
            sx={{ 
              mb: 1,
              fontWeight: 600,
              color: 'text.primary'
            }}
            component="h2"
          >
            Expected Documents
          </Typography>
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ 
              fontSize: isMobile ? '0.8rem' : '0.875rem',
              lineHeight: 1.5
            }}
          >
            Upload documents by dragging them to the appropriate slots below. Guidelines support all programs, while each program has its own matrix documents.
          </Typography>
        </Box>
      </Fade>

      {/* Global Error Summary */}
      {Object.keys(uploadErrors).length > 0 && (
        <Fade in={true}>
          <Alert 
            severity="warning" 
            sx={{ mb: 3 }}
            role="alert"
            aria-live="polite"
            action={
              <Button
                size="small"
                onClick={() => {
                  // Clear all errors
                  setUploadErrors({});
                  setShowErrorDetails({});
                }}
                aria-label="Clear all upload errors"
              >
                Clear All
              </Button>
            }
          >
            <Typography variant="subtitle2" sx={{ fontSize: isMobile ? '0.9rem' : '1rem' }}>
              {Object.keys(uploadErrors).length} document{Object.keys(uploadErrors).length === 1 ? '' : 's'} with upload errors
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5, fontSize: isMobile ? '0.8rem' : '0.875rem' }}>
              Review errors below and retry uploads as needed.
            </Typography>
          </Alert>
        </Fade>
      )}

      {/* Document Slots - Organized by Product/Program Structure */}
      {(() => {
        // Separate documents by level
        const productDocs = expectedDocuments.filter(doc => doc.level === 'product' || !doc.level);
        const programDocs = expectedDocuments.filter(doc => doc.level === 'program');
        
        // Group program documents by program
        const programGroups = programDocs.reduce((groups, doc) => {
          const programKey = doc.programCode || 'unknown';
          if (!groups[programKey]) {
            groups[programKey] = [];
          }
          groups[programKey].push(doc);
          return groups;
        }, {} as Record<string, ExpectedDocument[]>);

        return (
          <>
            {/* Product-Level Documents (Guidelines) */}
            {productDocs.length > 0 && (
              <Box sx={{ mb: 4 }}>
                <Typography 
                  variant="subtitle1" 
                  sx={{ 
                    mb: 2, 
                    fontWeight: 600,
                    color: 'text.primary',
                    borderBottom: '2px solid',
                    borderColor: 'primary.main',
                    pb: 0.5,
                    display: 'inline-block'
                  }}
                >
                  Product Guidelines
                </Typography>
                <Grid 
                  container 
                  spacing={isMobile ? 2 : 3}
                  sx={{
                    width: '100%',
                    margin: 0,
                    '& .MuiGrid-item': {
                      display: 'flex',
                      padding: isMobile ? '8px' : '12px'
                    }
                  }}
                >
                  {productDocs.map((document) => (
                    <Grid 
                      item 
                      xs={12} sm={12} md={6} lg={6} xl={6}
                      key={document.id}
                    >
                      <Box sx={{ width: '100%' }}>
                        <DocumentSlot document={document} />
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}

            {/* Program-Level Documents (Matrices) */}
            {Object.keys(programGroups).length > 0 && (
              <Box>
                <Typography 
                  variant="subtitle1" 
                  sx={{ 
                    mb: 2, 
                    fontWeight: 600,
                    color: 'text.primary',
                    borderBottom: '2px solid',
                    borderColor: 'secondary.main',
                    pb: 0.5,
                    display: 'inline-block'
                  }}
                >
                  Program Matrices
                </Typography>
                
                {Object.entries(programGroups).map(([programCode, docs]) => {
                  const programName = docs[0]?.programName || programCode;
                  
                  return (
                    <Box key={programCode} sx={{ mb: 3 }}>
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          mb: 1.5, 
                          fontWeight: 500,
                          color: 'text.secondary',
                          fontSize: isMobile ? '0.9rem' : '1rem'
                        }}
                      >
                        {programName} ({programCode})
                      </Typography>
                      
                      <Grid 
                        container 
                        spacing={isMobile ? 2 : 3}
                        sx={{
                          width: '100%',
                          margin: 0,
                          mb: 2,
                          '& .MuiGrid-item': {
                            display: 'flex',
                            padding: isMobile ? '8px' : '12px'
                          }
                        }}
                      >
                        {docs.map((document) => {
                          // For program matrices, use more responsive grid
                          const gridSizes = docs.length === 1 
                            ? { xs: 12, sm: 12, md: 6, lg: 6, xl: 6 }
                            : { xs: 12, sm: 6, md: 4, lg: 4, xl: 3 };
                            
                          return (
                            <Grid 
                              item 
                              {...gridSizes}
                              key={document.id}
                            >
                              <Box sx={{ width: '100%' }}>
                                <DocumentSlot document={document} />
                              </Box>
                            </Grid>
                          );
                        })}
                      </Grid>
                    </Box>
                  );
                })}
              </Box>
            )}
          </>
        );
      })()}

      {/* Completion Status */}
      <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
          <Typography variant="subtitle2">Package Completion</Typography>
          <Typography variant="body2" color="text.secondary">
            {expectedDocuments.filter(doc => doc.upload_status !== 'empty').length} of {expectedDocuments.length} documents uploaded
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={(expectedDocuments.filter(doc => doc.upload_status !== 'empty').length / expectedDocuments.length) * 100}
          sx={{ height: 6, borderRadius: 3 }}
        />
      </Box>
    </Box>
  );
};
import React, { useState, useCallback, useEffect } from 'react';
import {
  Button,
  IconButton
} from '@neo4j-ndl/react';
import {
  Box,
  Paper,
  Alert,
  Chip,
  Typography
} from '@mui/material';
import {
  CloudUpload as CloudArrowUpIcon,
  Description as DocumentIcon,
  Folder as FolderIcon,
  Close as XMarkIcon,
  CheckCircle as CheckCircleIcon,
  Warning as ExclamationTriangleIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { PackageSelectionContext, CustomFile } from '../../types';
import { DocumentTypeSlots, ExpectedDocument } from './DocumentTypeSlots';
import { getExpectedDocuments } from '../../services/PackageAPI';

interface ContextualDropZoneProps {
  selectionContext: PackageSelectionContext;
  onFilesUpload: (files: File[], context: PackageSelectionContext) => void;
  onFileUploadWithType: (file: File, expectedDocumentId: string, documentType: string, context: PackageSelectionContext) => void;
  packageModeEnabled: boolean;
  disabled?: boolean;
  className?: string;
}

const DOCUMENT_TYPE_VALIDATIONS = {
  'NQM': {
    acceptedTypes: ['.pdf', '.docx', '.xlsx', '.xls'],
    acceptedMimeTypes: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    recommendedDocuments: ['Guidelines', 'Rate Matrix', 'Underwriting Supplement', 'Program Guide'],
    maxFileSize: 50 * 1024 * 1024 // 50MB
  },
  'RTL': {
    acceptedTypes: ['.pdf', '.docx', '.xlsx', '.xls'],
    acceptedMimeTypes: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    recommendedDocuments: ['Guidelines', 'Rate Matrix', 'DSCR Calculator', 'Rental Analysis'],
    maxFileSize: 50 * 1024 * 1024
  },
  'SBC': {
    acceptedTypes: ['.pdf', '.docx', '.xlsx', '.xls'],
    acceptedMimeTypes: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    recommendedDocuments: ['Guidelines', 'Rate Matrix', 'Property Analysis', 'Loan Programs'],
    maxFileSize: 50 * 1024 * 1024
  },
  'CONV': {
    acceptedTypes: ['.pdf', '.docx', '.xlsx', '.xls'],
    acceptedMimeTypes: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    recommendedDocuments: ['Guidelines', 'Rate Matrix', 'DU/LP Findings', 'Overlays'],
    maxFileSize: 50 * 1024 * 1024
  }
};

export const ContextualDropZone: React.FC<ContextualDropZoneProps> = ({
  selectionContext,
  onFilesUpload,
  onFileUploadWithType,
  packageModeEnabled,
  disabled = false,
  className
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [expectedDocuments, setExpectedDocuments] = useState<ExpectedDocument[]>([]);
  const [loadingExpectedDocs, setLoadingExpectedDocs] = useState(false);
  const [useDocumentSlots, setUseDocumentSlots] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const maxFetchRetries = 3;

  // Fetch expected documents when product is selected
  useEffect(() => {
    const fetchExpectedDocuments = async (attempt = 0) => {
      if (packageModeEnabled && 
          selectionContext.selectionType === 'product' && 
          selectionContext.selectedProduct?.id) {
        
        setLoadingExpectedDocs(true);
        setFetchError(null);
        
        try {
          const response = await getExpectedDocuments(selectionContext.selectedProduct.id);
          if (response.status === 'Success' && response.data?.expected_documents) {
            setExpectedDocuments(response.data.expected_documents);
            setUseDocumentSlots(response.data.expected_documents.length > 0);
            setRetryCount(0);
            setFetchError(null);
          } else {
            throw new Error(response.message || 'No expected documents returned');
          }
        } catch (error) {
          console.error('Error fetching expected documents:', error);
          
          let errorMessage = 'Failed to load document requirements';
          let shouldRetry = false;
          
          if (error instanceof Error) {
            if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
              errorMessage = 'Network connection error. Please check your internet connection.';
              shouldRetry = true;
            } else if (error.message.includes('404')) {
              errorMessage = 'No document templates found for this product.';
              shouldRetry = false;
            } else if (error.message.includes('401') || error.message.includes('403')) {
              errorMessage = 'You do not have permission to access this product.';
              shouldRetry = false;
            } else if (error.message.includes('500') || error.message.includes('502') || error.message.includes('503')) {
              errorMessage = 'Server error. Please try again in a moment.';
              shouldRetry = true;
            } else {
              errorMessage = error.message || errorMessage;
              shouldRetry = true;
            }
          }
          
          setFetchError(errorMessage);
          setExpectedDocuments([]);
          setUseDocumentSlots(false);
          
          // Auto-retry for network/server errors
          if (shouldRetry && attempt < maxFetchRetries) {
            const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
            setTimeout(() => {
              setRetryCount(attempt + 1);
              fetchExpectedDocuments(attempt + 1);
            }, delay);
          } else {
            // Fall back to standard upload mode
            setUseDocumentSlots(false);
          }
        } finally {
          setLoadingExpectedDocs(false);
        }
      } else {
        setExpectedDocuments([]);
        setUseDocumentSlots(false);
        setFetchError(null);
      }
    };

    fetchExpectedDocuments();
  }, [packageModeEnabled, selectionContext.selectionType, selectionContext.selectedProduct?.id]);

  // Handle file upload with pre-selected document type
  const handleFileUploadWithType = useCallback(async (file: File, expectedDocumentId: string, documentType: string) => {
    try {
      // Call the upload handler
      onFileUploadWithType(file, expectedDocumentId, documentType, selectionContext);
      
      // Refresh expected documents after upload completes
      setTimeout(async () => {
        if (selectionContext.selectedProduct?.id) {
          try {
            const response = await getExpectedDocuments(selectionContext.selectedProduct.id);
            if (response.status === 'Success' && response.data?.expected_documents) {
              setExpectedDocuments(response.data.expected_documents);
              console.log('✅ Refreshed expected documents after upload');
              
              // Find the uploaded document and update its status to "uploaded"
              const uploadedDoc = response.data.expected_documents.find(doc => 
                doc.id === expectedDocumentId && doc.upload_status === 'uploaded'
              );
              
              if (uploadedDoc) {
                console.log(`✅ Document ${file.name} confirmed as uploaded in backend`);
              }
            }
          } catch (error) {
            console.error('Failed to refresh expected documents:', error);
            // If refresh fails, at least update the local state to show upload completion
            setExpectedDocuments(prev => prev.map(doc => 
              doc.id === expectedDocumentId 
                ? { 
                    ...doc, 
                    upload_status: 'uploaded',
                    uploaded_file: {
                      fileName: file.name,
                      fileSize: file.size,
                      uploadDate: new Date().toISOString(),
                      processingStatus: 'completed'
                    }
                  }
                : doc
            ));
          }
        }
      }, 1500); // 1.5 second delay to allow backend processing
      
    } catch (error) {
      console.error('Upload error:', error);
    }
  }, [onFileUploadWithType, selectionContext]);

  // Manual retry for expected documents fetch
  const handleRetryFetch = useCallback(() => {
    if (selectionContext.selectedProduct?.id) {
      const fetchExpectedDocuments = async () => {
        setLoadingExpectedDocs(true);
        setFetchError(null);
        setRetryCount(0);
        
        try {
          const response = await getExpectedDocuments(selectionContext.selectedProduct.id);
          if (response.status === 'Success' && response.data?.expected_documents) {
            setExpectedDocuments(response.data.expected_documents);
            setUseDocumentSlots(response.data.expected_documents.length > 0);
            setFetchError(null);
          } else {
            throw new Error(response.message || 'No expected documents returned');
          }
        } catch (error) {
          console.error('Retry failed:', error);
          setFetchError(error instanceof Error ? error.message : 'Retry failed');
          setUseDocumentSlots(false);
        } finally {
          setLoadingExpectedDocs(false);
        }
      };
      
      fetchExpectedDocuments();
    }
  }, [selectionContext.selectedProduct?.id]);

  const getValidationRules = () => {
    if (!packageModeEnabled || !selectionContext.selectedCategory) {
      return {
        acceptedTypes: ['.pdf', '.docx', '.xlsx', '.xls', '.txt', '.csv'],
        acceptedMimeTypes: {
          'application/pdf': ['.pdf'],
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
          'application/vnd.ms-excel': ['.xls'],
          'text/plain': ['.txt'],
          'text/csv': ['.csv']
        },
        maxFileSize: 100 * 1024 * 1024 // 100MB for standard mode
      };
    }

    return DOCUMENT_TYPE_VALIDATIONS[selectionContext.selectedCategory.type] || DOCUMENT_TYPE_VALIDATIONS['NQM'];
  };

  const validationRules = getValidationRules();

  const validateFile = useCallback((file: File) => {
    const errors: string[] = [];
    
    // Check file size
    if (file.size > validationRules.maxFileSize) {
      errors.push(`File size exceeds ${validationRules.maxFileSize / (1024 * 1024)}MB limit`);
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!validationRules.acceptedTypes.includes(fileExtension)) {
      errors.push(`File type ${fileExtension} not accepted for this category`);
    }

    return errors;
  }, [validationRules]);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setDragActive(false);

    if (rejectedFiles.length > 0) {
      console.warn('Some files were rejected:', rejectedFiles);
      return;
    }

    // Validate files
    const validatedFiles: File[] = [];
    const validationErrors: Record<string, string[]> = {};

    acceptedFiles.forEach(file => {
      const errors = validateFile(file);
      if (errors.length === 0) {
        validatedFiles.push(file);
      } else {
        validationErrors[file.name] = errors;
      }
    });

    if (Object.keys(validationErrors).length > 0) {
      // Show validation errors
      Object.entries(validationErrors).forEach(([fileName, errors]) => {
        console.error(`Validation failed for ${fileName}:`, errors);
      });
      return;
    }

    if (validatedFiles.length > 0) {
      onFilesUpload(validatedFiles, selectionContext);
    }
  }, [validateFile, onFilesUpload, selectionContext]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false),
    accept: validationRules.acceptedMimeTypes,
    disabled: disabled || (!packageModeEnabled && selectionContext.selectionType === 'none'),
    multiple: true
  });

  const getContextMessage = () => {
    if (!packageModeEnabled) {
      return {
        title: 'Standard File Upload',
        subtitle: 'Upload documents for individual processing',
        context: '',
        status: 'info' as const
      };
    }

    if (selectionContext.selectionType === 'none') {
      return {
        title: 'Select a Product for Upload',
        subtitle: 'Choose a category and product to upload documents',
        context: 'Create a category and product first',
        status: 'warning' as const
      };
    }

    if (selectionContext.selectionType === 'category') {
      return {
        title: 'Select a Product',
        subtitle: 'Choose a product within this category to upload documents',
        context: `Category: ${selectionContext.selectedCategory?.name}`,
        status: 'warning' as const
      };
    }

    if (selectionContext.selectionType === 'product') {
      return {
        title: 'Upload Documents',
        subtitle: 'Drop files here or click to browse',
        context: `${selectionContext.selectedCategory?.name} → ${selectionContext.selectedProduct?.name}`,
        status: 'success' as const
      };
    }

    return {
      title: 'Ready for Upload',
      subtitle: 'Drop files here or click to browse',
      context: '',
      status: 'info' as const
    };
  };

  const contextMessage = getContextMessage();
  const canUpload = !disabled && (
    !packageModeEnabled || 
    selectionContext.selectionType === 'product' || 
    selectionContext.selectionType === 'file'
  );

  return (
    <Box 
      className={className}
      sx={{ 
        width: '100%', 
        maxWidth: '100%',
        boxSizing: 'border-box'
      }}
    >

      {/* Document Type Slots (Package Mode with Expected Documents) */}
      {useDocumentSlots && !loadingExpectedDocs && (
        <Box sx={{ width: '100%', maxWidth: '100%' }}>
          <DocumentTypeSlots
            expectedDocuments={expectedDocuments}
            onFileUpload={handleFileUploadWithType}
            uploadProgress={uploadProgress}
            disabled={disabled}
            loading={loadingExpectedDocs}
            onError={(uploadError) => {
              console.error('Upload error:', uploadError);
              // Here you could also send to error tracking service
            }}
            onRetry={(documentId, file) => {
              const document = expectedDocuments.find(d => d.id === documentId);
              if (document) {
                handleFileUploadWithType(file, documentId, document.document_type);
              }
            }}
            onUploadStart={(documentId, file) => {
              // Optimistically update the expected documents state
              setExpectedDocuments(prev => prev.map(doc => 
                doc.id === documentId 
                  ? { 
                      ...doc, 
                      upload_status: 'processing',
                      uploaded_file: {
                        fileName: file.name,
                        fileSize: file.size,
                        uploadDate: new Date().toISOString(),
                        processingStatus: 'uploading'
                      }
                    }
                  : doc
              ));
            }}
            maxRetries={3}
          />
        </Box>
      )}

      {/* Loading State for Expected Documents */}
      {loadingExpectedDocs && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            Loading expected documents...
            {retryCount > 0 && (
              <Typography variant="caption" sx={{ display: 'block', mt: 1 }} color="warning.main">
                Retry attempt {retryCount}/{maxFetchRetries}
              </Typography>
            )}
          </Typography>
        </Box>
      )}

      {/* Error State for Expected Documents */}
      {fetchError && !loadingExpectedDocs && (
        <Alert 
          severity="warning" 
          sx={{ mb: 2 }}
          action={
            <Button
              size="small"
              onClick={handleRetryFetch}
              variant="outlined"
              color="warning"
            >
              Retry
            </Button>
          }
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Failed to load document requirements
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            {fetchError}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            Using standard upload mode instead. You can manually set document types after upload.
          </Typography>
        </Alert>
      )}

      {/* Standard Drop Zone (Non-package mode or no expected documents) */}
      {!useDocumentSlots && !loadingExpectedDocs && (
        <>
          {/* Main Drop Zone */}
          <Paper
        {...getRootProps()}
        sx={{
          p: 3,
          border: '2px dashed',
          borderColor: dragActive 
            ? 'primary.main' 
            : canUpload 
              ? 'divider' 
              : 'action.disabled',
          borderRadius: 2,
          textAlign: 'center',
          cursor: canUpload ? 'pointer' : 'not-allowed',
          bgcolor: dragActive 
            ? 'rgba(var(--theme-palette-primary-bg-strong), 0.08)' 
            : canUpload 
              ? 'background.paper' 
              : 'action.disabledBackground',
          opacity: canUpload ? 1 : 0.6,
          transition: 'all 0.2s ease',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          minHeight: '200px',
          '&:hover': canUpload ? {
            borderColor: 'primary.main',
            bgcolor: 'rgba(var(--theme-palette-primary-bg-strong), 0.08)'
          } : {}
        }}
      >
        <input {...getInputProps()} disabled={!canUpload} />
        
        <Box display="flex" flexDirection="column" alignItems="center" gap={1.5} sx={{ py: 2 }}>
          {/* Icon */}
          <CloudArrowUpIcon 
            style={{ 
              fontSize: 32, 
              color: canUpload 
                ? 'rgb(var(--theme-palette-primary-bg-strong))' 
                : 'rgb(var(--theme-palette-neutral-text-weak))',
              width: '32px',
              height: '32px'
            }} 
          />
          
          {/* Main Message */}
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="subtitle1" color={canUpload ? 'text.primary' : 'text.disabled'} sx={{ fontWeight: 600 }}>
              {contextMessage.title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {contextMessage.subtitle}
            </Typography>
          </Box>

          {/* Accepted File Types */}
          {canUpload && (
            <Box display="flex" flexWrap="wrap" gap={0.5} justifyContent="center" sx={{ maxWidth: '100%' }}>
              {validationRules.acceptedTypes.map((type) => (
                <Chip key={type} label={type.toUpperCase()} size="small" variant="outlined" />
              ))}
            </Box>
          )}

          {/* Recommended Documents */}
          {packageModeEnabled && selectionContext.selectedCategory && canUpload && (
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                Recommended document types:
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={0.5} justifyContent="center" sx={{ maxWidth: '100%' }}>
                {DOCUMENT_TYPE_VALIDATIONS[selectionContext.selectedCategory.type]?.recommendedDocuments.map((doc) => (
                  <Chip key={doc} label={doc} size="small" color="primary" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}

          {/* File Size Limit */}
          <Typography variant="caption" color="text.secondary">
            Maximum file size: {validationRules.maxFileSize / (1024 * 1024)}MB
          </Typography>
        </Box>
      </Paper>

      {/* Upload Progress (if files are being uploaded) */}
      {Object.keys(uploadProgress).length > 0 && (
        <Box mt={2}>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>Uploading files...</Typography>
          {Object.entries(uploadProgress).map(([fileName, progress]) => (
            <Box key={fileName} mb={1}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                <Typography variant="body2">{fileName}</Typography>
                <Typography variant="body2">{progress}%</Typography>
              </Box>
              <Box 
                sx={{ 
                  width: '100%', 
                  height: 4, 
                  bgcolor: 'action.hover', 
                  borderRadius: 1 
                }}
              >
                <Box
                  sx={{
                    width: `${progress}%`,
                    height: '100%',
                    bgcolor: 'primary.main',
                    borderRadius: 1,
                    transition: 'width 0.3s ease'
                  }}
                />
              </Box>
            </Box>
          ))}
        </Box>
      )}
        </>
      )}
    </Box>
  );
};
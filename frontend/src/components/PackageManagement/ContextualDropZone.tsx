import React, { useState, useCallback } from 'react';
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
  CloudArrowUpIcon,
  DocumentIcon,
  FolderIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useDropzone } from 'react-dropzone';
import { PackageSelectionContext, CustomFile } from '../../types';

interface ContextualDropZoneProps {
  selectionContext: PackageSelectionContext;
  onFilesUpload: (files: File[], context: PackageSelectionContext) => void;
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
  packageModeEnabled,
  disabled = false,
  className
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});

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
    <Box className={className}>
      {/* Upload Context Display */}
      {packageModeEnabled && selectionContext.selectionType !== 'none' && (
        <Box mb={2}>
          <Alert severity={contextMessage.status} variant="outlined">
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="subtitle1">{contextMessage.title}</Typography>
                {contextMessage.context && (
                  <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                    <FolderIcon className="w-4 h-4" />
                    <Typography variant="body2">{contextMessage.context}</Typography>
                  </Box>
                )}
              </Box>
              {contextMessage.status === 'success' && (
                <CheckCircleIcon className="w-5 h-5 text-green-500" />
              )}
            </Box>
          </Alert>
        </Box>
      )}

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
    </Box>
  );
};
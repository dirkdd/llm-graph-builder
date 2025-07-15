# Validation and Error Handling

## Overview
Comprehensive validation and error handling strategy for the document type slots interface, ensuring robust operation and excellent user experience.

## Current Implementation Status: 🟡 PARTIALLY IMPLEMENTED

### **✅ Completed**
- Basic file type and size validation in DocumentTypeSlots component
- Backend validation rules for different document types
- API error response structure

### **⚠️ Needs Implementation**
- Comprehensive error handling for network failures
- Retry mechanisms for failed uploads
- User-friendly error messages and recovery options
- Edge case handling (network timeouts, large files, etc.)

## Validation Strategy

### **1. Frontend Validation (Pre-Upload)** ✅
**File**: `frontend/src/components/PackageManagement/DocumentTypeSlots.tsx`

**Current Implementation**:
```typescript
const validateFile = useCallback((file: File, documentType: string) => {
  const errors: string[] = [];
  const rules = validationRules[documentType];
  
  // File size validation
  if (file.size > rules.max_file_size) {
    errors.push(`File size exceeds ${rules.max_file_size / (1024 * 1024)}MB limit`);
  }
  
  // File type validation
  const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!rules.accepted_types.includes(fileExtension)) {
    errors.push(`File type ${fileExtension} not accepted for ${documentType} documents`);
  }
  
  return errors;
}, []);
```

**Document Type Specific Rules**:
```typescript
const validation_rules = {
  'Guidelines': {
    accepted_types: ['.pdf', '.docx'],
    accepted_mime_types: ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    max_file_size: 50 * 1024 * 1024,  // 50MB
    description: 'Underwriting guidelines and policy documents'
  },
  'Matrix': {
    accepted_types: ['.pdf', '.xlsx', '.xls', '.csv'],
    accepted_mime_types: ['application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'text/csv'],
    max_file_size: 25 * 1024 * 1024,  // 25MB
    description: 'Rate matrices and pricing tables'
  }
  // ... other document types
};
```

### **2. Backend Validation (Server-Side)** ✅
**File**: `backend/src/graphDB_dataAccess.py`

**Current Implementation**:
```python
def _get_validation_rules_for_document_type(self, document_type: str) -> dict:
    """Get validation rules based on document type"""
    
    validation_rules = {
        'Guidelines': {
            'accepted_types': ['.pdf', '.docx'],
            'max_file_size': 50 * 1024 * 1024,
            'content_validation': 'guidelines_structure'
        },
        'Matrix': {
            'accepted_types': ['.pdf', '.xlsx', '.xls', '.csv'],
            'max_file_size': 25 * 1024 * 1024,
            'content_validation': 'matrix_structure'
        }
        # ... other types
    }
    
    return validation_rules.get(document_type, validation_rules['Other'])
```

## Error Handling Requirements

### **1. Network Error Handling** ❌ NEEDS IMPLEMENTATION

**Expected Documents Fetch Failure**:
```typescript
// TODO: Implement comprehensive error handling
const fetchExpectedDocuments = async () => {
  setLoadingExpectedDocs(true);
  try {
    const response = await getExpectedDocuments(selectionContext.selectedProduct.id);
    if (response.status === 'Success' && response.data?.expected_documents) {
      setExpectedDocuments(response.data.expected_documents);
      setUseDocumentSlots(response.data.expected_documents.length > 0);
    } else {
      // TODO: Handle API success but no data
      throw new Error('No expected documents returned');
    }
  } catch (error) {
    console.error('Error fetching expected documents:', error);
    
    // TODO: Implement proper error handling
    // - Show user-friendly error message
    // - Provide retry option
    // - Fall back to standard upload gracefully
    // - Log error for monitoring
    
    setExpectedDocuments([]);
    setUseDocumentSlots(false);
  } finally {
    setLoadingExpectedDocs(false);
  }
};
```

**Required Error Handling**:
```typescript
// TODO: Implement these error handling scenarios
const handleExpectedDocumentsError = (error: Error) => {
  if (error.name === 'NetworkError') {
    showErrorToast('Unable to connect to server. Please check your internet connection.');
    // Offer retry button
  } else if (error.message.includes('404')) {
    showWarningToast('No document templates found for this product. Using standard upload.');
    // Gracefully fall back to standard dropzone
  } else if (error.message.includes('401') || error.message.includes('403')) {
    showErrorToast('You do not have permission to access this product.');
    // Redirect to login or show permission error
  } else {
    showErrorToast('Failed to load document requirements. Please try again.');
    // Show retry option
  }
};
```

### **2. Upload Error Handling** ❌ NEEDS IMPLEMENTATION

**File Upload Failure**:
```typescript
// TODO: Implement comprehensive upload error handling
const handleUploadError = useCallback((error: Error, file: File, documentType: string) => {
  // Reset upload progress
  setUploadProgress(prev => {
    const updated = { ...prev };
    delete updated[file.name];
    return updated;
  });
  
  // TODO: Implement specific error handling
  if (error.message.includes('413')) {
    showErrorToast(`File ${file.name} is too large. Maximum size for ${documentType} is ${getMaxSizeForType(documentType)}`);
  } else if (error.message.includes('415')) {
    showErrorToast(`File type not supported for ${documentType}. Accepted types: ${getAcceptedTypesForType(documentType).join(', ')}`);
  } else if (error.message.includes('timeout')) {
    showErrorToast(`Upload timed out for ${file.name}. Please try again.`);
    // Show retry option
  } else if (error.message.includes('network')) {
    showErrorToast('Network error during upload. Please check your connection and try again.');
    // Show retry option
  } else {
    showErrorToast(`Failed to upload ${file.name}: ${error.message}`);
  }
}, []);
```

### **3. Validation Error Display** ❌ NEEDS IMPLEMENTATION

**User-Friendly Validation Messages**:
```typescript
// TODO: Implement better validation error display
const ValidationErrorDisplay: React.FC<{ errors: string[]; documentType: string }> = ({ errors, documentType }) => {
  return (
    <Alert severity="error" sx={{ mt: 1 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Cannot upload to {documentType} slot:
      </Typography>
      <ul style={{ margin: 0, paddingLeft: 20 }}>
        {errors.map((error, index) => (
          <li key={index}>{error}</li>
        ))}
      </ul>
      <Box sx={{ mt: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Accepted types: {getAcceptedTypesForType(documentType).join(', ')}
        </Typography>
      </Box>
    </Alert>
  );
};
```

## Retry Mechanisms

### **1. Automatic Retry with Exponential Backoff** ❌ NEEDS IMPLEMENTATION

```typescript
// TODO: Implement retry mechanism
const retryWithBackoff = async (
  operation: () => Promise<any>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<any> => {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (attempt === maxRetries - 1) {
        throw error; // Last attempt, re-throw error
      }
      
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
};

// Usage for expected documents fetch
const fetchExpectedDocumentsWithRetry = useCallback(async () => {
  try {
    const response = await retryWithBackoff(
      () => getExpectedDocuments(selectionContext.selectedProduct.id),
      3,
      1000
    );
    // Handle success
  } catch (error) {
    // Handle final failure after all retries
    handleExpectedDocumentsError(error);
  }
}, [selectionContext.selectedProduct?.id]);
```

### **2. Manual Retry Options** ❌ NEEDS IMPLEMENTATION

```typescript
// TODO: Implement manual retry UI
const RetryButton: React.FC<{ onRetry: () => void; isRetrying: boolean }> = ({ onRetry, isRetrying }) => {
  return (
    <Button
      variant="outlined"
      color="primary"
      onClick={onRetry}
      disabled={isRetrying}
      startIcon={isRetrying ? <CircularProgress size={16} /> : <RefreshIcon />}
      sx={{ mt: 1 }}
    >
      {isRetrying ? 'Retrying...' : 'Try Again'}
    </Button>
  );
};
```

## Edge Cases and Special Scenarios

### **1. Large File Uploads** ❌ NEEDS IMPLEMENTATION

```typescript
// TODO: Implement large file upload handling
const handleLargeFile = (file: File, documentType: string) => {
  const maxSize = getMaxSizeForType(documentType);
  
  if (file.size > maxSize) {
    // Show specific error with file size recommendations
    showErrorToast(
      `File too large: ${formatFileSize(file.size)}. ` +
      `Maximum for ${documentType}: ${formatFileSize(maxSize)}. ` +
      `Consider compressing your file or splitting it into smaller documents.`
    );
    return false;
  }
  
  if (file.size > 10 * 1024 * 1024) { // 10MB
    // Show progress indicator for large files
    showInfoToast(`Uploading large file (${formatFileSize(file.size)}). This may take a moment...`);
  }
  
  return true;
};
```

### **2. Concurrent Upload Limits** ❌ NEEDS IMPLEMENTATION

```typescript
// TODO: Implement concurrent upload management
const MAX_CONCURRENT_UPLOADS = 3;
const [activeUploads, setActiveUploads] = useState<Set<string>>(new Set());

const manageUploadQueue = useCallback((fileId: string, action: 'start' | 'complete') => {
  setActiveUploads(prev => {
    const updated = new Set(prev);
    if (action === 'start') {
      if (updated.size >= MAX_CONCURRENT_UPLOADS) {
        showWarningToast('Maximum concurrent uploads reached. Please wait for current uploads to complete.');
        return prev;
      }
      updated.add(fileId);
    } else {
      updated.delete(fileId);
    }
    return updated;
  });
}, []);
```

### **3. Browser Compatibility** ❌ NEEDS IMPLEMENTATION

```typescript
// TODO: Implement browser compatibility checks
const checkBrowserCompatibility = () => {
  const requiredFeatures = {
    'FileReader': typeof FileReader !== 'undefined',
    'FormData': typeof FormData !== 'undefined',
    'fetch': typeof fetch !== 'undefined',
    'dragAndDrop': 'draggable' in document.createElement('div')
  };
  
  const missingFeatures = Object.entries(requiredFeatures)
    .filter(([, supported]) => !supported)
    .map(([feature]) => feature);
  
  if (missingFeatures.length > 0) {
    showErrorToast(
      `Your browser doesn't support required features: ${missingFeatures.join(', ')}. ` +
      `Please upgrade to a modern browser.`
    );
    return false;
  }
  
  return true;
};
```

## User Experience Improvements

### **1. Progressive Enhancement** ❌ NEEDS IMPLEMENTATION

```typescript
// TODO: Implement progressive enhancement
const DocumentTypeSlotsWithFallback: React.FC<DocumentTypeSlotsProps> = (props) => {
  const [hasJavaScript] = useState(() => typeof window !== 'undefined');
  const [supportsDragDrop] = useState(() => 
    hasJavaScript && 'draggable' in document.createElement('div')
  );
  
  if (!hasJavaScript) {
    return <StandardFileInput {...props} />;
  }
  
  if (!supportsDragDrop) {
    return <ClickToUploadSlots {...props} />;
  }
  
  return <DocumentTypeSlots {...props} />;
};
```

### **2. Accessibility Improvements** ❌ NEEDS IMPLEMENTATION

```typescript
// TODO: Implement accessibility features
const AccessibleDocumentSlot: React.FC<{ document: ExpectedDocument }> = ({ document }) => {
  return (
    <Paper
      role="button"
      tabIndex={0}
      aria-label={`Upload ${document.document_type} document. Required: ${document.is_required}. Status: ${document.upload_status}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          // Trigger file picker
          fileInputRef.current?.click();
        }
      }}
      // ... other props
    >
      {/* Slot content */}
    </Paper>
  );
};
```

## Implementation Priority

### **High Priority (Must Have)**
1. ❌ Network error handling with graceful fallback
2. ❌ Upload failure handling with retry options
3. ❌ User-friendly error messages
4. ❌ Basic retry mechanisms

### **Medium Priority (Should Have)**
1. ❌ Large file upload handling
2. ❌ Concurrent upload management
3. ❌ Progress indicators for long operations
4. ❌ Accessibility improvements

### **Low Priority (Nice to Have)**
1. ❌ Advanced retry strategies
2. ❌ Browser compatibility warnings
3. ❌ Offline handling
4. ❌ Performance monitoring

## Testing Strategy

### **Error Scenario Tests**
1. ❌ Network disconnection during fetch
2. ❌ API server errors (500, 503)
3. ❌ Invalid file types
4. ❌ File size exceeding limits
5. ❌ Upload interruption
6. ❌ Concurrent upload limits
7. ❌ Browser compatibility edge cases

### **Recovery Tests**
1. ❌ Automatic retry success
2. ❌ Manual retry functionality
3. ❌ Graceful fallback to standard upload
4. ❌ Error message clarity and actionability

## Monitoring and Logging

### **Error Tracking** ❌ NEEDS IMPLEMENTATION
```typescript
// TODO: Implement error tracking
const logError = (error: Error, context: string, metadata?: any) => {
  // Send to error tracking service (e.g., Sentry, LogRocket)
  console.error(`[${context}]`, error, metadata);
  
  // Track user-facing errors separately
  if (context.includes('user-facing')) {
    analytics.track('Upload Error', {
      error_type: error.name,
      error_message: error.message,
      context,
      ...metadata
    });
  }
};
```

The validation and error handling implementation is currently **incomplete** and requires significant work to be production-ready. The basic validation is in place, but comprehensive error handling, retry mechanisms, and user experience improvements are still needed.
# Task 21: Create Package API Services - READY

## Overview
**Estimated Time**: 2 hours  
**Priority**: Critical  
**Dependencies**: Task 6  
**Phase**: 1.5 Frontend Integration

## Description
Implement frontend API service layer for package management that integrates with the existing backend package endpoints. Create type-safe API services following the established FormData patterns used throughout the application.

## Backend API Analysis

### ✅ Available Package Endpoints (Task 6)
- **POST** `/packages` - Create new document package
- **GET** `/packages/{package_id}` - Retrieve specific package 
- **GET** `/packages` - List packages with filtering
- **PUT** `/packages/{package_id}` - Update existing package
- **DELETE** `/packages/{package_id}` - Delete package
- **POST** `/packages/{package_id}/clone` - Clone package with modifications
- **GET** `/packages/{package_id}/versions` - Get version history
- **POST** `/packages/{package_id}/rollback` - Rollback to previous version
- **GET** `/packages/{package_id}/diff` - Compare package versions
- **POST** `/packages/validate` - Validate configuration without creating

### ✅ Existing Frontend Patterns
- **FormData API**: `services/CommonAPI.ts` with `apiCall` function
- **Response Format**: Standardized response with `create_api_response`
- **Error Handling**: Comprehensive error handling with retry logic
- **Type Safety**: Complete TypeScript integration

## Acceptance Criteria

### Core Implementation
- [ ] PackageAPI.ts with all CRUD operations
- [ ] createDocumentPackage function
- [ ] getDocumentPackages function
- [ ] applyPackageToFiles function
- [ ] Proper TypeScript typing
- [ ] Error handling and retry logic
- [ ] Tests for all API functions

### Technical Requirements

#### Service Architecture
```
services/
├── PackageAPI.ts              # Main package API service
├── PackageTypes.ts            # TypeScript type definitions
└── PackageUtils.ts            # Utility functions for transformations
```

#### API Service Functions
```typescript
// Core CRUD operations
export const createDocumentPackage = (packageData: CreatePackageRequest): Promise<PackageResponse>
export const getDocumentPackage = (packageId: string): Promise<PackageResponse>
export const getDocumentPackages = (filters?: PackageFilters): Promise<PackagesListResponse>
export const updateDocumentPackage = (packageId: string, updates: UpdatePackageRequest): Promise<PackageResponse>
export const deleteDocumentPackage = (packageId: string): Promise<void>

// Advanced operations
export const cloneDocumentPackage = (packageId: string, cloneData: ClonePackageRequest): Promise<PackageResponse>
export const getPackageVersions = (packageId: string): Promise<VersionHistoryResponse>
export const rollbackPackageVersion = (packageId: string, rollbackData: RollbackRequest): Promise<PackageResponse>
export const comparePackageVersions = (packageId: string, compareData: CompareRequest): Promise<DiffResponse>
export const validatePackageConfig = (config: ValidateConfigRequest): Promise<ValidationResponse>

// File integration
export const applyPackageToFiles = (packageId: string, fileIds: string[]): Promise<ApplyResponse>
```

### Type Definitions (PackageTypes.ts)

#### Request Types
```typescript
interface CreatePackageRequest {
  package_name: string;
  category: 'NQM' | 'RTL' | 'SBC' | 'CONV';
  description?: string;
  template?: string;
  documents?: DocumentDefinition[];
  relationships?: PackageRelationship[];
  customizations?: Record<string, any>;
  tenant_id?: string;
}

interface UpdatePackageRequest {
  package_name?: string;
  description?: string;
  status?: 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
  documents?: DocumentDefinition[];
  relationships?: PackageRelationship[];
  customizations?: Record<string, any>;
}

interface PackageFilters {
  tenant_id?: string;
  category?: 'NQM' | 'RTL' | 'SBC' | 'CONV';
  status?: 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
  search?: string;
  limit?: number;
  offset?: number;
}

interface ClonePackageRequest {
  new_name: string;
  modifications?: Record<string, any>;
  tenant_id?: string;
}
```

#### Response Types
```typescript
interface PackageResponse {
  success: boolean;
  data: {
    package_id: string;
    package_name: string;
    tenant_id: string;
    category: string;
    version: string;
    status: string;
    created_by: string;
    template_type: string;
    created_at: string;
    updated_at: string;
    documents: DocumentDefinition[];
    relationships: PackageRelationship[];
    template_mappings: Record<string, any>;
    validation_rules: Record<string, any>;
  };
  message: string;
  error?: string;
}

interface PackagesListResponse {
  success: boolean;
  data: {
    packages: PackageListItem[];
    total_count: number;
    filters_applied: PackageFilters;
  };
  message: string;
  error?: string;
}

interface ValidationResponse {
  success: boolean;
  data: {
    valid: boolean;
    validation_errors: string[];
    package_name: string;
    category: string;
    document_count: number;
    relationship_count: number;
  };
  message: string;
  error?: string;
}
```

#### Entity Types
```typescript
interface DocumentDefinition {
  document_id: string;
  name: string;
  description?: string;
  required: boolean;
  document_type: string;
  validation_rules: Record<string, any>;
  processing_config: Record<string, any>;
  metadata: Record<string, any>;
}

interface PackageRelationship {
  relationship_id: string;
  name: string;
  description?: string;
  source_document_id: string;
  target_document_id: string;
  relationship_type: string;
  validation_rules: Record<string, any>;
  metadata: Record<string, any>;
}
```

### Implementation Strategy

#### Phase 1: Core API Functions
```typescript
// PackageAPI.ts - Core implementation
import { apiCall } from './CommonAPI';
import { 
  CreatePackageRequest, 
  PackageResponse, 
  PackageFilters,
  PackagesListResponse 
} from './PackageTypes';

export const createDocumentPackage = async (
  packageData: CreatePackageRequest
): Promise<PackageResponse> => {
  try {
    const formParams = {
      package_name: packageData.package_name,
      category: packageData.category,
      description: packageData.description || '',
      template: packageData.template || '',
      documents: packageData.documents ? JSON.stringify(packageData.documents) : '',
      relationships: packageData.relationships ? JSON.stringify(packageData.relationships) : '',
      customizations: packageData.customizations ? JSON.stringify(packageData.customizations) : '',
      tenant_id: packageData.tenant_id || ''
    };
    
    return await apiCall('/packages', 'POST', formParams);
  } catch (error) {
    console.error('Error creating package:', error);
    throw error;
  }
};
```

#### Phase 2: Advanced Operations
```typescript
export const cloneDocumentPackage = async (
  packageId: string,
  cloneData: ClonePackageRequest
): Promise<PackageResponse> => {
  try {
    const formParams = {
      new_name: cloneData.new_name,
      modifications: cloneData.modifications ? JSON.stringify(cloneData.modifications) : '',
      tenant_id: cloneData.tenant_id || ''
    };
    
    return await apiCall(`/packages/${packageId}/clone`, 'POST', formParams);
  } catch (error) {
    console.error('Error cloning package:', error);
    throw error;
  }
};
```

#### Phase 3: Utility Functions
```typescript
// PackageUtils.ts - Helper functions
export const transformPackageForDisplay = (packageData: any) => {
  return {
    id: packageData.package_id,
    name: packageData.package_name,
    category: packageData.category,
    version: packageData.version,
    status: packageData.status,
    createdAt: new Date(packageData.created_at),
    updatedAt: new Date(packageData.updated_at),
    documentCount: packageData.documents?.length || 0,
    relationshipCount: packageData.relationships?.length || 0
  };
};

export const validatePackageData = (packageData: CreatePackageRequest): string[] => {
  const errors: string[] = [];
  
  if (!packageData.package_name || packageData.package_name.trim().length < 3) {
    errors.push('Package name must be at least 3 characters long');
  }
  
  if (!packageData.category) {
    errors.push('Package category is required');
  }
  
  return errors;
};
```

### Error Handling Strategy

#### Comprehensive Error Handling
```typescript
interface APIError {
  message: string;
  error?: string;
  status?: number;
  retryable?: boolean;
}

export const handlePackageAPIError = (error: any): APIError => {
  if (error.response) {
    // Server responded with error status
    return {
      message: error.response.data?.message || 'Server error occurred',
      error: error.response.data?.error || 'Unknown server error',
      status: error.response.status,
      retryable: error.response.status >= 500 && error.response.status < 600
    };
  } else if (error.request) {
    // Network error
    return {
      message: 'Network error - please check your connection',
      error: 'Network error',
      retryable: true
    };
  } else {
    // Other error
    return {
      message: 'An unexpected error occurred',
      error: error.message || 'Unknown error',
      retryable: false
    };
  }
};
```

#### Retry Logic Implementation
```typescript
export const apiCallWithRetry = async (
  url: string,
  method: string,
  params: any,
  maxRetries: number = 3
): Promise<any> => {
  let lastError: any;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall(url, method, params);
    } catch (error) {
      lastError = error;
      const apiError = handlePackageAPIError(error);
      
      if (!apiError.retryable || attempt === maxRetries) {
        throw error;
      }
      
      // Exponential backoff
      const delay = Math.pow(2, attempt) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
};
```

### Integration with Existing Context

#### File Context Integration
```typescript
// Integration with UsersFiles context
export const applyPackageToFiles = async (
  packageId: string, 
  fileIds: string[]
): Promise<ApplyResponse> => {
  try {
    const formParams = {
      package_id: packageId,
      file_ids: JSON.stringify(fileIds)
    };
    
    return await apiCall('/packages/apply', 'POST', formParams);
  } catch (error) {
    console.error('Error applying package to files:', error);
    throw error;
  }
};
```

### Testing Strategy

#### Unit Tests
```typescript
// __tests__/PackageAPI.test.ts
import { createDocumentPackage, getDocumentPackages } from '../PackageAPI';
import { apiCall } from '../CommonAPI';

jest.mock('../CommonAPI');
const mockApiCall = apiCall as jest.MockedFunction<typeof apiCall>;

describe('PackageAPI', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('createDocumentPackage', () => {
    it('should create package with valid data', async () => {
      const mockResponse = {
        success: true,
        data: { package_id: 'test-123' },
        message: 'Package created successfully'
      };
      
      mockApiCall.mockResolvedValue(mockResponse);
      
      const packageData = {
        package_name: 'Test Package',
        category: 'NQM' as const,
        description: 'Test description'
      };
      
      const result = await createDocumentPackage(packageData);
      
      expect(mockApiCall).toHaveBeenCalledWith('/packages', 'POST', expect.any(Object));
      expect(result).toEqual(mockResponse);
    });
  });
});
```

## Files to Create
- `frontend/src/services/PackageAPI.ts` - Main API service
- `frontend/src/services/PackageTypes.ts` - TypeScript type definitions  
- `frontend/src/services/PackageUtils.ts` - Utility functions
- `frontend/src/services/__tests__/PackageAPI.test.ts` - Unit tests

## Success Metrics
- All acceptance criteria must pass validation
- Complete type safety with no TypeScript errors
- Comprehensive error handling with retry logic
- 100% test coverage for all API functions
- Integration with existing API patterns

## Integration Points
- Backend Package API endpoints (Task 6)
- Existing FormData API pattern (`services/CommonAPI.ts`)
- User credentials context for authentication
- File context for package-file associations
- Alert context for user notifications

## Implementation Notes

### FormData Integration
- Follow existing `apiCall` pattern from `CommonAPI.ts`
- Use FormData for all API requests to match backend expectations
- JSON stringify complex objects (documents, relationships, customizations)
- Handle multipart form data for file uploads

### Response Handling
- Use standardized response format from `create_api_response`
- Extract data from response.data structure
- Handle both success and error responses consistently
- Transform backend data for frontend consumption

### Type Safety
- Complete TypeScript coverage for all API functions
- Interface definitions matching backend response structures
- Generic types for reusable patterns
- Proper error type definitions

This comprehensive API service layer will provide type-safe, reliable communication between the frontend package management components and the backend package system.
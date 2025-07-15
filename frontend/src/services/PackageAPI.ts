import { AxiosResponse } from 'axios';
import api from '../API/Index';
import { DocumentPackage, PackageFormData, PackageVersion } from '../types';

export interface PackageAPIResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
  message?: string;
}

// Create a new document package
export const createDocumentPackage = async (formData: PackageFormData & { documents?: any[], products?: any[] }): Promise<PackageAPIResponse<DocumentPackage>> => {
  try {
    const form = new FormData();
    form.append('package_name', formData.package_name);
    form.append('category', formData.category);
    form.append('template', formData.template);
    form.append('customizations', JSON.stringify(formData.customizations));
    form.append('tenant_id', 'default_tenant'); // Add required tenant_id field
    
    // Add products if provided (for 3-tier hierarchy)
    if (formData.products && formData.products.length > 0) {
      form.append('products', JSON.stringify(formData.products));
      console.log('Sending products to backend:', formData.products);
    }
    
    // Add documents if provided (for backwards compatibility)
    if (formData.documents && formData.documents.length > 0) {
      form.append('documents', JSON.stringify(formData.documents));
    }

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/packages',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error creating package:', error);
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
      console.error('Response headers:', error.response.headers);
    }
    throw error;
  }
};

// Get all document packages with optional filtering
export const getDocumentPackages = async (category?: string): Promise<PackageAPIResponse<DocumentPackage[]>> => {
  try {
    const params = new URLSearchParams();
    if (category) {
      params.append('category', category);
    }

    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/packages?${params.toString()}`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching packages:', error);
    throw error;
  }
};

// Get a specific document package by ID
export const getDocumentPackage = async (packageId: string): Promise<PackageAPIResponse<DocumentPackage>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/packages/${packageId}`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching package:', error);
    throw error;
  }
};

// Update an existing document package
export const updateDocumentPackage = async (
  packageId: string,
  updateData: Partial<PackageFormData>
): Promise<PackageAPIResponse<DocumentPackage>> => {
  try {
    const form = new FormData();
    if (updateData.package_name) form.append('package_name', updateData.package_name);
    if (updateData.category) form.append('category', updateData.category);
    if (updateData.template) form.append('template_type', updateData.template);
    if (updateData.customizations) form.append('customizations', JSON.stringify(updateData.customizations));

    const response: AxiosResponse = await api({
      method: 'PUT',
      url: `/packages/${packageId}`,
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error updating package:', error);
    throw error;
  }
};

// Delete a document package
export const deleteDocumentPackage = async (packageId: string): Promise<PackageAPIResponse<any>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'DELETE',
      url: `/packages/${packageId}`,
    });

    return response.data;
  } catch (error) {
    console.error('Error deleting package:', error);
    throw error;
  }
};

// Clone a document package
export const cloneDocumentPackage = async (
  packageId: string,
  newPackageName: string,
  modifications?: Record<string, any>
): Promise<PackageAPIResponse<DocumentPackage>> => {
  try {
    const form = new FormData();
    form.append('new_package_name', newPackageName);
    if (modifications) {
      form.append('modifications', JSON.stringify(modifications));
    }

    const response: AxiosResponse = await api({
      method: 'POST',
      url: `/packages/${packageId}/clone`,
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error cloning package:', error);
    throw error;
  }
};

// Get version history for a package
export const getPackageVersions = async (packageId: string): Promise<PackageAPIResponse<PackageVersion[]>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/packages/${packageId}/versions`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching package versions:', error);
    throw error;
  }
};

// Rollback package to a previous version
export const rollbackPackage = async (
  packageId: string,
  targetVersion: string
): Promise<PackageAPIResponse<DocumentPackage>> => {
  try {
    const form = new FormData();
    form.append('target_version', targetVersion);

    const response: AxiosResponse = await api({
      method: 'POST',
      url: `/packages/${packageId}/rollback`,
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error rolling back package:', error);
    throw error;
  }
};

// Compare two package versions
export const comparePackageVersions = async (
  packageId: string,
  version1: string,
  version2: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const params = new URLSearchParams();
    params.append('version1', version1);
    params.append('version2', version2);

    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/packages/${packageId}/diff?${params.toString()}`,
    });

    return response.data;
  } catch (error) {
    console.error('Error comparing package versions:', error);
    throw error;
  }
};

// Validate package configuration
export const validatePackageConfig = async (
  configData: PackageFormData
): Promise<PackageAPIResponse<any>> => {
  try {
    const form = new FormData();
    form.append('package_name', configData.package_name);
    form.append('category', configData.category);
    form.append('template_type', configData.template);
    form.append('customizations', JSON.stringify(configData.customizations));

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/packages/validate',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error validating package config:', error);
    throw error;
  }
};

// Get expected documents for a product
export const getExpectedDocuments = async (
  productId: string
): Promise<PackageAPIResponse<{
  product_id: string;
  product_name: string;
  expected_documents: Array<{
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
  }>;
  completion_status: {
    total_expected: number;
    uploaded_count: number;
    completion_percentage: number;
  };
}>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/products/${productId}/expected-documents`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching expected documents:', error);
    throw error;
  }
};

// Create DocumentPackage root node
export const createDocumentPackageNode = async (
  packageName: string,
  packageDescription?: string,
  workspaceId: string = 'default_workspace'
): Promise<PackageAPIResponse<any>> => {
  try {
    const form = new FormData();
    form.append('package_name', packageName);
    if (packageDescription) {
      form.append('package_description', packageDescription);
    }
    form.append('workspace_id', workspaceId);
    form.append('tenant_id', 'default_tenant');

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/document-packages',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error creating DocumentPackage:', error);
    throw error;
  }
};

// Create individual category with immediate node creation
export const createCategory = async (
  categoryCode: string,
  categoryName: string,
  categoryDescription?: string,
  packageId?: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const form = new FormData();
    form.append('category_code', categoryCode);
    form.append('category_name', categoryName);
    if (categoryDescription) {
      form.append('category_description', categoryDescription);
    }
    if (packageId) {
      form.append('package_id', packageId);
    }
    form.append('tenant_id', 'default_tenant');

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/categories',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error creating category:', error);
    throw error;
  }
};

// Create individual product with immediate node creation
export const createProduct = async (
  productName: string,
  categoryCode: string,
  productDescription?: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const form = new FormData();
    form.append('product_name', productName);
    form.append('category_code', categoryCode);
    if (productDescription) {
      form.append('product_description', productDescription);
    }
    form.append('tenant_id', 'default_tenant');

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/products',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error creating product:', error);
    throw error;
  }
};

// Create individual program with immediate node creation
export const createProgram = async (
  programName: string,
  programCode: string,
  productId: string,
  programDescription?: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const form = new FormData();
    form.append('program_name', programName);
    form.append('program_code', programCode);
    form.append('product_id', productId);
    if (programDescription) {
      form.append('program_description', programDescription);
    }
    form.append('tenant_id', 'default_tenant');

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/programs',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error creating program:', error);
    throw error;
  }
};

// Package Processing API Methods

export interface PackageProcessingRequest {
  packageId: string;
  modelname: string;
  model?: string;
  apikey?: string;
  baseURL?: string;
  isVectorSelected?: boolean;
  isGraphUpdate?: boolean;
  isReady?: boolean;
  language?: string;
  chatMode?: boolean;
  nodeLabels?: string[];
  relationshipLabels?: string[];
  packageData?: any; // Frontend package structure
}

export interface PackageProcessingStatus {
  packageId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentDocument?: string;
  processedDocuments: number;
  totalDocuments: number;
  error?: string;
  startTime?: string;
  endTime?: string;
  results?: any;
}

// Start package processing
export const processPackage = async (
  request: PackageProcessingRequest
): Promise<PackageAPIResponse<{ processing_id: string; status: PackageProcessingStatus }>> => {
  try {
    const form = new FormData();
    form.append('package_id', request.packageId);
    form.append('model', request.modelname);
    
    // Add package context to additional_instructions for backend detection
    form.append('additional_instructions', JSON.stringify({
      package_mode: true,
      package_id: request.packageId,
      processing_type: 'package_documents',
      enable_cross_document_relationships: true
    }));

    // Add package data if provided
    if (request.packageData) {
      form.append('package_data', JSON.stringify(request.packageData));
    }

    // Add other processing parameters
    if (request.apikey) form.append('apikey', request.apikey);
    if (request.baseURL) form.append('base_url', request.baseURL);
    if (request.isVectorSelected !== undefined) form.append('is_vector_selected', request.isVectorSelected.toString());
    if (request.isGraphUpdate !== undefined) form.append('is_graph_update', request.isGraphUpdate.toString());
    if (request.language) form.append('language', request.language);
    if (request.chatMode !== undefined) form.append('chat_mode', request.chatMode.toString());
    if (request.nodeLabels) form.append('node_labels', JSON.stringify(request.nodeLabels));
    if (request.relationshipLabels) form.append('relationship_labels', JSON.stringify(request.relationshipLabels));

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/packages/process',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error processing package:', error);
    throw error;
  }
};

// Get package processing status
export const getPackageProcessingStatus = async (
  packageId: string
): Promise<PackageAPIResponse<PackageProcessingStatus>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/packages/${packageId}/processing-status`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching processing status:', error);
    throw error;
  }
};

// Get package processing results
export const getPackageProcessingResults = async (
  packageId: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/packages/${packageId}/results`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching processing results:', error);
    throw error;
  }
};

// Cancel package processing
export const cancelPackageProcessing = async (
  packageId: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'POST',
      url: `/packages/${packageId}/cancel`,
    });

    return response.data;
  } catch (error) {
    console.error('Error cancelling package processing:', error);
    throw error;
  }
};

// Update document type and package associations
// Create a PackageDocument node (expected document)
export const createPackageDocument = async (
  productId: string,
  documentName: string,
  documentType: string,
  description?: string,
  expectedStructure?: any,
  validationRules?: any,
  requiredSections?: string[],
  optionalSections?: string[]
): Promise<PackageAPIResponse<any>> => {
  try {
    const form = new FormData();
    form.append('product_id', productId);
    form.append('document_name', documentName);
    form.append('document_type', documentType);
    
    if (description) {
      form.append('description', description);
    }
    if (expectedStructure) {
      form.append('expected_structure', JSON.stringify(expectedStructure));
    }
    if (validationRules) {
      form.append('validation_rules', JSON.stringify(validationRules));
    }
    if (requiredSections) {
      form.append('required_sections', JSON.stringify(requiredSections));
    }
    if (optionalSections) {
      form.append('optional_sections', JSON.stringify(optionalSections));
    }

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/package-documents',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error creating package document:', error);
    throw error;
  }
};

// Link uploaded document to package document
export const linkDocumentUpload = async (
  documentFilename: string,
  packageDocumentId: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const form = new FormData();
    form.append('document_filename', documentFilename);
    form.append('package_document_id', packageDocumentId);

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/package-documents/link-upload',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error linking document upload:', error);
    throw error;
  }
};

// Get package completion status
export const getPackageCompletionStatus = async (
  packageId: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/packages/${packageId}/completion-status`,
    });

    return response.data;
  } catch (error) {
    console.error('Error getting package completion status:', error);
    throw error;
  }
};

// Get discovered programs for a product
export const getDiscoveredPrograms = async (
  productId: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/products/${productId}/discovered-programs`,
    });

    return response.data;
  } catch (error) {
    console.error('Error getting discovered programs:', error);
    throw error;
  }
};

export const updateDocumentType = async (
  fileName: string,
  documentType: string,
  categoryId?: string,
  productId?: string,
  categoryName?: string,
  productName?: string
): Promise<PackageAPIResponse<any>> => {
  try {
    const form = new FormData();
    form.append('file_name', fileName);
    form.append('document_type', documentType);
    if (categoryId) {
      form.append('category_id', categoryId);
    }
    if (productId) {
      form.append('product_id', productId);
    }
    if (categoryName) {
      form.append('category_name', categoryName);
    }
    if (productName) {
      form.append('product_name', productName);
    }

    const response: AxiosResponse = await api({
      method: 'POST',
      url: '/documents/update-type',
      data: form,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error updating document type:', error);
    throw error;
  }
};
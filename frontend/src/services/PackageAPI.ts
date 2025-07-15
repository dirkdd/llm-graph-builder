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
export const createDocumentPackage = async (formData: PackageFormData & { documents?: any[] }): Promise<PackageAPIResponse<DocumentPackage>> => {
  try {
    const form = new FormData();
    form.append('package_name', formData.package_name);
    form.append('category', formData.category);
    form.append('template', formData.template);
    form.append('customizations', JSON.stringify(formData.customizations));
    form.append('tenant_id', 'default_tenant'); // Add required tenant_id field
    
    // Add documents if provided
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
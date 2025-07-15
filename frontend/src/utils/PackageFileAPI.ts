import { DocumentPackage, UploadParams } from '../types';
import { url } from './Utils';
import { apiCall } from '../services/CommonAPI';
import { Method } from 'axios';

export interface PackageUploadMetadata {
  package_id: string;
  package_name: string;
  category: string;
  template_type: string;
  expected_structure?: {
    navigation_depth: number;
    required_sections: string[];
    decision_trees: string[];
  };
}

// Enhanced upload function that includes package metadata
export const packageAwareUploadAPI = async (
  chunk: Blob, 
  model: string, 
  chunkNumber: number, 
  totalChunks: number, 
  originalname: string,
  packageInfo?: DocumentPackage,
  additionalParams?: Record<string, any>
): Promise<any> => {
  const urlUpload = `${url()}/upload`;
  const method: Method = 'post';
  
  // Create enhanced upload params
  let uploadParams: UploadParams & Record<string, any> = {
    file: chunk,
    model,
    chunkNumber,
    totalChunks,
    originalname,
  };
  
  // Add package-specific metadata
  if (packageInfo) {
    uploadParams.package_id = packageInfo.package_id;
    uploadParams.processing_type = 'package';
    
    const packageMetadata: PackageUploadMetadata = {
      package_id: packageInfo.package_id,
      package_name: packageInfo.package_name,
      category: packageInfo.category,
      template_type: packageInfo.template_type,
      expected_structure: packageInfo.documents[0]?.expected_structure
    };
    
    uploadParams.package_metadata = JSON.stringify(packageMetadata);
  } else {
    uploadParams.processing_type = 'standard';
  }
  
  // Add any additional parameters (user credentials, etc.)
  if (additionalParams) {
    uploadParams = { ...uploadParams, ...additionalParams };
  }
  
  const response = await apiCall(urlUpload, method, uploadParams);
  return response;
};

// Utility function to create package-aware file metadata
export const createPackageFileMetadata = (
  file: File, 
  packageInfo?: DocumentPackage
) => {
  const baseMetadata = {
    name: file.name,
    size: file.size,
    type: file.type,
    processing_type: packageInfo ? 'package' as const : 'standard' as const,
  };

  if (packageInfo) {
    return {
      ...baseMetadata,
      package_id: packageInfo.package_id,
      package_name: packageInfo.package_name,
      expected_structure: packageInfo.documents[0]?.expected_structure,
    };
  }

  return baseMetadata;
};

// Function to validate if a file is compatible with a package
export const validateFilePackageCompatibility = (
  file: File, 
  packageInfo: DocumentPackage
): { isCompatible: boolean; reason?: string } => {
  // Check file extension compatibility
  const fileExtension = file.name.toLowerCase().split('.').pop();
  const supportedExtensions = ['pdf', 'docx', 'txt', 'html', 'md'];
  
  if (!fileExtension || !supportedExtensions.includes(fileExtension)) {
    return {
      isCompatible: false,
      reason: `File type .${fileExtension} is not supported for package processing`
    };
  }

  // Check if package has specific document requirements
  if (packageInfo.documents && packageInfo.documents.length > 0) {
    const requiredDoc = packageInfo.documents.find(doc => 
      doc.document_type === 'GUIDELINE' && doc.required
    );
    
    if (requiredDoc && fileExtension !== 'pdf') {
      return {
        isCompatible: false,
        reason: `Package "${packageInfo.package_name}" requires PDF guidelines documents`
      };
    }
  }

  return { isCompatible: true };
};
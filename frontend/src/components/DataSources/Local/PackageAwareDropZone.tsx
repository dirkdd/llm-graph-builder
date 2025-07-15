import React, { useState, useEffect } from 'react';
import { useFileContext } from '../../../context/UsersFiles';
import { useCredentials } from '../../../context/UserCredentials';
import { usePackageUpload } from '../../../hooks/usePackageUpload';
import { EnhancedDropZone } from './EnhancedDropZone';
import { getDocumentPackages } from '../../../services/PackageAPI';
import { DocumentPackage } from '../../../types';
import { showErrorToast } from '../../../utils/Toasts';

interface PackageAwareDropZoneProps {
  enablePackageSelection?: boolean;
  defaultPackageId?: string;
}

export const PackageAwareDropZone: React.FC<PackageAwareDropZoneProps> = ({ 
  enablePackageSelection = true,
  defaultPackageId 
}) => {
  const { model, setFilesData } = useFileContext();
  const { userCredentials } = useCredentials();
  const [availablePackages, setAvailablePackages] = useState<DocumentPackage[]>([]);
  const [packagesLoading, setPackagesLoading] = useState(false);

  const { uploadWithPackage, isUploading } = usePackageUpload({
    model,
    userCredentials: userCredentials || {},
    onFileUpdate: setFilesData,
  });

  // Load available packages
  useEffect(() => {
    if (enablePackageSelection) {
      loadPackages();
    }
  }, [enablePackageSelection]);

  const loadPackages = async () => {
    setPackagesLoading(true);
    try {
      const response = await getDocumentPackages();
      if (response.status === 'success' && response.data) {
        setAvailablePackages(response.data);
      } else {
        console.warn('Failed to load packages:', response.error);
      }
    } catch (error) {
      console.error('Error loading packages:', error);
    } finally {
      setPackagesLoading(false);
    }
  };

  const handleStandardUpload = (files: File[]) => {
    uploadWithPackage(files);
  };

  const handlePackageUpload = (files: File[], packageId: string) => {
    const packageInfo = availablePackages.find(pkg => pkg.package_id === packageId);
    if (!packageInfo) {
      showErrorToast('Selected package not found');
      return;
    }
    uploadWithPackage(files, packageInfo);
  };

  return (
    <EnhancedDropZone
      packageId={defaultPackageId}
      enablePackageSelection={enablePackageSelection}
      onFilesDropped={handleStandardUpload}
      onPackageUpload={handlePackageUpload}
      isLoading={isUploading || packagesLoading}
      availablePackages={availablePackages}
    />
  );
};
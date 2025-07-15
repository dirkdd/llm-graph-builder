import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { DocumentPackage, PackageFormData, PackageContext } from '../types';
import { getDocumentPackages, createDocumentPackage, getDocumentPackage } from '../services/PackageAPI';
import { showErrorToast, showSuccessToast } from '../utils/Toasts';

interface PackageContextProviderProps {
  children: ReactNode;
}

const PackageContextData = createContext<PackageContext>({
  packages: [],
  selectedPackage: null,
  loadPackages: async () => {},
  selectPackage: () => {},
  createPackage: async () => ({} as DocumentPackage),
  applyPackage: async () => {},
  isLoading: false,
  error: null,
});

export const PackageContextProvider: React.FC<PackageContextProviderProps> = ({ children }) => {
  const [packages, setPackages] = useState<DocumentPackage[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<DocumentPackage | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load packages from localStorage (fallback to API if needed)
  const loadPackages = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Try to load from localStorage first
      const localPackages = loadPackagesFromLocalStorage();
      if (localPackages.length > 0) {
        setPackages(localPackages);
        setIsLoading(false);
        return;
      }

      // Fallback to API if available
      try {
        const response = await getDocumentPackages();
        if (response.status === 'success' && response.data) {
          setPackages(response.data);
        } else {
          // If API fails, just use empty packages array (no error)
          setPackages([]);
        }
      } catch (apiError) {
        // API not available or failing - just use empty packages
        console.log('Package API not available, using local storage only');
        setPackages([]);
      }
    } catch (err) {
      // Only show error for critical failures
      console.warn('Error loading packages:', err);
      setPackages([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to load packages from localStorage
  const loadPackagesFromLocalStorage = (): DocumentPackage[] => {
    try {
      const packages: DocumentPackage[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith('package_')) {
          const packageData = localStorage.getItem(key);
          if (packageData) {
            const data = JSON.parse(packageData);
            // Convert our localStorage format to DocumentPackage format
            const documentPackage: DocumentPackage = {
              package_id: key.replace('package_', ''),
              package_name: data.metadata?.package_name || `Package ${key.substring(8, 16)}`,
              category: data.categories?.[0]?.type || 'NQM',
              template_type: data.metadata?.template_type || 'default',
              version: '1.0.0',
              status: 'ACTIVE',
              created_at: data.metadata?.created_at || new Date().toISOString(),
              updated_at: data.metadata?.last_modified || data.metadata?.created_at || new Date().toISOString(),
              documents: [],
              metadata: data.metadata || {}
            };
            packages.push(documentPackage);
          }
        }
      }
      return packages.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    } catch (error) {
      console.error('Error loading packages from localStorage:', error);
      return [];
    }
  };

  // Select a package by ID
  const selectPackage = async (packageId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getDocumentPackage(packageId);
      if (response.status === 'success' && response.data) {
        setSelectedPackage(response.data);
      } else {
        throw new Error(response.error || 'Failed to select package');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to select package';
      setError(errorMessage);
      showErrorToast(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Create a new package
  const createPackage = async (formData: PackageFormData): Promise<DocumentPackage> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await createDocumentPackage(formData);
      if (response.status === 'success' && response.data) {
        const newPackage = response.data;
        setPackages(prev => [...prev, newPackage]);
        showSuccessToast(`Package "${newPackage.package_name}" created successfully`);
        return newPackage;
      } else {
        throw new Error(response.error || 'Failed to create package');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create package';
      setError(errorMessage);
      showErrorToast(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Apply a package for processing
  const applyPackage = async (packageId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      // First get the package details
      const response = await getDocumentPackage(packageId);
      if (response.status === 'success' && response.data) {
        setSelectedPackage(response.data);
        showSuccessToast(`Package "${response.data.package_name}" applied successfully`);
      } else {
        throw new Error(response.error || 'Failed to apply package');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to apply package';
      setError(errorMessage);
      showErrorToast(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Load packages on component mount
  useEffect(() => {
    loadPackages();
  }, []);

  // Clear selected package when packages change
  useEffect(() => {
    if (selectedPackage && !packages.find(pkg => pkg.package_id === selectedPackage.package_id)) {
      setSelectedPackage(null);
    }
  }, [packages, selectedPackage]);

  const contextValue: PackageContext = {
    packages,
    selectedPackage,
    loadPackages,
    selectPackage,
    createPackage,
    applyPackage,
    isLoading,
    error,
  };

  return (
    <PackageContextData.Provider value={contextValue}>
      {children}
    </PackageContextData.Provider>
  );
};

export const usePackageContext = () => {
  const context = useContext(PackageContextData);
  if (!context) {
    throw new Error('usePackageContext must be used within a PackageContextProvider');
  }
  return context;
};

export { PackageContextData as PackageContext };
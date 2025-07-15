import { useState, useCallback } from 'react';
import { usePackageContext } from '../context/PackageContext';
import { DocumentPackage, PackageProcessingStatus } from '../types';
import api from '../API/Index';

interface UsePackagesReturn {
  packages: DocumentPackage[];
  loading: boolean;
  error: string | null;
  fetchPackages: () => Promise<void>;
  getPackageProcessingStatus: (packageId: string) => Promise<PackageProcessingStatus>;
}

export const usePackages = (): UsePackagesReturn => {
  const { packages, loadPackages, isLoading, error } = usePackageContext();
  const [localError, setLocalError] = useState<string | null>(null);

  const fetchPackages = useCallback(async () => {
    setLocalError(null);
    try {
      await loadPackages();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch packages';
      setLocalError(errorMessage);
    }
  }, [loadPackages]);

  const getPackageProcessingStatus = useCallback(async (packageId: string): Promise<PackageProcessingStatus> => {
    try {
      const response = await api({
        method: 'GET',
        url: `/packages/${packageId}/processing-status`,
      });

      if (response.data.status === 'success') {
        return response.data.data;
      } else {
        throw new Error(response.data.error || 'Failed to get processing status');
      }
    } catch (error) {
      console.error(`Error fetching processing status for package ${packageId}:`, error);
      
      // Return a default status if the API call fails
      return {
        package_id: packageId,
        overall_status: 'unknown',
        files: [],
        progress: {
          completed: 0,
          total: 0,
          percentage: 0
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
    }
  }, []);

  return {
    packages,
    loading: isLoading,
    error: error || localError,
    fetchPackages,
    getPackageProcessingStatus,
  };
};
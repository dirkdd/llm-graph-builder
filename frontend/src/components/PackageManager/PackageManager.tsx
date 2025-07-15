import React, { useState, useEffect } from 'react';
import { Dialog, Typography, Button } from '@neo4j-ndl/react';
import { 
  Box,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  IconButton
} from '@mui/material';
import { PackageList } from './PackageList';
import { PackageCreator } from './PackageCreator';
import { getDocumentPackages } from '../../services/PackageAPI';
import { showSuccessToast, showErrorToast } from '../../utils/Toasts';
import { DocumentPackage } from '../../types';
import CloseIcon from '@mui/icons-material/Close';

interface PackageManagerProps {
  isOpen: boolean;
  onClose: () => void;
  onPackageSelected: (packageId: string) => void;
}

export const PackageManager: React.FC<PackageManagerProps> = ({ 
  isOpen, 
  onClose, 
  onPackageSelected 
}) => {
  const [packages, setPackages] = useState<DocumentPackage[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [showCreator, setShowCreator] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    if (isOpen) {
      loadPackages();
    }
  }, [isOpen, selectedCategory, refreshTrigger]);

  const loadPackages = async () => {
    setLoading(true);
    try {
      const response = await getDocumentPackages(selectedCategory || undefined);
      if (response.status === 'success' && response.data) {
        setPackages(response.data);
      } else {
        showErrorToast('Failed to load packages');
      }
    } catch (error) {
      showErrorToast('Error loading packages');
    } finally {
      setLoading(false);
    }
  };

  const handlePackageCreated = (newPackage: DocumentPackage) => {
    setRefreshTrigger(prev => prev + 1);
    setShowCreator(false);
    showSuccessToast(`Package "${newPackage.package_name}" created successfully`);
  };

  const handleEditPackage = (packageId: string) => {
    // TODO: Implement package editing
    console.log('Edit package:', packageId);
  };

  const handleClonePackage = async (packageId: string) => {
    // TODO: Implement package cloning
    console.log('Clone package:', packageId);
  };

  return (
    <>
      <Dialog isOpen={isOpen} onClose={onClose} size="large">
        <Dialog.Content className="n-flex n-flex-col n-gap-token-4">
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Document Package Manager</Typography>
            <IconButton onClick={onClose} size="small" aria-label="close">
              <CloseIcon />
            </IconButton>
          </Box>
          
          <Box>
            {/* Category Filter */}
            <Box sx={{ mb: 3 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter by Category</InputLabel>
                <Select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  displayEmpty
                  label="Filter by Category"
                >
                  <MenuItem value="">All Categories</MenuItem>
                  <MenuItem value="NQM">Non-QM</MenuItem>
                  <MenuItem value="RTL">Rental/Investment</MenuItem>
                  <MenuItem value="SBC">Small Balance Commercial</MenuItem>
                  <MenuItem value="CONV">Conventional</MenuItem>
                </Select>
              </FormControl>
            </Box>

            {/* Package List */}
            <PackageList 
              packages={packages}
              loading={loading}
              onSelect={onPackageSelected}
              onEdit={handleEditPackage}
              onClone={handleClonePackage}
            />

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, mt: 3, justifyContent: 'flex-end' }}>
              <Button 
                onClick={() => setShowCreator(true)}
                isDisabled={loading}
              >
                Create New Package
              </Button>
              <Button isDisabled>
                Import Template
              </Button>
            </Box>
          </Box>
        </Dialog.Content>
      </Dialog>

      {/* Package Creator Modal */}
      <PackageCreator
        isOpen={showCreator}
        onClose={() => setShowCreator(false)}
        onPackageCreated={handlePackageCreated}
      />
    </>
  );
};
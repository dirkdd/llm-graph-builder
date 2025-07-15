import React, { useState } from 'react';
import {
  Button,
  IconButton,
  Tooltip
} from '@neo4j-ndl/react';
import {
  Box,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Typography
} from '@mui/material';
import {
  DocumentPlusIcon,
  ArrowPathIcon,
  FolderIcon,
  FolderOpenIcon
} from '@heroicons/react/24/outline';
import { PackageHierarchyItem, PackageSelectionContext } from '../../types';

interface PackageActionBarProps {
  selectionContext: PackageSelectionContext;
  onAddCategory: (categoryType: string, categoryName: string) => void;
  onAddProduct: (categoryId: string, productName: string) => void;
  onTogglePackageMode: (enabled: boolean) => void;
  packageModeEnabled: boolean;
  onExportPackage?: (categoryId?: string, productId?: string) => void;
  onImportPackage?: () => void;
  selectedItems: PackageHierarchyItem[];
}

const MORTGAGE_CATEGORIES = [
  { value: 'NQM', label: 'Non-QM', color: 'primary', description: 'Non-Qualified Mortgage programs' },
  { value: 'RTL', label: 'Rental/Investment', color: 'secondary', description: 'Rental and investment property loans' },
  { value: 'SBC', label: 'Small Balance Commercial', color: 'success', description: 'Small commercial property loans' },
  { value: 'CONV', label: 'Conventional', color: 'warning', description: 'Conventional mortgage programs' }
] as const;

export const PackageActionBar: React.FC<PackageActionBarProps> = ({
  selectionContext,
  onAddCategory,
  onAddProduct,
  onTogglePackageMode,
  packageModeEnabled,
  onExportPackage,
  onImportPackage,
  selectedItems
}) => {
  const [showCategoryCreator, setShowCategoryCreator] = useState(false);
  const [showProductCreator, setShowProductCreator] = useState(false);
  const [newCategoryType, setNewCategoryType] = useState<string>('');
  const [newCategoryName, setNewCategoryName] = useState<string>('');
  const [newProductName, setNewProductName] = useState<string>('');

  const handleAddCategory = () => {
    if (!showCategoryCreator) {
      setShowCategoryCreator(true);
      setNewCategoryType('');
      setNewCategoryName('');
      return;
    }

    if (newCategoryType && newCategoryName.trim()) {
      onAddCategory(newCategoryType, newCategoryName.trim());
      setShowCategoryCreator(false);
      setNewCategoryType('');
      setNewCategoryName('');
    }
  };

  const handleAddProduct = () => {
    if (!showProductCreator) {
      setShowProductCreator(true);
      setNewProductName('');
      return;
    }

    if (newProductName.trim() && selectionContext.selectedCategory) {
      onAddProduct(selectionContext.selectedCategory.id, newProductName.trim());
      setShowProductCreator(false);
      setNewProductName('');
    }
  };

  const cancelCategoryCreation = () => {
    setShowCategoryCreator(false);
    setNewCategoryType('');
    setNewCategoryName('');
  };

  const cancelProductCreation = () => {
    setShowProductCreator(false);
    setNewProductName('');
  };

  const getSelectedCategoryInfo = () => {
    if (!selectionContext.selectedCategory) return null;
    return MORTGAGE_CATEGORIES.find(cat => cat.value === selectionContext.selectedCategory?.type);
  };

  const selectedCategoryInfo = getSelectedCategoryInfo();

  return (
    <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
      {/* Package Mode Toggle */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h6">Workspace Mode</Typography>
          <Button
            variant={packageModeEnabled ? 'contained' : 'outlined'}
            size="small"
            onClick={() => onTogglePackageMode(!packageModeEnabled)}
          >
            {packageModeEnabled ? (
              <><FolderOpenIcon style={{ width: '16px', height: '16px', marginRight: '8px' }} />Package Mode</>
            ) : (
              <><FolderIcon style={{ width: '16px', height: '16px', marginRight: '8px' }} />Standard Mode</>
            )}
          </Button>
        </Box>

        {/* Import/Export Actions */}
        <Box display="flex" gap={1}>
          <Tooltip title="Import Package Template">
            <IconButton
              size="small"
              onClick={onImportPackage}
              disabled={!packageModeEnabled}
            >
              <ArrowPathIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Save Package">
            <IconButton
              size="small"
              onClick={() => onExportPackage?.(
                selectionContext.selectedCategory?.id,
                selectionContext.selectedProduct?.id
              )}
              disabled={!packageModeEnabled || selectedItems.length === 0}
            >
              <DocumentPlusIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Package Mode Description */}
      <Typography variant="body1" style={{ color: 'var(--theme-palette-text-secondary)', marginBottom: '16px' }}>
        {packageModeEnabled 
          ? 'Create hierarchical document packages with categories, products, and structured file organization'
          : 'Upload and process individual files using standard workflow'
        }
      </Typography>

      {packageModeEnabled && (
        <>
          {/* Current Selection Context */}
          {(selectionContext.selectedCategory || selectionContext.selectedProduct) && (
            <Box mb={2}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>Current Selection</Typography>
              <Box display="flex" alignItems="center" gap={1}>
                {selectionContext.selectedCategory && (
                  <Chip 
                    label={`${selectionContext.selectedCategory.name} (${selectionContext.selectedCategory.type})`}
                    color={selectedCategoryInfo?.color || 'primary'}
                    size="small"
                  />
                )}
                {selectionContext.selectedProduct && (
                  <>
                    <Typography variant="body1" style={{ color: 'var(--theme-palette-text-secondary)' }}>→</Typography>
                    <Chip 
                      label={selectionContext.selectedProduct.name}
                      variant="outlined"
                      size="small"
                    />
                  </>
                )}
              </Box>
            </Box>
          )}

          {/* Category Creation */}
          {(!selectionContext.selectedCategory || showCategoryCreator) && (
            <Box mb={2}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>
                {showCategoryCreator ? 'Create New Category' : 'Add Mortgage Category'}
              </Typography>
              
              {!showCategoryCreator ? (
                <Button
                  variant="outlined"
                  onClick={handleAddCategory}
                  size="small"
                >
                  <FolderIcon style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                  Add Category
                </Button>
              ) : (
                <Box display="flex" flexDirection="column" gap={2}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Category Type</InputLabel>
                    <Select
                      value={newCategoryType}
                      onChange={(e) => setNewCategoryType(e.target.value)}
                      label="Category Type"
                    >
                      {MORTGAGE_CATEGORIES.map((category) => (
                        <MenuItem key={category.value} value={category.value}>
                          <Box>
                            <Typography variant="body1">{category.label}</Typography>
                            <Typography variant="body2" style={{ color: 'var(--theme-palette-text-secondary)' }}>
                              {category.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <TextField
                    fullWidth
                    size="small"
                    label="Category Name"
                    value={newCategoryName}
                    onChange={(e) => setNewCategoryName(e.target.value)}
                    placeholder={newCategoryType ? `e.g., ${newCategoryType} Enhanced Program` : 'Enter category name'}
                  />
                  
                  <Box display="flex" gap={1}>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={handleAddCategory}
                      disabled={!newCategoryType || !newCategoryName.trim()}
                    >
                      Create Category
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={cancelCategoryCreation}
                    >
                      Cancel
                    </Button>
                  </Box>
                </Box>
              )}
            </Box>
          )}

          {/* Product Creation */}
          {selectionContext.selectedCategory && !selectionContext.selectedProduct && (
            <Box mb={2}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>
                {showProductCreator ? 'Create New Product' : 'Add Product'}
              </Typography>
              
              {!showProductCreator ? (
                <Button
                  variant="outlined"
                  onClick={handleAddProduct}
                  size="small"
                >
                  <FolderIcon style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                  Add Product
                </Button>
              ) : (
                <Box display="flex" flexDirection="column" gap={2}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Product Name"
                    value={newProductName}
                    onChange={(e) => setNewProductName(e.target.value)}
                    placeholder={`e.g., ${selectionContext.selectedCategory.type} Premium Program`}
                  />
                  
                  <Box display="flex" gap={1}>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={handleAddProduct}
                      disabled={!newProductName.trim()}
                    >
                      Create Product
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={cancelProductCreation}
                    >
                      Cancel
                    </Button>
                  </Box>
                </Box>
              )}
            </Box>
          )}

          {/* Document Upload Context */}
          {selectionContext.selectedProduct && (
            <Box>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>Ready for Document Upload</Typography>
              <Box display="flex" alignItems="center" gap={1} p={1} 
                sx={{ 
                  backgroundColor: 'rgba(76, 175, 80, 0.15)',
                  border: '1px solid rgba(76, 175, 80, 0.3)',
                  borderRadius: 1 
                }}
              >
                <DocumentPlusIcon className="w-4 h-4" />
                <Typography variant="body1">
                  Files will be uploaded to: 
                  <strong> {selectionContext.selectedCategory?.name}</strong> → 
                  <strong> {selectionContext.selectedProduct.name}</strong>
                </Typography>
              </Box>
            </Box>
          )}

          {/* Save Package Section */}
          {selectedItems.length > 0 && (
            <Box mt={2} p={2} 
              sx={{ 
                backgroundColor: 'rgba(var(--theme-palette-primary-bg-strong), 0.15)',
                border: '1px solid rgba(var(--theme-palette-primary-bg-strong), 0.3)',
                borderRadius: 1 
              }}
            >
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="subtitle1" sx={{ mb: 1 }}>Package Ready</Typography>
                  <Typography variant="body1" color="text.secondary">
                    Save your package structure and file designations
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => onExportPackage?.(
                    selectionContext.selectedCategory?.id,
                    selectionContext.selectedProduct?.id
                  )}
                  startIcon={<DocumentPlusIcon className="w-4 h-4" />}
                >
                  Save Package
                </Button>
              </Box>
            </Box>
          )}
        </>
      )}
    </Paper>
  );
};
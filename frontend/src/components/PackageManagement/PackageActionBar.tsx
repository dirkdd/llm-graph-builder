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
  Save as DocumentPlusIcon,
  Refresh as ArrowPathIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon
} from '@mui/icons-material';
import { PackageHierarchyItem, PackageSelectionContext } from '../../types';

interface PackageActionBarProps {
  selectionContext: PackageSelectionContext;
  onAddCategory: (categoryType: string, categoryName: string, categoryDescription?: string) => void;
  onAddProduct: (categoryId: string, productName: string, productDescription?: string) => void;
  onExportPackage?: (categoryId?: string, productId?: string) => void;
  onImportPackage?: () => void;
  onResetPackage?: () => void;
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
  onExportPackage,
  onImportPackage,
  onResetPackage,
  selectedItems
}) => {
  const [showCategoryCreator, setShowCategoryCreator] = useState(false);
  const [showProductCreator, setShowProductCreator] = useState(false);
  const [newCategoryType, setNewCategoryType] = useState<string>('');
  const [newCategoryName, setNewCategoryName] = useState<string>('');
  const [newCategoryDescription, setNewCategoryDescription] = useState<string>('');
  const [newProductName, setNewProductName] = useState<string>('');
  const [newProductDescription, setNewProductDescription] = useState<string>('');

  const handleAddCategory = () => {
    if (!showCategoryCreator) {
      setShowCategoryCreator(true);
      setNewCategoryType('');
      setNewCategoryName('');
      setNewCategoryDescription('');
      return;
    }

    if (newCategoryType && newCategoryName.trim()) {
      onAddCategory(newCategoryType, newCategoryName.trim(), newCategoryDescription.trim());
      setShowCategoryCreator(false);
      setNewCategoryType('');
      setNewCategoryName('');
      setNewCategoryDescription('');
    }
  };

  const handleAddProduct = () => {
    if (!showProductCreator) {
      setShowProductCreator(true);
      setNewProductName('');
      setNewProductDescription('');
      return;
    }

    if (newProductName.trim() && selectionContext.selectedCategory) {
      onAddProduct(selectionContext.selectedCategory.id, newProductName.trim(), newProductDescription.trim());
      setShowProductCreator(false);
      setNewProductName('');
      setNewProductDescription('');
    }
  };

  const cancelCategoryCreation = () => {
    setShowCategoryCreator(false);
    setNewCategoryType('');
    setNewCategoryName('');
    setNewCategoryDescription('');
  };

  const cancelProductCreation = () => {
    setShowProductCreator(false);
    setNewProductName('');
    setNewProductDescription('');
  };

  const getSelectedCategoryInfo = () => {
    if (!selectionContext.selectedCategory) return null;
    return MORTGAGE_CATEGORIES.find(cat => cat.value === selectionContext.selectedCategory?.type);
  };

  const selectedCategoryInfo = getSelectedCategoryInfo();

  return (
    <Paper sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>

      <>

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
                  
                  <TextField
                    fullWidth
                    size="small"
                    label="Category Description (Optional)"
                    value={newCategoryDescription}
                    onChange={(e) => setNewCategoryDescription(e.target.value)}
                    placeholder="Describe this category's purpose and scope for enhanced LLM processing..."
                    multiline
                    rows={2}
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
                  
                  <TextField
                    fullWidth
                    size="small"
                    label="Product Description (Optional)"
                    value={newProductDescription}
                    onChange={(e) => setNewProductDescription(e.target.value)}
                    placeholder="Describe this product's features, target borrowers, and key characteristics for enhanced LLM processing..."
                    multiline
                    rows={3}
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


      </>
    </Paper>
  );
};
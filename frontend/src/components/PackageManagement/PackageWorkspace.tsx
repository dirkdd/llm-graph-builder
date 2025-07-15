import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Box, Paper, Alert, Typography, Button } from '@mui/material';
import { PlayArrowIcon } from '@neo4j-ndl/react/icons';
import { PackageActionBar } from './PackageActionBar';
import { HierarchicalPackageTable } from './HierarchicalPackageTable';
import { ContextualDropZone } from './ContextualDropZone';
import { 
  PackageHierarchyItem, 
  PackageSelectionContext, 
  PackageCategory, 
  PackageProduct, 
  CustomFile,
  PackageHierarchy
} from '../../types';
import { useFileContext } from '../../context/UsersFiles';
import { showSuccessToast, showErrorToast, showNormalToast } from '../../utils/Toasts';
import { v4 as uuidv4 } from 'uuid';
import { extractAPI } from '../../utils/FileAPI';

interface PackageWorkspaceProps {
  onFilesUpload: (files: File[], context: PackageSelectionContext) => void;
  className?: string;
}

export const PackageWorkspace: React.FC<PackageWorkspaceProps> = ({
  onFilesUpload,
  className
}) => {
  const { 
    filesData, 
    selectedNodes, 
    selectedRels, 
    selectedTokenChunkSize, 
    selectedChunk_overlap, 
    selectedChunks_to_combine,
    model,
    additionalInstructions
  } = useFileContext();
  const [packageModeEnabled, setPackageModeEnabled] = useState(true);
  const [selectionContext, setSelectionContext] = useState<PackageSelectionContext>({
    selectionType: 'none'
  });
  const [packageHierarchy, setPackageHierarchy] = useState<PackageHierarchy>({
    categories: {},
    flattenedItems: [],
    totalFiles: 0,
    totalCategories: 0,
    totalProducts: 0
  });
  
  // Package processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<{[fileId: string]: string}>({});
  const [processingResults, setProcessingResults] = useState<any>(null);

  // Package persistence functions
  const loadPackagesFromStorage = useCallback(() => {
    try {
      const savedPackages = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith('package_')) {
          const packageData = localStorage.getItem(key);
          if (packageData) {
            savedPackages.push({
              id: key.replace('package_', ''),
              data: JSON.parse(packageData)
            });
          }
        }
      }
      return savedPackages;
    } catch (error) {
      console.error('Error loading packages from storage:', error);
      return [];
    }
  }, []);

  const loadPackageData = useCallback((packageData: any, source: string) => {
    try {
      if (!packageData?.categories) return false;
      
      // Convert saved package back to our state format
      const categories: { [key: string]: PackageCategory } = {};
      let totalFiles = 0;
      
      packageData.categories.forEach((category: any) => {
        categories[category.id] = {
          ...category,
          products: category.products.map((product: any) => ({
            ...product,
            documents: product.documents.map((doc: any) => ({
              ...doc,
              // Ensure all required CustomFile properties are present
              processingTotalTime: doc.processingTotalTime || 0,
              status: doc.status || 'New',
              nodesCount: doc.nodesCount || 0,
              relationshipsCount: doc.relationshipsCount || 0,
              model: doc.model || 'openai_gpt_4o',
              fileSource: doc.fileSource || 'local',
              retryOptionStatus: doc.retryOptionStatus || false,
              retryOption: doc.retryOption || '',
              chunkNodeCount: doc.chunkNodeCount || 0,
              chunkRelCount: doc.chunkRelCount || 0,
              entityNodeCount: doc.entityNodeCount || 0,
              entityEntityRelCount: doc.entityEntityRelCount || 0,
              communityNodeCount: doc.communityNodeCount || 0,
              communityRelCount: doc.communityRelCount || 0,
              processing_type: doc.processing_type || 'package',
              document_type: doc.document_type || 'Other'
            }))
          }))
        };
        totalFiles += category.products.reduce((sum: number, p: any) => sum + p.documents.length, 0);
      });
      
      setPackageHierarchy({
        categories,
        flattenedItems: [],
        totalFiles,
        totalCategories: Object.keys(categories).length,
        totalProducts: Object.values(categories).reduce((sum, cat) => sum + cat.products.length, 0)
      });
      
      showSuccessToast(`Loaded package from ${source}`);
      return true;
    } catch (error) {
      console.error('Error loading package data:', error);
      return false;
    }
  }, []);

  const loadMostRecentPackage = useCallback(() => {
    try {
      // First check for auto-save
      const autoSaveData = localStorage.getItem('package_autosave');
      if (autoSaveData) {
        try {
          const packageData = JSON.parse(autoSaveData);
          if (packageData?.categories) {
            return loadPackageData(packageData, 'autosave');
          }
        } catch (error) {
          console.warn('Failed to load auto-save data:', error);
        }
      }

      // Fallback to saved packages
      const savedPackages = loadPackagesFromStorage();
      if (savedPackages.length > 0) {
        // Sort by creation date and get the most recent
        const mostRecent = savedPackages.sort((a, b) => 
          new Date(b.data.metadata.created_at).getTime() - new Date(a.data.metadata.created_at).getTime()
        )[0];
        
        if (mostRecent?.data?.categories) {
          return loadPackageData(mostRecent.data, `saved package: ${mostRecent.id.substring(0, 8)}`);
        }
      }
      return false;
    } catch (error) {
      console.error('Error loading most recent package:', error);
      showErrorToast('Failed to load packages');
      return false;
    }
  }, [loadPackagesFromStorage]);

  // Initialize data - try to load from storage first, then fall back to empty state
  const initializeData = useCallback(() => {
    if (packageModeEnabled && Object.keys(packageHierarchy.categories).length === 0) {
      const loaded = loadMostRecentPackage();
      if (!loaded) {
        // No packages found, start with empty state
        console.log('No existing packages found, starting fresh');
      }
    }
  }, [packageModeEnabled, packageHierarchy, loadMostRecentPackage]);

  // Convert package hierarchy to flat list for table
  const hierarchyData = useMemo((): PackageHierarchyItem[] => {
    const items: PackageHierarchyItem[] = [];
    
    Object.values(packageHierarchy.categories).forEach(category => {
      // Add category item
      const categoryItem: PackageHierarchyItem = {
        id: category.id,
        type: 'category',
        name: category.name,
        data: category,
        children: []
      };

      // Add product items
      category.products.forEach(product => {
        const productItem: PackageHierarchyItem = {
          id: product.id,
          type: 'product',
          name: product.name,
          parentId: category.id,
          data: product,
          children: []
        };

        // Add file items
        product.documents.forEach(file => {
          const fileItem: PackageHierarchyItem = {
            id: file.id,
            type: 'file',
            name: file.name,
            parentId: product.id,
            data: file
          };
          productItem.children!.push(fileItem);
        });

        categoryItem.children!.push(productItem);
      });

      items.push(categoryItem);
    });

    return items;
  }, [packageHierarchy]);

  const handleAddCategory = useCallback((categoryType: string, categoryName: string) => {
    const newCategory: PackageCategory = {
      id: uuidv4(),
      name: categoryName,
      type: categoryType as any,
      description: `${categoryType} mortgage category`,
      products: [],
      created_at: new Date().toISOString(),
      color: getCategoryColor(categoryType)
    };

    setPackageHierarchy(prev => ({
      ...prev,
      categories: {
        ...prev.categories,
        [newCategory.id]: newCategory
      },
      totalCategories: prev.totalCategories + 1
    }));

    showSuccessToast(`Category "${categoryName}" created successfully`);
  }, []);

  const handleAddProduct = useCallback((categoryId: string, productName: string) => {
    const newProduct: PackageProduct = {
      id: uuidv4(),
      name: productName,
      categoryId: categoryId,
      documents: [],
      completionStatus: {
        isComplete: false,
        requiredDocuments: ['Guidelines', 'Rate Matrix'],
        uploadedDocuments: [],
        missingDocuments: ['Guidelines', 'Rate Matrix'],
        completionPercentage: 0
      },
      created_at: new Date().toISOString()
    };

    setPackageHierarchy(prev => {
      const updatedCategories = { ...prev.categories };
      if (updatedCategories[categoryId]) {
        updatedCategories[categoryId] = {
          ...updatedCategories[categoryId],
          products: [...updatedCategories[categoryId].products, newProduct]
        };
      }

      return {
        ...prev,
        categories: updatedCategories,
        totalProducts: prev.totalProducts + 1
      };
    });

    // Auto-select the new product
    const category = packageHierarchy.categories[categoryId];
    if (category) {
      setSelectionContext({
        selectedCategory: category,
        selectedProduct: newProduct,
        selectionType: 'product'
      });
    }

    showSuccessToast(`Product "${productName}" created successfully`);
  }, [packageHierarchy.categories]);

  const handleSelectionChange = useCallback((context: PackageSelectionContext) => {
    setSelectionContext(context);
  }, []);

  const handleFilesUpload = useCallback((files: File[], context: PackageSelectionContext) => {
    if (packageModeEnabled && context.selectedProduct) {
      // Add files to the selected product
      const newFiles: CustomFile[] = files.map(file => ({
        id: uuidv4(),
        name: file.name,
        size: file.size,
        type: file.name.split('.').pop()?.toUpperCase() || 'UNKNOWN',
        status: 'New',
        nodesCount: 0,
        relationshipsCount: 0,
        model: 'openai_gpt_4o',
        fileSource: 'local',
        processingTotalTime: 0,
        retryOptionStatus: false,
        retryOption: '',
        chunkNodeCount: 0,
        chunkRelCount: 0,
        entityNodeCount: 0,
        entityEntityRelCount: 0,
        communityNodeCount: 0,
        communityRelCount: 0,
        package_id: context.selectedProduct.id,
        package_name: `${context.selectedCategory?.name} - ${context.selectedProduct.name}`,
        processing_type: 'package' as const,
        document_type: 'Other' as const // Default to 'Other', user can change via dropdown
      }));

      setPackageHierarchy(prev => {
        const updatedCategories = { ...prev.categories };
        const categoryId = context.selectedProduct!.categoryId;
        const category = updatedCategories[categoryId];
        
        if (category) {
          const productIndex = category.products.findIndex(p => p.id === context.selectedProduct!.id);
          if (productIndex !== -1) {
            const updatedProducts = [...category.products];
            updatedProducts[productIndex] = {
              ...updatedProducts[productIndex],
              documents: [...updatedProducts[productIndex].documents, ...newFiles]
            };
            
            updatedCategories[categoryId] = {
              ...category,
              products: updatedProducts
            };
          }
        }

        return {
          ...prev,
          categories: updatedCategories,
          totalFiles: prev.totalFiles + newFiles.length
        };
      });

      showSuccessToast(`${files.length} file(s) added to ${context.selectedProduct.name}`);
    }

    // Call the original upload handler
    onFilesUpload(files, context);
  }, [packageModeEnabled, onFilesUpload]);

  const handleFileAction = useCallback((fileId: string, action: string) => {
    console.log(`File action: ${action} on file ${fileId}`);
    // Implement file actions (view, edit, delete, etc.)
  }, []);

  const handleDocumentTypeChange = useCallback((fileId: string, documentType: 'Guidelines' | 'Matrix' | 'Supporting' | 'Other') => {
    setPackageHierarchy(prev => {
      const updatedCategories = { ...prev.categories };
      
      // Find and update the file
      Object.values(updatedCategories).forEach(category => {
        category.products.forEach(product => {
          const fileIndex = product.documents.findIndex(file => file.id === fileId);
          if (fileIndex !== -1) {
            product.documents[fileIndex] = {
              ...product.documents[fileIndex],
              document_type: documentType
            };
          }
        });
      });

      return {
        ...prev,
        categories: updatedCategories
      };
    });

    showSuccessToast(`Document type set to ${documentType}`);
  }, []);

  // Auto-save function (saves without download)
  const autoSavePackage = useCallback(() => {
    try {
      if (Object.keys(packageHierarchy.categories).length === 0) {
        return; // Nothing to save
      }

      const packageData = {
        categories: Object.values(packageHierarchy.categories).map(category => ({
          ...category,
          products: category.products.map(product => ({
            ...product,
            documents: product.documents.map(doc => ({
              id: doc.id,
              name: doc.name,
              type: doc.type,
              size: doc.size,
              document_type: doc.document_type || 'Other',
              package_id: doc.package_id,
              package_name: doc.package_name,
              processing_type: doc.processing_type,
              status: doc.status,
              nodesCount: doc.nodesCount,
              relationshipsCount: doc.relationshipsCount,
              model: doc.model,
              fileSource: doc.fileSource,
              processingTotalTime: doc.processingTotalTime,
              retryOptionStatus: doc.retryOptionStatus,
              retryOption: doc.retryOption,
              chunkNodeCount: doc.chunkNodeCount,
              chunkRelCount: doc.chunkRelCount,
              entityNodeCount: doc.entityNodeCount,
              entityEntityRelCount: doc.entityEntityRelCount,
              communityNodeCount: doc.communityNodeCount,
              communityRelCount: doc.communityRelCount
            }))
          }))
        })),
        metadata: {
          total_categories: packageHierarchy.totalCategories,
          total_products: packageHierarchy.totalProducts,
          total_files: packageHierarchy.totalFiles,
          created_at: new Date().toISOString(),
          package_type: 'mortgage_document_package',
          last_modified: new Date().toISOString()
        }
      };

      // Save to localStorage with a consistent key for auto-save
      const autoSaveKey = 'package_autosave';
      localStorage.setItem(autoSaveKey, JSON.stringify(packageData));
      
    } catch (error) {
      console.error('Error auto-saving package:', error);
    }
  }, [packageHierarchy]);

  const handleSavePackage = useCallback(async (categoryId?: string, productId?: string) => {
    try {
      // Create the package data structure
      const packageData = {
        categories: Object.values(packageHierarchy.categories).map(category => ({
          ...category,
          products: category.products.map(product => ({
            ...product,
            documents: product.documents.map(doc => ({
              id: doc.id,
              name: doc.name,
              type: doc.type,
              size: doc.size,
              document_type: doc.document_type || 'Other',
              package_id: doc.package_id,
              package_name: doc.package_name,
              processing_type: doc.processing_type,
              status: doc.status,
              nodesCount: doc.nodesCount,
              relationshipsCount: doc.relationshipsCount,
              model: doc.model,
              fileSource: doc.fileSource,
              processingTotalTime: doc.processingTotalTime,
              retryOptionStatus: doc.retryOptionStatus,
              retryOption: doc.retryOption,
              chunkNodeCount: doc.chunkNodeCount,
              chunkRelCount: doc.chunkRelCount,
              entityNodeCount: doc.entityNodeCount,
              entityEntityRelCount: doc.entityEntityRelCount,
              communityNodeCount: doc.communityNodeCount,
              communityRelCount: doc.communityRelCount
            }))
          }))
        })),
        metadata: {
          total_categories: packageHierarchy.totalCategories,
          total_products: packageHierarchy.totalProducts,
          total_files: packageHierarchy.totalFiles,
          created_at: new Date().toISOString(),
          package_type: 'mortgage_document_package'
        }
      };

      // Save to localStorage with unique ID
      const packageId = uuidv4();
      localStorage.setItem(`package_${packageId}`, JSON.stringify(packageData));
      
      // Also update the auto-save
      localStorage.setItem('package_autosave', JSON.stringify(packageData));
      
      showSuccessToast(`Package saved successfully! Package ID: ${packageId.substring(0, 8)}`);
      
      // Download as JSON
      const blob = new Blob([JSON.stringify(packageData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mortgage-package-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Error saving package:', error);
      showErrorToast('Failed to save package');
    }
  }, [packageHierarchy]);

  const handleImportPackage = useCallback(() => {
    console.log('Import package');
    // Implement package import functionality
    showSuccessToast('Import functionality coming soon');
  }, []);

  // Package processing functions
  const processPackageFile = useCallback(async (file: CustomFile) => {
    try {
      setProcessingStatus(prev => ({ ...prev, [file.id]: 'Processing' }));

      // Update package hierarchy to show processing status
      setPackageHierarchy(prev => {
        const updatedCategories = { ...prev.categories };
        Object.values(updatedCategories).forEach(category => {
          category.products.forEach(product => {
            const fileIndex = product.documents.findIndex(f => f.id === file.id);
            if (fileIndex !== -1) {
              product.documents[fileIndex] = {
                ...product.documents[fileIndex],
                status: 'Processing'
              };
            }
          });
        });
        return { ...prev, categories: updatedCategories };
      });

      // Call the extraction API with package-aware processing
      const apiResponse = await extractAPI(
        file.model || model,
        file.fileSource,
        file.retryOption ?? '',
        file.sourceUrl,
        localStorage.getItem('accesskey'),
        atob(localStorage.getItem('secretkey') ?? ''),
        file.name ?? '',
        file.gcsBucket ?? '',
        file.gcsBucketFolder ?? '',
        selectedNodes.map(l => l.value),
        selectedRels.map(t => t.value),
        selectedTokenChunkSize,
        selectedChunk_overlap,
        selectedChunks_to_combine,
        file.googleProjectId,
        file.language,
        file.accessToken,
        `${additionalInstructions || ''}\n\nPACKAGE CONTEXT: Processing as part of package "${file.package_name}". Document type: ${file.document_type}. Use hierarchical chunking with package-aware entity extraction.`
      );

      if (apiResponse?.status === 'Failed') {
        throw new Error(JSON.stringify({
          error: apiResponse.error,
          message: apiResponse.message,
          fileName: apiResponse.file_name
        }));
      }

      // Update package hierarchy with successful processing results
      setPackageHierarchy(prev => {
        const updatedCategories = { ...prev.categories };
        Object.values(updatedCategories).forEach(category => {
          category.products.forEach(product => {
            const fileIndex = product.documents.findIndex(f => f.id === file.id);
            if (fileIndex !== -1) {
              const apiRes = apiResponse?.data;
              product.documents[fileIndex] = {
                ...product.documents[fileIndex],
                status: apiRes?.status || 'Completed',
                nodesCount: apiRes?.nodeCount || 0,
                relationshipsCount: apiRes?.relationshipCount || 0,
                processingTotalTime: apiRes?.processingTime?.toFixed(2) || '0'
              };
            }
          });
        });
        return { ...prev, categories: updatedCategories };
      });

      setProcessingStatus(prev => ({ ...prev, [file.id]: 'Completed' }));
      showSuccessToast(`${file.name} processed successfully`);

      return { success: true, data: apiResponse?.data };
    } catch (error: any) {
      setProcessingStatus(prev => ({ ...prev, [file.id]: 'Failed' }));
      
      // Update package hierarchy with failed status
      setPackageHierarchy(prev => {
        const updatedCategories = { ...prev.categories };
        Object.values(updatedCategories).forEach(category => {
          category.products.forEach(product => {
            const fileIndex = product.documents.findIndex(f => f.id === file.id);
            if (fileIndex !== -1) {
              product.documents[fileIndex] = {
                ...product.documents[fileIndex],
                status: 'Failed',
                errorMessage: error.message || 'Processing failed'
              };
            }
          });
        });
        return { ...prev, categories: updatedCategories };
      });

      showErrorToast(`Failed to process ${file.name}: ${error.message}`);
      return { success: false, error: error.message };
    }
  }, [model, selectedNodes, selectedRels, selectedTokenChunkSize, selectedChunk_overlap, selectedChunks_to_combine, additionalInstructions]);

  const handleProcessPackage = useCallback(async () => {
    if (Object.keys(packageHierarchy.categories).length === 0) {
      showErrorToast('No package data to process');
      return;
    }

    // Get all files from the package
    const allFiles: CustomFile[] = [];
    Object.values(packageHierarchy.categories).forEach(category => {
      category.products.forEach(product => {
        allFiles.push(...product.documents);
      });
    });

    if (allFiles.length === 0) {
      showErrorToast('No files to process in package');
      return;
    }

    setIsProcessing(true);
    showNormalToast(`Starting package processing: ${allFiles.length} files`);

    const results = [];
    let successCount = 0;
    let failureCount = 0;

    try {
      // Process files sequentially to avoid overwhelming the API
      for (const file of allFiles) {
        if (file.status === 'New' || file.status === 'Ready to Reprocess') {
          const result = await processPackageFile(file);
          results.push({ file: file.name, result });
          
          if (result.success) {
            successCount++;
          } else {
            failureCount++;
          }
        }
      }

      // Set processing results
      setProcessingResults({
        totalFiles: allFiles.length,
        processedFiles: results.length,
        successCount,
        failureCount,
        results
      });

      if (successCount > 0) {
        showSuccessToast(`Package processing completed: ${successCount} successful, ${failureCount} failed`);
      } else {
        showErrorToast('Package processing failed for all files');
      }
    } catch (error) {
      console.error('Package processing error:', error);
      showErrorToast('Package processing failed unexpectedly');
    } finally {
      setIsProcessing(false);
    }
  }, [packageHierarchy, processPackageFile]);

  // Check if package has files ready to process
  const canProcessPackage = useMemo(() => {
    if (isProcessing) return false;
    
    const allFiles: CustomFile[] = [];
    Object.values(packageHierarchy.categories).forEach(category => {
      category.products.forEach(product => {
        allFiles.push(...product.documents);
      });
    });

    return allFiles.some(file => file.status === 'New' || file.status === 'Ready to Reprocess');
  }, [packageHierarchy, isProcessing]);

  const getCategoryColor = (type: string): 'primary' | 'secondary' | 'success' | 'warning' => {
    const colors = {
      'NQM': 'primary' as const,
      'RTL': 'secondary' as const,
      'SBC': 'success' as const,
      'CONV': 'warning' as const
    };
    return colors[type as keyof typeof colors] || 'primary';
  };

  useEffect(() => {
    initializeData();
  }, [initializeData]);

  // Auto-save when package hierarchy changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      autoSavePackage();
    }, 1000); // Debounce auto-save by 1 second

    return () => clearTimeout(timeoutId);
  }, [packageHierarchy, autoSavePackage]);

  return (
    <Box className={className}>
      {/* Package Action Bar */}
      <PackageActionBar
        selectionContext={selectionContext}
        onAddCategory={handleAddCategory}
        onAddProduct={handleAddProduct}
        onTogglePackageMode={setPackageModeEnabled}
        packageModeEnabled={packageModeEnabled}
        onExportPackage={handleSavePackage}
        onImportPackage={handleImportPackage}
        selectedItems={hierarchyData.filter(item => 
          selectionContext.selectionType !== 'none' && (
            item.id === selectionContext.selectedCategory?.id ||
            item.id === selectionContext.selectedProduct?.id
          )
        )}
      />

      {/* Main Content Area */}
      <Box display="flex" gap={2} sx={{ height: '600px' }}>
        {/* Left Panel - Package Structure */}
        <Box flex={2} display="flex" flexDirection="column">
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                {packageModeEnabled ? 'Package Structure' : 'Files'}
              </Typography>
              {packageModeEnabled && (
                <Box display="flex" gap={1}>
                  <Typography variant="body2" style={{ color: 'var(--theme-palette-text-secondary)' }}>
                    {packageHierarchy.totalCategories} categories • {packageHierarchy.totalProducts} products • {packageHierarchy.totalFiles} files
                  </Typography>
                </Box>
              )}
            </Box>

            <Box sx={{ flex: 1, minHeight: 0 }}>
              <HierarchicalPackageTable
                hierarchyData={hierarchyData}
                onSelectionChange={handleSelectionChange}
                onAddCategory={handleAddCategory}
                onAddProduct={handleAddProduct}
                onFileAction={handleFileAction}
                onDocumentTypeChange={handleDocumentTypeChange}
                selectionContext={selectionContext}
                packageModeEnabled={packageModeEnabled}
              />
            </Box>
          </Paper>
        </Box>

        {/* Right Panel - Upload Area */}
        <Box flex={1} display="flex" flexDirection="column">
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" mb={2}>File Upload</Typography>
            
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <ContextualDropZone
                selectionContext={selectionContext}
                onFilesUpload={handleFilesUpload}
                packageModeEnabled={packageModeEnabled}
              />

              {/* Package Context Info */}
              {packageModeEnabled && selectionContext.selectionType === 'product' && (
                <Box mt={2}>
                  <Alert severity="info" variant="outlined">
                    <Typography variant="body2">
                      <strong>Upload Context:</strong><br />
                      Category: {selectionContext.selectedCategory?.name}<br />
                      Product: {selectionContext.selectedProduct?.name}<br />
                      Files will be processed with package-aware extraction
                    </Typography>
                  </Alert>
                </Box>
              )}
            </Box>
          </Paper>
        </Box>
      </Box>

      {/* Package Statistics & Processing */}
      {packageModeEnabled && Object.keys(packageHierarchy.categories).length > 0 && (
        <Box mt={2}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
              <Typography variant="h6">Package Overview</Typography>
              <Button
                variant="contained"
                color="primary"
                startIcon={<PlayArrowIcon />}
                onClick={handleProcessPackage}
                disabled={!canProcessPackage}
                sx={{ 
                  minWidth: '160px',
                  height: '40px'
                }}
              >
                {isProcessing ? 'Processing...' : 'Process Package'}
              </Button>
            </Box>
            
            <Box display="flex" gap={4} mb={2}>
              <Box>
                <Typography variant="body2" color="text.secondary">Categories</Typography>
                <Typography variant="h6">{packageHierarchy.totalCategories}</Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Products</Typography>
                <Typography variant="h6">{packageHierarchy.totalProducts}</Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Files</Typography>
                <Typography variant="h6">{packageHierarchy.totalFiles}</Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Processing Type</Typography>
                <Typography variant="body1">
                  {packageModeEnabled ? 'Package-Aware' : 'Standard'}
                </Typography>
              </Box>
            </Box>

            {/* Processing Status */}
            {isProcessing && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Processing Package...</strong><br />
                  Files are being processed with package-aware hierarchical chunking and enhanced entity extraction.
                </Typography>
              </Alert>
            )}

            {/* Processing Results */}
            {processingResults && (
              <Alert severity={processingResults.failureCount > 0 ? 'warning' : 'success'} sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Processing Complete:</strong><br />
                  {processingResults.successCount} successful, {processingResults.failureCount} failed out of {processingResults.processedFiles} files processed
                </Typography>
              </Alert>
            )}

            {/* Package Processing Info */}
            {canProcessPackage && !isProcessing && (
              <Alert severity="info" variant="outlined" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Ready to Process:</strong> This package contains files that can be processed with package-aware extraction, including hierarchical chunking and enhanced entity relationships.
                </Typography>
              </Alert>
            )}
          </Paper>
        </Box>
      )}
    </Box>
  );
};
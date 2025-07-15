import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Box, Paper, Alert, Typography, Button, Chip, IconButton, Tooltip } from '@mui/material';
import { 
  PlayArrow as PlayArrowIcon,
  Refresh as ArrowPathIcon,
  Save as DocumentPlusIcon
} from '@mui/icons-material';
import { PackageActionBar } from './PackageActionBar';
import { HierarchicalPackageTable } from './HierarchicalPackageTable';
import { ContextualDropZone } from './ContextualDropZone';
import { 
  PackageHierarchyItem, 
  PackageSelectionContext, 
  PackageCategory, 
  PackageProduct, 
  PackageDocument,
  CustomFile,
  PackageHierarchy
} from '../../types';
import { useFileContext } from '../../context/UsersFiles';
import { showSuccessToast, showErrorToast, showNormalToast } from '../../utils/Toasts';
import { v4 as uuidv4 } from 'uuid';
import { extractAPI } from '../../utils/FileAPI';
import { PackageResultsViewer } from '../PackageProcessing/PackageResultsViewer';
import { 
  processPackage, 
  getPackageProcessingStatus, 
  getPackageProcessingResults,
  createDocumentPackage,
  createDocumentPackageNode,
  createCategory,
  createProduct,
  createProgram,
  updateDocumentType,
  createPackageDocument,
  linkDocumentUpload,
  getPackageCompletionStatus,
  getDiscoveredPrograms,
  PackageProcessingRequest,
  PackageProcessingStatus 
} from '../../services/PackageAPI';

interface PackageWorkspaceProps {
  onFilesUpload: (files: File[], context: PackageSelectionContext) => void;
  onStartChat?: (packageContext: any) => void;
  onViewGraph?: (packageId: string) => void;
  onProcessPackage?: (handler: () => void) => void;
  onProcessingComplete?: () => void;
  className?: string;
}

export const PackageWorkspace: React.FC<PackageWorkspaceProps> = ({
  onFilesUpload,
  onStartChat,
  onViewGraph,
  onProcessPackage,
  onProcessingComplete,
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
  const [currentPackageId, setCurrentPackageId] = useState<string | null>(null);
  
  // Package processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<{[fileId: string]: string}>({});
  const [processingResults, setProcessingResults] = useState<any>(null);
  const [showResults, setShowResults] = useState(false);

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
    if (Object.keys(packageHierarchy.categories).length === 0) {
      const loaded = loadMostRecentPackage();
      if (!loaded) {
        // No packages found, start with empty state
        console.log('No existing packages found, starting fresh');
      }
    }
  }, [packageHierarchy, loadMostRecentPackage]);

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

  const handleAddCategory = useCallback(async (categoryType: string, categoryName: string, categoryDescription?: string) => {
    try {
      // Check if this is the first category and we need to create a DocumentPackage
      const isFirstCategory = currentPackageId === null && Object.keys(packageHierarchy.categories).length === 0;
      let packageIdToUse = currentPackageId;
      
      if (isFirstCategory) {
        // Create DocumentPackage root node first
        const packageName = `${categoryType} Package`;
        const packageDescription = `Document package for ${categoryType} mortgage category`;
        
        const packageResponse = await createDocumentPackageNode(packageName, packageDescription);
        console.log('DocumentPackage response:', packageResponse);
        
        if (packageResponse.status === 'Success') {
          if (packageResponse.data && packageResponse.data.package_id) {
            packageIdToUse = packageResponse.data.package_id;
            setCurrentPackageId(packageIdToUse);
            showNormalToast(`Created DocumentPackage: ${packageName}`);
          } else {
            console.error('DocumentPackage response missing data or package_id:', packageResponse);
            throw new Error(`DocumentPackage response missing package_id`);
          }
        } else {
          throw new Error(`Failed to create DocumentPackage: ${packageResponse.error || 'Unknown error'}`);
        }
      }
      
      // Call backend API to create category with immediate node creation
      const response = await createCategory(categoryType, categoryName, categoryDescription, packageIdToUse || undefined);
      
      if (response.status === 'Success') {
        // Create local category object
        const newCategory: PackageCategory = {
          id: response.data.category_id,
          name: categoryName,
          type: categoryType as any,
          description: categoryDescription || `${categoryType} mortgage category`,
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

        const message = isFirstCategory 
          ? `DocumentPackage and Category "${categoryName}" created successfully with immediate node creation`
          : `Category "${categoryName}" created successfully with immediate node creation`;
        showSuccessToast(message);
      } else {
        showErrorToast(`Failed to create category: ${response.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating category:', error);
      showErrorToast(`Failed to create category: ${error.message || 'Network error'}`);
    }
  }, [currentPackageId, packageHierarchy.categories]);

  const handleAddProduct = useCallback(async (categoryId: string, productName: string, productDescription?: string) => {
    try {
      // Get category to pass category_code to API
      const category = packageHierarchy.categories[categoryId];
      if (!category) {
        showErrorToast('Category not found');
        return;
      }

      // Call backend API to create product with immediate node creation
      const response = await createProduct(productName, category.type, productDescription);
      
      if (response.status === 'Success') {
        const productId = response.data.product_id;
        
        // Create PackageDocument nodes for expected documents
        // Product-level: One Guidelines document that supports all programs
        const expectedDocuments = [
          { 
            name: `${productName} Guidelines`, 
            type: 'Guidelines', 
            description: 'Product guidelines supporting all programs',
            level: 'product' 
          }
        ];

        // Program-level: Each program gets its own matrix documents
        // For demo purposes, create common programs - in real use this would come from product configuration
        const programs = [
          { name: 'Standard Program', code: 'STD' },
          { name: 'Jumbo Program', code: 'JMB' },
          { name: 'Investment Program', code: 'INV' }
        ];

        // Add matrix documents for each program
        programs.forEach(program => {
          expectedDocuments.push({
            name: `${productName} ${program.name} Rate Matrix`,
            type: 'Matrix',
            description: `Rate matrix for ${program.name} (${program.code})`,
            level: 'program',
            programCode: program.code,
            programName: program.name
          });
        });
        
        const packageDocuments: PackageDocument[] = [];
        
        for (const doc of expectedDocuments) {
          try {
            const docResponse = await createPackageDocument(
              productId,
              doc.name,
              doc.type,
              doc.description || '', // description
              undefined, // expectedStructure
              undefined, // validation_rules
              doc.type === 'Guidelines' ? ['Eligibility', 'Documentation', 'Processing'] : undefined,
              doc.type === 'Matrix' ? ['Rates', 'Adjustments'] : undefined
            );
            
            if (docResponse.status === 'Success') {
              packageDocuments.push({
                id: docResponse.data.document_id,
                document_name: doc.name,
                document_type: doc.type as 'Guidelines' | 'Matrix',
                level: doc.level,
                programCode: doc.programCode,
                programName: doc.programName,
                has_upload: false,
                processing_status: 'PENDING',
                created_at: new Date().toISOString()
              });
            }
          } catch (error) {
            console.error(`Error creating package document for ${doc.name}:`, error);
          }
        }
        
        // Create local product object
        const newProduct: PackageProduct = {
          id: productId,
          name: productName,
          description: productDescription || `${productName} product`,
          categoryId: categoryId,
          documents: [],
          packageDocuments: packageDocuments, // Add expected documents
          completionStatus: {
            isComplete: false,
            requiredDocuments: ['Guidelines', 'Matrix'],
            uploadedDocuments: [],
            missingDocuments: ['Guidelines', 'Matrix'],
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

        showSuccessToast(`Product "${productName}" created successfully with immediate node creation`);
        
        // Auto-select the new product
        if (category) {
          setSelectionContext({
            selectedCategory: category,
            selectedProduct: newProduct,
            selectionType: 'product'
          });
        }
      } else {
        showErrorToast(`Failed to create product: ${response.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating product:', error);
      showErrorToast(`Failed to create product: ${error.message || 'Network error'}`);
    }
  }, [packageHierarchy.categories]);

  const handleSelectionChange = useCallback((context: PackageSelectionContext) => {
    setSelectionContext(context);
  }, []);

  // Calculate and update completion status based on uploaded documents
  const updateCompletionStatus = useCallback((productId: string, categoryId: string) => {
    setPackageHierarchy(prev => {
      const updatedCategories = { ...prev.categories };
      const category = updatedCategories[categoryId];
      
      if (category) {
        const productIndex = category.products.findIndex(p => p.id === productId);
        if (productIndex !== -1) {
          const product = category.products[productIndex];
          const requiredDocuments = product.completionStatus.requiredDocuments;
          
          // Get uploaded documents by type
          const uploadedDocuments = product.documents
            .filter(doc => doc.document_type && doc.document_type !== 'Other')
            .map(doc => doc.document_type);
          
          // Remove duplicates
          const uniqueUploadedDocuments = [...new Set(uploadedDocuments)];
          
          // Calculate missing documents
          const missingDocuments = requiredDocuments.filter(
            reqDoc => !uniqueUploadedDocuments.includes(reqDoc as any)
          );
          
          // Calculate completion percentage
          const completionPercentage = Math.round(
            (uniqueUploadedDocuments.length / requiredDocuments.length) * 100
          );
          
          // Update completion status
          const updatedProducts = [...category.products];
          updatedProducts[productIndex] = {
            ...product,
            completionStatus: {
              ...product.completionStatus,
              isComplete: missingDocuments.length === 0,
              uploadedDocuments: uniqueUploadedDocuments,
              missingDocuments,
              completionPercentage
            }
          };
          
          updatedCategories[categoryId] = {
            ...category,
            products: updatedProducts
          };
        }
      }
      
      return { ...prev, categories: updatedCategories };
    });
  }, []);

  const handleFilesUpload = useCallback((files: File[], context: PackageSelectionContext) => {
    if (context.selectedProduct) {
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
      
      // Update completion status after files are uploaded
      setTimeout(() => updateCompletionStatus(context.selectedProduct.id, context.selectedProduct.categoryId), 0);
    }

    // Call the original upload handler
    onFilesUpload(files, context);
  }, [onFilesUpload, updateCompletionStatus]);

  // Handle file upload with pre-selected document type (for document type slots)
  const handleFileUploadWithType = useCallback((file: File, expectedDocumentId: string, documentType: string, context: PackageSelectionContext) => {
    if (context.selectedProduct) {
      // Create a single file with pre-selected document type
      const newFile: CustomFile = {
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
        document_type: documentType as 'Guidelines' | 'Matrix' | 'Supporting' | 'Other',
        expected_document_id: expectedDocumentId // Store the PackageDocument template ID
      };

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
              documents: [...updatedProducts[productIndex].documents, newFile]
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
          totalFiles: prev.totalFiles + 1
        };
      });

      showSuccessToast(`${file.name} added as ${documentType} to ${context.selectedProduct.name}`);
      
      // Update completion status after file is uploaded
      setTimeout(() => updateCompletionStatus(context.selectedProduct.id, context.selectedProduct.categoryId), 0);
    }

    // Call the original upload handler with enhanced package context
    const enhancedContext = {
      ...context,
      expectedDocumentId,
      preSelectedDocumentType: documentType
    };
    
    onFilesUpload([file], enhancedContext);
  }, [onFilesUpload, updateCompletionStatus]);

  const handleFileAction = useCallback((fileId: string, action: string) => {
    console.log(`File action: ${action} on file ${fileId}`);
    // Implement file actions (view, edit, delete, etc.)
  }, []);

  const handleDocumentTypeChange = useCallback(async (fileId: string, documentType: 'Guidelines' | 'Matrix' | 'Supporting' | 'Other') => {
    let updatedProductId = '';
    let updatedCategoryId = '';
    let fileName = '';
    
    // Update local state first
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
            updatedProductId = product.id;
            updatedCategoryId = category.id;
            fileName = product.documents[fileIndex].name;
          }
        });
      });

      return {
        ...prev,
        categories: updatedCategories
      };
    });

    // Call backend API to update document type in database
    try {
      if (fileName && updatedCategoryId && updatedProductId) {
        // Get the category and product names from state
        const category = Object.values(packageHierarchy.categories).find(c => c.id === updatedCategoryId);
        const product = category?.products.find(p => p.id === updatedProductId);
        
        await updateDocumentType(fileName, documentType, updatedCategoryId, updatedProductId, category?.name, product?.name);
        showSuccessToast(`Document type updated to ${documentType} in database`);
      } else {
        showSuccessToast(`Document type set to ${documentType}`);
      }
    } catch (error) {
      console.error('Error updating document type in database:', error);
      showErrorToast('Failed to update document type in database');
    }

    // Update completion status after document type change
    if (updatedProductId && updatedCategoryId) {
      setTimeout(() => updateCompletionStatus(updatedProductId, updatedCategoryId), 0);
    }
  }, [updateCompletionStatus]);

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

  // Convert frontend package structure to database format
  const convertPackageToDatabase = useCallback(async () => {
    if (Object.keys(packageHierarchy.categories).length === 0) {
      throw new Error('No package data to convert');
    }

    // Determine primary category from package structure
    const primaryCategory = Object.values(packageHierarchy.categories)[0];
    const validCategories = ['NQM', 'RTL', 'SBC', 'CONV'];
    
    console.log('Package hierarchy categories:', packageHierarchy.categories);
    console.log('Primary category:', primaryCategory);
    console.log('Primary category type:', primaryCategory?.type);
    
    const packageCategory = primaryCategory?.type && validCategories.includes(primaryCategory.type) 
      ? primaryCategory.type 
      : 'NQM'; // Default to NQM if no valid category found
    
    console.log('Final package category:', packageCategory);
    
    // Create the package structure for database storage
    const packageData = {
      package_name: primaryCategory?.name || `Package_${Date.now()}`,
      category: packageCategory,
      template: 'mortgage_document_template',
      tenant_id: 'default_tenant',
      documents: [],
      // Add category and product descriptions for enhanced processing
      category_description: primaryCategory?.description || '',
      enable_immediate_node_creation: true,
      customizations: {
        package_type: 'mortgage_document_package',
        total_categories: packageHierarchy.totalCategories,
        total_products: packageHierarchy.totalProducts,
        total_files: packageHierarchy.totalFiles,
        categories: [],
        created_from: 'frontend_package_workspace'
      }
    };

    // Create products structure for 3-tier hierarchy
    const products: any[] = [];
    
    // Convert hierarchical structure to flat document list and products
    Object.values(packageHierarchy.categories).forEach(category => {
      packageData.customizations.categories.push({
        id: category.id,
        name: category.name,
        type: category.type,
        products: category.products.map(product => ({
          id: product.id,
          name: product.name,
          documents: product.documents.map(doc => doc.id)
        }))
      });

      category.products.forEach(product => {
        const productDocuments: any[] = [];
        
        product.documents.forEach(doc => {
          // Map frontend document types to backend expected types
          const mapDocumentType = (frontendType: string): string => {
            const typeMapping = {
              'Guidelines': 'guidelines',
              'Matrix': 'matrix',
              'Supporting': 'rate_sheet', // Map Supporting to rate_sheet
              'Other': 'guidelines' // Default to guidelines
            };
            return typeMapping[frontendType] || 'guidelines';
          };
          
          const backendDocumentType = mapDocumentType(doc.document_type || 'Other');
          
          console.log(`Mapping document type: ${doc.document_type} -> ${backendDocumentType}`);
          
          const docData = {
            document_name: doc.name,
            document_type: backendDocumentType,
            document_id: doc.id,
            file_size: doc.size,
            file_type: doc.type,
            category_id: category.id,
            category_name: category.name,
            product_id: product.id,
            product_name: product.name,
            processing_type: 'package',
            expected_structure: getExpectedStructure(backendDocumentType),
            required_sections: getRequiredSections(backendDocumentType),
            chunking_strategy: 'hierarchical',
            entity_types: ['Person', 'Organization', 'Location', 'Financial', 'Property'],
            validation_schema: getValidationSchema(backendDocumentType),
            quality_thresholds: {
              minimum_entities: 5,
              minimum_relationships: 3,
              confidence_threshold: 0.7
            }
          };
          
          // Add to flat document list (backwards compatibility)
          packageData.documents.push(docData);
          
          // Add to product documents (3-tier hierarchy)
          productDocuments.push(docData);
        });
        
        // Add product to products array
        products.push({
          product_id: product.id,
          product_name: product.name,
          description: product.description || `${product.name} product`,
          key_features: [],
          underwriting_highlights: [],
          target_borrowers: [],
          product_type: 'core',
          tier_level: 1,
          processing_priority: 1,
          dependencies: [],
          documents: productDocuments
        });
      });
    });
    
    // Add products to package data for 3-tier hierarchy
    packageData.products = products;
    
    console.log('Package data with 3-tier hierarchy:', packageData);

    try {
      console.log('Creating package in database:', packageData);
      console.log('Package category being used:', packageCategory);
      console.log('Primary category from hierarchy:', primaryCategory);
      
      const response = await createDocumentPackage(packageData);
      
      console.log('Raw API response:', response);
      console.log('Response status:', response?.status);
      console.log('Response data:', response?.data);
      
      // Check if response has the expected structure (backend returns "Success" with capital S)
      if (response && response.status === 'Success' && response.data && response.data.package_id) {
        console.log('Package created successfully:', response.data.package_id);
        showSuccessToast(`Package saved to database: ${response.data.package_id}`);
        return response.data.package_id;
      } else if (response && response.status === 'Failed') {
        // Handle backend failure response
        console.error('Package creation failed (backend error):', response);
        throw new Error(response.error || response.message || 'Package creation failed');
      } else {
        console.error('Package creation failed - unexpected response format:', response);
        throw new Error('Failed to create package - unexpected response format');
      }
    } catch (error) {
      console.error('Error creating package:', error);
      if (error.response) {
        console.error('Error response:', error.response.data);
        console.error('Error response status:', error.response.status);
        showErrorToast(`Failed to save package: ${error.response.data.error || error.response.data.message || error.message}`);
      } else {
        showErrorToast(`Failed to save package: ${error.message}`);
      }
      throw error;
    }
  }, [packageHierarchy]);

  const handleProcessPackage = useCallback(async () => {
    console.log('PackageWorkspace handleProcessPackage called');
    console.log('Package hierarchy:', packageHierarchy);
    
    if (Object.keys(packageHierarchy.categories).length === 0) {
      console.log('No package data to process');
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
      console.log('No files to process in package');
      showErrorToast('No files to process in package');
      return;
    }
    
    console.log('Found files to process:', allFiles.length);

    const packageName = Object.values(packageHierarchy.categories)[0]?.name || 'Unnamed Package';
    const packageId = uuidv4();

    setIsProcessing(true);
    showNormalToast(`Starting package processing: ${allFiles.length} files`);

    try {
      console.log('Starting package processing with request parameters');

      // Step 1: Save package to database first
      setIsProcessing(true);
      showNormalToast('Saving package to database...');
      
      const databasePackageId = await convertPackageToDatabase();
      
      // Step 2: Process from database with proper package context
      showNormalToast('Processing package from database...');
      
      // Prepare package processing request
      const processingRequest: PackageProcessingRequest = {
        packageId: databasePackageId, // Use database package ID
        modelname: model,
        apikey: localStorage.getItem('apikey') || undefined,
        baseURL: localStorage.getItem('baseURL') || undefined,
        isVectorSelected: true,
        isGraphUpdate: false,
        language: 'en',
        chatMode: false,
        nodeLabels: selectedNodes.map(n => n.value),
        relationshipLabels: selectedRels.map(r => r.value)
      };

      // Start package processing from database
      console.log('Sending package processing request:', processingRequest);
      const processResponse = await processPackage(processingRequest);
      console.log('Package processing response:', processResponse);
      
      if (processResponse.status === 'error') {
        console.error('Package processing failed:', processResponse.error);
        throw new Error(processResponse.error || 'Failed to start package processing');
      }
      
      // Update local state to reflect database package ID
      setPackageHierarchy(prev => ({
        ...prev,
        databasePackageId: databasePackageId
      }));

      showNormalToast('Package processing started, monitoring progress...');

      // Poll for processing status
      const pollInterval = 2000; // Poll every 2 seconds
      const maxPolls = 300; // Maximum 10 minutes
      let pollCount = 0;

      const statusPolling = setInterval(async () => {
        try {
          pollCount++;
          const statusResponse = await getPackageProcessingStatus(packageId);
          
          if (statusResponse.status === 'success' && statusResponse.data) {
            const status = statusResponse.data;
            
            // Update processing status in UI
            setProcessingStatus(prev => ({
              ...prev,
              [packageId]: status.status
            }));

            // Update progress info
            if (status.currentDocument) {
              showNormalToast(`Processing: ${status.currentDocument} (${status.processedDocuments}/${status.totalDocuments})`);
            }

            // Check if processing is complete
            if (status.status === 'completed' || status.status === 'failed') {
              clearInterval(statusPolling);
              
              if (status.status === 'completed') {
                // Fetch results
                const resultsResponse = await getPackageProcessingResults(packageId);
                
                if (resultsResponse.status === 'success' && resultsResponse.data) {
                  const results = resultsResponse.data;
                  
                  // Update package hierarchy with results
                  setPackageHierarchy(prev => {
                    const updatedCategories = { ...prev.categories };
                    
                    // Update file statuses and counts from results
                    Object.values(updatedCategories).forEach(category => {
                      category.products.forEach(product => {
                        product.documents.forEach((doc, index) => {
                          const fileResult = results.files?.find((f: any) => f.fileName === doc.name);
                          if (fileResult) {
                            product.documents[index] = {
                              ...doc,
                              status: fileResult.status === 'completed' ? 'Completed' : 'Failed',
                              nodesCount: fileResult.nodesCount || 0,
                              relationshipsCount: fileResult.relationshipsCount || 0,
                              processingTotalTime: fileResult.processingTime || 0,
                              errorMessage: fileResult.errorMessage
                            };
                          }
                        });
                      });
                    });
                    
                    return { ...prev, categories: updatedCategories };
                  });

                  // Set comprehensive results for PackageResultsViewer
                  const comprehensiveResults = {
                    packageId,
                    packageName,
                    totalFiles: status.totalDocuments,
                    processedFiles: status.processedDocuments,
                    successCount: results.successCount || 0,
                    failureCount: results.failureCount || 0,
                    processingTime: status.endTime && status.startTime ? 
                      new Date(status.endTime).getTime() - new Date(status.startTime).getTime() : 0,
                    totalNodes: results.totalNodes || 0,
                    totalRelationships: results.totalRelationships || 0,
                    results: results.files || [],
                    documentTypes: results.documentTypes || [],
                    categories: results.categories || [],
                    navigationData: results.navigationData || []
                  };

                  setProcessingResults(comprehensiveResults);
                  setShowResults(true);
                  
                  showSuccessToast(`Package processing completed: ${results.successCount || 0} successful, ${results.failureCount || 0} failed`);
                } else {
                  showErrorToast('Failed to fetch processing results');
                }
              } else {
                showErrorToast(`Package processing failed: ${status.error || 'Unknown error'}`);
              }
              
              setIsProcessing(false);
              if (onProcessingComplete) {
                onProcessingComplete();
              }
            }
          }
          
          // Check for timeout
          if (pollCount >= maxPolls) {
            clearInterval(statusPolling);
            setIsProcessing(false);
            showErrorToast('Package processing timed out');
          }
        } catch (error) {
          console.error('Status polling error:', error);
          if (pollCount >= 5) { // Stop after 5 failed polls
            clearInterval(statusPolling);
            setIsProcessing(false);
            showErrorToast('Failed to monitor processing status');
          }
        }
      }, pollInterval);

    } catch (error: any) {
      console.error('Package processing error:', error);
      if (error.message.includes('save package')) {
        showErrorToast(`Failed to save package to database: ${error.message}`);
      } else {
        showErrorToast(`Package processing failed: ${error.message}`);
      }
      setIsProcessing(false);
      if (onProcessingComplete) {
        onProcessingComplete();
      }
    }
  }, [packageHierarchy, model, selectedNodes, selectedRels]);

  // Check if package has files ready to process
  const canProcessPackage = useMemo(() => {
    if (isProcessing) return false;
    
    const allFiles: CustomFile[] = [];
    Object.values(packageHierarchy.categories).forEach(category => {
      category.products.forEach(product => {
        allFiles.push(...product.documents);
      });
    });

    // Allow processing for New, Failed, and Ready to Reprocess files
    return allFiles.some(file => 
      file.status === 'New' || 
      file.status === 'Failed' || 
      file.status === 'Ready to Reprocess'
    );
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

  // Helper functions for database package structure (using backend document types)
  const getExpectedStructure = (docType: string) => {
    const structures = {
      'guidelines': ['sections', 'subsections', 'rules', 'conditions'],
      'matrix': ['table', 'rows', 'columns', 'decision_logic'],
      'rate_sheet': ['rates', 'criteria', 'conditions', 'exceptions'],
    };
    return structures[docType] || structures['guidelines'];
  };

  const getRequiredSections = (docType: string) => {
    const sections = {
      'guidelines': ['Purpose', 'Scope', 'Requirements', 'Procedures'],
      'matrix': ['Criteria', 'Conditions', 'Outcomes', 'Exceptions'],
      'rate_sheet': ['Rate Table', 'Criteria', 'Conditions', 'Exceptions'],
    };
    return sections[docType] || sections['guidelines'];
  };

  const getValidationSchema = (docType: string) => {
    const schemas = {
      'guidelines': {
        required_fields: ['title', 'sections', 'requirements'],
        validation_rules: ['has_numbered_sections', 'contains_conditions']
      },
      'matrix': {
        required_fields: ['table_structure', 'decision_logic'],
        validation_rules: ['has_table_format', 'contains_decision_rules']
      },
      'rate_sheet': {
        required_fields: ['rate_table', 'criteria', 'conditions'],
        validation_rules: ['has_rate_table', 'contains_criteria']
      }
    };
    return schemas[docType] || schemas['guidelines'];
  };

  // Handlers for results viewer integration
  const handleStartChat = useCallback((packageContext: any) => {
    if (onStartChat) {
      onStartChat(packageContext);
    }
    showSuccessToast('Starting chat with package context...');
  }, [onStartChat]);

  // Reset package state
  const handleResetPackage = useCallback(() => {
    // Clear the package hierarchy state
    setPackageHierarchy({
      categories: {},
      flattenedItems: [],
      totalFiles: 0,
      totalCategories: 0,
      totalProducts: 0
    });
    
    // Clear any processing state
    setIsProcessing(false);
    setProcessingResults(null);
    setShowResults(false);
    
    // Clear selection context
    setSelectionContext({
      selectionType: 'none',
      selectedCategory: null,
      selectedProduct: null
    });
    
    // Clear any stored package data from localStorage
    localStorage.removeItem('packageHierarchy');
    localStorage.removeItem('packageData');
    localStorage.removeItem('selectedFiles');
    
    showSuccessToast('Package workspace reset successfully');
  }, []);

  // Register package processing handler with parent component
  useEffect(() => {
    console.log('PackageWorkspace registering handler with parent', { onProcessPackage, handleProcessPackage });
    if (onProcessPackage) {
      onProcessPackage(handleProcessPackage);
    }
  }, [onProcessPackage, handleProcessPackage]);

  const handleViewGraph = useCallback((packageId: string) => {
    if (onViewGraph) {
      onViewGraph(packageId);
    }
    showSuccessToast('Opening graph view...');
  }, [onViewGraph]);

  const handleBackToPackage = useCallback(() => {
    setShowResults(false);
    setProcessingResults(null);
  }, []);

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

  // If results are available and should be shown, display the results viewer
  if (showResults && processingResults) {
    return (
      <Box className={className}>
        <Box mb={2}>
          <Button
            variant="outlined"
            onClick={handleBackToPackage}
            sx={{ mb: 2 }}
          >
            ← Back to Package
          </Button>
        </Box>
        <PackageResultsViewer
          packageId={processingResults.packageId}
          processingResult={processingResults}
          onStartChat={handleStartChat}
          onViewGraph={handleViewGraph}
        />
      </Box>
    );
  }

  return (
    <Box className={className} sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Package Action Bar */}
      <PackageActionBar
        selectionContext={selectionContext}
        onAddCategory={handleAddCategory}
        onAddProduct={handleAddProduct}
        onExportPackage={handleSavePackage}
        onImportPackage={handleImportPackage}
        onResetPackage={handleResetPackage}
        selectedItems={hierarchyData.filter(item => 
          selectionContext.selectionType !== 'none' && (
            item.id === selectionContext.selectedCategory?.id ||
            item.id === selectionContext.selectedProduct?.id
          )
        )}
      />

      {/* Main Content Area */}
      <Box display="flex" gap={2} sx={{ flex: 1, minHeight: 0, maxHeight: 'calc(100vh - 200px)', overflow: 'hidden' }}>
        {/* Left Panel - Package Structure */}
        <Box flex={2} display="flex" flexDirection="column">
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Package Management Header and Actions */}
            <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
              <Box>
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                  Package Management
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', maxWidth: '600px' }}>
                  Create hierarchical document packages with categories, products, and structured file organization
                </Typography>
              </Box>

              {/* Import/Export Actions */}
              <Box display="flex" gap={1} sx={{ flexShrink: 0, ml: 2 }}>
                <Tooltip title="Import Package Template">
                  <IconButton
                    size="medium"
                    onClick={handleImportPackage}
                    sx={{ p: 1 }}
                  >
                    <ArrowPathIcon sx={{ width: 20, height: 20 }} />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Save Package">
                  <IconButton
                    size="medium"
                    onClick={() => handleSavePackage?.(
                      selectionContext.selectedCategory?.id,
                      selectionContext.selectedProduct?.id
                    )}
                    disabled={!selectionContext.selectedProduct}
                    sx={{ p: 1 }}
                  >
                    <DocumentPlusIcon sx={{ width: 20, height: 20 }} />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Reset Package Workspace">
                  <Button
                    variant="outlined"
                    size="medium"
                    color="error"
                    onClick={handleResetPackage}
                    sx={{ ml: 1, px: 2, py: 1 }}
                  >
                    Reset
                  </Button>
                </Tooltip>
              </Box>
            </Box>

            {/* Package Overview Statistics */}
            {Object.keys(packageHierarchy.categories).length > 0 && (
              <Box mb={2}>
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
                    <Typography variant="body2" color="text.secondary">Processing</Typography>
                    <Typography variant="body1">Package-Aware</Typography>
                  </Box>
                </Box>

                {/* Processing Status */}
                {isProcessing && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Processing Package...</strong><br />
                      Files are being processed with package-aware hierarchical chunking and enhanced entity extraction.
                    </Typography>
                  </Alert>
                )}

                {/* Processing Results */}
                {processingResults && (
                  <Alert severity={processingResults.failureCount > 0 ? 'warning' : 'success'} sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Processing Complete:</strong><br />
                      {processingResults.successCount} successful, {processingResults.failureCount} failed out of {processingResults.processedFiles} files processed
                    </Typography>
                  </Alert>
                )}

              </Box>
            )}

            <Box sx={{ flex: 1, minHeight: 0 }}>
              <HierarchicalPackageTable
                hierarchyData={hierarchyData}
                onSelectionChange={handleSelectionChange}
                onAddCategory={handleAddCategory}
                onAddProduct={handleAddProduct}
                onFileAction={handleFileAction}
                onDocumentTypeChange={handleDocumentTypeChange}
                selectionContext={selectionContext}
              />
            </Box>

            {/* Package Processing Info - positioned after DataGrid but within same container */}
            {canProcessPackage && !isProcessing && (
              <Alert severity="info" variant="outlined" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Ready to Process:</strong> This package contains files that can be processed with package-aware extraction, including hierarchical chunking and enhanced entity relationships.
                </Typography>
              </Alert>
            )}
          </Paper>
        </Box>

        {/* Right Panel - Upload Area */}
        <Box flex={1} display="flex" flexDirection="column">
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            
            {/* Current Selection Context */}
            {(selectionContext.selectedCategory || selectionContext.selectedProduct) && (
              <Box mb={2}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>Current Selection</Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  {selectionContext.selectedCategory && (
                    <Chip 
                      label={`${selectionContext.selectedCategory.name} (${selectionContext.selectedCategory.type})`}
                      color="primary"
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

            
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <ContextualDropZone
                selectionContext={selectionContext}
                onFilesUpload={handleFilesUpload}
                onFileUploadWithType={handleFileUploadWithType}
                packageModeEnabled={true}
              />

              {/* Package Context Info */}
              {selectionContext.selectionType === 'product' && (
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

    </Box>
  );
};
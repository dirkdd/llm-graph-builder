import React, { useState, useMemo, useCallback, useEffect } from 'react';
import {
  DataGrid,
  DataGridComponents,
  Flex,
  IconButton,
  StatusIndicator,
  Typography,
  Checkbox,
  Button
} from '@neo4j-ndl/react';
import {
  Box,
  Chip,
  LinearProgress,
  Select,
  MenuItem,
  FormControl
} from '@mui/material';
import {
  useReactTable,
  getCoreRowModel,
  createColumnHelper,
  getExpandedRowModel,
  ExpandedState,
  Row,
  CellContext
} from '@tanstack/react-table';
import {
  ChevronRight as ChevronRightIcon,
  ExpandMore as ChevronDownIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Description as DocumentIcon,
  MoreHoriz as EllipsisHorizontalIcon,
  Add as PlusIcon
} from '@mui/icons-material';
import { 
  PackageHierarchyItem, 
  PackageSelectionContext, 
  PackageCategory, 
  PackageProduct,
  CustomFile 
} from '../../types';
import { v4 as uuidv4 } from 'uuid';

interface HierarchicalPackageTableProps {
  hierarchyData: PackageHierarchyItem[];
  onSelectionChange: (context: PackageSelectionContext) => void;
  onAddCategory: (type: string, name: string, description?: string) => void;
  onAddProduct: (categoryId: string, name: string, description?: string) => void;
  onFileAction: (fileId: string, action: string) => void;
  onDocumentTypeChange: (fileId: string, documentType: 'Guidelines' | 'Matrix' | 'Supporting' | 'Other') => void;
  selectionContext: PackageSelectionContext;
}

export const HierarchicalPackageTable: React.FC<HierarchicalPackageTableProps> = ({
  hierarchyData,
  onSelectionChange,
  onAddCategory,
  onAddProduct,
  onFileAction,
  onDocumentTypeChange,
  selectionContext
}) => {
  const [expanded, setExpanded] = useState<ExpandedState>({});
  const [selectedRows, setSelectedRows] = useState<Record<string, boolean>>({});
  
  const columnHelper = createColumnHelper<PackageHierarchyItem>();

  // Auto-expand categories when they're created
  useEffect(() => {
    const categoryIds = hierarchyData
      .filter(item => item.type === 'category')
      .reduce((acc, item) => ({ ...acc, [item.id]: true }), {});
    
    setExpanded(prev => ({ ...prev, ...categoryIds }));
  }, [hierarchyData]);

  const handleRowSelect = useCallback((row: Row<PackageHierarchyItem>) => {
    const item = row.original;
    const newSelection = { ...selectedRows };
    
    // Clear previous selections for single-select behavior
    Object.keys(newSelection).forEach(key => {
      newSelection[key] = false;
    });
    
    newSelection[item.id] = true;
    setSelectedRows(newSelection);

    // Update selection context
    let newContext: PackageSelectionContext = {
      selectionType: 'none'
    };

    if (item.type === 'category') {
      newContext = {
        selectedCategory: item.data as PackageCategory,
        selectionType: 'category'
      };
    } else if (item.type === 'product') {
      const category = hierarchyData.find(h => h.id === item.parentId)?.data as PackageCategory;
      newContext = {
        selectedCategory: category,
        selectedProduct: item.data as PackageProduct,
        selectionType: 'product'
      };
    } else if (item.type === 'file') {
      const product = hierarchyData.find(h => h.id === item.parentId);
      const category = product ? hierarchyData.find(h => h.id === product.parentId)?.data as PackageCategory : undefined;
      newContext = {
        selectedCategory: category,
        selectedProduct: product?.data as PackageProduct,
        selectedFiles: [item.data as CustomFile],
        selectionType: 'file'
      };
    }

    onSelectionChange(newContext);
  }, [selectedRows, hierarchyData, onSelectionChange]);

  const getRowIcon = (item: PackageHierarchyItem, isExpanded: boolean) => {
    if (item.type === 'category') {
      return isExpanded ? <FolderOpenIcon sx={{ width: 16, height: 16 }} /> : <FolderIcon sx={{ width: 16, height: 16 }} />;
    } else if (item.type === 'product') {
      return <FolderIcon sx={{ width: 16, height: 16, opacity: 0.7 }} />;
    } else {
      return <DocumentIcon sx={{ width: 16, height: 16 }} />;
    }
  };

  const getCategoryColor = (type: string) => {
    const colors: Record<string, 'primary' | 'secondary' | 'success' | 'warning'> = {
      'NQM': 'primary',
      'RTL': 'secondary',
      'SBC': 'success',
      'CONV': 'warning'
    };
    return colors[type] || 'primary';
  };

  const getFileStatus = (file: CustomFile) => {
    const statusMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
      'Completed': 'success',
      'Processing': 'warning',
      'Failed': 'danger',
      'New': 'info',
      'Uploading': 'warning'
    };
    return statusMap[file.status] || 'info';
  };

  const columns = useMemo(() => [
    columnHelper.accessor('name', {
      id: 'name',
      header: 'Name',
      cell: (info: CellContext<PackageHierarchyItem, string>) => {
        const { row } = info;
        const item = row.original;
        const canExpand = row.getCanExpand();
        const isExpanded = row.getIsExpanded();
        const depth = row.depth;

        return (
          <Box 
            display="flex" 
            alignItems="center" 
            gap={1}
            style={{ 
              paddingLeft: `${depth * 24}px`,
              cursor: 'pointer'
            }}
            onClick={() => handleRowSelect(row)}
          >
            {/* Expand/Collapse Icon */}
            {canExpand && (
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  row.getToggleExpandedHandler()();
                }}
                style={{ padding: '2px' }}
              >
                {isExpanded ? <ChevronDownIcon sx={{ width: 12, height: 12 }} /> : <ChevronRightIcon sx={{ width: 12, height: 12 }} />}
              </IconButton>
            )}
            
            {/* Item Icon */}
            <Box display="flex" alignItems="center">
              {getRowIcon(item, isExpanded)}
            </Box>
            
            {/* Item Name */}
            <Typography 
              variant="body-medium" 
              style={{ 
                fontWeight: item.type === 'category' ? 600 : item.type === 'product' ? 500 : 400,
                color: selectedRows[item.id] ? 'var(--theme-palette-primary-text)' : undefined
              }}
            >
              {info.getValue()}
            </Typography>
            
            {/* Type Chips */}
            {item.type === 'category' && (
              <Chip 
                label={(item.data as PackageCategory).type}
                color={getCategoryColor((item.data as PackageCategory).type)}
                size="small"
              />
            )}
          </Box>
        );
      },
      size: 400
    }),

    columnHelper.accessor('type', {
      id: 'type',
      header: 'Type',
      cell: (info) => {
        const item = info.row.original;
        const typeLabels = {
          'category': 'Category',
          'product': 'Product',
          'file': 'Document'
        };
        return (
          <Typography variant="body-medium" color="text.secondary">
            {typeLabels[item.type]}
          </Typography>
        );
      },
      size: 100
    }),

    columnHelper.accessor((row) => row, {
      id: 'status',
      header: 'Status',
      cell: (info) => {
        const item = info.getValue();
        
        if (item.type === 'file') {
          const file = item.data as CustomFile;
          return (
            <Box display="flex" alignItems="center" gap={1}>
              <StatusIndicator type={getFileStatus(file)} />
              <Typography variant="body-small">{file.status}</Typography>
            </Box>
          );
        } else if (item.type === 'product') {
          const product = item.data as PackageProduct;
          const completionPercentage = product.completionStatus?.completionPercentage || 0;
          return (
            <Box display="flex" alignItems="center" gap={1}>
              <LinearProgress 
                variant="determinate" 
                value={completionPercentage} 
                sx={{ width: 60, height: 4 }}
              />
              <Typography variant="body-small">{completionPercentage}%</Typography>
            </Box>
          );
        } else if (item.type === 'category') {
          const category = item.data as PackageCategory;
          const productCount = category.products?.length || 0;
          return (
            <Typography variant="body-small" color="text.secondary">
              {productCount} product{productCount !== 1 ? 's' : ''}
            </Typography>
          );
        }
        
        return null;
      },
      size: 150
    }),

    // Document Type Column (only for files)
    columnHelper.accessor((row) => row, {
      id: 'documentType',
      header: 'Document Type',
      cell: (info) => {
        const item = info.getValue();
        
        if (item.type === 'file') {
          const file = item.data as CustomFile;
          return (
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <Select
                value={file.document_type || 'Other'}
                onChange={(e) => {
                  e.stopPropagation();
                  onDocumentTypeChange(item.id, e.target.value as 'Guidelines' | 'Matrix' | 'Supporting' | 'Other');
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <MenuItem value="Guidelines">Guidelines</MenuItem>
                <MenuItem value="Matrix">Matrix</MenuItem>
                <MenuItem value="Supporting">Supporting</MenuItem>
                <MenuItem value="Other">Other</MenuItem>
              </Select>
            </FormControl>
          );
        }
        
        return null;
      },
      size: 140
    }),

    columnHelper.accessor((row) => row, {
      id: 'actions',
      header: 'Actions',
      cell: (info) => {
        const item = info.getValue();
        
        return (
          <Box display="flex" alignItems="center" gap={1}>
            {item.type === 'category' && (
              <Button
                size="small"
                variant="outlined"
                onClick={(e) => {
                  e.stopPropagation();
                  // Select the category to trigger the UI flow for adding a product
                  handleRowSelect(info.row);
                }}
              >
                <PlusIcon sx={{ width: 12, height: 12, marginRight: 0.5 }} />
                Add
              </Button>
            )}
            
            {item.type === 'file' && (
              <>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onFileAction(item.id, 'view');
                  }}
                  title="View file details"
                >
                  <DocumentIcon sx={{ width: 16, height: 16 }} />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Show context menu for file actions
                  }}
                  title="More actions"
                >
                  <EllipsisHorizontalIcon sx={{ width: 16, height: 16 }} />
                </IconButton>
              </>
            )}
          </Box>
        );
      },
      size: 150
    })
  ], [selectedRows, handleRowSelect, onAddProduct, onFileAction]);

  const table = useReactTable({
    data: hierarchyData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    state: {
      expanded,
    },
    onExpandedChange: setExpanded,
    getSubRows: (row) => row.children || [],
    enableExpanding: true,
    getRowId: (row) => row.id,
  });


  if (hierarchyData.length === 0) {
    return (
      <Box 
        display="flex" 
        flexDirection="column" 
        alignItems="center" 
        justifyContent="center"
        p={4}
        textAlign="center"
      >
        <FolderIcon style={{ fontSize: 64, opacity: 0.3 }} />
        <Typography variant="h6" color="text.secondary" style={{ marginTop: 16 }}>
          No packages created yet
        </Typography>
        <Typography variant="body-medium" color="text.secondary" style={{ marginBottom: 16 }}>
          Create your first mortgage category to get started
        </Typography>
        <Button
          variant="contained"
          onClick={() => {
            const categoryName = prompt('Category name:');
            const categoryType = prompt('Category type (NQM/RTL/SBC/CONV):') as any;
            if (categoryName && categoryType) {
              onAddCategory(categoryType, categoryName);
            }
          }}
        >
          <PlusIcon sx={{ width: 16, height: 16, marginRight: 1 }} />
          Add First Category
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', width: '100%', display: 'flex', flexDirection: 'column' }}>
      <DataGrid
        tableInstance={table}
        isResizable={true}
        styling={{
          borderStyle: 'all-sides',
          hasZebraStriping: false,
          headerStyle: 'clean',
        }}
        rootProps={{
          style: {
            height: '100%',
            width: '100%',
            flex: 1,
            minHeight: 0 // Allow flex to control height
          }
        }}
        components={{
          Body: () => (
            <DataGridComponents.Body
              innerProps={{
                style: {
                  backgroundColor: 'var(--theme-palette-neutral-bg-weak)'
                }
              }}
            />
          ),
        }}
      />
    </Box>
  );
};
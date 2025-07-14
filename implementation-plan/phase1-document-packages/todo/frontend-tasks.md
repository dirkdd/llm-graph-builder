# Frontend Tasks - Detailed Implementation Guide

## Overview
8 frontend tasks implementing user interfaces for package management, enhanced upload flow, navigation visualization, and seamless integration with existing UI patterns.

---

# Phase 1.5: Frontend Integration (Tasks 17-24)

## Task 17: Create Package Management Components
**Duration**: 4 hours | **Priority**: Critical | **Dependencies**: Task 6 (Backend API)

### Implementation Steps

1. **Create PackageManager component structure** (60 min)
   ```typescript
   // frontend/src/components/PackageManager/PackageManager.tsx
   import React, { useState, useEffect, useContext } from 'react';
   import {
     Box,
     Typography,
     Button,
     MenuItem,
     Select as MUISelect,
     FormControl,
     InputLabel,
     Dialog,
     DialogTitle,
     DialogContent,
     IconButton
   } from '@neo4j-ndl/react';
   import { CustomModal } from '../HOC/CustomModal';
   import { UserCredentialsContext } from '../../context/UserCredentials';
   import { PackageList } from './PackageList';
   import { PackageCreator } from './PackageCreator';
   import { getDocumentPackages } from '../../services/PackageAPI';
   import { showSuccessToast, showErrorToast } from '../../utils/Toasts';
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
     const { userCredentials } = useContext(UserCredentialsContext);
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
         if (response.status === 'success') {
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
         <CustomModal isOpen={isOpen} onClose={onClose} size="large">
           <DialogTitle>
             <Box display="flex" justifyContent="space-between" alignItems="center">
               <Typography variant="h6">Document Package Manager</Typography>
               <IconButton onClick={onClose} size="small">
                 <CloseIcon />
               </IconButton>
             </Box>
           </DialogTitle>
           <DialogContent>
             <Box p={2}>
               {/* Category Filter */}
               <Box mb={3}>
                 <FormControl fullWidth size="small">
                   <InputLabel>Filter by Category</InputLabel>
                   <MUISelect
                     value={selectedCategory}
                     onChange={(e) => setSelectedCategory(e.target.value)}
                     displayEmpty
                   >
                     <MenuItem value="">All Categories</MenuItem>
                     <MenuItem value="NQM">Non-QM</MenuItem>
                     <MenuItem value="RTL">Rental/Investment</MenuItem>
                     <MenuItem value="SBC">Small Balance Commercial</MenuItem>
                     <MenuItem value="CONV">Conventional</MenuItem>
                   </MUISelect>
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
               <Box display="flex" gap={2} mt={3} justifyContent="flex-end">
                 <Button 
                   variant="outlined" 
                   onClick={() => setShowCreator(true)}
                   disabled={loading}
                 >
                   Create New Package
                 </Button>
                 <Button variant="outlined" disabled>
                   Import Template
                 </Button>
               </Box>
             </Box>
           </DialogContent>
         </CustomModal>
   
         {/* Package Creator Modal */}
         <PackageCreator
           isOpen={showCreator}
           onClose={() => setShowCreator(false)}
           onPackageCreated={handlePackageCreated}
         />
       </>
     );
   };
   ```

2. **Create PackageList component** (45 min)
   ```typescript
   // frontend/src/components/PackageManager/PackageList.tsx
   import React from 'react';
   import {
     Box,
     Card,
     CardContent,
     Typography,
     Chip,
     Button,
     Grid,
     Skeleton,
     IconButton,
     Tooltip
   } from '@neo4j-ndl/react';
   import EditIcon from '@mui/icons-material/Edit';
   import FileCopyIcon from '@mui/icons-material/FileCopy';
   import FolderIcon from '@mui/icons-material/Folder';
   import { DocumentPackage } from '../../types';
   
   interface PackageListProps {
     packages: DocumentPackage[];
     loading: boolean;
     onSelect: (packageId: string) => void;
     onEdit: (packageId: string) => void;
     onClone: (packageId: string) => void;
   }
   
   export const PackageList: React.FC<PackageListProps> = ({
     packages,
     loading,
     onSelect,
     onEdit,
     onClone
   }) => {
     if (loading) {
       return (
         <Grid container spacing={2}>
           {[1, 2, 3].map((item) => (
             <Grid item xs={12} sm={6} md={4} key={item}>
               <Card>
                 <CardContent>
                   <Skeleton variant="text" width="80%" height={24} />
                   <Skeleton variant="text" width="60%" height={20} />
                   <Skeleton variant="rectangular" width="100%" height={60} sx={{ mt: 1 }} />
                 </CardContent>
               </Card>
             </Grid>
           ))}
         </Grid>
       );
     }
   
     if (packages.length === 0) {
       return (
         <Box 
           display="flex" 
           flexDirection="column" 
           alignItems="center" 
           justifyContent="center"
           py={6}
         >
           <FolderIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
           <Typography variant="h6" color="text.secondary" gutterBottom>
             No packages found
           </Typography>
           <Typography variant="body2" color="text.secondary">
             Create your first document package to get started
           </Typography>
         </Box>
       );
     }
   
     const getCategoryColor = (category: string) => {
       const colors: Record<string, 'primary' | 'secondary' | 'success' | 'warning'> = {
         'NQM': 'primary',
         'RTL': 'secondary', 
         'SBC': 'success',
         'CONV': 'warning'
       };
       return colors[category] || 'primary';
     };
   
     return (
       <Grid container spacing={2}>
         {packages.map((pkg) => (
           <Grid item xs={12} sm={6} md={4} key={pkg.package_id}>
             <Card 
               sx={{ 
                 height: '100%',
                 cursor: 'pointer',
                 '&:hover': { boxShadow: 3 }
               }}
               onClick={() => onSelect(pkg.package_id)}
             >
               <CardContent>
                 <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                   <Typography variant="h6" component="h3" noWrap>
                     {pkg.package_name}
                   </Typography>
                   <Box display="flex" gap={0.5}>
                     <Tooltip title="Edit Package">
                       <IconButton 
                         size="small" 
                         onClick={(e) => {
                           e.stopPropagation();
                           onEdit(pkg.package_id);
                         }}
                       >
                         <EditIcon fontSize="small" />
                       </IconButton>
                     </Tooltip>
                     <Tooltip title="Clone Package">
                       <IconButton 
                         size="small"
                         onClick={(e) => {
                           e.stopPropagation();
                           onClone(pkg.package_id);
                         }}
                       >
                         <FileCopyIcon fontSize="small" />
                       </IconButton>
                     </Tooltip>
                   </Box>
                 </Box>
                 
                 <Box display="flex" gap={1} mb={2}>
                   <Chip 
                     label={pkg.category} 
                     color={getCategoryColor(pkg.category)}
                     size="small"
                   />
                   <Chip 
                     label={`v${pkg.version}`} 
                     variant="outlined"
                     size="small"
                   />
                 </Box>
   
                 <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                   {pkg.documents?.length || 0} document(s) • {pkg.template_type}
                 </Typography>
   
                 <Typography variant="caption" color="text.secondary">
                   Created: {new Date(pkg.created_at).toLocaleDateString()}
                 </Typography>
               </CardContent>
             </Card>
           </Grid>
         ))}
       </Grid>
     );
   };
   ```

3. **Create PackageCreator component** (75 min)
   ```typescript
   // frontend/src/components/PackageManager/PackageCreator.tsx
   import React, { useState, useEffect } from 'react';
   import {
     Box,
     Button,
     TextField,
     FormControl,
     InputLabel,
     Select as MUISelect,
     MenuItem,
     Typography,
     Paper,
     Accordion,
     AccordionSummary,
     AccordionDetails,
     Chip,
     FormHelperText
   } from '@neo4j-ndl/react';
   import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
   import { CustomModal } from '../HOC/CustomModal';
   import { createDocumentPackage } from '../../services/PackageAPI';
   import { showErrorToast } from '../../utils/Toasts';
   import { DocumentPackage, PackageFormData } from '../../types';
   
   interface PackageCreatorProps {
     isOpen: boolean;
     onClose: () => void;
     templateType?: string;
     onPackageCreated: (packageData: DocumentPackage) => void;
   }
   
   const MORTGAGE_CATEGORIES = [
     { value: 'NQM', label: 'Non-QM', description: 'Non-Qualified Mortgage programs' },
     { value: 'RTL', label: 'Rental/Investment', description: 'Rental and investment property loans' },
     { value: 'SBC', label: 'Small Balance Commercial', description: 'Small commercial property loans' },
     { value: 'CONV', label: 'Conventional', description: 'Conventional mortgage programs' }
   ];
   
   const TEMPLATES_BY_CATEGORY: Record<string, Array<{value: string, label: string}>> = {
     'NQM': [
       { value: 'NQM_STANDARD', label: 'Standard Non-QM Template' },
       { value: 'NQM_FOREIGN_NATIONAL', label: 'Foreign National Template' },
       { value: 'NQM_ASSET_DEPLETION', label: 'Asset Depletion Template' }
     ],
     'RTL': [
       { value: 'RTL_STANDARD', label: 'Standard Rental Template' },
       { value: 'RTL_DSCR', label: 'DSCR Rental Template' }
     ],
     'SBC': [
       { value: 'SBC_STANDARD', label: 'Standard SBC Template' }
     ],
     'CONV': [
       { value: 'CONV_STANDARD', label: 'Standard Conventional Template' }
     ]
   };
   
   export const PackageCreator: React.FC<PackageCreatorProps> = ({ 
     isOpen, 
     onClose, 
     templateType, 
     onPackageCreated 
   }) => {
     const [formData, setFormData] = useState<PackageFormData>({
       package_name: '',
       category: templateType || '',
       template: '',
       customizations: {}
     });
     const [loading, setLoading] = useState(false);
     const [errors, setErrors] = useState<Record<string, string>>({});
   
     useEffect(() => {
       if (templateType) {
         setFormData(prev => ({ ...prev, category: templateType }));
       }
     }, [templateType]);
   
     const validateForm = (): boolean => {
       const newErrors: Record<string, string> = {};
   
       if (!formData.package_name.trim()) {
         newErrors.package_name = 'Package name is required';
       }
   
       if (!formData.category) {
         newErrors.category = 'Category is required';
       }
   
       if (!formData.template) {
         newErrors.template = 'Template is required';
       }
   
       setErrors(newErrors);
       return Object.keys(newErrors).length === 0;
     };
   
     const handleSubmit = async () => {
       if (!validateForm()) {
         return;
       }
   
       setLoading(true);
       try {
         const response = await createDocumentPackage(formData);
         if (response.status === 'success') {
           onPackageCreated(response.data);
           handleClose();
         } else {
           showErrorToast(response.error || 'Failed to create package');
         }
       } catch (error) {
         showErrorToast('Failed to create package');
       } finally {
         setLoading(false);
       }
     };
   
     const handleClose = () => {
       setFormData({
         package_name: '',
         category: '',
         template: '',
         customizations: {}
       });
       setErrors({});
       onClose();
     };
   
     const availableTemplates = formData.category ? TEMPLATES_BY_CATEGORY[formData.category] || [] : [];
     const selectedCategory = MORTGAGE_CATEGORIES.find(cat => cat.value === formData.category);
   
     return (
       <CustomModal isOpen={isOpen} onClose={handleClose} size="medium">
         <Box p={3}>
           <Typography variant="h6" mb={3}>Create New Document Package</Typography>
   
           <Box component="form" noValidate>
             {/* Package Name */}
             <TextField
               fullWidth
               label="Package Name"
               value={formData.package_name}
               onChange={(e) => setFormData({...formData, package_name: e.target.value})}
               margin="normal"
               required
               error={!!errors.package_name}
               helperText={errors.package_name}
               placeholder="e.g., NQM Titanium Advantage Package"
             />
   
             {/* Category Selection */}
             <FormControl fullWidth margin="normal" error={!!errors.category}>
               <InputLabel required>Mortgage Category</InputLabel>
               <MUISelect
                 value={formData.category}
                 onChange={(e) => setFormData({...formData, category: e.target.value, template: ''})}
                 required
               >
                 {MORTGAGE_CATEGORIES.map((category) => (
                   <MenuItem key={category.value} value={category.value}>
                     <Box>
                       <Typography variant="body2">{category.label}</Typography>
                       <Typography variant="caption" color="text.secondary">
                         {category.description}
                       </Typography>
                     </Box>
                   </MenuItem>
                 ))}
               </MUISelect>
               {errors.category && <FormHelperText>{errors.category}</FormHelperText>}
             </FormControl>
   
             {/* Template Selection */}
             {formData.category && (
               <FormControl fullWidth margin="normal" error={!!errors.template}>
                 <InputLabel required>Base Template</InputLabel>
                 <MUISelect
                   value={formData.template}
                   onChange={(e) => setFormData({...formData, template: e.target.value})}
                   required
                 >
                   {availableTemplates.map((template) => (
                     <MenuItem key={template.value} value={template.value}>
                       {template.label}
                     </MenuItem>
                   ))}
                 </MUISelect>
                 {errors.template && <FormHelperText>{errors.template}</FormHelperText>}
               </FormControl>
             )}
   
             {/* Category Description */}
             {selectedCategory && (
               <Paper sx={{ p: 2, mt: 2, bgcolor: 'background.default' }}>
                 <Box display="flex" alignItems="center" gap={1} mb={1}>
                   <Chip label={selectedCategory.label} color="primary" size="small" />
                   <Typography variant="subtitle2">Category Overview</Typography>
                 </Box>
                 <Typography variant="body2" color="text.secondary">
                   {selectedCategory.description}
                 </Typography>
               </Paper>
             )}
   
             {/* Customization Options (Collapsed by default) */}
             {formData.template && (
               <Accordion sx={{ mt: 2 }}>
                 <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                   <Typography variant="subtitle2">Advanced Customizations (Optional)</Typography>
                 </AccordionSummary>
                 <AccordionDetails>
                   <Typography variant="body2" color="text.secondary" mb={2}>
                     Customize the template to add additional sections or modify default settings.
                   </Typography>
                   
                   <TextField
                     fullWidth
                     label="Additional Sections (comma-separated)"
                     placeholder="e.g., Foreign National Requirements, Specialty Programs"
                     margin="normal"
                     size="small"
                     onChange={(e) => {
                       const sections = e.target.value.split(',').map(s => s.trim()).filter(Boolean);
                       setFormData(prev => ({
                         ...prev,
                         customizations: { ...prev.customizations, additional_sections: sections }
                       }));
                     }}
                   />
                 </AccordionDetails>
               </Accordion>
             )}
   
             {/* Action Buttons */}
             <Box display="flex" gap={2} mt={4} justifyContent="flex-end">
               <Button variant="outlined" onClick={handleClose} disabled={loading}>
                 Cancel
               </Button>
               <Button 
                 variant="contained" 
                 onClick={handleSubmit}
                 disabled={loading}
               >
                 {loading ? 'Creating...' : 'Create Package'}
               </Button>
             </Box>
           </Box>
         </Box>
       </CustomModal>
     );
   };
   ```

4. **Add component exports and index** (15 min)
   ```typescript
   // frontend/src/components/PackageManager/index.ts
   export { PackageManager } from './PackageManager';
   export { PackageCreator } from './PackageCreator';
   export { PackageList } from './PackageList';
   ```

5. **Create component tests** (45 min)
   ```typescript
   // frontend/src/components/PackageManager/__tests__/PackageManager.test.tsx
   import React from 'react';
   import { render, screen, fireEvent, waitFor } from '@testing-library/react';
   import { PackageManager } from '../PackageManager';
   import { UserCredentialsContext } from '../../../context/UserCredentials';
   import { getDocumentPackages } from '../../../services/PackageAPI';
   
   // Mock API
   jest.mock('../../../services/PackageAPI');
   const mockGetDocumentPackages = getDocumentPackages as jest.MockedFunction<typeof getDocumentPackages>;
   
   const mockUserCredentials = {
     uri: 'neo4j://localhost',
     user: 'test',
     password: 'test',
     database: 'neo4j'
   };
   
   const mockPackages = [
     {
       package_id: 'pkg_nqm_001',
       package_name: 'Test NQM Package',
       category: 'NQM',
       version: '1.0.0',
       status: 'ACTIVE',
       created_at: '2024-01-01T00:00:00Z',
       template_type: 'NQM_STANDARD',
       documents: []
     }
   ];
   
   const renderWithContext = (component: React.ReactElement) => {
     return render(
       <UserCredentialsContext.Provider value={{ userCredentials: mockUserCredentials, setUserCredentials: jest.fn() }}>
         {component}
       </UserCredentialsContext.Provider>
     );
   };
   
   describe('PackageManager', () => {
     beforeEach(() => {
       jest.clearAllMocks();
       mockGetDocumentPackages.mockResolvedValue({
         status: 'success',
         data: mockPackages
       });
     });
   
     it('renders package manager modal when open', async () => {
       renderWithContext(
         <PackageManager 
           isOpen={true} 
           onClose={jest.fn()} 
           onPackageSelected={jest.fn()} 
         />
       );
   
       expect(screen.getByText('Document Package Manager')).toBeInTheDocument();
       expect(screen.getByText('Filter by Category')).toBeInTheDocument();
     });
   
     it('loads packages on mount', async () => {
       renderWithContext(
         <PackageManager 
           isOpen={true} 
           onClose={jest.fn()} 
           onPackageSelected={jest.fn()} 
         />
       );
   
       await waitFor(() => {
         expect(mockGetDocumentPackages).toHaveBeenCalledWith(undefined);
         expect(screen.getByText('Test NQM Package')).toBeInTheDocument();
       });
     });
   
     it('filters packages by category', async () => {
       renderWithContext(
         <PackageManager 
           isOpen={true} 
           onClose={jest.fn()} 
           onPackageSelected={jest.fn()} 
         />
       );
   
       const categorySelect = screen.getByRole('combobox');
       fireEvent.mouseDown(categorySelect);
       fireEvent.click(screen.getByText('Non-QM'));
   
       await waitFor(() => {
         expect(mockGetDocumentPackages).toHaveBeenCalledWith('NQM');
       });
     });
   
     it('opens package creator when create button clicked', async () => {
       renderWithContext(
         <PackageManager 
           isOpen={true} 
           onClose={jest.fn()} 
           onPackageSelected={jest.fn()} 
         />
       );
   
       const createButton = screen.getByText('Create New Package');
       fireEvent.click(createButton);
   
       expect(screen.getByText('Create New Document Package')).toBeInTheDocument();
     });
   });
   ```

### Acceptance Criteria Checklist
- [ ] PackageManager.tsx with modal integration using CustomModal
- [ ] PackageCreator.tsx with form validation and error handling
- [ ] PackageList.tsx with filtering, actions, and responsive grid layout
- [ ] Integration with existing CustomModal and UI patterns
- [ ] Material-UI component consistency with NDL design system
- [ ] Responsive design supporting mobile and desktop
- [ ] Component tests with Jest/RTL covering main interactions

---

## Task 18: Enhance Upload Flow
**Duration**: 3 hours | **Priority**: High | **Dependencies**: Task 17

### Implementation Steps

1. **Create EnhancedDropZone component** (90 min)
   ```typescript
   // frontend/src/components/DataSources/Local/EnhancedDropZone.tsx
   import React, { useState, useContext } from 'react';
   import {
     Box,
     Button,
     Chip,
     ToggleButton,
     ToggleButtonGroup,
     Typography,
     Alert,
     Paper
   } from '@neo4j-ndl/react';
   import { DropZone, DropZoneProps } from './DropZone';
   import { PackageManager } from '../../PackageManager';
   import { PackageContext } from '../../../context/PackageContext';
   import { DocumentPackage } from '../../../types';
   import FolderSpecialIcon from '@mui/icons-material/FolderSpecial';
   import CloudUploadIcon from '@mui/icons-material/CloudUpload';
   
   interface EnhancedDropZoneProps extends Omit<DropZoneProps, 'onFilesDropped'> {
     packageId?: string;
     enablePackageSelection?: boolean;
     onFilesDropped?: (files: File[], packageId?: string) => void;
     onPackageUpload?: (files: File[], packageId: string) => void;
   }
   
   type UploadMode = 'standard' | 'package';
   
   export const EnhancedDropZone: React.FC<EnhancedDropZoneProps> = ({ 
     packageId, 
     enablePackageSelection = true,
     onFilesDropped,
     onPackageUpload,
     ...dropZoneProps 
   }) => {
     const { selectedPackage, packages } = useContext(PackageContext);
     const [uploadMode, setUploadMode] = useState<UploadMode>('standard');
     const [localSelectedPackage, setLocalSelectedPackage] = useState<string | null>(
       packageId || selectedPackage?.package_id || null
     );
     const [showPackageManager, setShowPackageManager] = useState(false);
   
     const handleModeChange = (event: React.MouseEvent<HTMLElement>, newMode: UploadMode | null) => {
       if (newMode !== null) {
         setUploadMode(newMode);
       }
     };
   
     const handleFilesDropped = (files: File[]) => {
       if (uploadMode === 'package' && localSelectedPackage) {
         // Package-based upload
         onPackageUpload?.(files, localSelectedPackage);
       } else {
         // Standard upload
         onFilesDropped?.(files);
       }
     };
   
     const handlePackageSelected = (packageId: string) => {
       setLocalSelectedPackage(packageId);
       setShowPackageManager(false);
     };
   
     const getSelectedPackageInfo = (): DocumentPackage | null => {
       if (!localSelectedPackage) return null;
       return packages.find(pkg => pkg.package_id === localSelectedPackage) || null;
     };
   
     const selectedPackageInfo = getSelectedPackageInfo();
   
     return (
       <Box>
         {enablePackageSelection && (
           <>
             {/* Upload Mode Toggle */}
             <Box mb={2}>
               <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                 <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                   <Typography variant="subtitle2">Upload Mode</Typography>
                   <ToggleButtonGroup
                     value={uploadMode}
                     exclusive
                     onChange={handleModeChange}
                     size="small"
                   >
                     <ToggleButton value="standard">
                       <CloudUploadIcon sx={{ mr: 1, fontSize: 18 }} />
                       Standard
                     </ToggleButton>
                     <ToggleButton value="package">
                       <FolderSpecialIcon sx={{ mr: 1, fontSize: 18 }} />
                       Package-Based
                     </ToggleButton>
                   </ToggleButtonGroup>
                 </Box>
   
                 {/* Mode Description */}
                 <Typography variant="body2" color="text.secondary">
                   {uploadMode === 'standard' 
                     ? 'Upload files using the default processing pipeline'
                     : 'Upload files using a document package structure for enhanced processing'
                   }
                 </Typography>
               </Paper>
             </Box>
   
             {/* Package Selection (when in package mode) */}
             {uploadMode === 'package' && (
               <Box mb={2}>
                 <Paper sx={{ p: 2, border: '1px dashed', borderColor: 'primary.main' }}>
                   <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                     <Typography variant="subtitle2">Selected Package</Typography>
                     <Button 
                       size="small" 
                       variant="outlined"
                       onClick={() => setShowPackageManager(true)}
                     >
                       {localSelectedPackage ? 'Change Package' : 'Select Package'}
                     </Button>
                   </Box>
   
                   {selectedPackageInfo ? (
                     <Box display="flex" alignItems="center" gap={1}>
                       <Chip 
                         label={selectedPackageInfo.category}
                         color="primary"
                         size="small"
                       />
                       <Typography variant="body2">
                         {selectedPackageInfo.package_name}
                       </Typography>
                       <Chip 
                         label={`v${selectedPackageInfo.version}`}
                         variant="outlined"
                         size="small"
                       />
                     </Box>
                   ) : (
                     <Alert severity="warning" sx={{ mt: 1 }}>
                       Please select a package to enable package-based processing
                     </Alert>
                   )}
                 </Paper>
               </Box>
             )}
           </>
         )}
   
         {/* Enhanced DropZone */}
         <DropZone 
           {...dropZoneProps}
           onFilesDropped={handleFilesDropped}
           disabled={uploadMode === 'package' && !localSelectedPackage}
           additionalInfo={getAdditionalInfo()}
         />
   
         {/* Package Manager Modal */}
         <PackageManager 
           isOpen={showPackageManager}
           onClose={() => setShowPackageManager(false)}
           onPackageSelected={handlePackageSelected}
         />
       </Box>
     );
   
     function getAdditionalInfo(): string | undefined {
       if (uploadMode === 'package' && selectedPackageInfo) {
         return `Files will be processed using the ${selectedPackageInfo.package_name} package structure`;
       }
       if (uploadMode === 'package' && !selectedPackageInfo) {
         return 'Select a package to enable enhanced document processing';
       }
       return dropZoneProps.additionalInfo;
     }
   };
   ```

2. **Update DropZone to support additional info** (30 min)
   ```typescript
   // frontend/src/components/DataSources/Local/DropZone.tsx (add to existing)
   interface DropZoneProps {
     // ... existing props
     additionalInfo?: string;
     disabled?: boolean;
   }
   
   // Add to JSX before the main dropzone content:
   {additionalInfo && (
     <Box mb={2}>
       <Alert severity="info" variant="outlined">
         {additionalInfo}
       </Alert>
     </Box>
   )}
   
   // Add disabled styling to the dropzone:
   sx={{
     // ... existing styles
     opacity: disabled ? 0.6 : 1,
     pointerEvents: disabled ? 'none' : 'auto'
   }}
   ```

3. **Update package upload handling in upload logic** (30 min)
   ```typescript
   // Modify existing upload logic to handle package context
   const handlePackageUpload = async (files: File[], packageId: string) => {
     try {
       // Add package_id to upload metadata
       const uploadPromises = files.map(file => {
         const formData = new FormData();
         formData.append('file', file);
         formData.append('package_id', packageId);
         // ... append other required fields
         
         return uploadAPI(formData);
       });
   
       const results = await Promise.all(uploadPromises);
       
       // Handle results with package context
       results.forEach((result, index) => {
         if (result.status === 'success') {
           // Update file state with package information
           setFiles(prevFiles => 
             prevFiles.map(f => 
               f.name === files[index].name 
                 ? { ...f, package_id: packageId, processing_type: 'package' }
                 : f
             )
           );
         }
       });
       
     } catch (error) {
       showErrorToast('Package upload failed');
     }
   };
   ```

4. **Add package context to file processing** (30 min)
   ```typescript
   // Update file processing to include package metadata
   interface FileProcessingMetadata {
     package_id?: string;
     package_name?: string;
     processing_type: 'standard' | 'package';
     expected_structure?: {
       navigation_depth: number;
       required_sections: string[];
       decision_trees: string[];
     };
   }
   
   // Enhanced file upload with package awareness
   const enhancedUploadFile = async (file: File, packageInfo?: DocumentPackage) => {
     const formData = new FormData();
     formData.append('file', file);
     
     if (packageInfo) {
       formData.append('package_id', packageInfo.package_id);
       formData.append('processing_type', 'package');
       formData.append('package_metadata', JSON.stringify({
         category: packageInfo.category,
         template_type: packageInfo.template_type,
         expected_structure: packageInfo.documents[0]?.expected_structure
       }));
     } else {
       formData.append('processing_type', 'standard');
     }
     
     return await uploadAPI(formData);
   };
   ```

5. **Create integration tests** (30 min)
   ```typescript
   // frontend/src/components/DataSources/Local/__tests__/EnhancedDropZone.test.tsx
   import React from 'react';
   import { render, screen, fireEvent } from '@testing-library/react';
   import { EnhancedDropZone } from '../EnhancedDropZone';
   import { PackageContext } from '../../../../context/PackageContext';
   
   const mockPackageContext = {
     packages: [
       {
         package_id: 'pkg_test_001',
         package_name: 'Test Package',
         category: 'NQM',
         version: '1.0.0'
       }
     ],
     selectedPackage: null,
     loadPackages: jest.fn(),
     selectPackage: jest.fn(),
     createPackage: jest.fn(),
     applyPackage: jest.fn(),
     isLoading: false,
     error: null
   };
   
   const renderWithContext = (component: React.ReactElement) => {
     return render(
       <PackageContext.Provider value={mockPackageContext}>
         {component}
       </PackageContext.Provider>
     );
   };
   
   describe('EnhancedDropZone', () => {
     it('renders upload mode toggle when package selection enabled', () => {
       renderWithContext(
         <EnhancedDropZone 
           enablePackageSelection={true}
           onFilesDropped={jest.fn()}
         />
       );
   
       expect(screen.getByText('Standard')).toBeInTheDocument();
       expect(screen.getByText('Package-Based')).toBeInTheDocument();
     });
   
     it('shows package selection UI when package mode selected', () => {
       renderWithContext(
         <EnhancedDropZone 
           enablePackageSelection={true}
           onFilesDropped={jest.fn()}
         />
       );
   
       const packageButton = screen.getByText('Package-Based');
       fireEvent.click(packageButton);
   
       expect(screen.getByText('Selected Package')).toBeInTheDocument();
       expect(screen.getByText('Select Package')).toBeInTheDocument();
     });
   
     it('disables dropzone when package mode selected but no package chosen', () => {
       renderWithContext(
         <EnhancedDropZone 
           enablePackageSelection={true}
           onFilesDropped={jest.fn()}
         />
       );
   
       const packageButton = screen.getByText('Package-Based');
       fireEvent.click(packageButton);
   
       expect(screen.getByText('Select a package to enable enhanced document processing')).toBeInTheDocument();
     });
   });
   ```

### Acceptance Criteria Checklist
- [ ] EnhancedDropZone.tsx component with upload mode toggle
- [ ] Package selection integration with PackageContext
- [ ] Upload mode toggle between standard and package-based processing
- [ ] Backward compatibility with existing DropZone component
- [ ] Visual feedback for package mode including selected package info
- [ ] File type validation working for both modes
- [ ] Integration tests covering upload flow scenarios

---

## Task 19: Create Navigation Viewer
**Duration**: 4 hours | **Priority**: High | **Dependencies**: Task 11 (Backend Navigation)

### Implementation Steps

1. **Create NavigationTreeViewer component** (120 min)
   ```typescript
   // frontend/src/components/Navigation/NavigationTreeViewer.tsx
   import React, { useState, useEffect } from 'react';
   import {
     Box,
     Typography,
     Button,
     Chip,
     Card,
     CardContent,
     TreeView,
     TreeItem,
     IconButton,
     Tooltip,
     Alert,
     Skeleton
   } from '@neo4j-ndl/react';
   import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
   import ChevronRightIcon from '@mui/icons-material/ChevronRight';
   import AccountTreeIcon from '@mui/icons-material/AccountTree';
   import DescriptionIcon from '@mui/icons-material/Description';
   import RuleIcon from '@mui/icons-material/Rule';
   import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
   import { NavigationNode, NavigationTree, DecisionTree } from '../../types';
   import { DecisionTreePreview } from './DecisionTreePreview';
   
   interface NavigationTreeViewerProps {
     fileId: string;
     navigationData: NavigationTree | null;
     loading?: boolean;
     onNodeSelect?: (nodeId: string) => void;
     onNavigate?: (nodeId: string) => void;
   }
   
   export const NavigationTreeViewer: React.FC<NavigationTreeViewerProps> = ({ 
     fileId, 
     navigationData, 
     loading = false,
     onNodeSelect,
     onNavigate
   }) => {
     const [expandedNodes, setExpandedNodes] = useState<string[]>([]);
     const [selectedNode, setSelectedNode] = useState<string | null>(null);
     const [showDecisionPreview, setShowDecisionPreview] = useState(false);
   
     useEffect(() => {
       // Auto-expand root nodes when data loads
       if (navigationData?.nodes) {
         const rootNodes = navigationData.nodes
           .filter(node => !node.parent_id)
           .map(node => node.enhanced_node_id);
         setExpandedNodes(rootNodes);
       }
     }, [navigationData]);
   
     const handleNodeToggle = (event: React.SyntheticEvent, nodeIds: string[]) => {
       setExpandedNodes(nodeIds);
     };
   
     const handleNodeSelect = (event: React.SyntheticEvent, nodeId: string) => {
       setSelectedNode(nodeId);
       onNodeSelect?.(nodeId);
       
       // Check if this node has decision trees
       const node = findNodeById(nodeId);
       if (node?.requires_complete_tree) {
         setShowDecisionPreview(true);
       } else {
         setShowDecisionPreview(false);
       }
     };
   
     const findNodeById = (nodeId: string): NavigationNode | undefined => {
       return navigationData?.nodes.find(node => node.enhanced_node_id === nodeId);
     };
   
     const getNodeIcon = (nodeType: string) => {
       switch (nodeType) {
         case 'CHAPTER':
           return <DescriptionIcon fontSize="small" />;
         case 'SECTION':
           return <AccountTreeIcon fontSize="small" />;
         case 'SUBSECTION':
           return <RuleIcon fontSize="small" />;
         case 'DECISION_FLOW_SECTION':
           return <PlaylistAddCheckIcon fontSize="small" color="warning" />;
         default:
           return <DescriptionIcon fontSize="small" />;
       }
     };
   
     const getNodeTypeColor = (nodeType: string): 'default' | 'primary' | 'secondary' | 'warning' => {
       switch (nodeType) {
         case 'CHAPTER': return 'primary';
         case 'SECTION': return 'secondary';
         case 'SUBSECTION': return 'default';
         case 'DECISION_FLOW_SECTION': return 'warning';
         default: return 'default';
       }
     };
   
     const buildTreeItems = (nodes: NavigationNode[]): React.ReactNode[] => {
       // Get root nodes (no parent)
       const rootNodes = nodes.filter(node => !node.parent_id);
       
       const renderNode = (node: NavigationNode): React.ReactNode => {
         const children = nodes.filter(child => child.parent_id === node.enhanced_node_id);
         
         return (
           <TreeItem
             key={node.enhanced_node_id}
             nodeId={node.enhanced_node_id}
             label={
               <Box display="flex" alignItems="center" gap={1} py={0.5}>
                 {getNodeIcon(node.node_type)}
                 <Typography variant="body2" sx={{ flexGrow: 1 }}>
                   {node.title}
                 </Typography>
                 <Box display="flex" gap={0.5}>
                   <Chip 
                     size="small" 
                     label={node.node_type.replace('_', ' ')}
                     color={getNodeTypeColor(node.node_type)}
                     sx={{ fontSize: '0.7rem', height: 20 }}
                   />
                   {node.requires_complete_tree && (
                     <Chip 
                       size="small" 
                       label="Decision Tree"
                       color="warning"
                       sx={{ fontSize: '0.7rem', height: 20 }}
                     />
                   )}
                   {node.depth_level && (
                     <Chip 
                       size="small" 
                       label={`L${node.depth_level}`}
                       variant="outlined"
                       sx={{ fontSize: '0.7rem', height: 20 }}
                     />
                   )}
                 </Box>
               </Box>
             }
           >
             {children.map(child => renderNode(child))}
           </TreeItem>
         );
       };
   
       return rootNodes.map(node => renderNode(node));
     };
   
     const handleExpandAll = () => {
       if (navigationData?.nodes) {
         const allNodeIds = navigationData.nodes.map(node => node.enhanced_node_id);
         setExpandedNodes(allNodeIds);
       }
     };
   
     const handleCollapseAll = () => {
       setExpandedNodes([]);
     };
   
     const navigateToNode = (nodeId: string) => {
       onNavigate?.(nodeId);
     };
   
     if (loading) {
       return (
         <Box>
           <Box display="flex" alignItems="center" gap={2} mb={2}>
             <Skeleton variant="text" width={200} height={32} />
             <Skeleton variant="rectangular" width={80} height={24} />
             <Skeleton variant="rectangular" width={80} height={24} />
           </Box>
           {[1, 2, 3, 4].map((item) => (
             <Box key={item} display="flex" alignItems="center" gap={1} mb={1}>
               <Skeleton variant="circular" width={20} height={20} />
               <Skeleton variant="text" width={`${60 + item * 10}%`} height={24} />
             </Box>
           ))}
         </Box>
       );
     }
   
     if (!navigationData || !navigationData.nodes || navigationData.nodes.length === 0) {
       return (
         <Alert severity="info">
           No navigation structure available for this document. 
           The document may still be processing or may not have a clear hierarchical structure.
         </Alert>
       );
     }
   
     return (
       <Box>
         {/* Header */}
         <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
           <Box display="flex" alignItems="center" gap={2}>
             <Typography variant="h6">Document Navigation</Typography>
             <Chip 
               size="small" 
               label={`${navigationData.nodes.length} sections`}
               color="primary"
             />
             {navigationData.decision_trees && navigationData.decision_trees.length > 0 && (
               <Chip 
                 size="small" 
                 label={`${navigationData.decision_trees.length} decision trees`}
                 color="warning"
               />
             )}
           </Box>
           <Box display="flex" gap={1}>
             <Button size="small" onClick={handleCollapseAll}>
               Collapse All
             </Button>
             <Button size="small" onClick={handleExpandAll}>
               Expand All
             </Button>
           </Box>
         </Box>
   
         {/* Navigation Tree */}
         <Card variant="outlined">
           <CardContent sx={{ p: 1 }}>
             <TreeView
               defaultCollapseIcon={<ExpandMoreIcon />}
               defaultExpandIcon={<ChevronRightIcon />}
               expanded={expandedNodes}
               selected={selectedNode}
               onNodeToggle={handleNodeToggle}
               onNodeSelect={handleNodeSelect}
               sx={{
                 flexGrow: 1,
                 maxWidth: '100%',
                 overflowY: 'auto',
                 maxHeight: 400
               }}
             >
               {buildTreeItems(navigationData.nodes)}
             </TreeView>
           </CardContent>
         </Card>
   
         {/* Selected Node Details */}
         {selectedNode && (
           <Box mt={2}>
             <NodeDetails 
               node={findNodeById(selectedNode)!}
               onNavigate={navigateToNode}
             />
           </Box>
         )}
   
         {/* Decision Tree Preview */}
         {showDecisionPreview && selectedNode && navigationData.decision_trees && (
           <Box mt={2}>
             <DecisionTreePreview 
               nodeId={selectedNode}
               decisionTrees={navigationData.decision_trees}
               fileId={fileId}
             />
           </Box>
         )}
       </Box>
     );
   };
   
   // Node Details Component
   interface NodeDetailsProps {
     node: NavigationNode;
     onNavigate: (nodeId: string) => void;
   }
   
   const NodeDetails: React.FC<NodeDetailsProps> = ({ node, onNavigate }) => {
     return (
       <Card>
         <CardContent>
           <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
             <Typography variant="h6">{node.title}</Typography>
             <Box display="flex" gap={1}>
               <Chip 
                 size="small" 
                 label={node.node_type.replace('_', ' ')}
                 color={node.node_type === 'DECISION_FLOW_SECTION' ? 'warning' : 'primary'}
               />
               {node.chapter_number && (
                 <Chip size="small" label={`Chapter ${node.chapter_number}`} variant="outlined" />
               )}
               {node.section_number && (
                 <Chip size="small" label={`Section ${node.section_number}`} variant="outlined" />
               )}
             </Box>
           </Box>
   
           <Typography variant="body2" color="text.secondary" paragraph>
             Depth Level: {node.depth_level} | 
             Children: {node.children?.length || 0}
             {node.requires_complete_tree && ' | Contains Decision Logic'}
           </Typography>
   
           <Button
             variant="outlined"
             size="small"
             onClick={() => onNavigate(node.enhanced_node_id)}
           >
             Navigate to Section
           </Button>
         </CardContent>
       </Card>
     );
   };
   ```

2. **Create DecisionTreePreview component** (60 min)
   ```typescript
   // frontend/src/components/Navigation/DecisionTreePreview.tsx
   import React, { useState } from 'react';
   import {
     Box,
     Typography,
     Card,
     CardContent,
     Chip,
     Button,
     Accordion,
     AccordionSummary,
     AccordionDetails,
     Alert
   } from '@neo4j-ndl/react';
   import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
   import { DecisionTree, DecisionNode } from '../../types';
   
   interface DecisionTreePreviewProps {
     nodeId: string;
     decisionTrees: DecisionTree[];
     fileId: string;
   }
   
   export const DecisionTreePreview: React.FC<DecisionTreePreviewProps> = ({ 
     nodeId, 
     decisionTrees,
     fileId 
   }) => {
     const [expandedTrees, setExpandedTrees] = useState<string[]>([]);
   
     // Find decision trees related to this node
     const relatedTrees = decisionTrees.filter(tree => 
       tree.section_id === nodeId || tree.root?.enhanced_node_id?.includes(nodeId)
     );
   
     if (relatedTrees.length === 0) {
       return (
         <Alert severity="info">
           No decision trees found for this section.
         </Alert>
       );
     }
   
     const handleTreeToggle = (treeId: string) => {
       setExpandedTrees(prev => 
         prev.includes(treeId) 
           ? prev.filter(id => id !== treeId)
           : [...prev, treeId]
       );
     };
   
     const getOutcomeColor = (outcome: string): 'success' | 'error' | 'warning' => {
       switch (outcome.toUpperCase()) {
         case 'APPROVE': return 'success';
         case 'DECLINE': return 'error';
         case 'REFER': return 'warning';
         default: return 'warning';
       }
     };
   
     return (
       <Card>
         <CardContent>
           <Typography variant="h6" gutterBottom>
             Decision Trees ({relatedTrees.length})
           </Typography>
           
           {relatedTrees.map((tree, index) => (
             <Accordion 
               key={`${tree.section_id}_${index}`}
               expanded={expandedTrees.includes(`${tree.section_id}_${index}`)}
               onChange={() => handleTreeToggle(`${tree.section_id}_${index}`)}
             >
               <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                 <Box display="flex" alignItems="center" gap={2}>
                   <Typography variant="subtitle1">
                     Decision Tree {index + 1}
                   </Typography>
                   {tree.is_complete && (
                     <Chip size="small" label="Complete" color="success" />
                   )}
                   <Chip 
                     size="small" 
                     label={`${tree.leaves?.length || 0} outcomes`}
                     variant="outlined"
                   />
                 </Box>
               </AccordionSummary>
               <AccordionDetails>
                 <Box>
                   {/* Root Node */}
                   {tree.root && (
                     <Box mb={2}>
                       <Typography variant="subtitle2" gutterBottom>Root Policy</Typography>
                       <Card variant="outlined" sx={{ bgcolor: 'background.default' }}>
                         <CardContent sx={{ py: 1 }}>
                           <Typography variant="body2">{tree.root.title}</Typography>
                         </CardContent>
                       </Card>
                     </Box>
                   )}
   
                   {/* Branch Nodes */}
                   {tree.branches && tree.branches.length > 0 && (
                     <Box mb={2}>
                       <Typography variant="subtitle2" gutterBottom>
                         Evaluation Criteria ({tree.branches.length})
                       </Typography>
                       <Box display="flex" flexDirection="column" gap={1}>
                         {tree.branches.map((branch, branchIndex) => (
                           <Card key={branchIndex} variant="outlined" sx={{ bgcolor: 'info.light', bgcolor: 'background.default' }}>
                             <CardContent sx={{ py: 1 }}>
                               <Typography variant="body2">{branch.title}</Typography>
                               {branch.evaluation_precedence && (
                                 <Chip 
                                   size="small" 
                                   label={`Priority ${branch.evaluation_precedence}`}
                                   sx={{ mt: 0.5 }}
                                 />
                               )}
                             </CardContent>
                           </Card>
                         ))}
                       </Box>
                     </Box>
                   )}
   
                   {/* Leaf Nodes (Outcomes) */}
                   {tree.leaves && tree.leaves.length > 0 && (
                     <Box mb={2}>
                       <Typography variant="subtitle2" gutterBottom>
                         Possible Outcomes ({tree.leaves.length})
                       </Typography>
                       <Box display="flex" flexWrap="wrap" gap={1}>
                         {tree.leaves.map((leaf, leafIndex) => (
                           <Chip
                             key={leafIndex}
                             label={leaf.outcome || leaf.title}
                             color={getOutcomeColor(leaf.outcome || '')}
                             variant="filled"
                           />
                         ))}
                       </Box>
                     </Box>
                   )}
   
                   {/* Decision Paths */}
                   {tree.paths && tree.paths.length > 0 && (
                     <Box>
                       <Typography variant="subtitle2" gutterBottom>
                         Decision Paths ({tree.paths.length})
                       </Typography>
                       <Box display="flex" flexDirection="column" gap={1}>
                         {tree.paths.slice(0, 3).map((path, pathIndex) => (
                           <Box key={pathIndex} display="flex" alignItems="center" gap={1}>
                             <Typography variant="caption" color="text.secondary">
                               Path {pathIndex + 1}:
                             </Typography>
                             <Box display="flex" alignItems="center" gap={0.5}>
                               {path.steps?.map((step, stepIndex) => (
                                 <React.Fragment key={stepIndex}>
                                   <Chip size="small" label={step} variant="outlined" />
                                   {stepIndex < path.steps.length - 1 && (
                                     <Typography variant="caption">→</Typography>
                                   )}
                                 </React.Fragment>
                               ))}
                             </Box>
                           </Box>
                         ))}
                         {tree.paths.length > 3 && (
                           <Typography variant="caption" color="text.secondary">
                             ... and {tree.paths.length - 3} more paths
                           </Typography>
                         )}
                       </Box>
                     </Box>
                   )}
                 </Box>
               </AccordionDetails>
             </Accordion>
           ))}
   
           <Box mt={2} display="flex" gap={1}>
             <Button size="small" variant="outlined">
               View Full Decision Logic
             </Button>
             <Button size="small" variant="outlined">
               Export Decision Tree
             </Button>
           </Box>
         </CardContent>
       </Card>
     );
   };
   ```

3. **Add component exports and integration** (30 min)
   ```typescript
   // frontend/src/components/Navigation/index.ts
   export { NavigationTreeViewer } from './NavigationTreeViewer';
   export { DecisionTreePreview } from './DecisionTreePreview';
   ```

4. **Create component tests** (30 min)
   ```typescript
   // frontend/src/components/Navigation/__tests__/NavigationTreeViewer.test.tsx
   import React from 'react';
   import { render, screen, fireEvent } from '@testing-library/react';
   import { NavigationTreeViewer } from '../NavigationTreeViewer';
   import { NavigationTree } from '../../../types';
   
   const mockNavigationData: NavigationTree = {
     nodes: [
       {
         enhanced_node_id: 'node_001',
         node_type: 'CHAPTER',
         title: 'Chapter 1: Borrower Eligibility',
         depth_level: 1,
         chapter_number: 1,
         children: [
           {
             enhanced_node_id: 'node_002',
             node_type: 'SECTION',
             title: 'Section 1.1: Basic Requirements',
             depth_level: 2,
             parent_id: 'node_001',
             children: []
           }
         ],
         requires_complete_tree: false
       }
     ],
     decision_trees: [],
     metadata: {
       extraction_accuracy: 0.95,
       total_nodes: 2,
       decision_sections: 0
     }
   };
   
   describe('NavigationTreeViewer', () => {
     it('renders navigation tree structure', () => {
       render(
         <NavigationTreeViewer 
           fileId="test_file"
           navigationData={mockNavigationData}
           onNodeSelect={jest.fn()}
         />
       );
   
       expect(screen.getByText('Document Navigation')).toBeInTheDocument();
       expect(screen.getByText('Chapter 1: Borrower Eligibility')).toBeInTheDocument();
       expect(screen.getByText('2 sections')).toBeInTheDocument();
     });
   
     it('expands and collapses tree nodes', () => {
       render(
         <NavigationTreeViewer 
           fileId="test_file"
           navigationData={mockNavigationData}
           onNodeSelect={jest.fn()}
         />
       );
   
       const expandAllButton = screen.getByText('Expand All');
       fireEvent.click(expandAllButton);
   
       expect(screen.getByText('Section 1.1: Basic Requirements')).toBeInTheDocument();
   
       const collapseAllButton = screen.getByText('Collapse All');
       fireEvent.click(collapseAllButton);
     });
   
     it('calls onNodeSelect when node is clicked', () => {
       const mockOnNodeSelect = jest.fn();
       render(
         <NavigationTreeViewer 
           fileId="test_file"
           navigationData={mockNavigationData}
           onNodeSelect={mockOnNodeSelect}
         />
       );
   
       const chapterNode = screen.getByText('Chapter 1: Borrower Eligibility');
       fireEvent.click(chapterNode);
   
       expect(mockOnNodeSelect).toHaveBeenCalledWith('node_001');
     });
   
     it('shows loading state', () => {
       render(
         <NavigationTreeViewer 
           fileId="test_file"
           navigationData={null}
           loading={true}
           onNodeSelect={jest.fn()}
         />
       );
   
       expect(screen.getAllByTestId('skeleton')).toHaveLength(7); // Header + 4 items
     });
   
     it('shows empty state when no navigation data', () => {
       render(
         <NavigationTreeViewer 
           fileId="test_file"
           navigationData={{ nodes: [], decision_trees: [], metadata: {} }}
           onNodeSelect={jest.fn()}
         />
       );
   
       expect(screen.getByText(/No navigation structure available/)).toBeInTheDocument();
     });
   });
   ```

### Acceptance Criteria Checklist
- [ ] NavigationTreeViewer.tsx with TreeView integration
- [ ] Tree node display with icons and type indicators
- [ ] Node selection and preview functionality with detailed view
- [ ] Decision tree highlighting and preview integration
- [ ] Expand/collapse functionality for all nodes
- [ ] Navigation breadcrumbs and section metadata display
- [ ] Tests for tree interactions and state management

---

Continue with remaining frontend tasks (20-24) following the same detailed format...
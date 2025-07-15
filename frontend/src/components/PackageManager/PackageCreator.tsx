import React, { useState, useEffect } from 'react';
import { Dialog, Typography, Button, Flex, TextInput, Banner } from '@neo4j-ndl/react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  FormHelperText,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { createDocumentPackage } from '../../services/PackageAPI';
import { showErrorToast } from '../../utils/Toasts';
import { DocumentPackage, PackageFormData, DocumentDefinition } from '../../types';

interface PackageCreatorProps {
  isOpen: boolean;
  onClose: () => void;
  templateType?: string;
  onPackageCreated: (packageData: DocumentPackage) => void;
}

interface DocumentFormData {
  document_id: string;
  document_name: string;
  document_type: 'guidelines' | 'matrix' | 'rate_sheet';
  required: boolean;
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

const DOCUMENT_TYPES = [
  { value: 'guidelines', label: 'Guidelines Document' },
  { value: 'matrix', label: 'Matrix Document' },
  { value: 'rate_sheet', label: 'Rate Sheet' }
];

const getRequiredDocumentsForCategory = (category: string): DocumentFormData[] => {
  switch (category) {
    case 'NQM':
      return [
        { document_id: 'guidelines', document_name: 'Guidelines Document', document_type: 'guidelines', required: true },
        { document_id: 'matrix', document_name: 'Matrix Document', document_type: 'matrix', required: true }
      ];
    default:
      return [];
  }
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
  const [documents, setDocuments] = useState<DocumentFormData[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [documentErrors, setDocumentErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (templateType) {
      setFormData(prev => ({ ...prev, category: templateType }));
      setDocuments(getRequiredDocumentsForCategory(templateType));
    }
  }, [templateType]);

  useEffect(() => {
    if (formData.category) {
      const requiredDocs = getRequiredDocumentsForCategory(formData.category);
      setDocuments(prev => {
        const existing = prev.filter(doc => !doc.required);
        return [...requiredDocs, ...existing];
      });
    }
  }, [formData.category]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    const newDocumentErrors: Record<string, string> = {};

    if (!formData.package_name.trim()) {
      newErrors.package_name = 'Package name is required';
    }

    if (!formData.category) {
      newErrors.category = 'Category is required';
    }

    if (!formData.template) {
      newErrors.template = 'Template is required';
    }

    if (documents.length === 0) {
      newErrors.documents = 'At least one document is required';
    }

    // Validate each document
    documents.forEach((doc, index) => {
      if (!doc.document_name.trim()) {
        newDocumentErrors[`${index}_name`] = 'Document name is required';
      }
      if (!doc.document_id.trim()) {
        newDocumentErrors[`${index}_id`] = 'Document ID is required';
      }
    });

    // Check for duplicate document IDs
    const docIds = documents.map(doc => doc.document_id);
    const duplicateIds = docIds.filter((id, index) => docIds.indexOf(id) !== index);
    if (duplicateIds.length > 0) {
      newErrors.documents = 'Document IDs must be unique';
    }

    setErrors(newErrors);
    setDocumentErrors(newDocumentErrors);
    return Object.keys(newErrors).length === 0 && Object.keys(newDocumentErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const packageData = {
        ...formData,
        documents: documents.map(doc => ({
          document_id: doc.document_id,
          document_name: doc.document_name,
          document_type: doc.document_type,
          required_sections: [],
          optional_sections: [],
          chunking_strategy: 'hierarchical',
          entity_types: [],
          expected_structure: {
            navigation_depth: 3,
            required_sections: [],
            decision_trees: []
          },
          processing_config: {}
        }))
      };
      
      const response = await createDocumentPackage(packageData);
      if (response.status === 'success' && response.data) {
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
    setDocuments([]);
    setErrors({});
    setDocumentErrors({});
    onClose();
  };

  const addDocument = () => {
    const newDoc: DocumentFormData = {
      document_id: `doc_${Date.now()}`,
      document_name: '',
      document_type: 'guidelines',
      required: false
    };
    setDocuments(prev => [...prev, newDoc]);
  };

  const removeDocument = (index: number) => {
    setDocuments(prev => prev.filter((_, i) => i !== index));
  };

  const updateDocument = (index: number, field: keyof DocumentFormData, value: any) => {
    setDocuments(prev => prev.map((doc, i) => 
      i === index ? { ...doc, [field]: value } : doc
    ));
  };

  const availableTemplates = formData.category ? TEMPLATES_BY_CATEGORY[formData.category] || [] : [];
  const selectedCategory = MORTGAGE_CATEGORIES.find(cat => cat.value === formData.category);

  return (
    <Dialog isOpen={isOpen} onClose={handleClose} size="large">
      <Dialog.Header id="package-creator-header">
        <Typography variant="h4">Create New Document Package</Typography>
      </Dialog.Header>
      <Dialog.Content className="n-flex n-flex-col n-gap-token-4">

        <Box component="form" noValidate>
          {/* Package Name */}
          <Box sx={{ mb: 2 }}>
            <TextInput
              label="Package Name"
              value={formData.package_name}
              onChange={(e) => setFormData({...formData, package_name: e.target.value})}
              required
              isFluid
              helpText={errors.package_name}
              hasError={!!errors.package_name}
              placeholder="e.g., NQM Titanium Advantage Package"
            />
          </Box>

          {/* Category Selection */}
          <FormControl fullWidth margin="normal" error={!!errors.category}>
            <InputLabel required>Mortgage Category</InputLabel>
            <Select
              value={formData.category}
              onChange={(e) => setFormData({...formData, category: e.target.value, template: ''})}
              required
              label="Mortgage Category"
            >
              {MORTGAGE_CATEGORIES.map((category) => (
                <MenuItem key={category.value} value={category.value}>
                  <Box>
                    <Typography variant="body-medium">{category.label}</Typography>
                    <Typography variant="body-small" color="text.secondary">
                      {category.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
            {errors.category && <FormHelperText>{errors.category}</FormHelperText>}
          </FormControl>

          {/* Template Selection */}
          {formData.category && (
            <FormControl fullWidth margin="normal" error={!!errors.template}>
              <InputLabel required>Base Template</InputLabel>
              <Select
                value={formData.template}
                onChange={(e) => setFormData({...formData, template: e.target.value})}
                required
                label="Base Template"
              >
                {availableTemplates.map((template) => (
                  <MenuItem key={template.value} value={template.value}>
                    {template.label}
                  </MenuItem>
                ))}
              </Select>
              {errors.template && <FormHelperText>{errors.template}</FormHelperText>}
            </FormControl>
          )}

          {/* Category Description */}
          {selectedCategory && (
            <Paper sx={{ p: 2, mt: 2, bgcolor: 'background.default' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Chip label={selectedCategory.label} color="primary" size="small" />
                <Typography variant="subheading-medium">Category Overview</Typography>
              </Box>
              <Typography variant="body-medium">
                {selectedCategory.description}
              </Typography>
            </Paper>
          )}

          {/* Customization Options (Collapsed by default) */}
          {formData.template && (
            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subheading-medium">Advanced Customizations (Optional)</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body-medium" sx={{ mb: 2 }}>
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

          {/* Documents Section */}
          <Box sx={{ mt: 3 }}>
            <Flex justifyContent="space-between" alignItems="center" style={{ marginBottom: '16px' }}>
              <Typography variant="h6">Documents</Typography>
              <Button
                onClick={addDocument}
                size="small"
                fill="outlined"
                leftIcon={<AddIcon />}
              >
                Add Document
              </Button>
            </Flex>
            
            {errors.documents && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {errors.documents}
              </Alert>
            )}
            
            {documents.length > 0 && (
              <TableContainer component={Paper} sx={{ mb: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Document ID</TableCell>
                      <TableCell>Document Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Required</TableCell>
                      <TableCell width="50px">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {documents.map((doc, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <TextField
                            size="small"
                            value={doc.document_id}
                            onChange={(e) => updateDocument(index, 'document_id', e.target.value)}
                            error={!!documentErrors[`${index}_id`]}
                            helperText={documentErrors[`${index}_id`]}
                            disabled={doc.required}
                            fullWidth
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            value={doc.document_name}
                            onChange={(e) => updateDocument(index, 'document_name', e.target.value)}
                            error={!!documentErrors[`${index}_name`]}
                            helperText={documentErrors[`${index}_name`]}
                            fullWidth
                          />
                        </TableCell>
                        <TableCell>
                          <Select
                            size="small"
                            value={doc.document_type}
                            onChange={(e) => updateDocument(index, 'document_type', e.target.value)}
                            disabled={doc.required}
                            fullWidth
                          >
                            {DOCUMENT_TYPES.map(type => (
                              <MenuItem key={type.value} value={type.value}>
                                {type.label}
                              </MenuItem>
                            ))}
                          </Select>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={doc.required ? 'Required' : 'Optional'} 
                            color={doc.required ? 'error' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton
                            onClick={() => removeDocument(index)}
                            disabled={doc.required}
                            size="small"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
            
            {documents.length === 0 && (
              <Banner
                type="info"
                title="No documents added"
                description="Add at least one document to create a package. For NQM packages, guidelines and matrix documents are required."
              />
            )}
          </Box>
        </Box>
      </Dialog.Content>
      <Dialog.Actions>
        <Flex justifyContent="flex-end" gap="token-2">
          <Button onClick={handleClose} fill="outlined" isDisabled={loading}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit}
            isDisabled={loading}
          >
            {loading ? 'Creating...' : 'Create Package'}
          </Button>
        </Flex>
      </Dialog.Actions>
    </Dialog>
  );
};
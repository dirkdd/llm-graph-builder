import React, { useState } from 'react';
import { Dropzone, Flex, SpotlightTarget, Typography, Button } from '@neo4j-ndl/react';
import { 
  Box,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  Paper,
  Chip
} from '@mui/material';
import { InformationCircleIconOutline } from '@neo4j-ndl/react/icons';
import { IconButtonWithToolTip } from '../../UI/IconButtonToolTip';
import { PackageManager } from '../../PackageManager';
import { DocumentPackage } from '../../../types';
import { buttonCaptions } from '../../../utils/Constants';
import { showErrorToast } from '../../../utils/Toasts';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import FolderSpecialIcon from '@mui/icons-material/FolderSpecial';

interface EnhancedDropZoneProps {
  packageId?: string;
  enablePackageSelection?: boolean;
  onFilesDropped?: (files: File[], packageId?: string) => void;
  onPackageUpload?: (files: File[], packageId: string) => void;
  isLoading?: boolean;
  availablePackages?: DocumentPackage[];
}

type UploadMode = 'standard' | 'package';

export const EnhancedDropZone: React.FC<EnhancedDropZoneProps> = ({ 
  packageId, 
  enablePackageSelection = true,
  onFilesDropped,
  onPackageUpload,
  isLoading = false,
  availablePackages = []
}) => {
  const [uploadMode, setUploadMode] = useState<UploadMode>('standard');
  const [selectedPackageId, setSelectedPackageId] = useState<string | null>(
    packageId || null
  );
  const [showPackageManager, setShowPackageManager] = useState(false);

  const handleModeChange = (
    _event: React.MouseEvent<HTMLElement>, 
    newMode: UploadMode | null
  ) => {
    if (newMode !== null) {
      setUploadMode(newMode);
      // Clear package selection when switching to standard mode
      if (newMode === 'standard') {
        setSelectedPackageId(null);
      }
    }
  };

  const handleFilesDropped = (files: Partial<globalThis.File>[]) => {
    const fileList = files.map(f => f as File);
    
    if (uploadMode === 'package' && selectedPackageId) {
      // Package-based upload
      onPackageUpload?.(fileList, selectedPackageId);
    } else if (uploadMode === 'package' && !selectedPackageId) {
      // Prevent upload without package selection
      showErrorToast('Please select a package before uploading files');
      return;
    } else {
      // Standard upload
      onFilesDropped?.(fileList);
    }
  };

  const handlePackageSelected = (packageId: string) => {
    setSelectedPackageId(packageId);
    setShowPackageManager(false);
  };

  const getSelectedPackageInfo = (): DocumentPackage | null => {
    if (!selectedPackageId) return null;
    return availablePackages.find(pkg => pkg.package_id === selectedPackageId) || null;
  };

  const selectedPackageInfo = getSelectedPackageInfo();

  const getAdditionalInfo = (): string | undefined => {
    if (uploadMode === 'package' && selectedPackageInfo) {
      return `Files will be processed using the ${selectedPackageInfo.package_name} package structure`;
    }
    if (uploadMode === 'package' && !selectedPackageInfo) {
      return 'Select a package to enable enhanced document processing';
    }
    return undefined;
  };

  const isDropzoneDisabled = uploadMode === 'package' && !selectedPackageId;

  return (
    <Box>
      {enablePackageSelection && (
        <>
          {/* Upload Mode Toggle */}
          <Box sx={{ mb: 2 }}>
            <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="subheading-medium">Upload Mode</Typography>
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
              <Typography variant="body-medium">
                {uploadMode === 'standard' 
                  ? 'Upload files using the default processing pipeline'
                  : 'Upload files using a document package structure for enhanced processing'
                }
              </Typography>
            </Paper>
          </Box>

          {/* Package Selection (when in package mode) */}
          {uploadMode === 'package' && (
            <Box sx={{ mb: 2 }}>
              <Paper sx={{ p: 2, border: '1px dashed', borderColor: 'primary.main' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subheading-medium">Selected Package</Typography>
                  <Button 
                    size="small" 
                    onClick={() => setShowPackageManager(true)}
                  >
                    {selectedPackageId ? 'Change Package' : 'Select Package'}
                  </Button>
                </Box>

                {selectedPackageInfo ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip 
                      label={selectedPackageInfo.category}
                      color="primary"
                      size="small"
                    />
                    <Typography variant="body-medium">
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

          {/* Additional Info Alert */}
          {getAdditionalInfo() && (
            <Box sx={{ mb: 2 }}>
              <Alert severity="info" variant="outlined">
                {getAdditionalInfo()}
              </Alert>
            </Box>
          )}
        </>
      )}

      {/* Enhanced DropZone */}
      <SpotlightTarget
        id='enhanced-dropzone'
        hasPulse={true}
        indicatorVariant='border'
        hasAnchorPortal={false}
        borderRadius={11}
      >
        <Box sx={{ 
          opacity: isDropzoneDisabled ? 0.6 : 1,
          pointerEvents: isDropzoneDisabled ? 'none' : 'auto'
        }}>
          <Dropzone
            loadingComponent={isLoading && <div>Uploading...</div>}
            isTesting={true}
            className='bg-none! dropzoneContainer'
            supportedFilesDescription={
              <Typography variant='body-small'>
                <Flex>
                  <span>{buttonCaptions.dropzoneSpan}</span>
                  <div className='align-self-center'>
                    <IconButtonWithToolTip
                      label='Source info'
                      clean
                      text={
                        <Typography variant='body-small'>
                          <Flex gap='3' alignItems='flex-start'>
                            <span>Microsoft Office (.docx, .pptx, .xls, .xlsx)</span>
                            <span>PDF (.pdf)</span>
                            <span>Images (.jpeg, .jpg, .png, .svg)</span>
                            <span>Text (.html, .txt , .md)</span>
                          </Flex>
                        </Typography>
                      }
                    >
                      <InformationCircleIconOutline className='w-[22px] h-[22px]' />
                    </IconButtonWithToolTip>
                  </div>
                </Flex>
              </Typography>
            }
            dropZoneOptions={{
              accept: {
                'application/pdf': ['.pdf'],
                'image/*': ['.jpeg', '.jpg', '.png', '.svg'],
                'text/html': ['.html'],
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
                'text/plain': ['.txt'],
                'application/vnd.ms-powerpoint': ['.pptx'],
                'application/vnd.ms-excel': ['.xls'],
                'text/markdown': ['.md'],
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
              },
              onDrop: handleFilesDropped,
              onDropRejected: (e) => {
                if (e.length) {
                  showErrorToast('Failed To Upload, Unsupported file extension');
                }
              },
            }}
          />
        </Box>
      </SpotlightTarget>

      {/* Package Manager Modal */}
      <PackageManager 
        isOpen={showPackageManager}
        onClose={() => setShowPackageManager(false)}
        onPackageSelected={handlePackageSelected}
      />
    </Box>
  );
};
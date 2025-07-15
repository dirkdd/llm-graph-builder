import React from 'react';
import { PackageAwareDropZone } from './PackageAwareDropZone';

/**
 * Drop-in replacement for the original DropZone component
 * This wrapper provides backward compatibility while adding package-aware functionality
 */
const EnhancedDropZoneWrapper: React.FC = () => {
  return (
    <PackageAwareDropZone 
      enablePackageSelection={true}
    />
  );
};

export default EnhancedDropZoneWrapper;
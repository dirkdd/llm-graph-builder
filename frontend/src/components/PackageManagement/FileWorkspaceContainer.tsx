import React, { useState, useRef, forwardRef, useImperativeHandle } from 'react';
import { Box, Typography } from '@mui/material';
import FileTable from '../FileTable';
import { PackageWorkspace } from './PackageWorkspace';
import { CustomFile, FileTableHandle, PackageSelectionContext, ChatPackageContext } from '../../types';

interface FileWorkspaceContainerProps {
  // FileTable props (legacy - not used in package-only mode)
  connectionStatus: boolean;
  setConnectionStatus: (status: boolean) => void;
  onInspect: (name: string) => void;
  onRetry: (id: string) => void;
  onChunkView: (name: string) => void;
  handleProcessPackage: () => void; // Legacy prop for compatibility
  
  // Package workspace props
  onFilesUpload: (files: File[], context: PackageSelectionContext) => void;
  onStartChat?: (packageContext: ChatPackageContext) => void;
  onViewGraph?: (packageId: string) => void;
  onProcessPackage?: (handler: () => void) => void;
  onProcessingComplete?: () => void;
}

export interface FileWorkspaceHandle extends FileTableHandle {}

const FileWorkspaceContainer = forwardRef<FileWorkspaceHandle, FileWorkspaceContainerProps>(
  (props, ref) => {
    // Always use package mode
    console.log('Package Mode Active - FileWorkspaceContainer initialized');

    // No file table methods available in package mode
    useImperativeHandle(ref, () => ({
      getSelectedRows: () => []
    }), []);


    const handlePackageFilesUpload = (files: File[], context: PackageSelectionContext) => {
      // Process files for package upload
      props.onFilesUpload(files, context);
    };

    return (
      <Box sx={{ width: '100%', height: '100%', overflow: 'hidden', paddingBottom: '20px' }}>
        <PackageWorkspace
          onFilesUpload={handlePackageFilesUpload}
          onStartChat={props.onStartChat}
          onViewGraph={props.onViewGraph}
          onProcessPackage={props.onProcessPackage}
          onProcessingComplete={props.onProcessingComplete}
        />
      </Box>
    );
  }
);

FileWorkspaceContainer.displayName = 'FileWorkspaceContainer';

export default FileWorkspaceContainer;
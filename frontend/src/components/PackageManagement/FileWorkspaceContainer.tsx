import React, { useState, useRef, forwardRef, useImperativeHandle } from 'react';
import { Button, Flex } from '@neo4j-ndl/react';
import { Box, Typography } from '@mui/material';
import { ArrowsRightLeftIcon } from '@heroicons/react/24/outline';
import FileTable from '../FileTable';
import { PackageWorkspace } from './PackageWorkspace';
import { CustomFile, FileTableHandle, PackageSelectionContext } from '../../types';

interface FileWorkspaceContainerProps {
  // FileTable props
  connectionStatus: boolean;
  setConnectionStatus: (status: boolean) => void;
  onInspect: (name: string) => void;
  onRetry: (id: string) => void;
  onChunkView: (name: string) => void;
  handleGenerateGraph: () => void;
  
  // Package workspace props
  onFilesUpload: (files: File[], context: PackageSelectionContext) => void;
}

export interface FileWorkspaceHandle extends FileTableHandle {}

const FileWorkspaceContainer = forwardRef<FileWorkspaceHandle, FileWorkspaceContainerProps>(
  (props, ref) => {
    const [workspaceMode, setWorkspaceMode] = useState<'standard' | 'package'>('package');
    const fileTableRef = useRef<FileTableHandle>(null);

    // Forward FileTable methods through ref
    useImperativeHandle(ref, () => ({
      getSelectedRows: () => {
        if (workspaceMode === 'standard' && fileTableRef.current) {
          return fileTableRef.current.getSelectedRows();
        }
        return [];
      }
    }), [workspaceMode]);

    const toggleWorkspaceMode = () => {
      setWorkspaceMode(prev => prev === 'standard' ? 'package' : 'standard');
    };

    const handlePackageFilesUpload = (files: File[], context: PackageSelectionContext) => {
      // Process files for package upload
      props.onFilesUpload(files, context);
    };

    return (
      <Box>
        {/* Workspace Mode Toggle */}
        <Box style={{ marginBottom: '24px', padding: '16px', backgroundColor: 'var(--theme-palette-neutral-bg-weak)', borderRadius: '8px' }}>
          <Flex justifyContent="space-between" alignItems="center" style={{ marginBottom: '12px' }}>
            <Typography variant="h6">
              {workspaceMode === 'standard' ? 'Standard File Management' : 'Package Workspace'}
            </Typography>
            
            <Button
              variant="outlined"
              size="small"
              onClick={toggleWorkspaceMode}
            >
              <ArrowsRightLeftIcon className="w-4 h-4" style={{ marginRight: '8px' }} />
              Switch to {workspaceMode === 'standard' ? 'Package' : 'Standard'} Mode
            </Button>
          </Flex>

          {/* Mode Description */}
          <Typography variant="body2" style={{ color: 'var(--theme-palette-text-secondary)' }}>
            {workspaceMode === 'standard' 
              ? 'Individual file upload and processing with standard extraction pipeline'
              : 'Create hierarchical document packages with categories, products, and structured file organization for enhanced mortgage document processing'
            }
          </Typography>
        </Box>

        {/* Content Area */}
        {workspaceMode === 'standard' ? (
          <FileTable
            ref={fileTableRef}
            connectionStatus={props.connectionStatus}
            setConnectionStatus={props.setConnectionStatus}
            onInspect={props.onInspect}
            onRetry={props.onRetry}
            onChunkView={props.onChunkView}
            handleGenerateGraph={props.handleGenerateGraph}
          />
        ) : (
          <Box>
            <Typography variant="h6" style={{ marginBottom: '16px' }}>Debug: Package Mode Active</Typography>
            <PackageWorkspace
              onFilesUpload={handlePackageFilesUpload}
            />
          </Box>
        )}
      </Box>
    );
  }
);

FileWorkspaceContainer.displayName = 'FileWorkspaceContainer';

export default FileWorkspaceContainer;
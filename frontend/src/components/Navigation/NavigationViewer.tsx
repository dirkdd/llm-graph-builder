import React, { useState, useEffect } from 'react';
import { Typography } from '@neo4j-ndl/react';
import { Box, Grid, Paper } from '@mui/material';
import { NavigationTreeViewer } from './NavigationTreeViewer';
import { NavigationSearch } from './NavigationSearch';
import { useNavigationData } from '../../hooks/useNavigationData';
import { useFileContext } from '../../context/UsersFiles';

interface NavigationViewerProps {
  fileName?: string;
  packageId?: string;
  onNodeNavigate?: (nodeId: string) => void;
  showSearch?: boolean;
  showDecisionTrees?: boolean;
}

export const NavigationViewer: React.FC<NavigationViewerProps> = ({
  fileName,
  packageId,
  onNodeNavigate,
  showSearch = true,
  showDecisionTrees = true
}) => {
  const { userFiles } = useFileContext();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  
  // Use fileName from props or get from context
  const targetFileName = fileName || userFiles[0]?.name;
  
  const {
    navigationData,
    loading,
    error,
    selectNode,
    fetchNavigationData,
    hasNavigationData
  } = useNavigationData({
    fileName: targetFileName,
    packageId,
    includeDecisionTrees: showDecisionTrees,
    autoFetch: !!targetFileName
  });

  useEffect(() => {
    if (targetFileName && !hasNavigationData && !loading) {
      fetchNavigationData();
    }
  }, [targetFileName, hasNavigationData, loading, fetchNavigationData]);

  const handleNodeSelect = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    selectNode(nodeId);
  };

  const handleNodeNavigate = (nodeId: string) => {
    onNodeNavigate?.(nodeId);
  };

  const handleSearchNodeSelect = (nodeId: string) => {
    handleNodeSelect(nodeId);
    // Auto-scroll to node in tree if possible
    const element = document.getElementById(`navigation-node-${nodeId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  if (error) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="body-medium" color="error">
          Failed to load navigation data: {error}
        </Typography>
      </Paper>
    );
  }

  if (!targetFileName) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="body-medium" color="text.secondary">
          No file selected for navigation view.
        </Typography>
      </Paper>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h5" gutterBottom>
          Document Navigation
        </Typography>
        <Typography variant="body-medium" color="text.secondary">
          File: {targetFileName}
          {packageId && ` (Package: ${packageId})`}
        </Typography>
      </Box>

      {/* Search */}
      {showSearch && navigationData?.nodes && (
        <Box sx={{ mb: 2 }}>
          <NavigationSearch
            nodes={navigationData.nodes}
            onNodeSelect={handleSearchNodeSelect}
            placeholder="Search document sections..."
          />
        </Box>
      )}

      {/* Navigation Tree */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <NavigationTreeViewer
          fileId={targetFileName}
          navigationData={navigationData}
          loading={loading}
          onNodeSelect={handleNodeSelect}
          onNavigate={handleNodeNavigate}
        />
      </Box>
    </Box>
  );
};
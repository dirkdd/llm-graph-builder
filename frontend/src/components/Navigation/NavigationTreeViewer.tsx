import React, { useState, useEffect } from 'react';
import { Typography, Button } from '@neo4j-ndl/react';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Alert,
  Skeleton
} from '@mui/material';
import { SimpleTreeView, TreeItem } from '@mui/x-tree-view';
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
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.5 }}>
              {getNodeIcon(node.node_type)}
              <Typography variant="body-medium" sx={{ flexGrow: 1 }}>
                {node.title}
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5 }}>
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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Skeleton variant="text" width={200} height={32} />
          <Skeleton variant="rectangular" width={80} height={24} />
          <Skeleton variant="rectangular" width={80} height={24} />
        </Box>
        {[1, 2, 3, 4].map((item) => (
          <Box key={item} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
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
        <Box sx={{ display: 'flex', gap: 1 }}>
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
          <SimpleTreeView
            defaultCollapseIcon={<ExpandMoreIcon />}
            defaultExpandIcon={<ChevronRightIcon />}
            expanded={expandedNodes}
            selected={selectedNode || undefined}
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
          </SimpleTreeView>
        </CardContent>
      </Card>

      {/* Selected Node Details */}
      {selectedNode && (
        <Box sx={{ mt: 2 }}>
          <NodeDetails 
            node={findNodeById(selectedNode)!}
            onNavigate={navigateToNode}
          />
        </Box>
      )}

      {/* Decision Tree Preview */}
      {showDecisionPreview && selectedNode && navigationData.decision_trees && (
        <Box sx={{ mt: 2 }}>
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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6">{node.title}</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
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

        <Typography variant="body-medium" sx={{ mb: 2 }}>
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
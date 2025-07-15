import { useState, useEffect, useCallback } from 'react';
import { NavigationTree, NavigationNode } from '../types';
import { 
  getFileNavigationStructure, 
  getPackageNavigationStructure,
  getEnhancedNavigationData 
} from '../services/NavigationAPI';
import { showErrorToast } from '../utils/Toasts';

interface UseNavigationDataOptions {
  fileName?: string;
  packageId?: string;
  includeDecisionTrees?: boolean;
  autoFetch?: boolean;
}

export const useNavigationData = ({
  fileName,
  packageId,
  includeDecisionTrees = true,
  autoFetch = true
}: UseNavigationDataOptions = {}) => {
  const [navigationData, setNavigationData] = useState<NavigationTree | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<NavigationNode | null>(null);

  const fetchNavigationData = useCallback(async (
    targetFileName?: string,
    targetPackageId?: string
  ) => {
    const fileToFetch = targetFileName || fileName;
    if (!fileToFetch) return;

    setLoading(true);
    setError(null);

    try {
      let response;
      
      // Choose appropriate API call based on package processing
      if (targetPackageId || packageId) {
        response = await getPackageNavigationStructure(
          fileToFetch, 
          targetPackageId || packageId!
        );
      } else if (includeDecisionTrees) {
        response = await getEnhancedNavigationData(fileToFetch, true);
      } else {
        response = await getFileNavigationStructure(fileToFetch);
      }

      if (response.status === 'success' && response.data) {
        setNavigationData(response.data);
      } else {
        const errorMsg = response.error || 'Failed to load navigation data';
        setError(errorMsg);
        showErrorToast(errorMsg);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load navigation data';
      setError(errorMsg);
      showErrorToast(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fileName, packageId, includeDecisionTrees]);

  // Auto-fetch when dependencies change
  useEffect(() => {
    if (autoFetch && fileName) {
      fetchNavigationData();
    }
  }, [autoFetch, fetchNavigationData]);

  const selectNode = useCallback((nodeId: string) => {
    if (!navigationData?.nodes) return;
    
    const node = navigationData.nodes.find(n => n.enhanced_node_id === nodeId);
    setSelectedNode(node || null);
  }, [navigationData]);

  const clearSelection = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const refreshData = useCallback(() => {
    if (fileName) {
      fetchNavigationData();
    }
  }, [fetchNavigationData, fileName]);

  // Helper functions
  const getNodeById = useCallback((nodeId: string): NavigationNode | undefined => {
    return navigationData?.nodes.find(node => node.enhanced_node_id === nodeId);
  }, [navigationData]);

  const getChildNodes = useCallback((parentId: string): NavigationNode[] => {
    if (!navigationData?.nodes) return [];
    return navigationData.nodes.filter(node => node.parent_id === parentId);
  }, [navigationData]);

  const getRootNodes = useCallback((): NavigationNode[] => {
    if (!navigationData?.nodes) return [];
    return navigationData.nodes.filter(node => !node.parent_id);
  }, [navigationData]);

  const getDecisionTreeNodes = useCallback((): NavigationNode[] => {
    if (!navigationData?.nodes) return [];
    return navigationData.nodes.filter(node => node.requires_complete_tree);
  }, [navigationData]);

  const searchNodes = useCallback((query: string): NavigationNode[] => {
    if (!navigationData?.nodes || !query.trim()) return [];
    
    const searchTerm = query.toLowerCase();
    return navigationData.nodes.filter(node => 
      node.title.toLowerCase().includes(searchTerm) ||
      node.node_type.toLowerCase().includes(searchTerm)
    );
  }, [navigationData]);

  return {
    // Data
    navigationData,
    selectedNode,
    loading,
    error,
    
    // Actions
    fetchNavigationData,
    selectNode,
    clearSelection,
    refreshData,
    
    // Helper functions
    getNodeById,
    getChildNodes,
    getRootNodes,
    getDecisionTreeNodes,
    searchNodes,
    
    // Computed values
    hasNavigationData: !!navigationData && navigationData.nodes.length > 0,
    hasDecisionTrees: !!navigationData?.decision_trees && navigationData.decision_trees.length > 0,
    nodeCount: navigationData?.nodes.length || 0,
    decisionTreeCount: navigationData?.decision_trees?.length || 0,
  };
};
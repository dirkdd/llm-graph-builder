import { AxiosResponse } from 'axios';
import api from '../API/Index';
import { NavigationTree } from '../types';

export interface NavigationAPIResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
  message?: string;
}

// Get navigation structure for a specific file
export const getFileNavigationStructure = async (
  fileName: string
): Promise<NavigationAPIResponse<NavigationTree>> => {
  try {
    const params = new URLSearchParams();
    params.append('file_name', fileName);

    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/navigation/structure?${params.toString()}`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching navigation structure:', error);
    throw error;
  }
};

// Get navigation structure for a package-processed file
export const getPackageNavigationStructure = async (
  fileName: string,
  packageId: string
): Promise<NavigationAPIResponse<NavigationTree>> => {
  try {
    const params = new URLSearchParams();
    params.append('file_name', fileName);
    params.append('package_id', packageId);

    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/navigation/package-structure?${params.toString()}`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching package navigation structure:', error);
    throw error;
  }
};

// Get enhanced navigation data with decision trees
export const getEnhancedNavigationData = async (
  fileName: string,
  includeDecisionTrees: boolean = true
): Promise<NavigationAPIResponse<NavigationTree>> => {
  try {
    const params = new URLSearchParams();
    params.append('file_name', fileName);
    params.append('include_decision_trees', includeDecisionTrees.toString());

    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/navigation/enhanced?${params.toString()}`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching enhanced navigation data:', error);
    throw error;
  }
};

// Get navigation node details
export const getNavigationNodeDetails = async (
  nodeId: string
): Promise<NavigationAPIResponse<any>> => {
  try {
    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/navigation/node/${nodeId}`,
    });

    return response.data;
  } catch (error) {
    console.error('Error fetching navigation node details:', error);
    throw error;
  }
};

// Search navigation nodes
export const searchNavigationNodes = async (
  query: string,
  fileName?: string
): Promise<NavigationAPIResponse<any[]>> => {
  try {
    const params = new URLSearchParams();
    params.append('query', query);
    if (fileName) {
      params.append('file_name', fileName);
    }

    const response: AxiosResponse = await api({
      method: 'GET',
      url: `/navigation/search?${params.toString()}`,
    });

    return response.data;
  } catch (error) {
    console.error('Error searching navigation nodes:', error);
    throw error;
  }
};
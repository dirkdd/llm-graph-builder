import React, { useState, useEffect } from 'react';
import { Typography, Button } from '@neo4j-ndl/react';
import {
  Box,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  IconButton,
  Alert,
  Skeleton
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';
import RefreshIcon from '@mui/icons-material/Refresh';
import { ProcessingStatusCard } from './ProcessingStatusCard';
import { PackageProcessingStatus, PackageFile } from '../../types';
import { usePackages } from '../../hooks/usePackages';

interface ProcessingStatusListProps {
  packages?: string[];
  onRefresh?: () => void;
  onRetryFailed?: (packageId: string, fileId: string) => void;
  onViewResults?: (packageId: string, fileId: string) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const ProcessingStatusList: React.FC<ProcessingStatusListProps> = ({
  packages,
  onRefresh,
  onRetryFailed,
  onViewResults,
  autoRefresh = true,
  refreshInterval = 5000
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [expandedPackages, setExpandedPackages] = useState<string[]>([]);

  const {
    packages: allPackages,
    loading,
    error,
    fetchPackages,
    getPackageProcessingStatus
  } = usePackages();

  const [packageStatuses, setPackageStatuses] = useState<Record<string, PackageProcessingStatus>>({});

  // Filter packages to display
  const packagesToDisplay = packages || allPackages.map(p => p.id);

  // Auto-refresh logic
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      // Only refresh packages that are actively processing
      const activePackages = Object.entries(packageStatuses)
        .filter(([_, status]) => ['processing', 'pending'].includes(status.overall_status))
        .map(([packageId]) => packageId);

      if (activePackages.length > 0) {
        await Promise.all(
          activePackages.map(async (packageId) => {
            try {
              const status = await getPackageProcessingStatus(packageId);
              setPackageStatuses(prev => ({
                ...prev,
                [packageId]: status
              }));
            } catch (error) {
              console.error(`Failed to refresh status for package ${packageId}:`, error);
            }
          })
        );
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, packageStatuses, getPackageProcessingStatus]);

  // Load initial package statuses
  useEffect(() => {
    const loadPackageStatuses = async () => {
      const statusPromises = packagesToDisplay.map(async (packageId) => {
        try {
          const status = await getPackageProcessingStatus(packageId);
          return { packageId, status };
        } catch (error) {
          console.error(`Failed to load status for package ${packageId}:`, error);
          return null;
        }
      });

      const results = await Promise.all(statusPromises);
      const statusMap: Record<string, PackageProcessingStatus> = {};
      
      results.forEach((result) => {
        if (result) {
          statusMap[result.packageId] = result.status;
        }
      });

      setPackageStatuses(statusMap);
    };

    if (packagesToDisplay.length > 0) {
      loadPackageStatuses();
    }
  }, [packagesToDisplay, getPackageProcessingStatus]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
  };

  const handleRefreshAll = async () => {
    await fetchPackages();
    onRefresh?.();
    
    // Reload all package statuses
    const statusPromises = packagesToDisplay.map(async (packageId) => {
      try {
        const status = await getPackageProcessingStatus(packageId);
        return { packageId, status };
      } catch (error) {
        console.error(`Failed to refresh status for package ${packageId}:`, error);
        return null;
      }
    });

    const results = await Promise.all(statusPromises);
    const statusMap: Record<string, PackageProcessingStatus> = {};
    
    results.forEach((result) => {
      if (result) {
        statusMap[result.packageId] = result.status;
      }
    });

    setPackageStatuses(statusMap);
  };

  const handleRetryFailed = (packageId: string, fileId: string) => {
    onRetryFailed?.(packageId, fileId);
  };

  const handleViewResults = (packageId: string, fileId: string) => {
    onViewResults?.(packageId, fileId);
  };

  const getFilteredPackages = () => {
    return allPackages.filter(pkg => {
      // Filter by search query
      if (searchQuery && !pkg.name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }

      // Filter by status
      if (statusFilter !== 'all') {
        const status = packageStatuses[pkg.id];
        if (!status || status.overall_status !== statusFilter) {
          return false;
        }
      }

      // Only show packages that are in our display list
      return packagesToDisplay.includes(pkg.id);
    });
  };

  const getOverallStats = () => {
    const statuses = Object.values(packageStatuses);
    return {
      total: statuses.length,
      completed: statuses.filter(s => s.overall_status === 'completed').length,
      processing: statuses.filter(s => s.overall_status === 'processing').length,
      failed: statuses.filter(s => s.overall_status === 'failed').length,
      pending: statuses.filter(s => s.overall_status === 'pending').length
    };
  };

  const stats = getOverallStats();
  const filteredPackages = getFilteredPackages();

  if (error) {
    return (
      <Alert severity="error">
        Failed to load package processing status: {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Package Processing Status
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Typography variant="body-medium">
              {stats.total} packages
            </Typography>
            {stats.processing > 0 && (
              <Typography variant="body-medium" color="info.main">
                • {stats.processing} processing
              </Typography>
            )}
            {stats.failed > 0 && (
              <Typography variant="body-medium" color="error.main">
                • {stats.failed} failed
              </Typography>
            )}
          </Box>
        </Box>
        <Button 
          onClick={handleRefreshAll}
          startIcon={<RefreshIcon />}
          loading={loading}
        >
          Refresh All
        </Button>
      </Box>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          size="small"
          placeholder="Search packages..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          sx={{ minWidth: 250 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
            endAdornment: searchQuery && (
              <InputAdornment position="end">
                <IconButton size="small" onClick={handleClearSearch}>
                  <ClearIcon fontSize="small" />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            label="Status"
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <MenuItem value="all">All Status</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="processing">Processing</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Package Status Cards */}
      {loading ? (
        <Grid container spacing={2}>
          {[1, 2, 3].map((item) => (
            <Grid item xs={12} key={item}>
              <Skeleton variant="rectangular" height={200} />
            </Grid>
          ))}
        </Grid>
      ) : filteredPackages.length === 0 ? (
        <Alert severity="info">
          {searchQuery || statusFilter !== 'all' 
            ? 'No packages match the current filters.' 
            : 'No packages found.'}
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {filteredPackages.map((pkg) => {
            const status = packageStatuses[pkg.id];
            if (!status) {
              return (
                <Grid item xs={12} key={pkg.id}>
                  <Skeleton variant="rectangular" height={150} />
                </Grid>
              );
            }

            return (
              <Grid item xs={12} key={pkg.id}>
                <ProcessingStatusCard
                  packageId={pkg.id}
                  packageName={pkg.name}
                  status={status}
                  files={pkg.files || []}
                  onRefresh={() => handleRefreshAll()}
                  onRetryFailed={(fileId) => handleRetryFailed(pkg.id, fileId)}
                  onViewResults={(fileId) => handleViewResults(pkg.id, fileId)}
                />
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
};
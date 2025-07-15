import React from 'react';
import { Typography } from '@neo4j-ndl/react';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  Skeleton,
  IconButton,
  Tooltip
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import FileCopyIcon from '@mui/icons-material/FileCopy';
import FolderIcon from '@mui/icons-material/Folder';
import { DocumentPackage } from '../../types';

interface PackageListProps {
  packages: DocumentPackage[];
  loading: boolean;
  onSelect: (packageId: string) => void;
  onEdit: (packageId: string) => void;
  onClone: (packageId: string) => void;
}

export const PackageList: React.FC<PackageListProps> = ({
  packages,
  loading,
  onSelect,
  onEdit,
  onClone
}) => {
  if (loading) {
    return (
      <Grid container spacing={2}>
        {[1, 2, 3].map((item) => (
          <Grid item xs={12} sm={6} md={4} key={item}>
            <Card>
              <CardContent>
                <Skeleton variant="text" width="80%" height={24} />
                <Skeleton variant="text" width="60%" height={20} />
                <Skeleton variant="rectangular" width="100%" height={60} sx={{ mt: 1 }} />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  }

  if (packages.length === 0) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          py: 6
        }}
      >
        <FolderIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6">
          No packages found
        </Typography>
        <Typography variant="body-medium">
          Create your first document package to get started
        </Typography>
      </Box>
    );
  }

  const getCategoryColor = (category: string): 'primary' | 'secondary' | 'success' | 'warning' => {
    const colors: Record<string, 'primary' | 'secondary' | 'success' | 'warning'> = {
      'NQM': 'primary',
      'RTL': 'secondary', 
      'SBC': 'success',
      'CONV': 'warning'
    };
    return colors[category] || 'primary';
  };

  return (
    <Grid container spacing={2}>
      {packages.map((pkg) => (
        <Grid item xs={12} sm={6} md={4} key={pkg.package_id}>
          <Card 
            sx={{ 
              height: '100%',
              cursor: 'pointer',
              '&:hover': { boxShadow: 3 }
            }}
            onClick={() => onSelect(pkg.package_id)}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                <Typography variant="h6" component="h3" noWrap>
                  {pkg.package_name}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  <Tooltip title="Edit Package">
                    <IconButton 
                      size="small" 
                      onClick={(e) => {
                        e.stopPropagation();
                        onEdit(pkg.package_id);
                      }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Clone Package">
                    <IconButton 
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        onClone(pkg.package_id);
                      }}
                    >
                      <FileCopyIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
              
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip 
                  label={pkg.category} 
                  color={getCategoryColor(pkg.category)}
                  size="small"
                />
                <Chip 
                  label={`v${pkg.version}`} 
                  variant="outlined"
                  size="small"
                />
              </Box>

              <Typography variant="body-medium" sx={{ mb: 2 }}>
                {pkg.documents?.length || 0} document(s) • {pkg.template_type}
              </Typography>

              <Typography variant="body-small">
                Created: {new Date(pkg.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};
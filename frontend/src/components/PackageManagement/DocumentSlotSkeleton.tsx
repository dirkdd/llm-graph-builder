/**
 * Skeleton component for document type slots while loading.
 * Provides visual feedback during API calls and data loading.
 */

import React from 'react';
import {
  Box,
  Paper,
  Skeleton,
  Grid
} from '@mui/material';

interface DocumentSlotSkeletonProps {
  count?: number;
  className?: string;
}

export const DocumentSlotSkeleton: React.FC<DocumentSlotSkeletonProps> = ({
  count = 3,
  className
}) => {
  return (
    <Box className={className}>
      {/* Header Skeleton */}
      <Box sx={{ mb: 2 }}>
        <Skeleton variant="text" width={200} height={32} sx={{ mb: 1 }} />
        <Skeleton variant="text" width="60%" height={20} />
      </Box>

      {/* Document Slots Skeleton Grid */}
      <Grid container spacing={2}>
        {Array.from({ length: count }).map((_, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <DocumentSlotSkeletonItem />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

const DocumentSlotSkeletonItem: React.FC = () => {
  return (
    <Paper
      sx={{
        p: 2,
        border: '2px dashed',
        borderColor: 'divider',
        borderRadius: 2,
        height: '200px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
        bgcolor: 'background.paper'
      }}
    >
      {/* Required Badge Skeleton */}
      <Skeleton 
        variant="rounded" 
        width={60} 
        height={20} 
        sx={{ 
          position: 'absolute', 
          top: 8, 
          right: 8 
        }} 
      />

      {/* Status Icon Skeleton */}
      <Skeleton variant="circular" width={24} height={24} sx={{ mb: 1 }} />

      {/* Document Type Skeleton */}
      <Skeleton variant="text" width={120} height={28} sx={{ mb: 0.5 }} />
      
      {/* Document Name Skeleton */}
      <Skeleton variant="text" width={160} height={20} sx={{ mb: 1 }} />

      {/* Upload Icon Skeleton */}
      <Skeleton variant="circular" width={24} height={24} sx={{ mb: 1 }} />
      
      {/* Upload Text Skeleton */}
      <Skeleton variant="text" width={140} height={16} sx={{ mb: 1 }} />

      {/* File Types Skeleton */}
      <Box sx={{ display: 'flex', gap: 0.5, mb: 0.5 }}>
        <Skeleton variant="rounded" width={35} height={20} />
        <Skeleton variant="rounded" width={40} height={20} />
        <Skeleton variant="rounded" width={30} height={20} />
      </Box>

      {/* Max Size Skeleton */}
      <Skeleton variant="text" width={80} height={14} />
    </Paper>
  );
};
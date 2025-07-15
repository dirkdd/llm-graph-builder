import React, { useState } from 'react';
import { Button, Tabs } from '@neo4j-ndl/react';
import { Box, Grid, Card, CardContent, Typography } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ListIcon from '@mui/icons-material/List';
import MonitorIcon from '@mui/icons-material/Monitor';
import AccountTreeIcon from '@mui/icons-material/AccountTree';

import { PackageManager } from '../PackageManager/PackageManager';
import { ProcessingStatusList } from '../PackageProcessing/ProcessingStatusList';
import { NavigationViewer } from '../Navigation/NavigationViewer';
import { useFileContext } from '../../context/UsersFiles';

interface PackageManagementPageProps {
  onClose?: () => void;
}

export const PackageManagementPage: React.FC<PackageManagementPageProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [showPackageManager, setShowPackageManager] = useState(false);
  const { userFiles } = useFileContext();

  const tabs = [
    { label: 'Package Overview', icon: <ListIcon /> },
    { label: 'Processing Status', icon: <MonitorIcon /> },
    { label: 'Navigation Viewer', icon: <AccountTreeIcon /> }
  ];

  const handleTabChange = (index: number) => {
    setActiveTab(index);
  };

  const handleCreatePackage = () => {
    setShowPackageManager(true);
  };

  const handleClosePackageManager = () => {
    setShowPackageManager(false);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 0:
        return (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">Package Overview</Typography>
              <Button 
                onClick={handleCreatePackage}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AddIcon />
                  Create Package
                </Box>
              </Button>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" style={{ marginBottom: '8px' }}>Quick Actions</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Button 
                        onClick={handleCreatePackage}
                        variant="outlined"
                        style={{ width: '100%' }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <AddIcon />
                          Create New Package
                        </Box>
                      </Button>
                      <Button 
                        onClick={() => setActiveTab(1)}
                        variant="outlined"
                        style={{ width: '100%' }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <MonitorIcon />
                          View Processing Status
                        </Box>
                      </Button>
                      <Button 
                        onClick={() => setActiveTab(2)}
                        variant="outlined"
                        style={{ width: '100%' }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <AccountTreeIcon />
                          Navigate Documents
                        </Box>
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" style={{ marginBottom: '8px' }}>Recent Activity</Typography>
                    <Typography variant="body1" color="text.secondary">
                      No recent package activity to display.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        );

      case 1:
        return (
          <Box>
            <ProcessingStatusList 
              autoRefresh={true}
              refreshInterval={5000}
            />
          </Box>
        );

      case 2:
        return (
          <Box>
            <NavigationViewer 
              fileName={userFiles[0]?.name}
              showSearch={true}
              showDecisionTrees={true}
            />
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ 
        borderBottom: 1, 
        borderColor: 'divider', 
        px: 3, 
        py: 2,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Typography variant="h4">Package Management</Typography>
        {onClose && (
          <Button variant="outlined" onClick={onClose}>
            Close
          </Button>
        )}
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 3 }}>
        <Tabs value={activeTab} onChange={(_, value) => handleTabChange(value)}>
          {tabs.map((tab, index) => (
            <Tabs.Tab 
              key={index}
              tabId={index}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {tab.icon}
                {tab.label}
              </Box>
            </Tabs.Tab>
          ))}
        </Tabs>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
        {renderTabContent()}
      </Box>

      {/* Package Manager Modal */}
      <PackageManager 
        isOpen={showPackageManager}
        onClose={handleClosePackageManager}
      />
    </Box>
  );
};
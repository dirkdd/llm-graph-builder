import React, { useState } from 'react';
import { Typography } from '@neo4j-ndl/react';
import {
  Box,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Chip,
  InputAdornment,
  IconButton
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';
import DescriptionIcon from '@mui/icons-material/Description';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import RuleIcon from '@mui/icons-material/Rule';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import { NavigationNode } from '../../types';

interface NavigationSearchProps {
  nodes: NavigationNode[];
  onNodeSelect: (nodeId: string) => void;
  placeholder?: string;
}

export const NavigationSearch: React.FC<NavigationSearchProps> = ({
  nodes,
  onNodeSelect,
  placeholder = "Search navigation sections..."
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<NavigationNode[]>([]);
  const [showResults, setShowResults] = useState(false);

  const getNodeIcon = (nodeType: string) => {
    switch (nodeType) {
      case 'CHAPTER':
        return <DescriptionIcon fontSize="small" color="primary" />;
      case 'SECTION':
        return <AccountTreeIcon fontSize="small" color="secondary" />;
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

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    
    if (!query.trim()) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    const searchTerm = query.toLowerCase();
    const results = nodes.filter(node => 
      node.title.toLowerCase().includes(searchTerm) ||
      node.node_type.toLowerCase().includes(searchTerm) ||
      (node.chapter_number && node.chapter_number.toString().includes(searchTerm)) ||
      (node.section_number && node.section_number.toString().includes(searchTerm))
    );

    setSearchResults(results);
    setShowResults(true);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setShowResults(false);
  };

  const handleNodeClick = (nodeId: string) => {
    onNodeSelect(nodeId);
    setShowResults(false);
  };

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === query.toLowerCase() ? 
        <mark key={index} style={{ backgroundColor: '#ffeb3b', padding: '0 2px' }}>{part}</mark> : 
        part
    );
  };

  return (
    <Box sx={{ position: 'relative', mb: 2 }}>
      <TextField
        fullWidth
        size="small"
        placeholder={placeholder}
        value={searchQuery}
        onChange={(e) => handleSearch(e.target.value)}
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

      {/* Search Results */}
      {showResults && (
        <Paper 
          sx={{ 
            position: 'absolute', 
            top: '100%', 
            left: 0, 
            right: 0, 
            zIndex: 1000,
            maxHeight: 300,
            overflow: 'auto',
            mt: 1
          }}
        >
          {searchResults.length > 0 ? (
            <List dense>
              {searchResults.map((node) => (
                <ListItem
                  key={node.enhanced_node_id}
                  button
                  onClick={() => handleNodeClick(node.enhanced_node_id)}
                  sx={{ 
                    borderBottom: '1px solid', 
                    borderColor: 'divider',
                    '&:last-child': { borderBottom: 'none' }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {getNodeIcon(node.node_type)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body-medium">
                          {highlightText(node.title, searchQuery)}
                        </Typography>
                        <Chip
                          size="small"
                          label={node.node_type.replace('_', ' ')}
                          color={getNodeTypeColor(node.node_type)}
                          sx={{ fontSize: '0.7rem', height: 18 }}
                        />
                      </Box>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        {node.chapter_number && (
                          <Chip 
                            size="small" 
                            label={`Ch. ${node.chapter_number}`} 
                            variant="outlined"
                            sx={{ fontSize: '0.65rem', height: 16 }}
                          />
                        )}
                        {node.section_number && (
                          <Chip 
                            size="small" 
                            label={`Sec. ${node.section_number}`} 
                            variant="outlined"
                            sx={{ fontSize: '0.65rem', height: 16 }}
                          />
                        )}
                        {node.depth_level && (
                          <Chip 
                            size="small" 
                            label={`Level ${node.depth_level}`} 
                            variant="outlined"
                            sx={{ fontSize: '0.65rem', height: 16 }}
                          />
                        )}
                        {node.requires_complete_tree && (
                          <Chip 
                            size="small" 
                            label="Decision Tree" 
                            color="warning"
                            sx={{ fontSize: '0.65rem', height: 16 }}
                          />
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="body-medium" color="text.secondary">
                No navigation sections found for "{searchQuery}"
              </Typography>
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
};
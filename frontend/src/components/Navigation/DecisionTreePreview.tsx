import React, { useState } from 'react';
import { Typography, Button } from '@neo4j-ndl/react';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { DecisionTree, DecisionNode } from '../../types';

interface DecisionTreePreviewProps {
  nodeId: string;
  decisionTrees: DecisionTree[];
  fileId: string;
}

export const DecisionTreePreview: React.FC<DecisionTreePreviewProps> = ({ 
  nodeId, 
  decisionTrees,
  fileId 
}) => {
  const [expandedTrees, setExpandedTrees] = useState<string[]>([]);

  // Find decision trees related to this node
  const relatedTrees = decisionTrees.filter(tree => 
    tree.section_id === nodeId || tree.root?.enhanced_node_id?.includes(nodeId)
  );

  if (relatedTrees.length === 0) {
    return (
      <Alert severity="info">
        No decision trees found for this section.
      </Alert>
    );
  }

  const handleTreeToggle = (treeId: string) => {
    setExpandedTrees(prev => 
      prev.includes(treeId) 
        ? prev.filter(id => id !== treeId)
        : [...prev, treeId]
    );
  };

  const getOutcomeColor = (outcome: string): 'success' | 'error' | 'warning' => {
    switch (outcome.toUpperCase()) {
      case 'APPROVE': return 'success';
      case 'DECLINE': return 'error';
      case 'REFER': return 'warning';
      default: return 'warning';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Decision Trees ({relatedTrees.length})
        </Typography>
        
        {relatedTrees.map((tree, index) => (
          <Accordion 
            key={`${tree.section_id}_${index}`}
            expanded={expandedTrees.includes(`${tree.section_id}_${index}`)}
            onChange={() => handleTreeToggle(`${tree.section_id}_${index}`)}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="subheading-medium">
                  Decision Tree {index + 1}
                </Typography>
                {tree.is_complete && (
                  <Chip size="small" label="Complete" color="success" />
                )}
                <Chip 
                  size="small" 
                  label={`${tree.leaves?.length || 0} outcomes`}
                  variant="outlined"
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Box>
                {/* Root Node */}
                {tree.root && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subheading-medium" gutterBottom>Root Policy</Typography>
                    <Card variant="outlined" sx={{ bgcolor: 'background.default' }}>
                      <CardContent sx={{ py: 1 }}>
                        <Typography variant="body-medium">{tree.root.title}</Typography>
                      </CardContent>
                    </Card>
                  </Box>
                )}

                {/* Branch Nodes */}
                {tree.branches && tree.branches.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subheading-medium" gutterBottom>
                      Evaluation Criteria ({tree.branches.length})
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {tree.branches.map((branch, branchIndex) => (
                        <Card key={branchIndex} variant="outlined" sx={{ bgcolor: 'background.default' }}>
                          <CardContent sx={{ py: 1 }}>
                            <Typography variant="body-medium">{branch.title}</Typography>
                            {branch.evaluation_precedence && (
                              <Chip 
                                size="small" 
                                label={`Priority ${branch.evaluation_precedence}`}
                                sx={{ mt: 0.5 }}
                              />
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </Box>
                  </Box>
                )}

                {/* Leaf Nodes (Outcomes) */}
                {tree.leaves && tree.leaves.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subheading-medium" gutterBottom>
                      Possible Outcomes ({tree.leaves.length})
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {tree.leaves.map((leaf, leafIndex) => (
                        <Chip
                          key={leafIndex}
                          label={leaf.outcome || leaf.title}
                          color={getOutcomeColor(leaf.outcome || '')}
                          variant="filled"
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {/* Decision Paths */}
                {tree.paths && tree.paths.length > 0 && (
                  <Box>
                    <Typography variant="subheading-medium" gutterBottom>
                      Decision Paths ({tree.paths.length})
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {tree.paths.slice(0, 3).map((path, pathIndex) => (
                        <Box key={pathIndex} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body-small">
                            Path {pathIndex + 1}:
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            {path.steps?.map((step, stepIndex) => (
                              <React.Fragment key={stepIndex}>
                                <Chip size="small" label={step} variant="outlined" />
                                {stepIndex < path.steps.length - 1 && (
                                  <Typography variant="body-small">→</Typography>
                                )}
                              </React.Fragment>
                            ))}
                          </Box>
                        </Box>
                      ))}
                      {tree.paths.length > 3 && (
                        <Typography variant="body-small">
                          ... and {tree.paths.length - 3} more paths
                        </Typography>
                      )}
                    </Box>
                  </Box>
                )}
              </Box>
            </AccordionDetails>
          </Accordion>
        ))}

        <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
          <Button size="small">
            View Full Decision Logic
          </Button>
          <Button size="small">
            Export Decision Tree
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};
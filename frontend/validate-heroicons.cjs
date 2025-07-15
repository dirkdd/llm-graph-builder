#!/usr/bin/env node

/**
 * Heroicons Validator for Package Management Components
 * Validates Heroicons imports which are well-documented and consistent
 */

const fs = require('fs');
const path = require('path');

// Common Heroicons that are definitely available
const HEROICONS_OUTLINE = new Set([
  'ArrowDownIcon',
  'ArrowLeftIcon', 
  'ArrowRightIcon',
  'ArrowPathIcon',
  'ArrowsRightLeftIcon',
  'ChevronDownIcon',
  'ChevronLeftIcon',
  'ChevronRightIcon',
  'ChevronUpIcon',
  'CheckCircleIcon',
  'CloudArrowUpIcon',
  'DocumentIcon',
  'DocumentPlusIcon',
  'DocumentTextIcon',
  'EllipsisHorizontalIcon',
  'ExclamationTriangleIcon',
  'FolderIcon',
  'FolderOpenIcon',
  'MagnifyingGlassIcon',
  'PlusIcon',
  'TrashIcon',
  'XMarkIcon'
]);

// Solid versions (from @heroicons/react/24/solid)
const HEROICONS_SOLID = new Set([
  'ArrowDownIcon',
  'ArrowLeftIcon',
  'ArrowRightIcon', 
  'ArrowPathIcon',
  'ArrowsRightLeftIcon',
  'ChevronDownIcon',
  'ChevronLeftIcon',
  'ChevronRightIcon',
  'ChevronUpIcon',
  'CheckCircleIcon',
  'CloudArrowUpIcon',
  'DocumentIcon',
  'DocumentPlusIcon',
  'DocumentTextIcon',
  'EllipsisHorizontalIcon',
  'ExclamationTriangleIcon',
  'FolderIcon',
  'FolderOpenIcon',
  'MagnifyingGlassIcon',
  'PlusIcon',
  'TrashIcon',
  'XMarkIcon'
]);

// Common components that should NOT be imported from Neo4j NDL
const PROBLEMATIC_NDL_IMPORTS = new Set([
  'Progress',
  'LinearProgress', 
  'Chip',
  'Box',
  'Paper',
  'Alert',
  'TextField',
  'FormControl',
  'InputLabel',
  'Select',
  'MenuItem'
]);

function validateFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const errors = [];
  
  // Check for problematic Neo4j NDL imports
  const ndlRegex = /import\s*\{([^}]+)\}\s*from\s*['"]@neo4j-ndl\/react['"];/g;
  let ndlMatch;
  while ((ndlMatch = ndlRegex.exec(content)) !== null) {
    const componentList = ndlMatch[1];
    const components = componentList.split(',').map(comp => comp.trim()).filter(comp => comp);
    
    for (const component of components) {
      if (PROBLEMATIC_NDL_IMPORTS.has(component)) {
        errors.push({
          file: filePath,
          component: component,
          type: 'neo4j-ndl-unavailable',
          suggestion: 'Use @mui/material instead'
        });
      }
    }
  }
  
  // Match Heroicons imports
  const outlineRegex = /import\s*\{([^}]+)\}\s*from\s*['"]@heroicons\/react\/24\/outline['"];/g;
  const solidRegex = /import\s*\{([^}]+)\}\s*from\s*['"]@heroicons\/react\/24\/solid['"];/g;
  
  let match;
  
  // Check outline imports
  while ((match = outlineRegex.exec(content)) !== null) {
    const iconList = match[1];
    const icons = iconList.split(',').map(icon => icon.trim()).filter(icon => icon);
    
    for (const iconName of icons) {
      if (!HEROICONS_OUTLINE.has(iconName)) {
        errors.push({
          file: filePath,
          icon: iconName,
          type: 'outline',
          available: Array.from(HEROICONS_OUTLINE).slice(0, 5).join(', ') + '...'
        });
      }
    }
  }
  
  // Check solid imports
  while ((match = solidRegex.exec(content)) !== null) {
    const iconList = match[1];
    const icons = iconList.split(',').map(icon => icon.trim()).filter(icon => icon);
    
    for (const iconName of icons) {
      if (!HEROICONS_SOLID.has(iconName)) {
        errors.push({
          file: filePath,
          icon: iconName,
          type: 'solid',
          available: Array.from(HEROICONS_SOLID).slice(0, 5).join(', ') + '...'
        });
      }
    }
  }
  
  return errors;
}

function main() {
  console.log('🔍 Validating Heroicons in Package Management components...\n');
  
  const packageComponents = [
    'src/components/PackageManagement/PackageActionBar.tsx',
    'src/components/PackageManagement/HierarchicalPackageTable.tsx', 
    'src/components/PackageManagement/ContextualDropZone.tsx',
    'src/components/PackageManagement/PackageWorkspace.tsx',
    'src/components/PackageManagement/FileWorkspaceContainer.tsx'
  ];
  
  const allErrors = [];
  
  for (const file of packageComponents) {
    const fullPath = path.join(__dirname, file);
    if (fs.existsSync(fullPath)) {
      const errors = validateFile(fullPath);
      allErrors.push(...errors);
    }
  }
  
  if (allErrors.length === 0) {
    console.log('✅ All Heroicons imports are valid!');
    console.log('✅ No problematic Neo4j NDL imports found!');
    console.log('📚 Using well-documented Heroicons package');
    return true;
  } else {
    console.log('❌ Found invalid imports:\n');
    
    for (const error of allErrors) {
      console.log(`📁 ${path.basename(error.file)}`);
      if (error.type === 'neo4j-ndl-unavailable') {
        console.log(`   Unavailable in Neo4j NDL: ${error.component}`);
        console.log(`   Solution: ${error.suggestion}\n`);
      } else {
        console.log(`   Invalid: ${error.icon} (${error.type})`);
        console.log(`   Available: ${error.available}\n`);
      }
    }
    
    console.log('📖 See https://heroicons.com/ for complete icon list');
    return false;
  }
}

if (require.main === module) {
  const success = main();
  process.exit(success ? 0 : 1);
}

module.exports = { main };
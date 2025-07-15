#!/usr/bin/env node

/**
 * Package Management Icon Validator
 * Validates only the package management components to avoid full codebase validation
 */

const fs = require('fs');
const path = require('path');

const VALID_ICONS = new Set([
  // Valid icons found in working components
  'DocumentPlusIconSolid',
  'ArrowPathIconSolid',
  'ChevronRightIconSolid',
  'ChevronDownIconOutline',
  'FolderIcon',
  'FolderOpenIcon', 
  'DocumentIcon',
  'EllipsisHorizontalIconOutline',
  'PlusIconOutline',
  'CloudArrowUpIconSolid',
  'DocumentIconOutline',
  'FolderIconOutline',
  'XMarkIconOutline',
  'CheckCircleIconOutline',
  'ExclamationTriangleIconOutline'
]);

function validateFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const errors = [];
  
  // Match icon imports
  const importRegex = /import\s*\{([^}]+)\}\s*from\s*['"]@neo4j-ndl\/react\/icons['"];/g;
  
  let match;
  while ((match = importRegex.exec(content)) !== null) {
    const iconList = match[1];
    const icons = iconList.split(',').map(icon => icon.trim()).filter(icon => icon);
    
    for (const iconName of icons) {
      if (!VALID_ICONS.has(iconName)) {
        errors.push({
          file: filePath,
          icon: iconName
        });
      }
    }
  }
  
  return errors;
}

function main() {
  console.log('🔍 Validating Package Management icon imports...\n');
  
  const packageComponents = [
    'src/components/PackageManagement/PackageActionBar.tsx',
    'src/components/PackageManagement/HierarchicalPackageTable.tsx', 
    'src/components/PackageManagement/ContextualDropZone.tsx',
    'src/components/PackageManagement/PackageWorkspace.tsx'
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
    console.log('✅ All package management icon imports are valid!');
    return true;
  } else {
    console.log('❌ Found invalid icon imports in package components:\n');
    
    for (const error of allErrors) {
      console.log(`📁 ${path.basename(error.file)}`);
      console.log(`   Invalid: ${error.icon}\n`);
    }
    
    return false;
  }
}

if (require.main === module) {
  const success = main();
  process.exit(success ? 0 : 1);
}

module.exports = { main };
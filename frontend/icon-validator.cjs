#!/usr/bin/env node

/**
 * Icon Import Validator for Neo4j NDL React Icons
 * 
 * This script validates that all icon imports in the codebase use valid Neo4j NDL icon names.
 * Run this before development server to catch import issues early.
 */

const fs = require('fs');
const path = require('path');

// Known valid icons from comprehensive codebase analysis
const VALID_ICONS = new Set([
  // Outline Icons (most common)
  'ArrowDownTrayIconOutline',
  'ArrowLeftIconOutline', 
  'ArrowRightIconOutline',
  'ArrowTopRightOnSquareIconOutline',
  'ChevronDownIconOutline',
  'ChevronUpIconOutline',
  'CircleStackIconOutline',
  'ClipboardDocumentCheckIconOutline',
  'ClipboardDocumentIconOutline',
  'DocumentDuplicateIconOutline',
  'DocumentIconOutline',
  'DocumentTextIconOutline',
  'EllipsisHorizontalIconOutline',
  'FolderIconOutline',
  'GlobeAltIconOutline',
  'InformationCircleIconOutline',
  'MagnifyingGlassIconOutline',
  'MagnifyingGlassMinusIconOutline',
  'MagnifyingGlassPlusIconOutline',
  'PlusIconOutline',
  'SpeakerWaveIconOutline',
  'SpeakerXMarkIconOutline',
  'TrashIconOutline',
  'XMarkIconOutline',
  'CheckCircleIconOutline',
  'ExclamationTriangleIconOutline',

  // Solid Icons
  'ArrowPathIconSolid',
  'ChevronLeftIconSolid',
  'ChevronRightIconSolid',
  'ClipboardDocumentIconSolid',
  'CloudArrowUpIconSolid',
  'DocumentPlusIconSolid',
  'DocumentTextIconSolid',

  // Custom Neo4j Icons (no suffix)
  'DragIcon',
  'ExploreIcon',
  'FitToScreenIcon',
  'ScienceMoleculeIcon',
  'SwitchIcon',
  'FolderIcon',
  'FolderOpenIcon',
  'DocumentIcon'
]);

function findTsxFiles(dir) {
  const files = [];
  const items = fs.readdirSync(dir);
  
  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
      files.push(...findTsxFiles(fullPath));
    } else if (item.endsWith('.tsx') || item.endsWith('.ts')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

function extractIconImports(fileContent) {
  const imports = [];
  
  // Match: import { IconName, IconName2 } from '@neo4j-ndl/react/icons';
  const importRegex = /import\s*\{([^}]+)\}\s*from\s*['"]@neo4j-ndl\/react\/icons['"];/g;
  
  let match;
  while ((match = importRegex.exec(fileContent)) !== null) {
    const iconList = match[1];
    const icons = iconList.split(',').map(icon => icon.trim()).filter(icon => icon);
    imports.push(...icons);
  }
  
  return imports;
}

function validateFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const imports = extractIconImports(content);
  const errors = [];
  
  for (const iconName of imports) {
    if (!VALID_ICONS.has(iconName)) {
      errors.push({
        file: filePath,
        icon: iconName,
        suggestion: findClosestIcon(iconName)
      });
    }
  }
  
  return errors;
}

function findClosestIcon(iconName) {
  // Remove common suffixes to find base name
  const baseName = iconName.replace(/(Icon|IconOutline|IconSolid)$/, '');
  
  // Look for similar icons
  const candidates = Array.from(VALID_ICONS).filter(validIcon => 
    validIcon.toLowerCase().includes(baseName.toLowerCase()) ||
    baseName.toLowerCase().includes(validIcon.toLowerCase().replace(/(Icon|IconOutline|IconSolid)$/, ''))
  );
  
  return candidates.length > 0 ? candidates[0] : 'Check available icons list';
}

function main() {
  console.log('🔍 Validating Neo4j NDL React icon imports...\n');
  
  const srcDir = path.join(__dirname, 'src');
  const files = findTsxFiles(srcDir);
  const allErrors = [];
  
  for (const file of files) {
    const errors = validateFile(file);
    allErrors.push(...errors);
  }
  
  if (allErrors.length === 0) {
    console.log('✅ All icon imports are valid!');
    process.exit(0);
  } else {
    console.log('❌ Found invalid icon imports:\n');
    
    for (const error of allErrors) {
      console.log(`📁 ${path.relative(srcDir, error.file)}`);
      console.log(`   Invalid: ${error.icon}`);
      console.log(`   Suggestion: ${error.suggestion}\n`);
    }
    
    console.log(`\n💡 Fix these imports before starting the development server.`);
    console.log(`📚 See the comprehensive icon list for all available options.`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { validateFile, VALID_ICONS };
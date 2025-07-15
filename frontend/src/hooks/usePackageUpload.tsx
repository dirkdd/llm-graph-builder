import { useState, useCallback } from 'react';
import { DocumentPackage, CustomFile, CustomFileBase } from '../types';
import { packageAwareUploadAPI, validateFilePackageCompatibility } from '../utils/PackageFileAPI';
import { showErrorToast, showSuccessToast } from '../utils/Toasts';
import { chunkSize } from '../utils/Constants';
import { v4 as uuidv4 } from 'uuid';

interface UsePackageUploadOptions {
  model: string;
  userCredentials: Record<string, any>;
  onFileUpdate: (updater: (files: CustomFile[]) => CustomFile[]) => void;
}

export const usePackageUpload = ({
  model,
  userCredentials,
  onFileUpdate
}: UsePackageUploadOptions) => {
  const [isUploading, setIsUploading] = useState(false);

  const uploadWithPackage = useCallback(async (
    files: File[], 
    packageInfo?: DocumentPackage
  ) => {
    if (files.length === 0) return;

    setIsUploading(true);

    try {
      // Validate files if package is selected
      if (packageInfo) {
        for (const file of files) {
          const validation = validateFilePackageCompatibility(file, packageInfo);
          if (!validation.isCompatible) {
            showErrorToast(`${file.name}: ${validation.reason}`);
            setIsUploading(false);
            return;
          }
        }
      }

      // Create file entries in the files list
      const defaultValues: CustomFileBase = {
        processingTotalTime: 0,
        status: 'None',
        nodesCount: 0,
        relationshipsCount: 0,
        model: model,
        fileSource: packageInfo ? 'package file' : 'local file',
        uploadProgress: 0,
        processingProgress: undefined,
        retryOptionStatus: false,
        retryOption: '',
        chunkNodeCount: 0,
        chunkRelCount: 0,
        entityNodeCount: 0,
        entityEntityRelCount: 0,
        communityNodeCount: 0,
        communityRelCount: 0,
        createdAt: new Date(),
        // Package-specific fields
        package_id: packageInfo?.package_id,
        package_name: packageInfo?.package_name,
        processing_type: packageInfo ? 'package' : 'standard',
        expected_structure: packageInfo?.documents[0]?.expected_structure,
      };

      // Add files to the list
      onFileUpdate((prevFiles) => {
        const newFiles = [...prevFiles];
        
        files.forEach(file => {
          const existingIndex = newFiles.findIndex(f => f.name === file.name);
          const fileData: CustomFile = {
            name: file.name,
            type: file.name.substring(file.name.lastIndexOf('.') + 1).toUpperCase(),
            size: file.size,
            uploadProgress: file.size && file.size < chunkSize ? 100 : 0,
            id: uuidv4(),
            ...defaultValues,
          };

          if (existingIndex === -1) {
            newFiles.unshift(fileData);
          } else {
            newFiles[existingIndex] = {
              ...newFiles[existingIndex],
              ...fileData,
            };
          }
        });

        return newFiles;
      });

      // Upload each file
      for (const file of files) {
        await uploadFileInChunks(file, packageInfo);
      }

    } catch (error) {
      console.error('Upload error:', error);
      showErrorToast('Failed to upload files');
    } finally {
      setIsUploading(false);
    }
  }, [model, userCredentials, onFileUpdate]);

  const uploadFileInChunks = async (file: File, packageInfo?: DocumentPackage) => {
    const totalChunks = Math.ceil(file.size / chunkSize);
    const chunkProgressIncrement = 100 / totalChunks;
    let chunkNumber = 1;
    let start = 0;
    let end = chunkSize;

    const uploadNextChunk = async (): Promise<void> => {
      if (chunkNumber <= totalChunks) {
        const chunk = file.slice(start, end);

        // Update status to uploading
        onFileUpdate(prevFiles =>
          prevFiles.map(curfile => {
            if (curfile.name === file.name) {
              return { ...curfile, status: 'Uploading' };
            }
            return curfile;
          })
        );

        try {
          const apiResponse = await packageAwareUploadAPI(
            chunk, 
            model, 
            chunkNumber, 
            totalChunks, 
            file.name,
            packageInfo,
            userCredentials
          );

          if (apiResponse?.status === 'Failed') {
            throw new Error(`message:${apiResponse.data.message},fileName:${apiResponse.data.file_name}`);
          }

          // Update progress
          onFileUpdate(prevFiles =>
            prevFiles.map(curfile => {
              if (curfile.name === file.name) {
                return {
                  ...curfile,
                  uploadProgress: Math.ceil(chunkNumber * chunkProgressIncrement),
                };
              }
              return curfile;
            })
          );

          chunkNumber++;
          start = end;
          end = start + chunkSize < file.size ? start + chunkSize : file.size + 1;
          
          await uploadNextChunk();

        } catch (error) {
          console.error('Chunk upload error:', error);
          
          onFileUpdate(prevFiles =>
            prevFiles.map(curfile => {
              if (curfile.name === file.name) {
                return {
                  ...curfile,
                  status: 'Upload Failed',
                  type: file.name.substring(file.name.lastIndexOf('.') + 1).toUpperCase(),
                };
              }
              return curfile;
            })
          );

          if (error instanceof Error) {
            showErrorToast(`Error uploading ${file.name}: ${error.message}`);
          }
          throw error;
        }
      } else {
        // Upload completed
        onFileUpdate(prevFiles =>
          prevFiles.map(curfile => {
            if (curfile.name === file.name) {
              return {
                ...curfile,
                status: 'New',
                uploadProgress: 100,
                createdAt: new Date(),
              };
            }
            return curfile;
          })
        );

        const uploadType = packageInfo ? `package "${packageInfo.package_name}"` : 'standard processing';
        showSuccessToast(`${file.name} uploaded successfully with ${uploadType}`);
      }
    };

    await uploadNextChunk();
  };

  return {
    uploadWithPackage,
    isUploading,
  };
};
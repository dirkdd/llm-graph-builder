import { useEffect, useState, useMemo, useRef, Suspense, useReducer, useCallback, useContext } from 'react';
import FileWorkspaceContainer, { FileWorkspaceHandle } from './PackageManagement/FileWorkspaceContainer';
import {
  Button,
  Typography,
  Flex,
  StatusIndicator,
  useMediaQuery,
  Menu,
  SpotlightTarget,
  useSpotlightContext,
} from '@neo4j-ndl/react';
import { useCredentials } from '../context/UserCredentials';
import { useFileContext } from '../context/UsersFiles';
import { extractAPI } from '../utils/FileAPI';
import { BannerAlertProps, ContentProps, CustomFile, OptionType, chunkdata, PackageSelectionContext } from '../types';
import deleteAPI from '../services/DeleteFiles';
import { postProcessing } from '../services/PostProcessing';
import { triggerStatusUpdateAPI } from '../services/ServerSideStatusUpdateAPI';
import useServerSideEvent from '../hooks/useSse';
import {
  batchSize,
  buttonCaptions,
  chatModeLables,
  largeFileSize,
  llms,
  RETRY_OPIONS,
  tooltips,
  tokenchunkSize,
  chunkOverlap,
  chunksToCombine,
} from '../utils/Constants';
import ButtonWithToolTip from './UI/ButtonWithToolTip';
import DropdownComponent from './Dropdown';
import GraphViewModal from './Graph/GraphViewModal';
import { lazy } from 'react';
import FallBackDialog from './UI/FallBackDialog';
import DeletePopUp from './Popups/DeletePopUp/DeletePopUp';
import GraphEnhancementDialog from './Popups/GraphEnhancementDialog';
import { tokens } from '@neo4j-ndl/base';
import axios from 'axios';
import DatabaseStatusIcon from './UI/DatabaseStatusIcon';
import RetryConfirmationDialog from './Popups/RetryConfirmation/Index';
import retry from '../services/Retry';
import { showErrorToast, showNormalToast, showSuccessToast } from '../utils/Toasts';
import { useMessageContext } from '../context/UserMessages';
import PostProcessingToast from './Popups/GraphEnhancementDialog/PostProcessingCheckList/PostProcessingToast';
import { getChunkText } from '../services/getChunkText';
import ChunkPopUp from './Popups/ChunkPopUp';
import { isExpired, isFileReadyToProcess } from '../utils/Utils';
import { useHasSelections } from '../hooks/useHasSelections';
import { ChevronUpIconOutline, ChevronDownIconOutline } from '@neo4j-ndl/react/icons';
import { ThemeWrapperContext } from '../context/ThemeWrapper';
import { useAuth0 } from '@auth0/auth0-react';
import React from 'react';

const ConfirmationDialog = lazy(() => import('./Popups/LargeFilePopUp/ConfirmationDialog'));

let afterFirstRender = false;
const Content: React.FC<ContentProps> = ({
  showEnhancementDialog,
  toggleEnhancementDialog,
  setOpenConnection,
  showDisconnectButton,
  connectionStatus,
  combinedPatterns,
  setCombinedPatterns,
  combinedNodes,
  setCombinedNodes,
  combinedRels,
  setCombinedRels,
}) => {
  const { breakpoints } = tokens;
  const isTablet = useMediaQuery(`(min-width:${breakpoints.xs}) and (max-width: ${breakpoints.lg})`);
  const [openGraphView, setOpenGraphView] = useState<boolean>(false);
  const [inspectedName, setInspectedName] = useState<string>('');
  const [documentName, setDocumentName] = useState<string>('');
  const [showConfirmationModal, setShowConfirmationModal] = useState<boolean>(false);
  const [showExpirationModal, setShowExpirationModal] = useState<boolean>(false);
  const [extractLoading, setIsExtractLoading] = useState<boolean>(false);
  const { setUserCredentials, userCredentials, setConnectionStatus, isGdsActive, isReadOnlyUser, isGCSActive } =
    useCredentials();
  const [retryFile, setRetryFile] = useState<string>('');
  const [retryLoading, setRetryLoading] = useState<boolean>(false);
  const [showRetryPopup, toggleRetryPopup] = useReducer((state) => !state, false);
  const [showChunkPopup, toggleChunkPopup] = useReducer((state) => !state, false);
  const [chunksLoading, toggleChunksLoading] = useReducer((state) => !state, false);
  const [currentPage, setCurrentPage] = useState<number>(0);
  const [totalPageCount, setTotalPageCount] = useState<number | null>(null);
  const [textChunks, setTextChunks] = useState<chunkdata[]>([]);
  const [isGraphBtnMenuOpen, setIsGraphBtnMenuOpen] = useState<boolean>(false);
  const graphbtnRef = useRef<HTMLDivElement>(null);
  const chunksTextAbortController = useRef<AbortController>();
  const [packageProcessingHandler, setPackageProcessingHandler] = useState<(() => void) | null>(null);
  const { colorMode } = useContext(ThemeWrapperContext);
  const { isAuthenticated } = useAuth0();
  const { setIsOpen } = useSpotlightContext();
  const [alertStateForRetry, setAlertStateForRetry] = useState<BannerAlertProps>({
    showAlert: false,
    alertType: 'neutral',
    alertMessage: '',
  });
  const { setMessages } = useMessageContext();
  const {
    filesData,
    setFilesData,
    setModel,
    selectedNodes,
    selectedRels,
    selectedTokenChunkSize,
    selectedChunk_overlap,
    selectedChunks_to_combine,
    setSelectedNodes,
    setAllPatterns,
    setRowSelection,
    setSelectedRels,
    setSelectedTokenChunkSize,
    setSelectedChunk_overlap,
    setSelectedChunks_to_combine,
    postProcessingTasks,
    queue,
    processedCount,
    setProcessedCount,
    setchatModes,
    model,
    additionalInstructions,
    setAdditionalInstructions,
  } = useFileContext();
  const [viewPoint, setViewPoint] = useState<
    'tableView' | 'showGraphView' | 'chatInfoView' | 'neighborView' | 'showSchemaView'
  >('tableView');
  const [showDeletePopUp, setShowDeletePopUp] = useState<boolean>(false);
  const [deleteLoading, setIsDeleteLoading] = useState<boolean>(false);

  const hasSelections = useHasSelections(selectedNodes, selectedRels);

  const { updateStatusForLargeFiles } = useServerSideEvent(
    (inMinutes, time, fileName) => {
      showNormalToast(`${fileName} will take approx ${time} ${inMinutes ? 'Min' : 'Sec'}`);
      localStorage.setItem('alertShown', JSON.stringify(true));
    },
    (fileName) => {
      showErrorToast(`${fileName} Failed to process`);
    }
  );
  const childRef = useRef<FileWorkspaceHandle>(null);

  const incrementPage = async () => {
    setCurrentPage((prev) => prev + 1);
    await getChunks(documentName, currentPage + 1);
  };
  const decrementPage = async () => {
    setCurrentPage((prev) => prev - 1);
    await getChunks(documentName, currentPage - 1);
  };

  useEffect(() => {
    if (afterFirstRender) {
      localStorage.setItem('processedCount', JSON.stringify({ db: userCredentials?.uri, count: processedCount }));
    }
    if (processedCount == batchSize && !isReadOnlyUser) {
      handleProcessPackage([], true);
    }
    if (processedCount === 1 && queue.isEmpty()) {
      (async () => {
        showNormalToast(
          <PostProcessingToast
            isGdsActive={isGdsActive}
            postProcessingTasks={postProcessingTasks}
            isSchema={hasSelections}
          />
        );
        try {
          const payload = isGdsActive
            ? hasSelections
              ? postProcessingTasks.filter((task) => task !== 'graph_schema_consolidation')
              : postProcessingTasks
            : hasSelections
              ? postProcessingTasks.filter(
                  (task) => task !== 'graph_schema_consolidation' && task !== 'enable_communities'
                )
              : postProcessingTasks.filter((task) => task !== 'enable_communities');
          if (payload.length) {
            const response = await postProcessing(payload);
            if (response.data.status === 'Success') {
              const communityfiles = response.data?.data;
              if (Array.isArray(communityfiles) && communityfiles.length) {
                communityfiles?.forEach((c: any) => {
                  setFilesData((prev) => {
                    return prev.map((f) => {
                      if (f.name === c.filename) {
                        return {
                          ...f,
                          chunkNodeCount: c.chunkNodeCount ?? 0,
                          entityNodeCount: c.entityNodeCount ?? 0,
                          communityNodeCount: c.communityNodeCount ?? 0,
                          chunkRelCount: c.chunkRelCount ?? 0,
                          entityEntityRelCount: c.entityEntityRelCount ?? 0,
                          communityRelCount: c.communityRelCount ?? 0,
                          nodesCount: c.nodeCount,
                          relationshipsCount: c.relationshipCount,
                        };
                      }
                      return f;
                    });
                  });
                });
              }
              showSuccessToast('All Q&A functionality is available now.');
            } else {
              throw new Error(response.data.error);
            }
          }
        } catch (error) {
          if (error instanceof Error) {
            showSuccessToast(error.message);
          }
        }
      })();
    }
  }, [processedCount, userCredentials, queue, isReadOnlyUser, isGdsActive]);

  useEffect(() => {
    if (afterFirstRender) {
      localStorage.setItem('waitingQueue', JSON.stringify({ db: userCredentials?.uri, queue: queue.items }));
    }
    afterFirstRender = true;
  }, [queue.items.length, userCredentials]);
  const isFirstTimeUser = useMemo(() => {
    return localStorage.getItem('neo4j.connection') === null;
  }, []);
  useEffect(() => {
    if (!isAuthenticated && !connectionStatus && isFirstTimeUser) {
      setIsOpen(true);
    }
  }, [connectionStatus, isAuthenticated, isFirstTimeUser]);
  const handleDropdownChange = (selectedOption: OptionType | null | void) => {
    if (selectedOption?.value) {
      setModel(selectedOption?.value);
    }
    setFilesData((prevfiles) => {
      return prevfiles.map((curfile) => {
        return {
          ...curfile,
          model:
            curfile.status === 'New' || curfile.status === 'Ready to Reprocess'
              ? (selectedOption?.value ?? '')
              : curfile.model,
        };
      });
    });
  };
  const getChunks = async (name: string, pageNo: number) => {
    chunksTextAbortController.current = new AbortController();
    toggleChunksLoading();
    const response = await getChunkText(name, pageNo, chunksTextAbortController.current.signal);
    setTextChunks(response.data.data.pageitems);
    if (!totalPageCount) {
      setTotalPageCount(response.data.data.total_pages);
    }
    toggleChunksLoading();
  };

  const extractData = async (uid: string, isselectedRows = false, filesTobeProcess: CustomFile[]) => {
    if (!isselectedRows) {
      const fileItem = filesData.find((f) => f.id == uid);
      if (fileItem) {
        setIsExtractLoading(true);
        await extractHandler(fileItem, uid);
      }
    } else {
      const fileItem = filesTobeProcess.find((f) => f.id == uid);
      if (fileItem) {
        setIsExtractLoading(true);
        await extractHandler(fileItem, uid);
      }
    }
  };

  const extractHandler = async (fileItem: CustomFile, uid: string) => {
    queue.remove((item) => item.name === fileItem.name);
    try {
      setFilesData((prevfiles) =>
        prevfiles.map((curfile) => {
          if (curfile.id === uid) {
            return {
              ...curfile,
              status: 'Processing',
            };
          }
          return curfile;
        })
      );
      setRowSelection((prev) => {
        const copiedobj = { ...prev };
        for (const key in copiedobj) {
          if (key == uid) {
            copiedobj[key] = false;
          }
        }
        return copiedobj;
      });
      if (fileItem.name != undefined && userCredentials != null) {
        const { name } = fileItem;
        triggerStatusUpdateAPI(name as string, userCredentials, updateStatusForLargeFiles);
      }

      const apiResponse = await extractAPI(
        fileItem.model,
        fileItem.fileSource,
        fileItem.retryOption ?? '',
        fileItem.sourceUrl,
        localStorage.getItem('accesskey'),
        atob(localStorage.getItem('secretkey') ?? ''),
        fileItem.name ?? '',
        fileItem.gcsBucket ?? '',
        fileItem.gcsBucketFolder ?? '',
        selectedNodes.map((l) => l.value),
        selectedRels.map((t) => t.value),
        selectedTokenChunkSize,
        selectedChunk_overlap,
        selectedChunks_to_combine,
        fileItem.googleProjectId,
        fileItem.language,
        fileItem.accessToken,
        additionalInstructions
      );
      if (apiResponse?.status === 'Failed') {
        let errorobj = { error: apiResponse.error, message: apiResponse.message, fileName: apiResponse.file_name };
        throw new Error(JSON.stringify(errorobj));
      } else if (fileItem.size != undefined && fileItem.size < largeFileSize) {
        if (apiResponse.data.message) {
          const apiRes = apiResponse.data.message;
          showSuccessToast(apiRes);
        }
        setFilesData((prevfiles) => {
          return prevfiles.map((curfile) => {
            if (curfile.name == apiResponse?.data?.fileName) {
              const apiRes = apiResponse?.data;
              return {
                ...curfile,
                processingProgress: apiRes?.processingTime?.toFixed(2),
                processingTotalTime: apiRes?.processingTime?.toFixed(2),
                status: apiRes?.status,
                nodesCount: apiRes?.nodeCount,
                relationshipsCount: apiRes?.relationshipCount,
                model: apiRes?.model,
              };
            }
            return curfile;
          });
        });
      }
    } catch (err: any) {
      if (err instanceof Error) {
        try {
          const error = JSON.parse(err.message);
          if (Object.keys(error).includes('fileName')) {
            setProcessedCount((prev) => {
              if (prev == batchSize) {
                return batchSize - 1;
              }
              return prev + 1;
            });
            const { message, fileName } = error;
            queue.remove((item) => item.name === fileName);
            const errorMessage = error.message;
            showErrorToast(message);
            setFilesData((prevfiles) =>
              prevfiles.map((curfile) => {
                if (curfile.name == fileName) {
                  return { ...curfile, status: 'Failed', errorMessage };
                }
                return curfile;
              })
            );
          } else {
            console.error('Unexpected error format:', error);
          }
        } catch (parseError) {
          if (axios.isAxiosError(err)) {
            const axiosErrorMessage = err.response?.data?.message || err.message;
            console.error('Axios error occurred:', axiosErrorMessage);
          } else {
            console.error('An unexpected error occurred:', err.message);
          }
        }
      } else {
        console.error('An unknown error occurred:', err);
      }
    }
  };

  const triggerBatchProcessing = (
    batch: CustomFile[],
    selectedFiles: CustomFile[],
    isSelectedFiles: boolean,
    newCheck: boolean
  ) => {
    const data = [];
    showNormalToast(`Processing ${batch.length} files at a time.`);
    for (let i = 0; i < batch.length; i++) {
      if (newCheck) {
        if (batch[i]?.status === 'New' || batch[i].status === 'Ready to Reprocess') {
          data.push(extractData(batch[i].id, isSelectedFiles, selectedFiles as CustomFile[]));
        }
      } else {
        data.push(extractData(batch[i].id, isSelectedFiles, selectedFiles as CustomFile[]));
      }
    }
    return data;
  };

  const addFilesToQueue = async (remainingFiles: CustomFile[]) => {
    if (!remainingFiles.length && postProcessingTasks.length) {
      showNormalToast(
        <PostProcessingToast
          isGdsActive={isGdsActive}
          postProcessingTasks={postProcessingTasks}
          isSchema={hasSelections}
        />
      );
      try {
        const response = await postProcessing(postProcessingTasks);
        if (response.data.status === 'Success') {
          const communityfiles = response.data?.data;
          if (Array.isArray(communityfiles) && communityfiles.length) {
            communityfiles?.forEach((c: any) => {
              setFilesData((prev) => {
                return prev.map((f) => {
                  if (f.name === c.filename) {
                    return {
                      ...f,
                      chunkNodeCount: c.chunkNodeCount ?? 0,
                      entityNodeCount: c.entityNodeCount ?? 0,
                      communityNodeCount: c.communityNodeCount ?? 0,
                      chunkRelCount: c.chunkRelCount ?? 0,
                      entityEntityRelCount: c.entityEntityRelCount ?? 0,
                      communityRelCount: c.communityRelCount ?? 0,
                      nodesCount: c.nodeCount,
                      relationshipsCount: c.relationshipCount,
                    };
                  }
                  return f;
                });
              });
            });
          }
          showSuccessToast('All Q&A functionality is available now.');
        } else {
          throw new Error(response.data.error);
        }
      } catch (error) {
        if (error instanceof Error) {
          showSuccessToast(error.message);
        }
      }
    }
    for (let index = 0; index < remainingFiles.length; index++) {
      const f = remainingFiles[index];
      setFilesData((prev) =>
        prev.map((pf) => {
          if (pf.id === f.id) {
            return {
              ...pf,
              status: 'Waiting',
            };
          }
          return pf;
        })
      );
      queue.enqueue(f);
    }
  };

  const scheduleBatchWiseProcess = (selectedRows: CustomFile[], isSelectedFiles: boolean) => {
    let data = [];
    if (queue.size() > batchSize) {
      const batch = queue.items.slice(0, batchSize);
      data = triggerBatchProcessing(batch, selectedRows as CustomFile[], isSelectedFiles, false);
    } else {
      let mergedfiles = [...selectedRows];
      let filesToProcess: CustomFile[] = [];
      if (mergedfiles.length > batchSize) {
        filesToProcess = mergedfiles.slice(0, batchSize);
        const remainingFiles = [...(mergedfiles as CustomFile[])].splice(batchSize);
        addFilesToQueue(remainingFiles);
      } else {
        filesToProcess = mergedfiles;
      }
      data = triggerBatchProcessing(filesToProcess, selectedRows as CustomFile[], isSelectedFiles, false);
    }
    return data;
  };

  /**
   * Processes package files using the package processing pipeline.
   *
   * This function processes files using the package-aware processing system:
   *   - Uses Phase 1 hierarchical chunking for Guidelines documents
   *   - Processes files with enhanced relationship detection
   *   - Provides real-time status updates during processing
   *   - Displays comprehensive package results
   *
   * For package-only mode, this directs users to use the Package Structure interface.
   * Maintains backward compatibility for legacy file processing.
   *
   * @param filesTobeProcessed - The files to be processed (legacy compatibility).
   * @param queueFiles - Whether to prioritize processing files from the queue (legacy compatibility).
   */
  const handleProcessPackage = (filesTobeProcessed: CustomFile[] = [], queueFiles: boolean = false) => {
    console.log('handleProcessPackage called with:', { filesTobeProcessed, queueFiles, packageProcessingHandler });
    
    // Check database connection
    if (!connectionStatus) {
      console.log('Database connection required for package processing');
      showErrorToast('Database connection required for package processing');
      return;
    }

    // For package-only mode, use the package processing handler
    if (filesTobeProcessed.length === 0) {
      console.log('No files to process, checking for package processing handler');
      if (packageProcessingHandler) {
        console.log('Calling package processing handler');
        setIsExtractLoading(true);
        try {
          packageProcessingHandler();
        } catch (error) {
          console.error('Package processing handler failed:', error);
          setIsExtractLoading(false);
        }
        return;
      } else {
        console.log('No package processing handler available');
        showNormalToast('Create a package and upload documents in the Package Structure panel, then use this button to process them');
        return;
      }
    }

    // Maintain backward compatibility for legacy file processing if needed
    // This will use standard chunking instead of package-aware processing
    let data = [];
    const processingFilesCount = filesData.filter((f) => f.status === 'Processing').length;
    if (filesTobeProcessed.length && !queueFiles && processingFilesCount < batchSize) {
      if (!queue.isEmpty()) {
        data = scheduleBatchWiseProcess(filesTobeProcessed as CustomFile[], true);
      } else if (filesTobeProcessed.length > batchSize) {
        const filesToProcess = filesTobeProcessed?.slice(0, batchSize) as CustomFile[];
        data = triggerBatchProcessing(filesToProcess, filesTobeProcessed as CustomFile[], true, false);
        const remainingFiles = [...(filesTobeProcessed as CustomFile[])].splice(batchSize);
        addFilesToQueue(remainingFiles);
      } else {
        let filesTobeSchedule: CustomFile[] = filesTobeProcessed;
        if (filesTobeProcessed.length + processingFilesCount > batchSize) {
          filesTobeSchedule = filesTobeProcessed.slice(
            0,
            filesTobeProcessed.length + processingFilesCount - batchSize
          ) as CustomFile[];
          const idstoexclude = new Set(filesTobeSchedule.map((f) => f.id));
          const remainingFiles = [...(childRef.current?.getSelectedRows() as CustomFile[])].filter(
            (f) => !idstoexclude.has(f.id)
          );
          addFilesToQueue(remainingFiles);
        }
        data = triggerBatchProcessing(filesTobeSchedule, filesTobeProcessed, true, true);
      }
      Promise.allSettled(data).then((_) => {
        setIsExtractLoading(false);
      });
    } else if (queueFiles && !queue.isEmpty() && processingFilesCount < batchSize) {
      data = scheduleBatchWiseProcess(queue.items, true);
      Promise.allSettled(data).then((_) => {
        setIsExtractLoading(false);
      });
    } else {
      addFilesToQueue(filesTobeProcessed as CustomFile[]);
    }
  };

  const handlePackageFilesUpload = useCallback(async (files: File[], context: PackageSelectionContext) => {
    // Handle package-aware file uploads
    console.log('Package files upload:', files, context);
    console.log('Enhanced context properties:', {
      expectedDocumentId: context.expectedDocumentId,
      preSelectedDocumentType: context.preSelectedDocumentType
    });
    
    // Import the uploadAPI function and linkDocumentUpload
    const { uploadAPI } = await import('../utils/FileAPI');
    const { chunkSize } = await import('../utils/Constants');
    const { linkDocumentUpload } = await import('../services/PackageAPI');
    
    // Convert File objects to CustomFile format for the files data
    const customFiles: CustomFile[] = files.map((file, index) => ({
      id: `${Date.now()}-${index}`,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'None',
      model: model,
      fileSource: 'local file',
      processed: false,
      processing: false,
      uploadProgress: 0,
      processingProgress: undefined,
      nodesCount: 0,
      relationshipsCount: 0,
      retryOptionStatus: false,
      retryOption: '',
      chunkNodeCount: 0,
      chunkRelCount: 0,
      entityNodeCount: 0,
      entityEntityRelCount: 0,
      communityNodeCount: 0,
      communityRelCount: 0,
      createdAt: new Date(),
      
      // Add package context
      categoryId: context.selectedCategory?.id,
      categoryName: context.selectedCategory?.name,
      productId: context.selectedProduct?.id,
      productName: context.selectedProduct?.name,
      document_type: 'Other' // Will be set by the package workspace
    }));
    
    // Add files to the main files data
    setFilesData(prev => [...customFiles, ...prev]);
    
    // Upload each file to the backend
    for (const file of files) {
      try {
        console.log(`Uploading file: ${file.name}`);
        
        // For small files, upload directly
        if (file.size < chunkSize) {
          const response = await uploadAPI(file, model, 1, 1, file.name, {
            categoryId: context.selectedCategory?.id,
            categoryName: context.selectedCategory?.name,
            productId: context.selectedProduct?.id,
            productName: context.selectedProduct?.name,
            documentType: context.preSelectedDocumentType || 'Other',
            expectedDocumentId: context.expectedDocumentId,
            preSelectedDocumentType: context.preSelectedDocumentType
          });
          if (response?.status === 'Failed') {
            throw new Error(`Upload failed: ${response.data.message}`);
          }
          
          // Update file status to 'New' after successful upload
          setFilesData(prev => prev.map(f => 
            f.name === file.name 
              ? { ...f, status: 'New', uploadProgress: 100 }
              : f
          ));
          
          // Link uploaded document to PackageDocument if context available
          if (context.selectedProduct && context.selectedProduct.packageDocuments) {
            // Try to determine document type from filename
            const isGuidelines = file.name.toLowerCase().includes('guideline');
            const isMatrix = file.name.toLowerCase().includes('matrix');
            const documentType = isGuidelines ? 'Guidelines' : isMatrix ? 'Matrix' : 'Other';
            
            // Find matching PackageDocument
            const matchingPkgDoc = context.selectedProduct.packageDocuments.find(
              pd => pd.document_type === documentType && !pd.has_upload
            );
            
            if (matchingPkgDoc) {
              try {
                await linkDocumentUpload(file.name, matchingPkgDoc.id);
                console.log(`Linked ${file.name} to package document ${matchingPkgDoc.id}`);
              } catch (linkError) {
                console.error('Failed to link document to package document:', linkError);
              }
            }
          }
          
          showSuccessToast(`${file.name} uploaded successfully`);
        } else {
          // For large files, use chunked upload
          const totalChunks = Math.ceil(file.size / chunkSize);
          const chunkProgressIncrement = 100 / totalChunks;
          let chunkNumber = 1;
          let start = 0;
          let end = chunkSize;
          
          const uploadNextChunk = async () => {
            if (chunkNumber <= totalChunks) {
              const chunk = file.slice(start, end);
              const response = await uploadAPI(chunk, model, chunkNumber, totalChunks, file.name, {
                categoryId: context.selectedCategory?.id,
                categoryName: context.selectedCategory?.name,
                productId: context.selectedProduct?.id,
                productName: context.selectedProduct?.name,
                documentType: context.preSelectedDocumentType || 'Other',
                expectedDocumentId: context.expectedDocumentId,
                preSelectedDocumentType: context.preSelectedDocumentType
              });
              
              if (response?.status === 'Failed') {
                throw new Error(`Upload failed: ${response.data.message}`);
              }
              
              // Update progress
              setFilesData(prev => prev.map(f => 
                f.name === file.name 
                  ? { ...f, uploadProgress: Math.ceil(chunkNumber * chunkProgressIncrement) }
                  : f
              ));
              
              chunkNumber++;
              start = end;
              if (start + chunkSize < file.size) {
                end = start + chunkSize;
              } else {
                end = file.size + 1;
              }
              
              if (chunkNumber <= totalChunks) {
                await uploadNextChunk();
              } else {
                // Upload complete
                setFilesData(prev => prev.map(f => 
                  f.name === file.name 
                    ? { ...f, status: 'New', uploadProgress: 100 }
                    : f
                ));
                
                // Link uploaded document to PackageDocument if context available
                if (context.selectedProduct && context.selectedProduct.packageDocuments) {
                  // Try to determine document type from filename
                  const isGuidelines = file.name.toLowerCase().includes('guideline');
                  const isMatrix = file.name.toLowerCase().includes('matrix');
                  const documentType = isGuidelines ? 'Guidelines' : isMatrix ? 'Matrix' : 'Other';
                  
                  // Find matching PackageDocument
                  const matchingPkgDoc = context.selectedProduct.packageDocuments.find(
                    pd => pd.document_type === documentType && !pd.has_upload
                  );
                  
                  if (matchingPkgDoc) {
                    try {
                      await linkDocumentUpload(file.name, matchingPkgDoc.id);
                      console.log(`Linked ${file.name} to package document ${matchingPkgDoc.id}`);
                    } catch (linkError) {
                      console.error('Failed to link document to package document:', linkError);
                    }
                  }
                }
                
                showSuccessToast(`${file.name} uploaded successfully`);
              }
            }
          };
          
          await uploadNextChunk();
        }
      } catch (error) {
        console.error(`Error uploading file ${file.name}:`, error);
        
        // Update file status to 'Failed'
        setFilesData(prev => prev.map(f => 
          f.name === file.name 
            ? { ...f, status: 'Failed', uploadProgress: 0 }
            : f
        ));
        
        showErrorToast(`Failed to upload ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  }, [model, setFilesData, showSuccessToast, showErrorToast]);

  const handleRegisterPackageProcessing = useCallback((handler: () => void) => {
    console.log('Registering package processing handler:', handler);
    setPackageProcessingHandler(() => handler);
  }, []);

  const handleProcessingComplete = useCallback(() => {
    console.log('Package processing completed, resetting loading state');
    setIsExtractLoading(false);
  }, []);

  const processWaitingFilesOnRefresh = useCallback(() => {
    let data = [];
    const processingFilesCount = filesData.filter((f) => f.status === 'Processing').length;

    if (!queue.isEmpty() && processingFilesCount < batchSize) {
      if (queue.size() > batchSize) {
        const batch = queue.items.slice(0, batchSize);
        data = triggerBatchProcessing(batch, queue.items as CustomFile[], true, false);
      } else {
        data = triggerBatchProcessing(queue.items, queue.items as CustomFile[], true, false);
      }
      Promise.allSettled(data).then((_) => {
        setIsExtractLoading(false);
      });
    } else {
      const selectedNewFiles = childRef.current
        ?.getSelectedRows()
        .filter((f) => f.status === 'New' || f.status == 'Ready to Reprocess');
      addFilesToQueue(selectedNewFiles as CustomFile[]);
    }
  }, [filesData, queue]);

  const handleOpenGraphClick = () => {
    const bloomUrl = process.env.VITE_BLOOM_URL;
    let finalUrl = bloomUrl;
    if (userCredentials?.database && userCredentials.uri && userCredentials.userName) {
      const uriCoded = userCredentials.uri.replace(/:\d+$/, '');
      const connectURL = `${uriCoded.split('//')[0]}//${userCredentials.userName}@${uriCoded.split('//')[1]}:${
        userCredentials.port ?? '7687'
      }`;
      const encodedURL = encodeURIComponent(connectURL);
      finalUrl = bloomUrl?.replace('{CONNECT_URL}', encodedURL);
    }
    window.open(finalUrl, '_blank');
  };

  const handleGraphView = () => {
    setOpenGraphView(true);
    setViewPoint('showGraphView');
  };

  const disconnect = () => {
    queue.clear();
    const date = new Date();
    setProcessedCount(0);
    setConnectionStatus(false);
    localStorage.removeItem('password');
    localStorage.removeItem('selectedModel');
    setUserCredentials({ uri: '', password: '', userName: '', database: '', email: '' });
    setSelectedNodes([]);
    setSelectedRels([]);
    setAllPatterns([]);
    localStorage.removeItem('selectedTokenChunkSize');
    setSelectedTokenChunkSize(tokenchunkSize);
    localStorage.removeItem('selectedChunk_overlap');
    setSelectedChunk_overlap(chunkOverlap);
    localStorage.removeItem('selectedChunks_to_combine');
    setSelectedChunks_to_combine(chunksToCombine);
    localStorage.removeItem('instructions');
    localStorage.removeItem('selectedNodeLabels');
    localStorage.removeItem('selectedRelationshipLabels');
    localStorage.removeItem('selectedPattern');
    setAdditionalInstructions('');
    setMessages([
      {
        datetime: `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`,
        id: 2,
        modes: {
          'graph+vector+fulltext': {
            message:
              ' Welcome to the Neo4j Knowledge Graph Chat. You can ask questions related to documents which have been completely processed.',
          },
        },
        user: 'chatbot',
        currentMode: 'graph+vector+fulltext',
      },
    ]);
    setchatModes([chatModeLables['graph+vector+fulltext']]);
  };

  const retryHandler = async (filename: string, retryoption: string) => {
    try {
      setRetryLoading(true);
      const response = await retry(filename, retryoption);
      setRetryLoading(false);
      if (response.data.status === 'Failure') {
        throw new Error(response.data.error);
      } else if (
        response.data.status === 'Success' &&
        response.data?.message != undefined &&
        (response.data?.message as string).includes('Chunks are not created')
      ) {
        showNormalToast(response.data.message as string);
        retryOnclose();
      } else {
        const isStartFromBegining = retryoption === RETRY_OPIONS[0] || retryoption === RETRY_OPIONS[1];
        setFilesData((prev) => {
          return prev.map((f) => {
            return f.name === filename
              ? {
                  ...f,
                  status: 'Ready to Reprocess',
                  processingProgress: isStartFromBegining ? 0 : f.processingProgress,
                  nodesCount: isStartFromBegining ? 0 : f.nodesCount,
                  relationshipsCount: isStartFromBegining ? 0 : f.relationshipsCount,
                }
              : f;
          });
        });
        showSuccessToast(response.data.message as string);
        retryOnclose();
      }
    } catch (error) {
      setRetryLoading(false);
      if (error instanceof Error) {
        setAlertStateForRetry({
          showAlert: true,
          alertMessage: error.message,
          alertType: 'danger',
        });
      }
    }
  };

  const selectedfileslength = useMemo(
    () => childRef.current?.getSelectedRows().length,
    [childRef.current?.getSelectedRows()]
  );

  const newFilecheck = useMemo(
    () =>
      childRef.current?.getSelectedRows().filter((f) => f.status === 'New' || f.status == 'Ready to Reprocess').length,
    [childRef.current?.getSelectedRows()]
  );

  const completedfileNo = useMemo(
    () => childRef.current?.getSelectedRows().filter((f) => f.status === 'Completed').length,
    [childRef.current?.getSelectedRows()]
  );

  const dropdowncheck = useMemo(
    () => !filesData.some((f) => f.status === 'New' || f.status === 'Waiting' || f.status === 'Ready to Reprocess'),
    [filesData]
  );

  const disableCheck = useMemo(() => {
    // In package mode, always enable the button - package structure will handle validation
    // The button will direct users to use package interface or process available files
    return false;
  }, []);

  const showGraphCheck = useMemo(
    () => (selectedfileslength ? completedfileNo === 0 : true),
    [selectedfileslength, completedfileNo]
  );

  const filesForProcessing = useMemo(() => {
    let newstatusfiles: CustomFile[] = [];
    const selectedRows = childRef.current?.getSelectedRows();
    if (selectedRows?.length) {
      for (let index = 0; index < selectedRows.length; index++) {
        const parsedFile: CustomFile = selectedRows[index];
        if (parsedFile.status === 'New' || parsedFile.status == 'Ready to Reprocess') {
          newstatusfiles.push(parsedFile);
        }
      }
    } else if (filesData.length) {
      newstatusfiles = filesData.filter((f) => f.status === 'New' || f.status === 'Ready to Reprocess');
    }
    return newstatusfiles;
  }, [filesData, childRef.current?.getSelectedRows()]);

  const handleDeleteFiles = async (deleteEntities: boolean) => {
    try {
      setIsDeleteLoading(true);
      const response = await deleteAPI(childRef.current?.getSelectedRows() as CustomFile[], deleteEntities);
      queue.clear();
      setProcessedCount(0);
      setRowSelection({});
      setIsDeleteLoading(false);
      if (response.data.status == 'Success') {
        showSuccessToast(response.data.message);
        const filenames = childRef.current?.getSelectedRows().map((str) => str.name);
        if (filenames?.length) {
          for (let index = 0; index < filenames.length; index++) {
            const name = filenames[index];
            setFilesData((prev) => prev.filter((f) => f.name != name));
          }
        }
      } else {
        let errorobj = { error: response.data.error, message: response.data.message };
        throw new Error(JSON.stringify(errorobj));
      }
      setShowDeletePopUp(false);
    } catch (err) {
      setIsDeleteLoading(false);
      if (err instanceof Error) {
        const error = JSON.parse(err.message);
        const { message } = error;
        showErrorToast(message);
        console.log(err);
      }
    }
    setShowDeletePopUp(false);
  };

  const onClickHandler = () => {
    console.log('Generate Graph button clicked');
    const selectedRows = childRef.current?.getSelectedRows();
    console.log('Selected rows:', selectedRows);
    if (selectedRows?.length) {
      const expiredFilesExists = selectedRows.some(
        (c) => isFileReadyToProcess(c, true) && isExpired((c?.createdAt as Date) ?? new Date())
      );
      const largeFileExists = selectedRows.some(
        (c) => isFileReadyToProcess(c, true) && typeof c.size === 'number' && c.size > largeFileSize
      );
      if (expiredFilesExists) {
        setShowExpirationModal(true);
      } else if (largeFileExists && isGCSActive) {
        setShowConfirmationModal(true);
      } else {
        handleProcessPackage(selectedRows.filter((f) => isFileReadyToProcess(f, false)));
      }
    } else if (filesData.length) {
      console.log('Processing all files from filesData:', filesData.length);
      const expiredFileExists = filesData.some((c) => isFileReadyToProcess(c, true) && isExpired(c?.createdAt as Date));
      const largeFileExists = filesData.some(
        (c) => isFileReadyToProcess(c, true) && typeof c.size === 'number' && c.size > largeFileSize
      );
      const selectAllNewFiles = filesData.filter((f) => isFileReadyToProcess(f, false));
      console.log('Files ready to process:', selectAllNewFiles);
      const stringified = selectAllNewFiles.reduce((accu, f) => {
        const key = f.id;
        // @ts-ignore
        accu[key] = true;
        return accu;
      }, {});
      setRowSelection(stringified);
      if (largeFileExists) {
        setShowConfirmationModal(true);
      } else if (expiredFileExists && isGCSActive) {
        setShowExpirationModal(true);
      } else {
        handleProcessPackage(filesData.filter((f) => isFileReadyToProcess(f, false)));
      }
    } else {
      console.log('No files available, calling handleProcessPackage with empty array');
      handleProcessPackage([]);
    }
  };

  const retryOnclose = useCallback(() => {
    setRetryFile('');
    setAlertStateForRetry({
      showAlert: false,
      alertMessage: '',
      alertType: 'neutral',
    });
    setRetryLoading(false);
    toggleRetryPopup();
  }, []);

  const onBannerClose = useCallback(() => {
    setAlertStateForRetry({
      showAlert: false,
      alertMessage: '',
      alertType: 'neutral',
    });
  }, []);

  const handleSchemaView = () => {
    setOpenGraphView(true);
    setViewPoint('showSchemaView');
  };

  return (
    <>
      <RetryConfirmationDialog
        retryLoading={retryLoading}
        retryHandler={retryHandler}
        fileId={retryFile}
        onClose={retryOnclose}
        open={showRetryPopup}
        onBannerClose={onBannerClose}
        alertStatus={alertStateForRetry}
      />
      {showConfirmationModal && filesForProcessing.length && (
        <Suspense fallback={<FallBackDialog />}>
          <ConfirmationDialog
            open={showConfirmationModal}
            largeFiles={filesForProcessing}
            extractHandler={handleProcessPackage}
            onClose={() => setShowConfirmationModal(false)}
            loading={extractLoading}
            selectedRows={childRef.current?.getSelectedRows() as CustomFile[]}
            isLargeDocumentAlert={true}
          ></ConfirmationDialog>
        </Suspense>
      )}
      {showExpirationModal && filesForProcessing.length && (
        <Suspense fallback={<FallBackDialog />}>
          <ConfirmationDialog
            open={showExpirationModal}
            largeFiles={filesForProcessing}
            extractHandler={handleProcessPackage}
            onClose={() => setShowExpirationModal(false)}
            loading={extractLoading}
            selectedRows={childRef.current?.getSelectedRows() as CustomFile[]}
            isLargeDocumentAlert={false}
          ></ConfirmationDialog>
        </Suspense>
      )}
      {showExpirationModal && filesForProcessing.length && (
        <Suspense fallback={<FallBackDialog />}>
          <ConfirmationDialog
            open={showExpirationModal}
            largeFiles={filesForProcessing}
            extractHandler={handleProcessPackage}
            onClose={() => setShowExpirationModal(false)}
            loading={extractLoading}
            selectedRows={childRef.current?.getSelectedRows() as CustomFile[]}
            isLargeDocumentAlert={false}
          ></ConfirmationDialog>
        </Suspense>
      )}
      {showExpirationModal && filesForProcessing.length && (
        <Suspense fallback={<FallBackDialog />}>
          <ConfirmationDialog
            open={showExpirationModal}
            largeFiles={filesForProcessing}
            extractHandler={handleProcessPackage}
            onClose={() => setShowExpirationModal(false)}
            loading={extractLoading}
            selectedRows={childRef.current?.getSelectedRows() as CustomFile[]}
            isLargeDocumentAlert={false}
          ></ConfirmationDialog>
        </Suspense>
      )}
      {showDeletePopUp && (
        <DeletePopUp
          open={showDeletePopUp}
          no_of_files={selectedfileslength ?? 0}
          deleteHandler={(delentities: boolean) => handleDeleteFiles(delentities)}
          deleteCloseHandler={() => setShowDeletePopUp(false)}
          loading={deleteLoading}
          view='contentView'
        ></DeletePopUp>
      )}
      {showChunkPopup && (
        <ChunkPopUp
          chunksLoading={chunksLoading}
          onClose={() => {
            chunksTextAbortController.current?.abort();
            toggleChunkPopup();
          }}
          showChunkPopup={showChunkPopup}
          chunks={textChunks}
          incrementPage={incrementPage}
          decrementPage={decrementPage}
          currentPage={currentPage}
          totalPageCount={totalPageCount}
        ></ChunkPopUp>
      )}
      {showEnhancementDialog && (
        <GraphEnhancementDialog
          open={showEnhancementDialog}
          onClose={toggleEnhancementDialog}
          combinedPatterns={combinedPatterns}
          setCombinedPatterns={setCombinedPatterns}
          combinedNodes={combinedNodes}
          setCombinedNodes={setCombinedNodes}
          combinedRels={combinedRels}
          setCombinedRels={setCombinedRels}
        ></GraphEnhancementDialog>
      )}
      <GraphViewModal
        inspectedName={inspectedName}
        open={openGraphView}
        setGraphViewOpen={setOpenGraphView}
        viewPoint={viewPoint}
        selectedRows={childRef.current?.getSelectedRows()}
      />
      <div className={`n-bg-palette-neutral-bg-default main-content-wrapper`}>
        <Flex
          className='w-full absolute top-0'
          alignItems='center'
          justifyContent='space-between'
          flexDirection='row'
          flexWrap='wrap'
        >
          <div className='connectionstatus__container'>
            <span className='h6 px-1'>Neo4j connection {isReadOnlyUser ? '(Read only Mode)' : ''}</span>
            <Typography variant='body-medium'>
              <DatabaseStatusIcon
                isConnected={connectionStatus}
                isGdsActive={isGdsActive}
                uri={userCredentials?.uri}
                database={userCredentials?.database}
              />
              <div className='pt-1 flex! gap-1 items-center'>
                <div>{!hasSelections ? <StatusIndicator type='danger' /> : <StatusIndicator type='success' />}</div>
                <div>
                  {hasSelections ? (
                    <span className='n-body-small'>
                      {hasSelections} Graph Schema configured
                      {hasSelections ? `(${selectedNodes.length} Labels + ${selectedRels.length} Rel Types)` : ''}
                    </span>
                  ) : (
                    <span className='n-body-small'>No Graph Schema configured</span>
                  )}
                </div>
              </div>
            </Typography>
          </div>
          <div className='enhancement-btn__wrapper'>
            {!connectionStatus ? (
              <SpotlightTarget
                id='connectbutton'
                hasPulse={true}
                indicatorVariant='border'
                className='n-bg-palette-primary-bg-strong hover:n-bg-palette-primary-hover-strong'
              >
                <Button
                  size={isTablet ? 'small' : 'medium'}
                  className='mr-2!'
                  onClick={() => setOpenConnection((prev) => ({ ...prev, openPopUp: true }))}
                >
                  {buttonCaptions.connectToNeo4j}
                </Button>
              </SpotlightTarget>
            ) : (
              showDisconnectButton && (
                <Button size={isTablet ? 'small' : 'medium'} className='mr-2.5' onClick={disconnect}>
                  {buttonCaptions.disconnect}
                </Button>
              )
            )}
          </div>
        </Flex>

        <div style={{ marginTop: '100px', marginBottom: '120px' }}>
          <FileWorkspaceContainer
            connectionStatus={connectionStatus}
            setConnectionStatus={setConnectionStatus}
            onInspect={useCallback((name) => {
              setInspectedName(name);
              setOpenGraphView(true);
              setViewPoint('tableView');
            }, [])}
            onRetry={useCallback((id) => {
              setRetryFile(id);
              toggleRetryPopup();
            }, [])}
            onChunkView={useCallback(
              async (name) => {
                setDocumentName(name);
                if (name != documentName) {
                  toggleChunkPopup();
                  if (totalPageCount) {
                    setTotalPageCount(null);
                  }
                  setCurrentPage(1);
                  await getChunks(name, 1);
                }
              },
              [documentName, totalPageCount]
            )}
            ref={childRef}
            handleProcessPackage={processWaitingFilesOnRefresh}
            onFilesUpload={handlePackageFilesUpload}
            onProcessPackage={handleRegisterPackageProcessing}
            onProcessingComplete={handleProcessingComplete}
          />
        </div>

        <Flex className={`p-2.5  mt-1.5 absolute bottom-0 w-full`} justifyContent='space-between' flexDirection={'row'}>
          <div>
            <DropdownComponent
              onSelect={handleDropdownChange}
              options={llms ?? ['']}
              placeholder='Select LLM Model'
              defaultValue={model}
              view='ContentView'
              isDisabled={false}
            />
          </div>
          <Flex flexDirection='row' gap='4' className='self-end mb-2.5' flexWrap='wrap'>
            <ButtonWithToolTip
              placement='top'
              text='Enhance graph quality'
              label='Graph Enhancement Settings'
              className='mr-0.5'
              onClick={toggleEnhancementDialog}
              disabled={!connectionStatus || isReadOnlyUser}
              size={isTablet ? 'small' : 'medium'}
            >
              Graph Enhancement
            </ButtonWithToolTip>
            <SpotlightTarget id='generategraphbtn'>
              <ButtonWithToolTip
                text={tooltips.generateGraph}
                placement='top'
                label='generate graph'
                onClick={onClickHandler}
                disabled={disableCheck || isReadOnlyUser || extractLoading}
                className='mr-0.5'
                size={isTablet ? 'small' : 'medium'}
              >
                {extractLoading ? 'Processing...' : buttonCaptions.generateGraph}{' '}
                {selectedfileslength && !disableCheck && newFilecheck ? `(${newFilecheck})` : ''}
              </ButtonWithToolTip>
            </SpotlightTarget>
            <ButtonWithToolTip
              text={
                !selectedfileslength ? tooltips.deleteFile : `${selectedfileslength} ${tooltips.deleteSelectedFiles}`
              }
              placement='top'
              onClick={() => setShowDeletePopUp(true)}
              disabled={!selectedfileslength || isReadOnlyUser}
              className='ml-0.5'
              label='Delete Files'
              size={isTablet ? 'small' : 'medium'}
            >
              {buttonCaptions.deleteFiles}
              {selectedfileslength != undefined && selectedfileslength > 0 && `(${selectedfileslength})`}
            </ButtonWithToolTip>
            <SpotlightTarget id='visualizegraphbtn'>
              <Flex flexDirection='row' gap='0'>
                <Button
                  onClick={handleGraphView}
                  isDisabled={showGraphCheck}
                  className='px-0! flex! items-center justify-between gap-4 graphbtn'
                  size={isTablet ? 'small' : 'medium'}
                >
                  <span className='mx-2'>
                    {buttonCaptions.showPreviewGraph}{' '}
                    {selectedfileslength && completedfileNo ? `(${completedfileNo})` : ''}
                  </span>
                </Button>
                <div
                  className={`ndl-icon-btn ndl-clean dropdownbtn ${colorMode === 'dark' ? 'darktheme' : ''} ${
                    isTablet ? 'small' : 'medium'
                  }`}
                  onClick={(e) => {
                    setIsGraphBtnMenuOpen((old) => !old);
                    e.stopPropagation();
                  }}
                  ref={graphbtnRef}
                >
                  {!isGraphBtnMenuOpen ? (
                    <ChevronUpIconOutline className='n-size-token-5' />
                  ) : (
                    <ChevronDownIconOutline className='n-size-token-' />
                  )}
                </div>
              </Flex>
            </SpotlightTarget>
            <Menu
              placement='top-end-bottom-end'
              isOpen={isGraphBtnMenuOpen}
              anchorRef={graphbtnRef}
              onClose={() => setIsGraphBtnMenuOpen(false)}
            >
              <Menu.Items
                htmlAttributes={{
                  id: 'default-menu',
                }}
              >
                <Menu.Item title='Graph Schema' onClick={handleSchemaView} isDisabled={!connectionStatus} />
                <Menu.Item
                  title='Explore Graph in Neo4j'
                  onClick={handleOpenGraphClick}
                  isDisabled={!filesData.some((f) => f?.status === 'Completed')}
                />
              </Menu.Items>
            </Menu>
          </Flex>
        </Flex>
      </div>
    </>
  );
};

export default React.memo(Content);

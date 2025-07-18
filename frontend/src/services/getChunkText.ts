import { chunksData } from '../types';
import api from '../API/Index';

export const getChunkText = async (documentName: string, page_no: number, signal: AbortSignal) => {
  const formData = new FormData();
  formData.append('document_name', documentName);
  formData.append('page_no', page_no.toString());
  try {
    const response = await api.post<chunksData>(`/fetch_chunktext`, formData, { signal });
    return response;
  } catch (error) {
    console.log(error);
    throw error;
  }
};

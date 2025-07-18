import { CustomFile } from '../types';
import api from '../API/Index';

const deleteAPI = async (selectedFiles: CustomFile[], deleteEntities: boolean) => {
  try {
    const filenames = selectedFiles.map((str) => str.name);
    const source_types = selectedFiles.map((str) => str.fileSource);
    const formData = new FormData();
    formData.append('deleteEntities', JSON.stringify(deleteEntities));
    formData.append('filenames', JSON.stringify(filenames));
    formData.append('source_types', JSON.stringify(source_types));
    const response = await api.post(`/delete_document_and_entities`, formData);
    return response;
  } catch (error) {
    console.log('Error Posting the Question:', error);
    throw error;
  }
};
export default deleteAPI;

import api from '../API/Index';
import { ChatPackageContext } from '../types';

export const chatBotAPI = async (
  question: string,
  session_id: string,
  model: string,
  mode: string,
  document_names?: (string | undefined)[],
  packageContext?: ChatPackageContext
) => {
  try {
    const formData = new FormData();
    formData.append('question', question);
    formData.append('session_id', session_id);
    formData.append('model', model);
    formData.append('mode', mode);
    formData.append('document_names', JSON.stringify(document_names));
    
    // Add package context if provided
    if (packageContext) {
      formData.append('package_context', JSON.stringify(packageContext));
      
      // Enhanced question with package context
      const contextualQuestion = `
        ${question}
        
        PACKAGE CONTEXT:
        - Package: ${packageContext.packageName}
        - Document Types: ${packageContext.documentTypes.join(', ')}
        - Categories: ${packageContext.categories.join(', ')}
        - Products: ${packageContext.products.join(', ')}
        
        Please provide responses considering this package context and focus on relevant document types and categories.
      `;
      
      formData.set('question', contextualQuestion);
    }
    
    const startTime = Date.now();
    const response = await api.post(`/chat_bot`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    const endTime = Date.now();
    const timeTaken = endTime - startTime;
    return { response: response, timeTaken: timeTaken };
  } catch (error) {
    console.log('Error Posting the Question:', error);
    throw error;
  }
};

export const clearChatAPI = async (session_id: string) => {
  try {
    const formData = new FormData();
    formData.append('session_id', session_id);
    const response = await api.post(`/clear_chat_bot`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response;
  } catch (error) {
    console.log('Error Posting the Question:', error);
    throw error;
  }
};

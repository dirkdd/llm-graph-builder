import Header from './Layout/Header';
import React from 'react';
import PageLayout from './Layout/PageLayout';
import { FileContextProvider } from '../context/UsersFiles';
import UserCredentialsWrapper from '../context/UserCredentials';
import AlertContextWrapper from '../context/Alert';
import { MessageContextWrapper } from '../context/UserMessages';
import { PackageContextProvider } from '../context/PackageContext';

const QuickStarter: React.FunctionComponent = () => {
  return (
    <UserCredentialsWrapper>
      <FileContextProvider>
        <PackageContextProvider>
          <MessageContextWrapper>
            <AlertContextWrapper>
              <Header />
              <PageLayout />
            </AlertContextWrapper>
          </MessageContextWrapper>
        </PackageContextProvider>
      </FileContextProvider>
    </UserCredentialsWrapper>
  );
};
export default QuickStarter;

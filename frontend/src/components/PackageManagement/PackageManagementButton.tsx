import React, { useState } from 'react';
import { Button, Dialog } from '@neo4j-ndl/react';
import { Box } from '@mui/material';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import { IconButtonWithToolTip } from '../UI/IconButtonToolTip';
import { PackageManagementPage } from './PackageManagementPage';
import { tooltips } from '../../utils/Constants';

interface PackageManagementButtonProps {
  variant?: 'button' | 'icon';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
}

export const PackageManagementButton: React.FC<PackageManagementButtonProps> = ({
  variant = 'icon',
  size = 'large',
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleOpen = () => {
    setIsOpen(true);
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  const renderButton = () => {
    if (variant === 'button') {
      return (
        <Button
          onClick={handleOpen}
          disabled={disabled}
          startIcon={<AccountTreeIcon />}
          size={size}
        >
          Package Manager
        </Button>
      );
    }

    return (
      <IconButtonWithToolTip
        text="Package Management"
        onClick={handleOpen}
        size={size}
        clean
        placement="left"
        label="Package Management"
        disabled={disabled}
      >
        <AccountTreeIcon className="n-size-token-7" />
      </IconButtonWithToolTip>
    );
  };

  return (
    <>
      {renderButton()}
      
      <Dialog
        isOpen={isOpen}
        onClose={handleClose}
        size="large"
        htmlAttributes={{
          style: {
            width: '95vw',
            height: '95vh',
            maxWidth: '1400px',
            maxHeight: '900px'
          }
        }}
      >
        <Dialog.Content className="n-flex n-flex-col n-gap-token-4" style={{ padding: 0 }}>
          <PackageManagementPage onClose={handleClose} />
        </Dialog.Content>
      </Dialog>
    </>
  );
};
import React from 'react';
import { TextField } from '@mui/material';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  minHeight?: number;
}

export const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  placeholder,
  minHeight = 200,
}) => {
  return (
    <TextField
      fullWidth
      multiline
      minRows={Math.max(6, Math.ceil(minHeight / 28))}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  );
};

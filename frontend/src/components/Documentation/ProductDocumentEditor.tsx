import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Preview as PreviewIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { MarkdownEditor } from '../Common/MarkdownEditor';

export interface ProductDocument {
  id?: string;
  title: string;
  product_name: string;
  version: string;
  status: string;
  owner: string;
  stakeholders: string[];
  target_users: string[];
  use_cases: string[];
  primary_tech: string[];
  sla_requirements: string;
  data_residency: string;
  regulatory_considerations: string[];
  created_at?: string;
  updated_at?: string;
  content?: string;
}

interface DocumentSection {
  title: string;
  content: string;
  order: number;
}

const DEFAULT_SECTIONS: DocumentSection[] = [
  { title: '1. Executive Summary', content: '', order: 1 },
  { title: '2. Problem Statement', content: '', order: 2 },
  { title: '3. Goals and Non-Goals', content: '', order: 3 },
  { title: '4. Personas', content: '', order: 4 },
  { title: '5. User Journeys & Workflows', content: '', order: 5 },
  { title: '6. Functional Requirements', content: '', order: 6 },
];

interface ProductDocumentEditorProps {
  document?: ProductDocument;
  onSave?: (document: ProductDocument) => void | Promise<void>;
  onCancel?: () => void;
  mode?: 'create' | 'edit' | 'view';
}

export const ProductDocumentEditor: React.FC<ProductDocumentEditorProps> = ({
  document,
  onSave,
  onCancel,
  mode = 'create',
}) => {
  const notify = (message: string) => console.info(message);

  const [formData, setFormData] = useState<ProductDocument>({
    title: '',
    product_name: '',
    version: '0.1.0',
    status: 'Draft',
    owner: '',
    stakeholders: [],
    target_users: [],
    use_cases: [],
    primary_tech: [],
    sla_requirements: '',
    data_residency: '',
    regulatory_considerations: [],
  });
  const [sections, setSections] = useState<DocumentSection[]>(DEFAULT_SECTIONS);
  const [newStakeholder, setNewStakeholder] = useState('');
  const [newTargetUser, setNewTargetUser] = useState('');
  const [newUseCase, setNewUseCase] = useState('');
  const [newTech, setNewTech] = useState('');
  const [newRegulatory, setNewRegulatory] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    if (document) {
      setFormData({
        ...document,
        stakeholders: document.stakeholders || [],
        target_users: document.target_users || [],
        use_cases: document.use_cases || [],
        primary_tech: document.primary_tech || [],
        regulatory_considerations: document.regulatory_considerations || [],
        sla_requirements: document.sla_requirements || '',
        data_residency: document.data_residency || '',
      });
    }
  }, [document]);

  const handleInputChange = (field: keyof ProductDocument, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSectionChange = (index: number, value: string) => {
    const next = [...sections];
    next[index] = { ...next[index], content: value };
    setSections(next);
  };

  const addArrayItem = (field: keyof ProductDocument, value: string) => {
    if (!value.trim()) return;
    setFormData((prev) => ({
      ...prev,
      [field]: [...((prev[field] as string[]) || []), value.trim()],
    }));
    if (field === 'stakeholders') setNewStakeholder('');
    if (field === 'target_users') setNewTargetUser('');
    if (field === 'use_cases') setNewUseCase('');
    if (field === 'primary_tech') setNewTech('');
    if (field === 'regulatory_considerations') setNewRegulatory('');
  };

  const removeArrayItem = (field: keyof ProductDocument, index: number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: ((prev[field] as string[]) || []).filter((_, i) => i !== index),
    }));
  };

  const validateForm = () => {
    const nextErrors: string[] = [];
    if (!formData.title.trim()) nextErrors.push('Title is required');
    if (!formData.product_name.trim()) nextErrors.push('Product name is required');
    if (!formData.version.trim()) nextErrors.push('Version is required');
    if (!formData.owner.trim()) nextErrors.push('Owner is required');
    setErrors(nextErrors);
    return nextErrors.length === 0;
  };

  const generateMarkdown = (): string => {
    let markdown = `---\n`;
    markdown += `product_name: ${formData.product_name}\n`;
    markdown += `version: ${formData.version}\n`;
    markdown += `status: ${formData.status}\n`;
    markdown += `owner: ${formData.owner}\n`;
    markdown += `---\n\n`;
    markdown += `# Product Definition Document: ${formData.title}\n\n`;
    sections.forEach((section) => {
      if (section.content.trim()) {
        markdown += `## ${section.title}\n${section.content}\n\n`;
      }
    });
    return markdown;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      notify('Please fix validation errors');
      return;
    }
    setIsLoading(true);
    try {
      const documentToSave: ProductDocument = {
        ...formData,
        content: generateMarkdown(),
      };
      await onSave?.(documentToSave);
      notify('Document saved successfully');
    } catch (error) {
      notify('Failed to save document');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePreview = () => {
    const markdown = generateMarkdown();
    const newWindow = window.open('', '_blank');
    if (newWindow) {
      newWindow.document.write(`<pre>${markdown.replace(/</g, '&lt;')}</pre>`);
    }
  };

  const handleDownload = () => {
    const markdown = generateMarkdown();
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const anchor = window.document.createElement('a');
    anchor.href = url;
    anchor.download = `${formData.product_name.toLowerCase().replace(/\s+/g, '-')}-${formData.version}.md`;
    window.document.body.appendChild(anchor);
    anchor.click();
    window.document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  };

  const renderArrayField = (
    label: string,
    field: keyof ProductDocument,
    newValue: string,
    setNewValue: (value: string) => void,
  ) => (
    <Box>
      <Typography variant="subtitle2" gutterBottom>{label}</Typography>
      <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
        <TextField
          size="small"
          value={newValue}
          onChange={(e) => setNewValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addArrayItem(field, newValue)}
          placeholder={`Add ${label.toLowerCase().slice(0, -1)}`}
        />
        <Button variant="outlined" size="small" onClick={() => addArrayItem(field, newValue)}>
          <AddIcon />
        </Button>
      </Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {((formData[field] as string[]) || []).map((item, index) => (
          <Chip
            key={`${String(field)}-${index}`}
            label={item}
            onDelete={() => removeArrayItem(field, index)}
            deleteIcon={<DeleteIcon />}
          />
        ))}
      </Box>
    </Box>
  );

  if (mode === 'view') {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>{formData.title}</Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Product: {formData.product_name} | Version: {formData.version} | Status: {formData.status}
        </Typography>
        <Divider sx={{ my: 2 }} />
        <pre>{generateMarkdown()}</pre>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, margin: '0 auto', p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          {mode === 'create' ? 'Create New Product Document' : 'Edit Product Document'}
        </Typography>

        {errors.length > 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {errors.map((error, index) => <div key={index}>{error}</div>)}
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12}><Typography variant="h6">Basic Information</Typography></Grid>
          <Grid item xs={12} md={6}><TextField fullWidth label="Document Title" value={formData.title} onChange={(e) => handleInputChange('title', e.target.value)} required /></Grid>
          <Grid item xs={12} md={6}><TextField fullWidth label="Product Name" value={formData.product_name} onChange={(e) => handleInputChange('product_name', e.target.value)} required /></Grid>
          <Grid item xs={12} md={4}><TextField fullWidth label="Version" value={formData.version} onChange={(e) => handleInputChange('version', e.target.value)} required /></Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select value={formData.status} label="Status" onChange={(e) => handleInputChange('status', e.target.value)}>
                <MenuItem value="Draft">Draft</MenuItem>
                <MenuItem value="Review">Review</MenuItem>
                <MenuItem value="Approved">Approved</MenuItem>
                <MenuItem value="Deprecated">Deprecated</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}><TextField fullWidth label="Owner" value={formData.owner} onChange={(e) => handleInputChange('owner', e.target.value)} required /></Grid>

          <Grid item xs={12}><Typography variant="h6">Stakeholders & Users</Typography></Grid>
          <Grid item xs={12} md={6}>{renderArrayField('Stakeholders', 'stakeholders', newStakeholder, setNewStakeholder)}</Grid>
          <Grid item xs={12} md={6}>{renderArrayField('Target Users', 'target_users', newTargetUser, setNewTargetUser)}</Grid>
          <Grid item xs={12} md={6}>{renderArrayField('Use Cases', 'use_cases', newUseCase, setNewUseCase)}</Grid>
          <Grid item xs={12} md={6}>{renderArrayField('Primary Tech', 'primary_tech', newTech, setNewTech)}</Grid>
          <Grid item xs={12}>{renderArrayField('Regulatory Considerations', 'regulatory_considerations', newRegulatory, setNewRegulatory)}</Grid>

          <Grid item xs={12}><Typography variant="h6">Requirements</Typography></Grid>
          <Grid item xs={12} md={6}><TextField fullWidth label="SLA Requirements" value={formData.sla_requirements} onChange={(e) => handleInputChange('sla_requirements', e.target.value)} multiline rows={3} /></Grid>
          <Grid item xs={12} md={6}><TextField fullWidth label="Data Residency" value={formData.data_residency} onChange={(e) => handleInputChange('data_residency', e.target.value)} /></Grid>

          <Grid item xs={12}><Typography variant="h6">Document Content</Typography></Grid>
          {sections.map((section, index) => (
            <Grid item xs={12} key={section.order}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom>{section.title}</Typography>
                <MarkdownEditor value={section.content} onChange={(value: string) => handleSectionChange(index, value)} placeholder={`Enter content for ${section.title}...`} minHeight={200} />
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ display: 'flex', gap: 2, mt: 4, justifyContent: 'flex-end' }}>
          {onCancel && <Button variant="outlined" onClick={onCancel}>Cancel</Button>}
          <Tooltip title="Preview document"><Button variant="outlined" onClick={handlePreview}><PreviewIcon />Preview</Button></Tooltip>
          <Tooltip title="Download markdown"><Button variant="outlined" onClick={handleDownload}><DownloadIcon />Download</Button></Tooltip>
          <Button variant="contained" onClick={handleSave} disabled={isLoading} startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}>
            {isLoading ? 'Saving...' : 'Save Document'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

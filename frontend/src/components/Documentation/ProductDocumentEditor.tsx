import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Grid,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
  Tooltip
} from '@mui/material';
import {
  Save as SaveIcon,
  Preview as PreviewIcon,
  Download as DownloadIcon,
  Add as AddIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

interface ProductDocument {
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
  content?: string;
}

interface DocumentSection {
  id?: string;
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
  { title: '7. Non-Functional Requirements', content: '', order: 7 },
  { title: '8. Data Model Overview', content: '', order: 8 },
  { title: '9. Integration Points', content: '', order: 9 },
  { title: '10. Security & Compliance', content: '', order: 10 },
  { title: '11. Performance Requirements', content: '', order: 11 },
  { title: '12. Open Questions', content: '', order: 12 },
  { title: '13. Appendices', content: '', order: 13 }
];

interface ProductDocumentEditorProps {
  document?: ProductDocument;
  onSave?: (document: ProductDocument) => void | Promise<void>;
  onCancel?: () => void;
  mode?: 'create' | 'edit' | 'view';
}

export const ProductDocumentEditor: React.FC<ProductDocumentEditorProps> = ({
  document: initialDocument,
  onSave,
  onCancel,
  mode = 'create'
}) => {
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
    regulatory_considerations: []
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
    if (initialDocument) {
      setFormData(initialDocument);
      if (initialDocument.content) {
        // Parsing markdown back into sections can be added later.
      }
    }
  }, [initialDocument]);

  const handleInputChange = (field: keyof ProductDocument, value: string | string[]) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSectionChange = (index: number, field: keyof DocumentSection, value: string | number) => {
    const newSections = [...sections];
    newSections[index] = { ...newSections[index], [field]: value } as DocumentSection;
    setSections(newSections);
  };

  const addArrayItem = (field: keyof ProductDocument, value: string) => {
    if (value.trim()) {
      setFormData(prev => ({
        ...prev,
        [field]: [...(prev[field] as string[]), value.trim()]
      }));

      switch (field) {
        case 'stakeholders':
          setNewStakeholder('');
          break;
        case 'target_users':
          setNewTargetUser('');
          break;
        case 'use_cases':
          setNewUseCase('');
          break;
        case 'primary_tech':
          setNewTech('');
          break;
        case 'regulatory_considerations':
          setNewRegulatory('');
          break;
      }
    }
  };

  const removeArrayItem = (field: keyof ProductDocument, index: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: (prev[field] as string[]).filter((_, i) => i !== index)
    }));
  };

  const validateForm = (): boolean => {
    const newErrors: string[] = [];

    if (!formData.title.trim()) newErrors.push('Title is required');
    if (!formData.product_name.trim()) newErrors.push('Product name is required');
    if (!formData.version.trim()) newErrors.push('Version is required');
    if (!formData.owner.trim()) newErrors.push('Owner is required');

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const generateMarkdown = (): string => {
    let markdown = `---\n`;
    markdown += `product_name: ${formData.product_name}\n`;
    markdown += `version: ${formData.version}\n`;
    markdown += `status: ${formData.status}\n`;
    markdown += `last_updated: ${new Date().toISOString().split('T')[0]}\n`;
    markdown += `owner: ${formData.owner}\n`;

    const writeArray = (key: string, values: string[]) => {
      if (values.length > 0) {
        markdown += `${key}:\n`;
        values.forEach(value => {
          markdown += `  - ${value}\n`;
        });
      }
    };

    writeArray('stakeholders', formData.stakeholders);
    writeArray('target_users', formData.target_users);
    writeArray('use_cases', formData.use_cases);
    writeArray('primary_tech', formData.primary_tech);

    if (formData.sla_requirements) {
      markdown += `sla_requirements: ${formData.sla_requirements}\n`;
    }

    if (formData.data_residency) {
      markdown += `data_residency: ${formData.data_residency}\n`;
    }

    writeArray('regulatory_considerations', formData.regulatory_considerations);

    markdown += `---\n\n`;
    markdown += `# Product Definition Document: ${formData.title}\n\n`;

    sections.forEach(section => {
      if (section.content.trim()) {
        markdown += `## ${section.title}\n${section.content}\n\n`;
      }
    });

    return markdown;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      const markdownContent = generateMarkdown();
      const documentToSave: ProductDocument = {
        ...formData,
        content: markdownContent
      };

      if (onSave) {
        await onSave(documentToSave);
      }

      setErrors([]);
    } catch {
      setErrors(['Failed to save document']);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePreview = () => {
    const markdown = generateMarkdown();
    const previewWindow = window.open('', '_blank');
    if (previewWindow) {
      previewWindow.document.write(`
        <html>
          <head>
            <title>${formData.title} - Preview</title>
            <style>
              body { margin: 20px; font-family: sans-serif; }
              .markdown-body { max-width: 800px; margin: 0 auto; white-space: pre-wrap; }
            </style>
          </head>
          <body>
            <div class="markdown-body">${markdown}</div>
          </body>
        </html>
      `);
      previewWindow.document.close();
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

  const renderArrayEditor = (
    label: string,
    field: keyof ProductDocument,
    currentValue: string,
    setCurrentValue: (value: string) => void
  ) => (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        {label}
      </Typography>
      <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
        <TextField
          size="small"
          value={currentValue}
          onChange={(e) => setCurrentValue(e.target.value)}
          placeholder={`Add ${label.toLowerCase().slice(0, -1)}`}
          onKeyDown={(e) => e.key === 'Enter' && addArrayItem(field, currentValue)}
        />
        <Button variant="outlined" size="small" onClick={() => addArrayItem(field, currentValue)}>
          <AddIcon />
        </Button>
      </Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {(formData[field] as string[]).map((item, index) => (
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
        <Typography variant="h4" gutterBottom>
          {formData.title}
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Product: {formData.product_name} | Version: {formData.version} | Status: {formData.status}
        </Typography>
        <Divider sx={{ my: 2 }} />
        <Box component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
          {generateMarkdown()}
        </Box>
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
            {errors.map((error, index) => (
              <div key={index}>{error}</div>
            ))}
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField fullWidth label="Document Title" value={formData.title} onChange={(e) => handleInputChange('title', e.target.value)} required />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField fullWidth label="Product Name" value={formData.product_name} onChange={(e) => handleInputChange('product_name', e.target.value)} required />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField fullWidth label="Version" value={formData.version} onChange={(e) => handleInputChange('version', e.target.value)} required />
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select value={formData.status} onChange={(e) => handleInputChange('status', e.target.value)} label="Status">
                <MenuItem value="Draft">Draft</MenuItem>
                <MenuItem value="Review">Review</MenuItem>
                <MenuItem value="Approved">Approved</MenuItem>
                <MenuItem value="Deprecated">Deprecated</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField fullWidth label="Owner" value={formData.owner} onChange={(e) => handleInputChange('owner', e.target.value)} required />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Stakeholders & Users
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>{renderArrayEditor('Stakeholders', 'stakeholders', newStakeholder, setNewStakeholder)}</Grid>
          <Grid item xs={12} md={6}>{renderArrayEditor('Target Users', 'target_users', newTargetUser, setNewTargetUser)}</Grid>
          <Grid item xs={12} md={6}>{renderArrayEditor('Use Cases', 'use_cases', newUseCase, setNewUseCase)}</Grid>
          <Grid item xs={12} md={6}>{renderArrayEditor('Primary Tech', 'primary_tech', newTech, setNewTech)}</Grid>
          <Grid item xs={12} md={6}>{renderArrayEditor('Regulatory Considerations', 'regulatory_considerations', newRegulatory, setNewRegulatory)}</Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Requirements
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField fullWidth label="SLA Requirements" value={formData.sla_requirements} onChange={(e) => handleInputChange('sla_requirements', e.target.value)} multiline rows={3} />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField fullWidth label="Data Residency" value={formData.data_residency} onChange={(e) => handleInputChange('data_residency', e.target.value)} />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Document Content
            </Typography>
          </Grid>

          {sections.map((section, index) => (
            <Grid item xs={12} key={section.order}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  {section.title}
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  minRows={8}
                  value={section.content}
                  onChange={(e) => handleSectionChange(index, 'content', e.target.value)}
                  placeholder={`Enter content for ${section.title}...`}
                />
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ display: 'flex', gap: 2, mt: 4, justifyContent: 'flex-end' }}>
          {onCancel && <Button variant="outlined" onClick={onCancel}>Cancel</Button>}

          <Tooltip title="Preview document">
            <Button variant="outlined" onClick={handlePreview} startIcon={<PreviewIcon />}>
              Preview
            </Button>
          </Tooltip>

          <Tooltip title="Download markdown">
            <Button variant="outlined" onClick={handleDownload} startIcon={<DownloadIcon />}>
              Download
            </Button>
          </Tooltip>

          <Button variant="contained" onClick={handleSave} disabled={isLoading} startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}>
            {isLoading ? 'Saving...' : 'Save Document'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

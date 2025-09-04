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
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Save as SaveIcon,
  Preview as PreviewIcon,
  Download as DownloadIcon,
  Validate as ValidateIcon,
  Add as AddIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { MarkdownEditor } from '../Common/MarkdownEditor';
import { useSnackbar } from 'notistack';

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

const DEFAULT_SECTIONS = [
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
  onSave?: (document: ProductDocument) => void;
  onCancel?: () => void;
  mode?: 'create' | 'edit' | 'view';
}

export const ProductDocumentEditor: React.FC<ProductDocumentEditorProps> = ({
  document,
  onSave,
  onCancel,
  mode = 'create'
}) => {
  const { enqueueSnackbar } = useSnackbar();
  
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
    if (document) {
      setFormData(document);
      if (document.content) {
        // Parse content into sections if available
        // This would need to be implemented based on your markdown parsing logic
      }
    }
  }, [document]);

  const handleInputChange = (field: keyof ProductDocument, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSectionChange = (index: number, field: keyof DocumentSection, value: any) => {
    const newSections = [...sections];
    newSections[index] = { ...newSections[index], [field]: value };
    setSections(newSections);
  };

  const addArrayItem = (field: keyof ProductDocument, value: string) => {
    if (value.trim()) {
      setFormData(prev => ({
        ...prev,
        [field]: [...(prev[field] as string[]), value.trim()]
      }));
      // Clear the input field
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
    
    if (formData.stakeholders.length > 0) {
      markdown += `stakeholders:\n`;
      formData.stakeholders.forEach(stakeholder => {
        markdown += `  - ${stakeholder}\n`;
      });
    }
    
    if (formData.target_users.length > 0) {
      markdown += `target_users:\n`;
      formData.target_users.forEach(user => {
        markdown += `  - ${user}\n`;
      });
    }
    
    if (formData.use_cases.length > 0) {
      markdown += `use_cases:\n`;
      formData.use_cases.forEach(useCase => {
        markdown += `  - ${useCase}\n`;
      });
    }
    
    if (formData.primary_tech.length > 0) {
      markdown += `primary_tech:\n`;
      formData.primary_tech.forEach(tech => {
        markdown += `  - ${tech}\n`;
      });
    }
    
    if (formData.sla_requirements) {
      markdown += `sla_requirements: ${formData.sla_requirements}\n`;
    }
    
    if (formData.data_residency) {
      markdown += `data_residency: ${formData.data_residency}\n`;
    }
    
    if (formData.regulatory_considerations.length > 0) {
      markdown += `regulatory_considerations:\n`;
      formData.regulatory_considerations.forEach(reg => {
        markdown += `  - ${reg}\n`;
      });
    }
    
    markdown += `---\n\n`;
    markdown += `# Product Definition Document: ${formData.title}\n\n`;
    
    // Add sections
    sections.forEach(section => {
      if (section.content.trim()) {
        markdown += `## ${section.title}\n${section.content}\n\n`;
      }
    });
    
    return markdown;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      enqueueSnackbar('Please fix validation errors', { variant: 'error' });
      return;
    }

    setIsLoading(true);
    try {
      const markdownContent = generateMarkdown();
      const documentToSave = {
        ...formData,
        content: markdownContent
      };
      
      if (onSave) {
        await onSave(documentToSave);
      }
      
      enqueueSnackbar('Document saved successfully', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Failed to save document', { variant: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePreview = () => {
    const markdown = generateMarkdown();
    // Open in new window or modal for preview
    const newWindow = window.open('', '_blank');
    if (newWindow) {
      newWindow.document.write(`
        <html>
          <head>
            <title>${formData.title} - Preview</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5.2.0/github-markdown.min.css">
            <style>
              body { margin: 20px; }
              .markdown-body { max-width: 800px; margin: 0 auto; }
            </style>
          </head>
          <body>
            <div class="markdown-body">
              ${markdown}
            </div>
          </body>
        </html>
      `);
    }
  };

  const handleDownload = () => {
    const markdown = generateMarkdown();
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${formData.product_name.toLowerCase().replace(' ', '-')}-${formData.version}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (mode === 'view') {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          {formData.title}
        </Typography>
        <Typography variant="body1" color="textSecondary" gutterBottom>
          Product: {formData.product_name} | Version: {formData.version} | Status: {formData.status}
        </Typography>
        <Divider sx={{ my: 2 }} />
        <div className="markdown-body">
          {generateMarkdown()}
        </div>
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
          {/* Basic Information */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Document Title"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              required
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Product Name"
              value={formData.product_name}
              onChange={(e) => handleInputChange('product_name', e.target.value)}
              required
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Version"
              value={formData.version}
              onChange={(e) => handleInputChange('version', e.target.value)}
              required
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                onChange={(e) => handleInputChange('status', e.target.value)}
                label="Status"
              >
                <MenuItem value="Draft">Draft</MenuItem>
                <MenuItem value="Review">Review</MenuItem>
                <MenuItem value="Approved">Approved</MenuItem>
                <MenuItem value="Deprecated">Deprecated</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Owner"
              value={formData.owner}
              onChange={(e) => handleInputChange('owner', e.target.value)}
              required
            />
          </Grid>

          {/* Arrays */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Stakeholders & Users
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Stakeholders
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                <TextField
                  size="small"
                  value={newStakeholder}
                  onChange={(e) => setNewStakeholder(e.target.value)}
                  placeholder="Add stakeholder"
                  onKeyPress={(e) => e.key === 'Enter' && addArrayItem('stakeholders', newStakeholder)}
                />
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => addArrayItem('stakeholders', newStakeholder)}
                >
                  <AddIcon />
                </Button>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {formData.stakeholders.map((stakeholder, index) => (
                  <Chip
                    key={index}
                    label={stakeholder}
                    onDelete={() => removeArrayItem('stakeholders', index)}
                    deleteIcon={<DeleteIcon />}
                  />
                ))}
              </Box>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Target Users
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                <TextField
                  size="small"
                  value={newTargetUser}
                  onChange={(e) => setNewTargetUser(e.target.value)}
                  placeholder="Add target user"
                  onKeyPress={(e) => e.key === 'Enter' && addArrayItem('target_users', newTargetUser)}
                />
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => addArrayItem('target_users', newTargetUser)}
                >
                  <AddIcon />
                </Button>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {formData.target_users.map((user, index) => (
                  <Chip
                    key={index}
                    label={user}
                    onDelete={() => removeArrayItem('target_users', index)}
                    deleteIcon={<DeleteIcon />}
                  />
                ))}
              </Box>
            </Box>
          </Grid>

          {/* Requirements */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Requirements
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="SLA Requirements"
              value={formData.sla_requirements}
              onChange={(e) => handleInputChange('sla_requirements', e.target.value)}
              multiline
              rows={3}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Data Residency"
              value={formData.data_residency}
              onChange={(e) => handleInputChange('data_residency', e.target.value)}
            />
          </Grid>

          {/* Document Sections */}
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
                <MarkdownEditor
                  value={section.content}
                  onChange={(value) => handleSectionChange(index, 'content', value)}
                  placeholder={`Enter content for ${section.title}...`}
                  minHeight={200}
                />
              </Paper>
            </Grid>
          ))}
        </Grid>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, mt: 4, justifyContent: 'flex-end' }}>
          {onCancel && (
            <Button variant="outlined" onClick={onCancel}>
              Cancel
            </Button>
          )}
          
          <Tooltip title="Preview document">
            <Button variant="outlined" onClick={handlePreview}>
              <PreviewIcon />
              Preview
            </Button>
          </Tooltip>
          
          <Tooltip title="Download markdown">
            <Button variant="outlined" onClick={handleDownload}>
              <DownloadIcon />
              Download
            </Button>
          </Tooltip>
          
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={isLoading}
            startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            {isLoading ? 'Saving...' : 'Save Document'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};


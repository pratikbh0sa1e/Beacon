import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Upload, File, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { documentAPI, institutionAPI } from '../../services/api';
import { PageHeader } from '../../components/common/PageHeader';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Card, CardContent } from '../../components/ui/card';
import { Switch } from '../../components/ui/switch';
import { DOCUMENT_CATEGORIES, VISIBILITY_OPTIONS, DEPARTMENTS } from '../../constants/categories';
import { toast } from 'sonner';

export const DocumentUploadPage = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    department: '',
    category: '',
    year: new Date().getFullYear().toString(),
    version: '1.0',
    visibility: 'Public',
    institution: '',
    downloadAllowed: true,
    approvalRequired: false,
  });

  useEffect(() => {
    fetchInstitutions();
  }, []);

  const fetchInstitutions = async () => {
    try {
      const response = await institutionAPI.listInstitutions();
      setInstitutions(response.data);
    } catch (error) {
      console.error('Error fetching institutions:', error);
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.size > 50 * 1024 * 1024) {
        toast.error('File size must be less than 50MB');
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (droppedFile.size > 50 * 1024 * 1024) {
        toast.error('File size must be less than 50MB');
        return;
      }
      setFile(droppedFile);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      toast.error('Please select a file to upload');
      return;
    }

    setLoading(true);
    try {
      const uploadFormData = new FormData();
      uploadFormData.append('file', file);
      Object.keys(formData).forEach((key) => {
        uploadFormData.append(key, formData[key]);
      });

      await documentAPI.uploadDocument(uploadFormData);
      toast.success('Document uploaded successfully!');
      navigate('/documents');
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="Upload Document"
        description="Add a new document to the system with metadata"
        icon={Upload}
      />

      <form onSubmit={handleSubmit}>
        <div className="space-y-6">
          <Card className="glass-card border-border/50">
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-4">File Upload</h3>
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
              >
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  onChange={handleFileChange}
                  accept=".pdf,.doc,.docx,.txt"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  {file ? (
                    <div className="flex items-center justify-center gap-3">
                      <File className="h-8 w-8 text-primary" />
                      <div>
                        <p className="font-medium">{file.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.preventDefault();
                          setFile(null);
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    <div>
                      <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <p className="text-base font-medium mb-2">Drop your file here or click to browse</p>
                      <p className="text-sm text-muted-foreground">Supports PDF, DOC, DOCX, TXT (Max 50MB)</p>
                    </div>
                  )}
                </label>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card border-border/50">
            <CardContent className="p-6 space-y-6">
              <h3 className="text-lg font-semibold">Document Metadata</h3>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="title">Title *</Label>
                  <Input
                    id="title"
                    placeholder="Document title"
                    value={formData.title}
                    onChange={(e) => handleChange('title', e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Category *</Label>
                  <Select value={formData.category} onValueChange={(v) => handleChange('category', v)} required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {DOCUMENT_CATEGORIES.map((cat) => (
                        <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Brief description of the document"
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  rows={3}
                />
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="department">Department</Label>
                  <Select value={formData.department} onValueChange={(v) => handleChange('department', v)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select department" />
                    </SelectTrigger>
                    <SelectContent>
                      {DEPARTMENTS.map((dept) => (
                        <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="year">Year</Label>
                  <Input
                    id="year"
                    type="number"
                    value={formData.year}
                    onChange={(e) => handleChange('year', e.target.value)}
                    min="2000"
                    max="2100"
                  />
                </div>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="version">Version</Label>
                  <Input
                    id="version"
                    placeholder="1.0"
                    value={formData.version}
                    onChange={(e) => handleChange('version', e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="visibility">Visibility</Label>
                  <Select value={formData.visibility} onValueChange={(v) => handleChange('visibility', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {VISIBILITY_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {formData.visibility !== 'Public' && (
                <div className="space-y-2">
                  <Label htmlFor="institution">Institution</Label>
                  <Select value={formData.institution} onValueChange={(v) => handleChange('institution', v)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select institution" />
                    </SelectTrigger>
                    <SelectContent>
                      {institutions.map((inst) => (
                        <SelectItem key={inst.id} value={inst.id}>{inst.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="glass-card border-border/50">
            <CardContent className="p-6 space-y-4">
              <h3 className="text-lg font-semibold">Access Control</h3>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Allow Downloads</Label>
                  <p className="text-sm text-muted-foreground">Users can download this document</p>
                </div>
                <Switch
                  checked={formData.downloadAllowed}
                  onCheckedChange={(v) => handleChange('downloadAllowed', v)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Require Approval</Label>
                  <p className="text-sm text-muted-foreground">Document needs admin approval before publishing</p>
                </div>
                <Switch
                  checked={formData.approvalRequired}
                  onCheckedChange={(v) => handleChange('approvalRequired', v)}
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-4">
            <Button type="submit" className="flex-1 neon-glow" disabled={loading}>
              {loading ? 'Uploading...' : 'Upload Document'}
            </Button>
            <Button type="button" variant="outline" onClick={() => navigate('/documents')}>
              Cancel
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
};

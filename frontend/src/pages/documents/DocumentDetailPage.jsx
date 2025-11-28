import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Download, Eye, FileText, Calendar, Building2, Shield } from 'lucide-react';
import { documentAPI } from '../../services/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Separator } from '../../components/ui/separator';
import { formatDateTime } from '../../utils/dateFormat';
import { toast } from 'sonner';

export const DocumentDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchDocument();
    }
  }, [id]);

  const fetchDocument = async () => {
    try {
      const response = await documentAPI.getDocument(id);
      setDocument(response.data);
    } catch (error) {
      console.error('Error fetching document:', error);
      toast.error('Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await documentAPI.downloadDocument(id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', document.title);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Document downloaded successfully');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download document');
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading document..." />;
  }

  if (!document) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Document not found</p>
        <Button onClick={() => navigate('/documents')} className="mt-4">
          Back to Documents
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => navigate('/documents')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{document.title}</h1>
          <div className="flex items-center gap-2 mt-2">
            <Badge>{document.category}</Badge>
            <Badge variant="outline">{document.visibility}</Badge>
          </div>
        </div>
        <Button onClick={handleDownload} className="neon-glow">
          <Download className="h-4 w-4 mr-2" />
          Download
        </Button>
      </div>

      <Card className="glass-card border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Document Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <h3 className="font-semibold mb-2">Description</h3>
            <p className="text-muted-foreground">{document.description || 'No description available'}</p>
          </div>

          <Separator />

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Building2 className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Department</p>
                  <p className="font-medium">{document.department}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Year</p>
                  <p className="font-medium">{document.year}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Version</p>
                  <p className="font-medium">{document.version}</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Visibility</p>
                  <p className="font-medium">{document.visibility}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Eye className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Download Allowed</p>
                  <p className="font-medium">{document.download_allowed ? 'Yes' : 'No'}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Last Updated</p>
                  <p className="font-medium">{formatDateTime(document.updated_at)}</p>
                </div>
              </div>
            </div>
          </div>

          {document.institution && (
            <>
              <Separator />
              <div>
                <p className="text-sm text-muted-foreground mb-1">Institution</p>
                <p className="font-medium">{document.institution.name}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="glass-card border-border/50">
        <CardHeader>
          <CardTitle>Document Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="aspect-[4/3] bg-muted/50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <FileText className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">Document preview not available</p>
              <p className="text-sm text-muted-foreground mt-2">Download to view the full document</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

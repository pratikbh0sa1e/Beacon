import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, Grid3x3, List, Download, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { documentAPI } from '../../services/api';
import { PageHeader } from '../../components/common/PageHeader';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { formatDate } from '../../utils/dateFormat';
import { DOCUMENT_CATEGORIES } from '../../constants/categories';
import { toast } from 'sonner';

export const DocumentExplorerPage = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');

  useEffect(() => {
    fetchDocuments();
  }, [categoryFilter]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const params = categoryFilter !== 'all' ? { category: categoryFilter } : {};
      const response = await documentAPI.listDocuments(params);
      setDocuments(response.data?.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const filteredDocuments = documents.filter((doc) =>
    doc.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDownload = async (docId, title) => {
    try {
      const response = await documentAPI.downloadDocument(docId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', title);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Document downloaded successfully');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download document');
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Document Explorer"
        description="Browse, search, and access your document library"
        icon={Grid3x3}
        action={
          <Button onClick={() => navigate('/upload')} className="neon-glow">
            Upload Document
          </Button>
        }
      />

      <Card className="glass-card border-border/50">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search documents..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full sm:w-48">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {DOCUMENT_CATEGORIES.map((cat) => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex gap-2">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                size="icon"
                onClick={() => setViewMode('grid')}
              >
                <Grid3x3 className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="icon"
                onClick={() => setViewMode('list')}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <LoadingSpinner text="Loading documents..." />
      ) : filteredDocuments.length === 0 ? (
        <EmptyState
          title="No documents found"
          description="No documents match your search criteria. Try adjusting your filters or upload a new document."
          action={() => navigate('/upload')}
          actionLabel="Upload Document"
        />
      ) : (
        <div className={viewMode === 'grid' ? 'grid gap-6 md:grid-cols-2 lg:grid-cols-3' : 'space-y-4'}>
          {filteredDocuments.map((doc, index) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className="glass-card border-border/50 hover:border-primary/50 h-full flex flex-col">
                <CardContent className="p-6 flex flex-col flex-1">
                  <div className="flex items-start justify-between mb-4">
                    <Badge variant="outline">{doc.category}</Badge>
                    <Badge variant={doc.visibility === 'Public' ? 'default' : 'secondary'}>
                      {doc.visibility}
                    </Badge>
                  </div>
                  <h3 className="font-semibold text-lg mb-2 line-clamp-2">{doc.title}</h3>
                  <p className="text-sm text-muted-foreground mb-4 line-clamp-3 flex-1">
                    {doc.description || 'No description available'}
                  </p>
                  <div className="space-y-2 text-xs text-muted-foreground mb-4">
                    <p>Department: {doc.department}</p>
                    <p>Year: {doc.year}</p>
                    <p>Updated: {formatDate(doc.updated_at)}</p>
                  </div>
                  <div className="flex gap-2 mt-auto">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => navigate(`/documents/${doc.id}`)}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleDownload(doc.id, doc.title)}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

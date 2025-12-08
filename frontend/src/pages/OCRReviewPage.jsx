/**
 * OCR Review Page
 * Shows all documents that need OCR review
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Loader2, FileSearch, AlertCircle, Search, Filter } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/services/api';
import OCRReviewModal from '@/components/ocr/OCRReviewModal';
import TableViewer from '@/components/ocr/TableViewer';

const OCRReviewPage = () => {
    const [loading, setLoading] = useState(true);
    const [documents, setDocuments] = useState([]);
    const [filteredDocs, setFilteredDocs] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedDoc, setSelectedDoc] = useState(null);
    const [showReviewModal, setShowReviewModal] = useState(false);
    const [showTableViewer, setShowTableViewer] = useState(false);
    const [stats, setStats] = useState(null);

    useEffect(() => {
        fetchPendingReviews();
        fetchStats();
    }, []);

    useEffect(() => {
        // Filter documents based on search query
        if (searchQuery.trim()) {
            const filtered = documents.filter(doc =>
                doc.document_filename.toLowerCase().includes(searchQuery.toLowerCase())
            );
            setFilteredDocs(filtered);
        } else {
            setFilteredDocs(documents);
        }
    }, [searchQuery, documents]);

    const fetchPendingReviews = async () => {
        try {
            setLoading(true);
            const response = await api.get('/ocr/pending-review');
            setDocuments(response.data);
            setFilteredDocs(response.data);
        } catch (error) {
            console.error('Failed to fetch pending reviews:', error);
            toast.error('Failed to load pending reviews');
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const response = await api.get('/ocr/stats');
            setStats(response.data);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    const handleReviewClick = (doc) => {
        setSelectedDoc(doc);
        setShowReviewModal(true);
    };

    const handleViewTables = (doc) => {
        setSelectedDoc(doc);
        setShowTableViewer(true);
    };

    const handleReviewComplete = () => {
        fetchPendingReviews();
        fetchStats();
    };

    const getConfidenceColor = (confidence) => {
        if (confidence >= 0.9) return 'text-green-600';
        if (confidence >= 0.8) return 'text-yellow-600';
        return 'text-red-600';
    };

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">OCR Review Queue</h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Review and correct OCR extractions that need attention
                </p>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-gray-600">Total OCR Documents</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-2xl font-bold">{stats.total_ocr_documents}</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-gray-600">Needs Review</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-2xl font-bold text-orange-600">{stats.needs_review}</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-gray-600">Avg Confidence</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-2xl font-bold">{stats.average_confidence}%</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-gray-600">Completion Rate</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-2xl font-bold text-green-600">{stats.review_completion_rate}%</p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Search and Filter */}
            <Card className="mb-6">
                <CardContent className="pt-6">
                    <div className="flex items-center gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                            <Input
                                placeholder="Search documents..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10"
                            />
                        </div>
                        <Button variant="outline">
                            <Filter className="w-4 h-4 mr-2" />
                            Filter
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Documents List */}
            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
            ) : filteredDocs.length > 0 ? (
                <div className="space-y-4">
                    {filteredDocs.map((doc) => (
                        <Card key={doc.id} className="hover:shadow-lg transition-shadow">
                            <CardContent className="pt-6">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <FileSearch className="w-5 h-5 text-gray-400" />
                                            <h3 className="font-semibold text-lg">{doc.document_filename}</h3>
                                        </div>

                                        <div className="flex items-center gap-4 mb-3">
                                            <div className="flex items-center gap-2">
                                                <span className="text-sm text-gray-600">Confidence:</span>
                                                <span className={`font-semibold ${getConfidenceColor(doc.confidence_score)}`}>
                                                    {Math.round((doc.confidence_score || 0) * 100)}%
                                                </span>
                                            </div>

                                            <div className="flex items-center gap-2">
                                                <span className="text-sm text-gray-600">Language:</span>
                                                <Badge variant="outline" className="capitalize">
                                                    {doc.language_detected || 'Unknown'}
                                                </Badge>
                                            </div>

                                            {doc.pages_with_ocr && doc.pages_with_ocr.length > 0 && (
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm text-gray-600">OCR Pages:</span>
                                                    <Badge variant="secondary">
                                                        {doc.pages_with_ocr.length}
                                                    </Badge>
                                                </div>
                                            )}
                                        </div>

                                        {doc.issues && doc.issues.length > 0 && (
                                            <div className="flex items-start gap-2 mb-3">
                                                <AlertCircle className="w-4 h-4 text-orange-500 mt-0.5" />
                                                <div className="flex-1">
                                                    <p className="text-sm font-medium text-orange-700 dark:text-orange-400 mb-1">
                                                        Issues Detected:
                                                    </p>
                                                    <ul className="text-sm text-gray-600 dark:text-gray-400 list-disc list-inside">
                                                        {doc.issues.map((issue, idx) => (
                                                            <li key={idx}>{issue}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex flex-col gap-2">
                                        <Button onClick={() => handleReviewClick(doc)}>
                                            Review & Correct
                                        </Button>
                                        {doc.pages_with_ocr && doc.pages_with_ocr.length > 0 && (
                                            <Button variant="outline" size="sm">
                                                View Details
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card>
                    <CardContent className="py-12">
                        <div className="text-center">
                            <FileSearch className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No Documents Need Review</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                {searchQuery ? 'No documents match your search' : 'All OCR extractions have been reviewed'}
                            </p>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Modals */}
            {selectedDoc && (
                <>
                    <OCRReviewModal
                        isOpen={showReviewModal}
                        onClose={() => {
                            setShowReviewModal(false);
                            setSelectedDoc(null);
                        }}
                        documentId={selectedDoc.document_id}
                        onReviewComplete={handleReviewComplete}
                    />

                    <TableViewer
                        isOpen={showTableViewer}
                        onClose={() => {
                            setShowTableViewer(false);
                            setSelectedDoc(null);
                        }}
                        documentId={selectedDoc.document_id}
                        documentName={selectedDoc.document_filename}
                    />
                </>
            )}
        </div>
    );
};

export default OCRReviewPage;

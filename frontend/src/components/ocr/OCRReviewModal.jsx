/**
 * OCR Review Modal
 * Allows users to review and correct OCR extracted text
 */

import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, CheckCircle, RotateCw } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/services/api';

const OCRReviewModal = ({ isOpen, onClose, documentId, onReviewComplete }) => {
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [reprocessing, setReprocessing] = useState(false);
    const [ocrData, setOcrData] = useState(null);
    const [correctedText, setCorrectedText] = useState('');
    const [notes, setNotes] = useState('');

    useEffect(() => {
        if (isOpen && documentId) {
            fetchOCRData();
        }
    }, [isOpen, documentId]);

    const fetchOCRData = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/ocr/document/${documentId}`);
            setOcrData(response.data);
            setCorrectedText(response.data.processed_result || '');
        } catch (error) {
            console.error('Failed to fetch OCR data:', error);
            toast.error('Failed to load OCR data');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmitReview = async () => {
        try {
            setSubmitting(true);
            await api.post(`/ocr/review/${ocrData.id}`, {
                corrected_text: correctedText,
                notes: notes || undefined
            });

            toast.success('OCR review submitted successfully');
            onReviewComplete?.();
            onClose();
        } catch (error) {
            console.error('Failed to submit review:', error);
            toast.error('Failed to submit review');
        } finally {
            setSubmitting(false);
        }
    };

    const handleReprocess = async (level) => {
        try {
            setReprocessing(true);
            await api.post(`/ocr/reprocess/${documentId}`, {
                preprocessing_level: level
            });

            toast.success('Document reprocessed successfully');
            await fetchOCRData(); // Reload data
        } catch (error) {
            console.error('Failed to reprocess:', error);
            toast.error('Failed to reprocess document');
        } finally {
            setReprocessing(false);
        }
    };

    if (!isOpen) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Review OCR Extraction</DialogTitle>
                    <DialogDescription>
                        Review and correct the extracted text from the scanned document
                    </DialogDescription>
                </DialogHeader>

                {loading ? (
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                ) : ocrData ? (
                    <div className="space-y-4">
                        {/* OCR Metadata */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                            <div>
                                <p className="text-xs text-gray-500">Confidence</p>
                                <p className="text-lg font-semibold">
                                    {Math.round((ocrData.confidence_score || 0) * 100)}%
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Language</p>
                                <p className="text-lg font-semibold capitalize">
                                    {ocrData.language_detected || 'Unknown'}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Quality Score</p>
                                <p className="text-lg font-semibold">
                                    {Math.round((ocrData.quality_score || 0) * 100)}%
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Engine</p>
                                <p className="text-lg font-semibold uppercase">
                                    {ocrData.engine_used}
                                </p>
                            </div>
                        </div>

                        {/* Issues Alert */}
                        {ocrData.issues && ocrData.issues.length > 0 && (
                            <Alert>
                                <AlertCircle className="h-4 w-4" />
                                <AlertDescription>
                                    <p className="font-semibold mb-1">Issues Detected:</p>
                                    <ul className="list-disc list-inside text-sm">
                                        {ocrData.issues.map((issue, idx) => (
                                            <li key={idx}>{issue}</li>
                                        ))}
                                    </ul>
                                </AlertDescription>
                            </Alert>
                        )}

                        {/* Reprocess Options */}
                        <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm text-gray-600">Try reprocessing with:</span>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleReprocess('light')}
                                disabled={reprocessing}
                            >
                                {reprocessing ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <RotateCw className="w-3 h-3 mr-1" />}
                                Light
                            </Button>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleReprocess('medium')}
                                disabled={reprocessing}
                            >
                                {reprocessing ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <RotateCw className="w-3 h-3 mr-1" />}
                                Medium
                            </Button>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleReprocess('heavy')}
                                disabled={reprocessing}
                            >
                                {reprocessing ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <RotateCw className="w-3 h-3 mr-1" />}
                                Heavy
                            </Button>
                        </div>

                        {/* Extracted Text Editor */}
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Extracted Text (Edit to correct)
                            </label>
                            <Textarea
                                value={correctedText}
                                onChange={(e) => setCorrectedText(e.target.value)}
                                rows={15}
                                className="font-mono text-sm"
                                placeholder="Extracted text will appear here..."
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                {correctedText.length} characters
                            </p>
                        </div>

                        {/* Notes */}
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Review Notes (Optional)
                            </label>
                            <Textarea
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                rows={3}
                                placeholder="Add any notes about the corrections made..."
                            />
                        </div>
                    </div>
                ) : (
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                            Failed to load OCR data. Please try again.
                        </AlertDescription>
                    </Alert>
                )}

                <DialogFooter>
                    <Button variant="outline" onClick={onClose} disabled={submitting}>
                        Cancel
                    </Button>
                    <Button onClick={handleSubmitReview} disabled={submitting || loading}>
                        {submitting ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Submitting...
                            </>
                        ) : (
                            <>
                                <CheckCircle className="w-4 h-4 mr-2" />
                                Submit Review
                            </>
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default OCRReviewModal;

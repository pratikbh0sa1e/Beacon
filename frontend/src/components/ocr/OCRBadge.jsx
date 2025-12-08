/**
 * OCR Badge Component
 * Shows OCR status and confidence for scanned documents
 */

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { FileSearch, AlertCircle, CheckCircle, RotateCw, Table } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

const OCRBadge = ({ document }) => {
    if (!document.is_scanned) return null;

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
            case 'needs_review':
                return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
            case 'processing':
                return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
            case 'failed':
                return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
            default:
                return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="w-3 h-3" />;
            case 'needs_review':
                return <AlertCircle className="w-3 h-3" />;
            case 'processing':
                return <RotateCw className="w-3 h-3 animate-spin" />;
            default:
                return <FileSearch className="w-3 h-3" />;
        }
    };

    const confidence = document.ocr_confidence ? Math.round(document.ocr_confidence * 100) : null;

    return (
        <div className="flex items-center gap-2 flex-wrap">
            {/* OCR Status Badge */}
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger>
                        <Badge className={`flex items-center gap-1 ${getStatusColor(document.ocr_status)}`}>
                            {getStatusIcon(document.ocr_status)}
                            <span className="text-xs">
                                {document.ocr_status === 'completed' ? 'OCR' : document.ocr_status?.replace('_', ' ')}
                            </span>
                        </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Document was scanned and processed with OCR</p>
                        {confidence && <p className="text-xs mt-1">Confidence: {confidence}%</p>}
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            {/* Confidence Badge */}
            {confidence && (
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger>
                            <Badge
                                variant="outline"
                                className={`text-xs ${confidence >= 90 ? 'border-green-500 text-green-700' :
                                        confidence >= 80 ? 'border-yellow-500 text-yellow-700' :
                                            'border-red-500 text-red-700'
                                    }`}
                            >
                                {confidence}%
                            </Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>OCR Confidence Score</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            )}

            {/* Rotation Badge */}
            {document.rotation_corrected && document.rotation_corrected !== 0 && (
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger>
                            <Badge variant="outline" className="flex items-center gap-1 text-xs">
                                <RotateCw className="w-3 h-3" />
                                {document.rotation_corrected}°
                            </Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Document was rotated {document.rotation_corrected}° for better OCR</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            )}

            {/* Tables Badge */}
            {document.tables_found > 0 && (
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger>
                            <Badge variant="outline" className="flex items-center gap-1 text-xs">
                                <Table className="w-3 h-3" />
                                {document.tables_found}
                            </Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>{document.tables_found} table(s) extracted</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            )}

            {/* Needs Review Badge */}
            {document.needs_ocr_review && (
                <Badge className="bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 text-xs">
                    <AlertCircle className="w-3 h-3 mr-1" />
                    Review Needed
                </Badge>
            )}
        </div>
    );
};

export default OCRBadge;

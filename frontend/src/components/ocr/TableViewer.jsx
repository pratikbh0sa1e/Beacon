/**
 * Table Viewer Component
 * Displays extracted tables from OCR
 */

import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download, Table as TableIcon } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/services/api';

const TableViewer = ({ isOpen, onClose, documentId, documentName }) => {
    const [loading, setLoading] = useState(true);
    const [tables, setTables] = useState([]);
    const [format, setFormat] = useState('json');

    useEffect(() => {
        if (isOpen && documentId) {
            fetchTables();
        }
    }, [isOpen, documentId, format]);

    const fetchTables = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/ocr/tables/${documentId}?format=${format}`);
            setTables(response.data.tables || []);
        } catch (error) {
            console.error('Failed to fetch tables:', error);
            toast.error('Failed to load tables');
        } finally {
            setLoading(false);
        }
    };

    const downloadTable = (table, tableIndex) => {
        let content = '';
        let filename = '';
        let mimeType = '';

        if (format === 'json') {
            content = JSON.stringify(table.data || table, null, 2);
            filename = `${documentName}_table_${tableIndex}.json`;
            mimeType = 'application/json';
        } else if (format === 'markdown') {
            content = table.markdown || '';
            filename = `${documentName}_table_${tableIndex}.md`;
            mimeType = 'text/markdown';
        } else if (format === 'csv') {
            content = table.csv || '';
            filename = `${documentName}_table_${tableIndex}.csv`;
            mimeType = 'text/csv';
        } else if (format === 'html') {
            content = table.html || '';
            filename = `${documentName}_table_${tableIndex}.html`;
            mimeType = 'text/html';
        }

        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        toast.success(`Table ${tableIndex} downloaded`);
    };

    const renderTable = (table, index) => {
        if (format === 'json') {
            return (
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Badge variant="outline">Table {index}</Badge>
                            {table.page && <Badge variant="secondary">Page {table.page}</Badge>}
                        </div>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => downloadTable(table, index)}
                        >
                            <Download className="w-4 h-4 mr-1" />
                            Download
                        </Button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="min-w-full border border-gray-300 dark:border-gray-700">
                            <tbody>
                                {(table.data || []).map((row, rowIdx) => (
                                    <tr key={rowIdx} className={rowIdx === 0 ? 'bg-gray-100 dark:bg-gray-800 font-semibold' : ''}>
                                        {row.map((cell, cellIdx) => (
                                            <td
                                                key={cellIdx}
                                                className="border border-gray-300 dark:border-gray-700 px-4 py-2 text-sm"
                                            >
                                                {cell}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            );
        } else if (format === 'markdown') {
            return (
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Badge variant="outline">Table {table.table_number}</Badge>
                            {table.page && <Badge variant="secondary">Page {table.page}</Badge>}
                        </div>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => downloadTable(table, table.table_number)}
                        >
                            <Download className="w-4 h-4 mr-1" />
                            Download
                        </Button>
                    </div>
                    <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm">
                        {table.markdown}
                    </pre>
                </div>
            );
        } else if (format === 'csv') {
            return (
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Badge variant="outline">Table {table.table_number}</Badge>
                            {table.page && <Badge variant="secondary">Page {table.page}</Badge>}
                        </div>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => downloadTable(table, table.table_number)}
                        >
                            <Download className="w-4 h-4 mr-1" />
                            Download
                        </Button>
                    </div>
                    <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm">
                        {table.csv}
                    </pre>
                </div>
            );
        } else if (format === 'html') {
            return (
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Badge variant="outline">Table {table.table_number}</Badge>
                            {table.page && <Badge variant="secondary">Page {table.page}</Badge>}
                        </div>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => downloadTable(table, table.table_number)}
                        >
                            <Download className="w-4 h-4 mr-1" />
                            Download
                        </Button>
                    </div>
                    <div
                        className="border border-gray-300 dark:border-gray-700 rounded-lg p-4 overflow-x-auto"
                        dangerouslySetInnerHTML={{ __html: table.html }}
                    />
                </div>
            );
        }
    };

    if (!isOpen) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <TableIcon className="w-5 h-5" />
                        Extracted Tables
                    </DialogTitle>
                    <DialogDescription>
                        Tables extracted from {documentName}
                    </DialogDescription>
                </DialogHeader>

                <Tabs value={format} onValueChange={setFormat}>
                    <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="json">Table View</TabsTrigger>
                        <TabsTrigger value="markdown">Markdown</TabsTrigger>
                        <TabsTrigger value="csv">CSV</TabsTrigger>
                        <TabsTrigger value="html">HTML</TabsTrigger>
                    </TabsList>

                    <TabsContent value={format} className="mt-4">
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                            </div>
                        ) : tables.length > 0 ? (
                            <div className="space-y-6">
                                {tables.map((table, index) => (
                                    <div key={index}>
                                        {renderTable(table, index + 1)}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8 text-gray-500">
                                No tables found in this document
                            </div>
                        )}
                    </TabsContent>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
};

export default TableViewer;

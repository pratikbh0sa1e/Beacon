import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  X,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { documentAPI, institutionAPI } from "../../services/api";
import { PageHeader } from "../../components/common/PageHeader";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Card, CardContent } from "../../components/ui/card";
import { Progress } from "../../components/ui/progress";
import {
  DOCUMENT_CATEGORIES,
  VISIBILITY_OPTIONS,
  DEPARTMENTS,
} from "../../constants/categories";
import { toast } from "sonner";

export const DocumentUploadPage = () => {
  const navigate = useNavigate();
  const [fileList, setFileList] = useState([]);
  const [institutions, setInstitutions] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  
  useEffect(() => {
    const fetchInstitutions = async () => {
      try {
        const response = await institutionAPI.list();
        setInstitutions(response.data || []); // Handle potential null data
      } catch (error) {
        console.error("Error fetching institutions:", error);
      }
    };
    
    fetchInstitutions();
  }, []);
  // --- File Handling ---

  const handleFiles = (files) => {
    if (fileList.length + files.length > 5) {
      toast.error("You can only upload up to 5 files at a time.");
      return;
    }

    const newFiles = Array.from(files).map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: "pending", // pending, uploading, success, error
      progress: 0,
      meta: {
        title: "", // Leave blank to let AI decide
        category: "Uncategorized",
        description: "",
        department: "General",
        visibility: "public", // Default visibility
        institution: "",
      },
    }));

    setFileList((prev) => [...prev, ...newFiles]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  const handleFileSelect = (e) => {
    handleFiles(e.target.files);
  };

  const removeFile = (id) => {
    setFileList((prev) => prev.filter((f) => f.id !== id));
  };

  const updateFileMeta = (id, field, value) => {
    setFileList((prev) =>
      prev.map((item) =>
        item.id === id
          ? { ...item, meta: { ...item.meta, [field]: value } }
          : item
      )
    );
  };

  // --- Upload Logic ---

  const uploadSingleFile = async (fileItem) => {
    // 1. Update status to uploading
    setFileList((prev) =>
      prev.map((f) =>
        f.id === fileItem.id ? { ...f, status: "uploading" } : f
      )
    );

    const formData = new FormData();
    formData.append("file", fileItem.file);

    // 2. Add fields ONLY if they are filled (otherwise backend defaults apply)
    const { meta } = fileItem;
    if (meta.title) formData.append("title", meta.title);
    if (meta.category) formData.append("category", meta.category);
    if (meta.department) formData.append("department", meta.department);
    if (meta.description) formData.append("description", meta.description);
    if (meta.visibility) formData.append("visibility", meta.visibility);
    if (meta.institution) formData.append("institution", meta.institution);

    try {
      // Fake progress interval for UX (Axios upload progress is tricky to hook into per-item here easily)
      const interval = setInterval(() => {
        setFileList((prev) =>
          prev.map((f) =>
            f.id === fileItem.id && f.progress < 90
              ? { ...f, progress: f.progress + 10 }
              : f
          )
        );
      }, 300);

      await documentAPI.uploadDocument(formData);

      clearInterval(interval);
      setFileList((prev) =>
        prev.map((f) =>
          f.id === fileItem.id ? { ...f, status: "success", progress: 100 } : f
        )
      );
      return true;
    } catch (error) {
      console.error(`Error uploading ${fileItem.file.name}:`, error);
      setFileList((prev) =>
        prev.map((f) =>
          f.id === fileItem.id ? { ...f, status: "error", progress: 0 } : f
        )
      );
      toast.error(`Failed to upload ${fileItem.file.name}`);
      return false;
    }
  };

  const handleUploadAll = async () => {
    if (fileList.length === 0) {
      toast.error("Please select files to upload");
      return;
    }

    setIsUploading(true);
    let successCount = 0;

    // Upload sequentially to avoid overwhelming the server
    for (const fileItem of fileList) {
      if (fileItem.status !== "success") {
        const success = await uploadSingleFile(fileItem);
        if (success) successCount++;
      }
    }

    setIsUploading(false);

    if (successCount === fileList.length) {
      toast.success("All documents uploaded successfully!");
      setTimeout(() => navigate("/documents"), 1500);
    } else {
      toast.warning(`${successCount} of ${fileList.length} uploaded.`);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-24">
      <PageHeader
        title="Upload Documents"
        description="Smart Upload: Fill in details manually or leave blank for AI auto-fill."
        icon={Upload}
      />

      {/* Drag & Drop Area */}
      <Card className="glass-card border-border/50 border-dashed border-2 hover:border-primary/50 transition-colors">
        <CardContent
          className="p-10 flex flex-col items-center justify-center cursor-pointer min-h-[200px]"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => document.getElementById("file-upload").click()}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            multiple
            onChange={handleFileSelect}
            accept=".pdf,.doc,.docx,.txt"
          />
          <div className="bg-primary/10 p-4 rounded-full mb-4">
            <Upload className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold">
            Drop files here or click to browse
          </h3>
          <p className="text-muted-foreground mt-2 text-center">
            Upload up to 5 files (Max 50MB each)
          </p>
        </CardContent>
      </Card>

      {/* File List */}
      <div className="space-y-4">
        <AnimatePresence>
          {fileList.map((item, index) => (
            <FileFormItem
              key={item.id}
              item={item}
              onRemove={() => removeFile(item.id)}
              onUpdate={updateFileMeta}
              institutions={institutions}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* Footer Actions */}
      {fileList.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur-lg border-t z-50">
          <div className="container max-w-4xl mx-auto flex items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground hidden sm:block">
              {fileList.filter((f) => f.status === "success").length} /{" "}
              {fileList.length} completed
            </p>
            <div className="flex gap-4 w-full sm:w-auto">
              <Button
                variant="outline"
                onClick={() => setFileList([])}
                disabled={isUploading}
              >
                Clear All
              </Button>
              <Button
                onClick={handleUploadAll}
                disabled={isUploading}
                className="neon-glow min-w-[150px]"
              >
                {isUploading ? "Uploading..." : "Upload All Files"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// --- Helper Component: Individual File Form ---
const FileFormItem = ({ item, onRemove, onUpdate, institutions }) => {
  const [isOpen, setIsOpen] = useState(true);

  // Status Colors
  const borderColor =
    item.status === "error"
      ? "border-destructive/50"
      : item.status === "success"
      ? "border-success/50"
      : "border-border/50";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0 }}
    >
      <Card
        className={`glass-card overflow-hidden transition-all duration-300 ${borderColor}`}
      >
        {/* Header Bar */}
        <div className="p-4 flex items-center gap-4 bg-secondary/20 select-none">
          <div className="h-10 w-10 rounded-lg bg-background flex items-center justify-center shrink-0">
            <FileText className="h-5 w-5 text-primary" />
          </div>

          <div
            className="flex-1 min-w-0 cursor-pointer"
            onClick={() => setIsOpen(!isOpen)}
          >
            <div className="flex items-center gap-2">
              <h4 className="font-medium truncate max-w-[200px] sm:max-w-md">
                {item.file.name}
              </h4>
              {item.status === "success" && (
                <CheckCircle className="h-4 w-4 text-success" />
              )}
              {item.status === "error" && (
                <AlertCircle className="h-4 w-4 text-destructive" />
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {(item.file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>

          {item.status === "uploading" && (
            <div className="w-24 shrink-0">
              <Progress value={item.progress} className="h-2" />
            </div>
          )}

          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(!isOpen)}
            >
              {isOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
            {item.status !== "uploading" && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onRemove}
                className="hover:text-destructive"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Collapsible Form */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: "auto" }}
              exit={{ height: 0 }}
            >
              <CardContent className="p-6 space-y-4 border-t border-border/50">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Title (Optional)</Label>
                    <Input
                      placeholder="Leave blank for AI to generate"
                      value={item.meta.title}
                      onChange={(e) =>
                        onUpdate(item.id, "title", e.target.value)
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Select
                      value={item.meta.category}
                      onValueChange={(v) => onUpdate(item.id, "category", v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DOCUMENT_CATEGORIES.map((cat) => (
                          <SelectItem key={cat} value={cat}>
                            {cat}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Description (Optional)</Label>
                  <Textarea
                    placeholder="Brief summary..."
                    rows={2}
                    value={item.meta.description}
                    onChange={(e) =>
                      onUpdate(item.id, "description", e.target.value)
                    }
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Department</Label>
                    <Select
                      value={item.meta.department}
                      onValueChange={(v) => onUpdate(item.id, "department", v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DEPARTMENTS.map((d) => (
                          <SelectItem key={d} value={d}>
                            {d}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Visibility</Label>
                    <Select
                      value={item.meta.visibility}
                      onValueChange={(v) => onUpdate(item.id, "visibility", v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {VISIBILITY_OPTIONS.map((v) => (
                          <SelectItem key={v.value} value={v.value}>
                            {v.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
};

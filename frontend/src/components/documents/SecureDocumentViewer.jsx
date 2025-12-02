import { useEffect } from "react";
import { FileText } from "lucide-react";

export const SecureDocumentViewer = ({ url, fileType, userName }) => {
  // Basic keyboard shortcut prevention
  useEffect(() => {
    const preventPrint = (e) => {
      // Prevent Ctrl+P (print)
      if (e.ctrlKey && e.key === "p") {
        e.preventDefault();
        return false;
      }
    };

    document.addEventListener("keydown", preventPrint);
    return () => document.removeEventListener("keydown", preventPrint);
  }, []);

  // For PDFs - use Google Docs Viewer
  if (fileType === "pdf") {
    return (
      <div
        className="relative w-full h-[600px] bg-muted/50 rounded-lg overflow-hidden"
        onContextMenu={(e) => e.preventDefault()}
      >
        {/* Watermark overlay */}
        <div className="absolute inset-0 pointer-events-none z-10 flex items-center justify-center">
          <div className="text-7xl font-bold text-black/5 dark:text-white/5 rotate-[-45deg] select-none">
            {userName || "PREVIEW"}
          </div>
        </div>

        {/* PDF Viewer */}
        <iframe
          src={`https://docs.google.com/viewer?url=${encodeURIComponent(
            url
          )}&embedded=true`}
          className="w-full h-full"
          title="Document Preview"
          style={{ border: 0 }}
        />
      </div>
    );
  }

  // For Office docs - use Google Docs Viewer
  if (["docx", "pptx", "xlsx", "doc", "ppt", "xls"].includes(fileType)) {
    return (
      <div
        className="relative w-full h-[600px] bg-muted/50 rounded-lg overflow-hidden"
        onContextMenu={(e) => e.preventDefault()}
      >
        {/* Watermark overlay */}
        <div className="absolute inset-0 pointer-events-none z-10 flex items-center justify-center">
          <div className="text-7xl font-bold text-black/5 dark:text-white/5 rotate-[-45deg] select-none">
            {userName || "PREVIEW"}
          </div>
        </div>

        {/* Office Viewer */}
        <iframe
          src={`https://docs.google.com/viewer?url=${encodeURIComponent(
            url
          )}&embedded=true`}
          className="w-full h-full"
          title="Document Preview"
          style={{ border: 0 }}
        />
      </div>
    );
  }

  // For images - show with basic protection
  if (["jpg", "jpeg", "png", "gif", "webp"].includes(fileType)) {
    return (
      <div
        className="relative w-full max-h-[600px] bg-muted/50 rounded-lg overflow-hidden"
        onContextMenu={(e) => e.preventDefault()}
      >
        {/* Watermark */}
        <div className="absolute inset-0 pointer-events-none z-10 flex items-center justify-center">
          <div className="text-7xl font-bold text-black/10 dark:text-white/10 rotate-[-45deg]">
            {userName || "PREVIEW"}
          </div>
        </div>

        {/* Image */}
        <img
          src={url}
          alt="Document"
          className="w-full h-auto object-contain"
          draggable={false}
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>
    );
  }

  // Unsupported file type
  return (
    <div className="flex flex-col items-center justify-center h-[400px] bg-muted/50 rounded-lg p-6 text-center">
      <FileText className="h-16 w-16 mb-4 text-muted-foreground/50" />
      <p className="text-muted-foreground font-medium mb-2">
        Preview not available for {fileType?.toUpperCase()} files
      </p>
      <p className="text-sm text-muted-foreground">
        {fileType === "txt"
          ? "Text files cannot be previewed. Please download to view."
          : "This file type is not supported for preview."}
      </p>
    </div>
  );
};

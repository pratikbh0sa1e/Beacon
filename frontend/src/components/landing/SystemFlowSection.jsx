// SystemFlowSection.jsx - System workflow visualization

import React from "react";
import { FlowStep } from "./FlowStep";
import {
  Upload,
  FileText,
  Cloud,
  Database,
  CheckCircle,
  MessageSquare,
  Search,
  BarChart3,
  Sparkles,
  FileCheck,
} from "lucide-react";

const uploadFlow = [
  {
    icon: Upload,
    title: "Upload Document",
    description: "Upload PDF, DOCX, PPTX, or images in any supported format",
  },
  {
    icon: FileText,
    title: "Extract Text",
    description: "OCR for scanned documents and multilingual text extraction",
  },
  {
    icon: Cloud,
    title: "Store in Cloud",
    description: "Secure storage in Supabase S3 with PostgreSQL metadata",
  },
  {
    icon: Database,
    title: "Extract Metadata",
    description: "AI-powered analysis extracts key information and categories",
  },
  {
    icon: CheckCircle,
    title: "Ready for Search",
    description: "Document indexed with lazy embedding for instant availability",
  },
];

const queryFlow = [
  {
    icon: MessageSquare,
    title: "User Question",
    description: "Ask via text or voice in 100+ languages",
  },
  {
    icon: Search,
    title: "Search Metadata",
    description: "BM25 keyword search filters relevant documents",
  },
  {
    icon: BarChart3,
    title: "Rerank Results",
    description: "Relevance scoring prioritizes best matches",
  },
  {
    icon: Database,
    title: "Embed & Search",
    description: "Vector similarity search finds semantic matches",
  },
  {
    icon: Sparkles,
    title: "Generate Answer",
    description: "AI generates response with citations and confidence scores",
  },
];

export const SystemFlowSection = () => {
  return (
    <section className="py-20 px-4 bg-secondary/30">
      <div className="container mx-auto max-w-7xl">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            How BEACON Works
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            A seamless workflow from document upload to AI-powered insights
          </p>
        </div>

        {/* Upload Flow */}
        <div className="mb-16">
          <div className="flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Upload className="h-5 w-5 text-primary-foreground" />
            </div>
            <h3 className="text-2xl font-bold">Document Upload Flow</h3>
          </div>
          <div className="space-y-4 md:space-y-0 md:flex md:items-start md:gap-4">
            {uploadFlow.map((step, index) => (
              <FlowStep
                key={step.title}
                icon={step.icon}
                title={step.title}
                description={step.description}
                index={index}
                isLast={index === uploadFlow.length - 1}
              />
            ))}
          </div>
        </div>

        {/* Query Flow */}
        <div>
          <div className="flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <MessageSquare className="h-5 w-5 text-primary-foreground" />
            </div>
            <h3 className="text-2xl font-bold">Query & Retrieval Flow</h3>
          </div>
          <div className="space-y-4 md:space-y-0 md:flex md:items-start md:gap-4">
            {queryFlow.map((step, index) => (
              <FlowStep
                key={step.title}
                icon={step.icon}
                title={step.title}
                description={step.description}
                index={index}
                isLast={index === queryFlow.length - 1}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

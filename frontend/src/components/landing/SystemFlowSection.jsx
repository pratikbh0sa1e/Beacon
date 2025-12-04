// SystemFlowSection.jsx - System workflow visualization

import React from "react";
import { motion } from "framer-motion";
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
  ArrowRight,
  ArrowDown,
  ArrowLeft,
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
    description:
      "Document indexed with lazy embedding for instant availability",
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

const FlowBlock = ({ icon: Icon, title, description, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="relative"
    >
      <div className="glass-card p-6 rounded-xl border-2 border-primary/20 hover:border-primary/50 transition-all duration-300 bg-background/95 backdrop-blur-sm shadow-lg hover:shadow-xl">
        {/* Step number badge */}
        <div className="absolute -top-3 -left-3 h-10 w-10 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg neon-glow">
          <span className="text-sm font-bold text-primary-foreground">
            {index + 1}
          </span>
        </div>

        {/* Icon */}
        <div className="flex items-center justify-center mb-4">
          <div className="h-16 w-16 rounded-lg bg-gradient-to-br from-primary/10 to-accent/10 flex items-center justify-center">
            <Icon className="h-8 w-8 text-primary" />
          </div>
        </div>

        {/* Content */}
        <h4 className="font-semibold text-base mb-2 text-center">{title}</h4>
        <p className="text-sm text-muted-foreground text-center leading-relaxed">
          {description}
        </p>
      </div>
    </motion.div>
  );
};

const FlowArrowIcon = ({ direction }) => {
  const iconProps = {
    className: "h-8 w-8 text-primary drop-shadow-lg",
    strokeWidth: 3,
  };

  if (direction === "right") return <ArrowRight {...iconProps} />;
  if (direction === "left") return <ArrowLeft {...iconProps} />;
  if (direction === "down") return <ArrowDown {...iconProps} />;
  return null;
};

const RibbonFlow = ({ steps, flowId }) => {
  return (
    <div className="relative max-w-6xl mx-auto">
      {/* Desktop: Block flow with icon arrows */}
      <div className="hidden md:block">
        <div className="space-y-12">
          {/* Row 1: Steps 1-3 (Top) */}
          <div className="grid grid-cols-[1fr_auto_1fr_auto_1fr] gap-4 items-center">
            <FlowBlock
              icon={steps[0].icon}
              title={steps[0].title}
              description={steps[0].description}
              index={0}
            />

            {/* Arrow 1 to 2 */}
            <div className="flex items-center justify-center">
              <FlowArrowIcon direction="right" />
            </div>

            <FlowBlock
              icon={steps[1].icon}
              title={steps[1].title}
              description={steps[1].description}
              index={1}
            />

            {/* Arrow 2 to 3 */}
            <div className="flex items-center justify-center">
              <FlowArrowIcon direction="right" />
            </div>

            <FlowBlock
              icon={steps[2].icon}
              title={steps[2].title}
              description={steps[2].description}
              index={2}
            />
          </div>

          {/* Arrow 3 to 4 (down) */}
          <div className="flex justify-end pr-[16.5%]">
            <FlowArrowIcon direction="down" />
          </div>

          {/* Row 2: Steps 4-5 (Bottom) - Reversed */}
          <div className="grid grid-cols-[1fr_auto_1fr_auto_1fr] gap-4 items-center">
            <div></div>
            <div></div>

            <FlowBlock
              icon={steps[4].icon}
              title={steps[4].title}
              description={steps[4].description}
              index={4}
            />

            {/* Arrow 5 to 4 (left) */}
            <div className="flex items-center justify-center">
              <FlowArrowIcon direction="left" />
            </div>

            <FlowBlock
              icon={steps[3].icon}
              title={steps[3].title}
              description={steps[3].description}
              index={3}
            />
          </div>
        </div>
      </div>

      {/* Tablet: 2 columns with vertical arrows */}
      <div className="hidden sm:grid md:hidden grid-cols-2 gap-8">
        {steps.map((step, index) => (
          <React.Fragment key={index}>
            <FlowBlock
              icon={step.icon}
              title={step.title}
              description={step.description}
              index={index}
            />
            {index < steps.length - 1 && index % 2 === 1 && (
              <div className="col-span-2 flex justify-center">
                <FlowArrowIcon direction="down" />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Mobile: Single column with vertical arrows */}
      <div className="sm:hidden space-y-6">
        {steps.map((step, index) => (
          <React.Fragment key={index}>
            <FlowBlock
              icon={step.icon}
              title={step.title}
              description={step.description}
              index={index}
            />
            {index < steps.length - 1 && (
              <div className="flex justify-center">
                <FlowArrowIcon direction="down" />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

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
        <div className="mb-20">
          <div className="flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center neon-glow">
              <Upload className="h-5 w-5 text-primary-foreground" />
            </div>
            <h3 className="text-xl sm:text-2xl font-bold">
              Document Upload Flow
            </h3>
          </div>

          <RibbonFlow steps={uploadFlow} flowId="upload" />
        </div>

        {/* Query Flow */}
        <div>
          <div className="flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center neon-glow">
              <MessageSquare className="h-5 w-5 text-primary-foreground" />
            </div>
            <h3 className="text-xl sm:text-2xl font-bold">
              Query & Retrieval Flow
            </h3>
          </div>

          <RibbonFlow steps={queryFlow} flowId="query" />
        </div>
      </div>
    </section>
  );
};

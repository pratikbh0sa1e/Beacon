// FeaturesSection.jsx - Features section with all key capabilities

import React from "react";
import { FeatureCard } from "./FeatureCard";
import {
  FileText,
  Globe,
  Mic,
  Sparkles,
  Shield,
  CheckCircle,
  Quote,
} from "lucide-react";

const features = [
  {
    icon: FileText,
    title: "Multi-Format Support",
    description:
      "Process PDF, DOCX, PPTX, and images with OCR support for scanned documents and multilingual text extraction.",
  },
  {
    icon: Globe,
    title: "Multilingual Intelligence",
    description:
      "100+ languages including Hindi, Tamil, Telugu, Bengali with cross-lingual search capabilities.",
  },
  {
    icon: Mic,
    title: "Voice Queries",
    description:
      "Ask questions via audio in 98+ languages with automatic transcription and AI-powered responses.",
  },
  {
    icon: Sparkles,
    title: "AI-Powered Search",
    description:
      "Hybrid retrieval combining semantic and keyword search with AI-generated answers and citations.",
  },
  {
    icon: Shield,
    title: "Role-Based Access",
    description:
      "Granular permissions for developers, MoE admins, university administrators, and students.",
  },
  {
    icon: CheckCircle,
    title: "Approval Workflows",
    description:
      "Document review and approval system with status tracking and multi-level authorization.",
  },
  {
    icon: Quote,
    title: "Citation Tracking",
    description:
      "All AI responses include source documents with page numbers and confidence scores for transparency.",
  },
];

export const FeaturesSection = () => {
  return (
    <section className="py-20 px-4">
      <div className="container mx-auto max-w-7xl">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Powerful Features for Policy Intelligence
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Everything you need to manage, search, and analyze government policies
            with AI-powered intelligence.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <FeatureCard
              key={feature.title}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              delay={index * 0.1}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

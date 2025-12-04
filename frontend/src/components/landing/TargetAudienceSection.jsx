// TargetAudienceSection.jsx - Target audience section

import React from "react";
import { AudienceCard } from "./AudienceCard";
import {
  Building2,
  GraduationCap,
  School,
  Search,
  BookMarked,
} from "lucide-react";

const audiences = [
  {
    icon: Building2,
    title: "Ministry of Education (MoE)",
    description:
      "Centralized policy management and cross-institutional oversight with comprehensive analytics and reporting.",
  },
  {
    icon: GraduationCap,
    title: "Higher Education Bodies",
    description:
      "AICTE, UGC, and university administrators managing institutional policies with approval workflows.",
  },
  {
    icon: School,
    title: "University Administrators",
    description:
      "Institution-specific document management with role-based access and multi-level approval systems.",
  },
  {
    icon: Search,
    title: "Researchers & Faculty",
    description:
      "Quick access to policy documents with AI-powered search, citations, and cross-referencing capabilities.",
  },
  {
    icon: BookMarked,
    title: "Students",
    description:
      "Access to public and institution-specific policy information with multilingual support and voice queries.",
  },
];

export const TargetAudienceSection = () => {
  return (
    <section className="py-20 px-4 bg-secondary/30">
      <div className="container mx-auto max-w-7xl">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Built for Government & Education
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            BEACON serves the entire education ecosystem with role-based access
            and tailored features for each user type.
          </p>
        </div>

        {/* Audience Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {audiences.map((audience, index) => (
            <AudienceCard
              key={audience.title}
              icon={audience.icon}
              title={audience.title}
              description={audience.description}
              delay={index * 0.1}
            />
          ))}
        </div>

        {/* Additional Info */}
        <div className="mt-12 text-center">
          <p className="text-muted-foreground">
            Designed specifically for the Indian education sector with support for
            multiple languages and regional requirements.
          </p>
        </div>
      </div>
    </section>
  );
};

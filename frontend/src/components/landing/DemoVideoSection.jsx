// DemoVideoSection.jsx - Demo video section with placeholder support

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Play, Video } from "lucide-react";
import { Card, CardContent } from "../ui/card";

export const DemoVideoSection = ({ videoUrl, thumbnailUrl }) => {
  const [isPlaying, setIsPlaying] = useState(false);

  const handlePlay = () => {
    setIsPlaying(true);
  };

  return (
    <section className="py-20 px-4">
      <div className="container mx-auto max-w-5xl">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            See BEACON in Action
          </h2>
          <p className="text-lg text-muted-foreground">
            Watch how BEACON transforms policy management and retrieval
          </p>
        </div>

        {/* Video Container */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <Card className="glass-card overflow-hidden">
            <CardContent className="p-0">
              {/* 16:9 Aspect Ratio Container */}
              <div className="relative w-full" style={{ paddingBottom: "56.25%" }}>
                {videoUrl && isPlaying ? (
                  /* Video Player */
                  <iframe
                    className="absolute inset-0 w-full h-full"
                    src={videoUrl}
                    title="BEACON Demo Video"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                ) : (
                  /* Placeholder */
                  <div className="absolute inset-0 bg-gradient-to-br from-secondary via-background to-secondary flex items-center justify-center">
                    {thumbnailUrl ? (
                      /* Thumbnail with Play Button */
                      <div className="relative w-full h-full">
                        <img
                          src={thumbnailUrl}
                          alt="Video thumbnail"
                          className="w-full h-full object-cover"
                        />
                        <button
                          onClick={handlePlay}
                          className="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/40 transition-colors group"
                        >
                          <div className="h-20 w-20 rounded-full bg-primary flex items-center justify-center group-hover:scale-110 transition-transform neon-glow">
                            <Play className="h-10 w-10 text-primary-foreground ml-1" />
                          </div>
                        </button>
                      </div>
                    ) : (
                      /* No Video Placeholder */
                      <div className="text-center p-8">
                        <div className="inline-flex h-24 w-24 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 mb-6">
                          <Video className="h-12 w-12 text-primary" />
                        </div>
                        <h3 className="text-2xl font-semibold mb-2">
                          Demo Coming Soon
                        </h3>
                        <p className="text-muted-foreground max-w-md mx-auto">
                          We're preparing an exciting demonstration of BEACON's
                          capabilities. Check back soon!
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Optional: Video Description */}
        <div className="text-center mt-8">
          <p className="text-sm text-muted-foreground">
            Experience the power of AI-driven policy intelligence
          </p>
        </div>
      </div>
    </section>
  );
};

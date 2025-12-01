import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Home, ArrowLeft, Search, FileQuestion } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";

export const NotFoundPage = () => {
  const navigate = useNavigate();

  const suggestions = [
    { icon: Home, label: "Go to Dashboard", path: "/" },
    { icon: Search, label: "Browse Documents", path: "/documents" },
    { icon: FileQuestion, label: "AI Chat", path: "/ai-chat" },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-background via-background to-primary/5">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl"
      >
        <Card className="glass-card border-border/50">
          <CardContent className="p-8 md:p-12">
            <div className="text-center space-y-8">
              {/* 404 Animation */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                className="relative"
              >
                <div className="text-[120px] md:text-[180px] font-bold leading-none">
                  <span className="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
                    404
                  </span>
                </div>
                <motion.div
                  animate={{
                    rotate: [0, 10, -10, 10, 0],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    repeatDelay: 1,
                  }}
                  className="absolute -top-8 -right-8 md:-right-12"
                >
                  <FileQuestion className="h-16 w-16 md:h-24 md:w-24 text-primary/30" />
                </motion.div>
              </motion.div>

              {/* Message */}
              <div className="space-y-3">
                <h1 className="text-2xl md:text-3xl font-bold">
                  Page Not Found
                </h1>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Oops! The page you're looking for doesn't exist. It might have
                  been moved or deleted.
                </p>
              </div>

              {/* Suggestions */}
              <div className="space-y-4">
                <p className="text-sm font-medium text-muted-foreground">
                  Here are some helpful links:
                </p>
                <div className="grid gap-3 md:grid-cols-3">
                  {suggestions.map((item, index) => (
                    <motion.div
                      key={item.path}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 + index * 0.1 }}
                    >
                      <Button
                        variant="outline"
                        className="w-full h-auto py-4 flex flex-col gap-2 hover:bg-primary/5 hover:border-primary/50 transition-all"
                        onClick={() => navigate(item.path)}
                      >
                        <item.icon className="h-6 w-6" />
                        <span className="text-sm">{item.label}</span>
                      </Button>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
                <Button
                  onClick={() => navigate(-1)}
                  variant="outline"
                  className="gap-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Go Back
                </Button>
                <Button
                  onClick={() => navigate("/")}
                  className="neon-glow gap-2"
                >
                  <Home className="h-4 w-4" />
                  Go to Dashboard
                </Button>
              </div>

              {/* Additional Info */}
              <div className="pt-8 border-t border-border/40">
                <p className="text-xs text-muted-foreground">
                  If you believe this is an error, please contact support or try
                  refreshing the page.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

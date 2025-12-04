import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  HelpCircle,
  Mail,
  MessageSquare,
  Phone,
  Send,
  Book,
  Video,
  FileQuestion,
  ExternalLink,
  CheckCircle,
} from "lucide-react";
import { PageHeader } from "../components/common/PageHeader";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Label } from "../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { toast } from "sonner";
import { useAuthStore } from "../stores/authStore";

export const SupportPage = () => {
  const { user } = useAuthStore();
  const [formData, setFormData] = useState({
    subject: "",
    category: "",
    message: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    // Simulate API call
    setTimeout(() => {
      toast.success(
        "Support request submitted successfully! We'll get back to you soon."
      );
      setFormData({ subject: "", category: "", message: "" });
      setSubmitting(false);
    }, 1000);
  };

  const supportChannels = [
    {
      icon: Mail,
      title: "Email Support",
      description: "Get help via email within 24 hours",
      action: "support@beacon.edu",
      link: "mailto:support@beacon.edu",
    },
    {
      icon: MessageSquare,
      title: "Live Chat",
      description: "Chat with our support team",
      action: "Start Chat",
      link: "#",
    },
    {
      icon: Phone,
      title: "Phone Support",
      description: "Call us during business hours",
      action: "+1 (555) 123-4567",
      link: "tel:+15551234567",
    },
  ];

  const resources = [
    {
      icon: Book,
      title: "Documentation",
      description: "Browse our comprehensive guides and tutorials",
      link: "#",
    },
    {
      icon: Video,
      title: "Video Tutorials",
      description: "Watch step-by-step video guides",
      link: "#",
    },
    {
      icon: FileQuestion,
      title: "FAQs",
      description: "Find answers to commonly asked questions",
      link: "#",
    },
  ];

  const faqs = [
    {
      question: "How do I upload a document?",
      answer:
        "Navigate to the Upload page from the sidebar, select your file, fill in the required metadata, and click Submit. Supported formats include PDF, DOCX, PPTX, and images.",
    },
    {
      question: "How does the AI Assistant work?",
      answer:
        "The AI Assistant uses advanced RAG (Retrieval-Augmented Generation) technology to search through your documents and provide accurate answers with citations. Simply ask your question in natural language.",
    },
    {
      question: "Can I collaborate with others on documents?",
      answer:
        "Yes! Use the Discussion tab on any document detail page to chat with other users, ask questions, and collaborate. You can also mention specific users with @username.",
    },
    {
      question: "How do I request access to external data sources?",
      answer:
        "If you're a university or ministry admin, navigate to the Data Source Request page, fill in your database connection details, test the connection, and submit your request for approval.",
    },
    {
      question: "What are the different user roles?",
      answer:
        "BEACON has several roles: Developer (full access), Ministry Admin (ministry-wide access), University Admin (institution-specific access), and Student (read access). Each role has specific permissions.",
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Get Support"
        description="We're here to help you get the most out of BEACON"
        icon={HelpCircle}
      />

      {/* Support Channels */}
      <div className="grid gap-6 md:grid-cols-3">
        {supportChannels.map((channel, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="glass-card border-border/50 h-full hover:border-primary/50 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex flex-col items-center text-center space-y-4">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <channel.icon className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">{channel.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {channel.description}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      if (channel.link.startsWith("#")) {
                        toast.info("Feature coming soon!");
                      } else {
                        window.location.href = channel.link;
                      }
                    }}
                  >
                    {channel.action}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Contact Form */}
      <Card className="glass-card border-border/50">
        <CardHeader>
          <CardTitle>Submit a Support Request</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="subject">Subject *</Label>
                <Input
                  id="subject"
                  value={formData.subject}
                  onChange={(e) =>
                    setFormData({ ...formData, subject: e.target.value })
                  }
                  placeholder="Brief description of your issue"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="category">Category *</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) =>
                    setFormData({ ...formData, category: value })
                  }
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="technical">Technical Issue</SelectItem>
                    <SelectItem value="account">Account & Access</SelectItem>
                    <SelectItem value="documents">
                      Document Management
                    </SelectItem>
                    <SelectItem value="ai">AI Assistant</SelectItem>
                    <SelectItem value="feature">Feature Request</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="message">Message *</Label>
              <Textarea
                id="message"
                value={formData.message}
                onChange={(e) =>
                  setFormData({ ...formData, message: e.target.value })
                }
                placeholder="Describe your issue or question in detail..."
                rows={6}
                required
              />
            </div>

            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={
                  submitting ||
                  !formData.subject ||
                  !formData.category ||
                  !formData.message
                }
                className="neon-glow"
              >
                {submitting ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Submit Request
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Resources */}
      <Card className="glass-card border-border/50">
        <CardHeader>
          <CardTitle>Help Resources</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {resources.map((resource, index) => (
              <button
                key={index}
                onClick={() => toast.info("Feature coming soon!")}
                className="flex items-start gap-3 p-4 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-accent/50 transition-all text-left"
              >
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <resource.icon className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-sm mb-1 flex items-center gap-2">
                    {resource.title}
                    <ExternalLink className="h-3 w-3" />
                  </h4>
                  <p className="text-xs text-muted-foreground">
                    {resource.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* FAQs */}
      <Card className="glass-card border-border/50">
        <CardHeader>
          <CardTitle>Frequently Asked Questions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.05 }}
                className="border-b border-border/50 last:border-0 pb-4 last:pb-0"
              >
                <h4 className="font-semibold mb-2 flex items-start gap-2">
                  <HelpCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                  {faq.question}
                </h4>
                <p className="text-sm text-muted-foreground ml-6">
                  {faq.answer}
                </p>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

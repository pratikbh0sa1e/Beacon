import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, ArrowLeft, Loader2 } from "lucide-react";
import { authAPI } from "../../services/api";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import { toast } from "sonner";

export const ResendVerificationPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email.trim()) {
      toast.error("Please enter your email address");
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.resendVerification(email);
      setSent(true);
      toast.success(response.data.message);
    } catch (error) {
      toast.error(
        error.response?.data?.detail ||
          "Failed to send verification email. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-background via-background to-primary/5">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <Card className="glass-card border-border/50">
          <CardContent className="p-8">
            <div className="space-y-6">
              {/* Header */}
              <div className="text-center space-y-2">
                <div className="flex justify-center mb-4">
                  <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                    <Mail className="h-8 w-8 text-primary" />
                  </div>
                </div>
                <h1 className="text-2xl font-bold">
                  Resend Verification Email
                </h1>
                <p className="text-muted-foreground">
                  Enter your email address and we'll send you a new verification
                  link
                </p>
              </div>

              {!sent ? (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Email Address</label>
                    <Input
                      type="email"
                      placeholder="your.email@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={loading}
                      required
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full neon-glow"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      "Send Verification Email"
                    )}
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={() => navigate("/login")}
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Login
                  </Button>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 text-sm">
                    <p className="font-medium mb-2">✅ Email Sent!</p>
                    <p className="text-muted-foreground">
                      We've sent a verification link to <strong>{email}</strong>
                    </p>
                  </div>

                  <div className="text-sm text-muted-foreground space-y-2">
                    <p>
                      Please check your inbox and click the verification link.
                    </p>
                    <p>
                      <strong>Note:</strong> The link will expire in 24 hours.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Button
                      onClick={() => navigate("/login")}
                      className="w-full neon-glow"
                    >
                      Go to Login
                    </Button>
                    <Button
                      onClick={() => setSent(false)}
                      variant="outline"
                      className="w-full"
                    >
                      Send to Different Email
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

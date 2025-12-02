import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle, XCircle, Loader2, Mail } from "lucide-react";
import { authAPI } from "../../services/api";
import { Button } from "../../components/ui/button";
import { Card, CardContent } from "../../components/ui/card";

export const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("verifying"); // verifying, success, error, already_verified
  const [message, setMessage] = useState("");
  const [userName, setUserName] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");

    if (!token) {
      setStatus("error");
      setMessage("Invalid verification link. No token provided.");
      return;
    }

    // Only verify once - prevent double calls
    let isMounted = true;

    const doVerification = async () => {
      if (isMounted) {
        await verifyEmail(token);
      }
    };

    doVerification();

    return () => {
      isMounted = false;
    };
  }, []); // Empty dependency array - only run once on mount

  const verifyEmail = async (token) => {
    try {
      const response = await authAPI.verifyEmail(token);

      if (response.data.status === "already_verified") {
        setStatus("already_verified");
        setMessage(response.data.message);
        setUserName(response.data.user?.name || "");
      } else {
        setStatus("success");
        setMessage(response.data.message);
        setUserName(response.data.user?.name || "");
      }
    } catch (error) {
      setStatus("error");
      setMessage(
        error.response?.data?.detail ||
          "Failed to verify email. The link may have expired."
      );
    }
  };

  const handleGoToLogin = () => {
    navigate("/login");
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
            <div className="text-center space-y-6">
              {/* Icon */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring" }}
                className="flex justify-center"
              >
                {status === "verifying" && (
                  <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center">
                    <Loader2 className="h-10 w-10 text-primary animate-spin" />
                  </div>
                )}
                {status === "success" && (
                  <div className="h-20 w-20 rounded-full bg-green-500/10 flex items-center justify-center">
                    <CheckCircle className="h-10 w-10 text-green-500" />
                  </div>
                )}
                {status === "already_verified" && (
                  <div className="h-20 w-20 rounded-full bg-blue-500/10 flex items-center justify-center">
                    <Mail className="h-10 w-10 text-blue-500" />
                  </div>
                )}
                {status === "error" && (
                  <div className="h-20 w-20 rounded-full bg-red-500/10 flex items-center justify-center">
                    <XCircle className="h-10 w-10 text-red-500" />
                  </div>
                )}
              </motion.div>

              {/* Title */}
              <div>
                <h1 className="text-2xl font-bold mb-2">
                  {status === "verifying" && "Verifying Email..."}
                  {status === "success" && "Email Verified! ✅"}
                  {status === "already_verified" && "Already Verified"}
                  {status === "error" && "Verification Failed"}
                </h1>
                {userName && (
                  <p className="text-muted-foreground">Hi {userName}!</p>
                )}
              </div>

              {/* Message */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="space-y-4"
              >
                <p className="text-muted-foreground">{message}</p>

                {status === "success" && (
                  <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 text-sm text-left">
                    <p className="font-medium mb-2">What's next?</p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>✓ Your email has been verified</li>
                      <li>⏳ Your account is pending admin approval</li>
                      <li>📧 You'll receive an email once approved</li>
                      <li>🚀 Then you can log in and start using BEACON</li>
                    </ul>
                  </div>
                )}

                {status === "error" && (
                  <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-4 text-sm text-left">
                    <p className="font-medium mb-2">Possible reasons:</p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>• Verification link has expired (24 hours)</li>
                      <li>• Link has already been used</li>
                      <li>• Invalid or corrupted link</li>
                    </ul>
                  </div>
                )}
              </motion.div>

              {/* Actions */}
              <div className="space-y-2">
                {(status === "success" || status === "already_verified") && (
                  <Button
                    onClick={handleGoToLogin}
                    className="w-full neon-glow"
                  >
                    Go to Login
                  </Button>
                )}

                {status === "error" && (
                  <>
                    <Button
                      onClick={() => navigate("/resend-verification")}
                      className="w-full neon-glow"
                    >
                      Request New Verification Link
                    </Button>
                    <Button
                      onClick={handleGoToLogin}
                      variant="outline"
                      className="w-full"
                    >
                      Back to Login
                    </Button>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, CheckCircle, ArrowRight } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent } from "../../components/ui/card";

export const RegisterSuccessPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email || "your email";

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
                <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center">
                  <Mail className="h-10 w-10 text-primary" />
                </div>
              </motion.div>

              {/* Title */}
              <div>
                <h1 className="text-2xl font-bold mb-2">
                  Check Your Email! 📧
                </h1>
                <p className="text-muted-foreground">
                  We've sent a verification link to
                </p>
                <p className="font-medium text-primary mt-1">{email}</p>
              </div>

              {/* Instructions */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="space-y-4"
              >
                <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 text-left space-y-3">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-sm">
                        Step 1: Verify Email
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Click the verification link in your email
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-sm">
                        Step 2: Admin Approval
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Wait for an administrator to approve your account
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-sm">
                        Step 3: Start Using BEACON
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Log in and access the platform
                      </p>
                    </div>
                  </div>
                </div>

                <div className="text-sm text-muted-foreground space-y-2">
                  <p>
                    <strong>Didn't receive the email?</strong>
                  </p>
                  <ul className="text-xs space-y-1 pl-4">
                    <li>• Check your spam/junk folder</li>
                    <li>• Make sure you entered the correct email</li>
                    <li>• Wait a few minutes and check again</li>
                  </ul>
                </div>
              </motion.div>

              {/* Actions */}
              <div className="space-y-2">
                <Button
                  onClick={() => navigate("/resend-verification")}
                  variant="outline"
                  className="w-full"
                >
                  Resend Verification Email
                </Button>
                <Button
                  onClick={() => navigate("/login")}
                  className="w-full neon-glow"
                >
                  Go to Login
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>

              <p className="text-xs text-muted-foreground">
                The verification link will expire in 24 hours
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

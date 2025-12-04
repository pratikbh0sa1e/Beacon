import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, Lock, User, Building2, UserPlus, Moon, Sun } from "lucide-react";
import { authAPI, institutionAPI } from "../../services/api";
import { useThemeStore } from "../../stores/themeStore";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { toast } from "sonner";

export const RegisterPage = () => {
  const { theme, toggleTheme } = useThemeStore();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    role: "",
    institution_id: null,
    parent_ministry_id: null, // For two-step selection
  });
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // ✅ FIXED: Filter out 'developer' from available roles
  const availableRoles = [
    {
      value: "student",
      label: "Student",
      needsInstitution: true,
      institutionType: "university",
    },
    {
      value: "document_officer",
      label: "Document Officer",
      needsInstitution: true,
      institutionType: "university",
    },
    {
      value: "university_admin",
      label: "University Admin",
      needsInstitution: true,
      institutionType: "university",
    },
    {
      value: "ministry_admin",
      label: "Ministry Admin",
      needsInstitution: true,
      institutionType: "ministry",
    },
    {
      value: "public_viewer",
      label: "Public Viewer",
      needsInstitution: false,
    },
    // Developer role is NOT included - it's only created via backend initialization
  ];

  useEffect(() => {
    fetchInstitutions();
  }, []);

  const fetchInstitutions = async () => {
    try {
      const response = await institutionAPI.listPublic();
      setInstitutions(response.data || []);
    } catch (error) {
      console.error("Error fetching institutions:", error);
      toast.error("Failed to load institutions");
    }
  };

  const handleChange = (field, value) => {
    // If role changes, reset institution and ministry selection
    if (field === "role") {
      setFormData((prev) => ({
        ...prev,
        [field]: value,
        institution_id: null,
        parent_ministry_id: null,
      }));
    }
    // If ministry changes, reset institution selection
    else if (field === "parent_ministry_id") {
      setFormData((prev) => ({
        ...prev,
        [field]: value,
        institution_id: null,
      }));
    } else {
      setFormData((prev) => ({ ...prev, [field]: value }));
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();

    // Validation
    if (formData.password !== formData.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    if (!formData.role) {
      toast.error("Please select a role");
      return;
    }

    if (!formData.name.trim()) {
      toast.error("Please enter your name");
      return;
    }

    // Check if selected role needs institution
    const selectedRole = availableRoles.find((r) => r.value === formData.role);
    if (selectedRole?.needsInstitution && !formData.institution_id) {
      toast.error("Please select an institution for this role");
      return;
    }

    setLoading(true);
    try {
      await authAPI.register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        role: formData.role,
        institution_id: formData.institution_id
          ? parseInt(formData.institution_id)
          : null,
      });

      toast.success(
        "Registration successful! Please check your email to verify your account."
      );
      // Navigate to a success page showing email verification message
      navigate("/register-success", { state: { email: formData.email } });
    } catch (error) {
      console.error("Registration error:", error);
      toast.error(
        error.response?.data?.detail || "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  // Get selected role info
  const selectedRole = availableRoles.find((r) => r.value === formData.role);
  const showInstitutionField = selectedRole?.needsInstitution;

  // Get ministries for dropdown
  const ministries = institutions.filter((inst) => inst.type === "ministry");

  // Filter institutions based on selected role and ministry
  let filteredInstitutions = [];
  if (selectedRole?.institutionType === "ministry") {
    // Ministry admin: show only ministries
    filteredInstitutions = ministries;
  } else if (selectedRole?.institutionType === "university") {
    // University roles: show institutions under selected ministry
    if (formData.parent_ministry_id) {
      filteredInstitutions = institutions.filter(
        (inst) =>
          inst.type === "university" &&
          inst.parent_ministry_id === parseInt(formData.parent_ministry_id)
      );
    } else {
      // If no ministry selected yet, show all universities
      filteredInstitutions = institutions.filter(
        (inst) => inst.type === "university"
      );
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Theme Toggle Button */}
      <div className="absolute top-4 right-4 z-20">
        <Button
          variant="outline"
          size="icon"
          onClick={toggleTheme}
          className="glass-card"
        >
          {theme === "dark" ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </Button>
      </div>

      <div className="absolute inset-0 bg-gradient-to-br from-background via-secondary to-background" />
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, hsl(var(--primary) / 0.1) 1px, transparent 0)",
          backgroundSize: "40px 40px",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200 }}
            className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent mb-4 neon-glow"
          >
            <span className="text-2xl font-bold text-primary-foreground">
              B
            </span>
          </motion.div>
          <h1 className="text-4xl font-bold gradient-text mb-2">BEACON</h1>
          <p className="text-muted-foreground">Create your account</p>
        </div>

        <Card className="glass-card border-border/50">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl">Sign Up</CardTitle>
            <CardDescription>
              Create an account to access the document system
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleRegister}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="name"
                    type="text"
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={(e) => handleChange("name", e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="your.email@example.com"
                    value={formData.email}
                    onChange={(e) => handleChange("email", e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="role">Role</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground z-10" />
                  <Select
                    value={formData.role}
                    onValueChange={(value) => handleChange("role", value)}
                    required
                  >
                    <SelectTrigger className="pl-10">
                      <SelectValue placeholder="Select your role" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableRoles.map((role) => (
                        <SelectItem key={role.value} value={role.value}>
                          {role.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {showInstitutionField && (
                <>
                  {/* Step 1: Select Ministry (for university roles only) */}
                  {selectedRole?.institutionType === "university" && (
                    <div className="space-y-2">
                      <Label htmlFor="ministry">
                        Step 1: Select Ministry{" "}
                        <span className="text-destructive">*</span>
                      </Label>
                      <div className="relative">
                        <Building2 className="absolute left-3 top-3 h-4 w-4 text-muted-foreground z-10" />
                        <Select
                          value={
                            formData.parent_ministry_id
                              ? String(formData.parent_ministry_id)
                              : ""
                          }
                          onValueChange={(value) =>
                            handleChange("parent_ministry_id", value)
                          }
                          required
                        >
                          <SelectTrigger className="pl-10">
                            <SelectValue placeholder="Select governing ministry" />
                          </SelectTrigger>
                          <SelectContent>
                            {ministries.length > 0 ? (
                              ministries.map((ministry) => (
                                <SelectItem
                                  key={ministry.id}
                                  value={String(ministry.id)}
                                >
                                  {ministry.name}
                                </SelectItem>
                              ))
                            ) : (
                              <SelectItem value="none" disabled>
                                No ministries available
                              </SelectItem>
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                      {ministries.length === 0 && (
                        <p className="text-xs text-muted-foreground">
                          No ministries found. Please contact administrator.
                        </p>
                      )}
                    </div>
                  )}

                  {/* Step 2: Select Institution */}
                  <div className="space-y-2">
                    <Label htmlFor="institution">
                      {selectedRole?.institutionType === "university"
                        ? "Step 2: Select Institution"
                        : "Ministry"}{" "}
                      <span className="text-destructive">*</span>
                    </Label>
                    <div className="relative">
                      <Building2 className="absolute left-3 top-3 h-4 w-4 text-muted-foreground z-10" />
                      <Select
                        value={
                          formData.institution_id
                            ? String(formData.institution_id)
                            : ""
                        }
                        onValueChange={(value) =>
                          handleChange("institution_id", value)
                        }
                        required={showInstitutionField}
                        disabled={
                          selectedRole?.institutionType === "university" &&
                          !formData.parent_ministry_id
                        }
                      >
                        <SelectTrigger className="pl-10">
                          <SelectValue
                            placeholder={
                              selectedRole?.institutionType === "ministry"
                                ? "Select ministry"
                                : formData.parent_ministry_id
                                ? "Select institution under selected ministry"
                                : "Select ministry first"
                            }
                          />
                        </SelectTrigger>
                        <SelectContent>
                          {filteredInstitutions.length > 0 ? (
                            filteredInstitutions.map((inst) => (
                              <SelectItem key={inst.id} value={String(inst.id)}>
                                {inst.name}
                                {inst.location && ` - ${inst.location}`}
                              </SelectItem>
                            ))
                          ) : (
                            <SelectItem value="none" disabled>
                              {selectedRole?.institutionType === "university" &&
                              !formData.parent_ministry_id
                                ? "Please select a ministry first"
                                : `No ${
                                    selectedRole?.institutionType === "ministry"
                                      ? "ministries"
                                      : "institutions"
                                  } available`}
                            </SelectItem>
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                    {selectedRole?.institutionType === "university" &&
                      formData.parent_ministry_id &&
                      filteredInstitutions.length === 0 && (
                        <p className="text-xs text-muted-foreground">
                          No institutions found under selected ministry. Please
                          contact administrator.
                        </p>
                      )}
                  </div>
                </>
              )}

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="Create a password"
                    value={formData.password}
                    onChange={(e) => handleChange("password", e.target.value)}
                    className="pl-10"
                    required
                    minLength={8}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={(e) =>
                      handleChange("confirmPassword", e.target.value)
                    }
                    className="pl-10"
                    required
                    minLength={8}
                  />
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                className="w-full neon-glow"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        ease: "linear",
                      }}
                    >
                      <UserPlus className="h-4 w-4" />
                    </motion.div>
                    Creating account...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <UserPlus className="h-4 w-4" />
                    Create Account
                  </span>
                )}
              </Button>
              <p className="text-sm text-center text-muted-foreground">
                Already have an account?{" "}
                <Link
                  to="/login"
                  className="text-primary hover:underline font-medium"
                >
                  Sign in
                </Link>
              </p>
            </CardFooter>
          </form>
        </Card>
      </motion.div>
    </div>
  );
};

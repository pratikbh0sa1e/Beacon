import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Database,
  TestTube,
  Send,
  AlertCircle,
  Info,
  Loader2,
} from "lucide-react";
import { useAuthStore } from "../../stores/authStore";
import { PageHeader } from "../../components/common/PageHeader";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Alert, AlertDescription } from "../../components/ui/alert";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../components/ui/tooltip";
import { toast } from "sonner";
import axios from "axios";
import {
  formatErrorForToast,
  formatErrorForAlert,
} from "../../utils/errorHandlers";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const DataSourceRequestPage = () => {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

  const [formData, setFormData] = useState({
    name: "",
    ministry_name: "",
    description: "",
    host: "",
    port: 5432,
    database_name: "",
    username: "",
    password: "",
    table_name: "",
    file_column: "",
    filename_column: "",
    data_classification: "educational",
    request_notes: "",
  });

  const validateField = (field, value) => {
    const errors = {};

    switch (field) {
      case "name":
        if (!value || value.trim().length < 3) {
          errors[field] = "Name must be at least 3 characters";
        }
        break;
      case "ministry_name":
        if (!value || value.trim().length < 3) {
          errors[field] = "Institution name must be at least 3 characters";
        }
        break;
      case "host":
        if (!value || value.trim().length === 0) {
          errors[field] = "Host is required";
        } else if (!/^[a-zA-Z0-9.-]+$/.test(value)) {
          errors[field] = "Invalid host format";
        }
        break;
      case "port":
        if (!value || value < 1 || value > 65535) {
          errors[field] = "Port must be between 1 and 65535";
        }
        break;
      case "database_name":
        if (!value || value.trim().length === 0) {
          errors[field] = "Database name is required";
        }
        break;
      case "username":
        if (!value || value.trim().length === 0) {
          errors[field] = "Username is required";
        }
        break;
      case "password":
        if (!value || value.length < 4) {
          errors[field] = "Password must be at least 4 characters";
        }
        break;
      case "table_name":
        if (!value || value.trim().length === 0) {
          errors[field] = "Table name is required";
        }
        break;
      case "file_column":
        if (!value || value.trim().length === 0) {
          errors[field] = "File column is required";
        }
        break;
      case "filename_column":
        if (!value || value.trim().length === 0) {
          errors[field] = "Filename column is required";
        }
        break;
    }

    return errors;
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));

    // Real-time validation
    const fieldErrors = validateField(field, value);
    setValidationErrors((prev) => {
      const newErrors = { ...prev };
      if (Object.keys(fieldErrors).length > 0) {
        newErrors[field] = fieldErrors[field];
      } else {
        delete newErrors[field];
      }
      return newErrors;
    });
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const token = localStorage.getItem("beacon-auth");
      const authData = JSON.parse(token);

      const response = await axios.post(
        `${API_URL}/data-sources/test-connection`,
        {
          host: formData.host,
          port: formData.port,
          database_name: formData.database_name,
          username: formData.username,
          password: formData.password,
        },
        {
          headers: {
            Authorization: `Bearer ${authData.state.token}`,
          },
        }
      );

      setTestResult(response.data);
      if (response.data.status === "success") {
        toast.success("✅ Connection successful!");
      } else {
        // Use error handler for better messages
        const errorAlert = formatErrorForAlert(
          { response: { data: response.data } },
          "Connection failed"
        );
        setTestResult({
          status: "failed",
          message: errorAlert.message,
          hint: errorAlert.hint,
          icon: errorAlert.icon,
        });
        toast.error(
          formatErrorForToast(
            { response: { data: response.data } },
            "Connection failed"
          )
        );
      }
    } catch (error) {
      const errorAlert = formatErrorForAlert(error, "Connection test failed");
      setTestResult({
        status: "failed",
        message: errorAlert.message,
        hint: errorAlert.hint,
        icon: errorAlert.icon,
      });
      toast.error(formatErrorForToast(error, "Connection test failed"));
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem("beacon-auth");
      const authData = JSON.parse(token);

      const response = await axios.post(
        `${API_URL}/data-sources/request`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${authData.state.token}`,
          },
        }
      );

      toast.success(
        "✅ Request submitted successfully! Awaiting developer approval."
      );

      // Reset form
      setFormData({
        name: "",
        ministry_name: "",
        description: "",
        host: "",
        port: 5432,
        database_name: "",
        username: "",
        password: "",
        table_name: "",
        file_column: "",
        filename_column: "",
        data_classification: "educational",
        request_notes: "",
      });
      setTestResult(null);
    } catch (error) {
      toast.error(formatErrorForToast(error, "Failed to submit request"));
    } finally {
      setLoading(false);
    }
  };

  const isUniversityAdmin = user?.role === "university_admin";

  const FormField = ({ id, label, tooltip, error, children }) => (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Label htmlFor={id}>{label}</Label>
        {tooltip && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>{tooltip}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      {children}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs text-destructive flex items-center gap-1"
        >
          <AlertCircle className="h-3 w-3" />
          {error}
        </motion.p>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Request Data Source Connection"
        description="Connect your external database to BEACON"
        icon={Database}
      />

      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 md:grid-cols-2">
          {/* Basic Information */}
          <Card className="glass-card border-border/50 md:col-span-2">
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  id="name"
                  label="Data Source Name *"
                  tooltip="A descriptive name for this data source connection"
                  error={validationErrors.name}
                >
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleChange("name", e.target.value)}
                    placeholder="e.g., MIT Student Database"
                    className={
                      validationErrors.name ? "border-destructive" : ""
                    }
                    required
                  />
                </FormField>

                <FormField
                  id="ministry_name"
                  label={`${
                    isUniversityAdmin ? "Institution Name" : "Ministry Name"
                  } *`}
                  tooltip={`The name of your ${
                    isUniversityAdmin ? "institution" : "ministry"
                  }`}
                  error={validationErrors.ministry_name}
                >
                  <Input
                    id="ministry_name"
                    value={formData.ministry_name}
                    onChange={(e) =>
                      handleChange("ministry_name", e.target.value)
                    }
                    placeholder={
                      isUniversityAdmin
                        ? "e.g., MIT University"
                        : "e.g., Ministry of Education"
                    }
                    className={
                      validationErrors.ministry_name ? "border-destructive" : ""
                    }
                    required
                  />
                </FormField>
              </div>

              <FormField
                id="description"
                label="Description"
                tooltip="Optional description to help identify this data source"
              >
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleChange("description", e.target.value)}
                  placeholder="Brief description of the data source"
                  rows={3}
                />
              </FormField>
            </CardContent>
          </Card>

          {/* Database Connection */}
          <Card className="glass-card border-border/50 md:col-span-2">
            <CardHeader>
              <CardTitle>Database Connection Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="md:col-span-2">
                  <FormField
                    id="host"
                    label="Database Host *"
                    tooltip="The hostname or IP address of your database server"
                    error={validationErrors.host}
                  >
                    <Input
                      id="host"
                      value={formData.host}
                      onChange={(e) => handleChange("host", e.target.value)}
                      placeholder="e.g., db.example.com"
                      className={
                        validationErrors.host ? "border-destructive" : ""
                      }
                      required
                    />
                  </FormField>
                </div>

                <FormField
                  id="port"
                  label="Port *"
                  tooltip="Database port number (default PostgreSQL: 5432, MySQL: 3306)"
                  error={validationErrors.port}
                >
                  <Input
                    id="port"
                    type="number"
                    value={formData.port}
                    onChange={(e) =>
                      handleChange("port", parseInt(e.target.value) || 0)
                    }
                    placeholder="5432"
                    className={
                      validationErrors.port ? "border-destructive" : ""
                    }
                    required
                  />
                </FormField>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  id="database_name"
                  label="Database Name *"
                  tooltip="The name of the database containing your documents"
                  error={validationErrors.database_name}
                >
                  <Input
                    id="database_name"
                    value={formData.database_name}
                    onChange={(e) =>
                      handleChange("database_name", e.target.value)
                    }
                    placeholder="e.g., student_docs"
                    className={
                      validationErrors.database_name ? "border-destructive" : ""
                    }
                    required
                  />
                </FormField>

                <FormField
                  id="username"
                  label="Username *"
                  tooltip="Database user with read access to the documents table"
                  error={validationErrors.username}
                >
                  <Input
                    id="username"
                    value={formData.username}
                    onChange={(e) => handleChange("username", e.target.value)}
                    placeholder="Database username"
                    className={
                      validationErrors.username ? "border-destructive" : ""
                    }
                    required
                  />
                </FormField>
              </div>

              <FormField
                id="password"
                label="Password *"
                tooltip="Database password (will be encrypted and stored securely)"
                error={validationErrors.password}
              >
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => handleChange("password", e.target.value)}
                  placeholder="Database password"
                  className={
                    validationErrors.password ? "border-destructive" : ""
                  }
                  required
                />
              </FormField>

              <Button
                type="button"
                variant="outline"
                onClick={handleTestConnection}
                disabled={
                  testing ||
                  !formData.host ||
                  !formData.database_name ||
                  !formData.username ||
                  !formData.password ||
                  Object.keys(validationErrors).length > 0
                }
              >
                {testing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Testing Connection...
                  </>
                ) : (
                  <>
                    <TestTube className="h-4 w-4 mr-2" />
                    Test Connection
                  </>
                )}
              </Button>

              {testResult && (
                <Alert
                  variant={
                    testResult.status === "success" ? "default" : "destructive"
                  }
                >
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {testResult.status === "success" ? (
                      "✅ Connection successful!"
                    ) : (
                      <div className="space-y-2">
                        <div>
                          {testResult.icon && `${testResult.icon} `}
                          {testResult.message}
                        </div>
                        {testResult.hint && (
                          <div className="text-sm text-muted-foreground mt-2">
                            💡 <strong>Suggestion:</strong> {testResult.hint}
                          </div>
                        )}
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Table Configuration */}
          <Card className="glass-card border-border/50 md:col-span-2">
            <CardHeader>
              <CardTitle>Table Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <FormField
                  id="table_name"
                  label="Table Name *"
                  tooltip="The database table or collection containing document files"
                  error={validationErrors.table_name}
                >
                  <Input
                    id="table_name"
                    value={formData.table_name}
                    onChange={(e) => handleChange("table_name", e.target.value)}
                    placeholder="e.g., documents"
                    className={
                      validationErrors.table_name ? "border-destructive" : ""
                    }
                    required
                  />
                </FormField>

                <FormField
                  id="file_column"
                  label="File Column *"
                  tooltip="Column name containing the binary file data (bytea/blob)"
                  error={validationErrors.file_column}
                >
                  <Input
                    id="file_column"
                    value={formData.file_column}
                    onChange={(e) =>
                      handleChange("file_column", e.target.value)
                    }
                    placeholder="e.g., file_data"
                    className={
                      validationErrors.file_column ? "border-destructive" : ""
                    }
                    required
                  />
                </FormField>

                <FormField
                  id="filename_column"
                  label="Filename Column *"
                  tooltip="Column name containing the original filename (e.g., 'report.pdf')"
                  error={validationErrors.filename_column}
                >
                  <Input
                    id="filename_column"
                    value={formData.filename_column}
                    onChange={(e) =>
                      handleChange("filename_column", e.target.value)
                    }
                    placeholder="e.g., filename"
                    className={
                      validationErrors.filename_column
                        ? "border-destructive"
                        : ""
                    }
                    required
                  />
                </FormField>
              </div>
            </CardContent>
          </Card>

          {/* Data Classification */}
          <Card className="glass-card border-border/50 md:col-span-2">
            <CardHeader>
              <CardTitle>Data Classification</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isUniversityAdmin ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Institutional Data:</strong> Documents will be
                    visible only to users from your institution.
                  </AlertDescription>
                </Alert>
              ) : (
                <FormField
                  id="classification"
                  label="Data Classification *"
                  tooltip="Controls who can access documents from this data source"
                >
                  <Select
                    value={formData.data_classification}
                    onValueChange={(value) =>
                      handleChange("data_classification", value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="public">
                        Public - Everyone can see
                      </SelectItem>
                      <SelectItem value="educational">
                        Educational - Universities + Ministries
                      </SelectItem>
                      <SelectItem value="confidential">
                        Confidential - Ministry Only
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </FormField>
              )}

              <FormField
                id="request_notes"
                label="Request Notes"
                tooltip="Optional notes for the developer reviewing this request"
              >
                <Textarea
                  id="request_notes"
                  value={formData.request_notes}
                  onChange={(e) =>
                    handleChange("request_notes", e.target.value)
                  }
                  placeholder="Any additional information for the reviewer"
                  rows={3}
                />
              </FormField>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            type="submit"
            disabled={loading || Object.keys(validationErrors).length > 0}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Submitting Request...
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
    </div>
  );
};

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  MapPin,
  Plus,
  Search,
  School,
  Landmark,
  Trash2,
  AlertTriangle,
  User,
} from "lucide-react";
import { institutionAPI } from "../../services/api";
import { useAuthStore } from "../../stores/authStore";
import { PageHeader } from "../../components/common/PageHeader";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "../../components/ui/alert";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { Label } from "../../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { toast } from "sonner";

const INSTITUTION_TYPES = [
  {
    value: "university",
    label: "Institution (University, Hospital, Research Centre, etc.)",
    icon: School,
  },
  { value: "ministry", label: "Ministry", icon: Landmark },
];

export const InstitutionsPage = () => {
  const { user } = useAuthStore();
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState("university");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [institutionToDelete, setInstitutionToDelete] = useState(null);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");

  // New Institution Form State
  const [formData, setFormData] = useState({
    name: "",
    location: "",
    type: "university",
    parent_ministry_id: null,
  });

  // Get list of ministries for dropdown
  const ministries = institutions.filter((inst) => inst.type === "ministry");

  useEffect(() => {
    fetchInstitutions();
  }, []);

  const fetchInstitutions = async () => {
    setLoading(true);
    try {
      const response = await institutionAPI.list();
      setInstitutions(response.data || []);
    } catch (error) {
      console.error("Error fetching institutions:", error);
      toast.error("Failed to load institutions");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    setIsSubmitting(true);
    try {
      await institutionAPI.create(formData);
      toast.success(
        `${
          formData.type === "university" ? "Institution" : "Ministry"
        } created successfully!`
      );
      setIsCreateOpen(false);
      setFormData({
        name: "",
        location: "",
        type: activeTab,
        parent_ministry_id: null,
      }); // Reset form with current tab type
      fetchInstitutions(); // Refresh list
    } catch (error) {
      console.error("Creation error:", error);
      toast.error(
        error.response?.data?.detail || "Failed to create institution"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteClick = (institution) => {
    setInstitutionToDelete(institution);
    setDeleteConfirmText(""); // Reset confirmation text
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!institutionToDelete) return;

    // Validate confirmation text
    if (deleteConfirmText !== institutionToDelete.name) {
      toast.error(
        "Institution name does not match. Please type the exact name."
      );
      return;
    }

    setIsSubmitting(true);
    try {
      await institutionAPI.delete(institutionToDelete.id, { confirm: true });

      toast.success(
        `${institutionToDelete.name} deleted. ${institutionToDelete.user_count} users converted to public viewers.`
      );
      setDeleteDialogOpen(false);
      setInstitutionToDelete(null);
      setDeleteConfirmText("");
      fetchInstitutions(); // Refresh list
    } catch (error) {
      console.error("Deletion error:", error);
      toast.error(
        error.response?.data?.detail || "Failed to delete institution"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // When dialog opens, set form type to current tab
  const handleDialogOpen = (open) => {
    if (open) {
      setFormData({
        name: "",
        location: "",
        type: activeTab,
        parent_ministry_id: null,
      });
    }
    setIsCreateOpen(open);
  };

  // Filter by active tab and search term
  const filteredInstitutions = institutions.filter((inst) => {
    const matchesSearch =
      inst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inst.location?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTab = inst.type === activeTab;
    return matchesSearch && matchesTab;
  });

  // Count institutions by type
  const counts = {
    university: institutions.filter((i) => i.type === "university").length,
    ministry: institutions.filter((i) => i.type === "ministry").length,
  };

  // Check if user can add institution based on active tab
  const canAddInstitution = () => {
    if (activeTab === "ministry") {
      // Only developer can add ministries
      return user?.role === "developer";
    }
    // Developer and ministry admin can add institutions
    return ["developer", "ministry_admin"].includes(user?.role);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Institution Management"
        description={
          user?.role === "university_admin"
            ? "View your institution and parent ministry information."
            : "Register and manage institutions (universities, hospitals, research centres) and ministries."
        }
        icon={Building2}
        action={
          canAddInstitution() ? (
            <Dialog open={isCreateOpen} onOpenChange={handleDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  className="neon-glow"
                  disabled={!canAddInstitution()}
                  title={
                    !canAddInstitution()
                      ? activeTab === "ministry"
                        ? "Only developers can add ministries"
                        : "Insufficient permissions"
                      : ""
                  }
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add {activeTab === "university" ? "Institution" : "Ministry"}
                </Button>
              </DialogTrigger>
              <DialogContent className="glass-card sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>
                    Register New{" "}
                    {activeTab === "university" ? "Institution" : "Ministry"}
                  </DialogTitle>
                  <DialogDescription>
                    Add a new{" "}
                    {activeTab === "university"
                      ? "institution (university, hospital, research centre, defence academy, etc.)"
                      : "ministry"}{" "}
                    to the system.
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreate} className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">
                      {activeTab === "university"
                        ? "Institution Name"
                        : "Ministry Name"}
                    </Label>
                    <Input
                      id="name"
                      placeholder={
                        activeTab === "university"
                          ? "e.g., IIT Delhi, AIIMS Mumbai, DRDO"
                          : "e.g., Ministry of Education"
                      }
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="location">
                      Location{" "}
                      {activeTab === "ministry"
                        ? "(Headquarters)"
                        : "(City/State)"}
                    </Label>
                    <Input
                      id="location"
                      placeholder={
                        activeTab === "ministry"
                          ? "e.g., New Delhi"
                          : "e.g., Mumbai, Maharashtra"
                      }
                      value={formData.location}
                      onChange={(e) =>
                        setFormData({ ...formData, location: e.target.value })
                      }
                    />
                  </div>

                  {/* Ministry Selection - Only for Universities */}
                  {activeTab === "university" && (
                    <div className="space-y-2">
                      <Label htmlFor="parent_ministry">
                        Governing Ministry{" "}
                        <span className="text-destructive">*</span>
                      </Label>
                      <Select
                        value={
                          formData.parent_ministry_id
                            ? String(formData.parent_ministry_id)
                            : ""
                        }
                        onValueChange={(v) =>
                          setFormData({
                            ...formData,
                            parent_ministry_id: parseInt(v),
                          })
                        }
                        required
                      >
                        <SelectTrigger>
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
                      {ministries.length === 0 && (
                        <p className="text-xs text-muted-foreground">
                          Please create a ministry first before adding
                          universities.
                        </p>
                      )}
                    </div>
                  )}

                  {/* Hidden type field - auto-set based on active tab */}
                  <input type="hidden" name="type" value={formData.type} />

                  {/* Show type info as read-only badge */}
                  <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
                    {activeTab === "university" ? (
                      <>
                        <School className="h-4 w-4 text-primary" />
                        <span className="text-sm">
                          Type: Institution (University, Hospital, Research
                          Centre, etc.)
                        </span>
                      </>
                    ) : (
                      <>
                        <Landmark className="h-4 w-4 text-primary" />
                        <span className="text-sm">Type: Ministry</span>
                      </>
                    )}
                  </div>
                  <DialogFooter>
                    <Button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full neon-glow"
                    >
                      {isSubmitting
                        ? "Registering..."
                        : `Register ${
                            activeTab === "university"
                              ? "Institution"
                              : "Ministry"
                          }`}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          ) : null
        }
      />

      {/* Info for University Admin */}
      {user?.role === "university_admin" && (
        <Alert>
          <Building2 className="h-4 w-4" />
          <AlertTitle>Read-Only View</AlertTitle>
          <AlertDescription>
            You can view your institution and parent ministry information here.
            To manage users or settings, contact your ministry administrator.
          </AlertDescription>
        </Alert>
      )}

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList
          className={`grid w-full max-w-md ${
            user?.role === "developer" ? "grid-cols-2" : "grid-cols-1"
          }`}
        >
          <TabsTrigger value="university" className="flex items-center gap-2">
            <School className="h-4 w-4" />
            Institutions ({counts.university})
          </TabsTrigger>
          {user?.role === "developer" && (
            <TabsTrigger value="ministry" className="flex items-center gap-2">
              <Landmark className="h-4 w-4" />
              Ministries ({counts.ministry})
            </TabsTrigger>
          )}
        </TabsList>

        {/* Search Bar */}
        <Card className="glass-card border-border/50">
          <CardContent className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={`Search ${
                  activeTab === "university" ? "institutions" : "ministries"
                }...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        {/* Tab Content */}
        <TabsContent value={activeTab} className="mt-0">
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence>
              {filteredInstitutions.map((inst, index) => {
                const TypeIcon =
                  INSTITUTION_TYPES.find((t) => t.value === inst.type)?.icon ||
                  Building2;

                return (
                  <motion.div
                    key={inst.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className="glass-card border-border/50 hover:border-primary/50 transition-colors h-full">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            <TypeIcon className="h-5 w-5 text-primary" />
                          </div>
                          <Badge variant="outline">
                            {inst.type.replace("_", " ")}
                          </Badge>
                        </div>
                        <h3 className="font-semibold text-lg mb-1 line-clamp-2">
                          {inst.name}
                        </h3>
                        {inst.location && (
                          <p className="text-sm text-muted-foreground flex items-center gap-1 mb-2">
                            <MapPin className="h-3 w-3" />
                            {inst.location}
                          </p>
                        )}

                        {/* Show parent ministry for universities */}
                        {inst.type === "university" && inst.parent_ministry && (
                          <div className="mb-4">
                            <Badge variant="outline" className="text-xs">
                              <Landmark className="h-3 w-3 mr-1" />
                              {inst.parent_ministry.name}
                            </Badge>
                          </div>
                        )}

                        {/* Show stats for ministries */}
                        {inst.type === "ministry" && (
                          <div className="mb-4 space-y-2">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-muted-foreground flex items-center gap-1">
                                <School className="h-3 w-3" />
                                Institutions
                              </span>
                              <Badge variant="outline" className="text-xs">
                                {inst.child_universities_count || 0}
                              </Badge>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-muted-foreground flex items-center gap-1">
                                <User className="h-3 w-3" />
                                Ministry Admins
                              </span>
                              <Badge variant="outline" className="text-xs">
                                {inst.user_count || 0}
                              </Badge>
                            </div>
                          </div>
                        )}

                        {/* Delete button section - for both types */}
                        <div className="mt-auto pt-4 border-t border-border/40">
                          {/* Show user count for institutions */}
                          {inst.type === "university" && (
                            <div className="flex justify-between items-center text-sm mb-3">
                              <span className="text-muted-foreground">
                                Total Users
                              </span>
                              <Badge variant="secondary">
                                {inst.user_count || 0}
                              </Badge>
                            </div>
                          )}

                          {/* Delete Button */}
                          {(user?.role === "developer" ||
                            (user?.role === "ministry_admin" &&
                              inst.type === "university" &&
                              inst.parent_ministry_id ===
                                user?.institution_id)) && (
                            <Button
                              variant="destructive"
                              size="sm"
                              className="w-full"
                              onClick={() => handleDeleteClick(inst)}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete{" "}
                              {inst.type === "ministry"
                                ? "Ministry"
                                : "Institution"}
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {filteredInstitutions.length === 0 && !loading && (
              <div className="col-span-full text-center py-12 text-muted-foreground">
                {searchTerm ? (
                  <>
                    No{" "}
                    {activeTab === "university" ? "institutions" : "ministries"}{" "}
                    found matching "{searchTerm}".
                  </>
                ) : (
                  <>
                    No{" "}
                    {activeTab === "university" ? "institutions" : "ministries"}{" "}
                    registered yet. Click "Add{" "}
                    {activeTab === "university" ? "Institution" : "Ministry"}"
                    to add one.
                  </>
                )}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Delete Confirmation Dialog - AWS Style */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Delete {institutionToDelete?.name}?
            </DialogTitle>
            <DialogDescription>
              This action cannot be undone. Please read carefully before
              proceeding.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* User Count Warning */}
            {institutionToDelete?.user_count > 0 && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>
                  Warning: This institution has {institutionToDelete.user_count}{" "}
                  active users
                </AlertTitle>
                <AlertDescription>
                  All users will be immediately converted to Public Viewers and
                  notified via email.
                </AlertDescription>
              </Alert>
            )}

            {/* What Will Happen */}
            <div className="space-y-2 p-4 bg-muted/50 rounded-lg">
              <p className="font-semibold text-sm">What will happen:</p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-destructive mt-0.5">•</span>
                  <span>Institution will be permanently marked as deleted</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-destructive mt-0.5">•</span>
                  <span>
                    All {institutionToDelete?.user_count || 0} users will lose
                    their current role and institution access
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-destructive mt-0.5">•</span>
                  <span>
                    Users will be converted to Public Viewers (limited access)
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-destructive mt-0.5">•</span>
                  <span>
                    Users must re-register at a new institution to regain full
                    access
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Documents and historical data will be preserved</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>
                    Email notifications will be sent to all affected users
                  </span>
                </li>
              </ul>
            </div>

            {/* Confirmation Input - AWS Style */}
            <div className="space-y-2">
              <Label htmlFor="confirm-delete" className="text-sm font-semibold">
                To confirm deletion, type the institution name below:
              </Label>
              <div className="p-3 bg-muted rounded-md border">
                <code className="text-sm font-mono font-semibold">
                  {institutionToDelete?.name}
                </code>
              </div>
              <Input
                id="confirm-delete"
                placeholder="Type institution name here"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                className="font-mono"
                autoComplete="off"
              />
              {deleteConfirmText &&
                deleteConfirmText !== institutionToDelete?.name && (
                  <p className="text-xs text-destructive flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    Institution name does not match
                  </p>
                )}
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setDeleteConfirmText("");
              }}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={
                isSubmitting || deleteConfirmText !== institutionToDelete?.name
              }
            >
              {isSubmitting ? (
                <>Deleting...</>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Institution
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

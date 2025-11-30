import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  MapPin,
  Plus,
  Search,
  School,
  Landmark,
} from "lucide-react";
import { institutionAPI } from "../../services/api";
import { PageHeader } from "../../components/common/PageHeader";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
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
  { value: "university", label: "University / College", icon: School },
  { value: "government_dept", label: "Government Department", icon: Building2 },
  { value: "ministry", label: "Ministry", icon: Landmark },
];

export const InstitutionsPage = () => {
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // New Institution Form State
  const [formData, setFormData] = useState({
    name: "",
    location: "",
    type: "university",
  });

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
      toast.success("Institution created successfully!");
      setIsCreateOpen(false);
      setFormData({ name: "", location: "", type: "university" }); // Reset form
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

  const filteredInstitutions = institutions.filter(
    (inst) =>
      inst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inst.location?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Institution Management"
        description="Register and manage universities and government departments."
        icon={Building2}
        action={
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button className="neon-glow">
                <Plus className="h-4 w-4 mr-2" />
                Register Institution
              </Button>
            </DialogTrigger>
            <DialogContent className="glass-card sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Register New Institution</DialogTitle>
                <DialogDescription>
                  Add a new university or department to the system.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Institution Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., IIT Bombay"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location (City/State)</Label>
                  <Input
                    id="location"
                    placeholder="e.g., Mumbai, Maharashtra"
                    value={formData.location}
                    onChange={(e) =>
                      setFormData({ ...formData, location: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="type">Type</Label>
                  <Select
                    value={formData.type}
                    onValueChange={(v) => setFormData({ ...formData, type: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {INSTITUTION_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          <div className="flex items-center gap-2">
                            <type.icon className="h-4 w-4" />
                            {type.label}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <DialogFooter>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full neon-glow"
                  >
                    {isSubmitting ? "Registering..." : "Register Institution"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      {/* Search & Filter */}
      <Card className="glass-card border-border/50">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search institutions by name or location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* List */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
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
                      <p className="text-sm text-muted-foreground flex items-center gap-1 mb-4">
                        <MapPin className="h-3 w-3" />
                        {inst.location}
                      </p>
                    )}
                    <div className="mt-auto pt-4 border-t border-border/40 flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Users</span>
                      <Badge variant="secondary">{inst.user_count || 0}</Badge>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {filteredInstitutions.length === 0 && !loading && (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            No institutions found. Click "Register Institution" to add one.
          </div>
        )}
      </div>
    </div>
  );
};

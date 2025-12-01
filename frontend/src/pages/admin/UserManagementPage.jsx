import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Users,
  Check,
  X,
  Edit,
  Trash2,
  ShieldOff,
  MoreVertical,
} from "lucide-react";
import { userAPI } from "../../services/api";
import { ALL_ROLES } from "../../constants/roles";
import { PageHeader } from "../../components/common/PageHeader";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent } from "../../components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../../components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "../../components/ui/dropdown-menu";
import { formatDateTime } from "../../utils/dateFormat";
import { toast } from "sonner";

export const UserManagementPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionDialog, setActionDialog] = useState({
    open: false,
    user: null,
    action: null,
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await userAPI.listUsers();
      setUsers(response.data || []);
    } catch (error) {
      console.error("Error fetching users:", error);
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId) => {
    try {
      await userAPI.approveUser(userId);
      toast.success("User approved successfully");
      fetchUsers();
    } catch (error) {
      console.error("Approve error:", error);
      toast.error("Failed to approve user");
    }
    setActionDialog({ open: false, user: null, action: null });
  };

  const handleReject = async (userId) => {
    try {
      await userAPI.rejectUser(userId);
      toast.success("User rejected");
      fetchUsers();
    } catch (error) {
      console.error("Reject error:", error);
      toast.error("Failed to reject user");
    }
    setActionDialog({ open: false, user: null, action: null });
  };

  const handleRevoke = async (userId) => {
    try {
      await userAPI.revokeApproval(userId);
      toast.success("User approval revoked");
      fetchUsers();
    } catch (error) {
      console.error("Revoke error:", error);
      toast.error(error.response?.data?.detail || "Failed to revoke approval");
    }
    setActionDialog({ open: false, user: null, action: null });
  };

  const handleDelete = async (userId) => {
    try {
      await userAPI.deleteUser(userId);
      toast.success("User deleted successfully");
      fetchUsers();
    } catch (error) {
      console.error("Delete error:", error);
      toast.error(error.response?.data?.detail || "Failed to delete user");
    }
    setActionDialog({ open: false, user: null, action: null });
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await userAPI.changeRole(userId, newRole);
      toast.success("Role updated successfully");
      fetchUsers();
    } catch (error) {
      console.error("Role change error:", error);
      toast.error(error.response?.data?.detail || "Failed to update role");
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading users..." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="User Management"
        description="Manage user accounts, roles, and permissions"
        icon={Users}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="glass-card border-border/50">
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Total Users</p>
            <p className="text-3xl font-bold mt-2">{users.length}</p>
          </CardContent>
        </Card>
        <Card className="glass-card border-border/50">
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Pending Approval</p>
            <p className="text-3xl font-bold mt-2 text-warning">
              {users.filter((u) => !u.approved).length}
            </p>
          </CardContent>
        </Card>
        <Card className="glass-card border-border/50">
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Active Users</p>
            <p className="text-3xl font-bold mt-2 text-success">
              {users.filter((u) => u.approved).length}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="glass-card border-border/50">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Institution</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Registered</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user, index) => (
                  <motion.tr
                    key={user.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="border-border/40"
                  >
                    <TableCell className="font-medium">{user.email}</TableCell>
                    <TableCell>
                      <Select
                        value={user.role}
                        onValueChange={(value) =>
                          handleRoleChange(user.id, value)
                        }
                      >
                        <SelectTrigger className="w-40">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {ALL_ROLES.map((role) => (
                            <SelectItem key={role} value={role}>
                              {role}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      {user.institution?.name || (
                        <span className="text-muted-foreground">None</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.approved ? "default" : "outline"}>
                        {user.approved ? "Approved" : "Pending"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDateTime(user.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {!user.approved ? (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                setActionDialog({
                                  open: true,
                                  user,
                                  action: "approve",
                                })
                              }
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                setActionDialog({
                                  open: true,
                                  user,
                                  action: "reject",
                                })
                              }
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </>
                        ) : (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button size="sm" variant="outline">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() =>
                                  setActionDialog({
                                    open: true,
                                    user,
                                    action: "revoke",
                                  })
                                }
                              >
                                <ShieldOff className="h-4 w-4 mr-2" />
                                Revoke Approval
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() =>
                                  setActionDialog({
                                    open: true,
                                    user,
                                    action: "delete",
                                  })
                                }
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete User
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </div>
                    </TableCell>
                  </motion.tr>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <AlertDialog
        open={actionDialog.open}
        onOpenChange={(open) => setActionDialog({ ...actionDialog, open })}
      >
        <AlertDialogContent className="glass-card">
          <AlertDialogHeader>
            <AlertDialogTitle>
              {actionDialog.action === "approve" && "Approve User"}
              {actionDialog.action === "reject" && "Reject User"}
              {actionDialog.action === "revoke" && "Revoke Approval"}
              {actionDialog.action === "delete" && "Delete User"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {actionDialog.action === "approve" &&
                `Are you sure you want to approve ${actionDialog.user?.email}? This will grant them access to the system.`}
              {actionDialog.action === "reject" &&
                `Are you sure you want to reject ${actionDialog.user?.email}? This will delete their account.`}
              {actionDialog.action === "revoke" &&
                `Are you sure you want to revoke approval for ${actionDialog.user?.email}? They will lose access to the system.`}
              {actionDialog.action === "delete" &&
                `Are you sure you want to permanently delete ${actionDialog.user?.email}? This action cannot be undone.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className={
                actionDialog.action === "delete" ||
                actionDialog.action === "reject"
                  ? "bg-destructive hover:bg-destructive/90"
                  : ""
              }
              onClick={() => {
                if (actionDialog.action === "approve") {
                  handleApprove(actionDialog.user?.id);
                } else if (actionDialog.action === "reject") {
                  handleReject(actionDialog.user?.id);
                } else if (actionDialog.action === "revoke") {
                  handleRevoke(actionDialog.user?.id);
                } else if (actionDialog.action === "delete") {
                  handleDelete(actionDialog.user?.id);
                }
              }}
            >
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

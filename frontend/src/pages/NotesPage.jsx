import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  StickyNote,
  Plus,
  Search,
  FileText,
  Pin,
  Edit2,
  Trash2,
  Save,
  X,
  ExternalLink,
} from "lucide-react";
import { notesAPI } from "../services/api";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import { formatDateTime } from "../utils/dateFormat";

export const NotesPage = () => {
  const navigate = useNavigate();
  const [notes, setNotes] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [editingNote, setEditingNote] = useState(null);
  const [showNewNote, setShowNewNote] = useState(false);
  const [newNote, setNewNote] = useState({ title: "", content: "" });

  useEffect(() => {
    fetchNotes();
    fetchStats();
  }, []);

  const fetchNotes = async () => {
    try {
      const response = await notesAPI.list();
      setNotes(response.data);
    } catch (error) {
      console.error("Error fetching notes:", error);
      toast.error("Failed to load notes");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await notesAPI.stats();
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchNotes();
      return;
    }

    try {
      const response = await notesAPI.list({ search: searchQuery });
      setNotes(response.data);
    } catch (error) {
      console.error("Error searching notes:", error);
      toast.error("Search failed");
    }
  };

  const handleCreateNote = async () => {
    if (!newNote.content.trim()) {
      toast.error("Note content cannot be empty");
      return;
    }

    try {
      await notesAPI.create({
        title: newNote.title || null,
        content: newNote.content,
      });
      toast.success("Note created successfully");
      setNewNote({ title: "", content: "" });
      setShowNewNote(false);
      fetchNotes();
      fetchStats();
    } catch (error) {
      console.error("Error creating note:", error);
      toast.error("Failed to create note");
    }
  };

  const handleUpdateNote = async (noteId, updates) => {
    try {
      await notesAPI.update(noteId, updates);
      toast.success("Note updated successfully");
      setEditingNote(null);
      fetchNotes();
    } catch (error) {
      console.error("Error updating note:", error);
      toast.error("Failed to update note");
    }
  };

  const handleDeleteNote = async (noteId) => {
    if (!confirm("Are you sure you want to delete this note?")) return;

    try {
      await notesAPI.delete(noteId);
      toast.success("Note deleted successfully");
      fetchNotes();
      fetchStats();
    } catch (error) {
      console.error("Error deleting note:", error);
      toast.error("Failed to delete note");
    }
  };

  const handleTogglePin = async (note) => {
    try {
      await notesAPI.update(note.id, { is_pinned: !note.is_pinned });
      fetchNotes();
    } catch (error) {
      console.error("Error toggling pin:", error);
      toast.error("Failed to update note");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <StickyNote className="h-12 w-12 mx-auto mb-4 text-muted-foreground animate-pulse" />
          <p className="text-muted-foreground">Loading notes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <StickyNote className="h-8 w-8" />
            My Notes
          </h1>
          <p className="text-muted-foreground mt-1">
            Your personal study notes and annotations
          </p>
        </div>
        <Button onClick={() => setShowNewNote(!showNewNote)} className="gap-2">
          {showNewNote ? (
            <>
              <X className="h-4 w-4" /> Cancel
            </>
          ) : (
            <>
              <Plus className="h-4 w-4" /> New Note
            </>
          )}
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Notes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_notes}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Document Notes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.document_notes}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Standalone Notes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.standalone_notes}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Pinned Notes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.pinned_notes}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search notes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <Button onClick={handleSearch}>Search</Button>
            {searchQuery && (
              <Button
                variant="outline"
                onClick={() => {
                  setSearchQuery("");
                  fetchNotes();
                }}
              >
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* New Note Form */}
      {showNewNote && (
        <Card className="border-primary/50">
          <CardContent className="pt-6 space-y-3">
            <input
              type="text"
              placeholder="Note title (optional)"
              value={newNote.title}
              onChange={(e) =>
                setNewNote({ ...newNote, title: e.target.value })
              }
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <textarea
              placeholder="Write your note here..."
              value={newNote.content}
              onChange={(e) =>
                setNewNote({ ...newNote, content: e.target.value })
              }
              rows={6}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowNewNote(false);
                  setNewNote({ title: "", content: "" });
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleCreateNote} className="gap-2">
                <Save className="h-4 w-4" /> Save Note
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes List */}
      {notes.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-16 text-center">
            <StickyNote className="h-16 w-16 mx-auto mb-4 text-muted-foreground/50" />
            <p className="text-lg font-medium mb-2">No notes found</p>
            <p className="text-sm text-muted-foreground mb-4">
              {searchQuery
                ? "Try a different search term"
                : "Create your first note to get started"}
            </p>
            {!searchQuery && (
              <Button onClick={() => setShowNewNote(true)} className="gap-2">
                <Plus className="h-4 w-4" /> Create Note
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {notes.map((note) => (
            <Card
              key={note.id}
              className={`${
                note.is_pinned ? "border-primary/50 bg-primary/5" : ""
              } hover:shadow-lg transition-shadow`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    {editingNote?.id === note.id ? (
                      <input
                        type="text"
                        value={editingNote.title || ""}
                        onChange={(e) =>
                          setEditingNote({
                            ...editingNote,
                            title: e.target.value,
                          })
                        }
                        className="w-full px-2 py-1 bg-background border border-border rounded text-sm font-semibold"
                        placeholder="Note title"
                      />
                    ) : (
                      <CardTitle className="text-base flex items-center gap-2 truncate">
                        {note.is_pinned && (
                          <Pin className="h-4 w-4 text-primary fill-current flex-shrink-0" />
                        )}
                        <span className="truncate">
                          {note.title || "Untitled Note"}
                        </span>
                      </CardTitle>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDateTime(note.updated_at)}
                    </p>
                    {note.document_title && (
                      <Badge
                        variant="secondary"
                        className="mt-2 text-xs cursor-pointer"
                        onClick={() =>
                          navigate(`/documents/${note.document_id}`)
                        }
                      >
                        <FileText className="h-3 w-3 mr-1" />
                        {note.document_title}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handleTogglePin(note)}
                      title={note.is_pinned ? "Unpin" : "Pin"}
                    >
                      <Pin
                        className={`h-4 w-4 ${
                          note.is_pinned ? "fill-current text-primary" : ""
                        }`}
                      />
                    </Button>
                    {editingNote?.id === note.id ? (
                      <>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() =>
                            handleUpdateNote(note.id, {
                              title: editingNote.title,
                              content: editingNote.content,
                            })
                          }
                        >
                          <Save className="h-4 w-4 text-green-600" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => setEditingNote(null)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() =>
                            setEditingNote({
                              id: note.id,
                              title: note.title,
                              content: note.content,
                            })
                          }
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-600 hover:text-red-700"
                          onClick={() => handleDeleteNote(note.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {editingNote?.id === note.id ? (
                  <textarea
                    value={editingNote.content}
                    onChange={(e) =>
                      setEditingNote({
                        ...editingNote,
                        content: e.target.value,
                      })
                    }
                    rows={6}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  />
                ) : (
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap line-clamp-6">
                    {note.content}
                  </p>
                )}
                {note.document_id && !editingNote && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="mt-3 gap-2 text-xs"
                    onClick={() => navigate(`/documents/${note.document_id}`)}
                  >
                    <ExternalLink className="h-3 w-3" />
                    View Document
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

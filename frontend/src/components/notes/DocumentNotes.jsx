import { useState, useEffect } from "react";
import { Plus, Save, Trash2, Pin, Edit2, X } from "lucide-react";
import { notesAPI } from "../../services/api";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { toast } from "sonner";
import { formatDateTime } from "../../utils/dateFormat";

export const DocumentNotes = ({ documentId }) => {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingNote, setEditingNote] = useState(null);
  const [newNote, setNewNote] = useState({ title: "", content: "" });
  const [showNewNote, setShowNewNote] = useState(false);

  useEffect(() => {
    fetchNotes();
  }, [documentId]);

  const fetchNotes = async () => {
    try {
      const response = await notesAPI.list({ document_id: documentId });
      setNotes(response.data);
    } catch (error) {
      console.error("Error fetching notes:", error);
      toast.error("Failed to load notes");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNote = async () => {
    if (!newNote.content.trim()) {
      toast.error("Note content cannot be empty");
      return;
    }

    try {
      await notesAPI.create({
        document_id: documentId,
        title: newNote.title || null,
        content: newNote.content,
      });
      toast.success("Note created successfully");
      setNewNote({ title: "", content: "" });
      setShowNewNote(false);
      fetchNotes();
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
      <div className="text-center py-8">
        <p className="text-muted-foreground">Loading notes...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Add Button */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">My Notes</h3>
          <p className="text-sm text-muted-foreground">
            Private notes visible only to you
          </p>
        </div>
        <Button
          onClick={() => setShowNewNote(!showNewNote)}
          size="sm"
          className="gap-2"
        >
          {showNewNote ? (
            <>
              <X className="h-4 w-4" /> Cancel
            </>
          ) : (
            <>
              <Plus className="h-4 w-4" /> Add Note
            </>
          )}
        </Button>
      </div>

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
              rows={4}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowNewNote(false);
                  setNewNote({ title: "", content: "" });
                }}
              >
                Cancel
              </Button>
              <Button size="sm" onClick={handleCreateNote} className="gap-2">
                <Save className="h-4 w-4" /> Save Note
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes List */}
      {notes.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-2">No notes yet</p>
            <p className="text-sm text-muted-foreground">
              Click "Add Note" to create your first note
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {notes.map((note) => (
            <Card
              key={note.id}
              className={`${
                note.is_pinned ? "border-primary/50 bg-primary/5" : ""
              }`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
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
                      <CardTitle className="text-base flex items-center gap-2">
                        {note.is_pinned && (
                          <Pin className="h-4 w-4 text-primary fill-current" />
                        )}
                        {note.title || "Untitled Note"}
                      </CardTitle>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDateTime(note.updated_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
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
                    rows={4}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  />
                ) : (
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {note.content}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

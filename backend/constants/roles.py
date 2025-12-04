"""Role constants for consistent use across the application"""

# Role definitions - use lowercase with underscores for database
DEVELOPER = "developer"
MINISTRY_ADMIN = "ministry_admin"  # Generalized from MINISTRY_ADMIN
UNIVERSITY_ADMIN = "university_admin"
DOCUMENT_OFFICER = "document_officer"
STUDENT = "student"
PUBLIC_VIEWER = "public_viewer"

# Backward compatibility alias (deprecated)
MINISTRY_ADMIN = MINISTRY_ADMIN

# Role groups for permission checking
ADMIN_ROLES = [DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN]
DOCUMENT_MANAGER_ROLES = [DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN, DOCUMENT_OFFICER]
VIEWER_ROLES = [STUDENT, PUBLIC_VIEWER]
ALL_ROLES = [DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN, DOCUMENT_OFFICER, STUDENT, PUBLIC_VIEWER]

# Role display names for API responses
ROLE_DISPLAY_NAMES = {
    DEVELOPER: "Developer",
    MINISTRY_ADMIN: "Ministry Admin",
    UNIVERSITY_ADMIN: "University Admin",
    DOCUMENT_OFFICER: "Document Officer",
    STUDENT: "Student",
    PUBLIC_VIEWER: "Public Viewer"
}

# ROLES = list(ROLE_DISPLAY_NAMES.keys())


# Visibility levels for documents
VISIBILITY_PUBLIC = "public"
VISIBILITY_INSTITUTION = "institution_only"
VISIBILITY_RESTRICTED = "restricted"
VISIBILITY_CONFIDENTIAL = "confidential"

VISIBILITY_LEVELS = [
    VISIBILITY_PUBLIC,
    VISIBILITY_INSTITUTION,
    VISIBILITY_RESTRICTED,
    VISIBILITY_CONFIDENTIAL
]
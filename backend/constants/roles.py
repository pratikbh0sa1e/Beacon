ROLES = {
    "DEVELOPER": "Developer",
    "MOE_ADMIN": "MoE Admin",
    "UNIVERSITY_ADMIN": "University Admin",
    "DOCUMENT_OFFICER": "Document Officer",
    "STUDENT_VIEWER": "Student Viewer",
    "PUBLIC_VIEWER": "Public Viewer",
}

ADMIN_ROLES = [
    ROLES["DEVELOPER"],
    ROLES["MOE_ADMIN"],
    ROLES["UNIVERSITY_ADMIN"],
]

DOCUMENT_MANAGER_ROLES = [
    ROLES["DEVELOPER"],
    ROLES["MOE_ADMIN"],
    ROLES["UNIVERSITY_ADMIN"],
    ROLES["DOCUMENT_OFFICER"],
]

VIEWER_ROLES = [
    ROLES["STUDENT_VIEWER"],
    ROLES["PUBLIC_VIEWER"],
]

ALL_ROLES = list(ROLES.values())

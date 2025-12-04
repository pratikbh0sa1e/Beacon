// Role constants - match backend exactly
export const ROLES = {
  DEVELOPER: "developer",
  MINISTRY_ADMIN: "ministry_admin", // Generalized from MINISTRY_ADMIN
  UNIVERSITY_ADMIN: "university_admin",
  DOCUMENT_OFFICER: "document_officer",
  STUDENT: "student",
  PUBLIC_VIEWER: "public_viewer",
};

// Backward compatibility alias (deprecated)
export const MINISTRY_ADMIN = ROLES.MINISTRY_ADMIN;

// Display names for UI
export const ROLE_DISPLAY_NAMES = {
  developer: "Developer",
  ministry_admin: "Ministry Admin",
  university_admin: "University Admin",
  document_officer: "Document Officer",
  student: "Student",
  public_viewer: "Public Viewer",
};

// Helper to get display name
export const getRoleDisplayName = (role) => ROLE_DISPLAY_NAMES[role] || role;

// Role groups
export const ADMIN_ROLES = [
  ROLES.DEVELOPER,
  ROLES.MINISTRY_ADMIN,
  ROLES.UNIVERSITY_ADMIN,
];

export const DOCUMENT_MANAGER_ROLES = [
  ROLES.DEVELOPER,
  ROLES.MINISTRY_ADMIN,
  ROLES.UNIVERSITY_ADMIN,
  ROLES.DOCUMENT_OFFICER,
];

export const VIEWER_ROLES = [ROLES.STUDENT, ROLES.PUBLIC_VIEWER];

export const ALL_ROLES = Object.values(ROLES);

// Roles that can be assigned/changed (excludes developer)
export const MANAGEABLE_ROLES = [
  ROLES.MINISTRY_ADMIN,
  ROLES.UNIVERSITY_ADMIN,
  ROLES.DOCUMENT_OFFICER,
  ROLES.STUDENT,
  ROLES.PUBLIC_VIEWER,
];

// Document categories
export const DOCUMENT_CATEGORIES = [
  "Circular",
  "Notice",
  "Act",
  "Regulation",
  "Scheme",
  "Draft",
  "Handbook",
];

// Visibility options - VALUES match backend exactly
export const VISIBILITY_OPTIONS = [
  { value: "public", label: "Public - Visible to everyone" },
  {
    value: "institution_only",
    label: "Institution Only - Restricted to institution members",
  },
  { value: "restricted", label: "Restricted - Limited access" },
  { value: "confidential", label: "Confidential - Highly restricted" },
];

// Helper to get visibility label
export const getVisibilityLabel = (value) => {
  const option = VISIBILITY_OPTIONS.find((opt) => opt.value === value);
  return option ? option.label : value;
};

// Departments
export const DEPARTMENTS = [
  "Administration",
  "Academic Affairs",
  "Student Services",
  "Finance",
  "Human Resources",
  "IT Services",
  "Research & Development",
  "Legal",
  "Library",
  "Admissions",
];

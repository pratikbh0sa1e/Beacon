/**
 * BEACON - Feature Flags Configuration
 * Controls which features are visible in each SIH round
 *
 * Usage:
 * - Round 1 (MVP): Set ROUND = 1
 * - Round 2 (Advanced): Set ROUND = 2
 * - Round 3 (Production): Set ROUND = 3
 */

// ============================================
// CHANGE THIS VALUE BASED ON CURRENT ROUND
// ============================================
const CURRENT_ROUND = 1; // Change to 1, 2, or 3

// ============================================
// FEATURE FLAGS BY ROUND
// ============================================

const FEATURE_FLAGS = {
  // ========== ROUND 1: MVP (Core Features) ==========
  ROUND_1: {
    // Authentication & Users
    AUTH_LOGIN: true,
    AUTH_REGISTER: true,
    AUTH_EMAIL_VERIFICATION: true,

    // Basic Roles (Developer, Admin, Student only)
    ROLE_DEVELOPER: true,
    ROLE_MINISTRY_ADMIN: true,
    ROLE_STUDENT: true,
    ROLE_UNIVERSITY_ADMIN: false, // Hidden in Round 1
    ROLE_DOCUMENT_OFFICER: false, // Hidden in Round 1

    // Document Management
    DOCUMENT_UPLOAD: true,
    DOCUMENT_LIST: true,
    DOCUMENT_SEARCH: true,
    DOCUMENT_VIEW: true,
    DOCUMENT_DOWNLOAD: true,
    DOCUMENT_DELETE: true,

    // AI & RAG
    AI_CHAT: true,
    AI_CITATIONS: true,
    RAG_SEARCH: true,

    // UI Components
    DASHBOARD: true,
    SIDEBAR: true,
    HEADER: true,

    // DISABLED FEATURES (Hidden in Round 1)
    VOICE_QUERY: false,
    NOTIFICATIONS: false,
    APPROVAL_WORKFLOW: false,
    USER_APPROVAL: false,
    DOCUMENT_APPROVAL: false,
    ANALYTICS: false,
    EXTERNAL_DATA_SYNC: false,
    BOOKMARKS: false,
    NOTES: false,
    DOCUMENT_CHAT: false,
    INSTITUTION_MANAGEMENT: false,
    METADATA_EXTRACTION: false,
    MULTILINGUAL: false,
    SYSTEM_HEALTH: false,
  },

  // ========== ROUND 2: Advanced Prototype ==========
  ROUND_2: {
    // All Round 1 features
    ...this.ROUND_1,

    // Enable all roles
    ROLE_UNIVERSITY_ADMIN: true,
    ROLE_DOCUMENT_OFFICER: true,

    // Approval Workflows
    APPROVAL_WORKFLOW: true,
    USER_APPROVAL: true,
    DOCUMENT_APPROVAL: true,

    // Notifications
    NOTIFICATIONS: true,
    NOTIFICATION_PANEL: true,
    NOTIFICATION_TOAST: true,

    // Enhanced Features
    METADATA_EXTRACTION: true,
    MULTILINGUAL: true,
    VOICE_QUERY: true,

    // Basic Bookmarks & Notes
    BOOKMARKS: true,
    NOTES: true,

    // Institution Management
    INSTITUTION_MANAGEMENT: true,

    // STILL DISABLED (Round 3 only)
    EXTERNAL_DATA_SYNC: false,
    ANALYTICS: false,
    DOCUMENT_CHAT: false,
    SYSTEM_HEALTH: false,
  },

  // ========== ROUND 3: Production Ready ==========
  ROUND_3: {
    // All Round 2 features
    ...this.ROUND_2,

    // External Data Integration
    EXTERNAL_DATA_SYNC: true,
    DATA_SOURCE_REQUEST: true,
    DATA_SOURCE_APPROVAL: true,
    SCHEDULED_SYNC: true,

    // Analytics & Insights
    ANALYTICS: true,
    ANALYTICS_DASHBOARD: true,
    ACTIVITY_HEATMAP: true,
    USER_BEHAVIOR: true,

    // Advanced Collaboration
    DOCUMENT_CHAT: true,
    DOCUMENT_CHAT_ROOMS: true,
    REAL_TIME_MESSAGING: true,

    // System Monitoring
    SYSTEM_HEALTH: true,
    SYSTEM_HEALTH_DASHBOARD: true,
    COMPONENT_MONITORING: true,

    // Advanced Features
    DOCUMENT_VERSIONING: true,
    DOCUMENT_EXPIRY: true,
    DOWNLOAD_RESTRICTIONS: true,
    AUDIT_LOGS: true,
  },
};

// ============================================
// EXPORT CURRENT ROUND'S FEATURES
// ============================================

const getCurrentFeatures = () => {
  switch (CURRENT_ROUND) {
    case 1:
      return FEATURE_FLAGS.ROUND_1;
    case 2:
      return FEATURE_FLAGS.ROUND_2;
    case 3:
      return FEATURE_FLAGS.ROUND_3;
    default:
      return FEATURE_FLAGS.ROUND_1;
  }
};

export const features = getCurrentFeatures();
export const currentRound = CURRENT_ROUND;

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Check if a feature is enabled
 * @param {string} featureName - Name of the feature flag
 * @returns {boolean}
 */
export const isFeatureEnabled = (featureName) => {
  return features[featureName] === true;
};

/**
 * Get list of enabled features
 * @returns {string[]}
 */
export const getEnabledFeatures = () => {
  return Object.keys(features).filter((key) => features[key] === true);
};

/**
 * Get list of disabled features
 * @returns {string[]}
 */
export const getDisabledFeatures = () => {
  return Object.keys(features).filter((key) => features[key] === false);
};

/**
 * Check if current round is at least the specified round
 * @param {number} round - Round number (1, 2, or 3)
 * @returns {boolean}
 */
export const isRoundOrHigher = (round) => {
  return CURRENT_ROUND >= round;
};

// ============================================
// ROUND DESCRIPTIONS (for UI display)
// ============================================

export const ROUND_INFO = {
  1: {
    name: "Round 1: MVP",
    description: "Core functionality - Upload, Search, AI Answers",
    percentage: "35-40%",
    color: "blue",
  },
  2: {
    name: "Round 2: Advanced Prototype",
    description: "Workflows, Approvals, Multilingual, Voice",
    percentage: "75-80%",
    color: "purple",
  },
  3: {
    name: "Round 3: Production Ready",
    description: "Analytics, External Sync, Chat Rooms, Monitoring",
    percentage: "95-100%",
    color: "green",
  },
};

export const currentRoundInfo = ROUND_INFO[CURRENT_ROUND];

// ============================================
// CONSOLE LOG (for debugging)
// ============================================

if (import.meta.env.DEV) {
  console.log(`🚀 BEACON - ${currentRoundInfo.name}`);
  console.log(`📊 Implementation: ${currentRoundInfo.percentage}`);
  console.log(`✅ Enabled Features:`, getEnabledFeatures().length);
  console.log(`❌ Disabled Features:`, getDisabledFeatures().length);
}

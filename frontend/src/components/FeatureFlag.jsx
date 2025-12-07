import { isFeatureEnabled } from "../config/featureFlags";

/**
 * FeatureFlag Component
 * Conditionally renders children based on feature flag
 *
 * Usage:
 * <FeatureFlag feature="VOICE_QUERY">
 *   <VoiceQueryButton />
 * </FeatureFlag>
 */
const FeatureFlag = ({ feature, children, fallback = null }) => {
  if (isFeatureEnabled(feature)) {
    return <>{children}</>;
  }
  return fallback;
};

export default FeatureFlag;

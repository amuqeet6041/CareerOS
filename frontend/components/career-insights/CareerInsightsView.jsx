import CareerSnapshot from "./CareerSnapshot";
import StrengthsSection from "./StrengthsSection";
import SkillGapsSection from "./SkillGapsSection";
import CareerDirections from "./CareerDirections";
import AICareerInsights from "./AICareerInsights";
import ActionPlanSection from "./ActionPlanSection";

export default function CareerInsightsView({ data }) {
  return (
    <div className="space-y-6">
      <CareerSnapshot summary={data.profile_summary} />
      <StrengthsSection strengths={data.strengths ?? []} />
      <SkillGapsSection skillGaps={data.skill_gaps ?? []} />
      <CareerDirections directions={data.career_directions ?? []} />
      <AICareerInsights ai={data.ai_insights} />
      <ActionPlanSection
        actionPlan={data.action_plan ?? []}
        resumeSuggestions={data.resume_suggestions ?? []}
      />
    </div>
  );
}
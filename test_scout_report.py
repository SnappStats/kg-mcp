import traceback
from scout_report_agent.agent import generate_scout_report
from scout_report_agent.scout_report_schema import ScoutReport


def generate_report(player_name: str, graph_id: str = "test_graph"):
    print(f"Generating scout report for {player_name}...\n")
    print("=" * 80)

    try:
        report = generate_scout_report(graph_id, player_name)
        formatted_report = format_scout_report(report)
        print(formatted_report)
        print("\n" + "=" * 80)
        return formatted_report
    except Exception as e:
        print(f"Error generating report: {e}")
        traceback.print_exc()
        print("\n" + "=" * 80)
        return ""


def format_scout_report(report: ScoutReport) -> str:
    output = []

    output.append(f"# SCOUT REPORT: {report.player_name}")
    output.append(f"**Position:** {report.position} | **Class:** {report.graduation_class}")
    output.append(f"**School:** {report.school_name} ({report.location})")
    if report.twitter_handle:
        output.append(f"**Twitter:** {report.twitter_handle}")
    if report.previous_schools:
        output.append(f"**Previous Schools:** {report.previous_schools}")
    output.append("")

    if report.executive_summary:
        output.append("## Executive Summary")
        output.append(report.executive_summary)
        output.append("")

    if report.physical_profile.measurements or report.physical_profile.athletic_testing:
        output.append("## Physical & Athletic Profile")
        if report.physical_profile.measurements:
            output.append(f"**Measurements:** {report.physical_profile.measurements}")
        if report.physical_profile.athletic_testing:
            output.append(f"**Testing:** {report.physical_profile.athletic_testing}")
        if report.physical_profile.physical_development:
            output.append(f"**Development:** {report.physical_profile.physical_development}")
        output.append("")

    if any([report.recruiting_profile.star_ratings, report.recruiting_profile.scholarship_offers]):
        output.append("## Recruiting Profile")
        if report.recruiting_profile.star_ratings:
            output.append(f"**Rankings:** {report.recruiting_profile.star_ratings}")
        if report.recruiting_profile.scholarship_offers:
            output.append(f"**Offers:** {report.recruiting_profile.scholarship_offers}")
        if report.recruiting_profile.latest_offer:
            output.append(f"**Latest Offer:** {report.recruiting_profile.latest_offer}")
        if report.recruiting_profile.visits:
            output.append(f"**Visits:** {report.recruiting_profile.visits}")
        if report.recruiting_profile.school_interest:
            output.append(f"**Interest:** {report.recruiting_profile.school_interest}")
        output.append("")

    if report.statistics.season_stats:
        output.append("## On-Field Performance")
        output.append(f"**Stats:**\n{report.statistics.season_stats}")
        if report.statistics.team_records:
            output.append(f"\n**Team Records:** {report.statistics.team_records}")
        if report.statistics.competition_level:
            output.append(f"**Competition:** {report.statistics.competition_level}")
        output.append("")

    if report.rankings_accolades.accolades:
        output.append("## Accolades")
        output.append(report.rankings_accolades.accolades)
        output.append("")

    if any([report.intangibles.character_leadership, report.intangibles.academic_profile, report.intangibles.twitter_review]):
        output.append("## Intangibles")
        if report.intangibles.character_leadership:
            output.append(f"**Character & Leadership:** {report.intangibles.character_leadership}")
        if report.intangibles.twitter_review:
            output.append(f"**Social Media:** {report.intangibles.twitter_review}")
        if report.intangibles.academic_profile:
            output.append(f"**Academics:** {report.intangibles.academic_profile}")
        output.append("")

    if report.sources:
        output.append("## Sources")
        for source in report.sources:
            output.append(f"[{source.number}] {source.title} ({source.url})")
        output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    player_name = input("Enter player name (or press Enter for 'Caleb Williams'): ").strip()
    if not player_name:
        player_name = "Caleb Williams"

    report = generate_report(player_name)

    save = input("\nSave report to file? (y/n): ").strip().lower()
    if save == 'y':
        filename = f"scout_report_{player_name.replace(' ', '_')}.md"
        with open(filename, 'w') as f:
            f.write(report)
        print(f"Report saved to {filename}")

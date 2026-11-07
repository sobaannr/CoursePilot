"""Generate the 3-page report and 1-page updated proposal from measured outputs."""
import argparse
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coursepilot.catalogue import ROOT, load_catalogue, fingerprint
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.graphics.shapes import Drawing, String, Rect
from pypdf import PdfReader

NAVY=colors.HexColor("#172B4D")
TEAL=colors.HexColor("#087F8C")
GRAY=colors.HexColor("#53647B")
PALE=colors.HexColor("#EAF0F6")
STYLES=getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="CPTitle",fontName="Helvetica-Bold",fontSize=25,leading=29,textColor=NAVY,spaceAfter=9))
STYLES.add(ParagraphStyle(name="CPSub",fontName="Helvetica",fontSize=10,leading=14,textColor=GRAY,spaceAfter=10))
STYLES.add(ParagraphStyle(name="CPH",fontName="Helvetica-Bold",fontSize=12,leading=16,textColor=TEAL,spaceBefore=10,spaceAfter=6))
STYLES.add(ParagraphStyle(name="CPBody",fontName="Helvetica",fontSize=9.4,leading=13,textColor=NAVY,spaceAfter=7))
STYLES.add(ParagraphStyle(name="CPSmall",fontName="Helvetica",fontSize=8,leading=11,textColor=GRAY,spaceAfter=5))
STYLES.add(ParagraphStyle(name="CPCell",fontName="Helvetica",fontSize=8.5,leading=11,textColor=NAVY))

def p(text,style="CPBody"):
    return Paragraph(text,STYLES[style])

def heading(text): return p(text,"CPH")

def table(rows,widths):
    table=Table([[p(escape(str(cell)),"CPCell") for cell in row] for row in rows],colWidths=widths,hAlign="LEFT",repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),PALE),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),.7,TEAL),("LINEBELOW",(0,1),(-1,-1),.25,colors.HexColor("#DCE3EC")),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    return table

def footer(canvas,doc):
    canvas.setStrokeColor(TEAL);canvas.setLineWidth(1)
    canvas.line(42, A4[1]-30, A4[0]-42, A4[1]-30)
    canvas.setFont("Helvetica",8);canvas.setFillColor(GRAY)
    canvas.drawString(42,25,"CoursePilot | Recommender System | FAST-NUCES Karachi | Fall 2026")
    canvas.drawRightString(A4[0]-42,25,str(doc.page))

TEAM="Sobaan Nayyar | Individual implementation"

def bar_chart(summary):
    drawing=Drawing(505,134)
    for i,row in enumerate(summary[:4]):
        value=row["ndcg_at_k"]["mean"] or 0
        y=103-i*28
        drawing.add(String(0,y+4,row["method"],fontName="Helvetica",fontSize=9,fillColor=NAVY))
        drawing.add(Rect(67,y,375,16,fillColor=PALE,strokeColor=None))
        drawing.add(Rect(67,y,375*value,16,fillColor=TEAL,strokeColor=None))
        drawing.add(String(453,y+4,f"{value:.3f}",fontName="Helvetica-Bold",fontSize=9,fillColor=NAVY))
    return drawing

def build_report(metrics, human, feedback, out):
    story=[p("CoursePilot","CPTitle"),p("Explainable elective recommendation with transparent evaluation","CPSub"),
           p(TEAM,"CPSmall"),p("Instructor: Syed Zain Ul Hassan | Implementation report | 11 October 2026","CPSmall"),
           heading("1  Introduction"),
           p("CoursePilot ranks elective candidates using a student's selected interests, optional importance weights, a free-text learning goal and completed course codes. The system excludes completed courses and courses failing the prerequisites listed in its source. Every recommendation includes the exact matching-term contributions rather than generated explanatory prose."),
           p("The deliverable comprises a Streamlit interface, a reusable Python ranker, a stateless FastAPI service, source-tracked JSON/CSV data, automated checks and a reproducible evaluation command. The main model remains inherently transparent; no LLM or neural embedding model is required."),
           heading("2  Dataset details"),
           table([["Field","Implemented scope"],["Source","FAST-NUCES national computing catalogue, 2026; retrieved 11 October 2026 [1]."],["Catalogue","74 entries: 15 core courses, 54 project candidate electives, 5 referenced lab components."],["Metadata","Codes, titles, prerequisite text, source pages and checksum; curated summaries and topic tags."],["Limitations","Karachi batch applicability and offerings are unverified. Candidate roles are project-curated; absent credits remain null."]],[86,425]),
           Spacer(1,7),
           p("The source labels many specialization courses as core. We preserve these source labels separately and do not claim our candidate pool is an approved batch elective list. N/A means no prerequisite listed in that source, not an official waiver. The five lab labels are derived from explicit prerequisite references. These restrictions are visible in the app."),
           heading("3  Explanation of the model"),
           p("Course titles and curated descriptions undergo tokenization, stop-word removal, alias expansion and conservative domain-lexicon lemmatization. scikit-learn builds sublinear-TF, smoothed-IDF, L2-normalized vectors x. The normalized free-text vector and normalized weighted-interest vector are combined and normalized into profile p."),
           p("<b>TF-IDF score:</b> s = x dot p. Term t contributes exactly x[t] * p[t]; all term products reconstruct the score. <b>Hybrid extension:</b> 0.75s + 0.25h, where h is the fraction of selected interest weight covered by a course's tags. Without interests, text receives full weight. Scores lie in [0,1] and are not probabilities."),
           p("Eligibility is applied before scoring. Prerequisites are an AND of OR groups; required labs remain separate. Unknown prerequisite status is excluded. Zero-evidence deterministic results are omitted; ties use course code. All baselines use the same eligibility pool."),
           PageBreak(),
           p("Experiments & results","CPTitle"),
           heading("4  Details of experiments"),
           p("The included diagnostic benchmark contains 18 authored fictional profiles: six development and twelve test scenarios. Each candidate receives an explicit grade 0-3; grades 2-3 count as relevant. Authors know the catalogue, and labels are not independent student observations. The partition demonstrates the workflow; no tuning or unbiased generalization claim is made."),
           p("We compare TF-IDF, the fixed-weight hybrid, keyword overlap and random ranking. Random uses seeds 0-19; metrics are averaged within profile before aggregation. Text-only and topics-only ablations isolate the input signals. K=5. IDF is fitted on the fixed catalogue, never on relevance labels."),
           p("Precision@5 divides relevant returns by five, including unfilled slots. Recall@5 uses all relevant eligible courses. NDCG@5 uses gain 2^grade-1 discounted by log2(rank+1), normalized by the ideal eligible order. Zero-denominator recall/NDCG cases are excluded with counts recorded. Missing judgments are rejected. Real participants cannot appear in both splits."),
           heading("5  Results and discussion"),
           p("<b>Table 1. Authored diagnostic scenarios only; not human-study results.</b>","CPSmall")]
    rows=[["Method","P@5","R@5","NDCG@5","Violations"]]
    for row in metrics["summary"]:
        rows.append([row["method"],*[f"{row[key]['mean']:.3f}" if row[key]["mean"] is not None else "N/A" for key in ("precision_at_k","recall_at_k","ndcg_at_k")],row["violations"]])
    story += [table(rows,[145,90,90,96,90]),Spacer(1,10),bar_chart(metrics["summary"]),
              p("Figure 1. NDCG@5 on the twelve fictional test scenarios (higher is better).","CPSmall")]
    results={r["method"]:r for r in metrics["summary"]}
    delta=results["hybrid"]["ndcg_at_k"]["mean"]-results["tfidf"]["ndcg_at_k"]["mean"]
    story += [p(f"The hybrid changes mean NDCG@5 by {delta:+.3f} relative to TF-IDF on these fixtures. All measured methods have zero constraint violations under the encoded catalogue rules. This does not verify the rules against an individual student's batch policy. Descriptive participant-bootstrap intervals and per-profile outputs are saved in metrics.json and per_profile.csv."),
              p("Scores are optimistic because scenarios and labels were authored with knowledge of the course content and tags. The small catalogue and limited relevant-item counts constrain Precision@5. Random's reported catalogue coverage unions 20 seeds and must not be compared directly with a single deterministic run. Measured latency is local in-process scoring, not a production throughput test."),
              PageBreak(),p("Validation & next steps","CPTitle"),
              heading("Human evaluation")]
    if human:
        story.append(p(f"An imported human benchmark contains {human['participants']} test participants and {human['profiles']} profiles. Table 2 reports the evaluated held-out split. The team must document the actual recruitment dates, sampling and consent procedure alongside this report."))
        rows=[["Method","P@5","R@5","NDCG@5"]]
        for row in human["summary"][:4]:
            rows.append([row["method"],*[f"{row[k]['mean']:.3f}" if row[k]['mean'] is not None else "N/A" for k in ("precision_at_k","recall_at_k","ndcg_at_k")]])
        story.append(table(rows,[151,120,120,120]))
    else:
        story.append(p("<b>Pending: no real student ratings have been collected in this implementation session.</b> The UI provides consent text, anonymous profile export, randomized unranked judgment packets and 1-5 shortlist feedback. The human-study importer rejects incomplete judgments, duplicates, missing consent and catalogue-version mismatches. No synthetic response is presented as human evidence."))
        story.append(p("Planned procedure: recruit consenting students, designate development/test participants before examining responses, freeze the system, and collect relevance ratings before showing rankings. Map ratings 1/2 to grade 0, 3 to 1, 4 to 2 and 5 to 3. Collect post-ranking explanation/relevance feedback separately. A 20-30 student target is practical guidance, not a statistical power guarantee."))
    if feedback:
        for row in feedback["summary"]:
            rating=row["relevance_1_to_5"]
            story.append(p(f"Post-ranking {escape(row['method'])} feedback: {row['participants']} participants, {row['ratings']} ratings, participant-mean relevance {rating['mean']:.2f}/5 (bootstrap interval {rating['low']:.2f}-{rating['high']:.2f}). This pilot is unblinded and is not used as a complete relevance set."))
    else:
        story.append(p("Post-ranking 1-5 feedback: not yet available. The summarizer reports participant-averaged relevance and uncertainty from actual consented exports; partial shortlist feedback is never used to compute catalogue Recall@K."))
    story += [heading("Verification and reproducibility"),
              p("The test suite covers source/schema integrity, completed-course and prerequisite exclusions, separate lab requirements, exact score reconstruction, empty/OOV profiles, deterministic seeds, invalid API requests, metric hand calculations, label completeness, split leakage, study consent and the Streamlit recommendation/study flows. See docs/VERIFICATION.md for the executed checks and environment."),
              p("Run <font name='Courier'>python -m pytest -q</font>, then <font name='Courier'>python -m coursepilot.evaluate</font>. Start the interface with <font name='Courier'>python -m streamlit run app.py</font>. Regenerate this report using <font name='Courier'>python scripts/build_report.py</font>. Optional human metrics can be supplied after the real study. Dataset fingerprint: " + metrics["dataset_version"] + "."),
              heading("Limitations and contribution"),
              p("The contribution is an inspectable application combining content relevance, explicit interest weighting, source-tracked constraints and a reproducible comparison. It is not a novel algorithm. The system lacks behavioral interactions, confirmed current offerings, batch-specific rules and verified missing credits. Conservative vocabulary matching can miss synonyms; curation may introduce bias. Recommendations support exploration and do not determine registration eligibility."),
              p("Next steps are to validate the candidate pool with the department, collect and analyze real student judgments, review failure cases and then consider an instructor-approved embedding comparison. No public deployment or measured student benefit is claimed."),
              heading("Attribution and integrity"),
              p("Substantial OpenAI Codex assistance was used for implementation, curation, tests and documentation. The developer must review the work, follow course assistance rules and report their actual contributions. Authored scenarios are disclosed. The undertaking remains subject to developer review; no signatures or student responses were generated."),
              p("<b>References.</b> [1] FAST-NUCES, Computing Course Catalogue (2026), linked from <link href='https://nu.edu.pk/Admissions/ProgramOffered' color='#087F8C'>nu.edu.pk/Admissions/ProgramOffered</link>; source pages are recorded per course. [2] scikit-learn, <link href='https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction' color='#087F8C'>Text feature extraction</link>. [3] Google Developers, <link href='https://developers.google.com/machine-learning/recommendation/overview/types' color='#087F8C'>Recommendation systems overview</link>. Source briefs: provided CoursePilot proposal and Call for Proposals, Fall 2026.","CPSmall")]
    SimpleDocTemplate(str(out),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=43,bottomMargin=43,title="CoursePilot Project Report",author="Sobaan Nayyar (AI-assisted)").build(story,onFirstPage=footer,onLaterPages=footer)

def build_proposal(out):
    story=[p("CoursePilot","CPTitle"),p("Updated project proposal | FAST-NUCES Karachi | Fall 2026","CPSub"),
        p("Course: Recommender System | Instructor: Syed Zain Ul Hassan","CPSmall"),
        heading("1  Project developer"),
        table([["Developer","Contribution"],["Sobaan Nayyar","Individual implementation"]],[330,181]),
        heading("2  Introduction"),
        p("CoursePilot is an explainable content-based elective recommender using student interests, free-text goals and completed courses. Each suggestion includes matching terms and transparent score components."),
        heading("3  Dataset"),
        p("A curated subset of the official FAST-NUCES 2026 computing catalogue: 74 entries comprising 54 candidate electives, 15 core courses and five lab references. Metadata includes codes, titles, descriptions, tags, prerequisites and source pages. Karachi batch roles and offerings require confirmation; credit hours absent in the source are explicitly unknown."),
        heading("4  Ratings / recommendation target"),
        p("Return a ranked top-K elective list with matching scores in [0,1], excluding completed courses and unmet listed prerequisites. Profiles combine optional weighted interests, free-text topics and manually entered completed course codes. Scores are not predicted grades or probabilities."),
        heading("5  Techniques and evaluation"),
        p("Tokenization, stop-word removal and conservative domain lemmatization; TF-IDF with cosine similarity and a weighted profile; hard prerequisite filtering; exact term-contribution explanations. An additive topic-score variant extends the baseline while retaining transparency."),
        p("Compare TF-IDF and the topic-weighted variant against keyword and seeded random baselines using Precision@5, Recall@5 and NDCG@5; include text/topic ablations. Authored diagnostic labels are separated from real student judgments. Conduct a consented 1-5 relevance study before claiming human performance. Implement with Python, scikit-learn, Pandas and Streamlit, with a tested FastAPI interface."),
        heading("6  Undertaking (draft for developer review)"),
        p("We undertake to report data, results, external resources and assistance truthfully; not fabricate student responses or contributions; and follow the instructor's permitted-assistance rules. Substantial AI assistance used in preparing this implementation will be disclosed. The developer will review and understand the work before submission."),
        p("Updated scope reflects public-source limitations and the implemented system. This document has not been signed or submitted as a course submission.","CPSmall")]
    SimpleDocTemplate(str(out),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=43,bottomMargin=43,title="CoursePilot Updated Proposal",author="Sobaan Nayyar (AI-assisted)").build(story,onFirstPage=footer,onLaterPages=footer)

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--human-metrics",type=Path);parser.add_argument("--feedback-summary",type=Path)
    args=parser.parse_args()
    metrics=json.loads((ROOT/"output/evaluation/metrics.json").read_text())
    version=fingerprint(load_catalogue())
    if metrics["dataset_version"]!=version or metrics["label_origin"]!="authored_demo":
        raise ValueError("Default report requires current, explicitly authored demo results")
    human=json.loads(args.human_metrics.read_text()) if args.human_metrics else None
    feedback=json.loads(args.feedback_summary.read_text()) if args.feedback_summary else None
    for data,origin in [(human,"human"),(feedback,"human_feedback")]:
        if data and (data.get("label_origin")!=origin or data.get("dataset_version")!=version):
            raise ValueError("Human results must have correct origin and catalogue version")
    if human and (human.get("split")!="test" or human.get("k")!=5):
        raise ValueError("Report table expects held-out test results at K=5")
    out=ROOT/"output/pdf";out.mkdir(parents=True,exist_ok=True)
    build_report(metrics,human,feedback,out/"CoursePilot_Report.pdf")
    build_proposal(out/"CoursePilot_Proposal.pdf")
    for name,expected in [("CoursePilot_Report.pdf",3),("CoursePilot_Proposal.pdf",1)]:
        actual=len(PdfReader(out/name).pages)
        if actual!=expected: raise ValueError(f"Layout overflow: {name}: {actual} pages; expected {expected}")
        print(f"Created {name}: {actual} pages")

if __name__=="__main__": main()

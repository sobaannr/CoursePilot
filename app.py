"""CoursePilot Streamlit interface. Run with: streamlit run app.py"""
import hashlib
import json
import uuid
from dataclasses import asdict
import pandas as pd
import streamlit as st
from coursepilot.catalogue import ROOT, eligibility
from coursepilot.engine import Recommender, Profile
from coursepilot.study import csv_text, judgment_packet

st.set_page_config(page_title="CoursePilot | Find your next course", page_icon="🧭", layout="wide")
st.markdown("""<style>
.block-container{max-width:1200px;padding-top:4rem}
h1{letter-spacing:-1.5px} [data-testid="stMetric"]{background:#eaf0f6;border-radius:12px;padding:15px}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:2px;color:#087f8c;margin:0}
.hero{font-size:18px;color:#4c607b;max-width:760px;margin-bottom:22px}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def get_engine():
    return Recommender()

engine = get_engine()
st.markdown('<p class="eyebrow">COURSEPILOT / FAST-NUCES</p>', unsafe_allow_html=True)
st.title("Find a course that fits your curiosity.")
st.markdown('<p class="hero">Explore electives through your interests, see exactly why they match, and check the prerequisites listed in the public catalogue.</p>', unsafe_allow_html=True)
st.caption("Research prototype · Public 2026 catalogue · Karachi batch rules and semester offerings require confirmation")

recommend_tab, catalogue_tab, experiment_tab, study_tab = st.tabs(["Find courses", "Explore catalogue", "Experiments", "Student study"])

with recommend_tab:
    left, right = st.columns([1, 1.65], gap="large")
    with left:
        st.subheader("Your learning profile")
        demo = st.selectbox("Choose a starting point", ["My own profile", "AI engineer", "Data engineer", "Security engineer"])
        field = st.text_input("Your field or career goal", placeholder="e.g. robotics, game development, bioinformatics", key=f"field_{demo}")
        st.caption("The options above are shortcuts. Type any field here and describe the skills you want to learn below.")
        demo_tags = {"AI engineer":["machine learning", "mlops"],
                     "Data engineer":["data engineering", "databases"],
                     "Security engineer":["cybersecurity", "networks"]}
        demo_query = {"AI engineer":"Build and deploy machine learning models with reliable evaluation.",
                      "Data engineer":"Build distributed data pipelines and query large analytical databases.",
                      "Security engineer":"Protect networks and assess vulnerabilities in cloud applications."}
        with st.container():
            query = st.text_area("What would you like to learn?", value=demo_query.get(demo,""),
                                 placeholder="e.g. build search engines and personalized recommendations", max_chars=5000, key=f"query_{demo}")
            interests = st.multiselect("Interests", engine.tags, default=demo_tags.get(demo,[]), key=f"interests_{demo}")
            st.caption("Give more weight to the topics that matter most to you.")
            weights = {}
            for tag in interests:
                weights[tag] = st.slider(f"Importance: {tag}", 1, 5, 3, key=f"weight_{tag}_{demo}")
            default_completed = []
            with st.expander("Completed courses and lab components", expanded=True):
                completed = st.multiselect("Completed courses (include labs separately)", list(engine.by_code),
                    default=default_completed, format_func=lambda code:f"{code} · {engine.by_code[code]['title']}", key=f"completed_{demo}")
            st.caption(f"{len(completed)} completed course components selected")
            st.caption("Select only courses and lab components you have actually completed.")
            c1,c2 = st.columns(2)
            k = c1.slider("Courses to show", 1, 10, 5)
            method_label = c2.selectbox("Ranking", ["TF-IDF", "TF-IDF + topics"])
            submitted = st.button("Find my courses", type="primary", width="stretch")
            prepare_study = st.button("Prepare study profile without rankings", width="stretch")
        query = "\n".join(part.strip() for part in [field, query] if part.strip())[:5000]
        if prepare_study:
            st.session_state["profile"] = asdict(Profile(query, {tag:weights.get(tag,3) for tag in interests}, completed))
            st.session_state.pop("result", None)
            st.session_state.pop("result_id", None)
            st.success("Profile ready. Open Student study to export your unranked judgment packet.")
        if submitted:
            weights = {tag: weights.get(tag,3) for tag in interests}
            profile = Profile(query, weights, completed)
            result = engine.recommend(profile, k, "tfidf" if method_label == "TF-IDF" else "hybrid")
            st.session_state["result"] = result
            st.session_state["profile"] = asdict(profile)
            st.session_state["result_id"] = hashlib.sha256(json.dumps([asdict(profile),result["method"],k],sort_keys=True).encode()).hexdigest()[:12]
    with right:
        st.subheader("Your course shortlist")
        result = st.session_state.get("result")
        if result is None:
            st.info("Describe a learning goal or choose interests, add your completed courses, then select Find my courses.")
            st.markdown("**How your shortlist is built**\n\n1. Check completed courses and listed prerequisites.\n2. Match your profile to course descriptions.\n3. Show the terms and topics behind every score.")
        else:
            st.caption("Results reflect the last submitted profile. Submit again to apply edits.")
            a,b,c = st.columns(3)
            a.metric("Eligible", result["eligible_count"])
            b.metric("Shown", len(result["recommendations"]))
            c.metric("Time", f"{result['latency_ms']:.0f} ms")
            for warning in result["warnings"][1:]:
                st.info(warning)
            for rank, course in enumerate(result["recommendations"], 1):
                with st.container(border=True):
                    st.markdown(f"**{rank:02d} · {course['title']}**")
                    st.caption(f"{course['code']} · Match score {course['score']:.3f} / 1 · Credits: not stated in source")
                    st.write(course["description"])
                    tags = course["matched_tags"]
                    if tags:
                        st.caption("Your matching interests: " + " · ".join(tags))
                    top_terms = course["term_contributions"][:6]
                    st.caption("Matching terms: " + (", ".join(t["term"] for t in top_terms) or "No shared TF-IDF terms; match comes from selected topics."))
                    with st.expander("Why this course? See the calculation"):
                        st.write(course["eligibility"])
                        st.caption("Listed prerequisites: " + course["prerequisite_raw"] + ". N/A means none listed in this document.")
                        st.dataframe(pd.DataFrame([{"Component":k,"Contribution":v} for k,v in course["components"].items() if k in ("tfidf","topics")]), hide_index=True, width="stretch")
                        if course["term_contributions"]:
                            st.dataframe(pd.DataFrame(course["term_contributions"]), hide_index=True, width="stretch")
                        st.caption("All term contributions sum to the cosine score. Weighted components sum to the displayed match score; it is not a probability.")
                        st.markdown(f"[Official catalogue, page {course['source_page']}]({course['source_url']})")
                        st.caption("Elective status is project-curated and must be checked for your batch.")
            with st.expander("Courses excluded by eligibility rules"):
                st.dataframe(pd.DataFrame(result["excluded"]), hide_index=True, width="stretch")
            st.download_button("Download shortlist and explanations", json.dumps({"profile":st.session_state["profile"],**result},indent=2),
                               "coursepilot_shortlist.json", "application/json")

with catalogue_tab:
    st.subheader("A small catalogue, with traceable sources")
    st.write(engine.catalogue["scope"])
    search = st.text_input("Search titles, codes or topics", placeholder="Search e.g. databases")
    category = st.selectbox("Show", ["All entries", "Candidate electives", "Core courses", "Lab references"])
    mapping = {"Candidate electives":"elective","Core courses":"core","Lab references":"support"}
    records = [c for c in engine.courses if (category == "All entries" or c["category"]==mapping[category])
               and search.lower() in (c["code"]+" "+c["title"]+" "+" ".join(c["tags"])).lower()]
    st.dataframe(pd.DataFrame([{"Code":c["code"],"Title":c["title"],"Project role":c["category"],
        "Topics":", ".join(c["tags"]),"Prerequisites":c["prerequisite_raw"],"Source page":c["source_page"]} for c in records]), hide_index=True, width="stretch")
    st.caption(f"{len(records)} of {len(engine.courses)} entries · Dataset {engine.version}")
    with st.expander("Data quality and limitations", expanded=True):
        for limitation in engine.catalogue["limitations"]:
            st.write("• " + limitation)
    st.download_button("Download source-tracked catalogue", json.dumps(engine.catalogue,indent=2), "coursepilot_catalogue.json", "application/json")

with experiment_tab:
    st.subheader("Measure ranking quality")
    metrics_path = ROOT / "output/evaluation/metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
        st.warning("These results use authored fictional scenarios. They test the evaluation pipeline and are not measured student satisfaction.")
        display = [{"Method":r["method"],"Precision@5":r["precision_at_k"]["mean"],
                    "Recall@5":r["recall_at_k"]["mean"],"NDCG@5":r["ndcg_at_k"]["mean"],
                    "Constraint violations":r["violations"]} for r in metrics["summary"]]
        frame = pd.DataFrame(display)
        st.bar_chart(frame.set_index("Method")[["Precision@5","Recall@5","NDCG@5"]], horizontal=True)
        st.dataframe(frame, hide_index=True, width="stretch")
        st.caption(f"{metrics['profiles']} test scenarios · Random averaged over 20 seeds · Hybrid weight 0.75 · Higher is better")
        with st.expander("Protocol and metric definitions"):
            st.markdown("**Precision@K:** relevant returned courses / requested K.\n\n**Recall@K:** relevant returned / all relevant eligible courses.\n\n**NDCG@K:** discounted graded relevance relative to an ideal ordering. Grades are 0–3; grades 2–3 count as relevant.")
            for note in metrics["notes"]:
                st.write("• " + note)
        st.download_button("Download experiment results", metrics_path.read_text(), "metrics.json", "application/json")
    else:
        st.info("Run python -m coursepilot.evaluate to generate experiment results.")

with study_tab:
    st.subheader("Help evaluate CoursePilot")
    st.write("Participation is voluntary. Use an anonymous study ID; do not enter your name, student ID or grades. This app keeps your inputs only in the current session and exports a file when you choose to download it.")
    consent = st.checkbox("I agree to share my anonymous profile and ratings with the project team for this course study.")
    if "participant_alias" not in st.session_state:
        st.session_state["participant_alias"] = "P-" + uuid.uuid4().hex[:8]
    participant_id = st.text_input("Anonymous study ID", key="participant_alias", max_chars=64)
    profile_data = st.session_state.get("profile")
    if profile_data is None:
        st.info("Fill in your own learning profile in Find courses and choose Prepare study profile without rankings. Use your actual interests and completed courses for a real study response.")
    elif consent and participant_id.strip():
        profile = Profile(**profile_data)
        st.markdown("**Independent relevance judgments**")
        st.write("For the main study, complete the randomized catalogue packet before looking at ranked recommendations. Rate each candidate 1 (not relevant) to 5 (very relevant). This packet contains no scores or ranking labels.")
        packet = judgment_packet(engine, profile, participant_id.strip())
        st.download_button("Download blank judgment packet", csv_text(packet), "judgment_packet.csv", "text/csv")
        profile_export = {"dataset_version":engine.version,"profiles":[{"participant_id":participant_id.strip(),"consent":True,"split":"test","profile":profile_data}]}
        st.download_button("Download anonymous study profile", json.dumps(profile_export,indent=2), "study_profile.json", "application/json")
        st.caption("The coordinator assigns development/test groups before collection. Combine profile files and completed packets with the documented import command.")
        st.divider()
        st.markdown("**Shortlist feedback (separate usability pilot)**")
        st.caption("These post-recommendation ratings are not a complete relevance set and cannot be used to calculate Recall@K.")
        feedback = []
        result = st.session_state.get("result", {})
        rid = st.session_state.get("result_id", "none")
        for rank, c in enumerate(result.get("recommendations", []),1):
            rating = st.selectbox(f"How relevant is {c['title']}?", ["Not rated",1,2,3,4,5], key=f"rating_{rid}_{c['code']}")
            if rating != "Not rated":
                feedback.append({"participant_id":participant_id.strip(),"course_code":c["code"],"rank":rank,
                    "method":result["method"],"rating_1_to_5":rating,"dataset_version":engine.version,
                    "response_type":"post_ranking_feedback","consent":True})
        if feedback:
            st.download_button("Download my shortlist feedback", csv_text(feedback), "shortlist_feedback.csv", "text/csv")
        st.caption("Downloads stay on your device until you choose to share them. No response is submitted automatically.")

st.divider()
st.caption("CoursePilot · Explainable content-based recommendation · FAST-NUCES Recommender System project, Fall 2026")

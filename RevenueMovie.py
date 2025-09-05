import pandas as pd
import streamlit as st

# Load dataset
@st.cache_data
def load_data(file_path="RevenueMovies.csv"):
    df = pd.read_csv(file_path)
    if "title" not in df.columns or "revenue" not in df.columns:
        st.error("❌ Dataset must contain 'title' and 'revenue' columns.")
        return pd.DataFrame()
    df = df[['title', 'revenue']].dropna()
    df = df[df['revenue'] > 0].reset_index(drop=True)
    return df

def get_recommendations(df, selected_movie, locked_range):
    """Get 5 random recommendations from revenue range."""
    if locked_range:
        lower, upper = locked_range
        df = df[(df['revenue'] >= lower) & (df['revenue'] <= upper)]
    return df[df['title'] != selected_movie]

# ---- Streamlit App ----
st.set_page_config(page_title="🎬 Revenue-Based Movie Recommender", layout="wide")
st.title("🎥 Revenue-Based Movie Recommender")

df = load_data("RevenueMovies.csv")
if df.empty:
    st.stop()

# Session state
if "locked_range" not in st.session_state:
    st.session_state.locked_range = None
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = pd.DataFrame()
if "feedback_log" not in st.session_state:
    st.session_state.feedback_log = []

# Sidebar: Movie Selection
st.sidebar.header("Select a Movie")
sample_movies = df.sample(min(20, len(df))).reset_index(drop=True)
movie_choice = st.sidebar.radio(
    "Pick a movie you watched:", 
    sample_movies['title']
)

if st.sidebar.button("Confirm Selection"):
    selected_row = sample_movies[sample_movies['title'] == movie_choice].iloc[0]
    st.session_state.selected_movie = selected_row['title']
    selected_revenue = selected_row['revenue']
    
    # Lock revenue range
    if not st.session_state.locked_range:
        lower = selected_revenue * 0.7
        upper = selected_revenue * 1.3
        st.session_state.locked_range = (lower, upper)
    
    # Generate recommendations
    rec_pool = get_recommendations(df, st.session_state.selected_movie, st.session_state.locked_range)
    st.session_state.recommendations = rec_pool.sample(min(5, len(rec_pool))).reset_index(drop=True)

# Main Content
if st.session_state.selected_movie:
    st.subheader(f"🎬 Since you watched **{st.session_state.selected_movie}**, you might also like:")

    # Refresh recommendations
    if st.button("🔄 Refresh Recommendations"):
        rec_pool = get_recommendations(df, st.session_state.selected_movie, st.session_state.locked_range)
        st.session_state.recommendations = rec_pool.sample(min(5, len(rec_pool))).reset_index(drop=True)

    # Show recommendations
    if not st.session_state.recommendations.empty:
        liked_movies = []
        for i, row in st.session_state.recommendations.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{row['title']}** (Revenue: ${row['revenue']:,})")
            with col2:
                if st.button(f"👍 Like {row['title']}", key=row['title']):
                    liked_movies.append(row['title'])

        # Log feedback
        if liked_movies:
            st.session_state.feedback_log.append({
                "watched": st.session_state.selected_movie,
                "recommendations": list(st.session_state.recommendations['title']),
                "liked": liked_movies
            })
            st.success(f"✅ Feedback saved for {st.session_state.selected_movie}")

# Show summary
if st.sidebar.button("📊 Show Satisfaction Summary"):
    st.header("📊 User Satisfaction Summary")
    total_recs = sum(len(f["recommendations"]) for f in st.session_state.feedback_log)
    total_likes = sum(len(f["liked"]) for f in st.session_state.feedback_log)

    if total_recs > 0:
        precision = total_likes / total_recs
        st.write(f"**Total recommendations shown:** {total_recs}")
        st.write(f"**Total movies liked:** {total_likes}")
        st.write(f"**Precision (Liked ÷ Recommended):** {precision:.2f}")
    else:
        st.info("No feedback collected yet.")

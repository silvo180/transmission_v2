import math
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def classify_magnitude(value):
    """
    Impact rating categories:
      1–7   => Very low
      8–14  => Low
      15–25 => Moderate
      26–36 => High
      37+   => Very high
    We trigger an intermediate assessment if value >=15 (Moderate or higher).
    """
    if value <= 7:
        return "Very low"
    elif value <= 14:
        return "Low"
    elif value <= 25:
        return "Moderate"
    elif value <= 36:
        return "High"
    else:
        return "Very high"

def compute_sums(tower_height_m, span_between_towers_m, tower_angle_deg):
    """
    We have 2 sets of sums:
      (1) TOWERS ≥3°
      (2) ALL VISIBLE (≥0.1°)
    For each offset multiple of 'span_between_towers_m' from near -4000..+4000:
      - raw_angle = degrees(atan(tower_height_m / r))
      - if raw_angle >=0.1 => add to 'all visible'
      - if raw_angle >=3 => also add to '≥3°'
    """
    angle_radians = math.radians(tower_angle_deg)
    if abs(math.tan(angle_radians)) < 1e-12:
        return (0,0,0.0), (0,0,0.0)

    # Force the central tower to that angle
    d = tower_height_m / math.tan(angle_radians)

    # sums for TOWERS≥3°
    f3 = c3 = 0
    d3 = 0.0

    # sums for ALL≥0.1°
    fall = call = 0
    dall = 0.0

    # Instead of range(-4000,4001,step), we do a symmetrical multiple approach
    step = int(span_between_towers_m) if span_between_towers_m == int(span_between_towers_m) else int(span_between_towers_m + 0.9999)
    if step < 1:
        step = 1

    # Max number of spans to reach 4000
    max_n = 4000 // step  # integer division
    # We'll check multiples i from -max_n..+max_n
    # then skip if x < -4000 or x>4000
    for i in range(-max_n, max_n+1):
        x = i * step
        if x < -4000 or x > 4000:
            continue

        r = math.hypot(d, x)
        if r <= 0:
            continue

        raw_angle = math.degrees(math.atan(tower_height_m / r))
        if raw_angle < 0.1:
            continue

        # all visible≥0.1
        fall += math.floor(raw_angle)
        call += math.ceil(raw_angle)
        dall += raw_angle

        # towers≥3
        if raw_angle >= 3.0:
            f3 += math.floor(raw_angle)
            c3 += math.ceil(raw_angle)
            d3 += raw_angle

    return (f3, c3, d3), (fall, call, dall)

def visualize_towers(tower_height_m, span_between_towers_m, tower_angle_deg,
                     sums_3, classification, triggers_intermediate,
                     style_choice="180x40 degree grid"):
    """
    Plot logic: color=red if raw_angle>=3, else blue if >=0.1
    We'll do the same offset multiple approach to get tower data.
    """
    angle_radians = math.radians(tower_angle_deg)
    if abs(math.tan(angle_radians)) < 1e-12:
        st.write("Angle too small.")
        return None

    d = tower_height_m / math.tan(angle_radians)
    f3, c3, d3 = sums_3

    step = int(span_between_towers_m) if span_between_towers_m == int(span_between_towers_m) else int(span_between_towers_m+0.9999)
    if step < 1:
        step = 1
    max_n = 4000 // step

    towers_data = []
    for i in range(-max_n, max_n+1):
        x = i*step
        if x < -4000 or x>4000:
            continue

        r = math.hypot(d, x)
        if r<=0:
            continue
        raw_angle = math.degrees(math.atan(tower_height_m / r))
        if raw_angle<0.1:
            continue

        # horizontal angle
        if x==0:
            phi=95.0
        else:
            phi_calc = math.degrees(math.atan(abs(x)/d))
            phi= 95+phi_calc if x>0 else 95-phi_calc
            phi= max(0, min(180, phi))

        # color
        if raw_angle>=3.0:
            color='red'
        else:
            color='blue'

        top_deg= min(raw_angle,40.0)
        towers_data.append((phi, top_deg, color))

    fig, ax = plt.subplots(figsize=(12,3), dpi=300)

    if style_choice=="180x40 degree grid":
        for xv in range(0,181,10):
            ax.axvline(x=xv, color='gray', lw=0.5, alpha=0.5)
        for yv in range(0,41):
            ax.axhline(y=yv, color='gray', lw=0.5, alpha=0.5)

        ax.set_xticks(range(0,181,10))
        ax.set_yticks(range(0,41,5))
        ax.set_xlim(0,180)
        ax.set_ylim(0,40)
        ax.set_xlabel("Horizontal angle (°)")
        ax.set_ylabel("Vertical angle (°)")
        ax.set_title("Transmission Simple Assessment Tool")
        ax.set_aspect('equal', adjustable='box')

        # Summarize final sums≥3
        main_text = (f"Towers ≥3° => Lower Sum: {f3} | Upper Sum: {c3} | Decimal Sum: {d3:.2f} | "
                     f"Classification: {classification} | "
                     f"Intermediate: {'YES' if triggers_intermediate else 'NO'}")

        fig.subplots_adjust(bottom=0.7)
        fig.text(0.5, 0.0, main_text, ha='center', va='bottom', fontsize=10)

    else:
        ax.set_xlim(0,180)
        ax.set_ylim(0,40)
        ax.axis('off')
        ax.plot([0,180],[0,0],color='black',lw=1)
        ax.plot([0,180],[40,40],color='black',lw=1)
        ax.plot([0,0],[0,40],color='black',lw=1)
        ax.plot([180,180],[0,40],color='black',lw=1)

    # draw the towers
    for (phi, top_deg, color) in towers_data:
        if top_deg<=0:
            continue
        width=2.0
        left_x= phi-width/2
        rect=Rectangle((left_x,0), width, top_deg, facecolor=color, edgecolor=color, alpha=0.6)
        ax.add_patch(rect)

    plt.tight_layout()
    return fig

# --- The Streamlit App ---

st.title("Simple Tower Assessment Tool")

method_choice = st.radio(
    "Method",
    ("Use Tower Height Angle","Use Distance to Nearest Tower")
)

tower_height = st.number_input("Tower Height (m):", value=50.0, step=1.0)
span = st.number_input("Span Between Towers (m):", value=100.0, step=1.0)

if method_choice=="Use Tower Height Angle":
    tower_angle= st.number_input("Tower Height Angle (°):", min_value=1.0, max_value=20.0, value=5.0, step=0.1)
    used_angle= tower_angle
    distance_used=None
else:
    distance_used= st.number_input("Distance to Nearest Tower (m):", value=500.0, step=10.0)
    if distance_used>0:
        raw_angle_radians= math.atan(tower_height/ distance_used)
        used_angle= math.degrees(raw_angle_radians)
    else:
        used_angle=5.0
        distance_used=500.0

style_option= st.selectbox(
    "Plot Style",
    ("180x40 degree grid","Minimal with borders")
)

if st.button("Calculate"):
    # sums≥3, sums≥0.1
    sums_3, sums_all= compute_sums(tower_height, span, used_angle)
    f3, c3, d3= sums_3
    fall, call, dall= sums_all

    classification= classify_magnitude(c3)
    # intermediate if c3≥15 => moderate or higher
    triggers_intermediate= (c3>=15)

    st.subheader("RESULTS:")
    st.write(f"**Tower Height (m):** {tower_height}")
    st.write(f"**Span Between Towers (m):** {span}")

    if method_choice=="Use Tower Height Angle":
        st.write(f"**Tower Height Angle (°):** {tower_angle:.1f}")
    else:
        st.write(f"**Distance to Nearest Tower (m):** {distance_used}")
        st.write(f"**Computed Tower Angle (°):** {used_angle:.2f}")
    st.write("---")

    # towers≥3
    st.write("**CALCULATIONS FOR TOWERS ≥ 3°:**")
    st.write(f"Lower Sum: {f3}, Upper Sum: {c3}, Decimal Sum: {d3:.2f}")
    st.write(f"Classification: {classification}")
    if triggers_intermediate:
        st.write("NOTE: Occupied cells ≥15 => moderate or higher => intermediate assessment triggered.")

    st.write("")
    # all≥0.1
    st.write("**CALCULATIONS FOR ALL VISIBLE TOWERS ≥ 0.1°:** (blue if <3°, red if ≥3°)")
    st.write(f"Lower Sum: {fall}, Upper Sum: {call}, Decimal Sum: {dall:.2f}")

    fig = visualize_towers(
        tower_height, span, used_angle,
        sums_3,
        classification, triggers_intermediate,
        style_choice=style_option
    )
    if fig:
        st.pyplot(fig)

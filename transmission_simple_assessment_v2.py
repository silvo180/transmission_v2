import math
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def classify_magnitude(value):
    """
    Classify the summed value:
      1–7   => Very low
      8–14  => Low
      15–25 => Moderate
      26–36 => High
      37+   => Very high
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
    For each x in -4000..+4000 (step=span_between_towers_m), we do:

    1) Distance d = tower_height_m / tan(tower_angle_deg) ensures the central tower is forced to that angle
    2) r = sqrt(d^2 + x^2)
    3) raw_angle = degrees(atan(tower_height_m / r))

    Then:
      - If raw_angle >= 3.0 => add to the ≥3° sums (floor, ceil, decimal)
      - If raw_angle >= 2.0 => also add to the ≥2° sums (floor, ceil, decimal)

    (We skip angles < 0.1° as negligible.)
    """

    angle_radians = math.radians(tower_angle_deg)
    if abs(math.tan(angle_radians)) < 1e-12:
        # Angle is effectively 0 => can't do geometry
        # Return zeroed-out sums
        return (0,0,0.0), (0,0,0.0)

    # Force the central tower to tower_angle_deg
    d = tower_height_m / math.tan(angle_radians)

    # Sums for towers >=3°
    floor_3p = 0
    ceil_3p  = 0
    dec_3p   = 0.0

    # New sums for towers >=2°
    floor_2p = 0
    ceil_2p  = 0
    dec_2p   = 0.0

    # Loop offsets
    step = int(span_between_towers_m) if span_between_towers_m == int(span_between_towers_m) else int(span_between_towers_m + 0.9999)
    if step < 1:
        step = 1

    for x in range(-4000, 4001, step):
        r = math.hypot(d, x)
        if r <= 0:
            continue

        raw_angle = math.degrees(math.atan(tower_height_m / r))
        if raw_angle < 0.1:
            continue

        # If >=2°, add to the ≥2° sums
        if raw_angle >= 2.0:
            floor_2p += math.floor(raw_angle)
            ceil_2p  += math.ceil(raw_angle)
            dec_2p   += raw_angle

        # If >=3°, add to the ≥3° sums
        if raw_angle >= 3.0:
            floor_3p += math.floor(raw_angle)
            ceil_3p  += math.ceil(raw_angle)
            dec_3p   += raw_angle

    # Return in the form:
    # ( (floor_3, ceil_3, dec_3), (floor_2, ceil_2, dec_2) )
    return (floor_3p, ceil_3p, dec_3p), (floor_2p, ceil_2p, dec_2p)


def visualize_towers(tower_height_m, span_between_towers_m, tower_angle_deg,
                     f3, c3, d3,
                     classification, triggers_intermediate,
                     style_choice="180x40 degree grid"):
    """
    Two style options:
      1) "180x40 degree grid": original approach with grid lines, labeling, summary at bottom
      2) "Minimal with borders": no grid lines or text at bottom, but bounding lines at x=0..180, y=0..40

    The rectangles are drawn at the calculated positions with width=2, height=raw_angle (capped at 40).
    Red color if raw_angle >=3°, else blue.
    """
    angle_radians = math.radians(tower_angle_deg)
    if abs(math.tan(angle_radians)) < 1e-12:
        st.write("Angle too small.")
        return None

    # Distance for the central tower
    d = tower_height_m / math.tan(angle_radians)
    
    # Build tower data for plotting
    towers_data = []
    step = int(span_between_towers_m) if span_between_towers_m == int(span_between_towers_m) else int(span_between_towers_m + 0.9999)
    if step < 1:
        step = 1

    for x in range(-4000, 4001, step):
        r = math.hypot(d, x)
        if r <= 0:
            continue
        raw_angle = math.degrees(math.atan(tower_height_m / r))
        if raw_angle < 0.1:
            continue
        
        # horizontal angle
        if x == 0:
            phi = 95.0
        else:
            phi_calc = math.degrees(math.atan(abs(x) / d))
            phi = 95 + phi_calc if x > 0 else 95 - phi_calc
            phi = max(0, min(180, phi))
        
        color = 'red' if raw_angle >= 3.0 else 'blue'
        top_deg = min(raw_angle, 40.0)
        towers_data.append((phi, top_deg, color))

    fig, ax = plt.subplots(figsize=(12,3), dpi=300)

    if style_choice == "180x40 degree grid":
        # Original approach with grid lines
        for xv in range(0, 181, 10):
            ax.axvline(x=xv, color='gray', lw=0.5, alpha=0.5)
        for yv in range(0, 41):
            ax.axhline(y=yv, color='gray', lw=0.5, alpha=0.5)

        ax.set_xticks(range(0,181,10))
        ax.set_yticks(range(0,41,5))
        
        ax.set_xlim(0,180)
        ax.set_ylim(0,40)
        ax.set_xlabel("Horizontal angle (°)")
        ax.set_ylabel("Vertical angle (°)")
        ax.set_title("Transmission Simple Assessment Tool")

        ax.set_aspect('equal', adjustable='box')

        # Summarize
        main_text = (f"Towers ≥3° => Lower Sum: {f3} | Upper Sum: {c3} | Decimal Sum: {d3:.2f} | "
                     f"Classification: {classification} | "
                     f"Intermediate: {'YES' if triggers_intermediate else 'NO'}")
        
        fig.subplots_adjust(bottom=0.7)
        fig.text(0.5, 0.0, main_text, ha='center', va='bottom', fontsize=10)
    
    else:  # "Minimal with borders"
        ax.set_xlim(0,180)
        ax.set_ylim(0,40)
        ax.axis('off')
        # bounding lines
        ax.plot([0, 180],[0,0], color='black', lw=1)
        ax.plot([0, 180],[40,40], color='black', lw=1)
        ax.plot([0,0],[0,40], color='black', lw=1)
        ax.plot([180,180],[0,40], color='black', lw=1)

    # draw the towers
    for (phi,top_deg,color) in towers_data:
        if top_deg<=0:
            continue
        width=2.0
        left_x = phi - width/2
        lower_y=0
        rect=Rectangle((left_x,lower_y), width, top_deg,
                       facecolor=color, edgecolor=color, alpha=0.6)
        ax.add_patch(rect)

    plt.tight_layout()
    return fig


# --- The Streamlit App ---

st.title("Simple Tower Assessment Tool")

st.write("Choose how to provide your tower angle information:")

method_choice = st.radio(
    "Method",
    ("Use Tower Height Angle", "Use Distance to Nearest Tower")
)

tower_height = st.number_input("Tower Height (m):", value=50.0, step=1.0)
span = st.number_input("Span Between Towers (m):", value=100.0, step=1.0)

if method_choice == "Use Tower Height Angle":
    tower_angle = st.number_input("Tower Height Angle (°):", min_value=1.0, max_value=20.0, value=5.0, step=0.1)
    used_angle = tower_angle
    distance_used = None
else:
    distance_used = st.number_input("Distance to Nearest Tower (m):", value=500.0, step=10.0)
    if distance_used > 0:
        # convert distance -> angle
        raw_angle_radians = math.atan(tower_height / distance_used)
        computed_angle = math.degrees(raw_angle_radians)
        used_angle = computed_angle
    else:
        used_angle = 5.0
        distance_used = 500.0

style_option = st.selectbox(
    "Plot Style",
    ("180x40 degree grid", "Minimal with borders")
)

if st.button("Calculate"):
    # compute sums
    (f3, c3, d3), (f2, c2, d2) = compute_sums(tower_height, span, used_angle)
    classification = classify_magnitude(c3)
    triggers_intermediate = (c3 >= 16)

    st.subheader("RESULTS:")
    st.write(f"**Tower Height (m):** {tower_height}")
    st.write(f"**Span Between Towers (m):** {span}")

    if method_choice == "Use Tower Height Angle":
        st.write(f"**Tower Height Angle (°):** {tower_angle:.1f}")
        st.write("---")
    else:
        st.write(f"**Distance to Nearest Tower (m):** {distance_used}")
        st.write(f"**Computed Tower Angle (°):** {used_angle:.2f}")
        st.write("---")

    st.write("**CALCULATIONS FOR TOWERS ≥ 3°:**")
    st.write(f"Lower Sum: {f3}, Upper Sum: {c3}, Decimal Sum: {d3:.2f}")
    st.write(f"Classification: {classification}")
    if triggers_intermediate:
        st.write("NOTE: Upper sum >=16, so an intermediate assessment may be triggered.")

    st.write("")
    st.write("**CALCULATIONS FOR TOWERS ≥ 2°:**  (e.g. a 2.2° tower counts as 3 cells)")
    st.write(f"Lower Sum: {f2}, Upper Sum: {c2}, Decimal Sum: {d2:.2f}")

    # Show the chart
    fig = visualize_towers(
        tower_height, span, used_angle,
        f3, c3, d3,
        classification, triggers_intermediate,
        style_choice=style_option
    )
    if fig is not None:
        st.pyplot(fig)

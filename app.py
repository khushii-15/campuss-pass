
# ==========================================================
# CampusPass - Smart Campus Event Registration System
# Frontend: Streamlit
# Backend: Python + SQLite
# QR Code: qrcode + Pillow
# ==========================================================

# Import required libraries
import cv2
import numpy as np
import streamlit as st
import sqlite3
import qrcode
import uuid
import io
from datetime import datetime



# ----------------------------------------------------------
# 1. PAGE CONFIGURATION
# Controls the browser tab title and page layout
# ----------------------------------------------------------

st.set_page_config(
    page_title="CampusPass | Smart Event System",
    page_icon="🧿",
    layout="wide"
)
# CampusPass futuristic neon theme
st.markdown("""
<style>

/* Main application background */
.stApp {
    background: linear-gradient(135deg, #080d24, #11113a, #090b1a);
    color: #f1f5ff;
}

/* Main headings */
h1, h2, h3 {
    color: #ffffff !important;
    text-shadow: 0 0 12px rgba(0, 229, 255, 0.45);
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101633, #170e30);
    border-right: 1px solid #00e5ff;
}

/* Buttons with neon glow */
.stButton > button {
    background: linear-gradient(90deg, #5b21b6, #0077ff);
    color: white;
    border: 1px solid #00e5ff;
    border-radius: 12px;
    font-weight: bold;
    transition: 0.3s;
    box-shadow: 0 0 10px rgba(0, 229, 255, 0.25);
}

.stButton > button:hover {
    box-shadow: 0 0 22px #00e5ff;
    border: 1px solid #ffffff;
    transform: translateY(-2px);
}

/* Input boxes */
.stTextInput input, .stTextArea textarea {
    background-color: #141b38;
    color: white;
    border: 1px solid #6254ff;
    border-radius: 10px;
}

/* Dashboard cards */
[data-testid="stMetric"] {
    background: rgba(22, 31, 67, 0.8);
    border: 1px solid #5145cd;
    padding: 18px;
    border-radius: 15px;
    box-shadow: 0 0 12px rgba(81, 69, 205, 0.25);
}

/* Success messages */
[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Divider */
hr {
    border-color: #5145cd;
}

/* CampusPass Cambria Typography */

/* Apply Cambria to the entire application */
.stApp,
.stApp p,
.stApp label,
.stApp input,
.stApp textarea,
.stApp button,
.stApp li,
.stApp [data-testid="stMarkdownContainer"] {
    font-family: Cambria, Georgia, serif !important;
}

/* Main headings: bold Cambria */
.stApp h1,
.stApp h2,
.stApp h3 {
    font-family: Cambria, Georgia, serif !important;
    font-weight: bold !important;
    font-style: normal !important;
    color: #FFFFFF !important;
}

/* Main title neon effect */
.stApp h1 {
    color: #00E5FF !important;
    text-shadow: 0 0 12px rgba(0, 229, 255, 0.5);
}

/* Normal text */
.stApp p,
.stApp label,
.stApp li {
    font-weight: normal !important;
    font-style: normal !important;
    color: #CBD5F5 !important;
}

/* Dashboard metric numbers */
[data-testid="stMetricValue"] {
    font-family: Cambria, Georgia, serif !important;
    font-weight: bold !important;
    color: #00E5FF !important;
}

/* Sidebar headings */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: Cambria, Georgia, serif !important;
    font-weight: bold !important;
}

</style>
""", unsafe_allow_html=True)
# ----------------------------------------------------------
# 2. DATABASE SETUP
# SQLite stores registrations and entry records permanently
# ----------------------------------------------------------

DB_NAME = "campuspass.db"


def get_connection():
    """Create a connection to the CampusPass database."""
    return sqlite3.connect(DB_NAME)


def create_tables():
    """Create the database tables if they do not exist."""

    conn = get_connection()
    cursor = conn.cursor()

    # Store student registrations and their unique pass IDs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            pass_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            college_id TEXT NOT NULL,
            event_name TEXT NOT NULL,
            registered_at TEXT NOT NULL,
            checked_in INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# Create the database table when the app starts
create_tables()


# ----------------------------------------------------------
# 3. QR CODE GENERATOR
# Each pass gets a unique QR code containing its pass ID
# ----------------------------------------------------------

def generate_qr(pass_id):
    """Generate a QR code image for a given pass ID."""

    qr = qrcode.make(pass_id)

    # Save the QR image in memory instead of creating a file
    image_buffer = io.BytesIO()
    qr.save(image_buffer, format="PNG")
    image_buffer.seek(0)

    return image_buffer
# Function to read a QR code from an uploaded image
def read_qr_code(uploaded_file):

    # Get uploaded image bytes
    image_bytes = uploaded_file.getvalue()

    # Convert image bytes into an array
    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    # Decode image using OpenCV
    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    # Create QR detector
    detector = cv2.QRCodeDetector()

    # Read the Pass ID from the QR code
    decoded_text, points, _ = detector.detectAndDecode(image)

    # Return the detected Pass ID
    return decoded_text


# ----------------------------------------------------------
# 4. REGISTRATION BACKEND
# Validate the form and save the student in the database
# ----------------------------------------------------------

def register_student(name, email, college_id, event_name):
    """Save a new registration and return its unique pass ID."""

    # Generate a unique ID for this event pass
    pass_id = "CP-" + uuid.uuid4().hex[:8].upper()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Save the student's information in SQLite
        cursor.execute("""
            INSERT INTO registrations
            (pass_id, name, email, college_id,
             event_name, registered_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            pass_id,
            name,
            email,
            college_id,
            event_name,
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ))

        conn.commit()

    except sqlite3.IntegrityError:
        # Handle a rare duplicate pass ID
        conn.close()
        return None

    conn.close()
    return pass_id


# ----------------------------------------------------------
# 5. QR VERIFICATION BACKEND
# Check whether a pass is valid or has already been used
# ----------------------------------------------------------

def verify_pass(pass_id):
    """Verify a pass and mark it as checked in once."""

    conn = get_connection()
    cursor = conn.cursor()

    # Search for the pass ID in the registrations table
    cursor.execute(
        "SELECT * FROM registrations WHERE pass_id = ?",
        (pass_id.strip().upper(),)
    )

    record = cursor.fetchone()

    if record is None:
        conn.close()
        return "invalid", None

    # Column index 7 stores the checked-in status
    if record[6] == 1:
        conn.close()
        return "duplicate", record

    # Mark the pass as used after successful verification
    cursor.execute("""
        UPDATE registrations
        SET checked_in = 1
        WHERE pass_id = ?
    """, (pass_id.strip().upper(),))

    conn.commit()
    conn.close()

    return "valid", record


# ----------------------------------------------------------
# 6. SIDEBAR NAVIGATION
# Allows users to move between different app pages
# ----------------------------------------------------------

st.sidebar.title("🧿 CampusPass")
st.sidebar.caption("Smart Campus Event System")

page = st.sidebar.radio(
    "Navigate",
    [
        "Home",
        "Student Registration",
        "My Digital Pass",
        "QR Verification",
        "Admin Dashboard"
    ]
)

st.sidebar.divider()
st.sidebar.caption("CampusPass | Hackathon Prototype")


# ----------------------------------------------------------
# 7. HOME PAGE - CAMPUSPASS DASHBOARD
# ----------------------------------------------------------

if page == "Home":

    # Main dashboard heading
    st.title("🧿 CampusPass")
    st.subheader(
        "One Pass. One Scan. Secure Campus Events."
    )

    # Welcome banner
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #101a3c, #35205f);
        padding: 28px;
        border-radius: 18px;
        border: 1px solid #00e5ff;
        margin-bottom: 25px;
    ">
        <h2 style="color: #00e5ff; margin-bottom: 10px;">
            Welcome to CampusPass 🚀
        </h2>
        <p style="color: white; font-size: 17px;">
            Your smart campus event companion.
            Register for events, access your digital QR pass,
            and enjoy secure, seamless entry.
        </p>
        <p style="color: #b8c7ff;">
            Smart Registration | QR Verification | Digital Attendance
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch live registration statistics from the database
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM registrations")
    total_registered = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM registrations WHERE checked_in = 1"
    )
    total_checked_in = cursor.fetchone()[0]

    conn.close()

    # Calculate pending entries
    pending_entries = total_registered - total_checked_in

    # Dashboard statistics
    st.markdown("### 📊 Event Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="👥 Total Registrations",
            value=total_registered
        )

    with col2:
        st.metric(
            label="✅ Successful Check-ins",
            value=total_checked_in
        )

    with col3:
        st.metric(
            label="⏳ Pending Entries",
            value=pending_entries
        )

    st.divider()

    # Events available on CampusPass
    st.markdown("### 🎯 Featured Campus Events")

    event_col1, event_col2, event_col3 = st.columns(3)

    with event_col1:
        st.markdown("""
        <div style="
            background: #111b35;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #00e5ff;
            min-height: 150px;
        ">
            <h3 style="color: #00e5ff;">💻 TechFest 2026</h3>
            <p style="color: white;">
                Explore technology, innovation and coding.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with event_col2:
        st.markdown("""
        <div style="
            background: #111b35;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #a970ff;
            min-height: 150px;
        ">
            <h3 style="color: #c6a0ff;">🤖 AI Innovation Summit</h3>
            <p style="color: white;">
                Discover artificial intelligence and new ideas.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with event_col3:
        st.markdown("""
        <div style="
            background: #111b35;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #00ffc3;
            min-height: 150px;
        ">
            <h3 style="color: #00ffc3;">🎭 Cultural Night</h3>
            <p style="color: white;">
                Celebrate creativity, music and campus life.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # How to use CampusPass
    st.markdown("### ⚡ How CampusPass Works")

    st.markdown("""
    1. **Register:** Enter your details and select an event.
    2. **Get Your Pass:** Receive a unique Pass ID and QR code.
    3. **Verify:** Upload your QR pass or enter your Pass ID.
    4. **Check In:** Each valid pass can be used only once.
    """)

    st.success(
        "Your campus events, simplified. "
        "Select a page from the sidebar to get started!"
    )


# ----------------------------------------------------------
# 8. STUDENT REGISTRATION PAGE
# ----------------------------------------------------------


# ----------------------------------------------------------
# 8. STUDENT REGISTRATION PAGE
# ----------------------------------------------------------

elif page == "Student Registration":

    st.title("📝 Student Event Registration")
    st.write("Fill in your details to generate a digital event pass.")

    with st.form("registration_form"):

        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        college_id = st.text_input("College ID")

        event_name = st.selectbox(
            "Select Event",
            [
                "TechFest 2026",
                "AI Innovation Summit",
                "Campus Cultural Night"
            ]
        )

        submitted = st.form_submit_button(
            "Register & Generate Pass",
            use_container_width=True
        )

        if submitted:

            # Basic form validation
            if not name.strip() or not email.strip() or not college_id.strip():
                st.error("Please fill in all the required fields.")

            elif "@" not in email or "." not in email:
                st.error("Please enter a valid email address.")

            else:
                # Save registration and generate a pass ID
                pass_id = register_student(
                    name.strip(),
                    email.strip(),
                    college_id.strip(),
                    event_name
                )

                if pass_id:
                    st.session_state["latest_pass_id"] = pass_id

                    st.success("Registration successful!")
                    st.write("Your unique Pass ID is:")
                    st.code(pass_id)

                    st.info(
                        "Open My Digital Pass from the sidebar "
                        "to view your QR ticket."
                    )
                else:
                    st.error("Could not generate a pass. Please try again.")


# ----------------------------------------------------------
# 9. MY DIGITAL PASS PAGE
# ----------------------------------------------------------

elif page == "My Digital Pass":

    st.title("🎫 My Digital Pass")

    pass_id = st.session_state.get("latest_pass_id")

    if pass_id:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM registrations WHERE pass_id = ?",
            (pass_id,)
        )

        record = cursor.fetchone()
        conn.close()

        if record:

            st.success("Your digital event pass is ready!")

            st.subheader(record[1])
            st.write("Event:", record[4])
            st.write("College ID:", record[3])
            st.write("Pass ID:", record[0])

            # Generate and display the pass QR code
            qr_image = generate_qr(record[0])

            st.image(qr_image, caption="Scan this QR at the event entrance")

            # Allow the student to download their QR pass
            st.download_button(
                "Download QR Pass",
                data=qr_image.getvalue(),
                file_name=f"{record[0]}.png",
                mime="image/png",
                use_container_width=True
            )

        else:
            st.warning("Pass not found.")

    else:
        st.info(
            "Please register for an event first. "
            "Your pass will appear here."
        )


# ----------------------------------------------------------
# 10. QR VERIFICATION PAGE
# ----------------------------------------------------------


elif page == "QR Verification":

    st.title("🔍 Event Entry Verification")
    st.write("Verify student passes by entering a Pass ID or uploading a QR image.")

    # Option to choose verification method
    verification_method = st.radio(
        "Choose Verification Method",
        ["Enter Pass ID", "Upload QR Image"],
        horizontal=True
    )

    entered_pass_id = ""

    # METHOD 1: Manual Pass ID entry
    if verification_method == "Enter Pass ID":

        entered_pass_id = st.text_input(
            "Pass ID",
            placeholder="Example: CP-A1B2C3D4"
        )

    # METHOD 2: Upload QR code image
    else:

        uploaded_qr = st.file_uploader(
            "Upload Student QR Code",
            type=["png", "jpg", "jpeg"],
            help="Upload the QR image downloaded from My Digital Pass."
        )

        # Read the QR code when an image is uploaded
        if uploaded_qr is not None:

            decoded_pass_id = read_qr_code(uploaded_qr)

            if decoded_pass_id:
                st.success("QR Code Read Successfully!")
                st.write("Detected Pass ID:", decoded_pass_id)

                entered_pass_id = decoded_pass_id

            else:
                st.error("Could not read the QR code. Please upload a clear QR image.")

    # Verify the pass
    if st.button("Verify Entry", use_container_width=True):

        if not entered_pass_id.strip():

            st.warning("Please enter a Pass ID or upload a readable QR image.")

        else:

            status, record = verify_pass(entered_pass_id)

            if status == "valid":

                st.success("✅ VALID PASS — Entry Approved")
                st.write("Student:", record[1])
                st.write("Event:", record[4])
                st.write("Pass ID:", record[0])

            elif status == "duplicate":

                st.warning("⚠️ DUPLICATE PASS — Already Checked In")
                st.write("Student:", record[1])
                st.write("This pass has already been used.")

            else:

                st.error("❌ INVALID PASS — No matching registration found.")
# ----------------------------------------------------------
# 11. ADMIN DASHBOARD
# ----------------------------------------------------------

elif page == "Admin Dashboard":

    st.title("📊 Event Admin Dashboard")

    conn = get_connection()

    # Read all registrations from the database
    import pandas as pd

    df = pd.read_sql_query(
        "SELECT * FROM registrations ORDER BY registered_at DESC",
        conn
    )

    conn.close()

    if df.empty:
        st.info("No registrations yet. Register a student to begin.")

    else:
        total = len(df)
        checked_in = int(df["checked_in"].sum())
        pending = total - checked_in

        col1, col2, col3 = st.columns(3)

        col1.metric("Registered", total)
        col2.metric("Checked In", checked_in)
        col3.metric("Pending", pending)

        # Calculate attendance percentage safely
        attendance_percentage = (checked_in / total) * 100

        st.progress(
            attendance_percentage / 100,
            text=f"Attendance: {attendance_percentage:.1f}%"
        )

        st.subheader("Recent Registrations")

        # Display records in a clean table
        st.dataframe(
            df.drop(columns=["college_id"]),
            use_container_width=True,
            hide_index=True
        )

        # Download attendance report as CSV
        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Attendance Report",
            data=csv_data,
            file_name="campuspass_attendance.csv",
            mime="text/csv"
        )
        # This function reads a QR code from an uploaded image
def read_qr_code(uploaded_file):

    # Convert the uploaded image into bytes
    image_bytes = uploaded_file.getvalue()

    # Convert bytes into an image array that OpenCV can understand
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)

    # Decode the image into OpenCV format
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # Create a QR code detector
    detector = cv2.QRCodeDetector()

    # Read the text stored inside the QR code
    decoded_text, points, _ = detector.detectAndDecode(image)

    # Return the decoded Pass ID
    return decoded_text
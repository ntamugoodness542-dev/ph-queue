import streamlit as st
from datetime import datetime

st.set_page_config(page_title="PH Queue", page_icon="🏥", layout="wide")
st.title("🏥 PH Queue - One Accurate Queue")
st.caption("Online + Walk-In = Same Queue | By Ntamu Goodness")

if "patients" not in st.session_state:
    st.session_state.patients = {}
if "queue" not in st.session_state:
    st.session_state.queue = []
if "serving" not in st.session_state:
    st.session_state.serving = None
if "counter" not in st.session_state:
    st.session_state.counter = 0
if "role" not in st.session_state:
    st.session_state.role = None

# --- LOGIN ---
if st.session_state.role is None:
    st.subheader("Who are you?")
    role = st.radio("Login as:", ["🧑 Patient - Book Online From Home", "[STRIPPED 3 bytes] receptionist - Front Desk", "👨‍⚕️ Doctor"], horizontal=False)

    if role == "🧑 Patient - Book Online From Home":
        st.info("Book from home so you don't wait long at hospital.")
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        age = st.number_input("Age", 0, 120, 20)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        dept = st.selectbox("Department", ["General", "Pharmacy", "Lab", "Antenatal"])
        address = st.text_input("Village / Area")
        if st.button("📱 Book Online & Get My Ticket", use_container_width=True):
            if name and phone:
                st.session_state.counter += 1
                pid = f"PH-{st.session_state.counter:03d}"
                st.session_state.patients[pid] = {"id": pid, "name": name, "phone": phone, "age": age, "gender": gender, "dept": dept, "address": address, "type": "Online", "registered": datetime.now().strftime("%I:%M %p")}
                st.session_state.queue.append({"id": pid, "name": name, "dept": dept, "time": datetime.now().strftime("%I:%M %p"), "type": "Online"})
                st.session_state.my_id = pid
                st.session_state.role = "patient"
                st.rerun()
            else:
                st.warning("Enter name and phone")

        st.divider()
        pid_in = st.text_input("Returning? Enter Your ID e.g PH-001")
        if st.button("See My Place In Queue"):
            if pid_in in st.session_state.patients:
                st.session_state.my_id = pid_in
                st.session_state.role = "patient"
                st.rerun()
            else:
                st.error("ID not found")

    elif role == "[STRIPPED 3 bytes] receptionist - Front Desk":
        st.info("Demo: reception123")
        name = st.text_input("Receptionist Name")
        pw = st.text_input("Password", type="password")
        if st.button("Login as Receptionist"):
            if pw == "reception123" and name:
                st.session_state.role = "receptionist"
                st.session_state.staff_name = name
                st.rerun()
            else:
                st.error("Wrong password")
    else:
        st.info("Demo: doctor123")
        name = st.text_input("Doctor Name")
        pw = st.text_input("Password", type="password")
        if st.button("Login as Doctor"):
            if pw == "doctor123" and name:
                st.session_state.role = "doctor"
                st.session_state.staff_name = name
                st.rerun()
            else:
                st.error("Wrong password")
    st.stop()

if st.button("Logout"):
    st.session_state.role = None
    st.rerun()

# Helper counts
online_count = len([x for x in st.session_state.queue if x.get("type") == "Online"])
walkin_count = len([x for x in st.session_state.queue if x.get("type") == "Walk-In"])

# --- PATIENT VIEW ---
if st.session_state.role == "patient":
    pid = st.session_state.my_id
    p = st.session_state.patients.get(pid)
    st.success(f"🎫 YOUR TICKET: {pid} - Booked {p['type']}")
    st.write(f"**{p['name']}** | {p['dept']} | Phone {p['phone']}")
    if st.session_state.serving and st.session_state.serving["id"] == pid:
        st.success(f"🎉 IT'S YOUR TURN! Go to Doctor")
    elif any(x["id"] == pid for x in st.session_state.queue):
        pos = [x["id"] for x in st.session_state.queue].index(pid)
        st.info(f"You are #{pos+1} in queue. Total waiting: {len(st.session_state.queue)} (Online: {online_count}, Walk-In: {walkin_count}). Wait ~{(pos+1)*10} mins.")
        st.write("Stay at home until your number is close, then come.")
    else:
        st.info("You are not in queue. Receptionist will add you.")

# --- RECEPTIONIST VIEW - THE MAIN CONTROL ---
if st.session_state.role == "receptionist":
    st.subheader(f"🧑‍💼 Reception Desk - {st.session_state.staff_name}")
    st.markdown("### 📊 ACCURATE QUEUE TODAY - Online + Walk-In Together")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL WAITING", len(st.session_state.queue))
    c2.metric("📱 BOOKED ONLINE", online_count)
    c3.metric("🚶 WALK-IN", walkin_count)
    c4.metric("TOTAL REGISTERED", len(st.session_state.patients))
    if st.session_state.serving:
        st.success(f"🔊 NOW SEEING: {st.session_state.serving['id']} - {st.session_state.serving['name']}")

    st.markdown("### ➕ Add Walk-In Patient (No Phone People)")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Patient Name")
        age = st.number_input("Age", 0, 120, 20)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    with col2:
        phone = st.text_input("Phone (type 'No Phone' if none)")
        dept = st.selectbox("Department", ["General", "Pharmacy", "Lab", "Antenatal"])
        address = st.text_input("Village / Area")
    if st.button("✅ Register Walk-In + Add To Same Queue", use_container_width=True):
        if name:
            st.session_state.counter += 1
            pid = f"PH-{st.session_state.counter:03d}"
            st.session_state.patients[pid] = {"id": pid, "name": name, "phone": phone or "No Phone", "age": age, "gender": gender, "dept": dept, "address": address, "type": "Walk-In", "registered": datetime.now().strftime("%I:%M %p")}
            st.session_state.queue.append({"id": pid, "name": name, "dept": dept, "time": datetime.now().strftime("%I:%M %p"), "type": "Walk-In"})
            st.success(f"Added! Ticket: **{pid} - {name}** (Walk-In). Total queue now: {len(st.session_state.queue)}")
            st.balloons()
        else:
            st.warning("Enter name")

    st.divider()
    st.markdown("### 📋 FULL QUEUE IN ORDER - Who Is Next?")
    if st.session_state.queue:
        for i, q in enumerate(st.session_state.queue):
            icon = "📱 Online" if q.get("type")=="Online" else "🚶 Walk-In"
            st.write(f"{i+1}. **{q['id']} - {q['name']}** - {q['dept']} - {icon} - Joined {q['time']}")
    else:
        st.info("Queue empty - No online, no walk-in yet.")

# --- DOCTOR VIEW ---
if st.session_state.role == "doctor":
    st.subheader(f"👨‍⚕️ Doctor Screen - Dr. {st.session_state.staff_name}")
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL WAITING", len(st.session_state.queue))
    c2.metric("📱 ONLINE", online_count)
    c3.metric("🚶 WALK-IN", walkin_count)
    if st.session_state.serving:
        st.success(f"🔊 NOW SEEING: {st.session_state.serving['id']} - {st.session_state.serving['name']}")
    st.markdown("### 📋 Queue In Order")
    for i, q in enumerate(st.session_state.queue):
        icon = "📱 Online" if q.get("type")=="Online" else "🚶 Walk-In"
        st.write(f"{i+1}. {q['id']} - {q['name']} - {q['dept']} - {icon}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📢 Call Next", use_container_width=True):
            if st.session_state.queue:
                st.session_state.serving = st.session_state.queue.pop(0)
                st.rerun()
    with col2:
        if st.button("✅ Finish", use_container_width=True):
            st.session_state.serving = None
            st.rerun()
    st.divider()
    search = st.text_input("Search Patient By ID / Name / Phone")
    if st.button("Search"):
        found = None
        if search in st.session_state.patients:
            found = st.session_state.patients[search]
        else:
            for pid, d in st.session_state.patients.items():
                if d["name"].lower() == search.lower() or d["phone"] == search:
                    found = d
                    break
        if found:
            st.success(f"{found['id']} - {found['name']} | Age {found['age']} | {found['gender']} | {found['phone']} | {found['dept']} | {found['type']} | {found['address']}")
        else:
            st.error("Not found")

st.markdown("---")
st.caption("PH Queue V6 - One Queue: Online + Walk-In")
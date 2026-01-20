// ---------------- DOCTOR DATA ----------------
const doctorData = {
  "General": { doctor: "Dr. Kumar", fees: 300 },
  "ENT": { doctor: "Dr. Arjun", fees: 400 },
  "Dental": { doctor: "Dr. Priya", fees: 500 },
  "Cardiology": { doctor: "Dr. Rajesh", fees: 800 },
  "Psychiatrists": { doctor: "Dr. Meena", fees: 600 },
  "Dermatology": { doctor: "Dr. Anitha", fees: 450 }
};

// ---------------- UPDATE DOCTOR DETAILS ----------------
function updateDoctorDetails() {
  const dept = document.getElementById("department").value;
  const card = document.getElementById("doctorCard");

  if (!dept || !doctorData[dept]) {
    card.style.display = "none";
    return;
  }

  document.getElementById("doctorName").innerText = doctorData[dept].doctor;
  document.getElementById("doctorFees").innerText = "₹" + doctorData[dept].fees;
  card.style.display = "block";
}

// ---------------- SAVE PATIENT & GENERATE TOKEN ----------------
function savePatientAndGenerateToken() {
  const name = document.getElementById("name").value.trim();
  const phone = document.getElementById("phone").value.trim();
  const department = document.getElementById("department").value;
  const problem = document.getElementById("problem").value.trim();

  if (!name || !phone || !department || !problem) {
    alert("Please fill all required details");
    return;
  }

  fetch("/get_token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body:
      `name=${encodeURIComponent(name)}` +
      `&phone=${encodeURIComponent(phone)}` +
      `&department=${encodeURIComponent(department)}` +
      `&problem=${encodeURIComponent(problem)}`
  })
  .then(res => {
    if (!res.ok) throw new Error("Server error");
    return res.json();
  })
  .then(data => {
    if (data.status === "success") {
      document.getElementById("tokenNumber").innerText = data.token;
      document.getElementById("beforeCnt").innerText = data.before;
      document.getElementById("afterCnt").innerText = data.after;
      document.getElementById("result").style.display = "block";
      loadLiveQueue();
    } else {
      alert("Token generation failed.");
    }
  })
  .catch(err => {
    console.error("Token error:", err);
    alert("Something went wrong!");
  });
}

// ---------------- LIVE QUEUE ----------------
function loadLiveStatus(){
  fetch("/live_status")
    .then(res => res.json())
    .then(data => {
      if(data.waiting !== undefined){
        document.getElementById("waitingCount").innerText = data.waiting;
      }
    })
    .catch(err => console.log(err));
}

// auto refresh every 5 seconds
setInterval(loadLiveStatus, 5000);

// load once when page loads
window.onload = loadLiveStatus;

// ---------------- INIT ----------------
window.addEventListener("DOMContentLoaded", () => {
  loadLiveQueue();
  setInterval(loadLiveQueue, 5000);
  document.getElementById("department").addEventListener("change", updateDoctorDetails);
  document.getElementById("submitBtn").addEventListener("click", savePatientAndGenerateToken);
});
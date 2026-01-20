let department = document.getElementById("department")?.value || "";

function checkStatus() {
    const dept = document.getElementById("department").value;
    fetch(`/queue_status/${dept}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById("patientsWaiting").innerText = data.waiting ?? "--";
            document.getElementById("waitTime").innerText = data.wait_time ?? "--";
            document.getElementById("crowdLevel").innerText = data.crowd ?? "--";
            document.getElementById("currentToken").innerText = data.current ?? "--";
            document.getElementById("nextToken").innerText = data.next ?? "--";
        })
        .catch(err => console.error(err));
}

// ================= LOAD LIVE STATUS (AUTO) =================
function loadLiveStatus() {
    fetch("/queues_status")
        .then(res => res.json())
        .then(data => {
            const waitingEl = document.getElementById("waitingCount");
            const dept = document.getElementById("department")?.value;
            if (waitingEl && dept && data[dept] !== undefined) {
                waitingEl.innerText = data[dept];
            }
        })
        .catch(err => console.error(err));
}

// ================= FETCH QUEUE FOR DEPARTMENT =================
function fetchQueue() {
    if (!department) return;
    fetch(`/queue_status/${department}`)
        .then(res => res.json())
        .then(data => {
            const patientsWaiting = document.getElementById("patientsWaiting");
            if (patientsWaiting) patientsWaiting.innerText = data.waiting ?? "--";
            // other fields only if backend sends them
        })
        .catch(err => console.error(err));
}

// ================= NEXT PATIENT (ADMIN CLICK) =================
function nextPatient() {
    if (!department) return;
    fetch(`/next/${department}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert("Queue updated! Next patient: " + data.current);
                fetchQueue();
            } else {
                alert("No waiting patients");
            }
        })
        .catch(err => console.error(err));
}

// ================= DEPARTMENT CHANGE =================
function setDepartment(dept) {
    department = dept;
    fetchQueue();
}


function confirmCall(){
  if(confirm("Do you want to call Emergency 108?")){
    window.location.href = "tel:108";
  }
}


// ================= ON PAGE LOAD =================
window.onload = function () {
    loadLiveStatus();
    fetchQueue();
    setInterval(loadLiveStatus, 5000);
    setInterval(fetchQueue, 5000);
};
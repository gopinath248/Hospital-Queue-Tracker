function loadPatients() {
    fetch("/doctor/patients")
        .then(res => res.json())
        .then(data => {
            let tbody = document.getElementById("patientTable");
            tbody.innerHTML = "";

            data.forEach(p => {
                let row = `
                    <tr>
                        <td>${p.token_no}</td>
                        <td>${p.patient_name}</td>
                        <td>${p.phone}</td>
                        <td>${p.status}</td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
        });
}

// Auto refresh every 5 seconds
setInterval(loadPatients, 5000);

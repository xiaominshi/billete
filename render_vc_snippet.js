function renderVisualCard(data) {
    // Passengers
    let paxHtml = '';
    data.passengers.forEach((p, idx) => {
        paxHtml += `<div class="vc-pax-item">乘客 ${idx + 1}: ${p}</div>`;
    });
    document.getElementById('vc-pax-list').innerHTML = paxHtml;

    // Flights
    let flightsHtml = '';

    // Group by outbound/return simple heuristic: if date gap > 1 day?
    // Actually let's just list them simply first.
    let direction = 'Outbound / 启程';

    data.flights.forEach((f, idx) => {
        // If it's a return flight logic? 
        // For now just 1 card per flight

        // Simple formatting
        flightsHtml += `
                <div class="vc-flight-card">
                    <div class="vc-flight-header">
                        <span>${f.date}</span>
                        <span>${f.flight_no}</span>
                    </div>
                    <div class="vc-flight-route">
                        <div>
                            <div style="font-size:18px;">${f.origin}</div>
                            <div style="font-size:12px; font-weight:400; color:#6B7280;">${f.time}</div>
                        </div>
                        <div style="flex-grow:1; text-align:center; padding:0 20px;">
                            <div style="border-bottom:1px solid #E5E7EB; margin-bottom:5px; position:relative; top:-5px;"></div>
                            <div class="vc-icon">✈</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:18px;">${f.dest}</div>
                            <div style="font-size:12px; font-weight:400; color:#6B7280;">${f.arrival_time || '--:--'}</div>
                        </div>
                    </div>
                    <div class="vc-flight-details">
                         Class: Economy | Non-Stop
                    </div>
                </div>
                `;
    });
    document.getElementById('vc-flight-list').innerHTML = flightsHtml;

    // Luggage
    const lug = data.luggage;
    document.getElementById('vc-luggage').innerHTML = `
                <div>
                     <div style="font-weight:600; font-size:14px; margin-bottom:5px;">行李额度 Allowance</div>
                     <div style="font-size:12px; color:#6B7280;">
                        经济舱往返
                     </div>
                </div>
                <div style="display:flex; gap:20px; text-align:center;">
                     <div>
                        <div style="font-size:20px;">🧳</div>
                        <div style="font-size:12px; font-weight:600;">${lug.pack_count} x ${lug.pack_weight}kg</div>
                     </div>
                     <div>
                        <div style="font-size:20px;">👜</div>
                        <div style="font-size:12px; font-weight:600;">${lug.hand_count} x ${lug.hand_weight}kg</div>
                     </div>
                </div>
            `;

    // Date Header
    document.getElementById('vc-date').innerText = new Date().toLocaleDateString();
}

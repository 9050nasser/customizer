frappe.ui.form.on("Business Trip", {
    from_date: function(frm) {
        calculate_days(frm);
    },
    to_date: function(frm) {
        calculate_days(frm);
    },
    assignment_type: function(frm) {
        // Calculate cost total after setting assignment type
        calculate_cost_total(frm);
    },
    ticket_cost: function(frm) {
        calculate_cost_total(frm);
    },
    external_per_diem_rate: function(frm) {
        if (frm.doc.assignment_type && frm.doc.assignment_type.toLowerCase() === "external") {
            calculate_cost_total(frm);
        }
    },
    internal_per_diem_rate: function(frm) {
        if (frm.doc.assignment_type && frm.doc.assignment_type.toLowerCase() === "internal") {
            calculate_cost_total(frm);
        }
    }
});

function calculate_days(frm) {
    if (frm.doc.from_date && frm.doc.to_date) {
        const fromDate = moment(frm.doc.from_date, "YYYY-MM-DD");
        const toDate = moment(frm.doc.to_date, "YYYY-MM-DD");
        const days = toDate.diff(fromDate, 'days') + 1; // Add 1 to include the start date
        
        frm.set_value("days", days);
        console.log("Calculated days:", days);

        calculate_cost_total(frm); // Recalculate cost total whenever days change
    } else {
        console.log("From Date or To Date is missing.");
    }
}

function calculate_cost_total(frm) {
    const assignmentType = frm.doc.assignment_type ? frm.doc.assignment_type.trim().toLowerCase() : "";
    const days = frm.doc.days || 0;
    const ticketCost = frm.doc.ticket_cost || 0;

    console.log("Assignment type:", assignmentType);
    console.log("Days:", days);
    console.log("Ticket cost:", ticketCost);

    let perDiemRate = 0;

    if (assignmentType === "external") {
        perDiemRate = frm.doc.external_per_diem_rate || 0;
        console.log("Using External Per Diem Rate:", perDiemRate);
    } else if (assignmentType === "internal") {
        perDiemRate = frm.doc.internal_per_diem_rate || 0;
        console.log("Using Internal Per Diem Rate:", perDiemRate);
    } else {
        console.log("Assignment type not set or invalid");
        frm.set_value("cost_total", 0); // Set cost total to 0 if assignment type is invalid
        return;
    }

    // Ensure the per diem rate is valid
    if (perDiemRate <= 0) {
        console.log("Per Diem Rate is invalid or not set.");
        frm.set_value("cost_total", 0);
        return;
    }

    const costTotal = (days * perDiemRate) + ticketCost;
    frm.set_value("cost_total", costTotal);
    console.log("Calculated Cost Total:", costTotal);
}

